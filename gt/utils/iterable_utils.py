"""
Iterable Utilities - Utilities used for dealing with iterable elements, such as lists, sets and dictionaries
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.string_utils import extract_digits_as_int
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


def format_dict_with_keys_per_line(input_dict, keys_per_line=2, bracket_new_line=False):
    """
    Format a dictionary with a specified number of keys per line.

    Args:
        input_dict (dict): The dictionary to be formatted.
        keys_per_line (int, optional): The number of keys to include per line. Default is 2.
        bracket_new_line (bool, optional): If active, it adds a new line after the first bracket and
                                               before the last. e.g. "{\n"key":"value"\n}
    Returns:
        str: The formatted dictionary as a string.

    Example:
        sample_dict = {
            'name': 'John Doe',
            'age': 30,
            'city': 'New York',
            'email': 'john@example.com',
            'occupation': 'Software Engineer'
        }
        keys_per_line = 2
        formatted_dict = format_dict_with_keys_per_line(sample_dict, keys_per_line)
        print(formatted_dict)
        {
            "name": "John Doe", "age": 30,
            "city": "New York", "email": "john@example.com",
            "occupation": "Software Engineer"
        }
    """
    formatted_lines = []
    keys = list(input_dict.keys())

    for i in range(0, len(keys), keys_per_line):
        line_keys = keys[i:i + keys_per_line]
        line_entries = []
        for key in line_keys:
            value = input_dict[key]
            if isinstance(value, str):
                line_entries.append(f'"{key}": "{value}"')
            else:
                line_entries.append(f'"{key}": {repr(value)}')
        formatted_lines.append(", ".join(line_entries))

    _bracket_new_line = ""
    if bracket_new_line:
        _bracket_new_line = "\n"
    return "{" + _bracket_new_line + ",\n".join(formatted_lines) + _bracket_new_line + "}"


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


def round_numbers_in_list(input_list, num_digits=3):
    """
    Rounds all numbers found in a list to the specified number of digits.

    Args:
        input_list (list): List containing numbers.
        num_digits (int, optional): Number of digits to round to. Default is 0.

    Returns:
        list: A new list with all numbers rounded to the specified number of digits.
    """
    rounded_list = [round(x, num_digits) if isinstance(x, (int, float)) else x for x in input_list]
    return rounded_list


def get_highest_int_from_str_list(str_list):
    """
    Extract the highest digit from strings that follow the pattern 'proxy' followed by any number of digits.

    Args:
        str_list (list): A list of input strings.

    Returns:
        int: The highest digit found in the matching items or 0 if no matching items are found.
    """
    digits_list = [extract_digits_as_int(item) for item in str_list]
    return max(digits_list, default=0)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
