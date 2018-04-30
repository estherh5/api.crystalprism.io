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
          SELECT post.created, post.modified, post.post_id,
                 post_content.public, cp_user.username
            FROM post
                 JOIN post_content
                   ON post_content.created = post.modified
                      AND post_content.post_id = post.post_id
                 JOIN cp_user
                   ON post.member_id = cp_user.member_id
           WHERE cp_user.is_owner = TRUE
                 AND public = TRUE
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

    # Get photo filenames from S3 bucket
    photos = [item.key for item in bucket.objects.filter(
        Prefix=bucket_folder, Delimiter='/') if item.key != bucket_folder]

    # Sort photos numerically by filename, which should be named as "1.png",
    # "2.png", etc.
    photos = sorted(photos, key=lambda item: (int(
        item.split(bucket_folder)[1].split('.')[0].split('-')[0])))

    # Add photos to URL list
    for photo in photos:
        urls.append(os.environ['S3_URL'] + photo)

    return jsonify(urls[request_start:request_end])
