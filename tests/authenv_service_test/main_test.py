import unittest

from authenv_service.main import tests_ping


class TestMain(unittest.TestCase):
    def test_tests_ping(self):
        self.assertEqual(tests_ping(), {"test": "successful"})
