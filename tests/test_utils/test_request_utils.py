from unittest.mock import patch, Mock, MagicMock
import unittest
import urllib
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

    @patch('urllib.request.urlopen')
    def test_read_url_content(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_read = MagicMock()
        mock_read.decode.return_value = "content"
        mock_response.read.return_value = mock_read
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        content = request_utils.read_url_content('http://example.com')
        expected = "content"
        self.assertEqual(expected, content)

    @patch('urllib.request.urlopen')
    def test_read_url_content_failure(self, mock_urlopen):
        mock_response = Mock()
        mock_response.getcode.return_value = 404
        logging.disable(logging.WARNING)
        content = request_utils.read_url_content('http://example.com')
        logging.disable(logging.NOTSET)
        self.assertIsNone(content)

    @patch('urllib.request.urlopen', side_effect=urllib.error.URLError('URL error'))
    def test_read_url_content_exception(self, mock_urlopen):
        content = request_utils.read_url_content('http://example.com')
        self.assertIsNone(content)

    @patch('webbrowser.open')
    def test_open_url_in_browser(self, mock_webbrowser_open):
        request_utils.open_url_in_browser('http://example.com')
        mock_webbrowser_open.assert_called_once_with('http://example.com', new=2)
