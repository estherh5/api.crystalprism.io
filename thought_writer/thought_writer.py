import fcntl
import json
import os

from datetime import datetime, timezone
from flask import jsonify, make_response, request
from operator import itemgetter

from user import user

cwd = os.path.dirname(__file__)


def create_post(requester):
    # Request should contain:
    # title <str>
    # content <str>
    # public <boolean>
    data = request.get_json()

    # Generate timestamp to store with post
    timestamp = datetime.now(timezone.utc).isoformat()

    post = {
        'title': data['title'],
        'timestamp': timestamp,
        'content': data['content'],
        'public': data['public'],
        'comments': []
        }

    # Convert username to member_id for post storage and increase post count
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                writer_id = user_data['member_id']
                user_data['post_count'] += 1

    # Add post to private user file if it exists or generate new file for
    # first-time posting
    if os.path.exists(cwd + '/' + writer_id + '.json'):
        with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
            private_posts = json.load(private_file)
            private_posts.append(post)
    else:
        private_posts = [post]

    with open(cwd + '/' + writer_id + '.json', 'w') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)

    # Add post to public file if marked as public
    if data['public']:
        post = {
            'writer': writer_id,
            'title': data['title'],
            'timestamp': timestamp,
            'content': data['content'],
            'comments': []
            }

        with open(cwd + '/public/public.json', 'r') as public_file:
            public_posts = json.load(public_file)
            public_posts.append(post)

        with open(cwd + '/public/public.json', 'w') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)

    # Write changes to user file to update user's post count if post is
    # created successfully
    with open(cwd + '/../user/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response(timestamp, 201)


def update_post(requester):
    # Request should contain:
    # title <str>
    # timestamp <str>
    # content <str>
    # public <boolean>
    data = request.get_json()

    # Convert username to member_id for post retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                writer_id = user_data['member_id']

    post_found = False  # Stores whether post is found in private file

    # Update post in user's private file
    with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
        private_posts = json.load(private_file)

        for post in private_posts:
            if post['timestamp'] == data['timestamp']:
                # Get post's previous public status to see if status has
                # changed in update
                previously_public = post['public']
                post['title'] = data['title']
                post['content'] = data['content']
                post['public'] = data['public']
                # Get post's current comments to add to public file if post is
                # newly public
                comments = post['comments']
                post_found = True

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/' + writer_id + '.json', 'w') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)

    # Update post in public file if public
    if data['public']:
        with open(cwd + '/public/public.json', 'r') as public_file:
            public_posts = json.load(public_file)

            # Update post in public file if it was already public
            if previously_public:
                for post in public_posts:
                    if (post['writer'] == writer_id and
                        post['timestamp'] == data['timestamp']):
                        post['title'] = data['title']
                        post['content'] = data['content']

            # Add post to public file if it was not public previously
            else:
                post = {
                    'writer': writer_id,
                    'title': data['title'],
                    'timestamp': data['timestamp'],
                    'content': data['content'],
                    'comments': comments
                    }
                public_posts.append(post)

        with open(cwd + '/public/public.json', 'w') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)

    # Remove post from public file if it was previously public but is now
    # private
    if previously_public and not data['public']:
        with open(cwd + '/public/public.json', 'r') as public_file:
            public_posts = json.load(public_file)
            public_posts = [post for post in public_posts
                if not (post['writer'] == writer_id and
                        post['timestamp'] == data['timestamp'])
                ]

        with open(cwd + '/public/public.json', 'w') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)

    return make_response('Success', 200)


def delete_post(requester):
    # Request should contain:
    # timestamp <str>
    data = request.get_json()

    # Convert username to member_id for post retrieval and decrease post count
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == requester.lower():
                writer_id = user_data['member_id']
                user_data['post_count'] -= 1

    post_found = False  # Stores whether post is found in private file

    # Remove post from user's private file
    with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
        private_posts = json.load(private_file)

        # Get post's public status to see if it should also be removed from
        # public file
        for post in private_posts:
            if post['timestamp'] == data['timestamp']:
                public = post['public']
                post_found = True

        # Otherwise, remove post from private posts list
        private_posts = [post for post in private_posts
            if post['timestamp'] != data['timestamp']]

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/' + writer_id + '.json', 'w') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)

    # Remove post from public file if it is public
    if public:
        with open(cwd + '/public/public.json', 'r') as public_file:
            public_posts = json.load(public_file)
            public_posts = [post for post in public_posts
                if not (post['writer'] == writer_id and
                        post['timestamp'] == data['timestamp'])
                ]

        with open(cwd + '/public/public.json', 'w') as public_file:
            # Lock file to prevent overwrite
            fcntl.flock(public_file, fcntl.LOCK_EX)
            json.dump(public_posts, public_file)
            # Release lock on file
            fcntl.flock(public_file, fcntl.LOCK_UN)

    # Write changes to user file to update user's post count if post is
    # deleted successfully
    with open(cwd + '/../user/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response('Success', 200)


def read_post(writer_name, post_timestamp):
    # Convert username to member_id for post retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == writer_name.lower():
                writer_id = user_data['member_id']

    # Check if user is logged in
    verification = user.verify_token()

    # Retrieve post from private user file if user token is verified and
    # requester is the post writer
    if (verification.status_code == 200 and
        json.loads(verification.data.decode())['username']
        .lower() == writer_name.lower()):

        with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
            private_posts = json.load(private_file)

            # Replace member_id with commenter's username for each retrieved
            # post's comments
            for post in private_posts:
                if post['timestamp'] == post_timestamp:
                    for comment in post['comments']:
                        with open(cwd + '/../user/users.json', 'r') as users_file:
                            users = json.load(users_file)
                            for user_data in users:
                                if user_data['member_id'] == comment['commenter']:
                                    comment['commenter'] = user_data['username']

                    return jsonify(post)

            # If post is not found, return error to client
            return make_response('Post not found', 404)

    # Retrieve post from public file otherwise
    with open(cwd + '/public/public.json', 'r') as public_file:
        public_posts = json.load(public_file)

        # Replace member_ids with writer's username and with commenter's
        # username for each retrieved post's comments
        for post in public_posts:
            if (post['writer'] == writer_id and
                post['timestamp'] == post_timestamp):
                post['writer'] = writer_name
                for comment in post['comments']:
                    with open(cwd + '/../user/users.json', 'r') as users_file:
                        users = json.load(users_file)
                        for user_data in users:
                            if user_data['member_id'] == comment['commenter']:
                                comment['commenter'] = user_data['username']

                return jsonify(post)

        # If post is not found, return error to client
        return make_response('Post not found', 404)


def create_comment(requester, writer_name, post_timestamp):
    # Request should contain:
    # content <str>
    data = request.get_json()

    # Generate timestamp to store with post comment
    timestamp = datetime.now(timezone.utc).isoformat()

    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)

        for user_data in users:
            # Convert requester's username to member_id for comment storage and
            # increase comment number
            if user_data['username'].lower() == requester.lower():
                commenter_id = user_data['member_id']
                user_data['comment_count'] += 1

            # Convert post writer's username to member_id for post retrieval
            if user_data['username'].lower() == writer_name.lower():
                writer_id = user_data['member_id']

    # Store comment entry with commenter, timestamp, and content
    comment = {
        'commenter': commenter_id,
        'timestamp': timestamp,
        'content': data['content']
        }

    post_found = False  # Stores whether post is found in public file

    # Add comment to post's entry in public file
    with open(cwd + '/public/public.json', 'r') as public_file:
        public_posts = json.load(public_file)

        for post in public_posts:
            if (post['writer'] == writer_id and
                post['timestamp'] == post_timestamp):
                post['comments'].append(comment)
                post_found = True

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/public/public.json', 'w') as public_file:
        # Lock file to prevent overwrite
        fcntl.flock(public_file, fcntl.LOCK_EX)
        json.dump(public_posts, public_file)
        # Release lock on file
        fcntl.flock(public_file, fcntl.LOCK_UN)

    post_found = False  # Stores whether post is found in private file

    # Add comment to post's entry in private file
    with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
        private_posts = json.load(private_file)

        for post in private_posts:
            if post['timestamp'] == post_timestamp:
                post['comments'].append(comment)
                post_found = True

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/' + writer_id + '.json', 'w') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)

    # Write changes to user file to update user's comment count if comment is
    # created successfully
    with open(cwd + '/../user/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response('Success', 201)


def update_comment(requester, writer_name, post_timestamp):
    # Request should contain:
    # content <str>
    # timestamp <str>
    data = request.get_json()

    # Get original comment's timestamp from request
    old_timestamp = data['timestamp']

    # Generate new timestamp to store with updated comment
    new_timestamp = datetime.now(timezone.utc).isoformat()

    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            # Convert requester's username to member_id for comment storage
            if user_data['username'].lower() == requester.lower():
                commenter_id = user_data['member_id']

            # Convert post writer's username to member_id for post retrieval
            if user_data['username'].lower() == writer_name.lower():
                writer_id = user_data['member_id']

    post_found = False  # Stores whether post is found in public file

    # Update comment in post's entry in public file, locating comment by
    # commenter and previous timestamp
    with open(cwd + '/public/public.json', 'r') as public_file:
        public_posts = json.load(public_file)

        for post in public_posts:
            if (post['writer'] == writer_id and
                post['timestamp'] == post_timestamp):
                post_found = True

                for comment in post['comments']:
                    if (comment['commenter'] == commenter_id and
                        comment['timestamp'] == old_timestamp):
                        # Update comment's timestamp to timestamp of update
                        comment['timestamp'] = new_timestamp
                        comment['content'] = data['content']

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/public/public.json', 'w') as public_file:
        # Lock file to prevent overwrite
        fcntl.flock(public_file, fcntl.LOCK_EX)
        json.dump(public_posts, public_file)
        # Release lock on file
        fcntl.flock(public_file, fcntl.LOCK_UN)

    post_found = False  # Stores whether post is found in private file

    # Update comment in post's entry in private file, locating comment by
    # commenter and previous timestamp
    with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
        private_posts = json.load(private_file)

        for post in private_posts:
            if post['timestamp'] == post_timestamp:
                post_found = True

                for comment in post['comments']:
                    if (comment['commenter'] == commenter_id and
                        comment['timestamp'] == old_timestamp):
                        # Update comment's timestamp to timestamp of update
                        comment['timestamp'] = new_timestamp
                        comment['content'] = data['content']

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/' + writer_id + '.json', 'w') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)

    return make_response('Success', 200)


def delete_comment(requester, writer_name, post_timestamp):
    # Request should contain:
    # timestamp <str>
    data = request.get_json()

    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            # Convert requester's username to member_id for comment retrieval
            # and decrease comment number
            if user_data['username'].lower() == requester.lower():
                commenter_id = user_data['member_id']
                user_data['comment_count'] -= 1

            # Convert post writer's username to member_id for post retrieval
            if user_data['username'].lower() == writer_name.lower():
                writer_id = user_data['member_id']

    post_found = False  # Stores whether post is found in public file

    # Remove comment in post's entry in public file, locating comment by
    # commenter and timestamp
    with open(cwd + '/public/public.json', 'r') as public_file:
        public_posts = json.load(public_file)

        for post in public_posts:
            if (post['writer'] == writer_id and
                post['timestamp'] == post_timestamp):
                post_found = True

                post['comments'] = [comment for comment in post['comments']
                    if not (comment['commenter'] == commenter_id and
                            comment['timestamp'] == data['timestamp'])
                    ]

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/public/public.json', 'w') as public_file:
        # Lock file to prevent overwrite
        fcntl.flock(public_file, fcntl.LOCK_EX)
        json.dump(public_posts, public_file)
        # Release lock on file
        fcntl.flock(public_file, fcntl.LOCK_UN)

    post_found = False  # Stores whether post is found in private file

    # Remove comment in post's entry in private file, locating comment by
    # commenter and timestamp
    with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
        private_posts = json.load(private_file)

        for post in private_posts:
            if post['timestamp'] == post_timestamp:
                post_found = True

                post['comments'] = [comment for comment in post['comments']
                    if not (comment['commenter'] == commenter_id and
                            comment['timestamp'] == data['timestamp'])
                    ]

    # If post is not found, return error to client
    if not post_found:
        return make_response('Post not found', 404)

    with open(cwd + '/' + writer_id + '.json', 'w') as private_file:
        # Lock file to prevent overwrite
        fcntl.flock(private_file, fcntl.LOCK_EX)
        json.dump(private_posts, private_file)
        # Release lock on file
        fcntl.flock(private_file, fcntl.LOCK_UN)

    # Write changes to user file to update user's comment count if comment is
    # deleted successfully
    with open(cwd + '/../user/users.json', 'w') as users_file:
        # Lock file to prevent overwrite
        fcntl.flock(users_file, fcntl.LOCK_EX)
        json.dump(users, users_file)
        # Release lock on file
        fcntl.flock(users_file, fcntl.LOCK_UN)

    return make_response('Success', 200)


def read_posts():
    # Get number of requested posts from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Return specified number of posts from public file
    with open(cwd + '/public/public.json', 'r') as public_file:
        public_posts = json.load(public_file)

        # Sort posts by timestamp, with newest posts first
        public_posts.sort(key=itemgetter('timestamp'), reverse=True)
        for post in public_posts[request_start:request_end]:

            # Sort post comments by timestamp, with newest comments first
            post['comments'].sort(key=itemgetter('timestamp'), reverse=True)

            # Replace member_id with writer's username for each retrieved post
            with open(cwd + '/../user/users.json', 'r') as users_file:
                users = json.load(users_file)
                for user_data in users:
                    if user_data['member_id'] == post['writer']:
                        post['writer'] = user_data['username']
            # Replace member_id with commenter's username for each retrieved
            # post's comments
            for comment in post['comments']:
                with open(cwd + '/../user/users.json', 'r') as users_file:
                    users = json.load(users_file)
                    for user_data in users:
                        if user_data['member_id'] == comment['commenter']:
                            comment['commenter'] = user_data['username']

        return jsonify(public_posts[request_start:request_end])


def read_posts_for_one_user(writer_name):
    # Get number of requested posts from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Convert writer's username to member_id for post retrieval
    with open(cwd + '/../user/users.json', 'r') as users_file:
        users = json.load(users_file)
        for user_data in users:
            if user_data['username'].lower() == writer_name.lower():
                writer_id = user_data['member_id']

    # Check if user is logged in
    verification = user.verify_token()

    # Return specified number of posts from writer's private file if user
    # token is verified and requester is the post writer
    if (verification.status_code == 200 and
        json.loads(verification.data.decode())['username']
        .lower() == writer_name.lower()):

        if os.path.exists(cwd + '/' + writer_id + '.json'):
            with open(cwd + '/' + writer_id + '.json',
                'r') as private_file:
                private_posts = json.load(private_file)

                # Sort posts by timestamp, with newest posts first
                private_posts.sort(
                    key=itemgetter('timestamp'), reverse=True)

                for post in private_posts[request_start:request_end]:
                    # Sort post comments by timestamp, with newest comments
                    # first
                    post['comments'].sort(
                        key=itemgetter('timestamp'), reverse=True)

                    # Replace member_id with commenter's username for each
                    # retrieved post's comments
                    for comment in post['comments']:
                        with open(cwd + '/../user/users.json', 'r') as users_file:
                            users = json.load(users_file)
                            for user_data in users:
                                if user_data['member_id'] == comment['commenter']:
                                    comment['commenter'] = user_data['username']

                return jsonify(private_posts[request_start:request_end])

    # Return specified number of public posts from writer's private file
    # otherwise
    if os.path.exists(cwd + '/' + writer_id + '.json'):
        with open(cwd + '/' + writer_id + '.json', 'r') as private_file:
            private_posts = json.load(private_file)
            public_posts = [post for post in private_posts
                if post['public']
                ]

            # Sort posts by timestamp, with newest posts first
            public_posts.sort(key=itemgetter('timestamp'), reverse=True)

            for post in public_posts[request_start:request_end]:
                # Sort post comments by timestamp, with newest comments first
                post['comments'].sort(
                    key=itemgetter('timestamp'), reverse=True)
                # Replace member_id with commenter's username for each
                # retrieved post's comments
                for comment in post['comments']:
                    with open(cwd + '/../user/users.json', 'r') as users_file:
                        users = json.load(users_file)
                        for user_data in users:
                            if user_data['member_id'] == comment['commenter']:
                                comment['commenter'] = user_data['username']

            return jsonify(public_posts[request_start:request_end])

    return make_response('No posts for this user', 404)
