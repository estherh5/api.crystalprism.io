import bcrypt
import boto3
import hmac
import json
import os
import psycopg2 as pg
import psycopg2.extras
import re

from base64 import urlsafe_b64decode, urlsafe_b64encode
from flask import jsonify, make_response, request
from hashlib import sha256
from math import floor
from time import time

from canvashare import canvashare


def login():
    # Request should contain Authorization header:
    # 'Basic <username:password>' <base64>
    data = request.authorization

    # Check that authorization request contains required data
    if not data or not data.username or not data.password:
        return make_response('Unauthorized', 401,
            {'WWW-Authenticate': 'Basic realm="Login required!"'})

    username = data.username.strip()
    password = data.password

    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get hashed user password to check credentials against and user status
    cursor.execute(
        """
        SELECT username, password, status
          FROM cp_user
         WHERE LOWER(username) = %(username)s
         LIMIT 1;
        """,
        {'username': username.lower()}
        )

    user_data = cursor.fetchone()

    cursor.close()
    conn.close()

    # Return error if user account is not found
    if not user_data:
        return make_response('Unauthorized', 401)

    # Otherwise, convert user data to dictionary
    user_data = dict(user_data)

    # Return error if user account is deleted
    if user_data['status'] == 'deleted':
        return make_response('Unauthorized', 401)

    # Check requested password against stored hashed and salted password
    if bcrypt.checkpw(password.encode(), user_data['password'].encode()):

        # Generate JWT token if password is correct
        header = urlsafe_b64encode(b'{"alg": "HS256", "typ": "JWT"}')
        payload = urlsafe_b64encode(json.dumps({
            'username': user_data['username'],
            'exp': floor(time() + (60 * 60))  # in seconds
            }).encode())
        secret = os.environ['SECRET_KEY'].encode()
        message = header + b'.' + payload
        signature = hmac.new(secret, message, digestmod=sha256).digest()
        signature = urlsafe_b64encode(signature)
        token = message + b'.' + signature

        return make_response(token.decode(), 200)

    # Return error otherwise
    return make_response('Unauthorized', 401)


def create_user():
    # Request should contain:
    # password <str>
    # username <str>
    data = request.get_json()

    # Return error if request is missing data
    if not data or 'username' not in data or 'password' not in data:
        return make_response('Request must contain username and password', 400)

    username = data['username'].strip()
    password = data['password']

    # Return error if username is blank
    if not username:
        return make_response('Username cannot be blank', 400)

    # Return error if username contains unacceptable characters
    pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

    if not pattern.match(username):
        return make_response('Username contains unacceptable characters', 400)

    # Set up database connection wtih environment variable
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

    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        return make_response('Username already exists', 409)

    # Return error if password is too short
    if len(password) < 8:
        return make_response('Password too short', 400)

    # Generate hashed password with bcrypt cryptographic hash function and salt
    password = data['password'].encode()
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    # Add user account to database
    cursor.execute(
        """
        INSERT INTO cp_user
                    (username, password)
             VALUES (%(username)s, %(password)s);
        """,
        {'username': username, 'password': hashed_password.decode()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 201)


def read_user(requester):
    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve user account from database
    cursor.execute(
        """
        SELECT *
          FROM cp_user
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': requester.lower()}
        )

    user_data = dict(cursor.fetchone())

    # Get user's Shapes in Rain score count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM shapes_score
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['shapes_score_count'] = cursor.fetchone()[0]

    # Get user's Shapes in Rain high score
    cursor.execute(
        """
          SELECT score
            FROM shapes_score
           WHERE member_id = %(member_id)s
        ORDER BY score DESC
           LIMIT 1;
        """,
        {'member_id': user_data['member_id']}
        )

    shapes_high_score = cursor.fetchone()

    if not shapes_high_score:
        user_data['shapes_high_score'] = 0
    else:
        user_data['shapes_high_score'] = shapes_high_score[0]

    # Get user's Rhythm of Life score count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM rhythm_score
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['rhythm_score_count'] = cursor.fetchone()[0]

    # Get user's Rhythm of Life high score
    cursor.execute(
        """
          SELECT score
            FROM rhythm_score
           WHERE member_id = %(member_id)s
        ORDER BY score DESC
           LIMIT 1;
        """,
        {'member_id': user_data['member_id']}
        )

    rhythm_high_score = cursor.fetchone()

    if not rhythm_high_score:
        user_data['rhythm_high_score'] = 0
    else:
        user_data['rhythm_high_score'] = rhythm_high_score[0]

    # Get user's drawing count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM drawing
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['drawing_count'] = cursor.fetchone()[0]

    # Get user's drawing like count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM drawing_like
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['drawing_like_count'] = cursor.fetchone()[0]

    # Get user's post count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM post
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['post_count'] = cursor.fetchone()[0]

    # Get user's comment count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM comment
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['comment_count'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # Remove private information from user_data and return user_data to
    # requester
    user_data.pop('is_owner')
    user_data.pop('member_id')
    user_data.pop('modified')
    user_data.pop('password')

    return jsonify(user_data)


def update_user(requester):
    # Request should contain:
    # about <str>
    # background_color <str>
    # email <str>
    # email_public <boolean>
    # first_name <str>
    # icon_color <str>
    # last_name <str>
    # name_public <boolean>
    # password <str>
    # username <str>
    data = request.get_json()

    # Return error if request is missing data
    if (not data or 'about' not in data or 'background_color' not in data or
        'email' not in data or 'email_public' not in data or
        'first_name' not in data or 'icon_color' not in data or
        'last_name' not in data or 'name_public' not in data or
        'password' not in data or 'username' not in data):
            return make_response('Request is missing required data', 400)

    username = data['username'].strip()
    password = data['password']

    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Check if updated username already exists in database if it is different
    # than requester's username
    if username.lower() != requester.lower():
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

        if cursor.fetchone()[0]:
            cursor.close()
            conn.close()

            return make_response('Username already exists', 409)

    # Check if email address already exists in database if it is not null
    if data['email']:
        data['email'] = data['email'].strip()

        cursor.execute(
            """
            SELECT EXISTS (
                           SELECT 1
                             FROM cp_user
                            WHERE email = %(email)s
                                  AND LOWER(username) != %(username)s
                            LIMIT 1
            );
            """,
            {'email': data['email'],
            'username': requester.lower()}
            )

        if cursor.fetchone()[0]:
            cursor.close()
            conn.close()

            return make_response('Email address already claimed', 409)

    # Retrieve user account from database
    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    cursor.execute(
        """
        SELECT *
          FROM cp_user
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': requester.lower()}
        )

    user_data = dict(cursor.fetchone())

    # Create updated hashed password if user requested change
    if password:
        password = password.encode()
        user_data['password'] = bcrypt.hashpw(
            password, bcrypt.gensalt()).decode()

    # Add updated information to user account in database
    cursor.execute(
        """
        UPDATE cp_user
           SET username = %(username)s, password = %(password)s,
               first_name = %(first_name)s, last_name = %(last_name)s,
               name_public = %(name_public)s, email = %(email)s,
               email_public = %(email_public)s,
               background_color = %(background_color)s,
               icon_color = %(icon_color)s, about = %(about)s,
               modified = to_char
               (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
         WHERE LOWER(username) = %(old_username)s;
        """,
        {'username': username,
        'password': user_data['password'],
        'first_name': data['first_name'].strip(),
        'last_name': data['last_name'].strip(),
        'name_public': data['name_public'],
        'email': data['email'],
        'email_public': data['email_public'],
        'background_color': data['background_color'],
        'icon_color': data['icon_color'],
        'about': data['about'].strip(),
        'old_username': requester.lower()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    # Update bearer token and return to requester
    header = urlsafe_b64encode(b'{"alg": "HS256", "typ": "JWT"}')
    payload = urlsafe_b64encode(
        json.dumps({
            'username': username,
            'exp': floor(time() + (60 * 60))  # in seconds
            }).encode()
        )
    secret = os.environ['SECRET_KEY'].encode()
    message = header + b'.' + payload
    signature = hmac.new(secret, message, digestmod=sha256).digest()
    signature = urlsafe_b64encode(signature)
    token = message + b'.' + signature

    return make_response(token.decode(), 200)


def delete_user_soft(requester):
    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Set user account to 'deleted' status in database
    cursor.execute(
        """
        UPDATE cp_user
           SET status = 'deleted'
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': requester.lower()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def read_user_public(username):
    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve user account from database
    cursor.execute(
        """
        SELECT *
          FROM cp_user
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': username.lower()}
        )

    user_data = cursor.fetchone()

    # Return error if user account is not found
    if not user_data:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert user data to dictionary
    user_data = dict(user_data)

    # Return error if user account is deleted
    if user_data['status'] == 'deleted':
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Get user's Shapes in Rain score count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM shapes_score
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['shapes_score_count'] = cursor.fetchone()[0]

    # Get user's Shapes in Rain high score
    cursor.execute(
        """
          SELECT score, created
            FROM shapes_score
           WHERE member_id = %(member_id)s
        ORDER BY score DESC;
        """,
        {'member_id': user_data['member_id']}
        )

    shapes_high_score = cursor.fetchone()

    if not shapes_high_score:
        user_data['shapes_high_score'] = 0
    else:
        user_data['shapes_high_score'] = shapes_high_score[0]

    # Get user's Rhythm of Life score count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM rhythm_score
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['rhythm_score_count'] = cursor.fetchone()[0]

    # Get user's Rhythm of Life high score
    cursor.execute(
        """
          SELECT score, created
            FROM rhythm_score
           WHERE member_id = %(member_id)s
        ORDER BY score DESC;
        """,
        {'member_id': user_data['member_id']}
        )

    rhythm_high_score = cursor.fetchone()

    if not rhythm_high_score:
        user_data['rhythm_high_score'] = 0
    else:
        user_data['rhythm_high_score'] = rhythm_high_score[0]

    # Get user's drawing count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM drawing
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['drawing_count'] = cursor.fetchone()[0]

    # Get user's drawing like count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM drawing_like
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['drawing_like_count'] = cursor.fetchone()[0]

    # Get user's post count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM post
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['post_count'] = cursor.fetchone()[0]

    # Get user's comment count
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM comment
         WHERE member_id = %(member_id)s;
        """,
        {'member_id': user_data['member_id']}
        )

    user_data['comment_count'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # Remove user's email address if not public
    if not user_data['email_public']:
        user_data.pop('email')

    # Remove user's first and last name if not public
    if not user_data['name_public']:
        user_data.pop('first_name')
        user_data.pop('last_name')

    # Remove private information from user_data
    user_data.pop('email_public')
    user_data.pop('is_owner')
    user_data.pop('member_id')
    user_data.pop('modified')
    user_data.pop('name_public')
    user_data.pop('password')

    return jsonify(user_data)


def delete_user_hard(username):
    # Verify that requester is logged in and return error status code if not
    verification = verify_token()
    if verification.status_code != 200:
        return verification

    # Get username from payload if requester is logged in
    payload = json.loads(verification.data.decode())
    requester = payload['username']

    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve requester's account from database
    cursor.execute(
        """
        SELECT *
          FROM cp_user
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': requester.lower()}
        )

    requester_data = dict(cursor.fetchone())

    # Retrieve user's account from database
    cursor.execute(
        """
        SELECT *
          FROM cp_user
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': username.lower()}
        )

    user_data = cursor.fetchone()

    # Return error if user account is not found
    if not user_data:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert user data to dictionary
    user_data = dict(user_data)

    # Hard-delete user's account if requester is the user or if requester is an
    # admin
    if username.lower() == requester.lower() or requester_data['is_admin']:
        # Retrieve user's drawings from database
        cursor.execute(
            """
            SELECT drawing_id
              FROM drawing
             WHERE member_id = %(member_id)s;
            """,
            {'member_id': user_data['member_id']}
            )

        drawing_ids = []

        for row in cursor.fetchall():
            drawing_ids.append(row[0])

        # Remove each of user's drawings from S3 bucket
        for drawing_id in drawing_ids:
            canvashare.delete_drawing(requester, drawing_id)

        cursor.execute(
            """
            DELETE FROM cp_user
                  WHERE LOWER(username) = %(username)s;
            """,
            {'username': username.lower()}
            )

        conn.commit()

        cursor.close()
        conn.close()

        return make_response('Success', 200)

    cursor.close()
    conn.close()

    # Return error otherwise
    return make_response('Unauthorized', 401)


def verify_token():
    # Request should contain Authorization header:
    # 'Bearer <token>' <str>
    data = request.headers.get('Authorization')

    if not data:
        return make_response('Unauthorized', 401,
            {'WWW-Authenticate': 'Basic realm="Login required!"'})

    token = data.split(' ')[1]

    # Check if token in Authorization header is properly formatted
    pattern = re.compile(
        r'^[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}$')

    if not pattern.match(token):
        return make_response('Unauthorized', 401)

    header = token.split('.')[0].encode()
    payload = json.loads(urlsafe_b64decode(token.split('.')[1]).decode())

    # Check if token is past expiration time
    if payload['exp'] < time():
        return make_response('Unauthorized', 401)

    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Verify that user account is active
    cursor.execute(
        """
        SELECT status
          FROM cp_user
         WHERE LOWER(username) = %(username)s;
        """,
        {'username': payload['username'].lower()}
        )

    user_status = cursor.fetchone()

    cursor.close()
    conn.close()

    # Return error if user account is not found
    if not user_status:
        return make_response('Unauthorized', 401)

    # Return error if user account is deleted
    if user_status[0] == 'deleted':
        return make_response('Unauthorized', 401)

    signature = urlsafe_b64decode(token.split('.')[2])

    # Generate signature using secret to check against signature from Auth
    # header
    secret = os.environ['SECRET_KEY'].encode()
    message = header + b'.' + urlsafe_b64encode(json.dumps(payload).encode())
    signature_check = hmac.new(secret, message, digestmod=sha256).digest()
    if signature != signature_check:
        return make_response('Unauthorized', 401)

    return make_response(json.dumps(payload).encode(), 200)


def read_users():
    # Get number of requested users from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection wtih environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Retrieve user accounts from database
    cursor.execute(
        """
        SELECT username
          FROM cp_user
         WHERE status = 'active';
        """
        )

    usernames = [username[0] for username in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify(usernames[request_start:request_end])
