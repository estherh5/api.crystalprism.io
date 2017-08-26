import csv
import json
import os

from flask import jsonify, make_response, request
from operator import itemgetter


def add_leader():
    data = request.get_json()
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
        return jsonify(leaders[0:4])
