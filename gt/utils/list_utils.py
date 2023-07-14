"""
List Utilities - Utilities used for dealing with list
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
