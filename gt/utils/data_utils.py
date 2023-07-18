"""
Data Utilities - Reading and Writing data (JSONs, TXT, etc..)
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import logging
import json

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

