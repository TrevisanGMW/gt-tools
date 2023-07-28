"""
Data Utilities - Reading and Writing data (JSONs, TXT, etc..)
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import logging
import stat
import json
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def write_data(path, data):
    """
    Write data to a file.
    This function writes the given data to a file located at the specified path.

    Args:
        path (str): The file path where the data will be written.
                    If a file exists at this path, its content will be overwritten.
        data (str): The data to be written to the file.

    Returns:
        str: The path of the file where the data was written.

    Raises:
        Any exception that might occur during the file writing process will be logged as a warning, and the
        function will return without raising the exception.

    Example:
        write_data("data.txt", "Hello, world!")
        'data.txt'
    """
    try:
        with open(path, "w", encoding="utf-8") as data_file:
            data_file.write(data)
        return path
    except FileNotFoundError as fnf_err:
        logging.warning(f"File not found: {path}")
    except PermissionError as perm_err:
        logging.warning(f"Permission error when writing to: {path}")
    except Exception as e:
        logging.warning(f"An error occurred while writing to {path}: {e}")


def read_data(path):
    """
    Read data from a file.

    This function reads data from a file located at the specified path and returns its content as a string.

    Args:
        path (str): The file path from which the data will be read.

    Returns:
        str: The content of the file as a string.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        IOError: If there is an error reading the file.

    Example:
        data = read_data("data.txt")
        print(data)
        'Hello, world!'
    """
    try:
        with open(path, "r") as data_file:
            data = data_file.read()
        return data
    except FileNotFoundError:
        logger.warning(f"File not found: {path}")
    except IOError as e:
        logger.warning(f"Error reading file: {path}")


def write_json(path, data):
    """
    Writes a JSON file using the provided dictionary as data.

    Args:
        path (str): The file path where the JSON data will be saved.
                    If a file exists at this path, its content will be overwritten.
                    The path must be accessible, and the necessary permissions must be granted.
        data (dict): A Python dictionary to be converted into JSON data.

    Returns:
        str or None: If successful, returns the path where the JSON data was saved.
                     If failed due to an error, returns None.

    Raises:
        FileNotFoundError: If the specified path does not exist.
        PermissionError: If there are permission issues to write to the file.
        ValueError: If the provided data is not a valid Python dictionary.

    Notes:
        - This function converts the provided dictionary 'data' into JSON format and writes it to the file.
        - The function uses 'json.dumps()' with the 'indent' parameter set to 4 for a formatted output.
        - Non-ASCII characters are preserved in the JSON data by setting 'ensure_ascii' to False.

    Example:
        data = {"name": "Terry Fox", "age": 22, "city": "Vancouver"}
        result = write_json("data.json", data)
        if result is not None:
            print(f"JSON data written to: {result}")
    """
    try:
        if not isinstance(data, dict):
            raise ValueError("Data must be a valid Python dictionary.")

        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        with open(path, "w", encoding="utf-8") as json_file:
            json_file.write(json_data)
        return path
    except FileNotFoundError as fnf_err:
        logging.warning(f"Error: The path '{path}' was not found.")
    except PermissionError as perm_err:
        logging.warning(f"Error: Permission denied when writing to '{path}'.")
    except ValueError as ve:
        logging.warning(str(ve))
    except Exception as e:
        logging.warning(f"An error occurred while writing JSON to {path}: {e}")


def read_json_dict(path):
    """
    Reads a JSON file and returns its content as a dictionary.

    Args:
        path (str): The file path of the JSON file to read.

    Returns:
        dict: A dictionary containing the content of the JSON file.
              If the file could not be read or does not contain valid JSON data, an empty dictionary is returned.

    Raises:
        FileNotFoundError: If the specified path does not exist.
        JSONDecodeError: If the file exists but does not contain valid JSON data.

    Example:
        data = read_json_dict("data.json")
        print(data)
        {'name': 'John Doe', 'age': 30, 'city': 'New York'}
    """
    try:
        with open(path, 'r') as json_file:
            json_as_dict = json.load(json_file)
        return json_as_dict
    except FileNotFoundError as fnf_err:
        logging.warning(f"Error: The file '{path}' was not found.")
        return {}
    except json.JSONDecodeError as json_err:
        logging.warning(f"Error: Invalid JSON data in '{path}': {json_err}")
        return {}
    except Exception as e:
        logging.warning(f"An error occurred while reading JSON from {path}: {e}")
        return {}


class PermissionBits:
    def __init__(self):
        """
        A library of Permission Bits
        """
    # User permission bits
    USER_READ = stat.S_IRUSR
    USER_WRITE = stat.S_IWUSR
    USER_EXECUTE = stat.S_IXUSR

    # Group permission bits
    GROUP_READ = stat.S_IRGRP
    GROUP_WRITE = stat.S_IWGRP
    GROUP_EXECUTE = stat.S_IXGRP

    # Others permission bits
    OTHERS_READ = stat.S_IROTH
    OTHERS_WRITE = stat.S_IWOTH
    OTHERS_EXECUTE = stat.S_IXOTH

    # Commonly used combinations
    READ_ONLY = USER_READ | GROUP_READ | OTHERS_READ
    WRITE_ONLY = USER_WRITE | GROUP_WRITE | OTHERS_WRITE
    EXECUTE_ONLY = USER_EXECUTE | GROUP_EXECUTE | OTHERS_EXECUTE
    READ_WRITE = READ_ONLY | WRITE_ONLY
    READ_EXECUTE = READ_ONLY | EXECUTE_ONLY
    WRITE_EXECUTE = WRITE_ONLY | EXECUTE_ONLY
    ALL_PERMISSIONS = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


def set_file_permissions(file_path, permission_bits, keep_current=False):
    """
    Set the file permissions of the given file to the specified permission bits.

    Args:
        file_path (str): The path to the file whose permissions need to be modified.
        permission_bits (int): The permission bits to set for the file. These bits represent
                               the desired permissions in octal format, e.g., 0o755.
                               These can be found in the class "PermissionBits".
        keep_current (bool, optional): If active, current permissions are retained during operation.
                                       Default off

    Raises:
        FileNotFoundError: If the provided file_path does not exist.

    Example:
        set_file_permissions("/path/to/file.txt", 0o644)
        # This will set the file permissions of "file.txt" to read/write for the owner
        # and read-only for the group and others.
        set_file_permissions("/path/to/file.txt", PermissionBits.NO_WRITING)
        # This will set the file permission of "file.txt" to read-only
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    if keep_current:
        current_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
        os.chmod(file_path, current_permissions & permission_bits)
    else:
        os.chmod(file_path, permission_bits)


def set_file_permission_read_only(file_path):
    """
    Remove write permissions from this path, while keeping all other permissions intact.
    Params:
        path:  The path whose permissions to alter.
    """
    set_file_permissions(file_path, PermissionBits.READ_ONLY)


def set_file_permission_modifiable(file_path):
    """
    Remove write permissions from this path, while keeping all other permissions intact.
    Params:
        path:  The path whose permissions to alter.
    """
    set_file_permissions(file_path, PermissionBits.ALL_PERMISSIONS)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    from system_utils import get_desktop_path
    test_file = os.path.join(get_desktop_path(), "test.txt")
    set_file_permissions(test_file, PermissionBits.READ_ONLY)
    pprint(out)
