"""
String Utilities - Utilities used for dealing with strings
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("string_utils")
logger.setLevel(logging.DEBUG)


def remove_string_prefix(input_string, prefix):
    """
    Removes prefix from a string (if found). It only removes in case it's a prefix.
    This function does NOT use replace
    Args:
        input_string (str): Input to remove prefix from
        prefix (str): Prefix to remove (only if found)

    Returns:
        str: String without prefix (if prefix was found)
    """
    if input_string.startswith(prefix):
        return input_string[len(prefix):]
    return input_string


def remove_string_suffix(input_string, suffix):
    """
    Removes suffix from a string (if found). It only removes in case it's a suffix.
    This function does NOT use replace
    Args:
        input_string (str): Input to remove prefix from
        suffix (str): Suffix to remove (only if found)

    Returns:
        str: String without prefix (if prefix was found)
    """
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string


def string_list_to_snake_case(string_list, separating_string="_", force_lowercase=True):
    """
    Merges strings from a list of strings into one single string separating the strings with a character
    Args:
        string_list (list): A list of strings with combined words
        separating_string (optional, str): String used to separate words. (Default: "_")
        force_lowercase (optional, bool): If it should force all words to be lowercase (default: True)

    Returns:
        str: Combined string: e.g. "camelCase" becomes "camel_case"
    """
    if not string_list:
        return ""
    result_string = ""
    for index in range(len(string_list)):
        if force_lowercase:
            result_string += string_list[index].lower()
        else:
            result_string += string_list[index]
        if index != len(string_list) - 1:  # Last word doesn't need separating string
            result_string += separating_string
    return result_string


def camel_case_to_snake_case(camel_case_string):
    """
    Uses "string_list_to_snake_case" and "camel_case_split" to convert camelCase to snake_case
    Args:
        camel_case_string (str): camelCase string to be converted to snake_case
    Returns:
        str: camelCase convert to snake_case (string, lowercase)
    """
    return string_list_to_snake_case(camel_case_split(camel_case_string))


def camel_case_split(input_string):
    """
    Splits camelCase strings into a list of words
    Args:
        input_string (str): camel case string to be separated into a
    Returns:
        list: A list with words
    """
    words = [[input_string[0]]]

    for char in input_string[1:]:
        if words[-1][-1].islower() and char.isupper():
            words.append(list(char))
        else:
            words[-1].append(char)

    return [''.join(word) for word in words]


def remove_digits(input_string):
    """
    Removes all numbers (digits) from the provided string

    Args:
        input_string (str): input string (numbers will be removed from it)

    Returns:
        str: output string without numbers (digits)

    """
    return ''.join([i for i in input_string if not i.isdigit()])


def remove_strings_from_string(input_string, undesired_string_list):
    """
    Removes provided strings from input
    Args:
        input_string (str): String to be modified. E.g. "left_elbow_ctrl"
        undesired_string_list (list): A list of strings to be removed. E.g. ['left', 'ctrl'] # Outputs: "_elbow_"

    Returns:
        str: The "input_string" after without strings provided in the "undesired_string_list" list
    """
    for undesired in undesired_string_list:
        input_string = input_string.replace(undesired, '')
    return input_string


if __name__ == "__main__":
    from pprint import pprint
    out = None
    pprint(out)
