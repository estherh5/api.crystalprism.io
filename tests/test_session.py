import json
import os

from base64 import b64encode
from server import app
from unittest.mock import patch
from utils.tests import CrystalPrismTestCase


SITE_ORIGIN = 'https://crystalprism.io'
OTHER_ORIGIN = 'https://evil.example'


# Test the HttpOnly session cookie that browsers use alongside the bearer token
class TestSession(CrystalPrismTestCase):
    def setUp(self):
        super().setUp()
        self.create_user()
        self.login()

    def session_client(self):
        client = app.test_client()
        client.set_cookie('cp_session', self.token, path='/api')
        return client

    def session_cookie(self, response):
        cookies = [c for c in response.headers.getlist('Set-Cookie')
            if c.startswith('cp_session=')]
        self.assertEqual(len(cookies), 1)
        return cookies[0]

    def patch_data(self):
        return json.dumps({
            'about': 'Test',
            'background_color': '#000000',
            'email': 'test@crystalprism.io',
            'email_public': True,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'Test',
            'name_public': True,
            'password': 'password',
            'username': self.username
            })

    def test_login_sets_session_cookie(self):
        # Arrange
        b64_user_pass = b64encode(
            (self.username + ':password').encode()).decode()

        # Act
        response = self.client.get(
            '/api/login',
            headers={'Authorization': 'Basic ' + b64_user_pass}
            )
        token = response.get_data(as_text=True)
        cookie = self.session_cookie(response)

        # Assert: body still carries the token for bearer clients
        self.assertEqual(response.status_code, 200)
        self.assertTrue(cookie.startswith('cp_session=' + token + ';'))
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Secure', cookie)
        self.assertIn('SameSite=Strict', cookie)
        self.assertIn('Path=/api', cookie)

    def test_cookie_get_without_origin(self):
        # Act
        response = self.session_client().get('/api/user/verify')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.get_data(as_text=True))['username'],
            self.username)

    def test_cookie_patch_allowed_origin(self):
        # Act
        response = self.session_client().patch(
            '/api/user/' + self.username,
            headers={'Origin': SITE_ORIGIN},
            data=self.patch_data(),
            content_type='application/json'
            )

        # Assert: the re-minted token is returned and set as the cookie
        self.assertEqual(response.status_code, 200)
        token = response.get_data(as_text=True)
        self.assertTrue(self.session_cookie(response)
            .startswith('cp_session=' + token + ';'))

    def test_cookie_patch_bad_origin_error(self):
        for headers in ({'Origin': OTHER_ORIGIN}, {}):
            # Act
            response = self.session_client().patch(
                '/api/user/' + self.username,
                headers=headers,
                data=self.patch_data(),
                content_type='application/json'
                )

            # Assert
            self.assertEqual(response.status_code, 403)

    def test_cookie_post_bad_origin_error(self):
        # Act
        response = self.session_client().post(
            '/api/canvashare/drawing-like',
            headers={'Origin': OTHER_ORIGIN},
            data=json.dumps({'drawing_id': '1'}),
            content_type='application/json'
            )

        # Assert
        self.assertEqual(response.status_code, 403)

    def test_bearer_still_works_without_origin(self):
        # Act
        response = self.client.patch(
            '/api/user/' + self.username,
            headers={'Authorization': 'Bearer ' + self.token},
            data=self.patch_data(),
            content_type='application/json'
            )

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_header_wins_over_cookie(self):
        # Act
        response = self.session_client().get(
            '/api/user/verify',
            headers={'Authorization': 'Bearer null'}
            )

        # Assert
        self.assertEqual(response.status_code, 401)

    def test_non_bearer_scheme_error(self):
        # Arrange
        for scheme in ('Basic ', 'Token ', ''):
            # Act
            response = self.client.get(
                '/api/user/verify',
                headers={'Authorization': scheme + self.token}
                )

            # Assert
            self.assertEqual(response.status_code, 401)

    def test_tampered_signature_error(self):
        # Arrange
        header, payload, signature = self.token.split('.')
        forged = header + '.' + payload + '.' + ('A' * len(signature))

        # Act
        response = self.client.get(
            '/api/user/verify',
            headers={'Authorization': 'Bearer ' + forged}
            )

        # Assert
        self.assertEqual(response.status_code, 401)

    def test_session_post(self):
        # Act
        response = self.client.post(
            '/api/session',
            headers={'Authorization': 'Bearer ' + self.token,
                'Origin': SITE_ORIGIN}
            )
        cookie = self.session_cookie(response)

        # Assert
        self.assertEqual(response.status_code, 204)
        self.assertTrue(cookie.startswith('cp_session=' + self.token + ';'))
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Secure', cookie)
        self.assertIn('SameSite=Strict', cookie)
        self.assertIn('Path=/api', cookie)
        max_age = int(cookie.split('Max-Age=')[1].split(';')[0])
        self.assertTrue(3500 < max_age <= 3600)

    def test_session_post_errors(self):
        # Bad origin
        response = self.client.post(
            '/api/session',
            headers={'Authorization': 'Bearer ' + self.token,
                'Origin': OTHER_ORIGIN}
            )
        self.assertEqual(response.status_code, 403)

        # No bearer token (a cookie alone cannot mint a session)
        response = self.session_client().post(
            '/api/session',
            headers={'Origin': SITE_ORIGIN}
            )
        self.assertEqual(response.status_code, 401)

        # Invalid bearer token
        response = self.client.post(
            '/api/session',
            headers={'Authorization': 'Bearer null', 'Origin': SITE_ORIGIN}
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.getlist('Set-Cookie'), [])

    def test_logout_post(self):
        # Act
        response = self.session_client().post(
            '/api/logout',
            headers={'Origin': SITE_ORIGIN}
            )
        cookie = self.session_cookie(response)

        # Assert
        self.assertEqual(response.status_code, 204)
        self.assertTrue(cookie.startswith('cp_session=;'))
        self.assertIn('Max-Age=0', cookie)
        self.assertIn('Path=/api', cookie)

    def test_logout_post_bad_origin_error(self):
        # Act
        response = self.session_client().post(
            '/api/logout',
            headers={'Origin': OTHER_ORIGIN}
            )

        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.headers.getlist('Set-Cookie'), [])

    def test_cors_allowed_origin(self):
        for origin in (SITE_ORIGIN, 'https://www.crystalprism.io'):
            # Act
            response = self.client.get(
                '/api/ping', headers={'Origin': origin})

            # Assert
            self.assertEqual(
                response.headers['Access-Control-Allow-Origin'], origin)
            self.assertEqual(
                response.headers['Access-Control-Allow-Credentials'], 'true')
            self.assertIn('Origin', response.headers['Vary'])

    def test_cors_other_origin(self):
        # Act
        response = self.client.get(
            '/api/ping', headers={'Origin': OTHER_ORIGIN})

        # Assert: flask-cors's uncredentialed answer, unchanged (it echoes the
        # origin rather than sending a literal '*')
        self.assertEqual(
            response.headers['Access-Control-Allow-Origin'], OTHER_ORIGIN)
        self.assertNotIn('Access-Control-Allow-Credentials', response.headers)
        self.assertIn('Origin', response.headers['Vary'])

    def test_cors_preflight_allowed_origin(self):
        for method in ('PATCH', 'DELETE'):
            # Act
            response = self.client.options(
                '/api/user/' + self.username,
                headers={'Origin': SITE_ORIGIN,
                    'Access-Control-Request-Method': method,
                    'Access-Control-Request-Headers': 'Content-Type'}
                )

            # Assert
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers['Access-Control-Allow-Origin'], SITE_ORIGIN)
            self.assertEqual(
                response.headers['Access-Control-Allow-Credentials'], 'true')
            self.assertIn(method,
                response.headers['Access-Control-Allow-Methods'])
            self.assertEqual(
                response.headers['Access-Control-Allow-Headers'].lower(),
                'content-type')

    def test_dev_localhost_origin(self):
        origins = ('http://localhost:8000', 'http://127.0.0.1:5500')

        # Allowed in Dev
        with patch.dict(os.environ, {'ENV_TYPE': 'Dev'}):
            for origin in origins:
                response = self.client.get(
                    '/api/ping', headers={'Origin': origin})
                self.assertEqual(
                    response.headers['Access-Control-Allow-Origin'], origin)
                self.assertEqual(response.headers[
                    'Access-Control-Allow-Credentials'], 'true')

            response = self.client.get(
                '/api/ping', headers={'Origin': 'http://localhost.evil.io'})
            self.assertNotIn('Access-Control-Allow-Credentials',
                response.headers)

        # Refused in Prod
        with patch.dict(os.environ, {'ENV_TYPE': 'Prod'}):
            for origin in origins:
                response = self.client.get(
                    '/api/ping', headers={'Origin': origin})
                self.assertNotIn('Access-Control-Allow-Credentials',
                    response.headers)
