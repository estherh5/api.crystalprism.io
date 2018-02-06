import fcntl
import json
import os

from base64 import decodebytes
from datetime import datetime, timezone
from flask import jsonify, make_response, request, send_file
from glob import glob

from user import user

cwd = os.path.dirname(__file__)


def create_drawing(requester):
    # Request should contain:
    # image <data:image/png;base64...>
    # title <str>
    data = request.get_json()

    # Convert username to member_id for drawing storage and increase user's
    # drawing count
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                artist_id = user_data['member_id']
                user_data['drawing_count'] += 1
                # Get current drawing number to set as drawing file name
                drawing_number = str(user_data['drawing_count'])

    # Create folder for artist's drawings if one does not already exist
    if not os.path.exists(cwd + '/drawings/' + artist_id):
        os.makedirs(cwd + '/drawings/' + artist_id)

    # Save drawing as PNG file in artist's drawings folder
    with open(cwd + '/drawings/' + artist_id + '/' + drawing_number
        + '.png', 'wb') as drawing_file:
        # Remove 'data:image/png;base64' from image data URL
        drawing = data['drawing'].split(',')[1].encode('utf-8')
        drawing_file.write(decodebytes(drawing))

    # Create folder for artist's drawing information if one does not already
    # exist
    if not os.path.exists(cwd + '/drawing_info/' + artist_id):
        os.makedirs(cwd + '/drawing_info/' + artist_id)

    # Save drawing information as JSON file in artist's drawing_info folder
    with open(cwd + '/drawing_info/' + artist_id + '/' + drawing_number
        + '.json', 'w') as info_file:
        drawing_info = {
            'title': data['title'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'likes': 0,
            'views': 0,
            'liked_users': []
            }
        json.dump(drawing_info, info_file)

    # Write changes to user file to update user's drawing count if drawing is
    # created successfully
    with open(cwd + '/../user/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response('Success', 201)


def read_drawing(artist_name, drawing_file):
    # Convert artist's username to member_id for drawing information retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist_name.lower():
                artist_id = user_data['member_id']

    # Send drawing PNG file to client
    return send_file(cwd + '/drawings/' + artist_id + '/' + drawing_file)


def read_drawing_info(artist_name, drawing_id):
    # Convert artist's username to member_id for drawing information retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist_name.lower():
                artist_id = user_data['member_id']

    # Return specified drawing information file by drawing name
    with open(cwd + '/drawing_info/' + artist_id + '/' + drawing_id
        + '.json', 'r') as info_file:
        drawing_info = json.load(info_file)

        # Replace member_id with username for each user in drawing's liked
        # users list
        for i in range(len(drawing_info['liked_users'])):
            with open(cwd + '/../user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == drawing_info['liked_users'][i]:
                        drawing_info['liked_users'][i] = user_data['username']

        return jsonify(drawing_info)

    # Return error if drawing information file not found
    return make_response('File not found', 404)


def update_drawing_info(artist_name, drawing_id):
    # Request should contain:
    # request <str; 'view', 'like', 'unlike'>
    data = request.get_json()

    # Convert artist's username to member_id for drawing retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist_name.lower():
                artist_id = user_data['member_id']

    # If request is for viewing the drawing, increase view count without
    # requiring user to be logged in
    if data['request'] == 'view':
        with open(cwd + '/drawing_info/' + artist_id + '/' + drawing_id
            + '.json', 'r') as info_file:
            drawing_info = json.load(info_file)
            # Increment drawing's views by 1
            drawing_info['views'] += 1

        with open(cwd + '/drawing_info/' + artist_id + '/' + drawing_id
            + '.json', 'w') as info_file:
            # Lock file to prevent overwrite
            fcntl.flock(info_file, fcntl.LOCK_EX)
            json.dump(drawing_info, info_file)
            # Release lock on file
            fcntl.flock(info_file, fcntl.LOCK_UN)
            return make_response('Success', 200)

        # Return error if drawing information file not found
        return make_response('File not found', 404)

    # Otherwise, request is for liking/unliking drawing, so increase/decrease
    # like count

    # Verify that user is logged in and return error status code if not
    verification = user.verify_token()
    if verification.status_code != 200:
        return verification

    # Get username from payload if user is logged in
    payload = json.loads(verification.data.decode())
    requester = payload['username']

    # Convert requester's username to member_id for liker storage
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                liker_id = user_data['member_id']

    with open(cwd + '/drawing_info/' + artist_id + '/' + drawing_id
        + '.json', 'r') as info_file:
        drawing_info = json.load(info_file)

        # Decrement drawing's likes by 1 and remove liker from the drawing's
        # liked users if the request is to unlike drawing
        if data['request'] == 'unlike':

            # Check if requester is in list of liked users for drawing to
            # prevent tampering with like count
            if liker_id in drawing_info['liked_users']:

                drawing_info['likes'] -= 1
                drawing_info['liked_users'].remove(liker_id)

                # Remove drawing from liker's liked drawings list
                with open(cwd + '/../user/users.json', 'r') as users_file:
                    users = json.load(users_file)
                    for user_data in users:
                        if user_data['member_id'] == liker_id:
                            user_data['liked_drawings'].remove(
                                artist_id + '/' + drawing_id + '.png')

                with open(cwd + '/drawing_info/' + artist_id + '/'
                    + drawing_id + '.json', 'w') as info_file:
                    # Lock file to prevent overwrite
                    fcntl.flock(info_file, fcntl.LOCK_EX)
                    json.dump(drawing_info, info_file)
                    # Release lock on file
                    fcntl.flock(info_file, fcntl.LOCK_UN)

                # Write changes to user file to update user's liked drawings
                # list if drawing is unliked successfully
                with open(cwd + '/../user/users.json', 'w') as users_file:
                    # Lock file to prevent overwrite
                    fcntl.flock(users_file, fcntl.LOCK_EX)
                    json.dump(users, users_file)
                    # Release lock on file
                    fcntl.flock(users_file, fcntl.LOCK_UN)
                    return make_response('Success', 200)

            return make_response('User did not like drawing', 400)

        # Increment drawing's likes by 1 and add liker to the drawing's liked
        # users if the request is to like drawing
        if data['request'] == 'like':

            # Ensure user is not already in list of liked users for drawing to
            # prevent tampering with like count
            if liker_id not in drawing_info['liked_users']:

                drawing_info['likes'] += 1
                drawing_info['liked_users'].insert(0, liker_id)

                # Add drawing to liker's liked drawings list
                with open(cwd + '/../user/users.json', 'r') as users_file:
                    users = json.load(users_file)
                    for user_data in users:
                        if user_data['member_id'] == liker_id:
                            user_data['liked_drawings'].insert(
                                0, artist_id + '/' + drawing_id + '.png')

                with open(cwd + '/drawing_info/' + artist_id + '/'
                    + drawing_id + '.json', 'w') as info_file:
                    # Lock file to prevent overwrite
                    fcntl.flock(info_file, fcntl.LOCK_EX)
                    json.dump(drawing_info, info_file)
                    # Release lock on file
                    fcntl.flock(info_file, fcntl.LOCK_UN)

                # Write changes to user file to update user's liked drawings
                # list if drawing is liked successfully
                with open(cwd + '/../user/users.json', 'w') as users_file:
                    # Lock file to prevent overwrite
                    fcntl.flock(users_file, fcntl.LOCK_EX)
                    json.dump(users, users_file)
                    # Release lock on file
                    fcntl.flock(users_file, fcntl.LOCK_UN)
                    return make_response('Success', 200)

            return make_response('User already liked drawing', 400)

    # Return error if drawing information file is not found
    return make_response('File not found', 404)


def read_drawings():
    # Get number of requested drawings from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Get all drawings from all artists' folders
    all_drawings = glob(cwd + '/drawings/*/*', recursive = True)

    # Sort all drawings from newest to oldest creation time
    all_drawings.sort(key = os.path.getctime, reverse = True)

    # Return requested drawings' file paths as '[artist_name]/[drawing_id].png'
    requested_drawings = []

    for drawing in all_drawings[request_start:request_end]:
        # Replace artist member_id with username
        with open(cwd + '/../user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                if user_data['member_id'] == drawing.split('/')[-2]:
                    artist_name = user_data['username']

        requested_drawings.append(artist_name + '/' + drawing.split('/')[-1])

    return jsonify(requested_drawings)


def read_drawings_for_one_user(artist_name):
    # Get number of requested drawings from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Convert artist's username to member_id for drawing retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist_name.lower():
                artist_id = user_data['member_id']

    # Get all drawings from artist's drawings folder
    all_drawings = glob(cwd + '/drawings/' + artist_id + '/*', recursive = True)

    # Sort all drawings from newest to oldest creation time
    all_drawings.sort(key = os.path.getctime, reverse = True)

    # Return requested drawings' file paths as '[artist_name]/[drawing_id].png',
    # replacing artist's member_id with username
    requested_drawings = [
        artist_name + '/' + drawing.split('/')[-1]
        for drawing in all_drawings[request_start:request_end]
        ]

    return jsonify(requested_drawings)
