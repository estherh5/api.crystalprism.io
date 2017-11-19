import fcntl
import json
import os

from base64 import decodestring
from datetime import datetime, timezone
from flask import jsonify, make_response, request, send_file
from glob import glob
from user import user


def create_drawing():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']

    # Convert username to member_id for post storage and increase user's
    # drawing count
    with open('user/users.json', 'r') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                artist = user_data['member_id']
                user_data['drawing_number'] += 1
                # Get current drawing number to set as drawing file name
                drawing_number = str(user_data['drawing_number'])
    with open('user/users.json', 'w') as users_file:
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    # Get JSON image data URL in base64 format from request
    data = request.get_json()

    # Create folder for artist's drawings if one does not already exist
    if not os.path.exists('canvashare/drawings/' + artist):
        os.makedirs('canvashare/drawings/' + artist)

    # Save drawing as PNG file in artist's drawings folder
    with open('canvashare/drawings/' + artist + '/' + drawing_number + '.png',
        'wb') as drawing_file:
        # Remove 'data:image/png;base64' from image data URL
        drawing = data['drawing'].split(',')[1].encode('utf-8')
        drawing_file.write(decodestring(drawing))

    # Create folder for artist's drawing information if one does not already
    # exist
    if not os.path.exists('canvashare/drawing_info/' + artist):
        os.makedirs('canvashare/drawing_info/' + artist)

    # Save drawing information as JSON file in artist's drawing_info folder
    with open('canvashare/drawing_info/' + artist + '/' + drawing_number
        + '.json', 'w') as info_file:
        drawing_info = {
            'title': data['title'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'likes': 0,
            'views': 0,
            'liked_users': []
            }
        json.dump(drawing_info, info_file)

    return make_response('Success!', 200)


def read_drawing(artist, drawing_file):
    # Return drawing file path as '[artist]/[drawing_id].png'
    with open('user/users.json', 'r') as users_file:
        users = json.load(users_file)
        # Replace artist member_id with username for drawing retrieval
        for user_data in users:
            if user_data['username'].lower() == artist.lower():
                artist = user_data['member_id']

    return send_file('canvashare/drawings/' + artist + '/'
                     + drawing_file)


def read_drawing_info(artist, drawing_id):
    # Convert artist's username to member_id for drawing information retrieval
    with open('user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist.lower():
                artist = user_data['member_id']

    # Return specified drawing information file by drawing name
    with open('canvashare/drawing_info/' + artist + '/' + drawing_id + '.json',
        'r') as info_file:
        drawing_info = json.load(info_file)
        # Replace member_id with username for each user in drawing's liked users
        # list
        for i in range(len(drawing_info['liked_users'])):
            with open('user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == drawing_info['liked_users'][i]:
                        drawing_info['liked_users'][i] = user_data['username']
        return jsonify(drawing_info)


def update_drawing_info(artist, drawing_id):
    data = request.get_json()

    # If request is for viewing the drawing, increase view count without
    # requiring user to be logged in
    if data['request'] == 'view':
        with open('user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                # Convert artist's username to member_id for drawing retrieval
                if user_data['username'].lower() == artist.lower():
                    artist = user_data['member_id']
        with open('canvashare/drawing_info/' + artist + '/' + drawing_id
            + '.json', 'r') as info_file:
            # Lock file to prevent overwrite
            fcntl.flock(info_file, fcntl.LOCK_EX)
            drawing_info = json.load(info_file)
            # Increment drawing's views by 1 if the request's number of views
            # is greater than the drawing's current number of views
            drawing_info['views'] += 1
        with open('canvashare/drawing_info/' + artist + '/' + drawing_id
            + '.json', 'w') as info_file:
            json.dump(drawing_info, info_file)
            # Release lock on file
            fcntl.flock(info_file, fcntl.LOCK_UN)
        return make_response('Success!', 200)

    # Otherwise, request is for liking/unliking drawing, so verify that user is
    # logged in first
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']

    with open('user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            # Convert artist's username to member_id for drawing retrieval
            if user_data['username'].lower() == artist.lower():
                artist = user_data['member_id']
            # Convert requester's username to member_id for liker storage
            if user_data['username'].lower() == requester.lower():
                liker = user_data['member_id']

    with open('canvashare/drawing_info/' + artist + '/' + drawing_id + '.json',
        'r') as info_file:
        # Lock file to prevent overwrite
        fcntl.flock(info_file, fcntl.LOCK_EX)
        drawing_info = json.load(info_file)

        # Decrement drawing's likes by 1 and remove liker from the drawing's
        # liked users if the request is to unlike drawing
        if data['request'] == 'unlike':
            drawing_info['likes'] -= 1
            drawing_info['liked_users'].remove(liker)
            # Remove drawing from liker's liked drawings list
            with open('user/users.json', 'r') as users_file:
                # Lock file to prevent overwrite
                fcntl.flock(users_file, fcntl.LOCK_EX)
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == liker:
                        user_data['liked_drawings'].remove(
                            artist + '/' + drawing_id + '.png')
            with open('user/users.json', 'w') as users_file:
                json.dump(users, users_file)
                # Release lock on file
                fcntl.flock(users_file, fcntl.LOCK_UN)

        # Increment drawing's likes by 1 and add liker to the drawing's liked
        # users if the request is to like drawing
        if data['request'] == 'like':
            drawing_info['likes'] += 1
            drawing_info['liked_users'].insert(0, liker)
            # Add drawing to liker's liked drawings list
            with open('user/users.json', 'r') as users_file:
                # Lock file to prevent overwrite
                fcntl.flock(users_file, fcntl.LOCK_EX)
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == liker:
                        user_data['liked_drawings'].insert(
                            0, artist + '/' + drawing_id + '.png')
            with open('user/users.json', 'w') as users_file:
                json.dump(users, users_file)
                # Release lock on file
                fcntl.flock(users_file, fcntl.LOCK_UN)

    with open('canvashare/drawing_info/' + artist + '/' + drawing_id + '.json',
        'w') as info_file:
        json.dump(drawing_info, info_file)
        # Release lock on file
        fcntl.flock(info_file, fcntl.LOCK_UN)
        return make_response('Success!', 200)


def read_all_drawings():
    # Get number of requested drawings from query parameters
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))

    # Set default number of retrieved drawings if not specified in query
    # parameters
    else:
        request_start = 0
        request_end = 9

    # Get all drawings from all artist's folders
    all_drawings = glob('canvashare/drawings/*/*', recursive = True)

    # Sort all drawings by newest to oldest creation time
    all_drawings.sort(key = os.path.getctime, reverse = True)

    # Return requested drawings' file paths as '[artist]/[drawing_id].png'
    requested_drawings = []
    for drawing in all_drawings[request_start:request_end]:
        # Replace artist member_id with username
        with open('user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                if user_data['member_id'] == drawing.split('/')[-2]:
                    artist = user_data['username']
        requested_drawings.append(artist + '/' + drawing.split('/')[-1])
    return jsonify(requested_drawings)


def read_all_user_drawings(artist):
    # Get number of requested drawings from query parameters
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))

    # Set default number of retrieved drawings if not specified in query
    # parameters
    else:
        request_start = 0
        request_end = 9

    # Convert artist's username to member_id for drawing retrieval
    with open('user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist.lower():
                artist_id = user_data['member_id']

    # Get all drawings from artist's drawings folder
    all_drawings = glob(
        'canvashare/drawings/' + artist_id + '/*', recursive = True)

    # Sort all drawings by newest to oldest creation time
    all_drawings.sort(key = os.path.getctime, reverse = True)

    # Return requested drawings' file paths as '[artist]/[drawing_id].png',
    # replacing artist's member_id with username
    requested_drawings = [
        artist + '/' + drawing.split('/')[-1]
        for drawing in all_drawings[request_start:request_end]
        ]
    return jsonify(requested_drawings)
