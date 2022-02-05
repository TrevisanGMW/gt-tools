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

            Parameters:
                string (string): input string (numbers will be removed from it)

            Returns:
                string (string): output string without numbers (digits)

    """
    return ''.join([i for i in string if not i.isdigit()])