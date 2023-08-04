"""
Request Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.string_utils import remove_strings_from_string
import http.client as http_client
import urllib.request
import webbrowser
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PACKAGE_RELEASE_URL = 'https://api.github.com/repos/TrevisanGMW/gt-tools/releases/latest'
PACKAGE_TAG_RELEASE_URL = 'https://api.github.com/repos/TrevisanGMW/gt-tools/releases/tags/'


def parse_http_request_url(url):
    """
    Parses and returns two strings to be used with HTTPSConnection

    Args:
        url (str): Rest API url.
                   e.g. "https://api.github.com/repos/**USER**/**REPO**/releases/latest"

    Returns:
        tuple: (str, str) 1: Api host (string between "https://" and next "/")
                          2: The rest of the path (might be "")
    """
    path_no_http = remove_strings_from_string(input_string=url,
                                              undesired_string_list=['https://', 'http://'],
                                              only_prefix=True)
    path_elements = path_no_http.split('/')
    if len(path_elements) < 1:
        raise Exception('Unable to parse GitHub API path. URL seems incomplete.')
    repo = '/' + '/'.join(path_elements[1:])
    repo = "" if repo == '/' else repo
    host_out = path_elements[0]
    return host_out, repo


def http_request(url, host_overwrite=None, path_overwrite=None):
    """
    Make an HTTP GET request to a REST API and return the response.

    Args:
        url (str): Rest API
        host_overwrite (str): String for the host overwrite. For example: "api.github.com"
                              If provided, it will replace whatever was parsed out of the URL. Default None (do nothing)
        path_overwrite (str): String for the path overwrite. For example: "/repos/**USER**/**REPO**/releases/latest"
                              If provided, it will replace whatever was parsed out of the URL. Default None (do nothing)

    Returns:
        HTTPResponse: http.client.HTTPResponse object. Use "response.read()" to retrieve contents.
                      "response.status" for response status (e.g. 200)
                      "response.reason" for response reason (e.g. "OK")
    """
    try:
        host, path = parse_http_request_url(url)
        if host_overwrite:
            host = host_overwrite
        if isinstance(path_overwrite, str):
            path = path_overwrite
        connection = http_client.HTTPSConnection(host)
        connection.request("GET", path, headers={'Content-Type': 'application/json; charset=UTF-8',
                                                 'User-Agent': 'packaage_updater'})
        response = connection.getresponse()
        connection.close()
        return response
    except Exception as e:
        logger.warning(f'Unable to retrieve response. Issue: {e}')


def read_url_content(url):
    """
    Reads the content of a URL and returns it as a decoded UTF-8 string.

    Args:
        url (str): The URL to read the content from.

    Returns:
        str or None: The content of the URL as a UTF-8 string if the URL was opened successfully,
                     None if there was an error.
    """
    try:
        with urllib.request.urlopen(url) as response:
            if response.getcode() == 200:
                return response.read().decode('utf-8')
            else:
                logger.warning(f"Failed to open URL. Status code: {response.getcode()}")
    except urllib.error.URLError as e:
        logger.warning(f"Unable to read URL content. Issue: {e}")
    return None


def open_url_in_browser(url):
    """
    Opens a URL in a web browser, preferably in a new tab.

    Args:
        url (str): The URL to open in the web browser.
    """
    try:
        webbrowser.open(url, new=2)  # Opens in a new tab if possible
    except Exception as e:
        logger.warning(f"An error occurred when opening URL in browser: {e}")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
