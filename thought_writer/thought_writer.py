import csv
import json
import os

from datetime import datetime, timezone
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
    title = data['title']
    timestamp = json.dumps(datetime.now(timezone.utc), default = user.timeconvert)
    content = data['content']
    public = data['public']
    new_entry = {'writer': writer, 'title': title, 'timestamp': timestamp, 'content': content, 'public': public, 'comments': []}
    if public == 'true':
        with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
            public_content = json.load(public_file)
            public_content.append(new_entry)
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_content, public_file)
    if os.path.exists(os.path.dirname(__file__) + '/' + writer + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer + '.json') as thoughts_file:
            content = json.load(thoughts_file)
            content.append(new_entry)
    else:
        content = [new_entry]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(content, thoughts_file)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
        user_data = json.load(users_file)
        for info in user_data:
            if info['username'].lower() == writer.lower():
                posts = int(info['post_number']) + 1
                updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'background_color': info['background_color'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'drawings': info['drawings'], 'liked_drawings': info['liked_drawings'], 'post_number': posts}
                user_data = [info for info in user_data if info['username'].lower() != writer.lower()]
        user_data.append(updated_data)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(user_data, users_file)
    return make_response(timestamp, 200)

def update_entry():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    writer = payload['username']
    data = request.get_json()
    if data['public'] == 'true':
        with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
            public_content = json.load(public_file)
            public_content = [entry for entry in public_content if not (entry['writer'] == writer and entry['timestamp'] == request.args.get('timestamp'))]
            public_content.append(data)
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_content, public_file)
    if data['public'] == 'false':
        with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
            public_content = json.load(public_file)
            public_content = [entry for entry in public_content if not (entry['writer'] == writer and entry['timestamp'] == request.args.get('timestamp'))]
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_content, public_file)
    if os.path.exists(os.path.dirname(__file__) + '/' + writer + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer + '.json') as thoughts_file:
            content = json.load(thoughts_file)
            content = [entry for entry in content if entry['timestamp'] != request.args.get('timestamp')]
            content.append(data)
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(content, thoughts_file)
    return make_response('Success', 200)

def del_entry():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    writer = payload['username']
    with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
        public_content = json.load(public_file)
        public_content = [entry for entry in public_content if not (entry['writer'] == writer and entry['timestamp'] == request.args.get('timestamp'))]
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_content, public_file)
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        thought_entries = [entry for entry in thought_entries if entry['timestamp'] != request.args.get('timestamp')]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(thought_entries, thoughts_file)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
        user_data = json.load(users_file)
        for info in user_data:
            if info['username'].lower() == writer.lower():
                posts = int(info['post_number']) - 1
                updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'background_color': info['background_color'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'drawings': info['drawings'], 'liked_drawings': info['liked_drawings'], 'post_number': posts}
                user_data = [info for info in user_data if info['username'].lower() != writer.lower()]
        user_data.append(updated_data)
        updated_data = user_data
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(updated_data, users_file)
    return make_response('Success', 200)

def get_entry(writer_id, timestamp):
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
            public_content = json.load(public_file)
            for entry in public_content:
                if entry['writer'] == writer_id and entry['timestamp'] == timestamp:
                    return jsonify(entry)
    elif verification.status.split(' ')[0] == '200':
        payload = json.loads(verification.data.decode())
        requester = payload['username']
        if requester == writer_id:
            with open(os.path.dirname(__file__) + '/' + requester + '.json', 'r') as thoughts_file:
                thought_entries = json.load(thoughts_file)
                for entry in thought_entries:
                    if entry['timestamp'] == timestamp:
                        return jsonify(entry)
    else:
        return make_response('No post found', 404)

def add_comment():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    commenter = payload['username']
    data = request.get_json()
    timestamp = json.dumps(datetime.now(timezone.utc), default = user.timeconvert)
    comment = {'commenter': commenter, 'timestamp': timestamp, 'content': data['content']}
    with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
        public_content = json.load(public_file)
        for entry in public_content:
            if entry['timestamp'] == request.args.get('timestamp'):
                writer = entry['writer']
                comments = entry['comments']
                comments.append(comment)
                updated_entry = {'writer': entry['writer'], 'title': entry['title'], 'timestamp': entry['timestamp'], 'content': entry['content'], 'public': entry['public'], 'comments': comments}
        public_content = [entry for entry in public_content if not (entry['timestamp'] == request.args.get('timestamp'))]
        public_content.append(updated_entry)
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_content, public_file)
    with open(os.path.dirname(__file__) + '/' + writer + '.json') as thoughts_file:
        content = json.load(thoughts_file)
        for entry in content:
            if entry['timestamp'] == request.args.get('timestamp'):
                comments = entry['comments']
                comments.append(comment)
                updated_entry = {'writer': entry['writer'], 'title': entry['title'], 'timestamp': entry['timestamp'], 'content': entry['content'], 'public': entry['public'], 'comments': comments}
        content = [entry for entry in content if not (entry['timestamp'] == request.args.get('timestamp'))]
        content.append(updated_entry)
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(content, thoughts_file)
    return make_response('Success', 200)

def update_comment():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    commenter = payload['username']
    data = request.get_json()
    old_timestamp = data['timestamp']
    new_timestamp = json.dumps(datetime.now(timezone.utc), default = user.timeconvert)
    comment = {'commenter': commenter, 'timestamp': new_timestamp, 'content': data['content']}
    with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
        public_content = json.load(public_file)
        for entry in public_content:
            if entry['timestamp'] == request.args.get('timestamp'):
                updated_comments = [comment for comment in entry['comments'] if not (comment['writer'] == commenter and comment['timestamp'] == old_timestamp)]
                updated_comments.append(comment)
                updated_entry = {'writer': entry['writer'], 'title': entry['title'], 'timestamp': entry['timestamp'], 'content': entry['content'], 'public': entry['public'], 'comments': updated_comments}
        public_content = [entry for entry in public_content if not (entry['timestamp'] == request.args.get('timestamp'))]
        public_content.append(updated_entry)
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_content, public_file)
    with open(os.path.dirname(__file__) + '/' + writer + '.json') as thoughts_file:
        content = json.load(thoughts_file)
        for entry in content:
            if entry['timestamp'] == request.args.get('timestamp'):
                updated_comments = [comment for comment in entry['comments'] if not (comment['writer'] == commenter and comment['timestamp'] == old_timestamp)]
                updated_comments.append(comment)
                updated_entry = {'writer': entry['writer'], 'title': entry['title'], 'timestamp': entry['timestamp'], 'content': entry['content'], 'public': entry['public'], 'comments': updated_comments}
        content = [entry for entry in content if not (entry['timestamp'] == request.args.get('timestamp'))]
        content.append(updated_entry)
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(content, thoughts_file)
    return make_response('Success', 200)

def del_comment():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    commenter = payload['username']
    data = request.get_json()
    comment_timestamp = data['timestamp']
    with open(os.path.dirname(__file__) + '/public/public.json') as public_file:
        public_content = json.load(public_file)
        for entry in public_content:
            if entry['timestamp'] == request.args.get('timestamp'):
                updated_comments = [comment for comment in entry['comments'] if not (comment['writer'] == commenter and comment['timestamp'] == comment_timestamp)]
                updated_entry = {'writer': entry['writer'], 'title': entry['title'], 'timestamp': entry['timestamp'], 'content': entry['content'], 'public': entry['public'], 'comments': updated_comments}
        public_content = [entry for entry in public_content if not (entry['timestamp'] == request.args.get('timestamp'))]
        public_content.append(updated_entry)
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_content, public_file)
    with open(os.path.dirname(__file__) + '/' + writer + '.json') as thoughts_file:
        content = json.load(thoughts_file)
        for entry in content:
            if entry['timestamp'] == request.args.get('timestamp'):
                updated_comments = [comment for comment in entry['comments'] if not (comment['writer'] == commenter and comment['timestamp'] == comment_timestamp)]
                updated_entry = {'writer': entry['writer'], 'title': entry['title'], 'timestamp': entry['timestamp'], 'content': entry['content'], 'public': entry['public'], 'comments': updated_comments}
        content = [entry for entry in content if not (entry['timestamp'] == request.args.get('timestamp'))]
        content.append(updated_entry)
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as thoughts_file:
        json.dump(content, thoughts_file)
    return make_response('Success', 200)

def get_all_entries():
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 10
    with open(os.path.dirname(__file__) + '/public/public.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
        return jsonify(thought_entries[request_start:request_end])

def get_all_user_entries(writer_id):
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 10
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
            with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as thoughts_file:
                thought_entries = json.load(thoughts_file)
                thought_entries = [entry for entry in thought_entries if entry['public'] == 'true']
                thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
                return jsonify(thought_entries[request_start:request_end])
        else:
            return make_response('No posts for this user', 400)
    else:
        payload = json.loads(verification.data.decode())
        requester = payload['username']
        if requester == writer_id:
            if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
                with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as thoughts_file:
                    thought_entries = json.load(thoughts_file)
                    thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
                    return jsonify(thought_entries[request_start:request_end])
            else:
                return make_response('No posts for this user', 400)
        else:
            if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
                with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as thoughts_file:
                    thought_entries = json.load(thoughts_file)
                    thought_entries = [entry for entry in thought_entries if entry['public'] == 'true']
                    thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
                    return jsonify(thought_entries[request_start:request_end])
            else:
                return make_response('No posts for this user', 400)
