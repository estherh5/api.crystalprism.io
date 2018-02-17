import fcntl
import json
import os
import time
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
        self.delete_admin_user()

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

    # Delete user as admin
    def delete_user_admin(self, username_to_delete='test' + now,
        admin_username='admin' + now, admin_password='password'):
        self.create_user(admin_username, admin_password)

        # Set 'admin' item in user account to True
        with open(os.path.dirname(__file__) +
            '/../user/users.json', 'r') as users_file:
            users = json.load(users_file)

            for user_data in users:
                if user_data['username'].lower() == admin_username.lower():
                    user_data['admin'] = True

        with open(os.path.dirname(__file__) +
            '/../user/users.json', 'w') as users_file:
            # Lock file to prevent overwrite
            fcntl.flock(users_file, fcntl.LOCK_EX)
            json.dump(users, users_file)
            # Release lock on file
            fcntl.flock(users_file, fcntl.LOCK_UN)

        self.login(admin_username, admin_password)
        header = {'Authorization': 'Bearer ' + self.token}

        response = self.client.delete(
            '/api/user/' + username_to_delete,
            headers=header
        )

    # Delete admin user
    def delete_admin_user(self, username='admin' + now, password='password'):
        self.login(username, password)

        header = {'Authorization': 'Bearer ' + self.token}

        response = self.client.delete(
            '/api/user/' + username,
            headers=header
        )
