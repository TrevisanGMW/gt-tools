"""
UUID Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_attr, set_attr
import maya.cmds as cmds
import logging
import random
import string
import uuid
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_uuid(short=False, short_length=8, remove_dashes=False):
    """
    Generate a UUID (Universally Unique Identifier).

    This function generates a UUID using the uuid4 algorithm.
    Optionally, a shorter version of the UUID can be generated using a custom length and a character set consisting
    of lowercase letters and digits.

    Args:
        short (bool): If True, generate a short UUID using a custom character set. (Not guaranteed to be unique)
                      Collision probability:
                      For 10 generated UUIDs, collision probability: 0.0000000000  (length:8)
                      For 1000 generated UUIDs, collision probability: 0.0000001771  (length:8)
                      For 100000 generated UUIDs, collision probability: 0.0017707647  (length:8)
                      For 10 generated UUIDs, collision probability: 0.0000000000  (length:12)
                      For 1000 generated UUIDs, collision probability: 0.0000000000  (length:12)
                      For 100000 generated UUIDs, collision probability: 0.0000000011  (length:12)
        short_length (int): The length of the short UUID. Must be a positive integer.
        remove_dashes (bool, optional): If True, it will remove the dashes from the full UUIDs.

    Returns:
        str: A UUID string.

    Raises:
        ValueError: If short is True and short_length is not a positive integer.

    Examples:
        Normal UUID generation:
        generate_uuid()
        'da55c5a9-8e48-47f1-9bc5-58603d13a7e9'

        Short UUID generation:
        generate_uuid(short=True)
        '0d9a2c68'

        Short UUID generation with custom length:
        generate_uuid(short=True, short_length=6)
        '2e96b4'
    """
    _uuid = str(uuid.uuid4())
    if short and short_length <= 0:
        raise ValueError("Length must be a positive integer")
    if short:
        alphabet = string.ascii_lowercase + string.digits
        _uuid = ''.join(random.choices(alphabet, k=short_length))
    if remove_dashes:
        _uuid = _uuid.replace('-', '')
    return _uuid


def is_uuid_valid(uuid_string):
    """
    Check if a given UUID string is valid.

    Args:
        uuid_string (str): The UUID string to be checked.

    Returns:
        bool: True if the UUID is valid, False otherwise.
    """
    # uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    uuid_pattern = re.compile(r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$")
    return bool(uuid_pattern.match(uuid_string))


def is_short_uuid_valid(uuid_string, length=None):
    """
    Check if a string represents a valid short UUID containing only ASCII lowercase characters and digits.

    Args:
    uuid_string (str): The input string to be checked.
    length (int, optional): If provided, it will also check if the length matches what is expected.

    Returns:
    bool: True if the string is a valid short UUID, False otherwise.
    """
    alphabet = string.ascii_lowercase + string.digits
    valid_characters = set(alphabet)
    if not uuid_string or not isinstance(uuid_string, str) or length is not None and len(uuid_string) != length:
        return False
    return all(c in valid_characters for c in uuid_string)


def get_object_from_uuid_attr(uuid_string, attr_name, obj_type="transform"):
    """
    Return object if provided UUID is present in it
    Args:
        uuid_string (string): UUID to look for (if it matches, then the object is found)
        attr_name (string): Name of the attribute where the UUID is stored.
        obj_type (optional, string): Type of objects to look for (default is "transform")
    Returns:
        str, None: If found, the object with a matching UUID, otherwise None
    """
    obj_list = cmds.ls(typ=obj_type, long=True) or []
    for obj in obj_list:
        if cmds.objExists(f'{obj}.{attr_name}'):
            existing_uuid = cmds.getAttr(f'{obj}.{attr_name}')
            if existing_uuid == uuid_string:
                return obj


def get_uuid(obj_name):
    """
    Get the UUID of a Maya object from its long name.

    Args:
        obj_name (str): The long name of the Maya object.

    Returns:
        str or None: The UUID of the object, or None if the object doesn't exist.
    """
    try:
        # Use the ls command with -uuid flag to get the UUID
        _uuid = cmds.ls(obj_name, uuid=True)[0]
        return _uuid
    except Exception as e:
        logger.debug(f'Unable to get provided object UUID. Issue: {str(e)}')
        return None


def get_object_from_uuid(uuid_string):
    """
    Get the long name of a Maya object from its UUID.

    Args:
        uuid_string (str): The UUID of the Maya object.

    Returns:
        str or None: The long name of the object, or None if the object doesn't exist.
    """
    try:
        # Use the ls command with -l flag to get the long name
        long_name = cmds.ls(uuid_string, long=True)[0]
        return long_name
    except Exception as e:
        logger.debug(f'Unable to get object from UUID. Issue: {str(e)}')
        return None


def add_uuid_attr(obj_list, attr_name, set_initial_uuid_value=True):
    """
    Adds an uuid attribute to a list of objects or a single object.

    This function adds a proxy attribute to each object in the given object list.
    The proxy attribute can be used to store additional information related to the objects.

    Args:
        obj_list (list or str): A list of objects to which the proxy attribute will be added, or an object as a string.
                                If a string is provided, it will be converted into a list containing that object.
        attr_name (str): The name of the proxy attribute to be added to the objects.
        set_initial_uuid_value (bool, optional): Whether to set an initial UUID value for the proxy attribute.
                                                 Default is True. The generated UUID is uuid4 without dashes.

    Returns:
        list: A list of created proxy attribute paths.

    Examples:
        objects = ['object1', 'object2']
        proxy_attrs = add_proxy_attribute(objects, 'proxy_id')
    """
    if not obj_list or not isinstance(obj_list, (list, str)):
        logger.debug(f'Unable to add proxy attribute. Invalid object list : "{str(obj_list)}".')
        return []
    if not attr_name or not isinstance(attr_name, str):
        logger.debug(f'Unable to add proxy attribute. Invalid attribute name : "{str(obj_list)}".')
        return []
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    created_attrs = add_attr(target_list=obj_list, attributes=attr_name, attr_type='string', verbose=False)
    for attr in created_attrs:
        set_attr(attribute_path=attr, value="")
    if set_initial_uuid_value:
        for attr in created_attrs:
            set_attr(attribute_path=attr, value=generate_uuid(remove_dashes=True))
    return created_attrs


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
