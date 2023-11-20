"""
Iterable Utilities - Utilities used for dealing with iterable elements, such as lists, sets and dictionaries
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.string_utils import extract_digits_as_int
import logging
import pprint

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


def compare_identical_dict_values_types(dict1, dict2, allow_none=False):
    """
    Compare the types of values in two dictionaries.

    Args:
        dict1 (dict): The first dictionary.
        dict2 (dict): The second dictionary.
        allow_none (bool, optional): If True, this function will consider None a valid type
                                     when comparing with other types.
                                     e.g. "int" compared with "None" = Ok

    Returns:
        bool: True if all corresponding values have the same type, False otherwise.
    """
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())
    if keys1 != keys2:
        return False
    for key in keys1:
        if (dict1[key] is None or dict2[key] is None) and allow_none:
            continue
        if type(dict1[key]) != type(dict2[key]):
            return False
    return True


def dict_as_formatted_str(input_dict, indent=1, width=80, depth=None,
                          format_braces=True, one_key_per_line=False):
    """
    Convert a dictionary to a formatted string.

    Args:
    input_dict (dict): The dictionary to be formatted.
    indent (int, optional): Number of spaces for indentation (default is 1).
    width (int, optional): Width of the formatted string (default is 80).
    depth (int or None): The maximum depth to pretty-print nested structures.
            If None, there is no limit (default is None).
    format_braces (bool, optional): If True, format braces on separate lines (default is True).
    one_key_per_line (bool, optional): If True, it will enforce one key and one value per line (top level only)

    Returns:
      str: The formatted string representation of the dictionary.
    """
    formatted_dict = pprint.pformat(input_dict, indent=indent, width=width, depth=depth)
    if one_key_per_line:
        formatted_dict = "{"
        for index, (key, value) in enumerate(input_dict.items()):
            _key_dict = {key: value}
            try:
                _formatted_line = pprint.pformat(_key_dict, width=width, depth=depth, sort_dicts=False)
            except Exception as e:
                logger.debug(f'Unsupported kwarg called. Attempting with older version definition: {e}')
                _formatted_line = pprint.pformat(_key_dict, width=width, depth=depth)  # Older Python Versions
            formatted_dict += _formatted_line[1:-1]
            if index != len(input_dict) - 1:
                formatted_dict += ",\n "
        formatted_dict += "}"

    if formatted_dict.startswith("{") and formatted_dict.endswith("}") and format_braces:
        start_index = formatted_dict.find("{") + 1
        end_index = formatted_dict.rfind("}")

        formatted_result = (
                formatted_dict[:start_index] + "\n " +
                formatted_dict[start_index:end_index] + "\n" +
                formatted_dict[end_index:]
        )
        return formatted_result
    else:
        return formatted_dict


def sort_dict_by_keys(input_dict):
    """
    Sorts a dictionary based on its keys.
    Args:
        input_dict (dict): The input dictionary to be sorted.
    Returns:
        dict: A new dictionary sorted by keys.
    """
    sorted_dict = {k: v for k, v in sorted(input_dict.items(), key=lambda item: str(item[0]))}
    return sorted_dict


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
    print(dict_as_formatted_str({}))
