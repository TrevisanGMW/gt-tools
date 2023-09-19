"""
Tests module
"""
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

# Import Tests
from tests import test_curve_library
from tests import test_package_updater
from tests import test_sample_tool
from tests import test_utils
from tests import test_ui

# Modules to Test
modules_to_test = [
    # Ui
    test_ui.test_input_window_text,
    test_ui.test_line_text_widget,
    test_ui.test_maya_menu,
    test_ui.test_progress_bar,
    test_ui.test_python_output_view,
    test_ui.test_qt_utils,
    test_ui.test_resource_library,
    # Tools
    test_curve_library.test_curve_library_model,
    test_package_updater.test_package_updater_model,
    test_sample_tool.test_sample_tool_model,
    # Utils
    test_utils.test_alembic_utils,
    test_utils.test_anim_utils,
    test_utils.test_attr_utils,
    test_utils.test_color_utils,
    test_utils.test_camera_utils,
    test_utils.test_cleanup_utils,
    test_utils.test_constraint_utils,
    test_utils.test_control_data,
    test_utils.test_control_utils,
    test_utils.test_curve_utils,
    test_utils.test_data_utils,
    test_utils.test_display_utils,
    test_utils.test_feedback_utils,
    test_utils.test_iterable_utils,
    test_utils.test_math_utils,
    test_utils.test_namespace_utils,
    test_utils.test_naming_utils,
    test_utils.test_playblast_utils,
    test_utils.test_prefs_utils,
    test_utils.test_proxy_utils,
    test_utils.test_request_utils,
    test_utils.test_scene_utils,
    test_utils.test_session_utils,
    test_utils.test_setup_utils,
    test_utils.test_skin_utils,
    test_utils.test_string_utils,
    test_utils.test_system_utils,
    test_utils.test_transform_utils,
    test_utils.test_uuid_utils,
    test_utils.test_version_utils,
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


def regex_file_from_failure_or_error(message):
    """
    Formats the failure or error message string into simpler string that contains the filename and line number
    Args:
        message (string): The failure/error message string which includes traceback for finding where the tests failed.
    Returns:
        String with the file, line number and test name.
        In case operation fails, the entire failure/error message is returned instead.
    """
    find_file_regex = "(?=File).+(?<=, line).+"  # Keep only file line
    result = re.findall(find_file_regex, message)
    if result:
        return result[0]
    else:
        return str(message)


def run_all_tests_with_summary(print_results=True, print_traceback=False):
    """
    Runs all the unit tests found in the "modules_to_test" and generates a report
    Args:
        print_results (bool, optional): If active it prints the results
        print_traceback (bool, optional): If active, it will print traceback details of any errors/failures.
    Returns:
        str: Results in a Markdown table format
    """
    ran_counter = 0
    failed_counter = 0
    errors_counter = 0
    module_failures = {}
    module_errors = {}
    errors = []
    failures = []
    for name, result in zip(modules_to_test, run_test_modules(modules_to_test)):
        ran_counter += result.testsRun
        failed_counter += len(result.failures)
        errors_counter += len(result.errors)
        errors += result.errors
        failures += result.failures
        if len(result.failures) > 0:
            module = regex_module_name(name)
            first_failure = result.failures[0][1]
            module_failures[module] = regex_file_from_failure_or_error(first_failure)
        if len(result.errors) > 0:
            module = regex_module_name(name)
            first_error = result.errors[0][1]
            module_errors[module] = regex_file_from_failure_or_error(first_error)

    tests_summary = {"Test Runner Summary": ["Ran", "Failed"],
                     "": [ran_counter, failed_counter]}
    if errors_counter:
        tests_summary.get("Test Runner Summary").append("Errors")
        tests_summary.get("").append(str(errors_counter))

    output_string = "\n"
    output_string += dict_to_markdown_table(tests_summary)

    # Add failures
    if len(module_failures) > 0:
        modules = list(module_failures.keys())
        files = list(module_failures.values())
        module_failures = {"Failures": modules,
                           "Source": files}
        output_string += "\n" + dict_to_markdown_table(module_failures)
    if len(module_errors) > 0:
        modules = list(module_errors.keys())
        files = list(module_errors.values())
        module_errors = {"Errors": modules,
                         "Source": files}
        output_string += "\n" + dict_to_markdown_table(module_errors)

    if print_traceback and (errors or failures):
        for index, error in enumerate(errors):
            print(f'\n{"-"*40} Error {str(index+1).zfill(2)}: {"-"*40}')
            print(error[0])
            print(error[1])
        for index, fail in enumerate(failures):
            print(f'\n{"-"*40} Failure {str(index+1).zfill(2)}: {"-"*40}')
            print(fail[0])
            print(fail[1])

    if print_results:
        print(output_string)

    return output_string


if __name__ == "__main__":
    run_all_tests_with_summary(print_results=True, print_traceback=True)
