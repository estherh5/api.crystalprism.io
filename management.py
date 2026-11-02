#!/usr/bin/env python3
import argparse
import bcrypt
import getpass
import json
import os
import psycopg2 as pg

from base64 import decodebytes

from canvashare.hashing import average_hash
from utils import storage


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
             IF NOT EXISTS
                          (SELECT 1
                             FROM pg_type
                            WHERE typname = 'status')
                      THEN
               CREATE TYPE status AS ENUM ('active', 'deleted');
             END IF;
        END
        $$;

        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS cp_user (
            PRIMARY KEY (member_id),
            member_id        UUID          DEFAULT uuid_generate_v4() NOT NULL,
            status           STATUS        DEFAULT 'active'           NOT NULL,
            username         VARCHAR(50)   NOT NULL                   UNIQUE,
            password         TEXT          NOT NULL,
            is_owner         BOOLEAN       DEFAULT false              NOT NULL,
            is_admin         BOOLEAN       DEFAULT false              NOT NULL,
            background_color CHAR(7)       DEFAULT '#ffffff'          NOT NULL,
            icon_color       CHAR(7)       DEFAULT '#000000'          NOT NULL,
            email            TEXT          UNIQUE,
            email_public     BOOLEAN       DEFAULT false,
            first_name       VARCHAR(50),
            last_name        VARCHAR(50),
            name_public      BOOLEAN       DEFAULT false,
            about            VARCHAR(110),
            created          TEXT          DEFAULT to_char
                             (now() at time zone 'UTC',
                             'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')         NOT NULL,
            modified         TEXT          DEFAULT to_char
                             (now() at time zone 'UTC',
                             'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')         NOT NULL
        );

        CREATE UNIQUE INDEX ON cp_user (is_owner)
            WHERE is_owner = true;

        CREATE TABLE IF NOT EXISTS rhythm_score (
            PRIMARY KEY (score_id),
            score_id  SERIAL NOT NULL,
            member_id UUID   REFERENCES cp_user (member_id) ON DELETE CASCADE,
            score     INT    NOT NULL,
            created   TEXT   DEFAULT to_char
                      (now() at time zone 'UTC',
                      'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')      NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shapes_score (
            PRIMARY KEY (score_id),
            score_id  SERIAL NOT NULL,
            member_id UUID   REFERENCES cp_user (member_id) ON DELETE CASCADE,
            score     INT    NOT NULL,
            created   TEXT   DEFAULT to_char
                      (now() at time zone 'UTC',
                      'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')      NOT NULL
        );

        CREATE TABLE IF NOT EXISTS post (
            PRIMARY KEY (post_id),
            post_id   SERIAL      NOT NULL,
            member_id UUID        REFERENCES cp_user (member_id)
                      ON DELETE CASCADE,
            created   TEXT        DEFAULT to_char
                      (now() at time zone 'UTC',
                      'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') NOT NULL,
            modified  TEXT        DEFAULT to_char
                      (now() at time zone 'UTC',
                      'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') NOT NULL
        );

        CREATE TABLE IF NOT EXISTS post_content (
            PRIMARY KEY (post_content_id),
            post_content_id SERIAL      NOT NULL,
            post_id         INT         REFERENCES post(post_id)
                            ON DELETE CASCADE,
            content         TEXT        NOT NULL,
            public          BOOLEAN     DEFAULT false        NOT NULL,
            title           VARCHAR(25) NOT NULL,
            created         TEXT        DEFAULT to_char
                            (now() at time zone 'UTC',
                            'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comment (
            PRIMARY KEY (comment_id),
            comment_id SERIAL NOT NULL,
            post_id    INT    REFERENCES post (post_id)      ON DELETE CASCADE,
            member_id  UUID   REFERENCES cp_user (member_id) ON DELETE CASCADE,
            created    TEXT   DEFAULT to_char
                       (now() at time zone 'UTC',
                       'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')      NOT NULL,
            modified   TEXT   DEFAULT to_char
                       (now() at time zone 'UTC',
                       'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')      NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comment_content (
            PRIMARY KEY (comment_content_id),
            comment_content_id SERIAL NOT NULL,
            comment_id         INT    REFERENCES comment(comment_id)
                               ON DELETE CASCADE,
            content            TEXT   NOT NULL,
            created            TEXT   DEFAULT to_char
                               (now() at time zone 'UTC',
                               'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') NOT NULL
        );

        CREATE TABLE IF NOT EXISTS drawing (
            PRIMARY KEY (drawing_id),
            drawing_id TEXT        NOT NULL,
            member_id  UUID        REFERENCES cp_user (member_id)
                       ON DELETE CASCADE,
            title      VARCHAR(25) NOT NULL,
            url        TEXT        NOT NULL,
            views      INT         DEFAULT 0            NOT NULL,
            created    TEXT        DEFAULT to_char
                       (now() at time zone 'UTC',
                       'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') NOT NULL
        );

        CREATE TABLE IF NOT EXISTS drawing_like (
            PRIMARY KEY (drawing_like_id),
            drawing_like_id SERIAL NOT NULL,
            drawing_id      TEXT   REFERENCES drawing (drawing_id)
                            ON DELETE CASCADE,
            member_id       UUID   REFERENCES cp_user (member_id)
                            ON DELETE CASCADE,
            created         TEXT   DEFAULT to_char
                            (now() at time zone 'UTC',
                            'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') NOT NULL
        );

        CREATE TABLE IF NOT EXISTS auth_attempt (
            kind         TEXT        NOT NULL,
            subject      TEXT        NOT NULL,
            attempted_at TIMESTAMPTZ DEFAULT now() NOT NULL
        );

        CREATE INDEX IF NOT EXISTS auth_attempt_lookup
            ON auth_attempt (kind, subject, attempted_at);
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
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE is_owner = TRUE
                        LIMIT 1
        );
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
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE LOWER(username) = %(username)s
                        LIMIT 1
        );
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
        INSERT INTO cp_user
                    (username, is_admin, is_owner, password)
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
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE LOWER(username) = %(username)s
                        LIMIT 1
        );
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
        INSERT INTO cp_user
                    (username, is_admin, password)
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
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE LOWER(username) = %(username)s
                        LIMIT 1
        );
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
        INSERT INTO cp_user
                    (username, password)
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
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE LOWER(username) = %(username)s
                        LIMIT 1
        );
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
            INSERT INTO post
                        (member_id)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE LOWER(username) = %(username)s)
                 )
              RETURNING post_id;
            """,
            {'username': username.lower()}
            )

        post_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO post_content
                        (content, created, post_id, public, title)
                 VALUES (%(content)s,
                        (SELECT modified
                           FROM post
                          WHERE post_id = %(post_id)s),
                        %(post_id)s, %(public)s, %(title)s);
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
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE is_owner = TRUE
                        LIMIT 1
        );
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
            INSERT INTO post
                        (member_id)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE is_owner = TRUE)
                 )
              RETURNING post_id;
            """
            )

        post_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO post_content
                        (content, created, post_id, public, title)
                 VALUES (%(content)s,
                        (SELECT modified
                           FROM post
                          WHERE post_id = %(post_id)s),
                        %(post_id)s, %(public)s, %(title)s);
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


def create_all_drawings_from_bucket():
    username = input('Enter username for drawing artist: ')

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])
    cursor = conn.cursor()

    # Check if username exists in database
    cursor.execute(
        """
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE LOWER(username) = %(username)s
                        LIMIT 1
        );
        """,
        {'username': username.lower()}
        )

    # Rerun function to prompt for a new post writer if the username does not
    # exist
    if not cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        print('Username does not exist')

        create_all_drawings_from_bucket()

        return

    # Get existing drawings from the R2 bucket
    for drawing in storage.bucket().objects.filter(Prefix=storage.DRAWING_DIR):
        drawing_id = drawing.key.split(storage.DRAWING_DIR)[1].replace(".png", "")

        # Add drawing to database
        cursor.execute(
            """
            INSERT INTO drawing
                        (drawing_id, member_id, title, url)
                 VALUES (%(drawing_id)s,
                        (SELECT member_id
                           FROM cp_user
                          WHERE LOWER(username) = %(username)s),
                        %(title)s, %(url)s);
            """,
            {'drawing_id': drawing_id,
            'username': username.lower(),
            'title': drawing_id,
            'url': storage.public_url(drawing.key)}
            )

        print('Drawing "' + drawing_id + '" added to database.')

    conn.commit()
    cursor.close()
    conn.close()

    return


def create_drawings(drawings_filename):
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    username = input('Enter username for drawing artist: ')

    # Check if username exists in database
    cursor.execute(
        """
        SELECT EXISTS (
                       SELECT 1
                         FROM cp_user
                        WHERE LOWER(username) = %(username)s
                        LIMIT 1
        );
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

        # Generate unique id for drawing from its average hash, using the
        # same function the API uses so the two paths cannot drift apart
        drawing_id = average_hash(drawing_url)

        # Check if drawing already exists in database
        cursor.execute(
            """
            SELECT EXISTS (
                           SELECT 1
                             FROM drawing
                            WHERE drawing_id = %(drawing_id)s
                            LIMIT 1
            );
            """,
            {'drawing_id': drawing_id}
            )

        if cursor.fetchone()[0]:
            print('Drawing "' + drawing_id + '" already exists')

        else:
            # Upload drawing to the R2 bucket
            key = storage.DRAWING_DIR + drawing_id + '.png'

            storage.bucket().put_object(
                Key=key, Body=drawing_url, ContentType='image/png')

            # Set up database connection with environment variable
            conn = pg.connect(os.environ['DB_CONNECTION'])

            cursor = conn.cursor()

            # Add drawing to database
            cursor.execute(
                """
                INSERT INTO drawing
                            (drawing_id, member_id, title, url)
                     VALUES (%(drawing_id)s,
                            (SELECT member_id
                               FROM cp_user
                              WHERE LOWER(username) = %(username)s),
                            %(title)s, %(url)s);
                """,
                {'drawing_id': drawing_id,
                'username': username.lower(),
                'title': drawing['title'],
                'url': storage.public_url(key)}
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


if __name__ == '__main__':
    # Add arguments for initializing database in CLI
    parser = argparse.ArgumentParser(description='Management commands')
    parser.add_argument('action', type=str, help="an action for the database")
    args = parser.parse_args()
    if args.action == 'init_db':
        initialize_database()
    if args.action == 'load_data':
        load_initial_data()
    if args.action == 'load_bucket_drawings':
        create_all_drawings_from_bucket()
