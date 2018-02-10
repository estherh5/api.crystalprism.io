import json
import re

from server import app
from utils.tests import CrystalPrismTestCase


# Test /api/rhythm-of-life endpoint [POST, GET]
class TestScore(CrystalPrismTestCase):
    def test_score_post_and_get(self):
        # Arrange
        # Create user and login to get token for Authorization header
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {'score': 360000, 'lifespan': '100:00:00'}
        query = {'end': 1}

        # Act
        post_response = self.client.post(
            '/api/rhythm-of-life',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )

        get_response = self.client.get(
            '/api/rhythm-of-life',
            query_string=query
            )
        response_data = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(response_data[0]['score'], 360000)
        self.assertEqual(response_data[0]['lifespan'], '100:00:00')

    def test_leaders_get(self):
        # Act
        response = self.client.get('/api/rhythm-of-life')
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 5)

        # Ensure timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d.\d{6}\+\d\d:\d\d'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            response_data[0]['timestamp'])), True
            )

        # Ensure score is an integer
        self.assertEqual(isinstance(response_data[0]['score'], int), True)

        # Ensure lifespan is in the format 'HH:MM:SS'
        lifespan_pattern = re.compile(r'[0-9][0-9]:[0-5][0-9]:[0-5][0-9]')
        self.assertEqual(bool(lifespan_pattern.match(
            response_data[0]['lifespan'])), True
            )

        # Ensure player is a string
        self.assertEqual(isinstance(response_data[0]['player'], str), True)

    def test_leaders_get_none(self):
        # Arrange
        data = {'start': 100}

        # Act
        response = self.client.get(
            '/api/rhythm-of-life',
            query_string=data
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(response_data, [])

    def test_leaders_get_partial(self):
        # Arrange
        data = {'end': 3}

        # Act
        response = self.client.get(
            '/api/rhythm-of-life',
            query_string=data
            )
        response_data = json.loads(response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(response_data), 3)

    def test_leaders_get_error(self):
        # Arrange
        data = {'start': 5, 'end': 0}

        # Act
        response = self.client.get(
            '/api/rhythm-of-life',
            query_string=data
            )

        # Assert
        self.assertEqual(response.status_code, 400)
