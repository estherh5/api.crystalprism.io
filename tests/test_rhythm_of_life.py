import json
import re

from utils.tests import CrystalPrismTestCase


# Test /api/rhythm-of-life/score endpoint [POST, GET, DELETE]
class TestScore(CrystalPrismTestCase):
    def test_score_post_get_and_delete(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        first_score_data = {'score': 360000}
        second_score_data = {'score': 100000}

        # Act [POST] - post two scores
        first_post_response = self.client.post(
            '/api/rhythm-of-life/score',
            headers=header,
            data=json.dumps(first_score_data),
            content_type='application/json'
            )
        first_score_id = first_post_response.get_data(as_text=True)

        second_post_response = self.client.post(
            '/api/rhythm-of-life/score',
            headers=header,
            data=json.dumps(second_score_data),
            content_type='application/json'
            )
        second_score_id = second_post_response.get_data(as_text=True)

        # Assert [POST]
        self.assertEqual(first_post_response.status_code, 201)
        self.assertEqual(second_post_response.status_code, 201)

        # Act [GET]
        get_response = self.client.get(
            '/api/rhythm-of-life/score/' + first_score_id
            )
        score_data = json.loads(get_response.get_data(as_text=True))

        get_user_response = self.client.get(
            '/api/user/' + self.username
            )
        user_data = json.loads(get_user_response.get_data(as_text=True))

        # Assert [GET]
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(score_data['score_id'], int(first_score_id))
        self.assertEqual(score_data['score'], 360000)
        self.assertEqual(score_data['username'], self.username)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            score_data['created'])), True
            )

        self.assertEqual(user_data['rhythm_score_count'], 2)
        self.assertEqual(user_data['rhythm_high_score'], 360000)

        # Act [DELETE]
        delete_response = self.client.delete(
            '/api/rhythm-of-life/score/' + first_score_id,
            headers=header
            )

        delete_again_response = self.client.delete(
            '/api/rhythm-of-life/score/' + first_score_id,
            headers=header
            )
        delete_again_error = delete_again_response.get_data(as_text=True)

        deleted_get_response = self.client.get(
            '/api/rhythm-of-life/score/' + first_score_id
            )
        deleted_get_error = deleted_get_response.get_data(as_text=True)

        deleted_get_user_response = self.client.get(
            '/api/user/' + self.username
            )
        updated_user_data = json.loads(deleted_get_user_response.get_data(
            as_text=True)
            )

        # Assert [DELETE]
        self.assertEqual(delete_response.status_code, 200)

        self.assertEqual(delete_again_response.status_code, 404)
        self.assertEqual(delete_again_error, 'Not found')

        self.assertEqual(deleted_get_response.status_code, 404)
        self.assertEqual(deleted_get_error, 'Not found')

        self.assertEqual(updated_user_data['rhythm_score_count'], 1)
        self.assertEqual(updated_user_data['rhythm_high_score'], 100000)

    def test_score_post_unauthorized_error(self):
        # Act
        post_response = self.client.post('/api/rhythm-of-life/score')
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_score_post_data_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}

        # Act
        post_response = self.client.post(
            '/api/rhythm-of-life/score',
            headers=header
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Request must contain score')

    def test_score_post_score_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        post_data = {
            'score': ''
            }

        # Act
        post_response = self.client.post(
            '/api/rhythm-of-life/score',
            headers=header,
            data=json.dumps(post_data),
            content_type='application/json'
            )
        error = post_response.get_data(as_text=True)

        # Assert
        self.assertEqual(post_response.status_code, 400)
        self.assertEqual(error, 'Score must be an integer')

    def test_score_delete_unauthorized_error(self):
        # Arrange
        score_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/rhythm-of-life/score/' + score_id
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')

    def test_score_delete_not_player_error(self):
        # Arrange
        self.create_user()
        self.login()
        header = {'Authorization': 'Bearer ' + self.token}
        score_id = '1'

        # Act
        delete_response = self.client.delete(
            '/api/rhythm-of-life/score/' + score_id,
            headers=header
            )
        error = delete_response.get_data(as_text=True)

        # Assert
        self.assertEqual(delete_response.status_code, 401)
        self.assertEqual(error, 'Unauthorized')


# Test /api/rhythm-of-life/scores endpoint [GET]
class TestScores(CrystalPrismTestCase):
    def test_scores_get(self):
        # Act
        get_response = self.client.get('/api/rhythm-of-life/scores')
        scores = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(scores), 5)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            scores[0]['created'])), True
            )

        # Ensure each score id is an integer
        self.assertEqual(all(
            isinstance(score['score_id'], int) for score in scores), True)

        # Ensure each score is an integer
        self.assertEqual(all(
            isinstance(score['score'], int) for score in scores), True)

        # Ensure each player is a string
        self.assertEqual(all(
            isinstance(score['username'], str) for score in scores), True)

    def test_scores_get_none(self):
        # Arrange
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores',
            query_string=query
            )
        scores = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(scores, [])

    def test_scores_get_partial(self):
        # Arrange
        query = {'end': 3}

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores',
            query_string=query
            )
        scores = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(scores), 3)

    def test_scores_get_error(self):
        # Arrange
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores',
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')

    def test_user_scores_get(self):
        # Arrange
        player_name = 'user1'

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores/' + player_name
            )
        scores = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(scores), 5)

        # Ensure created timestamp matches UTC format
        timestamp_pattern = re.compile(
            r'\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-6]\d\.\d{3}Z'
            )
        self.assertEqual(bool(timestamp_pattern.match(
            scores[0]['created'])), True
            )

        # Ensure each score id is an integer
        self.assertEqual(all(
            isinstance(score['score_id'], int) for score in scores), True)

        # Ensure each score is an integer
        self.assertEqual(all(
            isinstance(score['score'], int) for score in scores), True)

        # Ensure player is specified player name
        self.assertEqual(all(
            score['username'] == player_name for score in scores), True)

    def test_user_scores_get_none(self):
        # Arrange
        player_name = 'user1'
        query = {'start': 100}

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores/' + player_name,
            query_string=query
            )
        scores = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(scores, [])

    def test_user_scores_get_partial(self):
        # Arrange
        player_name = 'user1'
        query = {'end': 3}

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores/' + player_name,
            query_string=query
            )
        scores = json.loads(get_response.get_data(as_text=True))

        # Assert
        self.assertEqual(len(scores), 3)

    def test_user_scores_get_error(self):
        # Arrange
        player_name = 'user1'
        query = {'start': 5, 'end': 0}

        # Act
        get_response = self.client.get(
            '/api/rhythm-of-life/scores/' + player_name,
            query_string=query
            )
        error = get_response.get_data(as_text=True)

        # Assert
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(error, 'Start param cannot be greater than end')
