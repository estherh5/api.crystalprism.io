import bcrypt
import json
import os
import psycopg2 as pg
import time
import testing.postgresql
import unittest

from base64 import b64encode
from server import app
from testing.common.database import DatabaseFactory

import management


now = str(round(time.time()))  # Current time in ms


# Create database tables and load initial data from fixtures into test database
def initialize_test_database(postgresql):
    db_port = postgresql.dsn()['port']
    db_host = postgresql.dsn()['host']
    db_user = postgresql.dsn()['user']
    database = postgresql.dsn()['database']
    os.environ['DB_NAME'] = database

    os.environ['DB_CONNECTION'] = ('dbname=' + database + ' user=' + db_user +
        ' host=' + db_host + ' port=' + str(db_port))

    # Create database tables
    management.initialize_database()

    # Connect to database with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Add 10 sample user accounts to database
    for id in range(1, 11):
        username = 'user' + str(id)
        password = 'password'

        password = password.encode()
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        cursor.execute(
            """
            INSERT INTO cp_user
                        (username, password)
                 VALUES (%(username)s, %(password)s);
            """,
            {'username': username,
            'password': hashed_password.decode()}
            )

    # Add 10 sample posts to database
    posts_file = 'fixtures/test-post.json'
    with open(posts_file, 'r') as post_data:
        post = json.load(post_data)

    for i in range(10):
        cursor.execute(
            """
            INSERT INTO post (member_id)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE LOWER(username) = %(username)s)
                 )
              RETURNING post_id;
            """,
            {'username': 'user1'}
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
            {'content': post['content'],
            'post_id': post_id,
            'public': post['public'],
            'title': post['title']}
            )

    # Update a post to create post history
    cursor.execute(
        """
        INSERT INTO post_content
                    (content, created, post_id, public, title)
             VALUES (%(content)s, %(created)s, %(post_id)s, %(public)s,
                    %(title)s);
        """,
        {'content': post['content'],
        'created': post['modified'],
        'post_id': 1,
        'public': post['public'],
        'title': post['title']}
        )

    cursor.execute(
        """
        UPDATE post
           SET modified = %(modified)s
         WHERE post_id = %(post_id)s;
        """,
        {'modified': post['modified'],
        'post_id': 1}
        )

    # Add 10 sample comments for post to database
    comment_file = 'fixtures/test-comment.json'
    with open(comment_file, 'r') as comment_data:
        comment = json.load(comment_data)

    for i in range(10):
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
            {'username': 'user1',
            'post_id': 1}
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
            'content': comment['content']}
            )

    # Update a comment to get comment history
    cursor.execute(
        """
        INSERT INTO comment_content
                    (comment_id, content, created)
             VALUES (%(comment_id)s, %(content)s, %(created)s);
        """,
        {'comment_id': 1,
        'content': comment['content'],
        'created': comment['modified']}
        )

    cursor.execute(
        """
        UPDATE comment
           SET modified = %(modified)s
         WHERE comment_id = %(comment_id)s;
        """,
        {'modified': comment['modified'],
        'comment_id': 1}
        )

    # Add 10 sample drawings to database
    drawing_file = 'fixtures/test-drawing.json'
    with open(drawing_file, 'r') as drawing_data:
        drawing = json.load(drawing_data)

    for i in range(10):
        cursor.execute(
            """
            INSERT INTO drawing
                        (drawing_id, member_id, title, url)
                 VALUES (%(drawing_id)s,
                        (SELECT member_id
                           FROM cp_user
                          WHERE LOWER(username) = %(username)s),
                        %(title)s, %(url)s);
            """,
            {'drawing_id': str(i),
            'username': 'user1',
            'title': drawing['title'],
            'url': drawing['url']}
            )

        # Add 1 like for each drawing to database
        cursor.execute(
            """
            INSERT INTO drawing_like
                        (member_id, drawing_id)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE LOWER(username) = %(username)s),
                         %(drawing_id)s
                 );
            """,
            {'username': 'user1',
            'drawing_id': str(i)}
            )

    # Add 10 likes for one drawing to database
    for id in range(1, 11):
        username = 'user' + str(id)

        cursor.execute(
            """
            INSERT INTO drawing_like
                        (member_id, drawing_id)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE LOWER(username) = %(username)s),
                         %(drawing_id)s
                 );
            """,
            {'username': username.lower(),
            'drawing_id': str(1)}
            )

    # Add 5 sample Shapes in Rain scores to database
    shapes_file = 'fixtures/shapes_scores.json'
    with open(shapes_file, 'r') as shapes_scores:
        shapes_scores = json.load(shapes_scores)

    for shapes_score in shapes_scores:
        cursor.execute(
            """
            INSERT INTO shapes_score
                        (member_id, score)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE LOWER(username) = %(username)s),
                         %(score)s
                 );
            """,
            {'username': 'user1',
            'score': shapes_score['score']}
            )

    # Add 5 sample Rhythm of Life scores to database
    rhythm_file = 'fixtures/rhythm_scores.json'
    with open(rhythm_file, 'r') as rhythm_scores:
        rhythm_scores = json.load(rhythm_scores)

    for rhythm_score in rhythm_scores:
        cursor.execute(
            """
            INSERT INTO rhythm_score
                        (member_id, score)
                 VALUES (
                         (SELECT member_id
                            FROM cp_user
                           WHERE LOWER(username) = %(username)s),
                         %(score)s
                 );
            """,
            {'username': 'user1',
            'score': rhythm_score['score']}
            )

    # Create owner user and 10 homepage posts
    cursor.execute(
        """
        INSERT INTO cp_user
                    (username, email, is_owner, password)
             VALUES (%(username)s, %(email)s, %(is_owner)s, %(password)s);
        """,
        {'username': 'owner',
        'email': 'admin@crystalprism.io',
        'is_owner': True,
        'password': hashed_password.decode()}
        )

    for i in range(10):
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
            {'username': 'owner'}
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
            {'content': post['content'],
            'post_id': post_id,
            'public': post['public'],
            'title': post['title']}
            )

    # Update a post to create post history
    cursor.execute(
        """
        INSERT INTO post_content
                    (content, created, post_id, public, title)
             VALUES (%(content)s, %(created)s, %(post_id)s, %(public)s,
                    %(title)s);
        """,
        {'content': post['content'],
        'created': post['modified'],
        'post_id': 11,
        'public': post['public'],
        'title': post['title']}
        )

    cursor.execute(
        """
        UPDATE post
           SET modified = %(modified)s
         WHERE post_id = %(post_id)s;
        """,
        {'modified': post['modified'],
        'post_id': 11}
        )

    conn.commit()

    cursor.close()
    conn.close()


# Create factory instance of Postgresql class that has cached database for
# testing
class PostgresqlFactory(DatabaseFactory):
    target_class = testing.postgresql.Postgresql


Postgresql = PostgresqlFactory(cache_initialized_db=True,
                               on_initialized=initialize_test_database)


class CrystalPrismTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.token = ''  # Login JWT token
        self.username = ''  # Username of test user
        self.postgresql = Postgresql()
        self.db_port = self.postgresql.dsn()['port']
        self.db_host = self.postgresql.dsn()['host']
        self.db_user = self.postgresql.dsn()['user']
        self.database = self.postgresql.dsn()['database']

        os.environ['DB_CONNECTION'] = ('dbname=' + self.database + ' user=' +
            self.db_user + ' host=' + self.db_host + ' port=' +
            str(self.db_port))

    def tearDown(self):
        self.delete_user()
        self.delete_admin_user()
        self.postgresql.stop()

    # Create test user
    def create_user(self, username='test' + now, password='password'):
        self.username = username
        data = {'username': username, 'password': password}

        response = self.client.post(
            '/api/user',
            data=json.dumps(data),
            content_type='application/json'
        )

    # Log in as test user and receive JWT token
    def login(self, username='test' + now, password='password'):
        b64_user_pass = str(b64encode((username + ':' + password).encode())
            .decode())
        header = {'Authorization': 'Basic ' + b64_user_pass}

        response = self.client.get(
            '/api/login',
            headers=header
        )
        self.token = response.get_data(as_text=True)

    # Delete test user as admin
    def delete_user(self, username_to_delete='test' + now,
        admin_username='admin' + now, admin_password='password'):
        self.create_user(admin_username, admin_password)

        conn = pg.connect(os.environ['DB_CONNECTION'])

        cursor = conn.cursor()

        # Set 'is_admin' item in user account to True
        cursor.execute(
            """
            UPDATE cp_user
               SET is_admin = TRUE
             WHERE username = %(username)s;
            """,
            {'username': admin_username}
            )

        conn.commit()

        cursor.close()
        conn.close()

        self.login(admin_username, admin_password)
        header = {'Authorization': 'Bearer ' + self.token}

        response = self.client.delete(
            '/api/user/data/' + username_to_delete,
            headers=header
        )

    # Delete admin user
    def delete_admin_user(self, username='admin' + now, password='password'):
        self.login(username, password)

        header = {'Authorization': 'Bearer ' + self.token}

        response = self.client.delete(
            '/api/user/data/' + username,
            headers=header
        )
