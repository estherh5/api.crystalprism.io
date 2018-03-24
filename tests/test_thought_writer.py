import json
import re

from utils.tests import CrystalPrismTestCase


# Test /api/thought-writer/post endpoint [POST, GET, PATCH, DELETE]
class TestPost(CrystalPrismTestCase):
    def test_post_post_get_patch_and_delete(self):
        # Arrange [POST]
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_data = {
            'content': 'Test',
            'public': False,
            'title': 'Test'
            }

        # Act [POST]
        post_response = self.client.post(
            '/api/thought-writer/post',
            headers=header,
            data=json.dumps(post_data),
            content_type='application/json'
            )
        post_id = post_response.get_data(as_text=True)

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)

        # Act [GET]
        get_response = self.client.get(
            '/api/thought-writer/post/' + post_id,
            headers=header
            )
        post = json.loads(get_response.get_data(as_text=True))

        get_user_response = self.client.get(
            '/api/user',
            headers=header
            )
        user_data = json.loads(get_user_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post['comment_count'], 0)
        self.assertEqual(post['content'], 'Test')
        self.assertEqual(post['title'], 'Test')
        self.assertEqual(post['public'], False)
        self.assertEqual(post['username'], self.username)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            post['created'])), True
            )

        self.assertEqual(user_data['post_count'], 1)

        # Arrange [PATCH]
        patch_data = {
            'content': 'Test 2',
            'public': True,
            'title': 'Test 2'
            }

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/thought-writer/post/' + post_id,
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )

        patched_get_response = self.client.get(
            '/api/thought-writer/post/' + post_id,
            headers=header
            )
        updated_post = json.loads(patched_get_response.get_data(as_text=True))

        # Assert [PATCH]
        self.assertEqual(patch_response.status_code, 200)

        self.assertEqual(patched_get_response.status_code, 200)
        self.assertEqual(updated_post['title'], 'Test 2')
        self.assertEqual(updated_post['content'], 'Test 2')
        self.assertEqual(updated_post['public'], True)

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/thought-writer/post/' + post_id,
            headers=header
            )

        deleted_get_response = self.client.get(
            '/api/thought-writer/post/' + post_id,
            headers=header
            )
        error = deleted_get_response.get_data(as_text=True)

        deleted_get_user_response = self.client.get(
            '/api/user',
            headers=header
            )
        updated_user_data = json.loads(
            deleted_get_user_response.get_data(as_text=True)
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)

        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(error, 'Not found')

        self.assertEqual(updated_user_data['post_count'], 0)

    def test_post_post_unauthorized_error(self):
        # Act
        post_response = self.client.post('/api/thought-writer/post')
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_private_post_get_unauthorized_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {
            'content': 'Test',
            'public': False,
            'title': 'Test'
            }

        # Create private post
        post_response = self.client.post(
            '/api/thought-writer/post',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        post_id = post_response.get_data(as_text=True)

        # Act
        get_response = self.client.get(
            '/api/thought-writer/post/' + post_id
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_post_patch_unauthorized_error(self):
        # Arrange
        post_id = '1'

        # Act
        patch_response = self.client.patch(
            '/api/thought-writer/post/' + post_id
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_post_patch_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_id = '10000'
        data = {
            'content': 'Test',
            'public': False,
            'title': 'Test'
            }

        # Act
        patch_response = self.client.patch(
            '/api/thought-writer/post/' + post_id,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_post_patch_not_writer_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_id = '1'
        data = {
            'content': 'Test',
            'public': False,
            'title': 'Test'
            }

        # Act
        patch_response = self.client.patch(
            '/api/thought-writer/post/' + post_id,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_post_delete_unauthorized_error(self):
        # Arrange
        post_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/thought-writer/post/' + post_id
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_post_delete_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_id = '10000'

        # Act
        delete_response = self.client.delete(
            '/api/thought-writer/post/' + post_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_post_delete_not_writer_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/thought-writer/post/' + post_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/thought-writer/posts endpoint [GET]
class TestPosts(CrystalPrismTestCase):
    def test_posts_get(self):
        # Arrange
        owner_name = 'owner'

        # Act
        get_response = self.client.get('/api/thought-writer/posts')
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(posts), 10)

        # Ensure each post's comment count is an integer
        self.assertEqual(all(
            isinstance(post['comment_count'], int) for post in posts), True)

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

        # Ensure each post's public status is a boolean
        self.assertEqual(all(isinstance(
            post['public'], bool) for post in posts), True)

        # Ensure each title is a string
        self.assertEqual(all(
            isinstance(post['title'], str) for post in posts), True)

        # Ensure each writer is a string
        self.assertEqual(all(isinstance(
            post['username'], str) for post in posts), True)

        # Ensure each writer is not the webpage owner
        self.assertEqual(all(
            post['username'] != owner_name for post in posts
            ), True)

    def test_posts_get_none(self):
        # Arrange
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts',
            query_string=query
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(posts, [])

    def test_posts_get_partial(self):
        # Arrange
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts',
            query_string=query
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(posts), 5)

    def test_posts_get_error(self):
        # Arrange
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts',
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')

    def test_user_public_posts_get(self):
        # Arrange
        writer_name = 'user1'

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts/' + writer_name
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(posts), 10)

        # Ensure each post's comment count is an integer
        self.assertEqual(all(
            isinstance(post['comment_count'], int) for post in posts), True)

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

        # Ensure each post's public status is a boolean
        self.assertEqual(all(isinstance(
            post['public'], bool) for post in posts), True)

        # Ensure each title is a string
        self.assertEqual(all(
            isinstance(post['title'], str) for post in posts), True)

        # Ensure each writer is specified writer name
        self.assertEqual(all(
            post['username'] == writer_name for post in posts
            ), True)

    def test_user_private_posts_get(self):
        # Arrange - create two user accounts
        first_username = 'first_username'
        self.create_user(first_username)
        self.login(first_username)
        first_user_header = {'Authorization': 'Bearer ' + self.token}

        second_username = 'second_username'
        self.create_user(second_username)
        self.login(second_username)
        second_user_header = {'Authorization': 'Bearer ' + self.token}

        private_data = {
            'title': 'Test',
            'content': 'Test',
            'public': False
            }

        public_data = {
            'title': 'Test',
            'content': 'Test',
            'public': True
            }

        # Create private and public post for first user
        private_post_response = self.client.post(
            '/api/thought-writer/post',
            headers=first_user_header,
            data=json.dumps(private_data),
            content_type='application/json'
            )
        private_post_id = private_post_response.get_data(as_text=True)

        public_post_response = self.client.post(
            '/api/thought-writer/post',
            headers=first_user_header,
            data=json.dumps(public_data),
            content_type='application/json'
            )
        public_post_id = public_post_response.get_data(as_text=True)

        # Act
        first_user_get_response = self.client.get(
            '/api/thought-writer/posts/' + first_username,
            headers=first_user_header
            )
        private_public_posts = json.loads(
            first_user_get_response.get_data(as_text=True)
            )

        second_user_get_response = self.client.get(
            '/api/thought-writer/posts/' + first_username,
            headers=second_user_header
            )
        public_posts = json.loads(
            second_user_get_response.get_data(as_text=True)
            )

        # Assert
        self.assertEqual(first_user_get_response.status_code, 200)

        # Ensure first user can get both the private and public post
        self.assertEqual(len(private_public_posts), 2)
        self.assertEqual(any(
            post['post_id'] == int(private_post_id) for post in
            private_public_posts), True)
        self.assertEqual(any(
            post['post_id'] == int(public_post_id) for post in
            private_public_posts), True)

        self.assertEqual(second_user_get_response.status_code, 200)

        # Ensure second user can only get the public post
        self.assertEqual(len(public_posts), 1)
        self.assertEqual(
            public_posts[0]['post_id'] == int(public_post_id), True
            )

        # Hard-delete users for clean-up
        self.delete_user(first_username)
        self.delete_user(second_username)

    def test_user_posts_get_none(self):
        # Arrange
        writer_name = 'user1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts/' + writer_name,
            query_string=query
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(posts, [])

    def test_user_posts_get_partial(self):
        # Arrange
        writer_name = 'user1'
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts/' + writer_name,
            query_string=query
            )
        posts = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(posts), 5)

    def test_user_posts_get_error(self):
        # Arrange
        writer_name = 'user1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/posts/' + writer_name,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')


# Test /api/thought-writer/comment endpoint [POST, GET, PATCH, DELETE]
class TestComment(CrystalPrismTestCase):
    def test_comment_post_get_patch_and_delete(self):
        # Arrange [POST]
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_id = 1
        post_data = {
            'content': 'Test',
            'post_id': post_id
            }

        # Get current number of post's comments
        initial_get_post_response = self.client.get(
            '/api/thought-writer/post/' + str(post_id)
            )
        comment_count = json.loads(
            initial_get_post_response.get_data(as_text=True))['comment_count']

        # Act [POST]
        post_response = self.client.post(
            '/api/thought-writer/comment',
            headers=header,
            data=json.dumps(post_data),
            content_type='application/json'
            )
        comment_id = post_response.get_data(as_text=True)

        # Assert [POST]
        self.assertEqual(post_response.status_code, 201)

        # Act [GET]
        get_response = self.client.get(
            '/api/thought-writer/comment/' + comment_id
            )
        comment = json.loads(get_response.get_data(as_text=True))

        get_post_response = self.client.get(
            '/api/thought-writer/post/' + str(post_id)
            )
        post = json.loads(get_post_response.get_data(as_text=True))

        get_user_response = self.client.get(
            '/api/user',
            headers=header
            )
        user_data = json.loads(get_user_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(comment['comment_id'], int(comment_id))
        self.assertEqual(comment['content'], 'Test')
        self.assertEqual(comment['post_id'], 1)
        self.assertEqual(comment['username'], self.username)

        self.assertEqual(post['comment_count'], comment_count + 1)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            comment['created'])), True
            )

        self.assertEqual(user_data['comment_count'], 1)

        # Arrange [PATCH]
        patch_data = {'content': 'Test 2'}

        # Act [PATCH]
        patch_response = self.client.patch(
            '/api/thought-writer/comment/' + comment_id,
            headers=header,
            data=json.dumps(patch_data),
            content_type='application/json'
            )

        patched_get_response = self.client.get(
            '/api/thought-writer/comment/' + comment_id
            )
        updated_comment = json.loads(
            patched_get_response.get_data(as_text=True)
            )

        # Assert [PATCH]
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patched_get_response.status_code, 200)
        self.assertEqual(updated_comment['content'], 'Test 2')

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/thought-writer/comment/' + comment_id,
            headers=header
            )

        deleted_get_response = self.client.get(
            '/api/thought-writer/comment/' + comment_id
            )
        error = deleted_get_response.get_data(as_text=True)

        deleted_get_user_response = self.client.get(
            '/api/user',
            headers=header
            )
        updated_user_data = json.loads(
            deleted_get_user_response.get_data(as_text=True)
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)

        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(error, 'Not found')

        self.assertEqual(updated_user_data['comment_count'], 0)

    def test_comment_post_unauthorized_error(self):
        # Act
        post_response = self.client.post('/api/thought-writer/comment')
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_comment_post_post_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        data = {
            'content': 'Test',
            'post_id': 10000
            }

        # Act
        post_response = self.client.post(
            '/api/thought-writer/comment',
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_comment_post_post_private_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_data = {
            'title': 'Test',
            'content': 'Test',
            'public': False
            }

        # Create private post
        post_response = self.client.post(
            '/api/thought-writer/post',
            headers=header,
            data=json.dumps(post_data),
            content_type='application/json'
            )
        post_id = post_response.get_data(as_text=True)

        comment_data = {
            'content': 'Test',
            'post_id': post_id
            }

        # Act
        post_response = self.client.post(
            '/api/thought-writer/comment',
            headers=header,
            data=json.dumps(comment_data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_comment_patch_unauthorized_error(self):
        # Arrange
        comment_id = '1'

        # Act
        patch_response = self.client.patch(
            '/api/thought-writer/comment/' + comment_id
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_comment_patch_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        comment_id = '10000'
        data = {'content': 'Test'}

        # Act
        patch_response = self.client.patch(
            '/api/thought-writer/comment/' + comment_id,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_comment_patch_not_commenter_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        comment_id = '1'
        data = {'content': 'Test'}

        # Act
        patch_response = self.client.patch(
            '/api/thought-writer/comment/' + comment_id,
            headers=header,
            data=json.dumps(data),
            content_type='application/json'
            )
        error = patch_response.get_data(as_text=True)

        # Assert
        self.assertEqual(patch_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_comment_delete_unauthorized_error(self):
        # Arrange
        comment_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/thought-writer/comment/' + comment_id
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_comment_delete_not_found_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        comment_id = '10000'

        # Act
        delete_response = self.client.delete(
            '/api/thought-writer/comment/' + comment_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 404)
        self.assertEqual(error, 'Not found')

    def test_comment_delete_not_commenter_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        comment_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/thought-writer/comment/' + comment_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/thought-writer/comments endpoint [GET]
class TestComments(CrystalPrismTestCase):
    def test_comments_get(self):
        # Arrange
        post_id = '1'

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/post/' + post_id
            )
        comments = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(comments), 10)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            comment['created'])) for comment in comments), True)

        # Ensure each comment id is an integer
        self.assertEqual(all(isinstance(comment['comment_id'], int)
            for comment in comments), True)

        # Ensure each comment's content is a string
        self.assertEqual(all(isinstance(comment['content'], str)
            for comment in comments), True)

        # Ensure each post id is specified post id
        self.assertEqual(all(comment['post_id'] == int(post_id)
            for comment in comments), True)

        # Ensure each commenter is a string
        self.assertEqual(all(isinstance(comment['username'], str)
            for comment in comments), True)

    def test_comments_get_none(self):
        # Arrange
        post_id = '1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/post/' + post_id,
            query_string=query
            )
        comments = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(comments, [])

    def test_comments_get_partial(self):
        # Arrange
        post_id = '1'
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/post/' + post_id,
            query_string=query
            )
        comments = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(comments), 5)

    def test_comments_get_error(self):
        # Arrange
        post_id = '1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/post/' + post_id,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')

    def test_user_comments_get(self):
        # Arrange
        commenter_name = 'user1'

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/user/' + commenter_name
            )
        comments = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(comments), 10)

        # Ensure each created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(all(bool(timestamp_pattern.match(
            comment['created'])) for comment in comments), True)

        # Ensure each comment id is an integer
        self.assertEqual(all(isinstance(comment['comment_id'], int)
            for comment in comments), True)

        # Ensure each comment's content is a string
        self.assertEqual(all(isinstance(comment['content'], str)
            for comment in comments), True)

        # Ensure each post id is an integer
        self.assertEqual(all(isinstance(comment['post_id'], int)
            for comment in comments), True)

        # Ensure each post's content is a string
        self.assertEqual(all(isinstance(comment['post_content'], str)
            for comment in comments), True)

        # Ensure each post's title is a string
        self.assertEqual(all(isinstance(comment['title'], str)
            for comment in comments), True)

        # Ensure each commenter is specified commenter name
        self.assertEqual(all(comment['username'] == commenter_name
            for comment in comments), True)

        # Ensure each post's writer is a string
        self.assertEqual(all(isinstance(comment['post_writer'], str)
            for comment in comments), True)

    def test_user_comments_get_none(self):
        # Arrange
        commenter_name = 'user1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/user/' + commenter_name,
            query_string=query
            )
        comments = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(comments, [])

    def test_user_comments_get_partial(self):
        # Arrange
        commenter_name = 'user1'
        query = {'end': 5}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/user/' + commenter_name,
            query_string=query
            )
        comments = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(comments), 5)

    def test_user_comments_get_error(self):
        # Arrange
        commenter_name = 'user1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/thought-writer/comments/user/' + commenter_name,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')
