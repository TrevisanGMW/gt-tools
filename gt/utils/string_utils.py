"""
String Utilities - Utilities used for dealing with strings
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def remove_prefix(input_string, prefix):
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


def remove_suffix(input_string, suffix):
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


def camel_to_snake(camel_case_string):
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


def remove_strings_from_string(input_string, undesired_string_list, only_prefix=False, only_suffix=False):
    """
    Removes provided strings from input
    Args:
        input_string (str): String to be modified. E.g. "left_elbow_ctrl"
        undesired_string_list (list): A list of strings to be removed. E.g. ['left', 'ctrl'] # Outputs: "_elbow_"
        only_prefix (bool, optional): If active, it will only remove strings in case they are found at the beginning
                                      of the input string.  - e.g. "one_two" with ["one'] would become "_two",
                                      while if processed with ["two"] the output would not change: "one_two"
        only_suffix (bool, optional): If active, it will only remove strings in case they are found at the end of the
                                      input string.  - e.g. "one_two" with ["two'] would become "one_",
                                      while if processed with ["one"] the output would not change: "one_two"

    Raises:
        ValueError: If both `only_prefix` and `only_suffix` are set to True.

    Returns:
        str: The "input_string" after without strings provided in the "undesired_string_list" list
    """
    # for undesired in undesired_string_list:
    #     input_string = input_string.replace(undesired, '')
    # return input_string
    if only_prefix and only_suffix:
        raise ValueError('"only_prefix" and "only_suffix" cannot both be True. Please choose one or the other.')

    for undesired in undesired_string_list:
        if only_prefix:
            if input_string.startswith(undesired):
                input_string = input_string[len(undesired):]
        elif only_suffix:
            if input_string.endswith(undesired):
                input_string = input_string[:-len(undesired)]
        else:
            input_string = input_string.replace(undesired, '')

    return input_string


def snake_to_camel(snake_case_str):
    """
    Converts a string from snake_case to camelCase.

    Snake case is a convention where words are separated by underscores, e.g., "hello_world".
    Camel case is a convention where words are joined together, and each word starts with a capital letter except the first one, e.g., "helloWorld".

    Parameters:
        snake_case_str (str): The input string in snake_case format.

    Returns:
        str: The converted string in camelCase format.

    Example:
        snake_to_camel("hello_world")
        # Output: "helloWorld"

        snake_to_camel("my_variable_name")
        # Output: "myVariableName"

        snake_to_camel("python_is_awesome")
        # Output: "pythonIsAwesome"
    """
    words = snake_case_str.split('_')
    camel_case_str = words[0] + ''.join(word.capitalize() for word in words[1:])
    return camel_case_str


def extract_digits(input_string, can_be_negative=False):
    """
    Extracts and returns only the digits from a given input string.

    Args:
        input_string (str): The input string from which digits will be extracted.
        can_be_negative (bool, optional): If True, it will also extract negative numbers by
                                          keeping any negative "-" symbols in front of the number.

    Returns:
        str: A string containing only the extracted digits.

    Examples:
        input_string = "Hello, my phone number is +1 (123) 456-7890."
        result = extract_digits(input_string)
        print(result)
        # Output: '11234567890'
    """
    pattern = r'\d+'
    if can_be_negative:
        pattern = r'-?\d+'
    digits_list = re.findall(pattern, input_string)
    return ''.join(digits_list)


def extract_digits_as_int(input_string, only_first_match=True, can_be_negative=False, default=0):
    """
    Extract digits from a string or return default if no digits are found.

    Args:
        input_string (str): The input string.
        only_first_match (bool, optional): If True, only the first found digit is used.
                                           If False, it might combine numbers in an unexpected way.
                                           e.g. "1_word_2" would return 12.
        can_be_negative (bool, optional): If True, it will also extract negative numbers.
        default (int, optional): If provided, this is used when no digits are found in the "input_string"

    Returns:
        int: Extracted digits or "default" (0) if no digits are found. - Default can be defined as an argument.
    """
    pattern = r'\d+'
    if can_be_negative:
        pattern = r'-?\d+'
    if only_first_match:
        match = re.search(pattern, input_string)
        return int(match.group()) if match else default
    else:
        extracted_digits = extract_digits(input_string, can_be_negative=can_be_negative)
        result = int(extracted_digits) if extracted_digits else default
        return result


if __name__ == "__main__":
    from pprint import pprint
    out = None
    pprint(out)
