import time
import json
import unittest

from base64 import b64encode
from server import app


now = str(round(time.time()))  # Current time in ms


class CrystalPrismTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.token = ''  # Login JWT token
        self.username = ''  # Username of test user

    def tearDown(self):
        self.delete_user()

    # Create test user
    def create_user(self, username='test' + now, password='password'):
        self.username = username
        data = {'username': username, 'password': password}

        response = self.client.post(
            '/api/user',
            data=json.dumps(data),
            content_type='application/json'
        )

    # Login as test user and receive JWT token
    def login(self, username='test' + now, password='password'):
        b64_user_pass = str(b64encode((username + ':' + password).encode())
            .decode())
        header = {'Authorization': 'Basic ' + b64_user_pass}

        response = self.client.get(
            '/api/login',
            headers=header
        )
        self.token = response.get_data(as_text=True)

    # Delete test user
    def delete_user(self, username='test' + now, password='password'):
        self.login(username, password)

        header = {'Authorization': 'Bearer ' + self.token}

        response = self.client.delete(
            '/api/user/' + username,
            headers=header
        )
