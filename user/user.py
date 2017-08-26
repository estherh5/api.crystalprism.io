import base64
import hashlib
import hmac
import json
import re

from base64 import b64decode, b64encode
from flask import jsonify, make_response, request
from hashlib import sha256, sha512
from os import path, urandom
from time import time


def create_user():
    data = request.get_json()
    username = data['username']
    password = data['password']
    password = password.encode()
    salt = b64encode(urandom(32))
    hashed_password = sha512(salt + password).hexdigest()
    data = {'username': username, 'password': hashed_password, 'salt': salt.decode(), 'admin': False}
    with open(path.dirname(__file__) + '/users.json') as users_file:
        content = json.load(users_file)
        for info in content:
            if info['username'] == username:
                return make_response('Username already exists', 400)
        content.append(data)
    with open(path.dirname(__file__) + '/users.json', 'w') as users_file:
        json.dump(content, users_file)
    return make_response('Success', 200)

def read_users():
    return 'read_users'

def read_user(user_id):
    return 'read_user' + ' ' + user_id

def update_user(user_id):
    return 'update_user' + ' ' + user_id

def delete_user(user_id):
    with open(path.dirname(__file__) + '/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user in users:
            if user['username'] == user_id:
                users = [user for user in users if user['username'] != user_id]
            else:
                return make_response('Username does not exist', 400)
    with open(path.dirname(__file__) + '/users.json', 'w') as users_file:
        json.dump(users, users_file)
    return make_response('Success', 200)

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
