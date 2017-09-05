import base64
import glob
import json
import os
import time

from flask import jsonify, make_response, request, send_file
from user import user


def add_drawing(painter_name, image_name):
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    painter = payload['username']
    # Get JSON image data URL in base64 format and view count
    data = request.get_json()
    # Remove 'data:image/png;base64'
    image = data['image'].split(',')[1].encode('utf-8')
    if not os.path.exists(os.path.dirname(__file__) + '/drawings/' + painter):
        os.makedirs(os.path.dirname(__file__) + '/drawings/' + painter)
    if os.path.exists(os.path.dirname(__file__) + '/drawings/' + painter + '/' + image_name + '.png'):
        same_name = image_name + '`{}'
        filename = same_name.format(int(time.time()))
    else:
        filename = image_name
    with open(os.path.dirname(__file__) + '/drawings/' + painter + '/' + filename + '.png', 'wb') as drawing_file:
        drawing_file.write(base64.decodestring(image))
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
        user_data = json.load(users_file)
        for info in user_data:
            if info['username'].lower() == painter.lower():
                images = info['images']
                images.append(painter + '/' + filename + '.png')
                updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'background_color': info['background_color'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'images': images, 'liked_images': info['liked_images'], 'post_number': info['post_number']}
                user_data = [info for info in user_data if info['username'].lower() != painter.lower()]
        user_data.append(updated_data)
        updated_data = user_data
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(updated_data, users_file)
    likes = data['likes']
    views = data['views']
    drawing_dir = {'painter': painter, 'likes': likes, 'views': views, 'liked_users': []}
    json_drawing_dir = json.dumps(drawing_dir)
    if not os.path.exists(os.path.dirname(__file__) + '/drawinginfo/' + painter):
        os.makedirs(os.path.dirname(__file__) + '/drawinginfo/' + painter)
    with open(os.path.dirname(__file__) + '/drawinginfo/' + painter + '/' + filename + '.json', 'w') as info_file:
        json.dump(json_drawing_dir, info_file)
    return make_response('Success!', 200)

def get_drawing(painter_name, image_name):
    return send_file(os.path.dirname(__file__) + '/drawings/' + painter_name + '/' + image_name)

def get_all_drawings():
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 12
    all_drawings = glob.glob(os.path.dirname(__file__) + '/drawings/*/*', recursive = True)
    all_drawings.sort(key = os.path.getctime, reverse = True)
    requested_drawings = all_drawings[request_start:request_end]
    images = [os.path.abspath(i).split('/drawings/')[1] for i in requested_drawings]
    return jsonify(images)

def get_all_user_drawings(painter_name):
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    else:
        request_start = 0
        request_end = 11
    all_drawings = glob.glob(os.path.dirname(__file__) + '/drawings/' + painter_name + '/*', recursive = True)
    all_drawings.sort(key = os.path.getctime, reverse = True)
    requested_drawings = all_drawings[request_start:request_end]
    images = [os.path.basename(i) for i in requested_drawings]
    return jsonify(images)

def update_drawing_info(painter_name, info_name):
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    liker = payload['username']
    data = request.get_json()
    likes = data['likes']
    views = data['views']
    with open(os.path.dirname(__file__) + '/drawinginfo/' + painter_name + '/' + info_name + '.json') as info_file:
        content = json.load(info_file)
        content = json.loads(content)
        painter = content['painter']
        liked_users = content['liked_users']
        if int(likes) < int(content['likes']):
            liked_users.remove(liker)
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
                user_data = json.load(users_file)
                for info in user_data:
                    if info['username'].lower() == liker.lower():
                        liked_images = info['liked_images']
                        liked_images.remove(painter_name + '/' + info_name + '.png')
                        updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'background_color': info['background_color'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'images': info['images'], 'liked_images': liked_images, 'post_number': info['post_number']}
                        user_data = [info for info in user_data if info['username'].lower() != liker.lower()]
                user_data.append(updated_data)
                updated_data = user_data
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
                json.dump(updated_data, users_file)
        if int(likes) > int(content['likes']):
            liked_users.append(liker)
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json') as users_file:
                user_data = json.load(users_file)
                for info in user_data:
                    if info['username'].lower() == liker.lower():
                        liked_images = info['liked_images']
                        liked_images.append(painter_name + '/' + info_name + '.png')
                        updated_data = {'username': info['username'], 'password': info['password'], 'salt': info['salt'], 'first_name': info['first_name'], 'last_name': info['last_name'], 'name_public': info['name_public'], 'email': info['email'], 'email_public': info['email_public'], 'background_color': info['background_color'], 'color': info['color'], 'about': info['about'], 'admin': info['admin'], 'member_since': info['member_since'], 'shapes_plays': info['shapes_plays'], 'shapes_scores': info['shapes_scores'], 'shapes_high_score': info['shapes_high_score'], 'rhythm_plays': info['rhythm_plays'], 'rhythm_scores': info['rhythm_scores'], 'rhythm_high_score': info['rhythm_high_score'], 'rhythm_high_lifespan': info['rhythm_high_lifespan'], 'images': info['images'], 'liked_images': liked_images, 'post_number': info['post_number']}
                        user_data = [info for info in user_data if info['username'].lower() != liker.lower()]
                user_data.append(updated_data)
                updated_data = user_data
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
                json.dump(updated_data, users_file)
        drawing_dir = {'painter': painter, 'likes': likes, 'views': views, 'liked_users': liked_users}
        json_drawing_dir = json.dumps(drawing_dir)
    with open(os.path.dirname(__file__) + '/drawinginfo/' + painter_name + '/' + info_name + '.json', 'w') as info_file:
        json.dump(json_drawing_dir, info_file)
        return make_response('Success!', 200)

def get_drawing_info(painter_name, info_name):
    with open(os.path.dirname(__file__) + '/drawinginfo/' + painter_name + '/' + info_name + '.json', 'r') as info_file:
        return info_file.read()
