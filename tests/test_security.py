import json
import os

from base64 import b64encode, urlsafe_b64encode
from hashlib import sha256
from io import BytesIO
from PIL import Image
from time import time
from unittest.mock import patch

import hmac
import psycopg2 as pg

from user import user
from utils.tests import CrystalPrismTestCase


def basic(username, password):
    return 'Basic ' + b64encode((username + ':' + password).encode()).decode()


def png_data_url(width=400, height=400, fmt='PNG'):
    buffer = BytesIO()
    Image.new('RGBA', (width, height), (255, 0, 0, 255)).save(buffer, fmt)
    return ('data:image/png;base64,' +
        b64encode(buffer.getvalue()).decode())


def sign(payload):
    # A token with a valid signature over whatever payload the test wants
    header = urlsafe_b64encode(b'{"alg": "HS256", "typ": "JWT"}')
    body = urlsafe_b64encode(json.dumps(payload).encode())
    message = header + b'.' + body
    signature = urlsafe_b64encode(hmac.new(
        os.environ['SECRET_KEY'].encode(), message, digestmod=sha256).digest())
    return (message + b'.' + signature).decode()


# Test the login and account-creation throttle
class TestThrottle(CrystalPrismTestCase):
    def setUp(self):
        super().setUp()
        self.create_user()

    def attempt(self, password, username=None, ip='203.0.113.1'):
        return self.client.get('/api/login', headers={
            'Authorization': basic(username or self.username, password),
            'X-Forwarded-For': ip})

    def test_account_locked_after_ten_failures(self):
        for _ in range(10):
            self.assertEqual(self.attempt('wrong-password').status_code, 401)

        # Even the right password is refused while the account is locked
        response = self.attempt('password')

        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers['Retry-After']), 0)

    def test_success_clears_account_failures(self):
        for _ in range(9):
            self.attempt('wrong-password')

        self.assertEqual(self.attempt('password').status_code, 200)

        # The count restarted, so nine more failures still leave it open
        for _ in range(9):
            self.attempt('wrong-password')

        self.assertEqual(self.attempt('password').status_code, 200)

    def test_address_locked_after_thirty_failures(self):
        # Spread across accounts so no single account reaches its limit
        for i in range(30):
            self.attempt('wrong-password', username='nobody' + str(i))

        self.assertEqual(self.attempt('password').status_code, 429)

        # Another address is unaffected
        self.assertEqual(
            self.attempt('password', ip='203.0.113.2').status_code, 200)

    def test_signup_capped_per_address(self):
        def signup(name, ip):
            return self.client.post('/api/user',
                data=json.dumps({'username': name, 'password': 'password'}),
                content_type='application/json',
                headers={'X-Forwarded-For': ip})

        for i in range(5):
            self.assertEqual(
                signup('cap' + str(i), '203.0.113.9').status_code, 201)

        response = signup('cap5', '203.0.113.9')

        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)
        self.assertEqual(signup('cap6', '203.0.113.10').status_code, 201)

    def test_signup_rejects_non_str_username(self):
        response = self.client.post('/api/user',
            data=json.dumps({'username': ['a'], 'password': 'password'}),
            content_type='application/json')

        self.assertEqual(response.status_code, 400)


# Test update_user's field validation
class TestProfileValidation(CrystalPrismTestCase):
    def setUp(self):
        super().setUp()
        self.create_user()
        self.login()

    def patch(self, **changes):
        data = {
            'about': 'Test',
            'background_color': '#000000',
            'email': 'test@crystalprism.io',
            'email_public': True,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'Test',
            'name_public': True,
            'password': '',
            'username': self.username
            }
        data.update(changes)

        return self.client.patch('/api/user/' + self.username,
            headers={'Authorization': 'Bearer ' + self.token},
            data=json.dumps(data), content_type='application/json')

    def test_non_str_text_fields_rejected(self):
        for field, value in (('about', ['<script>']), ('first_name', 1),
                             ('last_name', {'a': 'b'}), ('about', None)):
            response = self.patch(**{field: value})

            self.assertEqual(response.status_code, 400, field)

    def test_null_email_allowed(self):
        self.assertEqual(self.patch(email=None).status_code, 200)

    def test_non_str_email_rejected(self):
        self.assertEqual(self.patch(email=['a@b.c']).status_code, 400)

    def test_colours_must_be_hex(self):
        for value in ('red', '#fff', '#00000g', '#000000;x:y', None, 7):
            self.assertEqual(
                self.patch(background_color=value).status_code, 400, value)
            self.assertEqual(
                self.patch(icon_color=value).status_code, 400, value)

        self.assertEqual(
            self.patch(background_color='#9FFFAD',
                       icon_color='#ffb4e6').status_code, 200)

    def test_booleans_must_be_booleans(self):
        self.assertEqual(self.patch(email_public='yes').status_code, 400)


# Test verify_token against malformed and stale tokens
class TestTokenVerification(CrystalPrismTestCase):
    def setUp(self):
        super().setUp()
        self.create_user()
        self.login()

    def verify(self, token):
        return self.client.get('/api/user/verify',
            headers={'Authorization': 'Bearer ' + token})

    def password_hash(self):
        conn = pg.connect(os.environ['DB_CONNECTION'])
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM cp_user WHERE username = %s;',
            (self.username,))
        password_hash = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return password_hash

    def test_login_token_verifies(self):
        self.assertEqual(self.verify(self.token).status_code, 200)

    def test_signed_payload_missing_exp_is_401(self):
        token = sign({'username': self.username,
            'pwd': user.password_fingerprint(self.password_hash())})

        self.assertEqual(self.verify(token).status_code, 401)

    def test_signed_payload_not_json_is_401(self):
        header = urlsafe_b64encode(b'{"alg": "HS256", "typ": "JWT"}')
        message = header + b'.' + urlsafe_b64encode(b'not json')
        signature = urlsafe_b64encode(hmac.new(
            os.environ['SECRET_KEY'].encode(), message,
            digestmod=sha256).digest())

        self.assertEqual(
            self.verify((message + b'.' + signature).decode()).status_code,
            401)

    def test_ring_bridge_token_without_fingerprint_verifies(self):
        # auth.crystalprism.io mints exactly {username, exp}, in this byte form
        token = sign({'username': self.username, 'exp': int(time()) + 600})

        self.assertEqual(self.verify(token).status_code, 200)

    def test_wrong_fingerprint_is_401(self):
        token = sign({'username': self.username, 'exp': int(time()) + 600,
            'pwd': 'not-the-fingerprint'})

        self.assertEqual(self.verify(token).status_code, 401)

    def test_non_str_fingerprint_is_401(self):
        token = sign({'username': self.username, 'exp': int(time()) + 600,
            'pwd': 1})

        self.assertEqual(self.verify(token).status_code, 401)

    def test_forged_signature_is_401(self):
        header, payload, _ = self.token.split('.')
        forged = header + '.' + payload + '.' + urlsafe_b64encode(
            b'x' * 32).decode()

        self.assertEqual(self.verify(forged).status_code, 401)

    def test_password_change_revokes_old_tokens(self):
        old_token = self.token

        response = self.client.patch('/api/user/' + self.username,
            headers={'Authorization': 'Bearer ' + old_token},
            data=json.dumps({
                'about': '', 'background_color': '#ffffff', 'email': None,
                'email_public': False, 'first_name': '',
                'icon_color': '#000000', 'last_name': '',
                'name_public': False, 'password': 'new-password',
                'username': self.username}),
            content_type='application/json')
        new_token = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.verify(old_token).status_code, 401)
        self.assertEqual(self.verify(new_token).status_code, 200)

    def test_profile_edit_without_password_keeps_token(self):
        response = self.client.patch('/api/user/' + self.username,
            headers={'Authorization': 'Bearer ' + self.token},
            data=json.dumps({
                'about': 'hi', 'background_color': '#ffffff', 'email': None,
                'email_public': False, 'first_name': '',
                'icon_color': '#000000', 'last_name': '',
                'name_public': False, 'password': '',
                'username': self.username}),
            content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.verify(self.token).status_code, 200)


# Test the drawing upload's image validation
class TestDrawingUpload(CrystalPrismTestCase):
    def setUp(self):
        super().setUp()
        self.create_user()
        self.login()

    def post(self, drawing):
        return self.client.post('/api/canvashare/drawing',
            headers={'Authorization': 'Bearer ' + self.token},
            data=json.dumps({'drawing': drawing, 'title': 'Test'}),
            content_type='application/json')

    def assert_rejected(self, drawing):
        response = self.post(drawing)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True),
            'Drawing must be base64-encoded PNG image')

    @patch('canvashare.canvashare.boto3')
    def test_valid_png_stored_as_image_png(self, boto3):
        response = self.post(png_data_url())

        self.assertEqual(response.status_code, 201)
        bucket = boto3.resource.return_value.Bucket.return_value
        self.assertEqual(
            bucket.put_object.call_args.kwargs['ContentType'], 'image/png')

    def test_other_format_behind_png_prefix_rejected(self):
        self.assert_rejected(png_data_url(fmt='GIF'))

    def test_garbage_behind_png_prefix_rejected(self):
        self.assert_rejected('data:image/png;base64,' +
            b64encode(b'\x89PNG\r\n\x1a\n' + b'x' * 100).decode())

    def test_prefix_elsewhere_in_string_rejected(self):
        self.assert_rejected('x' + png_data_url())

    def test_oversized_dimensions_rejected(self):
        self.assert_rejected(png_data_url(width=1001, height=10))

    def test_oversized_payload_rejected(self):
        self.assert_rejected('data:image/png;base64,' +
            'A' * (2 * 1024 * 1024))

    def test_non_str_drawing_rejected(self):
        self.assert_rejected(['data:image/png;base64,'])


# Test that an unset ENV_TYPE is treated as not-Dev rather than crashing
class TestEnvType(CrystalPrismTestCase):
    def test_origin_check_without_env_type(self):
        with patch.dict(os.environ):
            os.environ.pop('ENV_TYPE', None)

            self.assertFalse(user.origin_allowed('http://localhost:3000'))
            self.assertTrue(user.origin_allowed('https://crystalprism.io'))
