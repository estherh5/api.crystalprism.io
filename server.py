import os

from canvashare import canvashare
from flask import Flask, request
from flask_cors import CORS
from rhythm_of_life import rhythm_of_life
from shapes_in_rain import shapes_in_rain
from thought_writer import thought_writer
from user import user

app = Flask(__name__)

# Only allow Production server access for requests coming from
# api.crystalprism.io
if os.environ['ENV_TYPE'] == 'Prod':
    prod_resource = {r"/api/*": {"origins": r"https://api.crystalprism.io"}}
    cors = CORS(app, resources = prod_resource)
elif os.environ['ENV_TYPE'] == 'Dev':
    cors = CORS(app, resources = {r"/api/*": {"origins": "*"}})
    app.config['DEBUG'] = True


@app.route('/api/canvashare/drawing', methods = ['POST'])
def drawing():
    # Post a drawing when client sends the jsonified drawing data URI in base64
    # format and drawing title in the request body and a verified bearer token
    # in the request Authorization header
    if request.method == 'POST':
        return canvashare.create_drawing()


@app.route('/api/canvashare/drawing/<artist>/<drawing_file>', methods = ['GET'])
def get_drawing(artist, drawing_file):
    # Retrieve a drawing PNG file when client sends the artist's username and
    # drawing file name (e.g., '1.png') in the request URL; no bearer token
    # needed
    if request.method == 'GET':
        return canvashare.read_drawing(artist, drawing_file)


@app.route('/api/canvashare/drawing-info/<artist>/<drawing_id>',
    methods = ['PATCH', 'GET'])
def drawing_info(artist, drawing_id):
    # Retrieve an artist's drawing's attributes when client sends the artist's
    # username and drawing file name without the extension (e.g., '1') in the
    # request URL; no bearer token needed
    if request.method == 'GET':
        return canvashare.read_drawing_info(artist, drawing_id)

    # Update a drawing's attributes when client sends the artist's username and
    # drawing file name without the extension (e.g., '1') in the request URL
    # and jsonified attribute request ('like', 'unlike', 'view') in request
    # body and verified bearer token in request Authorization header
    if request.method == 'PATCH':
        return canvashare.update_drawing_info(artist, drawing_id)


@app.route('/api/canvashare/gallery', methods = ['GET'])
def gallery():
    # Retrieve all users' drawing file paths as '[artist]/[drawing_id].png',
    # in order of newest to oldest drawings; no bearer token needed; query
    # params specify number of drawings
    if request.method == 'GET':
        return canvashare.read_all_drawings()


@app.route('/api/canvashare/gallery/<artist>', methods = ['GET'])
def user_gallery(artist):
    # Retrieve a user's drawing file paths as '[artist]/[drawing_name].png', in
    # order of newest to oldest drawings, when client sends the artist's
    # username in the request URL; no bearer token needed; query params specify
    # number of drawings
    if request.method == 'GET':
        return canvashare.read_all_user_drawings(artist)


@app.route('/api/login', methods = ['GET'])
def login_route():
    # Check if username and password in request Authorization header match
    # username and password stored for a user account and return JWT if so
    if request.method == 'GET':
        return user.login()


@app.route('/api/rhythm-of-life', methods = ['POST', 'GET'])
def rhythm_leaders():
    # Post a game score for a user when client sends the jsonified score and
    # lifespan in the request body and verified bearer token in request
    # Authorization header
    if request.method == 'POST':
        return rhythm_of_life.create_leader()

    # Retrieve all users' game scores, in order of highest to lowest score; no
    # bearer token needed; query params specify number of scores
    if request.method == 'GET':
        return rhythm_of_life.read_leaders()


@app.route('/api/shapes-in-rain', methods = ['POST', 'GET'])
def shapes_leaders():
    # Post a game score for a user when client sends the jsonified score in the
    # request body and verified bearer token in request Authorization header
    if request.method == 'POST':
        return shapes_in_rain.create_leader()

    # Retrieve all users' game scores, in order of highest to lowest score; no
    # bearer token needed; query params specify number of scores
    if request.method == 'GET':
        return shapes_in_rain.read_leaders()


@app.route('/api/thought-writer/post', methods = ['POST', 'PATCH', 'DELETE'])
def post():
    # Post a thought post when client sends the jsonified post content, title,
    # and public status ('true' or 'false') in the request body and a verified
    # bearer token in the request Authorization header
    if request.method == 'POST':
        return thought_writer.create_post()

    # Update a thought post when client sends the jsonified post content, post
    # creation timestamp (UTC), title, and public status ('true' or 'false') in
    # the request body and a verified bearer token in the request Authorization
    # header
    if request.method == 'PATCH':
        return thought_writer.update_post()

    # Delete a thought post when client sends the jsonified post creation
    # timestamp (UTC) in the request body and a verified bearer token in the
    # request Authorization header
    if request.method == 'DELETE':
        return thought_writer.delete_post()


@app.route('/api/thought-writer/post/<writer_name>/<post_timestamp>',
    methods = ['GET'])
def get_post(writer_name, post_timestamp):
    # Retrieve a user's thought post when client sends the writer's username and
    # the thought post's URI-encoded creation timestamp (UTC) in the request
    # URL; a verified bearer token must be in request Authorization header for
    # private post to be retrieved
    if request.method == 'GET':
        return thought_writer.read_post(writer_name, post_timestamp)


@app.route('/api/thought-writer/comment/<writer_name>/<post_timestamp>',
    methods = ['POST', 'PATCH', 'DELETE'])
def comment(writer_name, post_timestamp):
    # Post a comment to a thought post when client sends the post writer's
    # username and the thought post's URI-encoded creation timestamp (UTC) in
    # the request URL, the jsonified comment content in the request body, and a
    # verified bearer token in the request Authorization header
    if request.method == 'POST':
        return thought_writer.create_comment(writer_name, post_timestamp)

    # Update a comment to a thought post when client sends the post writer's
    # username and the thought post's URI-encoded creation timestamp (UTC) in
    # the request URL, the jsonified comment content and original comment
    # creation timestamp (UTC) in the request body, and a verified bearer token
    # in the request Authorization header
    if request.method == 'PATCH':
        return thought_writer.update_comment(writer_name, post_timestamp)

    # Delete a comment to a thought post when client sends the post writer's
    # username and the thought post's URI-encoded creation timestamp (UTC) in
    # the request URL, the jsonified comment creation timestamp (UTC) in the
    # request body, and a verified bearer token in request Authorization header
    if request.method == 'DELETE':
        return thought_writer.delete_comment(writer_name, post_timestamp)


@app.route('/api/thought-writer/post-board', methods = ['GET'])
def post_board():
    # Retrieve all users' public thought posts; no bearer token needed; query
    # params specify number of posts
    if request.method == 'GET':
        return thought_writer.read_all_posts()


@app.route('/api/thought-writer/post-board/<writer_name>', methods = ['GET'])
def user_post_board(writer_name):
    # Retrieve all of a single user's thought posts by specifying the writer's
    # username in the request URL; verified bearer token for the writer is
    # needed in the request Authorization header to send user's private and
    # public posts; otherwise, only public posts will be sent; query params
    # specify number of posts
    if request.method == 'GET':
        return thought_writer.read_all_user_posts(writer_name)


@app.route('/api/user', methods = ['POST', 'GET', 'PATCH', 'DELETE'])
def user_info_private():
    # Create a user account when client sends the jsonified username and
    # password in the request body
    if request.method == 'POST':
        return user.create_user()

    # Retrieve a user's complete account information when there is a verified
    # bearer token for the user in the request Authorization header
    if request.method == 'GET':
        return user.read_user()

    # Update a user's account when the client sends the jsonified account
    # updates in the request body and a verified bearer token for the user in
    # the request Authorization header
    if request.method == 'PATCH':
        return user.update_user()

    # Change a user's account status to deleted when there is a verified
    # bearer token for the user in the request Authorization header
    if request.method == 'DELETE':
        return user.delete_user()


@app.route('/api/user/<username>', methods = ['GET'])
def user_info_public(username):
    # Retrieve a user's limited account information; no bearer token needed
    if request.method == 'GET':
        return user.read_user_public(username)


@app.route('/api/user/verify', methods = ['GET'])
def verify_user_token():
    # Check if bearer token in request Authorization header is valid and
    # return the expiration time (in seconds since epoch) if so
    if request.method == 'GET':
        return user.verify_token()


@app.route('/api/users', methods = ['GET'])
def users_info():
    # Retrieve all users' usernames if there is a verified bearer token in the
    # Authorization header; query params specify number of users
    if request.method == 'GET':
        return user.read_users()
