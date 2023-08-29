from unittest.mock import patch, Mock, MagicMock, mock_open
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

    @patch('http.client.HTTPSConnection')
    def test_http_get_request(self, mock_http_connection):
        mock_connection = MagicMock()
        mock_getresponse = MagicMock()
        mock_read = MagicMock()
        mock_read.decode.return_value = "mocked_decode"
        mock_getresponse.read.return_value = mock_read
        mock_connection.getresponse.return_value = mock_getresponse
        mock_connection.__enter__.return_value = mock_connection
        mock_http_connection.return_value = mock_connection
        url = 'https://api.github.com/mocked_path'
        response, response_content = request_utils.http_get_request(url=url)
        expected = mock_getresponse
        self.assertEqual(expected, response)
        expected = "mocked_decode"
        self.assertEqual(expected, response_content)

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

    def test_get_http_response_type_informational_response(self):
        self.assertEqual(request_utils.get_http_response_type(100), "informational")
        self.assertEqual(request_utils.get_http_response_type(199), "informational")

    def test_get_http_response_type_successful_response(self):
        self.assertEqual(request_utils.get_http_response_type(200), "successful")
        self.assertEqual(request_utils.get_http_response_type(299), "successful")

    def test_get_http_response_type_redirection_message(self):
        self.assertEqual(request_utils.get_http_response_type(300), "redirection")
        self.assertEqual(request_utils.get_http_response_type(399), "redirection")

    def test_get_http_response_type_client_error_response(self):
        self.assertEqual(request_utils.get_http_response_type(400), "client error")
        self.assertEqual(request_utils.get_http_response_type(499), "client error")

    def test_get_http_response_type_server_error_response(self):
        self.assertEqual(request_utils.get_http_response_type(500), "server error")
        self.assertEqual(request_utils.get_http_response_type(599), "server error")

    def test_get_http_response_type_unknown_response_type(self):
        self.assertEqual(request_utils.get_http_response_type(0), "unknown response")
        self.assertEqual(request_utils.get_http_response_type(999), "unknown response")

    @patch('urllib.request.urlopen')
    @patch('builtins.open', new_callable=mock_open())
    def test_download_file(self, mock_open, mock_urlopen):
        # Mock response from urlopen
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.info.return_value = {'Content-Length': '10000'}
        mock_response.read.side_effect = [b'chunk1', b'chunk2', b'']

        mock_urlopen.return_value = mock_response

        # Mock callback function
        mock_callback = MagicMock()

        # Call the function
        request_utils.download_file("http://example.com/file.txt", "downloaded/file.txt",
                                    chunk_size=5, callback=mock_callback)

        # Assertions
        mock_urlopen.assert_called_once_with("http://example.com/file.txt")
        mock_open.assert_called_once_with("downloaded/file.txt", 'wb')
        mock_response.read.assert_called()
        self.assertEqual(mock_response.read.call_count, 3)
        mock_callback.assert_called_with(100.0)

    @patch('socket.socket')
    def test_connected_to_internet(self, mock_socket):
        # Mock the socket to simulate a successful connection
        instance = mock_socket.return_value
        instance.connect.return_value = None

        result = request_utils.is_connected_to_internet()
        self.assertTrue(result)

    @patch('socket.socket')
    def test_not_connected_to_internet(self, mock_socket):
        # Mock the socket to simulate a failed connection
        instance = mock_socket.return_value
        instance.connect.side_effect = Exception("Test exception")

        result = request_utils.is_connected_to_internet()
        self.assertFalse(result)

    @patch('gt.utils.request_utils.open_url_in_browser')
    def test_open_package_docs_url_in_browser(self, mocked_open_url):
        request_utils.open_package_docs_url_in_browser()
        mocked_open_url.assert_called_once()
