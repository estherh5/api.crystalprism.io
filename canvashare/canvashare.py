import boto3
import os
import psycopg2 as pg
import psycopg2.extras

from base64 import decodebytes
from flask import jsonify, make_response, request
from io import BytesIO
from PIL import Image

from user import user


def create_drawing(requester):
    # Request should contain:
    # drawing <data:image/png;base64...>
    # title <str>
    data = request.get_json()

    # Return error if request is missing data
    if not data or 'drawing' not in data or 'title' not in data:
        return make_response('Request must contain drawing and title', 400)

    # Return error if drawing is not base64-encoded PNG image
    if 'data:image/png;base64' not in data['drawing']:
        return make_response('Drawing must be base64-encoded PNG image', 400)

    # Return error if title is blank
    if not data['title']:
        return make_response('Drawing title cannot be blank', 400)

    # Remove 'data:image/png;base64' from image data URL
    drawing = decodebytes(data['drawing'].split(',')[1].encode('utf-8'))

    # Reduce drawing size to generate average hash for assessing drawing
    # uniqueness
    drawing_small = Image.open(BytesIO(drawing)).resize(
        (8, 8), Image.ANTIALIAS)

    # Convert small drawing to grayscale
    drawing_small = drawing_small.convert('L')

    # Get average pixel value of small drawing
    pixels = list(drawing_small.getdata())
    average_pixels = sum(pixels) / len(pixels)

    # Generate bit string by comparing each pixel in the small drawing to the
    # average pixel value
    bit_string = "".join(map(
        lambda pixel: '1' if pixel < average_pixels else '0', pixels))

    # Generate unique id for drawing by converting bit string to hexadecimal
    drawing_id = int(bit_string, 2).__format__('016x')

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Check if drawing_id already exists in database (i.e., if user is
    # submitting a duplicate drawing)
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM drawing WHERE drawing_id = %(drawing_id)s LIMIT 1);
        """,
        {'drawing_id': drawing_id}
        )

    if cursor.fetchone()[0]:
        cursor.close()
        conn.close()

        return make_response('Drawing already exists', 409)

    # Upload drawing to S3 bucket
    s3 = boto3.resource('s3')
    bucket_name = os.environ['S3_BUCKET']
    bucket = s3.Bucket(bucket_name)
    bucket_folder = os.environ['S3_CANVASHARE_DIR']

    drawing_name = drawing_id + '.png'

    bucket.put_object(
        Key=bucket_folder + drawing_name,
        Body=drawing
        )

    # Add drawing to database
    cursor.execute(
        """
        INSERT INTO drawing (drawing_id, member_id, title, url)
        VALUES (%(drawing_id)s, (SELECT member_id FROM cp_user
        WHERE LOWER(username) = %(username)s), %(title)s, %(url)s);
        """,
        {'drawing_id': drawing_id,
        'username': requester.lower(),
        'title': data['title'],
        'url': os.environ['S3_URL'] + bucket_folder + drawing_name}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response(drawing_id, 201)


def read_drawing(drawing_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve drawing information from database
    cursor.execute(
        """
        SELECT drawing.created, drawing.drawing_id, drawing.title, drawing.url,
        drawing.views, cp_user.username FROM drawing
        JOIN cp_user ON drawing.member_id = cp_user.member_id
        WHERE drawing_id = %(drawing_id)s;
        """,
        {'drawing_id': drawing_id}
        )

    drawing_data = cursor.fetchone()

    # Return error if drawing not found
    if not drawing_data:
        return make_response('Not found', 404)

    # Otherwise, convert drawing data to dictionary
    drawing_data = dict(drawing_data)

    # Get drawing's likers and like count from database
    cursor.execute(
        """
        SELECT drawing_like.drawing_like_id, cp_user.username
        FROM drawing_like
        JOIN cp_user ON drawing_like.member_id = cp_user.member_id
        WHERE drawing_id = %(drawing_id)s;
        """,
        {'drawing_id': drawing_id}
        )

    drawing_data['likers'] = []

    for row in cursor.fetchall():
        drawing_data['likers'].append(dict(row))

    drawing_data['like_count'] = len(drawing_data['likers'])

    cursor.close()
    conn.close()

    # Return drawing data to client
    return jsonify(drawing_data)


def update_drawing(drawing_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Retrieve current drawing views from database
    cursor.execute(
        """
        SELECT views FROM drawing WHERE drawing_id = %(drawing_id)s;
        """,
        {'drawing_id': drawing_id}
        )

    drawing_views = cursor.fetchone()

    # Return error if drawing not found
    if not drawing_views:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Increment views for drawing in database
    cursor.execute(
        """
        UPDATE drawing SET views = %(views)s
        WHERE drawing_id = %(drawing_id)s;
        """,
        {'views': drawing_views[0] + 1,
        'drawing_id': drawing_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def delete_drawing(requester, drawing_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get drawing from database
    cursor.execute(
        """
        SELECT drawing.*, cp_user.username FROM drawing
        JOIN cp_user ON drawing.member_id = cp_user.member_id
        WHERE drawing_id = %(drawing_id)s;
        """,
        {'drawing_id': drawing_id}
        )

    drawing = cursor.fetchone()

    # Return error if drawing not found
    if not drawing:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert drawing to dictionary
    drawing = dict(drawing)

    # Return error if requester is not the artist
    if requester.lower() != drawing['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Delete drawing from database
    cursor.execute(
        """
        DELETE FROM drawing WHERE drawing_id = %(drawing_id)s;
        """,
        {'drawing_id': drawing_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    # Remove drawing from S3 bucket
    s3 = boto3.resource('s3')
    bucket_name = os.environ['S3_BUCKET']
    bucket_folder = os.environ['S3_CANVASHARE_DIR']

    drawing_name = str(drawing_id) + '.png'

    s3.Object(bucket_name, bucket_folder + drawing_name).delete()

    return make_response('Success', 200)


def read_drawings():
    # Get number of requested drawings from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve drawings from database
    cursor.execute(
        """
        SELECT drawing.created, drawing.drawing_id, drawing.title, drawing.url,
        drawing.views, cp_user.username FROM drawing
        JOIN cp_user ON drawing.member_id = cp_user.member_id
        ORDER BY created DESC;
        """
        )

    drawings = []

    for row in cursor.fetchall():
        drawings.append(dict(row))

    # Get each drawing's likers and like count from database
    for drawing in drawings:
        cursor.execute(
            """
            SELECT drawing_like.drawing_like_id, cp_user.username
            FROM drawing_like
            JOIN cp_user ON drawing_like.member_id = cp_user.member_id
            WHERE drawing_id = %(drawing_id)s;
            """,
            {'drawing_id': drawing['drawing_id']}
            )

        drawing['likers'] = []

        for row in cursor.fetchall():
            drawing['likers'].append(dict(row))

        drawing['like_count'] = len(drawing['likers'])

    cursor.close()
    conn.close()

    return jsonify(drawings[request_start:request_end])


def read_drawings_for_one_user(artist_name):
    # Get number of requested drawings from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve drawings from database
    cursor.execute(
        """
        SELECT drawing.created, drawing.drawing_id, drawing.title, drawing.url,
        drawing.views, cp_user.username FROM drawing
        JOIN cp_user ON drawing.member_id = cp_user.member_id
        WHERE LOWER(cp_user.username) = %(username)s
        ORDER BY created DESC;
        """,
        {'username': artist_name.lower()}
        )

    drawings = []

    for row in cursor.fetchall():
        drawings.append(dict(row))

    # Get each drawing's likers and like count from database
    for drawing in drawings:
        cursor.execute(
            """
            SELECT drawing_like.drawing_like_id, cp_user.username
            FROM drawing_like
            JOIN cp_user ON drawing_like.member_id = cp_user.member_id
            WHERE drawing_id = %(drawing_id)s;
            """,
            {'drawing_id': drawing['drawing_id']}
            )

        drawing['likers'] = []

        for row in cursor.fetchall():
            drawing['likers'].append(dict(row))

        drawing['like_count'] = len(drawing['likers'])

    cursor.close()
    conn.close()

    return jsonify(drawings[request_start:request_end])


def create_drawing_like(requester):
    # Request should contain:
    # drawing_id <str>
    data = request.get_json()

    # Return error if request is missing data
    if not data or 'drawing_id' not in data:
        return make_response('Request must contain drawing id', 400)

    # Return error if drawing id is blank or not a string
    if not data['drawing_id'] or not isinstance(data['drawing_id'], str):
        return make_response('Drawing id must be a string', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Verify that drawing exists
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM drawing
        WHERE drawing_id = %(drawing_id)s LIMIT 1);
        """,
        {'drawing_id': data['drawing_id']}
        )

    drawing = cursor.fetchone()[0]

    # Return error if drawing not found
    if not drawing:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Verify that user did not like drawing previously
    cursor.execute(
        """
        SELECT exists (
        SELECT 1 FROM drawing_like
        WHERE drawing_id = %(drawing_id)s AND member_id =
        (SELECT member_id FROM cp_user
        WHERE LOWER(username) = %(username)s) LIMIT 1);
        """,
        {'drawing_id': data['drawing_id'],
        'username': requester.lower()}
        )

    drawing_like = cursor.fetchone()[0]

    if drawing_like:
        cursor.close()
        conn.close()

        return make_response('User already liked drawing', 400)

    # Add drawing like to database
    cursor.execute(
        """
        INSERT INTO drawing_like (member_id, drawing_id)
        VALUES ((SELECT member_id FROM cp_user
        WHERE LOWER(username) = %(username)s), %(drawing_id)s)
        RETURNING drawing_like_id;
        """,
        {'username': requester.lower(),
        'drawing_id': data['drawing_id']}
        )

    drawing_like_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return make_response(str(drawing_like_id), 201)


def read_drawing_like(drawing_like_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get drawing like from database
    cursor.execute(
        """
        SELECT drawing_like.created, drawing_like.drawing_id,
        drawing_like.drawing_like_id, cp_user.username FROM drawing_like
        JOIN cp_user ON drawing_like.member_id = cp_user.member_id
        WHERE drawing_like_id = %(drawing_like_id)s;
        """,
        {'drawing_like_id': drawing_like_id}
        )

    drawing_like = cursor.fetchone()

    cursor.close()
    conn.close()

    # Return error if drawing like not found
    if not drawing_like:
        return make_response('Not found', 404)

    # Otherwise, convert drawing like data to dictionary
    drawing_like = dict(drawing_like)

    return jsonify(drawing_like)


def delete_drawing_like(requester, drawing_like_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Verify that user liked drawing previously
    cursor.execute(
        """
        SELECT drawing_like.*, cp_user.username FROM drawing_like
        JOIN cp_user ON drawing_like.member_id = cp_user.member_id
        WHERE drawing_like_id = %(drawing_like_id)s;
        """,
        {'drawing_like_id': drawing_like_id}
        )

    drawing_like = cursor.fetchone()

    # Return error if user did not like drawing previously
    if not drawing_like:
        cursor.close()
        conn.close()

        return make_response('User did not like drawing', 400)

    # Otherwise, convert drawing_like to dictionary
    drawing_like = dict(drawing_like)

    # Return error if requester is not the liker
    if requester.lower() != drawing_like['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Delete like for drawing in database
    cursor.execute(
        """
        DELETE FROM drawing_like
        WHERE drawing_like_id = %(drawing_like_id)s;
        """,
        {'drawing_like_id': drawing_like_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def read_drawing_likes(drawing_id):
    # Get number of requested drawing likes from query parameters, using
    # default if null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve drawing likes from database
    cursor.execute(
        """
        SELECT drawing_like.created, drawing_like.drawing_id,
        drawing_like.drawing_like_id, cp_user.username FROM drawing_like
        JOIN cp_user ON drawing_like.member_id = cp_user.member_id
        INNER JOIN drawing ON drawing_like.drawing_id = drawing.drawing_id
        WHERE drawing_like.drawing_id = %(drawing_id)s
        ORDER BY created DESC;
        """,
        {'drawing_id': drawing_id}
        )

    drawing_likes = []

    for row in cursor.fetchall():
        drawing_likes.append(dict(row))

    cursor.close()
    conn.close()

    return jsonify(drawing_likes[request_start:request_end])


def read_drawing_likes_for_one_user(liker_name):
    # Get number of requested drawings from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 10))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve drawing likes from database
    cursor.execute(
        """
        SELECT drawing_like.created, drawing_like.drawing_like_id,
        drawing.drawing_id, drawing.url, drawing.title, drawing.views,
        drawing.member_id, cp_user.username FROM drawing_like
        JOIN drawing ON drawing_like.drawing_id = drawing.drawing_id
        JOIN cp_user ON drawing_like.member_id = cp_user.member_id
        WHERE LOWER(cp_user.username) = %(username)s
        ORDER BY drawing_like.created DESC;
        """,
        {'username': liker_name.lower()}
        )

    drawing_likes = []

    for row in cursor.fetchall():
        drawing_likes.append(dict(row))

    # Replace each drawing artist's member id with username and get each
    # drawing's likers and like count from database
    for drawing_like in drawing_likes:
        cursor.execute(
            """
            SELECT username FROM cp_user
            WHERE member_id = %(member_id)s;
            """,
            {'member_id': drawing_like['member_id']}
            )

        drawing_like.pop('member_id')
        drawing_like['artist_name'] = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT drawing_like.drawing_like_id, cp_user.username
            FROM drawing_like
            JOIN cp_user ON drawing_like.member_id = cp_user.member_id
            WHERE drawing_id = %(drawing_id)s;
            """,
            {'drawing_id': drawing_like['drawing_id']}
            )

        drawing_like['likers'] = []

        for row in cursor.fetchall():
            drawing_like['likers'].append(dict(row))

        drawing_like['like_count'] = len(drawing_like['likers'])

    cursor.close()
    conn.close()

    return jsonify(drawing_likes[request_start:request_end])
