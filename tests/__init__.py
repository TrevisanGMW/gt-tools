"""
Tests module
"""
import test_utils
import unittest
import logging
import sys
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("tests")
logger.setLevel(logging.INFO)

# Paths to Append
source_dir = os.path.dirname(__file__)
tools_root_dir = os.path.dirname(source_dir)
for to_append in [source_dir, tools_root_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)


# Modules to Test
modules_to_test = [
    test_utils.test_alembic_utils,
    test_utils.test_color_utils,
    test_utils.test_list_utils,
    test_utils.test_namespace_utils,
    test_utils.test_scene_utils,
    test_utils.test_session_utils,
    test_utils.test_string_utils,
]


def get_test_suites_from_modules(module_list):
    """
    Get test suits from list of modules
    Args:
        module_list (list): A list of modules
    Returns:
        a list of test suites
    """
    all_suites = []
    for module in module_list:
        all_suites.append(unittest.TestLoader().loadTestsFromModule(module))
    return all_suites


def run_test_modules(module_list):
    """
    Run provided tests and returns the results
    Args:
        module_list (list): A list of modules
    Returns:
        A list of test results
    """
    results = []
    for suite in get_test_suites_from_modules(module_list):
        results.append(unittest.TextTestRunner(verbosity=1).run(suite))
    return results


def dict_to_markdown_table(dictionary):
    """
    Converts a dictionary to a Markdown table with perfectly aligned columns.

    Args:
        dictionary (dict): The dictionary to convert. Keys are the headers. Values should be lists that become rows.
                          e.g. data = {Name": ["Alice", "Bob", "Charlie"],
                                               "Age": [25, 30, 35],
                                               "Gender": ["Female", "Male", "Male"],
                                      }
                          In case the value is a not a list, it will be automatically converted (put into) a list
    Returns:
        str: The Markdown table string
    """
    for key, value in dictionary.items():  # Enforces that value is a list, so it doesn't choke with len()
        if not isinstance(value, list):
            dictionary[key] = [value]
    headers = list(dictionary.keys())  # Determine the column headers
    num_rows = max(len(dictionary[key]) for key in dictionary)  # Determine the number of rows
    rows = [[] for _ in range(num_rows)]  # Create a list of lists to hold the dictionary
    for key in headers:  # Populate the rows list with the dictionary
        values = dictionary[key]
        for i in range(num_rows):
            if i < len(values):
                rows[i].append(str(values[i]))
            else:
                rows[i].append("")

    # Determine the maximum width of each column
    col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]

    # Create the Markdown table
    md_table = "| " + " | ".join([header.ljust(col_widths[i]) for i, header in enumerate(headers)]) + " |\n"
    md_table += "|-" + "-|-".join(["-" * col_widths[i] for i in range(len(headers))]) + "-|\n"
    for row in rows:
        md_table += "| " + " | ".join([str(row[i]).ljust(col_widths[i]) for i in range(len(headers))]) + " |\n"

    return md_table


def regex_module_name(module):
    """
    Args:
        module (module): A module to extract the name
    Returns:
        String without extra module and from portions. In case operation fails, module is returned as a string
        e.g.
        "<module 'test_module.test_module' from 'path'>"   becomes    "test_module.test_module"
    """
    find_file_regex = "(?<=module ').+(?=' from)"  # Ignore "<module " and " from 'path'>"
    result = re.findall(find_file_regex, str(module))
    if result:
        return result[0]
    else:
        return str(module)


def regex_file_from_failure(failure_message):
    """
    Formats the failure message string into simpler string that contains the filename and line number
    Args:
        failure_message (string): The failure_message string which includes traceback for finding where the tests failed
    Returns:
        String with the file, line number and test name.
        In case operation fails, the entire failure message is returned instead.
    """
    find_file_regex = "(?=File).+(?<=, line).+"  # Keep only file line
    result = re.findall(find_file_regex, failure_message)
    if result:
        return result[0]
    else:
        return str(failure_message)


def run_all_tests_with_summary(print_results=True):
    """
    Runs all the unit tests found in the "modules_to_test" and generates a report
    Args:
        print_results (optional, bool): If active it prints the results
    Returns:
        str: Results in a Markdown table format
    """
    ran = 0
    failed = 0
    module_failures = {}
    for name, result in zip(modules_to_test, run_test_modules(modules_to_test)):
        ran += result.testsRun
        failed += len(result.failures)
        if len(result.failures) > 0:
            module = regex_module_name(name)
            first_failure = result.failures[0][1]
            module_failures[module] = regex_file_from_failure(first_failure)

    tests_summary = {"Test Runner Summary": ["Ran", "Failed"],
                     "": [ran, failed]}

    output_string = dict_to_markdown_table(tests_summary)

    # Add failures
    if len(module_failures) > 0:
        modules = list(module_failures.keys())
        files = list(module_failures.values())
        module_failures = {"Failures": modules,
                           "Source": files}
        output_string += "\n" + dict_to_markdown_table(module_failures)
    if print_results:
        print(output_string)
    return output_string


if __name__ == "__main__":
    run_all_tests_with_summary()
