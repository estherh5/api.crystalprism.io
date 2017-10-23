import base64
import hashlib
import hmac
import json
import math
import os
import re
import uuid

from base64 import b64decode, b64encode
from datetime import datetime, timezone
from flask import jsonify, make_response, request
from hashlib import sha256, sha512
from time import time


def create_user():
    data = request.get_json()
    username = data['username']
    with open(os.path.dirname(__file__) + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        # Check if username already exists
        for user_data in users:
            if user_data['username'].lower() == username.lower():
                return make_response('Username already exists', 400)
        # Generate random UUID as non-client-facing user identifier
        member_id = str(uuid.uuid4())
        password = data['password'].encode()
        # Generate salt using CSPRNG (32 random alphanumeric characters)
        salt = b64encode(os.urandom(32))
        # Hash password with SHA512 cryptographic hash function
        hashed_password = sha512(salt + password).hexdigest()
        entry = {'member_id': member_id, 'status': 'active', 'username': username, 'password': hashed_password, 'salt': salt.decode(), 'admin': False, 'member_since': datetime.now(timezone.utc).isoformat(), 'first_name': '', 'last_name': '', 'name_public': False, 'email': '', 'email_public': False, 'background_color': '#ffffff', 'icon_color': '#000000', 'about': '', 'shapes_plays': 0, 'shapes_scores': [], 'shapes_high_score': 0, 'rhythm_plays': 0, 'rhythm_scores': [], 'rhythm_high_score': 0, 'rhythm_high_lifespan': '00:00:00', 'drawing_number': 0, 'liked_drawings': [], 'post_number': 0, 'comment_number': 0}
        users.append(entry)
    with open(os.path.dirname(__file__) + '/users.json', 'w') as users_file:
        json.dump(users, users_file)
    return make_response('Success', 200)

def read_user():
    verification = verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Access denied', 403)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    with open(os.path.dirname(__file__) + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                # Replace artist member_id with username for each drawing the user liked
                for i in range(len(user_data['liked_drawings'])):
                    for artist in users:
                        if artist['member_id'] == user_data['liked_drawings'][i].split('/', 1)[0]:
                            user_data['liked_drawings'][i] = str(artist['username'] + '/' + user_data['liked_drawings'][i].split('/', 1)[1])
                return jsonify(user_data)

def update_user():
    verification = verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Access denied', 403)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    data = request.get_json()
    username = data['username']
    password = data['password']
    with open(os.path.dirname(__file__) + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        # Check if username already exists if user requests to update it
        if username.lower() != requester.lower():
            for user_data in users:
                if user_data['username'].lower() == username.lower():
                    return make_response('Username already exists', 400)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                user_data['username'] = username
                if password != '':
                    password = password.encode()
                    salt = b64encode(os.urandom(32))
                    user_data['password'] = sha512(salt + password).hexdigest()
                    user_data['salt'] = salt.decode()
                user_data['first_name'] = data['first_name']
                user_data['last_name'] = data['last_name']
                user_data['name_public'] = data['name_public']
                user_data['email'] = data['email']
                user_data['email_public'] = data['email_public']
                user_data['background_color'] = data['background_color']
                user_data['icon_color'] = data['icon_color']
                user_data['about'] = data['about']
            # Update bearer token if user requests username update
            if username.lower() != requester.lower():
                header = b'{"alg": "HS256", "typ": "JWT"}'
                payload = json.dumps({'username': username, 'exp': math.floor(time() + (60 * 60))}).encode()
                secret = b'MySecret'
                message = base64.urlsafe_b64encode(header) + b'.' + base64.urlsafe_b64encode(payload)
                signature = hmac.new(secret, message, digestmod = hashlib.sha256).digest()
                signature = base64.urlsafe_b64encode(signature)
                token = message + b'.' + signature
                response = token.decode()
            else:
                response = 'Success'
    with open(os.path.dirname(__file__) + '/users.json', 'w') as users_file:
        json.dump(users, users_file)
    return make_response(response, 200)

def delete_user():
    verification = verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Access denied', 403)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    with open(os.path.dirname(__file__) + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                user_data['status'] = 'deleted'
    with open(os.path.dirname(__file__) + '/users.json', 'w') as users_file:
        json.dump(users, users_file)
    return make_response('Success', 200)

def read_user_public(username):
    with open(os.path.dirname(__file__) + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == username.lower():
                if user_data['status'] == 'deleted':
                    return make_response('Username does not exist', 400)
                if user_data['name_public'] == True:
                    name = user_data['first_name'] + ' ' + user_data['last_name']
                else:
                    name = ''
                if user_data['email_public'] == True:
                    email = user_data['email']
                else:
                    email = ''
                data = {'name': name, 'email': email, 'background_color': user_data['background_color'], 'icon_color': user_data['icon_color'], 'about': user_data['about'], 'member_since': user_data['member_since'], 'shapes_high_score': user_data['shapes_high_score'], 'rhythm_high_lifespan': user_data['rhythm_high_lifespan'], 'drawing_number': user_data['drawing_number'], 'post_number': user_data['post_number'], 'comment_number': user_data['comment_number']}
                return jsonify(data)
        return make_response('Username does not exist', 400)

def verify_token():
    data = request.headers.get('Authorization')
    if not data:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    token = data.split(' ')[1]
    # Check if token in Authorization header is properly formatted
    pattern = re.compile(r'^[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}$')
    if not pattern.match(token):
        return make_response('Token is incorrect format', 401)
    header = base64.urlsafe_b64decode(token.split('.')[0])
    payload = json.loads(base64.urlsafe_b64decode(token.split('.')[1]).decode())
    # Check if token is past expiration time
    if payload['exp'] < time():
        return make_response('Token expired', 401)
    signature = base64.urlsafe_b64decode(token.split('.')[2])
    # Generate signature using secret to check against signature from Auth header
    secret = b'MySecret'
    message = base64.urlsafe_b64encode(header) + b'.' + base64.urlsafe_b64encode(json.dumps(payload).encode())
    signature_check = hmac.new(secret, message, digestmod = hashlib.sha256).digest()
    if signature != signature_check:
        return make_response('Token compromised', 401)
    return make_response(json.dumps(payload).encode(), 200)

def read_users():
    verification = verify_token()
    # Return list of usernames for logged-in user
    if verification.status.split(' ')[0] == '200':
        with open(os.path.dirname(__file__) + '/users.json', 'r') as users_file:
            users = json.load(users_file)
            usernames = [user_data['username'] for user_data in users]
            return jsonify(usernames)
    else:
        return make_response('Access denied', 403)
