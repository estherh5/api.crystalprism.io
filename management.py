#!/usr/bin/env python3
import argparse
import bcrypt
import boto3
import datetime
import getpass
import json
import os
import psycopg2 as pg
import subprocess

from base64 import decodebytes
from crontab import CronTab
from io import BytesIO
from PIL import Image


def initialize_database():
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Create status type, UUID extension for member_id generation, and database
    # tables
    cursor.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status') THEN
                CREATE TYPE status AS ENUM ('active', 'deleted');
            END IF;
        END
        $$;

        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS cp_user (
        about varchar(110),
        background_color char(7) NOT NULL DEFAULT '#ffffff',
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        email text UNIQUE,
        email_public boolean DEFAULT false,
        first_name varchar(50),
        icon_color char(7) NOT NULL DEFAULT '#000000',
        is_admin boolean NOT NULL DEFAULT false,
        is_owner boolean NOT NULL DEFAULT false,
        last_name varchar(50),
        member_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
        modified text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        name_public boolean DEFAULT false,
        password text NOT NULL,
        status status NOT NULL DEFAULT 'active',
        username varchar(50) UNIQUE NOT NULL);

        CREATE UNIQUE INDEX ON cp_user (is_owner) WHERE is_owner = true;

        CREATE TABLE IF NOT EXISTS rhythm_score (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        score int NOT NULL,
        score_id SERIAL PRIMARY KEY);

        CREATE TABLE IF NOT EXISTS shapes_score (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        score int NOT NULL,
        score_id SERIAL PRIMARY KEY);

        CREATE TABLE IF NOT EXISTS post (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        modified text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        post_id SERIAL PRIMARY KEY);

        CREATE TABLE IF NOT EXISTS post_content (
        content text NOT NULL,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        post_content_id SERIAL PRIMARY KEY,
        post_id int REFERENCES post(post_id) ON DELETE CASCADE,
        public boolean NOT NULL DEFAULT false,
        title varchar(25) NOT NULL);

        CREATE TABLE IF NOT EXISTS comment (
        comment_id SERIAL PRIMARY KEY,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        modified text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        post_id int REFERENCES post(post_id) ON DELETE CASCADE);

        CREATE TABLE IF NOT EXISTS comment_content (
        comment_content_id SERIAL PRIMARY KEY,
        comment_id int REFERENCES comment(comment_id) ON DELETE CASCADE,
        content text NOT NULL,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'));

        CREATE TABLE IF NOT EXISTS drawing (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        drawing_id text PRIMARY KEY,
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        title varchar(25) NOT NULL,
        url text NOT NULL,
        views int NOT NULL DEFAULT 0);

        CREATE TABLE IF NOT EXISTS drawing_like (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        drawing_id text REFERENCES drawing(drawing_id) ON DELETE CASCADE,
        drawing_like_id SERIAL PRIMARY KEY,
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE);
        """
        )

    conn.commit()

    cursor.close()
    conn.close()

    print('Database ' + os.environ['DB_NAME'] + ' initialized successfully.')

    return


def create_owner_user():
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Check if owner already exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE is_owner = TRUE LIMIT 1);
        """
        )

    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Owner user already exists')

        return

    username = input('Enter username for webpage owner: ')

    # Check if username already exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE LOWER(username) = %(username)s LIMIT 1);
        """,
        {'username': username.lower()}
        )

    # Rerun function to prompt for a new username if the username already
    # exists
    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username already exists')

        create_owner_user()

        return

    # Prompt for password that is at least 8 characters long
    password = getpass.getpass('Enter password for ' + username + ': ')

    while len(password) < 8:
        print('Password must be at least 8 characters long')
        password = getpass.getpass('Enter password for ' + username + ': ')

    # Generate hashed password with bcrypt cryptographic hash function and salt
    password = password.encode()
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    # Add user account to database
    cursor.execute(
        """
        INSERT INTO cp_user (username, is_admin, is_owner, password)
        VALUES (%(username)s, %(is_admin)s, %(is_owner)s, %(password)s);
        """,
        {'username': username,
        'is_admin': True,
        'is_owner': True,
        'password': hashed_password.decode()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    print('Owner user "' + username + '" added to database.')

    return


def create_admin_user():
    username = input('Enter username for admin: ')

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Check if username already exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE LOWER(username) = %(username)s LIMIT 1);
        """,
        {'username': username.lower()}
        )

    # Rerun function to prompt for a new username if the username already
    # exists
    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username already exists')

        create_admin_user()

        return

    # Prompt for password that is at least 8 characters long
    password = getpass.getpass('Enter password for ' + username + ': ')

    while len(password) < 8:
        print('Password must be at least 8 characters long')
        password = getpass.getpass('Enter password for ' + username + ': ')

    # Generate hashed password with bcrypt cryptographic hash function and salt
    password = password.encode()
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    # Add user account to database
    cursor.execute(
        """
        INSERT INTO cp_user (username, is_admin, password)
        VALUES (%(username)s, %(is_admin)s, %(password)s);
        """,
        {'username': username,
        'is_admin': True,
        'password': hashed_password.decode()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    print('Admin user "' + username + '" added to database.')

    return


def create_user():
    username = input('Enter username for general user: ')

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Check if username already exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE LOWER(username) = %(username)s LIMIT 1);
        """,
        {'username': username.lower()}
        )

    # Rerun function to prompt for a new username if the username already
    # exists
    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username already exists')

        create_user()

        return

    # Prompt for password that is at least 8 characters long
    password = getpass.getpass('Enter password for ' + username + ': ')

    while len(password) < 8:
        print('Password must be at least 8 characters long')
        password = getpass.getpass('Enter password for ' + username + ': ')

    # Generate hashed password with bcrypt cryptographic hash function and salt
    password = password.encode()
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    # Add user account to database
    cursor.execute(
        """
        INSERT INTO cp_user (username, password)
        VALUES (%(username)s, %(password)s);
        """,
        {'username': username,
        'password': hashed_password.decode()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    print('User "' + username + '" added to database.')

    return


def create_posts(posts_filename):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    username = input('Enter username for post writer: ')

    # Check if username exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE LOWER(username) = %(username)s LIMIT 1);
        """,
        {'username': username.lower()}
        )

    # Rerun function to prompt for a new post writer if the username does not
    # exist
    if not cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username does not exist')

        create_posts(posts_filename)

        return

    # Open posts_filename to get initial post data
    posts_file = 'fixtures/' + posts_filename
    with open(posts_file, 'r') as post_data:
        posts = json.load(post_data)

    # Add posts to database
    for post in posts:
        cursor.execute(
            """
            INSERT INTO post (member_id)
            VALUES ((SELECT member_id FROM cp_user
            WHERE LOWER(username) = %(username)s))
            RETURNING post_id;
            """,
            {'username': username.lower()}
            )

        post_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO post_content (content, created, post_id, public, title)
            VALUES (%(content)s, (SELECT modified FROM post
            WHERE post_id = %(post_id)s), %(post_id)s, %(public)s, %(title)s);
            """,
            {'content': post['content'],
            'post_id': post_id,
            'public': post['public'],
            'title': post['title']}
            )

        conn.commit()

        print('Post "' + str(post_id) + '" added to database.')

    cursor.close()
    conn.close()

    return


def create_ideas(ideas_filename):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Check if owner user exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE is_owner = TRUE LIMIT 1);
        """
        )

    # Rerun function to prompt for an owner user if the user does not exist
    if not cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Owner user does not exist')

        # Prompt user to create webpage owner
        create_owner = input('Create owner user? Y/N: ')
        while create_owner.lower() != 'y' and create_owner.lower() != 'n':
            create_owner = input('Create owner user? Y/N: ')

        # Create webpage owner user if user specifies
        if create_owner.lower() == 'y':
            create_owner_user()
            create_ideas(ideas_filename)

        return

    # Open posts_filename to get initial post data
    posts_file = 'fixtures/' + ideas_filename
    with open(posts_file, 'r') as post_data:
        posts = json.load(post_data)

    # Add posts to database
    for post in posts:
        cursor.execute(
            """
            INSERT INTO post (member_id)
            VALUES ((SELECT member_id FROM cp_user
            WHERE is_owner = TRUE))
            RETURNING post_id;
            """
            )

        post_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO post_content (content, created, post_id, public, title)
            VALUES (%(content)s, (SELECT modified FROM post
            WHERE post_id = %(post_id)s), %(post_id)s, %(public)s, %(title)s);
            """,
            {'content': post['content'],
            'post_id': post_id,
            'public': post['public'],
            'title': post['title']}
            )

        conn.commit()

        print('Post "' + str(post_id) + '" added to database.')

    cursor.close()
    conn.close()

    return


def create_drawings(drawings_filename):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    username = input('Enter username for drawing artist: ')

    # Check if username exists in database
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM cp_user WHERE LOWER(username) = %(username)s LIMIT 1);
        """,
        {'username': username.lower()}
        )

    # Rerun function to prompt for a new post writer if the username does not
    # exist
    if not cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username does not exist')

        create_drawings(drawings_filename)

        return

    # Open drawings_filename to get initial drawing data
    drawings_file = 'fixtures/' + drawings_filename
    with open(drawings_file, 'r') as drawing_data:
        drawings = json.load(drawing_data)

    # Add drawings to database
    for drawing in drawings:

        # Remove 'data:image/png;base64' from image data URL
        drawing_url = decodebytes(drawing['url'].split(',')[1].encode('utf-8'))

        # Reduce drawing size to generate average hash for assessing drawing
        # uniqueness
        drawing_small = Image.open(BytesIO(drawing_url)).resize(
            (8, 8), Image.ANTIALIAS)

        # Convert small drawing to grayscale
        drawing_small = drawing_small.convert('L')

        # Get average pixel value of small drawing
        pixels = list(drawing_small.getdata())
        average_pixels = sum(pixels) / len(pixels)

        # Generate bit string by comparing each pixel in the small drawing to
        # the average pixel value
        bit_string = "".join(map(
            lambda pixel: '1' if pixel < average_pixels else '0', pixels))

        # Generate unique id for drawing by converting bit string to
        # hexadecimal
        drawing_id = int(bit_string, 2).__format__('016x')

        # Check if drawing already exists in database
        cursor.execute(
            """
            SELECT exists (
            SELECT 1 FROM drawing WHERE drawing_id = %(drawing_id)s LIMIT 1);
            """,
            {'drawing_id': drawing_id}
            )

        if cursor.fetchone()[0]:
            print('Drawing "' + drawing_id + '" already exists')

        else:
            # Upload drawing to S3 bucket
            s3 = boto3.resource('s3')
            bucket_name = os.environ['S3_BUCKET']
            bucket = s3.Bucket(bucket_name)
            bucket_folder = os.environ['S3_CANVASHARE_DIR']

            drawing_name = drawing_id + '.png'

            bucket.put_object(
                Key=bucket_folder + drawing_name,
                Body=drawing_url
                )

            # Set up database connection with environment variable
            conn = pg.connect(os.environ['DB_CONNECTION'])

            cursor = conn.cursor()

            # Add drawing to database
            cursor.execute(
                """
                INSERT INTO drawing (drawing_id, member_id, title, url)
                VALUES (%(drawing_id)s, (SELECT member_id FROM cp_user
                WHERE LOWER(username) = %(username)s), %(title)s, %(url)s);
                """,
                {'drawing_id': drawing_id,
                'username': username.lower(),
                'title': drawing['title'],
                'url': os.environ['S3_URL'] + bucket_folder + drawing_name}
                )

            conn.commit()

            cursor.close()
            conn.close()

            print('Drawing "' + drawing_id + '" added to database.')

    return


def load_initial_data():
    # Prompt user to create webpage owner
    create_owner = input('Create owner user? Y/N: ')
    while create_owner.lower() != 'y' and create_owner.lower() != 'n':
        create_owner = input('Create owner user? Y/N: ')

    # Create webpage owner user if user specifies
    if create_owner.lower() == 'y':
        create_owner_user()

    # Prompt user to create admin
    create_admin = input('Create admin user? Y/N: ')
    while create_admin.lower() != 'y' and create_admin.lower() != 'n':
        create_admin = input('Create admin user? Y/N: ')

    # Create admin user if user specifies
    if create_admin.lower() == 'y':
        create_admin_user()

    # Prompt user to create initial Thought Writer posts
    create_init_posts = input('Create initial Thought Writer posts? Y/N: ')
    while (create_init_posts.lower() != 'y' and
        create_init_posts.lower() != 'n'):
            create_init_posts = input(
                'Create initial Thought Writer posts? Y/N: '
                )

    # Create initial Thought Writer posts if user specifies
    if create_init_posts.lower() == 'y':
        create_posts('thought-writer-posts.json')

    # Prompt user to create initial homepage posts
    create_init_ideas = input('Create initial homepage Ideas post? Y/N: ')
    while (create_init_ideas.lower() != 'y' and
        create_init_ideas.lower() != 'n'):
            create_init_ideas = input(
                'Create initial homepage Ideas post? Y/N: '
                )

    # Create initial homepage post if user specifies
    if create_init_ideas.lower() == 'y':
        create_ideas('homepage-post.json')

    # Prompt user to create initial drawings
    create_init_drawings = input('Create initial CanvaShare drawings? Y/N: ')
    while (create_init_drawings.lower() != 'y' and
        create_init_drawings.lower() != 'n'):
            create_init_drawings = input(
                'Create initial CanvaShare drawings? Y/N: '
                )

    # Create initial drawings if user specifies
    if create_init_drawings.lower() == 'y':
        create_drawings('canvashare-drawing.json')

    print('Initial database data loaded successfully.')

    return


def backup_database():
    # Define database name and user
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']

    # Define backup file path
    now = str(datetime.datetime.now().isoformat())
    file_path = os.environ['BACKUP_DIR'] + '/' + now

    # Define command to run to back up database
    command = 'pg_dump ' + db_name + ' -U ' + db_user + ' -Fc -f ' + file_path

    # Dump database backup to file path
    ps = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
        cwd=os.path.dirname(os.path.realpath(__file__)))
    print('Backup saved to ' + file_path)

    # Upload file to s3 backup bucket
    s3 = boto3.resource('s3')
    bucket_name = os.environ['S3_BUCKET']
    bucket = s3.Bucket(bucket_name)
    bucket_folder = os.environ['S3_BACKUP_DIR']

    data = open(file_path, 'rb')

    bucket.put_object(Key=bucket_folder + now, Body=data)

    print('Backup saved to S3 ' + bucket_name + ' bucket')

    return


def schedule_weekly_backup():
    # Initiate CronTab instance for current user
    user = getpass.getuser()
    cron = CronTab(user)

    # Create weekly job to back up database
    job = cron.new(
        command='export WORKON_HOME=~/.virtualenvs; ' +
        'VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3; ' +
        'source /usr/local/bin/virtualenvwrapper.sh; ' +
        'workon ' + os.environ['VIRTUAL_ENV_NAME'] + '; ' +
        'source ~/.virtualenvs/' + os.environ['VIRTUAL_ENV_NAME'] +
        '/bin/postactivate; python ' + os.path.abspath(__file__) + ' backup_db'
        )
    job.minute.on(0)
    job.hour.on(0)
    job.dow.on(0)

    cron.write()

    print(
        'Weekly backup scheduled for ' + os.environ['DB_NAME'] + ' database.'
        )

    return


# Add arguments for initializing database in CLI
parser = argparse.ArgumentParser(description='Management commands')
parser.add_argument('action', type=str, help="an action for the database")
args = parser.parse_args()
if args.action == 'init_db':
    initialize_database()
if args.action == 'load_data':
    load_initial_data()
if args.action == 'backup_db':
    backup_database()
if args.action == 'sched_backup':
    schedule_weekly_backup()
