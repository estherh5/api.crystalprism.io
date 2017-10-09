import base64
import glob
import json
import os
import time

from datetime import datetime, timezone
from flask import jsonify, make_response, request, send_file
from user import user


def create_drawing(artist, drawing_name):
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    # Append timestamp to drawing name if user has another drawing with that name
    if os.path.exists(os.path.dirname(__file__) + '/drawings/' + artist + '/' + drawing_name + '.png'):
        drawing_name = drawing_name + '`{}'
        drawing_name = drawing_name.format(int(time.time()))
    # Convert username to member_id for post storage and add drawing to user's created drawings
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                artist = user_data['member_id']
                user_data['created_drawings'].append(drawing_name + '.png')
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
    # Get JSON image data URL in base64 format from request
    data = request.get_json()
    # Create folder for artist's drawings if one does not already exist
    if not os.path.exists(os.path.dirname(__file__) + '/drawings/' + artist):
        os.makedirs(os.path.dirname(__file__) + '/drawings/' + artist)
    # Save drawing as PNG file in artist's drawings folder
    with open(os.path.dirname(__file__) + '/drawings/' + artist + '/' + drawing_name + '.png', 'wb') as drawing_file:
        # Remove 'data:image/png;base64' from image data URL
        drawing = data['drawing'].split(',')[1].encode('utf-8')
        drawing_file.write(base64.decodestring(drawing))
    # Create folder for artist's drawings' information if one does not already exist
    if not os.path.exists(os.path.dirname(__file__) + '/drawing_info/' + artist):
        os.makedirs(os.path.dirname(__file__) + '/drawing_info/' + artist)
    # Save drawing information as JSON file in artist's drawing_info folder
    with open(os.path.dirname(__file__) + '/drawing_info/' + artist + '/' + drawing_name + '.json', 'w') as info_file:
        drawing_info = {'timestamp': json.dumps(datetime.now(timezone.utc).isoformat(), default = user.timeconvert), 'likes': 0, 'views': 0, 'liked_users': []}
        json.dump(json.dumps(drawing_info), info_file)
    return make_response('Success!', 200)

def read_drawing(artist, drawing_name):
    # Return drawing file path as '[artist]/[drawing_name].png'
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        # Replace artist member_id with username
        for user_data in users:
            if user_data['username'].lower() == artist.lower():
                artist = user_data['member_id']
    return send_file(os.path.dirname(__file__) + '/drawings/' + artist + '/' + drawing_name)

def update_drawing_info(artist, drawing_name):
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            # Convert artist's username to member_id for drawing retrieval
            if user_data['username'].lower() == artist.lower():
                artist = user_data['member_id']
            # Convert requester's username to member_id for liker storage
            if user_data['username'].lower() == requester.lower():
                liker = user_data['member_id']
    data = request.get_json()
    with open(os.path.dirname(__file__) + '/drawing_info/' + artist + '/' + drawing_name + '.json', 'r') as info_file:
        drawing_info = json.load(info_file)
        drawing_info = json.loads(drawing_info)
        # Decrement drawing's likes by 1 and remove liker from the drawing's liked users if the request's number of likes is smaller than the drawing's current number of likes
        if int(data['likes']) < int(drawing_info['likes']):
            drawing_info['likes'] = int(drawing_info['likes']) - 1
            drawing_info['liked_users'].remove(liker)
            # Remove drawing from liker's liked drawings list
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == liker:
                        user_data['liked_drawings'].remove(artist + '/' + drawing_name + '.png')
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
                json.dump(users, users_file)
        # Increment drawing's likes by 1 and add liker to the drawing's liked users if the request's number of likes is greater than the drawing's current number of likes
        if int(data['likes']) > int(drawing_info['likes']):
            drawing_info['likes'] = int(drawing_info['likes']) + 1
            drawing_info['liked_users'].append(liker)
            # Add drawing to liker's liked drawings list
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == liker:
                        user_data['liked_drawings'].append(artist + '/' + drawing_name + '.png')
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
                json.dump(users, users_file)
        # Increment drawing's views by 1 if the request's number of views is greater than the drawing's current number of views
        if int(data['views']) > int(drawing_info['views']):
            drawing_info['views'] = int(drawing_info['views']) + 1
    with open(os.path.dirname(__file__) + '/drawing_info/' + artist + '/' + drawing_name + '.json', 'w') as info_file:
        json.dump(json.dumps(drawing_info), info_file)
        return make_response('Success!', 200)

def read_drawing_info(artist, drawing_name):
    # Convert artist's username to member_id for drawing information retrieval
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist.lower():
                artist = user_data['member_id']
    # Return specified drawing information file by drawing name
    with open(os.path.dirname(__file__) + '/drawing_info/' + artist + '/' + drawing_name + '.json', 'r') as info_file:
        drawing_info = json.load(info_file)
        drawing_info = json.loads(drawing_info)
        # Replace member_id with username for each user in drawing's liked users list
        for i in range(len(drawing_info['liked_users'])):
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == drawing_info['liked_users'][i]:
                        drawing_info['liked_users'][i] = user_data['username']
        return jsonify(json.dumps(drawing_info))

def read_all_drawings():
    # Get number of requested drawings from query parameters
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    # Set default number of retrieved drawings if not specified in query parameters
    else:
        request_start = 0
        request_end = 12
    # Get all drawings from all artist's folders
    all_drawings = glob.glob(os.path.dirname(__file__) + '/drawings/*/*', recursive = True)
    # Sort all drawings by newest to oldest creation time
    all_drawings.sort(key = os.path.getctime, reverse = True)
    # Return requested drawings' file paths as '[artist]/[drawing_name].png'
    requested_drawings = []
    for drawing in all_drawings[request_start:request_end]:
        # Replace artist member_id with username
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                if user_data['member_id'] == os.path.abspath(drawing).split('/drawings/')[1].split('/')[0]:
                    artist = user_data['username']
        requested_drawings.append(artist + '/' + os.path.abspath(drawing).split('/drawings/')[1].split('/', 1)[1])
    return jsonify(requested_drawings)

def read_all_user_drawings(artist):
    # Get number of requested drawings from query parameters
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    # Set default number of retrieved drawings if not specified in query parameters
    else:
        request_start = 0
        request_end = 11
    # Convert artist's username to member_id for drawing retrieval
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == artist.lower():
                artist_id = user_data['member_id']
    # Get all drawings from artist's drawings folder
    all_drawings = glob.glob(os.path.dirname(__file__) + '/drawings/' + artist_id + '/*', recursive = True)
    # Sort all drawings by newest to oldest creation time
    all_drawings.sort(key = os.path.getctime, reverse = True)
    # Return requested drawings' file paths as '[artist]/[drawing_name].png', replacing artist's member_id with username
    requested_drawings = [artist + os.path.abspath(drawing).split('/drawings/' + artist_id)[1] for drawing in all_drawings[request_start:request_end]]
    return jsonify(requested_drawings)
