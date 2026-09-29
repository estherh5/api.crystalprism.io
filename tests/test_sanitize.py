import json
import os
import unittest

from unittest.mock import patch
from utils.tests import CrystalPrismTestCase


IMG_ONERROR = '<img src=x onerror=alert(1)>'
SCRIPT = '<script>alert(1)</script>'
JS_HREF = '<a href="javascript:alert(1)">click</a>'
# Fits the 25-character title columns
TITLE_XSS = '<svg onload=alert(1)>'

# What Thought Writer's editor emits (a real stored post's shapes: centred
# div, bold/underline/strike/sub/sup, coloured font, list, links, pasted image)
FORMATTED = (
    '<div style="text-align: center;"><b>Welcome</b> to <u>the</u> '
    '<font color="#ff00ff">board</font></div><div><br></div>'
    '<div><ul><li><i>one</i></li><li><strike style="font-weight: bold;">'
    'S</strike> <sub>2</sub><sup>3</sup></li></ul><ol><li>a</li></ol></div>'
    '<div><a href="https://crystalprism.io/canvashare">CanvaShare</a> or '
    '<a href="mailto:admin@crystalprism.io" style="">email</a>&nbsp;me</div>'
    '<div align="right"><img src="https://example.com/a.png">'
    '<img src="data:image/png;base64,iVBORw0KGgo="></div>'
    )


class TestRichTextSanitiser(unittest.TestCase):
    def setUp(self):
        from utils import sanitize
        self.sanitize = sanitize

    def test_payloads_are_neutralised(self):
        clean = self.sanitize.clean_rich_text
        self.assertEqual(clean('hi' + IMG_ONERROR), 'hi<img>')
        self.assertEqual(clean('hi' + SCRIPT), 'hi')
        self.assertEqual(clean(JS_HREF), '<a>click</a>')
        self.assertEqual(clean('<a href="data:text/html,x">y</a>'), '<a>y</a>')
        self.assertEqual(
            clean('<div style="position:fixed;top:0">x</div>'), '<div>x</div>')
        self.assertEqual(
            clean('<font color="red;background:url(x)">x</font>'),
            '<font>x</font>')
        self.assertEqual(
            clean('<b onclick="alert(1)" class="x" id="y">x</b>'), '<b>x</b>')
        self.assertEqual(
            clean('<iframe src="https://evil"></iframe><svg onload=alert(1)>'
                  '<style>*{}</style>t'), 't')

    def test_editor_formatting_survives_unchanged(self):
        self.assertEqual(self.sanitize.clean_rich_text(FORMATTED), FORMATTED)

    def test_svg_data_uri_stripped_png_survives(self):
        clean = self.sanitize.clean_rich_text
        self.assertEqual(
            clean('<img src="data:image/svg+xml;base64,'
                  'PHN2ZyBvbmxvYWQ9YWxlcnQoMSk+">'),
            '<img>')
        png = '<img src="data:image/png;base64,iVBORw0KGgo=">'
        self.assertEqual(clean(png), png)

    def test_contains_markup(self):
        contains = self.sanitize.contains_markup
        for text in (IMG_ONERROR, SCRIPT, '</b>', '<!-- x -->', TITLE_XSS):
            self.assertTrue(contains(text), text)
        for text in ('I <3 cats', 'a < b > c', '< img>', 'Tom & Jerry', 'naïve 🎨',
                     'test@crystalprism.io'):
            self.assertFalse(contains(text), text)


# Stored content reaches crystalprism.io pages, so the write endpoints must
# store only what the editor could have produced
class TestSanitiseOnWrite(CrystalPrismTestCase):
    def auth(self):
        self.create_user()
        self.login()
        return {'Authorization': 'Bearer ' + self.token}

    def send(self, method, path, header, data):
        return getattr(self.client, method)(
            path, headers=header, data=json.dumps(data),
            content_type='application/json')

    def test_post_content_stored_sanitised(self):
        header = self.auth()
        response = self.send('post', '/api/thought-writer/post', header, {
            'content': FORMATTED + IMG_ONERROR + SCRIPT + JS_HREF,
            'public': True, 'title': 'Test'})
        self.assertEqual(response.status_code, 201)
        post_id = response.get_data(as_text=True)

        post = json.loads(self.client.get(
            '/api/thought-writer/post/' + post_id).get_data(as_text=True))
        self.assertEqual(post['content'], FORMATTED + '<img><a>click</a>')

        # PATCH is sanitised the same way
        response = self.send('patch', '/api/thought-writer/post/' + post_id,
            header, {'content': 'x' + IMG_ONERROR, 'public': True,
                     'title': 'Test'})
        self.assertEqual(response.status_code, 200)
        post = json.loads(self.client.get(
            '/api/thought-writer/post/' + post_id).get_data(as_text=True))
        self.assertEqual(post['content'], 'x<img>')

    def test_post_content_only_script_is_blank(self):
        header = self.auth()
        response = self.send('post', '/api/thought-writer/post', header, {
            'content': SCRIPT, 'public': True, 'title': 'Test'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True),
                         'Post cannot be blank')

    def test_post_title_markup_rejected(self):
        header = self.auth()
        for method, path in (('post', '/api/thought-writer/post'),
                             ('patch', '/api/thought-writer/post/1')):
            response = self.send(method, path, header, {
                'content': 'Test', 'public': True, 'title': TITLE_XSS})
            self.assertEqual(response.status_code, 400, method)
            self.assertEqual(response.get_data(as_text=True),
                             'Post title cannot contain HTML')

    def test_comment_content_stored_sanitised(self):
        header = self.auth()
        response = self.send('post', '/api/thought-writer/comment', header, {
            'content': '<b>hi</b>' + IMG_ONERROR + SCRIPT + JS_HREF,
            'post_id': 1})
        self.assertEqual(response.status_code, 201)
        comment_id = response.get_data(as_text=True)

        comment = json.loads(self.client.get(
            '/api/thought-writer/comment/' + comment_id)
            .get_data(as_text=True))
        self.assertEqual(comment['content'], '<b>hi</b><img><a>click</a>')

        response = self.send('patch',
            '/api/thought-writer/comment/' + comment_id, header,
            {'content': '<div>edited</div>' + IMG_ONERROR})
        self.assertEqual(response.status_code, 200)
        comment = json.loads(self.client.get(
            '/api/thought-writer/comment/' + comment_id)
            .get_data(as_text=True))
        self.assertEqual(comment['content'], '<div>edited</div><img>')

    def user_data(self, **changes):
        data = {
            'about': 'I <3 drawing & games',
            'background_color': '#000000',
            'email': 'test@crystalprism.io',
            'email_public': True,
            'first_name': 'Test',
            'icon_color': '#ffffff',
            'last_name': 'User',
            'name_public': True,
            'password': '',
            'username': self.username
            }
        data.update(changes)
        return data

    def test_user_plain_text_fields_reject_markup(self):
        header = self.auth()
        for field in ('about', 'email', 'first_name', 'last_name'):
            response = self.send('patch', '/api/user/' + self.username,
                header, self.user_data(**{field: 'x' + IMG_ONERROR}))
            self.assertEqual(response.status_code, 400, field)
            self.assertEqual(response.get_data(as_text=True),
                             'Profile fields cannot contain HTML', field)

        # Plain text with '<' and '&' that is not markup is still accepted
        response = self.send('patch', '/api/user/' + self.username, header,
                             self.user_data())
        self.assertEqual(response.status_code, 200)
        user_data = json.loads(self.client.get(
            '/api/user/' + self.username).get_data(as_text=True))
        self.assertEqual(user_data['about'], 'I <3 drawing & games')

    def test_non_string_content_and_title_rejected(self):
        header = self.auth()

        response = self.send('post', '/api/thought-writer/post', header, {
            'content': ['x'], 'public': True, 'title': 'Test'})
        self.assertEqual(response.status_code, 400, 'create_post content')
        self.assertEqual(response.get_data(as_text=True),
                         'Post content must be a string')

        response = self.send('post', '/api/thought-writer/post', header, {
            'content': 'Test', 'public': True, 'title': ['x']})
        self.assertEqual(response.status_code, 400, 'create_post title')
        self.assertEqual(response.get_data(as_text=True),
                         'Post title must be a string')

        response = self.send('patch', '/api/thought-writer/post/1', header, {
            'content': ['x'], 'public': True, 'title': 'Test'})
        self.assertEqual(response.status_code, 400, 'update_post content')
        self.assertEqual(response.get_data(as_text=True),
                         'Post content must be a string')

        response = self.send('post', '/api/thought-writer/comment', header, {
            'content': ['x'], 'post_id': 1})
        self.assertEqual(response.status_code, 400, 'create_comment')
        self.assertEqual(response.get_data(as_text=True),
                         'Comment content must be a string')

        response = self.send('patch', '/api/thought-writer/comment/1',
            header, {'content': ['x']})
        self.assertEqual(response.status_code, 400, 'update_comment')
        self.assertEqual(response.get_data(as_text=True),
                         'Comment content must be a string')

        response = self.send('post', '/api/canvashare/drawing', header,
            {'drawing': 'data:image/png;base64,x', 'title': ['x']})
        self.assertEqual(response.status_code, 400, 'create_drawing title')
        self.assertEqual(response.get_data(as_text=True),
                         'Drawing title must be a string')

    @patch('canvashare.canvashare.boto3')
    def test_drawing_title_markup_rejected(self, boto3):
        header = self.auth()
        with open(os.path.dirname(__file__) +
                  '/../fixtures/test-drawing.txt') as drawing:
            drawing = drawing.read()
        response = self.send('post', '/api/canvashare/drawing', header,
                             {'drawing': drawing, 'title': TITLE_XSS})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True),
                         'Drawing title cannot contain HTML')
