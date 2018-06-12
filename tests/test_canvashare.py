import boto3
import json
import os
import re

from unittest.mock import patch
from utils.tests import CrystalPrismTestCase


# Test /api/canvashare/drawing endpoint [POST, GET, PATCH, DELETE]
class TestDrawing(CrystalPrismTestCase):
    @patch('canvashare.canvashare.boto3')
    def test_drawing_post_get_patch_and_delete(self, boto3):
        # Arrange [POST]
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        resource = boto3.resource.return_value
        bucket = resource.Bucket.return_value

        # Get sample image data URL
        test_drawing = (
            os.path.dirname(__file__) + '/../fixtures/test-drawing.txt'
            )
        with open(test_drawing, 'r') as drawing:
            drawing = drawing.read()
        data = {
            'drawing': drawing,
            'title': 'Test'
            }

        # Act [POST]
        post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        drawing_id = post_response.get_data(as_text=True)

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)

        boto3.resource.return_value.Bucket.assert_called_with(
            os.environ['S3_BUCKET']
            )

        # Act [GET]
        get_response = self.client.get(
            '/api/canvashare/drawing/' + drawing_id
            )
        drawing = json.loads(get_response.get_data(as_text=True))

        get_user_response = self.client.get(
            '/api/user/' + self.username
            )
        user_data = json.loads(get_user_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(drawing['drawing_id'], drawing_id)
        self.assertEqual(drawing['like_count'], 0)
        self.assertEqual(drawing['likers'], [])
        self.assertEqual(drawing['title'], 'Test')
        self.assertEqual(
            os.environ['S3_URL'] + os.environ['S3_CANVASHARE_DIR']
            in drawing['url'], True
            )
        self.assertEqual(drawing['username'], self.username)
        self.assertEqual(drawing['views'], 0)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            drawing['created'])), True
            )

        self.assertEqual(user_data['drawing_count'], 1)

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/canvashare/drawing/' + drawing_id,
            headers=header
            )

        patch_get_response = self.client.get(
            '/api/canvashare/drawing/' + drawing_id
            )
        updated_drawing = json.loads(patch_get_response.get_data(as_text=True))

        # Assert [PATCH]
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_get_response.status_code, 200)
        self.assertEqual(updated_drawing['views'], 1)

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/canvashare/drawing/' + drawing_id,
            headers=header
            )

        deleted_get_response = self.client.get(
            '/api/canvashare/drawing/' + drawing_id
            )
        error = deleted_get_response.get_data(as_text=True)

        deleted_get_user_response = self.client.get(
            '/api/user/' + self.username
            )
        updated_user_data = json.loads(
            deleted_get_user_response.get_data(as_text=True)
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)

        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(error, 'Not found')

        self.assertEqual(updated_user_data['drawing_count'], 0)

    def test_drawing_post_unauthorized_error(self):
        # Act
        post_response = self.client.post('/api/canvashare/drawing')
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_drawing_post_data_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Request must contain drawing and title')

    def test_drawing_image_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        data = {
            'drawing': '',
            'title': 'Test'
            }

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Drawing must be base64-encoded PNG image')

    def test_drawing_post_title_blank_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Get sample image data URL
        test_drawing = (
            os.path.dirname(__file__) + '/../fixtures/test-drawing.txt'
            )
        with open(test_drawing, 'r') as drawing:
            drawing = drawing.read()
        data = {
            'drawing': drawing,
            'title': ''
            }

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Drawing title cannot be blank')

    @patch('canvashare.canvashare.boto3')
    def test_drawing_post_not_unique_error(self, boto3):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        resource = boto3.resource.return_value
        bucket = resource.Bucket.return_value

        # Get sample image data URL
        test_drawing = (
            os.path.dirname(__file__) + '/../fixtures/test-drawing.txt'
            )
        with open(test_drawing, 'r') as drawing:
            drawing = drawing.read()
        data = {
            'drawing': drawing,
            'title': 'Test'
            }

        # Post drawing
        post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        drawing_id = post_response.get_data(as_text=True)

        # Act - attempt to post the same drawing
        second_post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = second_post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(second_post_response.status_code, 409)
        self.assertEqual(error, 'Drawing already exists')

        # Delete drawing for clean-up
        self.client.delete(
            '/api/canvashare/drawing/' + drawing_id,
            headers=header
        )

    def test_drawing_patch_not_found_error(self):
        # Arrange
        drawing_id = '10000'

        # Act
        patch_response = self.client.patch(
            '/api/canvashare/drawing/' + drawing_id
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_drawing_delete_unauthorized_error(self):
        # Arrange
        drawing_id = '1'

        # Act
        post_response = self.client.delete(
            '/api/canvashare/drawing/' + drawing_id
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_drawing_delete_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        drawing_id = '10000'

        # Act
        delete_response = self.client.delete(
            '/api/canvashare/drawing/' + drawing_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_drawing_delete_not_artist_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        drawing_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/canvashare/drawing/' + drawing_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/canvashare/drawings endpoint [GET]
class TestDrawings(CrystalPrismTestCase):
    def test_drawings_get(self):
        # Act
        get_response = self.client.get('/api/canvashare/drawings')
        drawings = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(drawings), 10)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            drawing['created'])) for drawing in drawings), True)

        # Ensure each drawing id is a string
        self.assertEqual(all(isinstance(
            drawing['drawing_id'], str) for drawing in drawings), True)

        # Ensure each like count is an integer
        self.assertEqual(all(
            isinstance(drawing['like_count'], int) for drawing in drawings
            ), True)

        # Ensure each likers list is a list
        self.assertEqual(all(
            isinstance(drawing['likers'], list) for drawing in drawings), True)

        # Ensure each title is a string
        self.assertEqual(all(
            isinstance(drawing['title'], str) for drawing in drawings), True)

        # Ensure each view count is an integer
        self.assertEqual(all(
            isinstance(drawing['views'], int) for drawing in drawings), True)

        # Ensure each url contains CanvaShare S3 bucket URL start
        self.assertEqual(all(
            (os.environ['S3_URL'] + os.environ['S3_CANVASHARE_DIR'])
            in drawing['url'] for drawing in drawings), True)

        # Ensure each artist is a string
        self.assertEqual(all(isinstance(
            drawing['username'], str) for drawing in drawings), True)

    def test_drawings_get_none(self):
        # Arrange
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings',
            query_string=query
            )
        drawings = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(drawings, [])

    def test_drawings_get_partial(self):
        # Arrange
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings',
            query_string=query
            )
        drawings = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(drawings), 5)

    def test_drawings_get_error(self):
        # Arrange
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings',
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')

    def test_user_drawings_get(self):
        # Arrange
        artist_name = 'user1'

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings/' + artist_name
            )
        drawings = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(drawings), 10)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            drawing['created'])) for drawing in drawings), True)

        # Ensure each drawing id is a string
        self.assertEqual(all(isinstance(
            drawing['drawing_id'], str) for drawing in drawings), True)

        # Ensure each like count is an integer
        self.assertEqual(all(
            isinstance(drawing['like_count'], int) for drawing in drawings
            ), True)

        # Ensure each likers list is a list
        self.assertEqual(all(
            isinstance(drawing['likers'], list) for drawing in drawings), True)

        # Ensure each title is a string
        self.assertEqual(all(
            isinstance(drawing['title'], str) for drawing in drawings), True)

        # Ensure each view count is an integer
        self.assertEqual(all(
            isinstance(drawing['views'], int) for drawing in drawings), True)

        # Ensure each url contains CanvaShare S3 bucket URL start
        self.assertEqual(all(
            (os.environ['S3_URL'] + os.environ['S3_CANVASHARE_DIR'])
            in drawing['url'] for drawing in drawings), True)

        # Ensure each artist is specified artist name
        self.assertEqual(all(
            drawing['username'] == artist_name for drawing in drawings
            ), True)

    def test_user_drawings_get_none(self):
        # Arrange
        artist_name = 'user1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings/' + artist_name,
            query_string=query
            )
        drawings = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(drawings, [])

    def test_user_drawings_get_partial(self):
        # Arrange
        artist_name = 'user1'
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings/' + artist_name,
            query_string=query
            )
        drawings = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(drawings), 5)

    def test_user_drawings_get_error(self):
        # Arrange
        artist_name = 'user1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawings/' + artist_name,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')


# Test /api/canvashare/drawing-like endpoint [POST, GET, DELETE]
class TestDrawingLike(CrystalPrismTestCase):
    def test_drawing_like_post_get_and_delete(self):
        # Arrange [POST]
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        drawing_id = '1'
        data = {'drawing_id': drawing_id}

        # Get current number of drawing's likes
        initial_get_drawing_response = self.client.get(
            '/api/canvashare/drawing/' + drawing_id
            )
        like_count = json.loads(
            initial_get_drawing_response.get_data(as_text=True))['like_count']

        # Act [POST]
        post_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        drawing_like_id = post_response.get_data(as_text=True)

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)

        # Act [GET]
        get_response = self.client.get(
            '/api/canvashare/drawing-like/' + drawing_like_id
            )
        drawing_like = json.loads(get_response.get_data(as_text=True))

        get_drawing_response = self.client.get(
            '/api/canvashare/drawing/' + drawing_id
            )
        drawing = json.loads(get_drawing_response.get_data(as_text=True))

        get_user_response = self.client.get(
            '/api/user/' + self.username
            )
        user_data = json.loads(get_user_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(drawing_like['drawing_like_id'], int(drawing_like_id))
        self.assertEqual(drawing_like['drawing_id'], str(1))
        self.assertEqual(drawing_like['username'], self.username)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            drawing_like['created'])), True
            )

        self.assertEqual(drawing['like_count'], like_count + 1)
        self.assertEqual(any(
            self.username in liker['username'] for liker in drawing['likers']
            ), True)

        self.assertEqual(user_data['drawing_like_count'], 1)

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/canvashare/drawing-like/' + drawing_like_id,
            headers=header
            )

        deleted_get_response = self.client.get(
            '/api/canvashare/drawing-like/' + drawing_like_id
            )
        error = deleted_get_response.get_data(as_text=True)

        deleted_get_user_response = self.client.get(
            '/api/user/' + self.username
            )
        updated_user_data = json.loads(
            deleted_get_user_response.get_data(as_text=True)
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)

        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(error, 'Not found')

        self.assertEqual(updated_user_data['drawing_like_count'], 0)

    def test_drawing_like_post_unauthorized_error(self):
        # Act
        post_response = self.client.post('/api/canvashare/drawing-like')
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_drawing_like_post_data_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=header
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Request must contain drawing id')

    def test_drawing_like_post_id_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {'drawing_id': ''}

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Drawing id must be a string')

    def test_drawing_like_post_drawing_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {'drawing_id': '10000'}

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_drawing_like_post_already_liked_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {'drawing_id': '1'}

        # Post a like for drawing
        self.client.post(
            '/api/canvashare/drawing-like',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )

        # Act - attempt to post another like for drawing
        post_response = self.client.post(
            '/api/canvashare/drawing-like',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'User already liked drawing')

    def test_drawing_like_delete_unauthorized_error(self):
        # Arrange
        drawing_like_id = '1'

        # Act
        post_response = self.client.delete(
            '/api/canvashare/drawing-like/' + drawing_like_id
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_drawing_like_delete_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        drawing_like_id = '10000'

        # Act
        delete_response = self.client.delete(
            '/api/canvashare/drawing-like/' + drawing_like_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 400)
        self.assertEqual(error, 'User did not like drawing')

    def test_drawing_like_delete_not_liker_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        drawing_like_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/canvashare/drawing-like/' + drawing_like_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/canvashare/drawing-likes endpoint [GET]
class TestDrawingLikes(CrystalPrismTestCase):
    def test_drawing_likes_get(self):
        # Arrange
        drawing_id = '1'

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/drawing/' + drawing_id
            )
        drawing_likes = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(drawing_likes), 10)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            drawing_like['created'])) for drawing_like in drawing_likes), True)

        # Ensure each drawing like id is an integer
        self.assertEqual(all(isinstance(drawing_like['drawing_like_id'], int)
            for drawing_like in drawing_likes), True)

        # Ensure each drawing id is specified drawing id
        self.assertEqual(all(drawing_like['drawing_id'] == str(1)
            for drawing_like in drawing_likes), True)

        # Ensure each liker is a string
        self.assertEqual(all(isinstance(drawing_like['username'], str)
            for drawing_like in drawing_likes), True)

    def test_drawing_likes_get_none(self):
        # Arrange
        drawing_id = '1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/drawing/' + drawing_id,
            query_string=query
            )
        drawing_likes = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(drawing_likes, [])

    def test_drawing_likes_get_partial(self):
        # Arrange
        drawing_id = '1'
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/drawing/' + drawing_id,
            query_string=query
            )
        drawing_likes = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(drawing_likes), 5)

    def test_drawing_likes_get_error(self):
        # Arrange
        drawing_id = '1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/drawing/' + drawing_id,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')

    def test_user_drawing_likes_get(self):
        # Arrange
        liker_name = 'user1'

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/user/' + liker_name
            )
        drawing_likes = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(drawing_likes), 10)

        # Ensure each liked drawing's artist is a string
        self.assertEqual(all(isinstance(drawing_like['artist_name'], str)
            for drawing_like in drawing_likes), True)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            drawing_like['created'])) for drawing_like in drawing_likes), True)

        # Ensure each drawing like id is an integer
        self.assertEqual(all(isinstance(drawing_like['drawing_like_id'], int)
            for drawing_like in drawing_likes), True)

        # Ensure each drawing id is a string
        self.assertEqual(all(isinstance(drawing_like['drawing_id'], str)
            for drawing_like in drawing_likes), True)

        # Ensure each liked drawing's like count is an integer
        self.assertEqual(all(isinstance(
            drawing_like['like_count'], int) for drawing_like in drawing_likes
            ), True)

        # Ensure each liked drawing's likers list is a list
        self.assertEqual(all(isinstance(
            drawing_like['likers'], list) for drawing_like in drawing_likes),
            True)

        # Ensure each liked drawing's title is a string
        self.assertEqual(all(isinstance(drawing_like['title'], str)
            for drawing_like in drawing_likes), True)

        # Ensure each liked drawing's url contains CanvaShare S3 bucket URL
        # start
        self.assertEqual(all(
            (os.environ['S3_URL'] + os.environ['S3_CANVASHARE_DIR'])
            in drawing_like['url'] for drawing_like in drawing_likes), True)

        # Ensure each liker is specified liker name
        self.assertEqual(all(drawing_like['username'] == liker_name
            for drawing_like in drawing_likes), True)

        # Ensure each liked drawing's view count is an integer
        self.assertEqual(all(isinstance(drawing_like['views'], int)
            for drawing_like in drawing_likes), True)

    def test_user_drawing_likes_get_none(self):
        # Arrange
        liker_name = 'user1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/user/' + liker_name,
            query_string=query
            )
        drawing_likes = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(drawing_likes, [])

    def test_user_drawing_likes_get_partial(self):
        # Arrange
        liker_name = 'user1'
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/user/' + liker_name,
            query_string=query
            )
        drawing_likes = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(drawing_likes), 5)

    def test_user_drawing_likes_get_error(self):
        # Arrange
        liker_name = 'user1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/canvashare/drawing-likes/user/' + liker_name,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')
