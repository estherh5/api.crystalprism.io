import boto3
import json
import os

from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

from canvashare import canvashare
from rhythm_of_life import rhythm_of_life
from shapes_in_rain import shapes_in_rain
from thought_writer import thought_writer
from user import user

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
if os.environ['ENV_TYPE'] == 'Dev':
    app.config['DEBUG'] = True


@app.route('/api/canvashare/drawing', methods=['POST'])
def drawing():
    # Post a drawing when client sends the jsonified drawing data URI in base64
    # format and drawing title in the request body and a verified bearer token
    # in the request Authorization header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return canvashare.create_drawing(requester)


@app.route('/api/canvashare/drawing/<artist_name>/<drawing_file>',
    methods=['GET'])
def get_drawing(artist_name, drawing_file):
    # Retrieve a drawing PNG file when client sends the artist's username and
    # drawing file name (e.g., '1.png') in the request URL; no bearer token
    # needed
    if request.method == 'GET':
        return canvashare.read_drawing(artist_name, drawing_file)


@app.route('/api/canvashare/drawing-info/<artist_name>/<drawing_id>',
    methods=['GET', 'PATCH'])
def drawing_info(artist_name, drawing_id):
    # Retrieve an artist's drawing's attributes when client sends the artist's
    # username and drawing file name without the extension (e.g., '1') in the
    # request URL; no bearer token needed
    if request.method == 'GET':
        return canvashare.read_drawing_info(artist_name, drawing_id)

    # Update a drawing's attributes when client sends the artist's username and
    # drawing file name without the extension (e.g., '1') in the request URL
    # and jsonified attribute request ('like', 'unlike', 'view') in request
    # body and verified bearer token in request Authorization header if request
    # is to like/unlike drawing (not required to view drawing)
    if request.method == 'PATCH':
        return canvashare.update_drawing_info(artist_name, drawing_id)


@app.route('/api/canvashare/gallery', methods=['GET'])
def gallery():
    # Retrieve all drawing file paths as '[artist_name]/[drawing_id].png', in
    # order of newest to oldest drawings; no bearer token needed; query params
    # specify number of drawings
    if request.method == 'GET':
        return canvashare.read_drawings()


@app.route('/api/canvashare/gallery/<artist_name>', methods=['GET'])
def user_gallery(artist_name):
    # Retrieve user's drawing file paths as '[artist_name]/[drawing_name].png',
    # in order of newest to oldest drawings, when client sends the artist's
    # username in the request URL; no bearer token needed; query params specify
    # number of drawings
    if request.method == 'GET':
        return canvashare.read_drawings_for_one_user(artist_name)


@app.route('/api/login', methods=['GET'])
def login_route():
    # Check if username and password in request Authorization header match
    # username and password stored for a user account and return JWT if so
    if request.method == 'GET':
        return user.login()


@app.route('/api/photos', methods=['GET'])
def photos():
    # Retrieve URLs for photos stored on Amazon S3 crystalprism-photos bucket;
    # environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must
    # be set from AWS account; query params specify number of URLs
    if request.method == 'GET':
        # Get number of requested photos from query parameters, using default
        # if null
        request_start = int(request.args.get('start', 0))
        request_end = int(request.args.get('end', request_start + 10))

        # Return error if start query parameter is greater than end
        if request_start > request_end:
            return make_response('Start param cannot be greater than end', 400)

        urls = []

        s3 = boto3.resource('s3')
        bucket_name = os.environ['S3_BUCKET']
        bucket = s3.Bucket(bucket_name)
        bucket_folder = os.environ['S3_PHOTO_DIR']

        for item in bucket.objects.filter(Prefix=bucket_folder, Delimiter='/'):

            # Exclude bucket folder from URLs list
            if item.key != bucket_folder:
                urls.append(os.environ['S3_URL_START'] + item.key)

        return jsonify(urls[request_start:request_end])


@app.route('/api/ping', methods=['GET'])
def ping():
    # Return success response if server is up
    return make_response('Success', 200)


@app.route('/api/rhythm-of-life', methods=['POST', 'GET'])
def rhythm_leaders():
    # Post a game score for a user when client sends the jsonified score and
    # lifespan in the request body and verified bearer token in request
    # Authorization header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return rhythm_of_life.create_leader(requester)

    # Retrieve all users' game scores, in order of highest to lowest score; no
    # bearer token needed; query params specify number of scores
    if request.method == 'GET':
        return rhythm_of_life.read_leaders()


@app.route('/api/shapes-in-rain', methods=['POST', 'GET'])
def shapes_leaders():
    # Post a game score for a user when client sends the jsonified score in the
    # request body and verified bearer token in request Authorization header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return shapes_in_rain.create_leader(requester)

    # Retrieve all users' game scores, in order of highest to lowest score; no
    # bearer token needed; query params specify number of scores
    if request.method == 'GET':
        return shapes_in_rain.read_leaders()


@app.route('/api/thought-writer/post', methods=['POST', 'PATCH', 'DELETE'])
def post():
    # Post a thought post when client sends the jsonified post content, title,
    # and public status ('true' or 'false') in the request body and a verified
    # bearer token in the request Authorization header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.create_post(requester)

    # Update a thought post when client sends the jsonified post content, post
    # creation timestamp (UTC), title, and public status ('true' or 'false') in
    # the request body and a verified bearer token in the request Authorization
    # header
    if request.method == 'PATCH':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.update_post(requester)

    # Delete a thought post when client sends the jsonified post creation
    # timestamp (UTC) in the request body and a verified bearer token in the
    # request Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.delete_post(requester)


@app.route('/api/thought-writer/post/<writer_name>/<post_timestamp>',
    methods=['GET'])
def get_post(writer_name, post_timestamp):
    # Retrieve a user's thought post when client sends the writer's username
    # and the thought post's URI-encoded creation timestamp (UTC) in the
    # request URL; a verified bearer token must be in request Authorization
    # header for private post to be retrieved
    if request.method == 'GET':
        return thought_writer.read_post(writer_name, post_timestamp)


@app.route('/api/thought-writer/comment/<writer_name>/<post_timestamp>',
    methods=['POST', 'PATCH', 'DELETE'])
def comment(writer_name, post_timestamp):
    # Post a comment to a thought post when client sends the post writer's
    # username and the thought post's URI-encoded creation timestamp (UTC) in
    # the request URL, the jsonified comment content in the request body, and a
    # verified bearer token in the request Authorization header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.create_comment(requester, writer_name,
            post_timestamp)

    # Update a comment to a thought post when client sends the post writer's
    # username and the thought post's URI-encoded creation timestamp (UTC) in
    # the request URL, the jsonified comment content and original comment
    # creation timestamp (UTC) in the request body, and a verified bearer token
    # in the request Authorization header
    if request.method == 'PATCH':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.update_comment(requester, writer_name,
            post_timestamp)

    # Delete a comment to a thought post when client sends the post writer's
    # username and the thought post's URI-encoded creation timestamp (UTC) in
    # the request URL, the jsonified comment creation timestamp (UTC) in the
    # request body, and a verified bearer token in request Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.delete_comment(requester, writer_name,
            post_timestamp)


@app.route('/api/thought-writer/post-board', methods=['GET'])
def post_board():
    # Retrieve all users' public thought posts; no bearer token needed; query
    # params specify number of posts
    if request.method == 'GET':
        return thought_writer.read_posts()


@app.route('/api/thought-writer/post-board/<writer_name>', methods=['GET'])
def user_post_board(writer_name):
    # Retrieve all of a single user's thought posts by specifying the writer's
    # username in the request URL; verified bearer token for the writer is
    # needed in the request Authorization header to send user's private and
    # public posts; otherwise, only public posts will be sent; query params
    # specify number of posts
    if request.method == 'GET':
        return thought_writer.read_posts_for_one_user(writer_name)


@app.route('/api/user', methods=['POST', 'GET', 'PATCH', 'DELETE'])
def user_private():
    # Create a user account when client sends the jsonified username and
    # password in the request body
    if request.method == 'POST':
        return user.create_user()

    # Retrieve a user's complete account information when client sends verified
    # bearer token for the user in the request Authorization header
    if request.method == 'GET':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return user.read_user(requester)

    # Update a user's account when client sends the jsonified account
    # updates in the request body and a verified bearer token for the user in
    # the request Authorization header
    if request.method == 'PATCH':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return user.update_user(requester)

    # Change a user's account status to deleted when client sends a verified
    # bearer token for the user in the request Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return user.delete_user_soft(requester)


@app.route('/api/user/<username>', methods=['GET', 'DELETE'])
def user_public(username):
    # Retrieve a user's public account information; no bearer token needed
    if request.method == 'GET':
        return user.read_user_public(username)

    # Delete all of a user's account data and set status to deleted when client
    # sends a verified bearer token for the user or for an admin in the request
    # Authorization header
    if request.method == 'DELETE':
        return user.delete_user_hard(username)


@app.route('/api/user/verify', methods=['GET'])
def verify_user_token():
    # Check if bearer token in client's request Authorization header is valid
    # and return the expiration time (in seconds since epoch) if so
    if request.method == 'GET':
        return user.verify_token()


@app.route('/api/users', methods=['GET'])
def users():
    # Retrieve all users' usernames when client sends a verified bearer token
    # in the request Authorization header; query params specify number of users
    if request.method == 'GET':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        return user.read_users()
