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
from shapes_in_rain import shapes_in_rain
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


@app.route('/api/user/verify', methods = ['GET'])
def verify_user_token():
    if request.method == 'GET':
        return user.verify_token()


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
                if info['username'].lower() == username.lower():
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


@app.route('/api/canvashare/drawing/<painter_name>/<image_name>', methods = ['POST', 'GET'])
def drawing(painter_name, image_name):
    if request.method == 'POST':
        return canvashare.add_drawing(painter_name, image_name)
    if request.method == 'GET':
        return canvashare.get_drawing(painter_name, image_name)


@app.route('/api/canvashare/gallery', methods = ['GET'])
def gallery():
    if request.method == 'GET':
        return canvashare.get_all_drawings()


@app.route('/api/canvashare/gallery/<painter_name>', methods = ['GET'])
def user_gallery(painter_name):
    if request.method == 'GET':
        return canvashare.get_all_user_drawings(painter_name)


@app.route('/api/canvashare/drawinginfo/<painter_name>/<info_name>', methods = ['POST', 'GET'])
def drawing_info(painter_name, info_name):
    if request.method == 'POST':
        return canvashare.update_drawing_info(painter_name, info_name)
    if request.method == 'GET':
        return canvashare.get_drawing_info(painter_name, info_name)


@app.route('/api/shapes-in-rain', methods = ['POST', 'GET'])
def shapes_leaders():
    if request.method == 'POST':
        return shapes_in_rain.add_leader()
    if request.method == 'GET':
        return shapes_in_rain.get_leaders()


@app.route('/api/rhythm-of-life', methods = ['POST', 'GET'])
def rhythm_leaders():
    if request.method == 'POST':
        return rhythm_of_life.add_leader()
    if request.method == 'GET':
        return rhythm_of_life.get_leaders()


@app.route('/api/thought-writer/thoughts', methods = ['POST', 'GET', 'DELETE'])
def thoughts():
    if request.method == 'POST':
        return thought_writer.add_entry()
    if request.method == 'GET':
        return thought_writer.get_entry()
    if request.method == 'DELETE':
        return thought_writer.del_entry()


@app.route('/api/thought-writer/entries/<writer_id>', methods = ['GET'])
def entries(writer_id):
    if request.method == 'GET':
        return thought_writer.get_entries(writer_id)
