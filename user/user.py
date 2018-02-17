import bcrypt
import fcntl
import hmac
import json
import os
import re
import shutil

from base64 import b64encode, urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone
from flask import jsonify, make_response, request
from hashlib import sha256
from math import floor
from time import time
from uuid import uuid4

cwd = os.path.dirname(__file__)


def login():
    # Request should contain Authorization header:
    # 'Basic <username:password>' <base64>
    data = request.authorization

    # Check that authorization request contains required data
    if not data or not data.username or not data.password:
        return make_response('Could not verify', 401,
            {'WWW-Authenticate': 'Basic realm="Login required!"'})

    username = data.username
    password = data.password

    # Check that request credentials are correct
    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:

            if user_data['username'].lower() == username.lower():

                # Reject requests for logging into deleted user accounts
                if user_data['status'] == 'deleted':
                    return make_response('Username does not exist', 404)

                # Check requested password against stored hashed and salted
                # password
                if bcrypt.checkpw(
                    password.encode(), user_data['password'].encode()):
                    # Generate JWT token if password is correct
                    header = urlsafe_b64encode(
                        b'{"alg": "HS256", "typ": "JWT"}')
                    payload = urlsafe_b64encode(
                        json.dumps({
                            'username': username,
                            'exp': floor(time() + (60 * 60))  # in seconds
                            }).encode()
                        )
                    secret = os.environ['SECRET_KEY'].encode()
                    message = header + b'.' + payload
                    signature = hmac.new(secret, message,
                        digestmod=sha256).digest()
                    signature = urlsafe_b64encode(signature)
                    token = message + b'.' + signature
                    return make_response(token.decode(), 200)

                return make_response('Incorrect password', 401)

        return make_response('Username does not exist', 404)


def create_user():
    # Request should contain:
    # username <str>
    # password <str>
    data = request.get_json()

    username = data['username']

    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)

        # Check if username already exists
        for user_data in users:
            if user_data['username'].lower() == username.lower():
                return make_response('Username already exists', 409)

        # Generate random UUID as non-client-facing user identifier
        member_id = str(uuid4())

        # Hash password with bcrypt cryptographic hash function and salt
        password = data['password'].encode()
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        entry = {
            'member_id': member_id,
            'status': 'active',
            'username': username,
            'password': hashed_password.decode(),
            'admin': False,
            'member_since': datetime.now(timezone.utc).isoformat(),
            'first_name': '',
            'last_name': '',
            'name_public': False,
            'email': '',
            'email_public': False,
            'background_color': '#ffffff',
            'icon_color': '#000000',
            'about': '',
            'shapes_plays': 0,
            'shapes_scores': [],
            'shapes_high_score': 0,
            'rhythm_plays': 0,
            'rhythm_scores': [],
            'rhythm_high_score': 0,
            'rhythm_high_lifespan': '00:00:00',
            'drawing_count': 0,
            'liked_drawings': [],
            'post_count': 0,
            'comment_count': 0
            }
        users.append(entry)

    with open(cwd + '/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response('Success', 201)


def read_user(requester):
    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)

        for user_data in users:
            if user_data['username'].lower() == requester.lower():

                # Return error if user account was deleted
                if user_data['status'] == 'deleted':
                    return make_response('Username does not exist', 404)

                # Replace artist member_id with username for each drawing the
                # user liked
                for i in range(len(user_data['liked_drawings'])):
                    for artist in users:
                        liked_file = user_data['liked_drawings'][i].split('/')
                        if artist['member_id'] == liked_file[-2]:
                            user_data['liked_drawings'][i] = str(
                                artist['username'] + '/' + liked_file[-1])

                # Remove password from user_data
                user_data.pop('password')

                return jsonify(user_data)

        # Return error if user account is not found
        return make_response('Username does not exist', 404)


def update_user(requester):
    # Request should contain:
    # username <str>
    # password <str>
    # about <str>
    # first_name <str>
    # last_name <str>
    # name_public <boolean>
    # email <str>
    # email_public <boolean>
    # background_color <str>
    # icon_color <str>
    data = request.get_json()

    username = data['username']
    password = data['password']

    user_found = False  # Stores whether user account is found in users file

    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)

        # Check if username already exists if user requests to update it
        if username.lower() != requester.lower():
            for user_data in users:
                if user_data['username'].lower() == username.lower():
                    return make_response('Username already exists', 409)

        for user_data in users:
            if user_data['username'].lower() == requester.lower():

                user_found = True

                # Return error if user account was deleted
                if user_data['status'] == 'deleted':
                    return make_response('Username does not exist', 404)

                user_data['username'] = username

                # Store hashed password if user requested change
                if password != '':
                    password = password.encode()
                    user_data['password'] = bcrypt.hashpw(password,
                        bcrypt.gensalt()).decode()

                user_data['first_name'] = data['first_name']
                user_data['last_name'] = data['last_name']
                user_data['name_public'] = data['name_public']
                user_data['email'] = data['email']
                user_data['email_public'] = data['email_public']
                user_data['background_color'] = data['background_color']
                user_data['icon_color'] = data['icon_color']
                user_data['about'] = data['about']

                # Update bearer token
                header = urlsafe_b64encode(b'{"alg": "HS256", "typ": "JWT"}')
                payload = urlsafe_b64encode(
                    json.dumps({
                        'username': username,
                        'exp': floor(time() + (60 * 60))  # in seconds
                        }).encode()
                    )
                secret = os.environ['SECRET_KEY'].encode()
                message = header + b'.' + payload
                signature = hmac.new(secret, message,
                    digestmod=sha256).digest()
                signature = urlsafe_b64encode(signature)
                token = message + b'.' + signature

    # Return error if user account is not found
    if not user_found:
        return make_response('Username does not exist', 404)

    with open(cwd + '/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response(token.decode(), 200)


def delete_user_soft(requester):
    user_found = False  # Stores whether user account is found in users file

    # Set user account status to deleted
    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                user_data['status'] = 'deleted'
                user_found = True

    # Return error if user account is not found
    if not user_found:
        return make_response('Username does not exist', 404)

    with open(cwd + '/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response('Success', 200)


def read_user_public(username):
    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == username.lower():

                # Return error if user account is deleted
                if user_data['status'] == 'deleted':
                    return make_response('Username does not exist', 404)

                # Send user's first and last name if public
                if user_data['name_public']:
                    first_name = user_data['first_name']
                    last_name = user_data['last_name']
                    name = first_name + ' ' + last_name
                else:
                    name = ''

                # Send user's email address if public
                if user_data['email_public']:
                    email = user_data['email']
                else:
                    email = ''

                data = {
                    'username': user_data['username'],
                    'name': name,
                    'email': email,
                    'background_color': user_data['background_color'],
                    'icon_color': user_data['icon_color'],
                    'about': user_data['about'],
                    'member_since': user_data['member_since'],
                    'shapes_high_score': user_data['shapes_high_score'],
                    'rhythm_high_lifespan': user_data['rhythm_high_lifespan'],
                    'drawing_count': user_data['drawing_count'],
                    'post_count': user_data['post_count'],
                    'comment_count': user_data['comment_count']
                    }
                return jsonify(data)

        return make_response('Username does not exist', 404)


def delete_user_hard(username):
    user_found = False  # Stores whether user account is found in users file

    # Remove user account from users file
    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == username.lower():
                user_id = user_data['member_id']
                liked_drawings = user_data['liked_drawings']
                user_data['username'] = '[deleted]'
                user_data['password'] = '[deleted]'
                user_data['first_name'] = ''
                user_data['last_name'] = ''
                user_data['email'] = ''
                user_data['about'] = ''
                user_data['status'] = 'deleted'
                user_found = True

    # Return error if user account is not found
    if not user_found:
        return make_response('Username does not exist', 404)

    with open(cwd + '/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    # Delete user's drawings and drawing info files
    if os.path.exists(cwd + '/../canvashare/drawings/' + user_id):
        user_drawings = os.listdir(cwd + '/../canvashare/drawings/' + user_id)
        user_drawings = [user_id + '/' + drawing for drawing in user_drawings]
        shutil.rmtree(cwd + '/../canvashare/drawings/' + user_id)
        shutil.rmtree(cwd + '/../canvashare/drawing_info/' + user_id)

    else:
        user_drawings = []

    # Remove user's drawings from others' liked drawings list if user created
    # drawings
    if user_drawings:
        with open(cwd + '/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                for drawing in user_data['liked_drawings']:
                    if drawing in user_drawings:
                        user_data['liked_drawings'].remove(drawing)

        with open(cwd + '/users.json', 'w') as users_file:
            # Lock file to prevent overwrite
            fcntl.flock(users_file, fcntl.LOCK_EX)
            json.dump(users, users_file)
            # Release lock on file
            fcntl.flock(users_file, fcntl.LOCK_UN)

    # Remove user as liker from other users' drawings
    for liked_drawing in liked_drawings:
        liked_drawing_file = liked_drawing.replace('png', 'json')
        with open(cwd + '/../canvashare/drawing_info/' + liked_drawing_file,
            'r') as info_file:
            drawing_info = json.load(info_file)
            drawing_info['liked_users'].remove(user_id)
            drawing_info['likes'] -= 1

        with open(cwd + '/../canvashare/drawing_info/' + liked_drawing_file,
            'w') as info_file:
            # Lock file to prevent overwrite
            fcntl.flock(info_file, fcntl.LOCK_EX)
            json.dump(drawing_info, info_file)
            # Release lock on file
            fcntl.flock(info_file, fcntl.LOCK_UN)

    # Delete user's private and public posts if user had posts
    if os.path.exists(cwd + '/../thought_writer/' + user_id + '.json'):
        os.remove(cwd + '/../thought_writer/' + user_id + '.json')

        with open(cwd + '/../thought_writer/public/public.json',
            'r') as public_file:
            public_posts = json.load(public_file)
            for post in public_posts:
                if post['writer'] == user_id:
                    public_posts.remove(post)

        with open(cwd + '/../thought_writer/public/public.json',
            'w') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)

    # Delete user from leaders file for Shapes in Rain
    with open(cwd + '/../shapes_in_rain/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)
        for entry in leaders:
            if entry['player'] == user_id:
                leaders.remove(entry)

    with open(cwd + '/../shapes_in_rain/leaders.json', 'w') as leaders_file:
        # Lock file to prevent overwrite
        fcntl.flock(leaders_file, fcntl.LOCK_EX)
        json.dump(leaders, leaders_file)
        # Release lock on file
        fcntl.flock(leaders_file, fcntl.LOCK_UN)

    # Delete user from leaders file for Rhythm of Life
    with open(cwd + '/../rhythm_of_life/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)
        for entry in leaders:
            if entry['player'] == user_id:
                leaders.remove(entry)

    with open(cwd + '/../rhythm_of_life/leaders.json', 'w') as leaders_file:
        # Lock file to prevent overwrite
        fcntl.flock(leaders_file, fcntl.LOCK_EX)
        json.dump(leaders, leaders_file)
        # Release lock on file
        fcntl.flock(leaders_file, fcntl.LOCK_UN)

    return make_response('Success', 200)


def verify_token():
    # Request should contain Authorization header:
    # 'Bearer <token>' <str>
    data = request.headers.get('Authorization')

    if not data:
        return make_response('Could not verify', 401,
            {'WWW-Authenticate': 'Basic realm="Login required!"'})

    token = data.split(' ')[1]

    # Check if token in Authorization header is properly formatted
    pattern = re.compile(
        r'^[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}$')

    if not pattern.match(token):
        return make_response('Token is incorrect format', 401)

    header = token.split('.')[0].encode()
    payload = json.loads(urlsafe_b64decode(token.split('.')[1]).decode())

    # Check if token is past expiration time
    if payload['exp'] < time():
        return make_response('Token expired', 401)

    signature = urlsafe_b64decode(token.split('.')[2])

    # Generate signature using secret to check against signature from Auth
    # header
    secret = os.environ['SECRET_KEY'].encode()
    message = header + b'.' + urlsafe_b64encode(json.dumps(payload).encode())
    signature_check = hmac.new(secret, message, digestmod=sha256).digest()
    if signature != signature_check:
        return make_response('Token compromised', 401)

    return make_response(json.dumps(payload).encode(), 200)


def read_users():
    # Get number of requested users from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Return list of requested number of usernames
    with open(cwd + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        usernames = [user_data['username']
            for user_data in users if user_data['status'] != 'deleted'
            ]

        return jsonify(usernames[request_start:request_end])
