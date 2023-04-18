"""
Data Utilities
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
"""
import logging
import json

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("data_utils")
logger.setLevel(logging.INFO)


def write_json(path, data):
    """
    Writes a JSON file using the provided dictionary as data
    Args:
        path (string): Path to save the file. e.g. "C:/my_file.json" (Must be accessible)
        data (dict): A python dictionary to be converted into JSON data.
    Returns:
        Path if successful, None if it failed
    """
    try:
        json_data = json.dumps(data, indent=4)
        with open(path, "w") as json_file:
            json_file.write(json_data)
        return path
    except Exception as e:
        logger.warning(e)
        return


def read_json_dict(path):
    """
    Reads JSON file assuming that it will find a dictionary pattern in it.
    Converts read information to a dictionary and returns it.
    Returns:
        Dictionary with the content of the JSON file (None in case it failed to read)
    """
    try:
        with open(f'{path}', 'r') as json_file:
            json_as_dict = json.load(json_file)
        return json_as_dict
    except Exception as e:
        logger.warning(e)
        return
