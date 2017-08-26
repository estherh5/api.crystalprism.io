import csv
import json
import os

from flask import jsonify, make_response, request
from operator import itemgetter


def add_entry(writer_id):
    data = request.get_json()
    if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer_id + '.json') as thoughts_file:
            content = json.load(thoughts_file)
            for entry in content:
                if entry['timestamp'] == int(request.args.get('timestamp')):
                    content = [entry for entry in content if entry['timestamp'] != int(request.args.get('timestamp'))]
            content.append(data)
            data = content
    else:
        data = [data]
    with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'w') as thoughts_file:
        json.dump(data, thoughts_file)
    return 'Success!'

def get_entry(writer_id):
    with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        print(thought_entries)
        for entry in thought_entries:
            print(int(request.args.get('timestamp')))
            if entry['timestamp'] == int(request.args.get('timestamp')):
                return jsonify(entry)
            else:
                return jsonify(thought_entries[0])

def del_entry(writer_id):
    with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as thoughts_file:
        thought_entries = json.load(thoughts_file)
        thought_entries = [entry for entry in thought_entries if entry['timestamp'] != int(request.args.get('timestamp'))]
    with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'w') as thoughts_file:
        json.dump(thought_entries, thoughts_file)
    return 'Success!'

def get_entries(writer_id):
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 10
    if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as thoughts_file:
            thought_entries = json.load(thoughts_file)
            thought_entries.sort(key = itemgetter('timestamp'), reverse = True)
            return jsonify(thought_entries[request_start:request_end])
    else:
        return make_response('No posts for this user', 400)
