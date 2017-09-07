import base64
import hashlib
import hmac
import json
import re

from base64 import b64decode, b64encode
from datetime import datetime, timezone
from flask import jsonify, make_response, request
from hashlib import sha256, sha512
from os import path, urandom
from time import time


def timeconvert(obj):
    if isinstance(obj, datetime):
        return obj.__str__()

def create_user():
    data = request.get_json()
    username = data['username']
    password = data['password']
    password = password.encode()
    salt = b64encode(urandom(32))
    hashed_password = sha512(salt + password).hexdigest()
    member_since = json.dumps(datetime.now(timezone.utc), default = timeconvert)
    data = {'username': username, 'password': hashed_password, 'salt': salt.decode(), 'first_name': '', 'last_name': '', 'name_public': '', 'email': '', 'email_public': '', 'background_color': '#ffffff', 'color': '#000000', 'about': '', 'admin': False, 'member_since': member_since, 'shapes_plays': 0, 'shapes_scores': [], 'shapes_high_score': 0, 'rhythm_plays': 0, 'rhythm_scores': [], 'rhythm_high_score': 0, 'rhythm_high_lifespan': '00:00:00', 'images': [], 'liked_images': [], 'post_number': 0}
    with open(path.dirname(__file__) + '/users.json') as users_file:
        content = json.load(users_file)
        for info in content:
            if info['username'].lower() == username.lower():
                return make_response('Username already exists', 400)
        content.append(data)
    with open(path.dirname(__file__) + '/users.json', 'w') as users_file:
        json.dump(content, users_file)
    return make_response('Success', 200)

def read_users():
    verification = verify_token()
    if verification.status.split(' ')[0] == '200':
        with open(path.dirname(__file__) + '/users.json', 'r') as users_file:
            content = json.load(users_file)
            data = [info['username'] for info in content]
            return jsonify(data)
    else:
        return make_response('Access denied', 403)

def read_user(user_id):
    verification = verify_token()
    if verification.status.split(' ')[0] != '200':
        with open(path.dirname(__file__) + '/users.json', 'r') as users_file:
            content = json.load(users_file)
            for info in content:
                if info['username'].lower() == user_id.lower():
                    if info['name_public'] == True:
                        name = info['first_name'] + ' ' + info['last_name']
                    else:
                        name = ''
                    if info['email_public'] == True:
                        email = info['email']
                    else:
                        email = ''
                    data = {'name': name, 'email': email, 'background_color': info['background_color'], 'color': info['color'], 'about': info['about'], 'member_since': info['member_since'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'images': info['images']}
                    return jsonify(data)
            return make_response('Username does not exist', 400)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    if verification.status.split(' ')[0] == '200' and requester == user_id:
        with open(path.dirname(__file__) + '/users.json', 'r') as users_file:
            content = json.load(users_file)
            for info in content:
                if info['username'].lower() == user_id.lower():
                    return jsonify(info)
    else:
        return make_response('Access denied', 403)

def update_user(user_id):
    verification = verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Access denied', 403)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    if requester == user_id:
        data = request.get_json()
        username = data['username']
        password = data['password']
        with open(path.dirname(__file__) + '/users.json') as users_file:
            content = json.load(users_file)
            if username.lower() != user_id.lower():
                for info in content:
                    if info['username'].lower() == username.lower():
                        return make_response('Username already exists', 400)
            for info in content:
                if info['username'].lower() == user_id.lower():
                    if password != '':
                        password = password.encode()
                        salt = b64encode(urandom(32))
                        password = sha512(salt + password).hexdigest()
                        salt = salt.decode()
                    else:
                        password = info['password']
                        salt = info['salt']
                    member_since = info['member_since']
                    images = info['images']
                    liked_images = info['liked_images']
                    post_number = info['post_number']
                    shapes_plays = info['shapes_plays']
                    shapes_scores = info['shapes_scores']
                    shapes_score = info['shapes_high_score']
                    rhythm_plays = info['rhythm_plays']
                    rhythm_scores = info['rhythm_scores']
                    rhythm_score = info['rhythm_high_score']
                    lifespan = info['rhythm_high_lifespan']
                    content = [info for info in content if info['username'].lower() != user_id.lower()]
            data = {'username': username, 'password': password, 'salt': salt, 'first_name': data['first_name'], 'last_name': data['last_name'], 'name_public': data['name_public'], 'email': data['email'], 'email_public': data['email_public'], 'background_color': data['background_color'], 'color': data['color'], 'about': data['about'], 'admin': False, 'member_since': member_since, 'shapes_plays': shapes_plays, 'shapes_scores': shapes_scores, 'shapes_high_score': shapes_score, 'rhythm_plays': rhythm_plays, 'rhythm_scores': rhythm_scores, 'rhythm_high_score': rhythm_score, 'rhythm_high_lifespan': lifespan, 'images': images, 'liked_images': liked_images, 'post_number': post_number}
            content.append(data)
            data = content
        with open(path.dirname(__file__) + '/users.json', 'w') as users_file:
            json.dump(data, users_file)
        return make_response('Success', 200)
    else:
        return make_response('Access denied', 403)

def delete_user(user_id):
    verification = verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Access denied', 403)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    if requester == user_id:
        with open(path.dirname(__file__) + '/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user in users:
                if user['username'].lower() == user_id.lower():
                    users = [user for user in users if user['username'].lower() != user_id.lower()]
        with open(path.dirname(__file__) + '/users.json', 'w') as users_file:
            json.dump(users, users_file)
        return make_response('Success', 200)
    else:
        return make_response('Access denied', 403)

def verify_token():
    data = request.headers.get('Authorization')
    if not data:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    token = data.split(' ')[1]
    pattern = re.compile(r'^[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}$')
    if not pattern.match(token):
        return make_response('Token is incorrect format', 401)
    if pattern.match(token):
        header = base64.urlsafe_b64decode(token.split('.')[0])
        payload = json.loads(base64.urlsafe_b64decode(token.split('.')[1]).decode())
        if payload['exp'] < time():
            return make_response('Token expired', 401)
        signature = base64.urlsafe_b64decode(token.split('.')[2])
        secret = b'MySecret'
        message = base64.urlsafe_b64encode(header) + b'.' + base64.urlsafe_b64encode(json.dumps(payload).encode())
        signature_check = hmac.new(secret, message, digestmod=hashlib.sha256).digest()
        if signature != signature_check:
            return make_response('Token compromised', 401)
        return make_response(json.dumps(payload).encode(), 200)
