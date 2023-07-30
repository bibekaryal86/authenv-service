import unittest
from unittest.mock import patch

from src.authenv_service.main import ping, reset
from tests.authenv_service_test.utils_test import dummy_request


class MainTest(unittest.TestCase):
    def test_ping(self):
        self.assertEqual(ping(), {"test": "successful"})

    @patch("src.authenv_service.main.gateway_api")
    def test_reset(self, mock_gateway_api):
        mock_gateway_api.set_env_details.return_value = "return value"
        self.assertEqual(reset(request=dummy_request), {"reset": "successful"})
        assert mock_gateway_api.set_env_details.called
