import unittest
from unittest.mock import patch
from authenv_service.main import ping, reset
from starlette.requests import Request


class MainTest(unittest.TestCase):
    dummy_request: Request = {}

    def test_ping(self):
        self.assertEqual(ping(), {"test": "successful"})

    @patch('authenv_service.main.gateway_api')
    def test_reset(self, mock_gateway_api):
        mock_gateway_api.set_env_details.return_value = 'return value'
        self.assertEqual(reset(request=self.dummy_request), {"reset": "successful"})
        assert mock_gateway_api.set_env_details.called
