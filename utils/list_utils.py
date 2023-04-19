import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("list_utils")
logger.setLevel(logging.INFO)


def get_list_intersection(list_a, list_b):
    """
    Converts lists into sets and returns the intersection of the sets
    Args:
        list_a (list):
        list_b (list):
    Returns:
        intersection
    """
    set_a = set(list_a)
    set_b = set(list_b)
    return list(set_a.intersection(set_b))


def get_list_difference(list_a, list_b):
    """
    Convert lists into sets and extra their difference
    Args:
        list_a: First list to extract difference
        list_b: Second list to extract difference
    Returns:
        tuple: difference_a (against b), difference_b (against a)
    """
    set_a = set(list_a)
    set_b = set(list_b)
    return list(set_a.difference(set_b)), list(set_b.difference(set_a))


def get_list_missing_elements(expected_list, result_list):
    """
    Args:
        expected_list (list):
        result_list (list):
    Returns:
        difference  list
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
    

def remove_numbers(string):
    """
    Removes all numbers (digits) from the provided string

    Args:
        string (string): input string (numbers will be removed from it)

    Returns:
        string (string): output string without numbers (digits)

    """
    return ''.join([i for i in string if not i.isdigit()])


def remove_strings_from_string(input_string, undesired_string_list):
    """
    Removes provided strings from input
    Args:
        input_string: String to be modified. E.g. "left_elbow_ctrl"
        undesired_string_list (list): A list of strings to be removed. E.g. ['left', 'ctrl'] # Outputs: "_elbow_"

    Returns:
        clean_string (string): The "input_string" after without strings provided in the "undesired_string_list" list
    """
    for undesired in undesired_string_list:
        input_string = input_string.replace(undesired, '')
    return input_string


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
