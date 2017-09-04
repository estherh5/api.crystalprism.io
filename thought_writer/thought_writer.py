import csv
import json
import os

from flask import jsonify, make_response, request
from operator import itemgetter
from user import user


def add_entry():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    writer = payload['username']
    data = request.get_json()
    if os.path.exists(os.path.dirname(__file__) + '/' + writer + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer + '.json') as thoughts_file:
            content = json.load(thoughts_file)
            for entry in content:
                if entry['timestamp'] == int(request.args.get('timestamp')):
                    content = [entry for entry in content if entry['timestamp'] != int(request.args.get('timestamp'))]
            content.append(data)
            data = content
    else:
        data = [data]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(data, thoughts_file)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
        user_data = json.load(users_file)
        for info in user_data:
            if info['username'].lower() == writer.lower():
                posts = int(info['post_number']) + 1
                updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'images': info['images'], 'liked_images': info['liked_images'], 'post_number': posts}
                user_data = [info for info in user_data if info['username'].lower() != writer.lower()]
        user_data.append(updated_data)
        updated_data = user_data
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(updated_data, users_file)
    return make_response('Success', 200)

def get_entry():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    writer = payload['username']
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        for entry in thought_entries:
            if entry['timestamp'] == int(request.args.get('timestamp')):
                return jsonify(entry)
            else:
                return jsonify(thought_entries[0])

def del_entry():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    writer = payload['username']
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        thought_entries = [entry for entry in thought_entries if entry['timestamp'] != int(request.args.get('timestamp'))]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(thought_entries, thoughts_file)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
        user_data = json.load(users_file)
        for info in user_data:
            if info['username'].lower() == writer.lower():
                posts = int(info['post_number']) - 1
                updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'images': info['images'], 'liked_images': info['liked_images'], 'post_number': posts}
                user_data = [info for info in user_data if info['username'].lower() != writer.lower()]
        user_data.append(updated_data)
        updated_data = user_data
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(updated_data, users_file)
    return make_response('Success', 200)

def get_entries():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    writer = payload['username']
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 10
    if os.path.exists(os.path.dirname(__file__) + '/' + writer + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as thoughts_file:
            thought_entries = json.load(thoughts_file)
            thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
            return jsonify(thought_entries[request_start:request_end])
    else:
        return make_response('No posts for this user', 400)

def get_esther_entries():
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 10
    with open(os.path.dirname(__file__) + '/esther.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
        return jsonify(thought_entries[request_start:request_end])
