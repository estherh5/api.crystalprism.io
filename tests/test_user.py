import boto3
import hmac
import json
import os
import re

from base64 import b64encode, urlsafe_b64encode
from hashlib import sha256
from math import floor
from time import time
from unittest.mock import patch
from utils.tests import CrystalPrismTestCase


# Test /api/login endpoint [GET]
class TestLogin(CrystalPrismTestCase):
    def test_login_get(self):
        # Arrange
        self.create_user()

        b64_user_pass = str(b64encode((self.username + ':password').encode())
            .decode())
        header = {'Authorization': 'Basic ' + b64_user_pass}

        # Act
        get_response = self.client.get(
            '/api/login',
            headers=header
        )
        token = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 200)

        # Ensure patched token is correct format
        token_pattern = re.compile(
            r'^[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}' +
            r'\.[a-zA-Z0-9-_]+={0,2}$'
            )
        self.assertEqual(bool(token_pattern.match(token)), True)

    def test_login_get_verify_error(self):
        # Act
        get_response = self.client.get('/api/login')
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_login_get_not_found_error(self):
        # Arrange
        username = 'test'

        b64_user_pass = str(b64encode((username + ':password').encode())
            .decode())
        header = {'Authorization': 'Basic ' + b64_user_pass}

        # Act
        get_response = self.client.get(
            '/api/login',
            headers=header
        )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_login_get_username_deleted_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Soft-delete user
        self.client.delete(
            '/api/user/' + self.username,
            headers=header
            )

        # Generate login header for deleted user
        b64_user_pass = str(b64encode((self.username + ':password').encode())
            .decode())
        login_header = {'Authorization': 'Basic ' + b64_user_pass}

        # Act
        get_response = self.client.get(
            '/api/login',
            headers=login_header
        )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_login_get_password_error(self):
        # Arrange
        self.create_user()

        b64_user_pass = str(b64encode((self.username + ':incorrect').encode())
            .decode())
        header = {'Authorization': 'Basic ' + b64_user_pass}

        # Act
        get_response = self.client.get(
            '/api/login',
            headers=header
        )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/user endpoint [POST, GET, PATCH, DELETE]
class TestUser(CrystalPrismTestCase):
    def test_user_post_get_patch_and_soft_delete(self):
        # Arrange [POST]
        username = 'test_user'
        password = 'password'
        post_data = {
            'username': username,
            'password': password
            }

        # Act [POST]
        post_response = self.client.post(
            '/api/user',
            data=json.dumps(post_data),
            content_type='application/json'
            )
        self.login(username, password)

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)

        # Arrange [GET]
        header = {'Authorization': 'Bearer ' + self.token}

        # Act [GET]
        get_response = self.client.get(
            '/api/user/' + username,
            headers=header
            )
        user_data = json.loads(get_response.get_data(as_text=True))

        get_public_response = self.client.get(
            '/api/user/' + username
            )
        public_user_data = json.loads(
            get_public_response.get_data(as_text=True)
            )

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(user_data['about'], None)
        self.assertEqual(user_data['background_color'], '#ffffff')
        self.assertEqual(user_data['comment_count'], 0)
        self.assertEqual(user_data['drawing_count'], 0)
        self.assertEqual(user_data['drawing_like_count'], 0)
        self.assertEqual(user_data['email'], None)
        self.assertEqual(user_data['email_public'], False)
        self.assertEqual(user_data['first_name'], None)
        self.assertEqual(user_data['last_name'], None)
        self.assertEqual(user_data['icon_color'], '#000000')
        self.assertEqual(user_data['name_public'], False)
        self.assertEqual(user_data['post_count'], 0)
        self.assertEqual(user_data['rhythm_high_score'], 0)
        self.assertEqual(user_data['rhythm_score_count'], 0)
        self.assertEqual(user_data['shapes_high_score'], 0)
        self.assertEqual(user_data['shapes_score_count'], 0)
        self.assertEqual(user_data['status'], 'active')
        self.assertEqual(user_data['username'], username)

        self.assertEqual(get_public_response.status_code, 200)
        self.assertEqual(public_user_data['about'], None)
        self.assertEqual(public_user_data['background_color'], '#ffffff')
        self.assertEqual(public_user_data['comment_count'], 0)
        self.assertEqual(public_user_data['drawing_count'], 0)
        self.assertEqual(public_user_data['drawing_like_count'], 0)
        self.assertEqual(public_user_data['icon_color'], '#000000')
        self.assertEqual(public_user_data['post_count'], 0)
        self.assertEqual(public_user_data['rhythm_high_score'], 0)
        self.assertEqual(public_user_data['rhythm_score_count'], 0)
        self.assertEqual(public_user_data['shapes_high_score'], 0)
        self.assertEqual(public_user_data['shapes_score_count'], 0)
        self.assertEqual(public_user_data['status'], 'active')
        self.assertEqual(public_user_data['username'], username)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            user_data['created'])), True
            )

        # Arrange [PATCH]
        updated_username = 'test_user2'
        updated_password = 'password2'
        patch_data = {
            'about': 'Test',
            'background_color': '#000000',
            'email': 'test@crystalprism.io',
            'email_public': True,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'Test',
            'name_public': True,
            'password': updated_password,
            'username': updated_username
            }

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/user/' + username,
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )
        patched_token = patch_response.get_data(as_text=True)
        patched_header = {'Authorization': 'Bearer ' + patched_token}

        patched_get_response = self.client.get(
            '/api/user/' + updated_username,
            headers=patched_header
            )
        patched_user_data = json.loads(
            patched_get_response.get_data(as_text=True)
            )

        patched_get_public_response = self.client.get(
            '/api/user/' + updated_username
            )

        patched_public_user_data = json.loads(
            patched_get_public_response.get_data(as_text=True)
            )

        # Assert [PATCH]
        self.assertEqual(patch_response.status_code, 200)

        # Ensure patched token is correct format
        token_pattern = re.compile(
            r'^[a-zA-Z0-9-_]+={0,2}\.[a-zA-Z0-9-_]+={0,2}' +
            r'\.[a-zA-Z0-9-_]+={0,2}$'
            )
        self.assertEqual(bool(token_pattern.match(patched_token)), True)

        self.assertEqual(patched_get_response.status_code, 200)
        self.assertEqual(patched_user_data['about'], 'Test')
        self.assertEqual(patched_user_data['background_color'], '#000000')
        self.assertEqual(patched_user_data['email'], 'test@crystalprism.io')
        self.assertEqual(patched_user_data['email_public'], True)
        self.assertEqual(patched_user_data['first_name'], 'Test')
        self.assertEqual(patched_user_data['icon_color'], '#ffffff')
        self.assertEqual(patched_user_data['last_name'], 'Test')
        self.assertEqual(patched_user_data['name_public'], True)
        self.assertEqual(patched_user_data['username'], updated_username)

        self.assertEqual(patched_get_public_response.status_code, 200)
        self.assertEqual(patched_public_user_data['about'], 'Test')
        self.assertEqual(
            patched_public_user_data['background_color'], '#000000'
            )
        self.assertEqual(
            patched_public_user_data['email'], 'test@crystalprism.io'
            )
        self.assertEqual(patched_public_user_data['first_name'], 'Test')
        self.assertEqual(patched_public_user_data['icon_color'], '#ffffff')
        self.assertEqual(patched_public_user_data['last_name'], 'Test')
        self.assertEqual(
            patched_public_user_data['username'], updated_username
            )

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/user/' + updated_username,
            headers=patched_header
            )

        deleted_get_response = self.client.get(
            '/api/user/' + updated_username,
            headers=patched_header
            )
        deleted_error = deleted_get_response.get_data(as_text=True)

        deleted_get_public_response = self.client.get(
            '/api/user/' + updated_username
            )
        deleted_public_error = deleted_get_public_response.get_data(
            as_text=True
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(deleted_error, 'Not found')

        self.assertEqual(deleted_get_public_response.status_code, 404)
        self.assertEqual(deleted_public_error, 'Not found')

        # Hard-delete user for clean-up
        self.delete_user(updated_username)

    def test_user_post_data_error(self):
        # Act
        post_response = self.client.post(
            '/api/user'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Request must contain username and password')

    def test_user_post_username_blank_error(self):
        # Arrange
        username = ''
        password = 'password'
        post_data = {
            'username': username,
            'password': password
            }

        # Act
        post_response = self.client.post(
            '/api/user',
            data=json.dumps(post_data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Username cannot be blank')

    def test_user_post_username_character_error(self):
        # Arrange
        username = 'test_user$'
        password = 'password'
        post_data = {
            'username': username,
            'password': password
            }

        # Act
        post_response = self.client.post(
            '/api/user',
            data=json.dumps(post_data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Username contains unacceptable characters')

    def test_user_post_username_exists_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {
            'username': self.username,
            'password': 'password'
            }

        # Soft-delete user
        self.client.delete(
            '/api/user/' + self.username,
            headers=header
            )

        # Act
        post_response = self.client.post(
            '/api/user',
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 409)
        self.assertEqual(error, 'Username already exists')

    def test_user_post_password_error(self):
        # Arrange
        username = 'new_user'
        password = 'short'
        post_data = {
            'username': username,
            'password': password
            }

        # Act
        post_response = self.client.post(
            '/api/user',
            data=json.dumps(post_data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Password too short')

    def test_user_patch_unauthorized_error(self):
        # Arrange
        username = 'user1'

        # Act
        patch_response = self.client.patch(
            '/api/user/' + username
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_user_patch_not_user_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        username = 'user1'

        # Act
        patch_response = self.client.patch(
            '/api/user/' + username,
            headers=header
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_user_patch_data_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        patch_response = self.client.patch(
            '/api/user/' + self.username,
            headers=header
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 400)
        self.assertEqual(error, 'Request is missing required data')

    def test_user_patch_username_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {
            'about': 'Test',
            'background_color': '#000000',
            'email': 'test@crystalprism.io',
            'email_public': True,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'Test',
            'name_public': True,
            'password': 'password1',
            'username': 'user1'
            }

        # Act
        patch_response = self.client.patch(
            '/api/user/' + self.username,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 409)
        self.assertEqual(error, 'Username already exists')

    def test_user_patch_email_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {
            'about': 'Test',
            'background_color': '#000000',
            'email': 'admin@crystalprism.io',
            'email_public': True,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'Test',
            'name_public': True,
            'password': 'password1',
            'username': 'email_test'
            }

        # Act
        patch_response = self.client.patch(
            '/api/user/' + self.username,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 409)
        self.assertEqual(error, 'Email address already claimed')

    def test_user_delete_unauthorized_error(self):
        # Arrange
        username = 'user1'

        # Act
        delete_response = self.client.delete(
            '/api/user/' + username
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_user_delete_not_user_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        username = 'user1'

        # Act
        delete_response = self.client.delete(
            '/api/user/' + username,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/user/data endpoint [GET, DELETE]
class TestUserData(CrystalPrismTestCase):
    def test_user_data_get(self):
        # Arrange
        username = 'user1'
        self.login(username)
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        get_response = self.client.get(
            '/api/user/data/' + username,
            headers=header
            )

        # Act - update user data
        data = {
            'about': 'Test',
            'background_color': '#000000',
            'email': None,
            'email_public': False,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'Test',
            'name_public': True,
            'password': 'password',
            'username': username
            }

        patch_response = self.client.patch(
            '/api/user/' + username,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )

        patched_get_response = self.client.get(
            '/api/user/data/' + username,
            headers=header
            )

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.mimetype, 'application/zip')
        self.assertEqual(patched_get_response.status_code, 200)
        self.assertEqual(patched_get_response.mimetype, 'application/zip')

    def test_user_data_get_unauthorized_error(self):
        # Arrange
        username = 'user1'

        # Act
        get_response = self.client.get(
            '/api/user/data/' + username
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_user_data_get_not_user_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        username = 'user1'

        # Act
        get_response = self.client.get(
            '/api/user/data/' + username,
            headers=header
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    @patch('canvashare.canvashare.boto3')
    def test_user_hard_delete(self, boto3):
        # Arrange - set up mock for CanvaShare S3 bucket
        resource = boto3.resource.return_value
        bucket = resource.Bucket.return_value

        # Arrange - create two user accounts
        first_username = 'first_username'
        self.create_user(first_username)
        self.login(first_username)
        first_user_header = {'Authorization': 'Bearer ' + self.token}

        second_username = 'second_username'
        self.create_user(second_username)
        self.login(second_username)
        second_user_header = {'Authorization': 'Bearer ' + self.token}

        # Arrange - first user creates drawing
        test_drawing = (
            os.path.dirname(__file__) + '/../fixtures/test-drawing.txt'
            )
        with open(test_drawing, 'r') as drawing:
            drawing = drawing.read()
        drawing_data = {
            'drawing': drawing,
            'title': 'Test'
            }

        drawing_post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=first_user_header,
            data=json.dumps(drawing_data),
            content_type='application/json'
            )
        drawing_id = drawing_post_response.get_data(as_text=True)

        # Arrange - first user likes a drawing
        first_drawing_like_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=first_user_header,
            data=json.dumps({'drawing_id': '1'}),
            content_type='application/json'
            )
        first_drawing_like_id = first_drawing_like_response.get_data(
            as_text=True
            )

        # Arrange - second user likes first user's drawing
        second_drawing_like_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=second_user_header,
            data=json.dumps({'drawing_id': drawing_id}),
            content_type='application/json'
            )
        second_drawing_like_id = second_drawing_like_response.get_data(
            as_text=True
            )

        # Arrange - first user creates post
        post_data = {
            'content': 'Test',
            'public': True,
            'title': 'Test'
            }

        post_post_response = self.client.post(
            '/api/thought-writer/post',
            headers=first_user_header,
            data=json.dumps(post_data),
            content_type='application/json'
            )
        post_id = post_post_response.get_data(as_text=True)

        # Arrange - first user adds comment to post
        comment_data = {
            'content': 'Test',
            'post_id': int(post_id)
            }

        first_post_comment_response = self.client.post(
            '/api/thought-writer/comment',
            headers=first_user_header,
            data=json.dumps(comment_data),
            content_type='application/json'
            )
        first_comment_id = first_post_comment_response.get_data(as_text=True)

        # Arrange - second user adds comment to post
        second_post_comment_response = self.client.post(
            '/api/thought-writer/comment',
            headers=second_user_header,
            data=json.dumps(comment_data),
            content_type='application/json'
            )
        second_comment_id = second_post_comment_response.get_data(as_text=True)

        # Arrange - first user posts score for Shapes in Rain
        shapes_data = {'score': 100000}

        shapes_response = self.client.post(
            '/api/shapes-in-rain/score',
            headers=first_user_header,
            data=json.dumps(shapes_data),
            content_type='application/json'
            )
        shapes_score_id = shapes_response.get_data(as_text=True)

        # Arrange - first user posts score for Rhythm of Life
        rhythm_data = {'score': 360000}

        rhythm_response = self.client.post(
            '/api/rhythm-of-life/score',
            headers=first_user_header,
            data=json.dumps(rhythm_data),
            content_type='application/json'
            )
        rhythm_score_id = rhythm_response.get_data(as_text=True)

        # Act - attempt to delete first user account as second user
        delete_unauthorized_response = self.client.delete(
            '/api/user/data/' + first_username,
            headers=second_user_header
            )
        unauthorized_error = delete_unauthorized_response.get_data(
            as_text=True
            )

        # Act - delete first user account as first user
        delete_response = self.client.delete(
            '/api/user/data/' + first_username,
            headers=first_user_header
            )

        # Assert
        self.assertEqual(delete_unauthorized_response.status_code, 401)
        self.assertEqual(unauthorized_error, 'Unauthorized')

        self.assertEqual(delete_response.status_code, 200)

        # Ensure S3 bucket was called to create and delete user's drawing
        boto3.resource.return_value.Bucket.assert_called_with(
            os.environ['S3_BUCKET']
            )

        # Ensure deleted user account isn't found when user is searched for
        deleted_get_response = self.client.get(
            '/api/user/' + first_username
            )
        deleted_error = deleted_get_response.get_data(as_text=True)

        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(deleted_error, 'Not found')

        # Ensure deleted user's drawing is not found when searched for
        deleted_drawing_response = self.client.get(
            '/api/canvashare/drawing/' + drawing_id
            )
        drawing_error = deleted_drawing_response.get_data(as_text=True)

        self.assertEqual(deleted_drawing_response.status_code, 404)
        self.assertEqual(drawing_error, 'Not found')

        # Ensure deleted user's drawing like is not found when searched for
        first_deleted_like_response = self.client.get(
            '/api/canvashare/drawing-like/' + first_drawing_like_id
            )
        first_like_error = first_deleted_like_response.get_data(as_text=True)

        self.assertEqual(first_deleted_like_response.status_code, 404)
        self.assertEqual(first_like_error, 'Not found')

        # Ensure second user's drawing like for deleted drawing is not found
        # when searched for
        second_deleted_like_response = self.client.get(
            '/api/canvashare/drawing-like/' + second_drawing_like_id
            )
        second_like_error = second_deleted_like_response.get_data(as_text=True)

        self.assertEqual(second_deleted_like_response.status_code, 404)
        self.assertEqual(second_like_error, 'Not found')

        # Ensure deleted user's drawing is not in second user's liked drawings
        # list
        deleted_drawing_likes_response = self.client.get(
            '/api/canvashare/drawing-likes/user/' + second_username,
            headers=second_user_header
            )
        second_user_likes = json.loads(
            deleted_drawing_likes_response.get_data(as_text=True)
            )
        self.assertEqual(all(
            drawing_id not in like['drawing_id'] for like in second_user_likes
            ), True)

        # Ensure deleted user's post is not found when searched for
        deleted_post_response = self.client.get(
            '/api/thought-writer/post/' + post_id
            )
        post_error = deleted_post_response.get_data(as_text=True)

        self.assertEqual(deleted_post_response.status_code, 404)
        self.assertEqual(post_error, 'Not found')

        # Ensure deleted user's comment is not found when searched for
        first_deleted_comment_response = self.client.get(
            '/api/thought-writer/comment/' + first_comment_id
            )
        first_comment_error = first_deleted_comment_response.get_data(
            as_text=True
            )

        self.assertEqual(first_deleted_comment_response.status_code, 404)
        self.assertEqual(first_comment_error, 'Not found')

        # Ensure second user's comment for deleted post is not found when
        # searched for
        second_deleted_comment_response = self.client.get(
            '/api/thought-writer/comment/' + second_comment_id
            )
        second_comment_error = second_deleted_comment_response.get_data(
            as_text=True
            )

        self.assertEqual(second_deleted_comment_response.status_code, 404)
        self.assertEqual(second_comment_error, 'Not found')

        # Ensure deleted user's Shapes in Rain score is not found when searched
        # for
        deleted_shapes_response = self.client.get(
            '/api/shapes-in-rain/score/' + shapes_score_id
            )
        shapes_error = deleted_shapes_response.get_data(as_text=True)

        self.assertEqual(deleted_shapes_response.status_code, 404)
        self.assertEqual(shapes_error, 'Not found')

        # Ensure deleted user's Rhythm of Life score is not found when searched
        # for
        deleted_rhythm_response = self.client.get(
            '/api/rhythm-of-life/score/' + rhythm_score_id
            )
        rhythm_error = deleted_rhythm_response.get_data(as_text=True)

        self.assertEqual(deleted_rhythm_response.status_code, 404)
        self.assertEqual(rhythm_error, 'Not found')

        # Delete second user account for clean-up
        self.delete_user(second_username)

    def test_user_hard_delete_unauthorized_error(self):
        # Arrange
        username = 'user1'

        # Act
        delete_response = self.client.delete(
            '/api/user/data/' + username
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_user_hard_delete_not_user_or_admin_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        username = 'user1'

        # Act
        delete_response = self.client.delete(
            '/api/user/data/' + username,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/user/verify endpoint [GET]
class TestVerify(CrystalPrismTestCase):
    def test_verify_get(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        get_response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        payload = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(payload['username'], self.username)

        # Ensure expiration time is 10-digit integer
        self.assertEqual(isinstance(payload['exp'], int), True)
        self.assertEqual(len(str(payload['exp'])), 10)

    def test_verify_get_data_missing_error(self):
        # Act
        get_response = self.client.get(
            '/api/user/verify'
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_verify_get_format_error(self):
        # Arrange
        header = {'Authorization': 'Bearer token'}

        # Act
        get_response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_verify_get_expiration_error(self):
        # Arrange
        self.create_user()
        self.login()
        initial_header = {'Authorization': 'Bearer ' + self.token}

        # Create new token with payload past expiration time (1 hour)
        token_header = urlsafe_b64encode(b'{"alg": "HS256", "typ": "JWT"}')

        expired_payload = urlsafe_b64encode(json.dumps({
            'username': self.username,
            'exp': floor(time() - (61 * 60))
            }).encode())

        secret = os.environ['SECRET_KEY'].encode()
        message = token_header + b'.' + expired_payload
        signature = hmac.new(secret, message, digestmod=sha256).digest()
        signature = urlsafe_b64encode(signature)
        expired_token = (message + b'.' + signature).decode()

        final_header = {'Authorization': 'Bearer ' + expired_token}

        # Act
        final_response = self.client.get(
            '/api/user/verify',
            headers=final_header
            )
        error = final_response.get_data(as_text=True)

        # Assert
        self.assertEqual(final_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_verify_get_deleted_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Soft-delete user
        self.client.delete(
            '/api/user/' + self.username,
            headers=header
        )

        # Act
        soft_delete_get_response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        soft_delete_error = soft_delete_get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(soft_delete_get_response.status_code, 401)
        self.assertEqual(soft_delete_error, 'Unauthorized')

        # Hard-delete user
        self.delete_user(self.username)

        # Act
        hard_delete_get_response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        hard_delete_error = hard_delete_get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(hard_delete_get_response.status_code, 401)
        self.assertEqual(hard_delete_error, 'Unauthorized')

    def test_verify_get_compromised_error(self):
        # Arrange
        self.create_user()
        self.login()

        # Change first letter in token to compromise it
        compromised_token = list(self.token)
        compromised_token[0] = 'f'
        compromised_token = "".join(compromised_token)

        header = {'Authorization': 'Bearer ' + compromised_token}

        # Act
        get_response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/users endpoint [GET]
class TestUsers(CrystalPrismTestCase):
    def test_users_get(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        get_response = self.client.get(
            '/api/users',
            headers=header
            )
        users = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(users), 10)

        # Ensure each username is a string
        self.assertEqual(all(
            isinstance(user, str) for user in users), True
            )

    def test_users_get_none(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        query = {'start': 100000}

        # Act
        get_response = self.client.get(
            '/api/users',
            headers=header,
            query_string=query
            )
        users = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(users, [])

    def test_users_get_partial(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/users',
            headers=header,
            query_string=query
            )
        users = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(users), 5)

    def test_users_get_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/users',
            headers=header,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')

    def test_users_get_unauthorized_error(self):
        # Act
        get_response = self.client.get(
            '/api/users'
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')
