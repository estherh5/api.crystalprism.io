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

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Add post to database
    cursor.execute(
        """
        INSERT INTO post (member_id, content, public, title)
        VALUES ((SELECT member_id FROM cp_user
        WHERE LOWER(username) = %(username)s), %(content)s, %(public)s,
        %(title)s) RETURNING post_id;
        """,
        {'username': requester.lower(),
        'content': data['content'],
        'public': data['public'],
        'title': data['title']}
        )

    conn.commit()

    post_id = cursor.fetchone()[0]

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
        SELECT post.content, post.created, post.modified, post.post_id,
        post.public, post.title, cp_user.username FROM post
        JOIN cp_user ON post.member_id = cp_user.member_id
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

    # Retrieve comment count from database
    cursor.execute(
        """
        SELECT COUNT(*) FROM comment
        WHERE post_id = %(post_id)s;
        """,
        {'post_id': post_id}
        )

    post['comment_count'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # If post is private, return post to client only if requester's user token
    # is verified and requester is the writer
    if not post['public']:

        # Check if user is logged in
        verification = user.verify_token()

        if (verification.status_code == 200 and
            json.loads(verification.data.decode())['username']
            .lower() == post['username'].lower()):

                return jsonify(post)

        return make_response('Unauthorized', 401)

    # Otherwise, if post is public, return post without login verification
    return jsonify(post)


def update_post(requester, post_id):
    # Request should contain:
    # content <str>
    # public <boolean>
    # title <str>
    data = request.get_json()

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get current post from database
    cursor.execute(
        """
        SELECT post.*, cp_user.username FROM post
        JOIN cp_user ON post.member_id = cp_user.member_id
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

    # Update post in database
    cursor.execute(
        """
        UPDATE post SET title = %(title)s, content = %(content)s,
        modified = to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        public = %(public)s
        WHERE post_id = %(post_id)s;
        """,
        {'title': data['title'],
        'content': data['content'],
        'public': data['public'],
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
        SELECT post.*, cp_user.username FROM post
        JOIN cp_user ON post.member_id = cp_user.member_id
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
        DELETE FROM post WHERE post_id = %(post_id)s;
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

    # Retrieve public posts from database
    cursor.execute(
        """
        SELECT post.content, post.created, post.modified, post.post_id,
        post.public, post.title, cp_user.username FROM post
        JOIN cp_user ON post.member_id = cp_user.member_id
        WHERE public = TRUE AND cp_user.is_owner != TRUE
        ORDER BY created DESC;
        """
        )

    posts = []

    for row in cursor.fetchall():
        posts.append(dict(row))

    # Retrieve each post's comment count from database
    for post in posts:
        cursor.execute(
            """
            SELECT COUNT(*) FROM comment
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
        SELECT post.content, post.created, post.modified, post.post_id,
        post.public, post.title, cp_user.username FROM post
        JOIN cp_user ON post.member_id = cp_user.member_id
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

    # Otherwise, return only public posts to client
    else:
        for row in cursor.fetchall():
            if row['public']:
                posts.append(dict(row))

    # Retrieve each post's comment count from database
    for post in posts:
        cursor.execute(
            """
            SELECT COUNT(*) FROM comment
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

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Get post from database and ensure it is public
    cursor.execute(
        """
        SELECT public FROM post WHERE post_id = %(post_id)s;
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
        INSERT INTO comment (member_id, post_id, content)
        VALUES ((SELECT member_id FROM cp_user
        WHERE LOWER(username) = %(username)s), %(post_id)s, %(content)s)
        RETURNING comment_id;
        """,
        {'username': requester.lower(),
        'post_id': data['post_id'],
        'content': data['content']}
        )

    comment_id = cursor.fetchone()[0]

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
        SELECT comment.comment_id, comment.content, comment.created,
        comment.modified, comment.post_id, cp_user.username FROM comment
        JOIN cp_user ON comment.member_id = cp_user.member_id
        WHERE comment_id = %(comment_id)s;
        """,
        {'comment_id': comment_id}
        )

    comment = cursor.fetchone()

    cursor.close()
    conn.close()

    # Return error if comment not found
    if not comment:
        return make_response('Not found', 404)

    # Otherwise, convert comment data to dictionary
    comment = dict(comment)

    return jsonify(comment)


def update_comment(requester, comment_id):
    # Request should contain:
    # content <str>
    data = request.get_json()

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get current comment from database
    cursor.execute(
        """
        SELECT comment.*, cp_user.username FROM comment
        JOIN cp_user ON comment.member_id = cp_user.member_id
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

    # Update comment in database
    cursor.execute(
        """
        UPDATE comment SET content = %(content)s, modified = to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        WHERE comment_id = %(comment_id)s;
        """,
        {'content': data['content'],
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
        SELECT comment.*, cp_user.username FROM comment
        JOIN cp_user ON comment.member_id = cp_user.member_id
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
        DELETE FROM comment WHERE comment_id = %(comment_id)s;
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
        SELECT comment.comment_id, comment.content, comment.created,
        comment.modified, comment.post_id, cp_user.username FROM comment
        JOIN cp_user ON comment.member_id = cp_user.member_id
        WHERE post_id = %(post_id)s
        ORDER BY created DESC;
        """,
        {'post_id': post_id}
        )

    comments = []

    for row in cursor.fetchall():
        comments.append(dict(row))

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
        SELECT comment.comment_id, comment.content, comment.created,
        comment.modified, comment.post_id, post.content AS post_content,
        post.member_id, post.title, cp_user.username FROM comment
        JOIN post ON comment.post_id = post.post_id
        JOIN cp_user ON comment.member_id = cp_user.member_id
        WHERE LOWER(cp_user.username) = %(username)s
        ORDER BY comment.created DESC;
        """,
        {'username': commenter_name.lower()}
        )

    comments = []

    for row in cursor.fetchall():
        comments.append(dict(row))

    # Replace each post writer's member id with username
    for comment in comments:
        cursor.execute(
            """
            SELECT username FROM cp_user
            WHERE member_id = %(member_id)s;
            """,
            {'member_id': comment['member_id']}
            )

        comment.pop('member_id')
        comment['post_writer'] = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify(comments[request_start:request_end])
