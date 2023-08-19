"""
Iterable Utilities - Utilities used for dealing with iterable elements, such as lists, sets and dictionaries
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_list_intersection(list_a, list_b):
    """
    Converts lists into sets and returns the intersection of the sets
    Args:
        list_a (list):
        list_b (list):
    Returns:
        intersection list (sorted)
    """
    set_a = set(list_a)
    set_b = set(list_b)
    return sorted(list(set_a.intersection(set_b)))


def get_list_difference(list_a, list_b):
    """
    Convert lists into sets and extra their difference
    Args:
        list_a: First list to extract difference
        list_b: Second list to extract difference
    Returns:
        tuple: difference_a (against b), difference_b (against a)
        Lists within the tuple are sorted
    """
    set_a = set(list_a)
    set_b = set(list_b)
    return sorted(list(set_a.difference(set_b))), sorted(list(set_b.difference(set_a)))


def get_list_missing_elements(expected_list, result_list):
    """
    Args:
        expected_list (list): Full list - What you would expect to see
        result_list (list): Actual list - List to be compared (the one that might be missing elements)
    Returns:
        difference list
    """
    difference = get_list_difference(expected_list, result_list)[0]
    return difference


def get_next_dict_item(dictionary, key, cycle=False):
    """
    Get the next item in a dictionary after the given key.

    Args:
        dictionary (dict): The dictionary.
        key: The key after which you want to find the next item.
        cycle (bool): If True, enables cycling through the dictionary.

    Returns:
        tuple: A tuple containing the key-value pair of the next item, or None if no next item exists.
    """
    iterator = iter(dictionary)
    try:
        while True:
            current_key = next(iterator)
            if current_key == key:
                next_key = next(iterator, None)
                if next_key is not None:
                    return next_key, dictionary[next_key]
                elif cycle:
                    first_key = next(iter(dictionary))
                    return first_key, dictionary[first_key]
                else:
                    return None
    except StopIteration:
        return None


def compare_identical_dict_keys(dict1, dict2):
    """
    Compare two dictionaries and check if they have exactly the same keys.

    Args:
        dict1 (dict): The first dictionary.
        dict2 (dict): The second dictionary.

    Returns:
        bool: True if both dictionaries have exactly the same keys, False otherwise.
    """
    return set(dict1.keys()) == set(dict2.keys())


def compare_identical_dict_values_types(dict1, dict2):
    """
    Compare the types of values in two dictionaries.

    Args:
        dict1 (dict): The first dictionary.
        dict2 (dict): The second dictionary.

    Returns:
        bool: True if all corresponding values have the same type, False otherwise.
    """
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())
    if keys1 != keys2:
        return False
    for key in keys1:
        if type(dict1[key]) != type(dict2[key]):
            return False
    return True


def remove_list_duplicates(input_list):
    """
    Remove duplicates from a list using a set.

    Args:
        input_list (list): The input list with duplicates.

    Returns:
        list: A new list with duplicates removed.
    """
    return list(set(input_list))


def remove_list_duplicates_ordered(input_list):
    """
    Remove duplicates from a list while preserving the order.

    Args:
        input_list (list): The input list with duplicates.

    Returns:
        list: A new list with duplicates removed and the original order preserved.
    """
    seen = set()
    unique_list = []
    for item in input_list:
        if item not in seen:
            unique_list.append(item)
            seen.add(item)
    return unique_list


def make_flat_list(*args):
    """
    Return a single list of all the items, essentially merging lists and single object into one list.
    Args:
        *args: comma sep list of items and lists of items

    Returns:
        flat item list
    """
    _flat = []
    for _arg in args:
        if isinstance(_arg, str):
            _flat.append(_arg)
        elif hasattr(_arg, '__iter__'):
            for _item in _arg:
                _flat.extend(make_flat_list(_item))
        else:
            _flat.append(_arg)
    return _flat


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    out = None
    pprint(out)
