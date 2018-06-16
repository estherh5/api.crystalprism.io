import json
import os
import psycopg2 as pg
import psycopg2.extras

from flask import jsonify, make_response, request

from user import user


def create_post(requester):
    # Request should contain:
    # content <str>
    # public <boolean>
    # title <str>
    data = request.get_json()

    # Return error if request is missing data
    if (not data or 'content' not in data or 'public' not in data or
        'title' not in data):
            return make_response('Request is missing required data', 400)

    # Return error if post is blank
    if not data['content']:
        return make_response('Post cannot be blank', 400)

    # Return error if title is blank
    if not data['title']:
        return make_response('Post title cannot be blank', 400)

    # Return error if public status is not boolean
    if not isinstance(data['public'], bool):
        return make_response('Public status must be true or false', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Add post to database
    cursor.execute(
        """
        INSERT INTO post
                    (member_id)
             VALUES (
                     (SELECT member_id
                        FROM cp_user
                       WHERE LOWER(username) = %(username)s)
             )
          RETURNING post_id;
        """,
        {'username': requester.lower()}
        )

    post_id = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO post_content
                    (content, created, post_id, public, title)
             VALUES (%(content)s,
                    (SELECT modified
                       FROM post
                      WHERE post_id = %(post_id)s),
                    %(post_id)s, %(public)s, %(title)s);
        """,
        {'content': data['content'].strip(),
        'post_id': post_id,
        'public': data['public'],
        'title': data['title'].strip()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response(str(post_id), 201)


def read_post(post_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve post from database
    cursor.execute(
        """
        SELECT post.created, post.modified, post.post_id,
               cp_user.username
          FROM post
               JOIN cp_user
                 ON post.member_id = cp_user.member_id
         WHERE post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    post = cursor.fetchone()

    # Return error if post not found
    if not post:
        return make_response('Not found', 404)

    # Otherwise, convert post data to dictionary
    post = dict(post)

    # Retrieve all post content versions from database
    cursor.execute(
        """
        SELECT content, created, public, title
          FROM post_content
         WHERE post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    post['history'] = []

    for row in cursor.fetchall():
        row = dict(row)

        # Set current post content, public, and title items
        if row['created'] == post['modified']:
            post['content'] = row['content']
            post['public'] = row['public']
            post['title'] = row['title']

        # Add rest of post versions to history item
        else:
            post['history'].append(row)

    # Retrieve comment count from database
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM comment
         WHERE post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    post['comment_count'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # Check if user is logged in
    verification = user.verify_token()

    # If requester's user token is verified and requester is the writer, return
    # post and its entire history
    if (verification.status_code == 200 and json.loads(verification.data
        .decode())['username'].lower() == post['username'].lower()):

            return jsonify(post)

    # if post is private and requester is not the writer, retun error
    if not post['public']:
        return make_response('Unauthorized', 401)

    # Otherwise, if post is public, return post with private history removed
    # without login verification
    post['history'] = [content for content in post['history']
        if content['public']]

    return jsonify(post)


def update_post(requester, post_id):
    # Request should contain:
    # content <str>
    # public <boolean>
    # title <str>
    data = request.get_json()

    # Return error if request is missing data
    if (not data or 'content' not in data or 'public' not in data or
        'title' not in data):
            return make_response('Request is missing required data', 400)

    # Return error if post is blank
    if not data['content']:
        return make_response('Post cannot be blank', 400)

    # Return error if title is blank
    if not data['title']:
        return make_response('Post title cannot be blank', 400)

    # Return error if public status is not boolean
    if not isinstance(data['public'], bool):
        return make_response('Public status must be true or false', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get current post from database
    cursor.execute(
        """
        SELECT post.*, post_content.*, cp_user.username
          FROM post
               JOIN post_content
                 ON post.modified = post_content.created
                    AND post.post_id = post_content.post_id
               JOIN cp_user
                 ON post.member_id = cp_user.member_id
         WHERE post.post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    post = cursor.fetchone()

    # Return error if post not found
    if not post:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert post data to dictionary
    post = dict(post)

    # Return error if requester is not the writer
    if requester.lower() != post['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Return error if there are no changes to post
    if (data['content'] == post['content'] and
        data['public'] == post['public'] and data['title'] == post['title']):
            return make_response('No changes made', 409)

    # Otherwise, add post content version to database
    cursor.execute(
        """
        INSERT INTO post_content
                    (content, post_id, public, title)
             VALUES (%(content)s, %(post_id)s, %(public)s, %(title)s)
          RETURNING created;
        """,
        {'content': data['content'].strip(),
        'post_id': post_id,
        'public': data['public'],
        'title': data['title'].strip()}
        )

    content_timestamp = cursor.fetchone()[0]

    # Update post modified time to created timestamp for post content version
    cursor.execute(
        """
        UPDATE post
           SET modified = %(modified)s
         WHERE post_id = %(post_id)s;
        """,
        {'modified': content_timestamp,
        'post_id': post_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def delete_post(requester, post_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get post from database
    cursor.execute(
        """
        SELECT post.*, cp_user.username
          FROM post
               JOIN cp_user
                 ON post.member_id = cp_user.member_id
         WHERE post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    post = cursor.fetchone()

    # Return error if post not found
    if not post:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert post data to dictionary
    post = dict(post)

    # Return error if requester is not the writer
    if requester.lower() != post['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Delete post from database
    cursor.execute(
        """
        DELETE FROM post
              WHERE post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def read_posts():
    # Get number of requested posts from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve all posts except for website owner's from database
    cursor.execute(
        """
          SELECT post.created, post.modified, post.post_id,
                 post_content.public, cp_user.username
            FROM post
                 JOIN post_content
                   ON post_content.created = post.modified
                      AND post_content.post_id = post.post_id
                 JOIN cp_user
                   ON post.member_id = cp_user.member_id
           WHERE cp_user.is_owner != TRUE
                 AND post_content.public = TRUE
        ORDER BY created DESC;
        """
        )

    posts = []

    for row in cursor.fetchall():
        posts.append(dict(row))

    # Retrieve each post's public content versions from database
    for post in posts:
        cursor.execute(
            """
            SELECT content, created, title
              FROM post_content
             WHERE post_id = %(post_id)s
                   AND public = TRUE;
            """,
            {'post_id': post['post_id']}
            )

        post['history'] = []

        for row in cursor.fetchall():
            row = dict(row)

            # Set current post content, public, and title items
            if row['created'] == post['modified']:
                post['content'] = row['content']
                post['title'] = row['title']

            # Add rest of post versions to history item
            else:
                post['history'].append(row)

    # Retrieve each post's comment count from database
    for post in posts:
        cursor.execute(
            """
            SELECT COUNT(*)
              FROM comment
             WHERE post_id = %(post_id)s;
            """,
            {'post_id': post['post_id']}
            )

        post['comment_count'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify(posts[request_start:request_end])


def read_posts_for_one_user(writer_name):
    # Get number of requested posts from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve posts from database
    cursor.execute(
        """
          SELECT post.created, post.modified, post.post_id,
                 post_content.public, cp_user.username
            FROM post
                 JOIN post_content
                   ON post_content.created = post.modified
                      AND post_content.post_id = post.post_id
                 JOIN cp_user
                   ON post.member_id = cp_user.member_id
           WHERE LOWER(cp_user.username) = %(username)s
        ORDER BY created DESC;
        """,
        {'username': writer_name.lower()}
        )

    posts = []

    # Check if user is logged in
    verification = user.verify_token()

    # Return all posts to client only if requester's user token is verified and
    # requester is the writer
    if (verification.status_code == 200 and
        json.loads(verification.data.decode())['username']
        .lower() == writer_name.lower()):

        for row in cursor.fetchall():
            posts.append(dict(row))

        # Retrieve each post's public and private content versions from
        # database
        for post in posts:
            cursor.execute(
                """
                SELECT content, created, title
                  FROM post_content
                 WHERE post_id = %(post_id)s;
                """,
                {'post_id': post['post_id']}
                )

            post['history'] = []

            for row in cursor.fetchall():
                row = dict(row)

                # Set current post content, public, and title items
                if row['created'] == post['modified']:
                    post['content'] = row['content']
                    post['title'] = row['title']

                # Add rest of post versions to history item
                else:
                    post['history'].append(row)

    # Otherwise, return only public posts to client
    else:
        for row in cursor.fetchall():
            if row['public']:
                posts.append(dict(row))

        # Retrieve each post's public content versions from database
        for post in posts:
            cursor.execute(
                """
                SELECT content, created, title
                  FROM post_content
                 WHERE post_id = %(post_id)s
                       AND public = TRUE;
                """,
                {'post_id': post['post_id']}
                )

            post['history'] = []

            for row in cursor.fetchall():
                row = dict(row)

                # Set current post content, public, and title items
                if row['created'] == post['modified']:
                    post['content'] = row['content']
                    post['title'] = row['title']

                # Add rest of post versions to history item
                else:
                    post['history'].append(row)

    # Retrieve each post's comment count from database
    for post in posts:
        cursor.execute(
            """
            SELECT COUNT(*)
              FROM comment
             WHERE post_id = %(post_id)s;
            """,
            {'post_id': post['post_id']}
            )

        post['comment_count'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify(posts[request_start:request_end])


def create_comment(requester):
    # Request should contain:
    # content <str>
    # post_id <int>
    data = request.get_json()

    # Return error if request is missing data
    if not data or 'content' not in data or 'post_id' not in data:
        return make_response(
            'Request must contain post id and comment content', 400
            )

    # Return error if post id is blank or not an integer
    if not isinstance(data['post_id'], int):
        return make_response('Post id must be an integer', 400)

    # Return error if comment is blank
    if not data['content']:
        return make_response('Comment cannot be blank', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Get latest post content from database and ensure it is public
    cursor.execute(
        """
        SELECT public
          FROM post_content
         WHERE post_id = %(post_id)s
               AND created = (
                              SELECT modified
                                FROM post
                               WHERE post_id = %(post_id)s
               );
        """,
        {'post_id': data['post_id']}
        )

    public = cursor.fetchone()

    # Return error if post not found
    if not public:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Return error if post not public
    if not public[0]:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Add comment to database
    cursor.execute(
        """
        INSERT INTO comment
                    (member_id, post_id)
             VALUES (
                     (SELECT member_id
                        FROM cp_user
                       WHERE LOWER(username) = %(username)s),
                     %(post_id)s
             )
          RETURNING comment_id;
        """,
        {'username': requester.lower(),
        'post_id': data['post_id']}
        )

    comment_id = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO comment_content
                    (comment_id, content, created)
             VALUES (%(comment_id)s, %(content)s,
                    (SELECT modified
                       FROM comment
                      WHERE comment_id = %(comment_id)s));
        """,
        {'comment_id': comment_id,
        'content': data['content'].strip()}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response(str(comment_id), 201)


def read_comment(comment_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get comment from database
    cursor.execute(
        """
        SELECT comment.comment_id, comment.created, comment.modified,
               comment.post_id, cp_user.username
          FROM comment
               JOIN cp_user
                 ON comment.member_id = cp_user.member_id
         WHERE comment_id = %(comment_id)s;
        """,
        {'comment_id': comment_id}
        )

    comment = cursor.fetchone()

    # Return error if comment not found
    if not comment:
        return make_response('Not found', 404)

    # Otherwise, convert comment data to dictionary
    comment = dict(comment)

    # Get latest post content from database and ensure it is public
    cursor.execute(
        """
        SELECT public
          FROM post_content
         WHERE post_id = %(post_id)s
               AND created = (
                              SELECT modified
                                FROM post
                               WHERE post_id = %(post_id)s
               );
        """,
        {'post_id': comment['post_id']}
        )

    public = cursor.fetchone()

    # Return error if post not public
    if not public[0]:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Retrieve all comment content versions from database
    cursor.execute(
        """
        SELECT content, created
          FROM comment_content
         WHERE comment_id = %(comment_id)s;
        """,
        {'comment_id': comment_id}
        )

    comment['history'] = []

    for row in cursor.fetchall():
        row = dict(row)

        # Set current comment content items
        if row['created'] == comment['modified']:
            comment['content'] = row['content']

        # Add rest of comment versions to history item
        else:
            comment['history'].append(row)

    cursor.close()
    conn.close()

    return jsonify(comment)


def update_comment(requester, comment_id):
    # Request should contain:
    # content <str>
    data = request.get_json()

    # Return error if request is missing data
    if not data or 'content' not in data:
        return make_response('Request must contain comment content', 400)

    # Return error if comment is blank
    if not data['content']:
        return make_response('Comment cannot be blank', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get current comment from database
    cursor.execute(
        """
        SELECT comment.*, comment_content.*, cp_user.username
          FROM comment
               JOIN comment_content
                 ON comment.modified = comment_content.created
                    AND comment.comment_id = comment_content.comment_id
               JOIN cp_user
                 ON comment.member_id = cp_user.member_id
         WHERE comment.comment_id = %(comment_id)s;
        """,
        {'comment_id': comment_id}
        )

    comment = cursor.fetchone()

    # Return error if comment not found
    if not comment:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert comment data to dictionary
    comment = dict(comment)

    # Return error if requester is not the commenter
    if requester.lower() != comment['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Return error if there are no changes to comment
    if data['content'] == comment['content']:
        return make_response('No changes made', 409)

    # Otherwise, add comment content version to database
    cursor.execute(
        """
        INSERT INTO comment_content
                    (comment_id, content)
             VALUES (%(comment_id)s, %(content)s)
          RETURNING created;
        """,
        {'comment_id': comment_id,
        'content': data['content'].strip()}
        )

    content_timestamp = cursor.fetchone()[0]

    # Update comment modified time to created timestamp for comment content
    # version
    cursor.execute(
        """
        UPDATE comment
           SET modified = %(modified)s
         WHERE comment_id = %(comment_id)s;
        """,
        {'modified': content_timestamp,
        'comment_id': comment_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def delete_comment(requester, comment_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get current comment from database
    cursor.execute(
        """
        SELECT comment.*, cp_user.username
          FROM comment
               JOIN cp_user
                 ON comment.member_id = cp_user.member_id
         WHERE comment_id = %(comment_id)s;
        """,
        {'comment_id': comment_id}
        )

    comment = cursor.fetchone()

    # Return error if comment not found
    if not comment:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert comment data to dictionary
    comment = dict(comment)

    # Return error if requester is not the commenter
    if requester.lower() != comment['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Delete comment from database
    cursor.execute(
        """
        DELETE FROM comment
              WHERE comment_id = %(comment_id)s;
        """,
        {'comment_id': comment_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def read_comments(post_id):
    # Get number of requested comments from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve comments from database
    cursor.execute(
        """
          SELECT comment.comment_id, comment.created, comment.modified,
                 comment.post_id, cp_user.username
            FROM comment
                 JOIN cp_user
                   ON comment.member_id = cp_user.member_id
                 JOIN post
                   ON comment.post_id = post.post_id
                 JOIN post_content
                   ON comment.post_id = post_content.post_id
                      AND post.modified = post_content.created
           WHERE comment.post_id = %(post_id)s
                 AND post_content.public = TRUE
        ORDER BY created DESC;
        """,
        {'post_id': post_id}
        )

    comments = []

    for row in cursor.fetchall():
        comments.append(dict(row))

    for comment in comments:
        # Retrieve each comment's content versions from database
        cursor.execute(
            """
            SELECT content, created
              FROM comment_content
             WHERE comment_id = %(comment_id)s;
            """,
            {'comment_id': comment['comment_id']}
            )

        comment['history'] = []

        for row in cursor.fetchall():
            row = dict(row)

            # Set current comment content items
            if row['created'] == comment['modified']:
                comment['content'] = row['content']

            # Add rest of comment versions to history item
            else:
                comment['history'].append(row)

    cursor.close()
    conn.close()

    return jsonify(comments[request_start:request_end])


def read_comments_for_one_user(commenter_name):
    # Get number of requested posts from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve comments from database
    cursor.execute(
        """
          SELECT comment.comment_id, comment.created, comment.modified,
                 comment.post_id, post_content.content AS post_content,
                 post.member_id, post_content.title, cp_user.username
            FROM comment
                 JOIN post
                   ON comment.post_id = post.post_id
                 JOIN post_content
                   ON post_content.post_id = post.post_id
                      AND post_content.created = post.modified
                 JOIN cp_user
                   ON comment.member_id = cp_user.member_id
           WHERE LOWER(cp_user.username) = %(username)s
                 AND post_content.public = TRUE
        ORDER BY comment.created DESC;
        """,
        {'username': commenter_name.lower()}
        )

    comments = []

    for row in cursor.fetchall():
        comments.append(dict(row))

    for comment in comments:
        # Replace each post writer's member id with username
        cursor.execute(
            """
            SELECT username
              FROM cp_user
             WHERE member_id = %(member_id)s;
            """,
            {'member_id': comment['member_id']}
            )

        comment.pop('member_id')
        comment['post_writer'] = cursor.fetchone()[0]

        # Retrieve each comment's content versions from database
        cursor.execute(
            """
            SELECT content, created
              FROM comment_content
             WHERE comment_id = %(comment_id)s;
            """,
            {'comment_id': comment['comment_id']}
            )

        comment['history'] = []

        for row in cursor.fetchall():
            row = dict(row)

            # Set current comment content items
            if row['created'] == comment['modified']:
                comment['content'] = row['content']

            # Add rest of comment versions to history item
            else:
                comment['history'].append(row)

    cursor.close()
    conn.close()

    return jsonify(comments[request_start:request_end])
