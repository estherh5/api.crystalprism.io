import json
import os
import re
import unittest

from server import app
from utils.tests import CrystalPrismTestCase


# Test /api/canvashare/drawing endpoint [POST, GET]
class TestDrawing(CrystalPrismTestCase):
    def setUp(self):
        super(TestDrawing, self).setUp()


    def test_drawing_post_and_get(self):
        # Arrange
        # Create user and login to get token for Authorization header
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Open drawing.txt to get sample image data URL
        test_drawing = os.path.dirname(__file__) + '/../fixtures/drawing.txt'
        with open(test_drawing, 'r') as drawing:
            drawing = drawing.read()
        data = {'drawing': drawing, 'title': 'Test'}

        # Act
        post_response = self.client.post(
            '/api/canvashare/drawing',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )

        get_response = self.client.get(
            '/api/canvashare/drawing/' + self.username + '/1.png'
            )

        # Assert
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(get_response.mimetype, 'image/png')


# Test /api/canvashare/gallery endpoint [GET]
class TestGallery(CrystalPrismTestCase):
    def setUp(self):
        super(TestGallery, self).setUp()


    def test_gallery_get(self):
        # Act
        response = self.client.get('/api/canvashare/gallery')
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 10)

        # Ensure response is a list of drawing file paths
        pattern = re.compile(r'^[a-zA-Z0-9-_]*[/]\d{1,}\.png$')
        filtered_response = filter(pattern.match, response_data)
        self.assertEqual(len([i for i in filtered_response]), 10)


    def test_gallery_get_none(self):
        # Arrange
        data = {'start': 100}

        # Act
        response = self.client.get(
            '/api/canvashare/gallery',
            query_string=data
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response_data, [])


    def test_gallery_get_partial(self):
        # Arrange
        data = {'end': 5}

        # Act
        response = self.client.get(
            '/api/canvashare/gallery',
            query_string=data
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(response_data), 5)


    def test_gallery_get_error(self):
        # Arrange
        data = {'start': 5, 'end': 0}

        # Act
        response = self.client.get(
            '/api/canvashare/gallery',
            query_string=data
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response_data, [])
