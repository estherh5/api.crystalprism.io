import fcntl
import json
import os

from datetime import datetime, timezone
from flask import jsonify, make_response, request
from operator import itemgetter
from user import user


def create_leader():
    data = request.get_json()
    timestamp = datetime.now(timezone.utc).isoformat()
    # Update player's user account with score data
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                # Convert username to member_id for player storage
                player = user_data['member_id']
                # Increment number of game plays by 1
                user_data['rhythm_plays'] = int(user_data['rhythm_plays']) + 1
                # Save current score as user's high score if it is higher than the current high score
                if int(user_data['rhythm_high_score']) < int(data['score']):
                    user_data['rhythm_high_score'] = data['score']
                    user_data['rhythm_high_lifespan'] = data['lifespan']
                # Add score data to user's stored game scores and sort game scores by highest to lowest
                user_data['rhythm_scores'].append({'timestamp': timestamp, 'score': data['score'], 'lifespan': data['lifespan']})
                user_data['rhythm_scores'].sort(key = itemgetter('score'), reverse = True)
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)
    # Add score to game leaders file
    with open(os.path.dirname(__file__) + '/leaders.json', 'r') as leaders_file:
        # Lock file to prevent overwrite
        fcntl.flock(leaders_file, fcntl.LOCK_EX)
        leaders = json.load(leaders_file)
        leaders.append({'timestamp': timestamp, 'score': data['score'], 'lifespan': data['lifespan'], 'player': player})
    with open(os.path.dirname(__file__) + '/leaders.json', 'w') as leaders_file:
        json.dump(leaders, leaders_file)
        # Release lock on file
        fcntl.flock(leaders_file, fcntl.LOCK_UN)
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
                    if user_data['member_id'] == entry['player']:
                        entry['player'] = user_data['username']
        return jsonify(leaders[0:5])
