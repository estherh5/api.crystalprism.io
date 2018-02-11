import json
import re

from server import app
from utils.tests import CrystalPrismTestCase


# Test /api/thought-writer/post endpoint [POST, GET, PATCH, DELETE]
class TestPost(CrystalPrismTestCase):
    def test_post_post_get_patch_and_delete(self):
        # Arrange [POST]
        # Create user and login to get token for Authorization header
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_data = {'title': 'Test', 'content': 'Test', 'public': False}

        # Act [POST]
        post_response = self.client.post(
            '/api/thought-writer/post',
            headers=header,
            data=json.dumps(post_data),
            content_type='application/json'
            )
        timestamp = post_response.get_data(as_text=True)

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)

        # Ensure timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d.\d{6}\+\d\d:\d\d'
            )
        self.assertEqual(bool(timestamp_pattern.match(timestamp)), True)

        # Act [GET]
        get_response = self.client.get(
            '/api/thought-writer/post/' + self.username + '/' + timestamp,
            headers=header
            )
        post = json.loads(get_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post['title'], 'Test')
        self.assertEqual(bool(timestamp_pattern.match(
            post['timestamp'])), True
            )
        self.assertEqual(post['content'], 'Test')
        self.assertEqual(post['public'], False)
        self.assertEqual(post['comments'], [])

        # Arrange [PATCH]
        patch_data = {'title': 'Test 2', 'timestamp': timestamp,
            'content': 'Test 2', 'public': True}

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/thought-writer/post',
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )

        patched_get_response = self.client.get(
            '/api/thought-writer/post/' + self.username + '/' + timestamp,
            headers=header
            )
        patched_post = json.loads(patched_get_response.get_data(as_text=True))

        # Assert [PATCH]
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patched_get_response.status_code, 200)
        self.assertEqual(patched_post['title'], 'Test 2')
        self.assertEqual(bool(timestamp_pattern.match(
            patched_post['timestamp'])), True
            )
        self.assertEqual(patched_post['content'], 'Test 2')
        self.assertEqual(patched_post['public'], True)
        self.assertEqual(patched_post['comments'], [])

        # Arrange [DELETE]
        delete_data = {'timestamp': timestamp}

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/thought-writer/post',
            headers=header,
            data=json.dumps(delete_data),
            content_type='application/json'
            )

        deleted_get_response = self.client.get(
            '/api/thought-writer/post/' + self.username + '/' + timestamp,
            headers=header
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(deleted_get_response.status_code, 404)

    def test_public_post_get(self):
        writer_name = 'user'
        timestamp = '2017-10-05T00:00:00.000000+00:00'

        # Act
        get_response = self.client.get(
            '/api/thought-writer/post/' + writer_name + '/' + timestamp
            )
        post = json.loads(get_response.get_data(as_text=True))

        # Assert [POST]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post['writer'], 'user')
        self.assertEqual(post['title'], 'Welcome')
        self.assertEqual(post['timestamp'], timestamp)
        self.assertEqual('Welcome to Thought Writer' in post['content'], True)
        self.assertEqual(post['comments'], [])


# Test /api/thought-writer/comment endpoint [POST, PATCH, DELETE]
class TestComment(CrystalPrismTestCase):
    def test_comment_post_patch_and_delete(self):
        # Arrange [POST]
        # Create user and login to get token for Authorization header
        self.create_user()
        self.login()

        writer_name = 'user'
        timestamp = '2017-10-05T00:00:00.000000+00:00'

        header = {'Authorization': 'Bearer ' + self.token}
        post_data = {'content': 'Test comment'}

        # Act [POST]
        post_response = self.client.post(
            '/api/thought-writer/comment/' + writer_name + '/' + timestamp,
            headers=header,
            data=json.dumps(post_data),
            content_type='application/json'
            )

        # Retrieve post to ensure comment is now associated with it
        get_response = self.client.get(
            '/api/thought-writer/post/' + writer_name + '/' + timestamp
            )
        post = json.loads(get_response.get_data(as_text=True))
        comment_timestamp = post['comments'][0]['timestamp']

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post['comments'][0]['commenter'], self.username)

        # Ensure timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d.\d{6}\+\d\d:\d\d'
            )
        self.assertEqual(
            bool(timestamp_pattern.match(comment_timestamp)), True
            )

        self.assertEqual(post['comments'][0]['content'], 'Test comment')

        # Arrange [PATCH]
        patch_data = {
            'content': 'Test comment 2',
            'timestamp': comment_timestamp
            }

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/thought-writer/comment/' + writer_name + '/' + timestamp,
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )

        # Retrieve post to ensure updated comment is now associated with it
        patched_get_response = self.client.get(
            '/api/thought-writer/post/' + writer_name + '/' + timestamp
            )
        patched_post = json.loads(patched_get_response.get_data(as_text=True))
        patched_timestamp = patched_post['comments'][0]['timestamp']

        # Assert [PATCH]
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patched_get_response.status_code, 200)
        self.assertEqual(
            patched_post['comments'][0]['commenter'], self.username
            )

        # Ensure timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d.\d{6}\+\d\d:\d\d'
            )
        self.assertEqual(
            bool(timestamp_pattern.match(patched_timestamp)), True
            )

        self.assertEqual(
            patched_post['comments'][0]['content'], 'Test comment 2'
            )

        # Arrange [DELETE]
        delete_data = {'timestamp': patched_timestamp}

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/thought-writer/comment/' + writer_name + '/' + timestamp,
            headers=header,
            data=json.dumps(delete_data),
            content_type='application/json'
            )

        # Retrieve post to ensure deleted comment is not associated with it
        deleted_get_response = self.client.get(
            '/api/thought-writer/post/' + writer_name + '/' + timestamp
            )
        deleted_comment_post = json.loads(
            deleted_get_response.get_data(as_text=True)
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(deleted_get_response.status_code, 200)
        self.assertEqual(deleted_comment_post['comments'], [])
