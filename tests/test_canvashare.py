import json
import unittest

from server import app
from utils.tests import CrystalPrismTestCase


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
        self.assertEqual(response_data, ['user/1.png'])

    def test_gallery_get_none(self):
        # Arrange
        data = {'start': 50}

        # Act
        response = self.client.get(
            '/api/canvashare/gallery',
            query_string=data, # data=data for self.client.post()
            content_type='application/json'
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response_data, [])

    def test_gallery_get_five(self):
        # Arrange
        data = {'end': 5}

        # Act
        response = self.client.get(
            '/api/canvashare/gallery',
            query_string=data, # data=data for self.client.post()
            content_type='application/json'
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
            query_string=data, # data=data for self.client.post()
            content_type='application/json'
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response_data, [])
