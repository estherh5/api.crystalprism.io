import os

from utils.tests import CrystalPrismTestCase


# Test /api/ping endpoint [GET]
class TestPing(CrystalPrismTestCase):
    def test_ping_get(self):
        # Act
        response = self.client.get('/api/ping')

        # Assert
        self.assertEqual(response.status_code, 200)
