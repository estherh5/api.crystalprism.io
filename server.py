import json
import os

from flask import Flask, make_response, request
from flask_cors import CORS

from canvashare import canvashare
from homepage import homepage
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


@app.route('/api/canvashare/drawing/<drawing_id>',
    methods=['GET', 'PATCH', 'DELETE'])
def drawing_id(drawing_id):
    # Retrieve an artist's drawing's attributes when client sends the drawing
    # id in the request URL; no bearer token needed
    if request.method == 'GET':
        return canvashare.read_drawing(drawing_id)

    # Update a drawing's view count when client sends the drawing id in the
    # request URL; no bearer token needed
    if request.method == 'PATCH':
        return canvashare.update_drawing(drawing_id)

    # Delete a drawing when client sends the drawing id in the request URL and
    # a verified bearer token for the artist in the request Authorization
    # header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return canvashare.delete_drawing(requester, drawing_id)


@app.route('/api/canvashare/drawings', methods=['GET'])
def drawings():
    # Retrieve all drawings in order of newest to oldest; no bearer token
    # needed; query params specify number of drawings
    if request.method == 'GET':
        return canvashare.read_drawings()


@app.route('/api/canvashare/drawings/<artist_name>', methods=['GET'])
def user_drawings(artist_name):
    # Retrieve user's drawings in order of newest to oldest when client sends
    # the artist's username in the request URL; no bearer token needed; query
    # params specify number of drawings
    if request.method == 'GET':
        return canvashare.read_drawings_for_one_user(artist_name)


@app.route('/api/canvashare/drawing-like', methods=['POST'])
def drawing_like():
    # Post a like for a drawing when client sends the jsonified drawing id in
    # the request body and a verified bearer token in the request Authorization
    # header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return canvashare.create_drawing_like(requester)


@app.route('/api/canvashare/drawing-like/<drawing_like_id>',
    methods=['GET', 'DELETE'])
def drawing_like_id(drawing_like_id):
    # Get information for a drawing like when client sends the drawing like id
    # in the request URL; no bearer token needed
    if request.method == 'GET':
        return canvashare.read_drawing_like(drawing_like_id)

    # Delete a like for a drawing when client sends the drawing like id in the
    # request URL and a verified bearer token for the liker in the request
    # Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return canvashare.delete_drawing_like(requester, drawing_like_id)


@app.route('/api/canvashare/drawing-likes/drawing/<drawing_id>',
    methods=['GET'])
def drawing_likes(drawing_id):
    # Get all like information for a drawing in order of newest to oldest when
    # client sends the drawing id in the request URL; no bearer token needed;
    # query params specify number of likes
    if request.method == 'GET':
        return canvashare.read_drawing_likes(drawing_id)


@app.route('/api/canvashare/drawing-likes/user/<liker_name>', methods=['GET'])
def user_drawing_likes(liker_name):
    # Get all of a user's drawing likes in order of newest to oldest when
    # client sends the liker's username in the request URL; no bearer token
    # needed; query params specify number of liked drawings
    if request.method == 'GET':
        return canvashare.read_drawing_likes_for_one_user(liker_name)


@app.route('/api/homepage/ideas', methods=['GET'])
def ideas():
    # Retrieve public posts written by webpage owner in order of newest to
    # oldest; no bearer token needed; query params specify number of posts
    if request.method == 'GET':
        return homepage.read_ideas()


@app.route('/api/homepage/photos', methods=['GET'])
def photos():
    # Retrieve URLs for photos stored on Amazon S3 crystalprism-photos bucket;
    # query params specify number of URLs; no bearer token needed
    if request.method == 'GET':
        return homepage.read_photos()


@app.route('/api/login', methods=['GET'])
def login_route():
    # Check if username and password in request Authorization header match
    # username and password stored for a user account and return JWT if so
    if request.method == 'GET':
        return user.login()


@app.route('/api/ping', methods=['GET'])
def ping():
    # Return success response if server is up
    return make_response('Success', 200)


@app.route('/api/rhythm-of-life/score', methods=['POST'])
def rhythm_score():
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

        return rhythm_of_life.create_score(requester)


@app.route('/api/rhythm-of-life/score/<score_id>', methods=['GET', 'DELETE'])
def rhythm_score_id(score_id):
    # Retrieve a user's game score when client sends the score id in the
    # request URL; no bearer token needed
    if request.method == 'GET':
        return rhythm_of_life.read_score(score_id)

    # Delete a game score for a user when client sends the score id in the
    # request URL and verified bearer token for the player in request
    # Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return rhythm_of_life.delete_score(requester, score_id)


@app.route('/api/rhythm-of-life/scores', methods=['GET'])
def rhythm_scores():
    # Retrieve all users' game scores in order of highest to lowest score; no
    # bearer token needed; query params specify number of scores
    if request.method == 'GET':
        return rhythm_of_life.read_scores()


@app.route('/api/rhythm-of-life/scores/<player_name>', methods=['GET'])
def rhythm_user_scores(player_name):
    # Retrieve a single user's game scores in order of highest to lowest score
    # when client sends the player's username in the request URL; no bearer
    # token needed; query params specify number of scores
    if request.method == 'GET':
        return rhythm_of_life.read_scores_for_one_user(player_name)


@app.route('/api/shapes-in-rain/score', methods=['POST'])
def shapes_score():
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

        return shapes_in_rain.create_score(requester)


@app.route('/api/shapes-in-rain/score/<score_id>', methods=['GET', 'DELETE'])
def shapes_score_id(score_id):
    # Retrieve a user's game score when client sends the score id in the
    # request URL; no bearer token needed
    if request.method == 'GET':
        return shapes_in_rain.read_score(score_id)

    # Delete a game score for a user when client sends the score id in the
    # request URL and verified bearer token in request Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return shapes_in_rain.delete_score(requester, score_id)


@app.route('/api/shapes-in-rain/scores', methods=['GET'])
def shapes_scores():
    # Retrieve all users' game scores in order of highest to lowest score; no
    # bearer token needed; query params specify number of scores
    if request.method == 'GET':
        return shapes_in_rain.read_scores()


@app.route('/api/shapes-in-rain/scores/<player_name>', methods=['GET'])
def shapes_user_scores(player_name):
    # Retrieve a single user's game scores in order of highest to lowest score
    # when client sends the player's username in the request URL; no bearer
    # token needed; query params specify number of scores
    if request.method == 'GET':
        return shapes_in_rain.read_scores_for_one_user(player_name)


@app.route('/api/thought-writer/post', methods=['POST'])
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


@app.route('/api/thought-writer/post/<post_id>',
    methods=['GET', 'PATCH', 'DELETE'])
def post_id(post_id):
    # Retrieve a user's thought post when client sends the post id in the
    # request URL; a verified bearer token for the writer must be in the
    # request Authorization header for private post to be retrieved
    if request.method == 'GET':
        return thought_writer.read_post(post_id)

    # Update a thought post when client sends the post id in the request URL,
    # the jsonified post content, title, and public status ('true' or 'false')
    # in the request body and a verified bearer token for the writer in the
    # request Authorization header
    if request.method == 'PATCH':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.update_post(requester, post_id)

    # Delete a thought post when client sends the post id in the request URL
    # and a verified bearer token for the writer in the request Authorization
    # header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.delete_post(requester, post_id)


@app.route('/api/thought-writer/posts', methods=['GET'])
def posts():
    # Retrieve all users' public thought posts in order of newest to oldest,
    # excluding the webpage owner's posts; no bearer token needed; query params
    # specify number of posts
    if request.method == 'GET':
        return thought_writer.read_posts()


@app.route('/api/thought-writer/posts/<writer_name>', methods=['GET'])
def user_posts(writer_name):
    # Retrieve all of a single user's thought posts in order of newest to
    # oldest by specifying the writer's username in the request URL; verified
    # bearer token for the writer is needed in the request Authorization header
    # to send user's private and public posts; otherwise, only public posts
    # will be sent; query params specify number of posts
    if request.method == 'GET':
        return thought_writer.read_posts_for_one_user(writer_name)


@app.route('/api/thought-writer/comment', methods=['POST'])
def comment():
    # Post a comment to a thought post when client sends the jsonified comment
    # content and post id in the request body and a verified bearer token in
    # the request Authorization header
    if request.method == 'POST':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.create_comment(requester)


@app.route('/api/thought-writer/comment/<comment_id>',
    methods=['GET', 'PATCH', 'DELETE'])
def comment_id(comment_id):
    # Retrieve a comment to a thought post when client sends the comment id in
    # the request URL; no bearer token needed
    if request.method == 'GET':
        return thought_writer.read_comment(comment_id)

    # Update a comment to a thought post when client sends the comment id in
    # the request URL, the jsonified comment content in the request body, and a
    # verified bearer token for the commenter in the request Authorization
    # header
    if request.method == 'PATCH':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.update_comment(requester, comment_id)

    # Delete a comment to a thought post when client sends the comment id in
    # the request URL and a verified bearer token for the commenter in the
    # request Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return thought_writer.delete_comment(requester, comment_id)


@app.route('/api/thought-writer/comments/post/<post_id>', methods=['GET'])
def comments(post_id):
    # Retrieve all comments to a thought post in order of newest to oldest by
    # specifying the post id in the request URL; no bearer token needed; query
    # params specify number of comments
    if request.method == 'GET':
        return thought_writer.read_comments(post_id)


@app.route('/api/thought-writer/comments/user/<commenter_name>',
    methods=['GET'])
def user_comments(commenter_name):
    # Retrieve all of a single user's comments in order of newest to oldest by
    # specifying the commenter's username in the request URL; no bearer token
    # needed; query params specify number of comments
    if request.method == 'GET':
        return thought_writer.read_comments_for_one_user(commenter_name)


@app.route('/api/user', methods=['POST'])
def user_account():
    # Create a user account when client sends the jsonified username and
    # password in the request body
    if request.method == 'POST':
        return user.create_user()


@app.route('/api/user/<username>', methods=['GET', 'PATCH', 'DELETE'])
def user_account_id(username):
    # Retrieve a user's account information; complete information will be sent
    # if client sends verified bearer token for the user in the request
    # Authorization header; otherwise, only public information will be sent
    if request.method == 'GET':
        return user.read_user(username)

    # Update a user's account when client sends the jsonified account updates
    # in the request body and a verified bearer token for the user in the
    # request Authorization header
    if request.method == 'PATCH':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        # Return error if requester is not the user
        if requester.lower() != username.lower():
            return make_response('Unauthorized', 401)

        return user.update_user(requester)

    # Change a user's account status to deleted (while keeping his/her data
    # intact) when client sends a verified bearer token for the user in the
    # request Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        # Return error if requester is not the user
        if requester.lower() != username.lower():
            return make_response('Unauthorized', 401)

        return user.delete_user_soft(requester)


@app.route('/api/user/data/<username>', methods=['GET', 'DELETE'])
def user_account_data(username):
    # Send all of a user's data (drawings, posts, etc.) in a downloadable zip
    # file when client sends a verified bearer token for the user in the
    # request Authorization header
    if request.method == 'GET':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        # Return error if requester is not the user
        if requester.lower() != username.lower():
            return make_response('Unauthorized', 401)

        return user.read_user_data(requester)

    # Delete all of a user's data and set status to deleted when client sends a
    # verified bearer token for the user or for an admin in the request
    # Authorization header
    if request.method == 'DELETE':
        # Verify that user is logged in and return error status code if not
        verification = user.verify_token()
        if verification.status_code != 200:
            return verification

        # Get username from payload if user is logged in
        payload = json.loads(verification.data.decode())
        requester = payload['username']

        return user.delete_user_hard(requester, username)


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
