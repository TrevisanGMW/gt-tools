"""
Request Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.string_utils import remove_strings_from_string
import http.client as http_client
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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
