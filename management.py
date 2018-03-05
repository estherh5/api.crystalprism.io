#!/usr/bin/env python3
import argparse
import bcrypt
import getpass
import json
import os
import psycopg2 as pg

from base64 import decodebytes


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
        content text NOT NULL,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        post_id SERIAL PRIMARY KEY,
        public boolean NOT NULL DEFAULT false,
        title varchar(25) NOT NULL);

        CREATE TABLE IF NOT EXISTS comment (
        comment_id SERIAL PRIMARY KEY,
        content text NOT NULL,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        post_id int REFERENCES post(post_id) ON DELETE CASCADE);

        CREATE TABLE IF NOT EXISTS drawing (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        drawing_id SERIAL PRIMARY KEY,
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        title varchar(25) NOT NULL,
        url text NOT NULL,
        views int NOT NULL DEFAULT 0);

        CREATE TABLE IF NOT EXISTS drawing_like (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        drawing_id int REFERENCES drawing(drawing_id) ON DELETE CASCADE,
        drawing_like_id SERIAL PRIMARY KEY,
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE);
        """
        )

    conn.commit()

    cursor.close()
    conn.close()

    print('Database ' + os.environ['DB_NAME'] + ' initialized successfully.')

    return


def create_owner_user(username):
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

    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username already exists')

        return

    # Generate hashed password with bcrypt cryptographic hash function and salt
    password = getpass.getpass('Enter password for ' + username + ': ')
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

    print('User "' + username + '" added to database.')

    return


def create_admin_user(username):
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

    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username already exists')

        return

    # Generate hashed password with bcrypt cryptographic hash function and salt
    password = getpass.getpass('Enter password for ' + username + ': ')
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


def create_posts(username, posts_filename):
    # Open posts_filename to get initial post data
    posts_file = 'fixtures/' + posts_filename
    with open(posts_file, 'r') as post_data:
        posts = json.load(post_data)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Add posts to database
    for post in posts:
        cursor.execute(
            """
            INSERT INTO post (member_id, content, title, public)
            VALUES ((SELECT member_id FROM cp_user
            WHERE LOWER(username) = %(username)s), %(content)s, %(title)s,
            %(public)s)
            RETURNING post_id;
            """,
            {'username': username.lower(),
            'content': post['content'],
            'title': post['title'],
            'public': post['public']}
            )

        conn.commit()

        post['post_id'] = cursor.fetchone()[0]

        print('Post "' + str(post['post_id']) + '" added to database.')

    cursor.close()
    conn.close()

    return


def create_drawings(username, drawings_filename):
    # Open drawings_filename to get initial drawing data
    drawings_file = 'fixtures/' + drawings_filename
    with open(drawings_file, 'r') as drawing_data:
        drawings = json.load(drawing_data)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Add drawings to database
    for drawing in drawings:
        cursor.execute(
            """
            INSERT INTO drawing (member_id, title, url)
            VALUES ((SELECT member_id FROM cp_user
            WHERE LOWER(username) = %(username)s), %(title)s, %(url)s)
            RETURNING drawing_id;
            """,
            {'username': username.lower(),
            'title': drawing['title'],
            'url': drawing['url']}
            )

        conn.commit()

        drawing_id = cursor.fetchone()[0]

        # Remove 'data:image/png;base64' from image data URL
        drawing['url'] = drawing['url'].split(',')[1].encode('utf-8')

        # Upload drawing to S3 bucket
        s3 = boto3.resource('s3')
        bucket_name = os.environ['S3_BUCKET']
        bucket = s3.Bucket(bucket_name)
        bucket_folder = os.environ['S3_CANVASHARE_DIR']

        drawing_name = str(drawing_id) + '.png'

        bucket.put_object(
            Key=bucket_folder + drawing_name,
            Body=decodebytes(drawing['url'])
            )

        # Add drawing URL to database
        cursor.execute(
            """
            UPDATE drawing SET url = %(url)s WHERE drawing_id = %(drawing_id)s;
            """,
            {'url': os.environ['S3_URL'] + bucket_folder + drawing_name,
            'drawing_id': drawing_id}
            )

        conn.commit()

        cursor.close()
        conn.close()

        print('Drawing "' + str(drawing_id) + '" added to database.')

    return


def load_initial_data():
    # Create webpage owner user
    user = input('Enter username for webpage owner: ')
    create_owner_user(user)

    # Create admin user
    admin = input('Enter username for admin user: ')
    create_admin_user(admin)

    # Create initial Thought Writer posts
    create_posts(admin, 'thought-writer-posts.json')

    # Create initial homepage post
    create_posts(user, 'homepage-post.json')

    # Create initial drawing
    create_drawings(admin, 'canvashare-drawing.json')

    print('Initial database data loaded successfully.')

    return


# Add arguments for initializing database in CLI
parser = argparse.ArgumentParser(description='Management commands')
parser.add_argument('action', type=str, help="an action for the database")
args = parser.parse_args()
if args.action == 'init_db':
    initialize_database()
if args.action == 'load_data':
    load_initial_data()
