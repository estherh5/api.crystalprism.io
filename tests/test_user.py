import json
import os
import re
import time

from server import app
from utils.tests import CrystalPrismTestCase
from uuid import UUID


# Test /api/user endpoint [POST, GET, PATCH, DELETE]
class TestUser(CrystalPrismTestCase):
    def test_user_post_get_patch_and_soft_delete(self):
        # Arrange [POST]
        username = 'test1' + str(round(time.time()))
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
            '/api/user',
            headers=header
            )
        user_data = json.loads(get_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)

        # Ensure member_id is correct format
        self.assertEqual(bool(UUID(
            user_data['member_id'], version=4)), True
            )

        self.assertEqual(user_data['status'], 'active')
        self.assertEqual(user_data['username'], username)
        self.assertEqual(user_data['admin'], False)
        self.assertEqual(user_data['first_name'], '')
        self.assertEqual(user_data['last_name'], '')
        self.assertEqual(user_data['name_public'], False)
        self.assertEqual(user_data['email'], '')
        self.assertEqual(user_data['email_public'], False)
        self.assertEqual(user_data['background_color'], '#ffffff')
        self.assertEqual(user_data['icon_color'], '#000000')
        self.assertEqual(user_data['about'], '')
        self.assertEqual(user_data['shapes_plays'], 0)
        self.assertEqual(user_data['shapes_scores'], [])
        self.assertEqual(user_data['shapes_high_score'], 0)
        self.assertEqual(user_data['rhythm_plays'], 0)
        self.assertEqual(user_data['rhythm_scores'], [])
        self.assertEqual(user_data['rhythm_high_score'], 0)
        self.assertEqual(user_data['rhythm_high_lifespan'], '00:00:00')
        self.assertEqual(user_data['drawing_count'], 0)
        self.assertEqual(user_data['liked_drawings'], [])
        self.assertEqual(user_data['post_count'], 0)
        self.assertEqual(user_data['comment_count'], 0)

        # Ensure member since timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d.\d{6}\+\d\d:\d\d'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            user_data['member_since'])), True
            )

        # Arrange [PATCH]
        updated_username = 'test2' + str(round(time.time()))
        updated_password = 'password2'
        patch_data = {
            'username': updated_username,
            'password': updated_password,
            'about': 'Test',
            'first_name': 'Test',
            'last_name': 'Test',
            'name_public': True,
            'email': 'test@crystalprism.io',
            'email_public': True,
            'background_color': '#000000',
            'icon_color': '#ffffff'
            }

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/user',
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )
        patched_token = patch_response.get_data(as_text=True)
        patched_header = {'Authorization': 'Bearer ' + patched_token}

        patched_get_response = self.client.get(
            '/api/user',
            headers=patched_header
            )
        patched_user_data = json.loads(
            patched_get_response.get_data(as_text=True)
            )

        patched_get_response_public = self.client.get(
            '/api/user/' + updated_username
            )
        patched_user_data_public = json.loads(
            patched_get_response_public.get_data(as_text=True)
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
        self.assertEqual(patched_get_response_public.status_code, 200)

        self.assertEqual(patched_user_data['username'], updated_username)
        self.assertEqual(patched_user_data['about'], 'Test')

        self.assertEqual(patched_user_data['first_name'], 'Test')
        self.assertEqual(patched_user_data['last_name'], 'Test')
        self.assertEqual(patched_user_data['name_public'], True)
        self.assertEqual(patched_user_data_public['name'], 'Test Test')

        self.assertEqual(patched_user_data['email'], 'test@crystalprism.io')
        self.assertEqual(patched_user_data['email_public'], True)
        self.assertEqual(
            patched_user_data_public['email'], 'test@crystalprism.io'
            )

        self.assertEqual(patched_user_data['background_color'], '#000000')
        self.assertEqual(patched_user_data['icon_color'], '#ffffff')

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/user',
            headers=patched_header
            )

        deleted_get_response = self.client.get(
            '/api/user',
            headers=patched_header
            )
        error = deleted_get_response.get_data(as_text=True)

        deleted_get_response_public = self.client.get(
            '/api/user/' + updated_username
            )
        public_error = deleted_get_response_public.get_data(as_text=True)

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(error, 'Username does not exist')
        self.assertEqual(deleted_get_response_public.status_code, 404)
        self.assertEqual(public_error, 'Username does not exist')

        # Hard-delete user for clean-up
        self.delete_user_admin(updated_username)

        # Ensure deleted user account isn't able to be deleted again
        delete_again_response = self.client.delete(
            '/api/user',
            headers=patched_header
            )
        delete_error = delete_again_response.get_data(as_text=True)

        self.assertEqual(delete_again_response.status_code, 404)
        self.assertEqual(delete_error, 'Username does not exist')

    def test_user_post_already_exists_error(self):
        # Arrange
        username = 'test3' + str(round(time.time()))
        password = 'password'
        self.create_user(username, password)
        self.login(username, password)
        header = {'Authorization': 'Bearer ' + self.token}
        post_data = {
            'username': username,
            'password': password
            }

        # Soft-delete user
        self.client.delete(
            '/api/user',
            headers=header
            )

        # Act
        response = self.client.post(
            '/api/user',
            data=json.dumps(post_data),
            content_type='application/json'
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 409)
        self.assertEqual(error, 'Username already exists')

        # Hard-delete user for clean-up
        self.delete_user_admin(username)

    def test_user_patch_username_error(self):
        # Arrange
        username = 'test4' + str(round(time.time()))
        self.create_user(username)
        self.login(username)
        header = {'Authorization': 'Bearer ' + self.token}
        patch_data = {
            'username': 'user',
            'password': ''
            }

        # Act
        response = self.client.patch(
            '/api/user',
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 409)
        self.assertEqual(error, 'Username already exists')

        # Delete user for clean-up
        self.delete_user(username)

    def test_user_patch_soft_deleted_error(self):
        # Arrange
        username = 'test5' + str(round(time.time()))
        self.create_user(username)
        self.login(username)
        header = {'Authorization': 'Bearer ' + self.token}
        patch_data = {
            'username': username,
            'password': ''
            }

        # Soft-delete user
        self.client.delete(
            '/api/user',
            headers=header
            )

        # Act
        response = self.client.patch(
            '/api/user',
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(error, 'Username does not exist')

        # Hard-delete user for clean-up
        self.delete_user_admin(username)

    def test_user_patch_hard_deleted_error(self):
        # Arrange
        username = 'test6' + str(round(time.time()))
        self.create_user(username)
        self.login(username)
        header = {'Authorization': 'Bearer ' + self.token}
        patch_data = {
            'username': username,
            'password': ''
            }

        # Hard-delete user
        self.client.delete(
            '/api/user/' + username,
            headers=header
            )

        # Act
        response = self.client.patch(
            '/api/user',
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(error, 'Username does not exist')

    def test_user_get_error(self):
        # Arrange
        username = 'test7' + str(round(time.time()))
        self.create_user(username)
        self.login(username)
        header = {'Authorization': 'Bearer ' + self.token}

        # Delete user
        self.client.delete(
            '/api/user/' + username,
            headers=header
            )

        # Act
        response = self.client.get(
            '/api/user',
            headers=header
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(error, 'Username does not exist')

    def test_public_user_get(self):
        username = 'user'

        # Act
        get_response = self.client.get('/api/user/' + username)
        user_data = json.loads(get_response.get_data(as_text=True))

        # Assert [POST]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(user_data['username'], username)
        self.assertEqual(user_data['name'], '')
        self.assertEqual(user_data['email'], '')
        self.assertEqual(user_data['background_color'], '#ffffff')
        self.assertEqual(user_data['icon_color'], '#000000')
        self.assertEqual(user_data['about'], '')
        self.assertEqual(
            user_data['member_since'], '2017-10-04T00:00:00.000000+00:00'
            )
        self.assertEqual(user_data['shapes_high_score'], 55)
        self.assertEqual(user_data['rhythm_high_lifespan'], '00:04:10')
        self.assertEqual(user_data['drawing_count'], 10)
        self.assertEqual(user_data['post_count'], 10)
        self.assertEqual(user_data['comment_count'], 0)

    def test_public_user_get_error(self):
        username = 'fakeuseraccount' + str(round(time.time()))

        # Act
        response = self.client.get('/api/user/' + username)
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(error, 'Username does not exist')

    def test_user_hard_delete(self):
        # Arrange - create two user accounts
        first_username = 'test8' + str(round(time.time()))
        self.create_user(first_username)
        self.login(first_username)
        first_user_header = {'Authorization': 'Bearer ' + self.token}

        second_username = 'test9' + str(round(time.time()))
        self.create_user(second_username)
        self.login(second_username)
        second_user_header = {'Authorization': 'Bearer ' + self.token}

        # Arrange - first user creates drawing
        test_drawing = os.path.dirname(__file__) + '/../fixtures/drawing.txt'
        with open(test_drawing, 'r') as drawing:
            drawing = drawing.read()
        post_drawing_data = {
            'drawing': drawing,
            'title': 'Test'
            }

        self.client.post(
            '/api/canvashare/drawing',
            headers=first_user_header,
            data=json.dumps(post_drawing_data),
            content_type='application/json'
            )

        # Arrange - second user likes drawing
        self.client.patch(
            '/api/canvashare/drawing-info/' + first_username + '/1',
            headers=second_user_header,
            data=json.dumps({'request': 'like'}),
            content_type='application/json'
            )

        # Arrange - first user likes a different drawing
        self.client.patch(
            '/api/canvashare/drawing-info/user/1',
            headers=first_user_header,
            data=json.dumps({'request': 'like'}),
            content_type='application/json'
            )

        # Arrange - first user creates post
        post_post_data = {
            'title': 'Test',
            'content': 'Test',
            'public': True
            }

        post_post_response = self.client.post(
            '/api/thought-writer/post',
            headers=first_user_header,
            data=json.dumps(post_post_data),
            content_type='application/json'
            )
        timestamp = post_post_response.get_data(as_text=True)

        # Arrange - first user posts score for Shapes in Rain
        shapes_data = {'score': 100000}

        self.client.post(
            '/api/shapes-in-rain',
            headers=first_user_header,
            data=json.dumps(shapes_data),
            content_type='application/json'
            )

        # Arrange - first user posts score for Rhythm of Life
        rhythm_data = {
            'score': 360000,
            'lifespan': '100:00:00'
            }

        self.client.post(
            '/api/rhythm-of-life',
            headers=first_user_header,
            data=json.dumps(rhythm_data),
            content_type='application/json'
            )

        # Act - delete first user account
        delete_response = self.client.delete(
            '/api/user/' + first_username,
            headers=first_user_header
            )

        # Assert
        self.assertEqual(delete_response.status_code, 200)

        # Ensure deleted user account isn't found when user is searched for
        deleted_user_response = self.client.get(
            '/api/user/' + first_username
            )
        deleted_error = deleted_user_response.get_data(as_text=True)

        self.assertEqual(deleted_user_response.status_code, 404)
        self.assertEqual(deleted_error, 'Username does not exist')

        # Ensure deleted user account isn't able to be deleted again
        delete_again_response = self.client.delete(
            '/api/user/' + first_username,
            headers=first_user_header
            )
        delete_again_error = deleted_user_response.get_data(as_text=True)

        self.assertEqual(delete_again_response.status_code, 404)
        self.assertEqual(delete_again_error, 'Username does not exist')

        # Ensure deleted user's drawing is not found when searched for
        deleted_drawing_response = self.client.get(
            '/api/canvashare/drawing/' + first_username + '/1.png'
            )
        deleted_drawing_error = deleted_drawing_response.get_data(as_text=True)

        self.assertEqual(deleted_drawing_response.status_code, 404)
        self.assertEqual(deleted_drawing_error, 'File not found')

        # Ensure deleted user's drawing is not in second user's liked drawings
        # list
        deleted_liker_response = self.client.get(
            '/api/user',
            headers=second_user_header
            )
        second_user_data = json.loads(
            deleted_liker_response.get_data(as_text=True)
            )
        self.assertEqual(second_user_data['liked_drawings'], [])

        # Ensure drawing that deleted user liked no longer contains deleted
        # user as liked user
        deleted_like_response = self.client.get(
            '/api/canvashare/drawing-info/user/1'
            )
        drawing_response_data = json.loads(
            deleted_like_response.get_data(as_text=True)
            )
        self.assertEqual(drawing_response_data['liked_users'], [])

        # Ensure deleted user's post is not found when searched for
        deleted_post_response = self.client.get(
            '/api/thought-writer/post/' + first_username + '/' + timestamp
            )

        # Ensure deleted user does not appear in leaders data for Shapes in
        # Rain
        deleted_shapes_response = self.client.get('/api/shapes-in-rain')
        shapes_response_data = json.loads(
            deleted_shapes_response.get_data(as_text=True)
            )
        self.assertEqual(
            shapes_response_data[0]['player'] != first_username, True
            )

        # Ensure deleted user does not appear in leaders data for Rhythm of
        # Life
        deleted_rhythm_response = self.client.get('/api/rhythm-of-life')
        rhythm_response_data = json.loads(
            deleted_rhythm_response.get_data(as_text=True)
            )
        self.assertEqual(
            rhythm_response_data[0]['player'] != first_username, True
            )

        # Act - delete second user account for clean-up
        delete_response = self.client.delete(
            '/api/user/' + second_username,
            headers=second_user_header
            )


# Test /api/user/verify endpoint [GET]
class TestVerify(CrystalPrismTestCase):
    def test_verify_get(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['username'], self.username)

        # Ensure expiration time is 10-digit integer
        self.assertEqual(isinstance(response_data['exp'], int), True)
        self.assertEqual(len(str(response_data['exp'])), 10)

    def test_verify_get_error(self):
        # Act
        response = self.client.get('/api/user/verify')
        response_data = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response_data, 'Could not verify')

    def test_verify_get_format_error(self):
        # Arrange
        header = {'Authorization': 'Bearer token'}

        # Act
        response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        response_data = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response_data, 'Token is incorrect format')

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
        response = self.client.get(
            '/api/user/verify',
            headers=header
            )
        response_data = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response_data, 'Token compromised')