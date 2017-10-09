import json
import os

from datetime import datetime, timezone
from flask import jsonify, make_response, request
from operator import itemgetter
from user import user


def create_leader():
    data = request.get_json()
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    timestamp = json.dumps(datetime.now(timezone.utc).isoformat(), default = user.timeconvert)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                # Convert username to member_id for player storage
                player = user_data['member_id']
                # Increment number of game plays by 1
                user_data['shapes_plays'] = int(user_data['shapes_plays']) + 1
                # Save current score as user's high score if it is higher than the current high score
                if int(user_data['shapes_high_score']) < int(data['score']):
                    user_data['shapes_high_score'] = data['score']
                # Add score data to user's stored game scores and sort game scores by highest to lowest
                user_data['shapes_scores'].append({'timestamp': timestamp, 'score': data['score']})
                user_data['shapes_scores'].sort(key = itemgetter('score'), reverse = True)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
    entry = {'timestamp': timestamp, 'score': data['score'], 'player': player}
    # Add score to game leaders file
    with open(os.path.dirname(__file__) + '/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)
        leaders.append(entry)
    with open(os.path.dirname(__file__) + '/leaders.json', 'w') as leaders_file:
        json.dump(leaders, leaders_file)
    return make_response('Success!', 200)

def read_leaders():
    # Return top 5 game leaders
    with open(os.path.dirname(__file__) + '/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)
        # Sort game leaders by highest to lowest score
        leaders.sort(key = itemgetter('score'), reverse = True)
        # Replace each player's member_id with username
        for entry in leaders[0:5]:
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['player'] == entry['player']:
                        entry['player'] = user_data['username']
        return jsonify(leaders[0:5])
