import boto3
import json
import os

from unittest.mock import patch
from utils.tests import CrystalPrismTestCase


# Test /api/photos endpoint [GET]
class TestPhotos(CrystalPrismTestCase):
    class MockObjectSummary(object):
        def __init__(self, key):
            self.key = key

    @patch('server.boto3')
    def test_photos_get(self, boto3):
        # Arrange
        url_start = os.environ['PHOTO_URL_START']
        resource = boto3.resource.return_value
        bucket = resource.Bucket.return_value
        bucket.objects.all.return_value = [
            self.MockObjectSummary('1.png'),
            self.MockObjectSummary('10.png'),
            self.MockObjectSummary('2.png'),
            self.MockObjectSummary('3.png'),
            self.MockObjectSummary('4.png'),
            self.MockObjectSummary('5.png'),
            self.MockObjectSummary('6.png'),
            self.MockObjectSummary('7.png'),
            self.MockObjectSummary('8.png'),
            self.MockObjectSummary('9.png')
            ]

        # Act
        response = self.client.get('/api/photos')
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        boto3.resource.return_value.Bucket.assert_called_with(
            os.environ['S3_PHOTOS_BUCKET']
            )

        self.assertEqual(len(response_data), 10)
        self.assertEqual(all(url_start in url for url in response_data),
            True)

    @patch('server.boto3')
    def test_photos_get_error(self, boto3):
        # Arrange
        data = {'start': 5, 'end': 0}

        # Act
        response = self.client.get(
            '/api/photos',
            query_string=data
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')
