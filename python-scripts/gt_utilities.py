"""
 GT Utilities - Helpful general functions
 github.com/TrevisanGMW - 2022-01-04

"""

def _make_flat_list(*args):
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
                _flat.extend(_make_flat_list(_item))
        else:
            _flat.append(_arg)
    return _flat
