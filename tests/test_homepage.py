import boto3
import json
import os
import re

from unittest.mock import patch
from utils.tests import CrystalPrismTestCase


# Test /api/homepage/ideas endpoint [GET]
class TestIdeas(CrystalPrismTestCase):
    def test_ideas_get(self):
        # Arrange
        owner_name = 'owner'

        # Act
        get_response = self.client.get('/api/homepage/ideas')
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(posts), 10)

        # Ensure each post's content is a string
        self.assertEqual(all(
            isinstance(post['content'], str) for post in posts), True)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            post['created'])) for post in posts), True)

        # Ensure each post id is an integer
        self.assertEqual(all(isinstance(
            post['post_id'], int) for post in posts), True)

        # Ensure each title is a string
        self.assertEqual(all(
            isinstance(post['title'], str) for post in posts), True)

        # Ensure each post is written by owner
        self.assertEqual(all(
            post['username'] == owner_name for post in posts
            ), True)

    def test_ideas_get_none(self):
        # Arrange
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/homepage/ideas',
            query_string=query
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(posts, [])

    def test_ideas_get_partial(self):
        # Arrange
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/homepage/ideas',
            query_string=query
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(posts), 5)

    def test_ideas_get_error(self):
        # Arrange
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/homepage/ideas',
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')


# Test /api/homepage/photos endpoint [GET]
class TestPhotos(CrystalPrismTestCase):
    class MockObjectSummary(object):
        def __init__(self, key):
            self.key = key

    @patch('homepage.homepage.boto3')
    def test_photos_get(self, boto3):
        # Arrange
        url_start = os.environ['S3_URL'] + os.environ['S3_PHOTO_DIR']
        resource = boto3.resource.return_value
        bucket = resource.Bucket.return_value
        bucket.objects.filter.return_value = [
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '1.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '10.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '2.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '3.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '4.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '5.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '6.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '7.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '8.png'),
            self.MockObjectSummary(os.environ['S3_PHOTO_DIR'] + '9.png')
            ]

        # Act
        response = self.client.get('/api/homepage/photos')
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        boto3.resource.return_value.Bucket.assert_called_with(
            os.environ['S3_BUCKET']
            )

        self.assertEqual(len(response_data), 10)
        self.assertEqual(all(url_start in url for url in response_data),
            True)

    @patch('homepage.homepage.boto3')
    def test_photos_get_error(self, boto3):
        # Arrange
        data = {'start': 5, 'end': 0}

        # Act
        response = self.client.get(
            '/api/homepage/photos',
            query_string=data
            )
        error = response.get_data(as_text=True)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')
