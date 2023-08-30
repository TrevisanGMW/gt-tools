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


def http_get_request(url, timeout_ms=2000, host_overwrite=None, path_overwrite=None):
    """
    Make an HTTP GET request to a REST API and return the response.

    Args:
        url (str): Rest API
        timeout_ms (int): Timeout for the request in milliseconds. Default is 2000 milliseconds (2 seconds).
        host_overwrite (str): String for the host overwrite. For example: "api.github.com"
                              If provided, it will replace whatever was parsed out of the URL. Default None (do nothing)
        path_overwrite (str): String for the path overwrite. For example: "/repos/**USER**/**REPO**/releases/latest"
                              If provided, it will replace whatever was parsed out of the URL. Default None (do nothing)

    Returns:
        tuple: A tuple with (HTTPResponse, response content)
               1: http.client.HTTPResponse object. Use examples:
                "response.status" for response status (e.g. 200)
                "response.reason" for response reason (e.g. "OK")
               2: response content is the output of the HTTPResponse.read() operation.
                 It's retrieved during the function execution because the connection is closed after retrieving it.
    """
    try:
        host, path = parse_http_request_url(url)
        if host_overwrite:
            host = host_overwrite
        if isinstance(path_overwrite, str):
            path = path_overwrite
        timeout_sec = timeout_ms / 1000  # Convert milliseconds to seconds
        connection = http_client.HTTPSConnection(host, timeout=timeout_sec)
        connection.request("GET", path, headers={'Content-Type': 'application/json; charset=UTF-8',
                                                 'User-Agent': 'packaage_updater'})
        response = connection.getresponse()
        response_content = None
        try:
            response_content = response.read().decode('utf-8')
        except Exception as e:
            logger.debug(f'Failed to read HTTP response. Issue: "{e}".')
        connection.close()
        return response, response_content
    except Exception as e:
        logger.warning(f'Unable to get HTTP response. Issue: {e}')
        return None, None


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


def open_package_docs_url_in_browser():
    """
    Opens the package docs URL in a web browser.
    """
    open_url_in_browser(r"https://github.com/TrevisanGMW/gt-tools/tree/release/docs")


def get_http_response_type(status_code):
    """
    Determine the type of HTTP response based on the status code.

    Args:
        status_code (int): The HTTP status code.

    Returns:
        str: A string indicating the type of HTTP response based on the status code.
            Possible values:
            - "Informational" for status codes in the range 100 - 199
            - "Successful" for status codes in the range 200 - 299
            - "Redirection" for status codes in the range 300 - 399
            - "Client error" for status codes in the range 400 - 499
            - "Server error" for status codes in the range 500 - 599
            - "Unknown response" if the status code does not fall into any of the above ranges.
    """
    if 100 <= status_code < 200:
        return "informational"
    elif 200 <= status_code < 300:
        return "successful"
    elif 300 <= status_code < 400:
        return "redirection"
    elif 400 <= status_code < 500:
        return "client error"
    elif 500 <= status_code < 600:
        return "server error"
    else:
        return "unknown response"


def download_file(url, destination, chunk_size=8192, callback=None):
    """
    Downloads a file from a given URL and saves it to a specified destination.

    Args:
        url (str): The URL of the file to download.
        destination (str): The local path where the downloaded file will be saved.
        chunk_size (int, optional): The size of each download chunk in bytes. Defaults to 8192.
        callback (function, optional): A callback function that accepts a progress value (0-100)
                                       as an argument and can be used to track the download progress. Defaults to None.

    Example usage of the callback function:
        def print_progress(progress):
            print(f"Download progress: {progress:.2f}%")

        download_file(download_link, download_destination, callback=print_progress)
    """
    with urllib.request.urlopen(url) as response, open(destination, 'wb') as file:
        headers = response.info()
        total_size = int(headers.get('Content-Length', 0))
        chunk_size = chunk_size
        downloaded = 0

        while True:
            data = response.read(chunk_size)
            if not data:
                break
            file.write(data)
            downloaded += len(data)
            if total_size > 0 and callback:
                progress = (downloaded / total_size) * 100
                callback(progress)
        if callback:
            callback(100)


def is_connected_to_internet(timeout_ms=1000, server="8.8.8.8", port=53):
    """
    Check if the device is connected to the internet using the provided server and port (default: Google DNS servers).

    Args:
        timeout_ms (int): Timeout value in milliseconds for the connection attempt.
        server (str): The IP address or hostname of the server to check connectivity with.
        port (int): The port number on which to check connectivity.

    Returns:
        bool: True if connected to the internet, False otherwise.
    """
    import socket
    timeout_sec = timeout_ms / 1000.0  # Convert milliseconds to seconds
    try:
        # Create a socket and attempt to connect to Google's DNS server (8.8.8.8) on port 53 (DNS)
        socket.setdefaulttimeout(timeout_sec)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sock.close()
        return True
    except Exception as e:
        logger.debug(f'Unable to connect to "{str(server)}:{str(port)}". Issue: {e}')
        return False


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    print()
    pprint(out)
