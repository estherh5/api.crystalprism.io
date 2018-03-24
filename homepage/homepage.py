import boto3
import os
import psycopg2 as pg
import psycopg2.extras

from flask import jsonify, make_response, request


def read_ideas():
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
        SELECT post.content, post.created, post.post_id, post.title,
        cp_user.username FROM post
        JOIN cp_user ON post.member_id = cp_user.member_id
        WHERE cp_user.is_owner = TRUE AND public = TRUE
        ORDER BY created DESC;
        """
        )

    posts = []

    for row in cursor.fetchall():
        posts.append(dict(row))

    cursor.close()
    conn.close()

    return jsonify(posts[request_start:request_end])


def read_photos():
    # Get number of requested photos from query parameters, using default
    # if null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    urls = []

    s3 = boto3.resource('s3')
    bucket_name = os.environ['S3_BUCKET']
    bucket = s3.Bucket(bucket_name)
    bucket_folder = os.environ['S3_PHOTO_DIR']

    for item in bucket.objects.filter(Prefix=bucket_folder, Delimiter='/'):

        # Exclude bucket folder from URLs list
        if item.key != bucket_folder:
            urls.append(os.environ['S3_URL'] + item.key)

    return jsonify(urls[request_start:request_end])
