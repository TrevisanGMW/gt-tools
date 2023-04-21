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
    test_utils.test_session_utils,
    test_utils.test_string_utils,
]


def get_test_suites_from_modules(modules):
    all_suites = []
    for module in modules:
        all_suites.append(unittest.TestLoader().loadTestsFromModule(module))
    return all_suites


def run_test_modules(module_list):
    _results = []
    for suite in get_test_suites_from_modules(module_list):
        _results.append(unittest.TextTestRunner(verbosity=1).run(suite))
    return _results


def extract_file_from_failure(failure_message):
    """
    Formats the failure message string into simpler string that contains the filename and line number
    Args:
        failure_message (string): The failure_message string which includes traceback for finding where the tests failed
    Returns:
        String with the file and line number
    """
    find_file_regex = "(?=File).+(?<=, line).+"
    result = re.findall(find_file_regex, failure_message)
    return result[0]


def run_all_tests_with_summary():
    """
    Runs all the unit tests found in the "modules_to_test" and generates a report
    """
    ran = 0
    failed = 0
    module_failures = []
    for name, result in zip(modules_to_test, run_test_modules(modules_to_test)):
        ran += result.testsRun
        failed += len(result.failures)
        if len(result.failures) > 0:
            module_failures.append(result.failures[0])

    width = 100
    print("\n|" + "*"*width)
    print(f"|   Test Runner Summary:")
    print(f"|   Ran       {ran}\n"
          f"|   Failed    {failed}")

    # Append list of failures
    if len(module_failures) > 0:
        print("|" + "-"*width)
        for module in module_failures:
            print(f"|  - {extract_file_from_failure(module[1])}")

    print("|" + "*"*width)


if __name__ == "__main__":
    run_all_tests_with_summary()
