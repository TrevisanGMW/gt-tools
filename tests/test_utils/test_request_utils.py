from unittest.mock import patch
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.utils import request_utils


class TestRequestUtils(unittest.TestCase):
    def test_parse_http_request_url(self):
        url = 'https://api.github.com/repos/etc'
        result = request_utils.parse_http_request_url(url=url)
        expected = ('api.github.com', '/repos/etc')
        self.assertEqual(expected, result)

    def test_parse_http_request_url_no_path(self):
        url = 'https://api.github.com/'
        result = request_utils.parse_http_request_url(url=url)
        expected = ('api.github.com', '')
        self.assertEqual(expected, result)

    @patch('http.client.HTTPSConnection.getresponse')
    @patch('http.client.HTTPSConnection.request')
    def test_http_request(self, mock_request, mock_getresponse):
        mock_response = b'This is a mock response'
        mock_getresponse.return_value = mock_response
        url = 'https://api.github.com/mocked_path'
        result = request_utils.http_request(url=url)
        mock_request.assert_called_once_with('GET', "/mocked_path",
                                             headers={'Content-Type': 'application/json; charset=UTF-8',
                                                      'User-Agent': 'packaage_updater'})
        mock_getresponse.assert_called_once()
        self.assertEqual(mock_response, result)

