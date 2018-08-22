import os
import psycopg2 as pg
import psycopg2.extras

from flask import jsonify, make_response, request


def create_score(requester):
    # Request should contain:
    # score <int>
    data = request.get_json()

    # Return error if request is missing data
    if not data or 'score' not in data:
        return make_response('Request must contain score', 400)

    # Return error if score is not an integer
    if not isinstance(data['score'], int):
        return make_response('Score must be an integer', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Add score to database
    cursor.execute(
        """
        INSERT INTO rhythm_score
                    (member_id, score)
             VALUES (
                     (SELECT member_id
                        FROM cp_user
                       WHERE LOWER(username) = %(username)s),
                      %(score)s
             )
          RETURNING score_id;
        """,
        {'username': requester.lower(), 'score': data['score']}
        )

    score_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return make_response(str(score_id), 201)


def read_score(score_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Retrieve score from database
    cursor.execute(
        """
        SELECT rhythm_score.created, rhythm_score.score, rhythm_score.score_id,
               cp_user.username
          FROM rhythm_score, cp_user
         WHERE score_id = %(score_id)s
               AND rhythm_score.member_id = cp_user.member_id;
        """,
        {'score_id': score_id}
        )

    score = cursor.fetchone()

    cursor.close()
    conn.close()

    # Return error if score not found
    if not score:
        return make_response('Not found', 404)

    # Otherwise, convert score to dictionary
    score = dict(score)

    return jsonify(score)


def delete_score(requester, score_id):
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get score from database
    cursor.execute(
        """
        SELECT rhythm_score.*, cp_user.username
          FROM rhythm_score, cp_user
         WHERE score_id = %(score_id)s
               AND rhythm_score.member_id = cp_user.member_id;
        """,
        {'score_id': score_id}
        )

    score = cursor.fetchone()

    # Return error if score not found
    if not score:
        cursor.close()
        conn.close()

        return make_response('Not found', 404)

    # Otherwise, convert score to dictionary
    score = dict(score)

    # Return error if requester is not the player
    if requester.lower() != score['username'].lower():
        cursor.close()
        conn.close()

        return make_response('Unauthorized', 401)

    # Delete score from database
    cursor.execute(
        """
        DELETE FROM rhythm_score
              WHERE score_id = %(score_id)s;
        """,
        {'score_id': score_id}
        )

    conn.commit()

    cursor.close()
    conn.close()

    return make_response('Success', 200)


def read_scores():
    # Get number of requested scores from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 5))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get requested game scores, sorted by highest to lowest score
    cursor.execute(
        """
          SELECT rhythm_score.created, rhythm_score.score,
                 rhythm_score.score_id, cp_user.username
            FROM rhythm_score, cp_user
           WHERE rhythm_score.member_id = cp_user.member_id
        ORDER BY score DESC;
        """
        )

    scores = []

    for row in cursor.fetchall():
        scores.append(dict(row))

    cursor.close()
    conn.close()

    return jsonify(scores[request_start:request_end])


def read_scores_for_one_user(player_name):
    # Get number of requested scores from query parameters, using default if
    # null
    request_start = int(request.args.get('start', 0))
    request_end = int(request.args.get('end', request_start + 5))

    # Return error if start query parameter is greater than end
    if request_start > request_end:
        return make_response('Start param cannot be greater than end', 400)

    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor(cursor_factory=pg.extras.DictCursor)

    # Get requested game scores, sorted by highest to lowest score
    cursor.execute(
        """
          SELECT rhythm_score.created, rhythm_score.score,
                 rhythm_score.score_id, cp_user.username
            FROM rhythm_score, cp_user
           WHERE LOWER(cp_user.username) = %(username)s
                 AND rhythm_score.member_id = cp_user.member_id
        ORDER BY score DESC;
        """,
        {'username': player_name.lower()}
        )

    scores = []

    for row in cursor.fetchall():
        scores.append(dict(row))

    cursor.close()
    conn.close()

    return jsonify(scores[request_start:request_end])
