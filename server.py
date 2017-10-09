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
# Only allow Production server access for requests coming from api.crystalprism.io
if os.environ['ENV_TYPE'] == 'Production':
    cors = CORS(app, resources = {r"/api/*": {"origins": r"https://api.crystalprism.io"}})
elif os.environ['ENV_TYPE'] == 'Dev':
    cors = CORS(app, resources = {r"/api/*": {"origins": "*"}})


@app.route('/api/user', methods = ['POST', 'GET', 'PUT', 'DELETE'])
def user_info():
    if request.method == 'POST':
        return user.create_user()
    if request.method == 'GET':
        return user.read_user()
    if request.method == 'PUT':
        return user.update_user()
    if request.method == 'DELETE':
        return user.delete_user()


@app.route('/api/user/<username>', methods = ['GET'])
def user_info_public(username):
    if request.method == 'GET':
        return user.read_user_public(username)


@app.route('/api/user/verify', methods = ['GET'])
def verify_user_token():
    if request.method == 'GET':
        return user.verify_token()


@app.route('/api/users', methods = ['GET'])
def users_info():
    if request.method == 'GET':
        return user.read_users()


@app.route('/api/login', methods = ['GET'])
def login_route():
    if request.method == 'GET':
        data = request.authorization
        username = data.username
        password = data.password
        # Check that authorization request contains required data (header, username, password)
        if not data or not data.username or not data.password:
            return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
        with open(os.path.dirname(__file__) + '/user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                if user_data['username'].lower() == username.lower():
                    # Reject requests for logging into deleted user accounts
                    if user_data['status'] == 'deleted':
                        return make_response('Username does not exist', 400)
                    # Check requested password against stored hashed and salted password
                    salt = user_data['salt'].encode()
                    password = password.encode()
                    hashed_password = sha512(salt + password).hexdigest()
                    # Generate JWT token if password is correct
                    if user_data['password'] == hashed_password:
                        header = b'{"alg": "HS256", "typ": "JWT"}'
                        payload = json.dumps({'username': username, 'exp': math.floor(time() + (60 * 60))}).encode()
                        secret = b'MySecret'
                        message = base64.urlsafe_b64encode(header) + b'.' + base64.urlsafe_b64encode(payload)
                        signature = hmac.new(secret, message, digestmod = hashlib.sha256).digest()
                        signature = base64.urlsafe_b64encode(signature)
                        token = message + b'.' + signature
                        response = {'token': token.decode()}
                        return json.dumps(response)
                    else:
                        return make_response('Incorrect password', 400)
            return make_response('Username does not exist', 400)


@app.route('/api/canvashare/drawing/<artist>/<drawing_name>', methods = ['POST', 'GET'])
def drawing(artist, drawing_name):
    if request.method == 'POST':
        return canvashare.create_drawing(artist, drawing_name)
    if request.method == 'GET':
        return canvashare.read_drawing(artist, drawing_name)


@app.route('/api/canvashare/drawing-info/<artist>/<drawing_name>', methods = ['POST', 'GET'])
def drawing_info(artist, drawing_name):
    if request.method == 'POST':
        return canvashare.update_drawing_info(artist, drawing_name)
    if request.method == 'GET':
        return canvashare.read_drawing_info(artist, drawing_name)


@app.route('/api/canvashare/gallery', methods = ['GET'])
def gallery():
    if request.method == 'GET':
        return canvashare.read_all_drawings()


@app.route('/api/canvashare/gallery/<artist>', methods = ['GET'])
def user_gallery(artist):
    if request.method == 'GET':
        return canvashare.read_all_user_drawings(artist)


@app.route('/api/shapes-in-rain', methods = ['POST', 'GET'])
def shapes_leaders():
    if request.method == 'POST':
        return shapes_in_rain.create_leader()
    if request.method == 'GET':
        return shapes_in_rain.read_leaders()


@app.route('/api/rhythm-of-life', methods = ['POST', 'GET'])
def rhythm_leaders():
    if request.method == 'POST':
        return rhythm_of_life.create_leader()
    if request.method == 'GET':
        return rhythm_of_life.read_leaders()


@app.route('/api/thought-writer/post', methods = ['POST', 'GET', 'PUT', 'DELETE'])
def post():
    if request.method == 'POST':
        return thought_writer.create_post()
    if request.method == 'GET':
        return thought_writer.read_post()
    if request.method == 'PUT':
        return thought_writer.update_post()
    if request.method == 'DELETE':
        return thought_writer.delete_post()


@app.route('/api/thought-writer/comment', methods = ['POST', 'PUT', 'DELETE'])
def comment():
    if request.method == 'POST':
        return thought_writer.create_comment()
    if request.method == 'PUT':
        return thought_writer.update_comment()
    if request.method == 'DELETE':
        return thought_writer.delete_comment()


@app.route('/api/thought-writer/post-board', methods = ['GET'])
def post_board():
    if request.method == 'GET':
        return thought_writer.read_all_posts()


@app.route('/api/thought-writer/post-board/<writer>', methods = ['GET'])
def user_post_board(writer):
    if request.method == 'GET':
        return thought_writer.read_all_user_posts(writer)
