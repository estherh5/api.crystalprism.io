import json
import os

from datetime import datetime, timezone
from flask import jsonify, make_response, request
from operator import itemgetter
from user import user


def add_leader():
    data = request.get_json()
    if data['status'] == 'user':
        verification = user.verify_token()
        if verification.status.split(' ')[0] != '200':
            return make_response('Could not verify', 401)
        payload = json.loads(verification.data.decode())
        player = payload['username']
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
            user_data = json.load(users_file)
            for info in user_data:
                if info['username'].lower() == player.lower():
                    plays = int(info['rhythm_plays']) + 1
                    if int(info['rhythm_high_score']) < int(data['score']):
                        score = data['score']
                        lifespan = data['lifespan']
                    else:
                        score = info['rhythm_high_score']
                        lifespan = info['rhythm_high_lifespan']
                    score_data = {'date': json.dumps(datetime.now(timezone.utc), default = user.timeconvert), 'score': data['score'], 'lifespan': data['lifespan']}
                    scores = info['rhythm_scores']
                    scores.append(score_data)
                    scores.sort(key = itemgetter('score'), reverse = True)
                    updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': plays, 'rhythm_scores': scores, 'rhythm_high_score': score, 'rhythm_high_lifespan': lifespan, 'images': info['images'], 'liked_images': info['liked_images'], 'post_number': info['post_number']}
                    user_data = [info for info in user_data if info['username'].lower() != player.lower()]
            user_data.append(updated_data)
            updated_data = user_data
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
            json.dump(updated_data, users_file)
    with open(os.path.dirname(__file__) + '/leaders.json') as leaders_file:
        content = json.load(leaders_file)
        content.append(data)
    with open(os.path.dirname(__file__) + '/leaders.json', 'w') as leaders_file:
        json.dump(content, leaders_file)
    return make_response('Success!', 200)

def get_leaders():
    with open(os.path.dirname(__file__) + '/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)
        leaders.sort(key = itemgetter('score'), reverse = True)
        return jsonify(leaders[0:5])
