import base64
import hashlib
import hmac
import json
import math
import os

from base64 import b64encode
from canvashare import canvashare
from flask import Flask, make_response, request
from flask_cors import CORS
from hashlib import sha256, sha512
from math import floor
from rhythm_of_life import rhythm_of_life
from thought_writer import thought_writer
from time import time
from user import user

app = Flask(__name__)
app.config['DEBUG'] = True
if os.environ['ENV_TYPE'] == 'Production':
    cors = CORS(app, resources = {r"/api/*": {"origins": r"https://api.crystalprism.io"}})
elif os.environ['ENV_TYPE'] == 'Dev':
    cors = CORS(app, resources = {r"/api/*": {"origins": "*"}})


@app.route('/api/user', methods = ['POST', 'GET'])
def user_route():
    if request.method == 'POST':
        return user.create_user()
    if request.method == 'GET':
        return user.read_users()


@app.route('/api/user/<user_id>', methods = ['GET', 'PUT', 'DELETE'])
def user_info(user_id):
    if request.method == 'GET':
        return user.read_user(user_id)
    if request.method == 'PUT':
        return user.update_user(user_id)
    if request.method == 'DELETE':
        return user.delete_user(user_id)


@app.route('/api/login', methods = ['GET'])
def login_route():
    if request.method == 'GET':
        data = request.authorization
        username = data.username
        password = data.password
        if not data or not data.username or not data.password:
            return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
        with open(os.path.dirname(__file__) + '/user/users.json') as users_file:
            content = json.load(users_file)
            for info in content:
                if info['username'] == username:
                    salt = info['salt'].encode()
                    password = password.encode()
                    hashed_password = sha512(salt + password).hexdigest()
                    if info['password'] == hashed_password:
                        header = b'{"alg": "HS256", "typ": "JWT"}'
                        payload = json.dumps({'username': username, 'exp': math.floor(time() + (60 * 60))}).encode()
                        secret = b'MySecret'
                        message = base64.urlsafe_b64encode(header) + b'.' + base64.urlsafe_b64encode(payload)
                        signature = hmac.new(secret, message, digestmod=hashlib.sha256).digest()
                        signature = base64.urlsafe_b64encode(signature)
                        token = message + b'.' + signature
                        response = {'token': token.decode()}
                        return json.dumps(response)
                    else:
                        return make_response('Incorrect password', 400)
            return make_response('Username does not exist', 400)


@app.route('/api/canvashare/drawing/<image_name>', methods = ['POST', 'GET'])
def drawing(image_name):
    if request.method == 'POST':
        return canvashare.add_drawing(image_name)
    if request.method == 'GET':
        return canvashare.get_drawing(image_name)


@app.route('/api/canvashare/gallery', methods = ['GET'])
def gallery():
    if request.method == 'GET':
        return canvashare.get_all_drawings()


@app.route('/api/canvashare/drawinginfo/<info_name>', methods = ['POST', 'GET'])
def drawing_info(info_name):
    if request.method == 'POST':
        return canvashare.update_drawing_info(info_name)
    if request.method == 'GET':
        return canvashare.get_drawing_info(info_name)


@app.route('/api/rhythm-of-life', methods = ['POST', 'GET'])
def leaders():
    if request.method == 'POST':
        return rhythm_of_life.add_leader()
    if request.method == 'GET':
        return rhythm_of_life.get_leaders()


@app.route('/api/thought-writer/thoughts/<writer_id>', methods = ['POST', 'GET', 'DELETE'])
def thoughts(writer_id):
    if request.method == 'POST':
        return thought_writer.add_entry(writer_id)
    if request.method == 'GET':
        return thought_writer.get_entry(writer_id)
    if request.method == 'DELETE':
        return thought_writer.del_entry(writer_id)

@app.route('/api/thought-writer/entries/<writer_id>', methods = ['GET'])
def entries(writer_id):
    if request.method == 'GET':
        return thought_writer.get_entries(writer_id)
