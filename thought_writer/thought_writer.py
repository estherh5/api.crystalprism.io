import fcntl
import json
import os

from datetime import datetime, timezone
from flask import jsonify, make_response, request
from operator import itemgetter
from user import user


def create_post():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    # Convert username to member_id for post storage and increase post count
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                writer = user_data['member_id']
                user_data['post_number'] = int(user_data['post_number']) + 1
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)
    data = request.get_json()
    timestamp = datetime.now(timezone.utc).isoformat()
    post = {'title': data['title'], 'timestamp': timestamp, 'content': data['content'], 'public': data['public'], 'comments': []}
    # Add post to private user file if it exists or generate new file for first-time posting
    if os.path.exists(os.path.dirname(__file__) + '/' + writer + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as private_file:
            # Lock file to prevent overwrite
            fcntl.flock(private_file, fcntl.LOCK_EX)
            private_posts = json.load(private_file)
            private_posts.append(post)
    else:
        private_posts = [post]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as private_file:
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)
    # Add post to public file if marked as public
    if data['public'] == True:
        post = {'writer': writer, 'title': data['title'], 'timestamp': timestamp, 'content': data['content'], 'comments': []}
        with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            public_posts = json.load(public_file)
            public_posts.append(post)
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)
    return make_response(timestamp, 200)

def update_post():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    # Convert username to member_id for post retrieval
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                writer = user_data['member_id']
    data = request.get_json()
    # Update post in user's private file
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        private_posts = json.load(private_file)
        for post in private_posts:
            if post['timestamp'] == data['timestamp']:
                # Get post's previous public status to see if status has changed in update
                previously_public = post['public']
                post['title'] = data['title']
                post['content'] = data['content']
                post['public'] = data['public']
                # Get post's current comments to add to public file if post is newly public
                comments = post['comments']
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as private_file:
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)
    # Update post in public file if public
    if data['public'] == True:
        with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            public_posts = json.load(public_file)
            # Update post in public file if it was already public
            if previously_public == True:
                for post in public_posts:
                    if post['writer'] == writer and post['timestamp'] == data['timestamp']:
                        post['title'] = data['title']
                        post['content'] = data['content']
            # Add post to public file if it was not public previously
            else:
                post = {'writer': writer, 'title': data['title'], 'timestamp': data['timestamp'], 'content': data['content'], 'comments': comments}
                public_posts.append(post)
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)
    # Remove post from public file if it was previously public but is now private
    if data['public'] == False and previously_public == True:
        with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            public_posts = json.load(public_file)
            public_posts = [post for post in public_posts if not (post['writer'] == writer and post['timestamp'] == data['timestamp'])]
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)
    return make_response('Success', 200)

def delete_post():
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    # Convert username to member_id for post retrieval and decrease post count
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                writer = user_data['member_id']
                user_data['post_number'] = int(user_data['post_number']) - 1
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)
    data = request.get_json()
    # Remove post from user's private file
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        private_posts = json.load(private_file)
        # Get post's public status to see if it should also be removed from public file
        for post in private_posts:
            if post['timestamp'] == data['timestamp']:
                public = post['public']
        private_posts = [post for post in private_posts if post['timestamp'] != data['timestamp']]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as private_file:
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)
    # Remove post from public file if it is public
    if public == True:
        with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            public_posts = json.load(public_file)
            public_posts = [post for post in public_posts if not (post['writer'] == writer and post['timestamp'] == data['timestamp'])]
        with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)
    return make_response('Success', 200)

def read_post(writer_name, post_timestamp):
    verification = user.verify_token()
    # Retrieve post from private user file if user token is verified
    if verification.status.split(' ')[0] == '200':
        payload = json.loads(verification.data.decode())
        requester = payload['username']
        # Convert username to member_id for post retrieval
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                if user_data['username'].lower() == requester.lower():
                    writer_id = user_data['member_id']
        # Replace member_id with commenter's username for each retrieved post's comments
        with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as private_file:
            private_posts = json.load(private_file)
            for post in private_posts:
                if post['timestamp'] == post_timestamp:
                    for comment in post['comments']:
                        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                            users = json.load(users_file)
                            for user_data in users:
                                if user_data['member_id'] == comment['commenter']:
                                    comment['commenter'] = user_data['username']
                    return jsonify(post)
    # Retrieve post from public file if user token is not verified
    else:
        # Convert username to member_id for post retrieval
        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
            users = json.load(users_file)
            for user_data in users:
                if user_data['username'].lower() == writer_name.lower():
                    writer_id = user_data['member_id']
        # Replace member_ids with writer's username and with commenter's username for each retrieved post's comments
        with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
            public_posts = json.load(public_file)
            for post in public_posts:
                if post['writer'] == writer_id and post['timestamp'] == post_timestamp:
                    post['writer'] = writer_name
                    for comment in post['comments']:
                        with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                            users = json.load(users_file)
                            for user_data in users:
                                if user_data['member_id'] == comment['commenter']:
                                    comment['commenter'] = user_data['username']
                    return jsonify(post)
    return make_response('No post found', 404)

def create_comment(writer_name, post_timestamp):
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
            # Convert requester's username to member_id for comment storage and increase comment number
            if user_data['username'].lower() == requester.lower():
                commenter = user_data['member_id']
                user_data['comment_number'] = int(user_data['comment_number']) + 1
            # Convert writer's username to member_id for post retrieval
            if user_data['username'].lower() == writer_name.lower():
                writer = user_data['member_id']
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)
    data = request.get_json()
    timestamp = datetime.now(timezone.utc).isoformat()
    comment = {'commenter': commenter, 'timestamp': timestamp, 'content': data['content']}
    # Add comment to post's entry in public file
    with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
        # Lock file to prevent overwrite
        fcntl.flock(public_file, fcntl.LOCK_EX)
        public_posts = json.load(public_file)
        for post in public_posts:
            if post['writer'] == writer and post['timestamp'] == post_timestamp:
                post['comments'].append(comment)
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_posts, public_file)
        # Release lock on file
        fcntl.flock(public_file, fcntl.LOCK_UN)
    # Add comment to post's entry in private file
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        private_posts = json.load(private_file)
        for post in private_posts:
            if post['timestamp'] == post_timestamp:
                post['comments'].append(comment)
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as private_file:
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)
    return make_response('Success', 200)

def update_comment(writer_name, post_timestamp):
    verification = user.verify_token()
    if verification.status.split(' ')[0] != '200':
        return make_response('Could not verify', 401)
    payload = json.loads(verification.data.decode())
    requester = payload['username']
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            # Convert requester's username to member_id for comment storage
            if user_data['username'].lower() == requester.lower():
                commenter = user_data['member_id']
            # Convert writer's username to member_id for post retrieval
            if user_data['username'].lower() == writer_name.lower():
                writer = user_data['member_id']
    data = request.get_json()
    old_timestamp = data['timestamp']
    new_timestamp = datetime.now(timezone.utc).isoformat()
    # Update comment in post's entry in public file, locating comment by commenter and previous timestaxmp
    with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
        # Lock file to prevent overwrite
        fcntl.flock(public_file, fcntl.LOCK_EX)
        public_posts = json.load(public_file)
        for post in public_posts:
            if post['writer'] == writer and post['timestamp'] == post_timestamp:
                for comment in post['comments']:
                    if comment['commenter'] == commenter and comment['timestamp'] == old_timestamp:
                        # Update comment's timestamp to timestamp of update
                        comment['timestamp'] = new_timestamp
                        comment['content'] = data['content']
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_posts, public_file)
        # Release lock on file
        fcntl.flock(public_file, fcntl.LOCK_UN)
    # Update comment in post's entry in private file, locating comment by commenter and previous timestamp
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'r') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        private_posts = json.load(private_file)
        for post in private_posts:
            if post['timestamp'] == post_timestamp:
                for comment in post['comments']:
                    if comment['commenter'] == commenter and comment['timestamp'] == old_timestamp:
                        # Update comment's timestamp to timestamp of update
                        comment['timestamp'] = new_timestamp
                        comment['content'] = data['content']
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as private_file:
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)
    return make_response('Success', 200)

def delete_comment(writer_name, post_timestamp):
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
            # Convert requester's username to member_id for comment retrieval and decrease comment number
            if user_data['username'].lower() == requester.lower():
                commenter = user_data['member_id']
                user_data['comment_number'] = int(user_data['comment_number']) - 1
            # Convert writer's username to member_id for post retrieval
            if user_data['username'].lower() == writer_name.lower():
                writer = user_data['member_id']
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'w') as users_file:
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)
    data = request.get_json()
    # Remove comment in post's entry in public file, locating comment by commenter and timestamp
    with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
        # Lock file to prevent overwrite
        fcntl.flock(public_file, fcntl.LOCK_EX)
        public_posts = json.load(public_file)
        for post in public_posts:
            if post['writer'] == writer and post['timestamp'] == post_timestamp:
                post['comments'] = [comment for comment in post['comments'] if not (comment['commenter'] == commenter and comment['timestamp'] == data['timestamp'])]
    with open(os.path.dirname(__file__) + '/public/public.json', 'w') as public_file:
        json.dump(public_posts, public_file)
        # Release lock on file
        fcntl.flock(public_file, fcntl.LOCK_UN)
    # Remove comment in post's entry in private file, locating comment by commenter and timestamp
    with open(os.path.dirname(__file__) + '/' + writer + '.json','r') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        private_posts = json.load(private_file)
        for post in private_posts:
            if post['timestamp'] == post_timestamp:
                post['comments'] = [comment for comment in post['comments'] if not (comment['commenter'] == commenter and comment['timestamp'] == data['timestamp'])]
    with open(os.path.dirname(__file__) + '/' + writer + '.json', 'w') as private_file:
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)
    return make_response('Success', 200)

def read_all_posts():
    # Get number of requested posts from query parameters
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    # Set default number of retrieved posts if not specified in query parameters
    else:
        request_start = 0
        request_end = 11
    # Return specified number of posts from public file
    with open(os.path.dirname(__file__) + '/public/public.json', 'r') as public_file:
        public_posts = json.load(public_file)
        # Sort posts by timestamp, with newest posts first
        public_posts.sort(key = itemgetter('timestamp'), reverse = True)
        for post in public_posts[request_start:request_end]:
            # Sort post comments by timestamp, with newest comments first
            post['comments'].sort(key = itemgetter('timestamp'), reverse = True)
            # Replace member_id with writer's username for each retrieved post
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == post['writer']:
                        post['writer'] = user_data['username']
            # Replace member_id with commenter's username for each retrieved post's comments
            for comment in post['comments']:
                with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                    users = json.load(users_file)
                    for user_data in users:
                        if user_data['member_id'] == comment['commenter']:
                            comment['commenter'] = user_data['username']
        return jsonify(public_posts[request_start:request_end])

def read_all_user_posts(writer_name):
    # Get number of requested posts from query parameters
    if request.args.get('start') is not None:
        request_start = int(request.args.get('start'))
        request_end = int(request.args.get('end'))
    # Set default number of retrieved posts if not specified in query parameters
    else:
        request_start = 0
        request_end = 11
    # Convert writer's username to member_id for post retrieval
    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == writer_name.lower():
                writer_id = user_data['member_id']
    verification = user.verify_token()
    # Return specified number of posts from writer's private file if verification is successful and requester is the writer
    if verification.status.split(' ')[0] == '200':
        payload = json.loads(verification.data.decode())
        requester = payload['username']
        if requester == writer_name:
            if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
                with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as private_file:
                    private_posts = json.load(private_file)
                    # Sort posts by timestamp, with newest posts first
                    private_posts.sort(key = itemgetter('timestamp'), reverse = True)
                    # Replace member_id with commenter's username for each retrieved post's comments
                    for post in private_posts[request_start:request_end]:
                        # Sort post comments by timestamp, with newest comments first
                        post['comments'].sort(key = itemgetter('timestamp'), reverse = True)
                        for comment in post['comments']:
                            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json', 'r') as users_file:
                                users = json.load(users_file)
                                for user_data in users:
                                    if user_data['member_id'] == comment['commenter']:
                                        comment['commenter'] = user_data['username']
                    return jsonify(private_posts[request_start:request_end])
            else:
                return make_response('No posts for this user', 400)
    # Return specified number of public posts from writer's private file otherwise
    if os.path.exists(os.path.dirname(__file__) + '/' + writer_id + '.json'):
        with open(os.path.dirname(__file__) + '/' + writer_id + '.json', 'r') as private_file:
            private_posts = json.load(private_file)
            public_posts = [post for post in private_posts if post['public'] == True]
            # Sort posts by timestamp, with newest posts first
            public_posts.sort(key = itemgetter('timestamp'), reverse = True)
            # Replace member_id with commenter's username for each retrieved post's comments
            for post in public_posts[request_start:request_end]:
                # Sort post comments by timestamp, with newest comments first
                post['comments'].sort(key = itemgetter('timestamp'), reverse = True)
                for comment in post['comments']:
                    with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/user/users.json','r') as users_file:
                        users = json.load(users_file)
                        for user_data in users:
                            if user_data['member_id'] == comment['commenter']:
                                comment['commenter'] = user_data['username']
            return jsonify(public_posts[request_start:request_end])
    else:
        return make_response('No posts for this user', 400)
