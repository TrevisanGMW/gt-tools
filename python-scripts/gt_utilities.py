"""
 GT Utilities - Helpful general functions
 github.com/TrevisanGMW - 2022-01-04

"""


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
