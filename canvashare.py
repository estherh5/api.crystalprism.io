import base64
import glob
import json
import os
import time

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS


app = Flask(__name__)
if os.environ['ENV_TYPE'] == 'Production':
    cors = CORS(app, resources = {r"/api/*": {"origins": r"http://crystalprism.io"}})
elif os.environ['ENV_TYPE'] == 'Dev':
    cors = CORS(app, resources = {r"/api/*": {"origins": "*"}})


@app.route('/api/drawing/<image_name>', methods = ['POST', 'GET'])
def drawing(image_name):
    if request.method == 'POST':
        return add_drawing(image_name)
    if request.method == 'GET':
        return get_drawing(image_name)


@app.route('/api/gallery', methods = ['GET'])
def gallery():
    if request.method == 'GET':
        return get_all_drawings()


@app.route('/api/drawinginfo/<info_name>', methods = ['POST', 'GET'])
def drawing_info(info_name):
    if request.method == 'POST':
        return update_drawing_info(info_name)
    if request.method == 'GET':
        return get_drawing_info(info_name)


def add_drawing(image_name):
    # Get JSON image data URL in base64 format and view count
    data = request.get_json()
    # Remove 'data:image/png;base64'
    image = data['image'].split(',')[1].encode('utf-8')
    if os.path.exists(os.path.dirname(__file__) + '/drawings/' + image_name + '.png'):
        same_name = image_name + '`{}'
        filename = same_name.format(int(time.time()))
    else:
        filename = image_name
    with open(os.path.dirname(__file__) + '/drawings/' + filename + '.png', 'wb') as drawing_file:
        drawing_file.write(base64.decodestring(image))
    views = data['views']
    with open(os.path.dirname(__file__) + '/drawinginfo/' + filename + '.csv', 'w') as info_file:
        info_file.write(views)
    return "Success!"

def get_drawing(image_name):
    return send_file(os.path.dirname(__file__) + '/drawings/' + image_name)

def get_all_drawings():
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 12
    all_drawings = glob.glob(os.path.dirname(__file__) + '/drawings/*')
    all_drawings.sort(key = os.path.getctime, reverse = True)
    requested_drawings = all_drawings[request_start:request_end]
    images = [os.path.basename(i) for i in requested_drawings]
    return jsonify(images)

def update_drawing_info(info_name):
    data = request.get_json()
    views = data['views']
    with open(os.path.dirname(__file__) + '/drawinginfo/' + info_name + '.csv', 'w') as info_file:
        info_file.write(views)
    return "Success!"

def get_drawing_info(info_name):
    with open(os.path.dirname(__file__) + '/drawinginfo/' + info_name + '.csv', 'r') as info_file:
        return jsonify(info_file.read())
