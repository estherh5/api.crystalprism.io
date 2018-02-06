import fcntl
import json
import os

from datetime import datetime, timezone
from flask import jsonify, make_response, request
from operator import itemgetter

cwd = os.path.dirname(__file__)


def create_leader(requester):
    # Request should contain:
    # score <int>
    data = request.get_json()

    # Generate timestamp in UTC format to associate with score
    timestamp = datetime.now(timezone.utc).isoformat()

    # Update player's user account with score data
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                # Convert username to member_id for player storage
                player = user_data['member_id']

                # Increment number of game plays by 1
                user_data['shapes_plays'] += 1

                # Save current score as user's high score if it is higher than
                # the current high score
                if user_data['shapes_high_score'] < data['score']:
                    user_data['shapes_high_score'] = data['score']

                # Add score data to user's stored game scores and sort game
                # scores by highest to lowest
                user_data['shapes_scores'].append({
                    'timestamp': timestamp,
                    'score': data['score']
                    })

                user_data['shapes_scores'].sort(
                    key=itemgetter('score'), reverse=True)

    with open(cwd + '/../user/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    # Add score to game leaders file
    with open(cwd + '/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)
        leaders.append({
            'timestamp': timestamp,
            'score': data['score'],
            'player': player
            })

    with open(cwd + '/leaders.json', 'w') as leaders_file:
        # Lock file to prevent overwrite
        fcntl.flock(leaders_file, fcntl.LOCK_EX)
        json.dump(leaders, leaders_file)
        # Release lock on file
        fcntl.flock(leaders_file, fcntl.LOCK_UN)

    return make_response('Success', 201)


def read_leaders():
    # Get number of requested leaders from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 5))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Return requested game leaders
    with open(cwd + '/leaders.json', 'r') as leaders_file:
        leaders = json.load(leaders_file)

        # Sort game leaders by highest to lowest score
        leaders.sort(key=itemgetter('score'), reverse=True)

        # Replace each player's member_id with username
        for entry in leaders[request_start:request_end]:
            with open(cwd + '/../user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == entry['player']:
                        entry['player'] = user_data['username']

        return jsonify(leaders[request_start:request_end])
