"""
Tests module
"""
import test_utils
import unittest
import logging
import sys
import os

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
    test_utils.test_session_utils,
    test_utils.test_alembic_utils,
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


def run_all_tests():
    for name, result in zip(modules_to_test, run_test_modules(modules_to_test)):
        print(f"For {name}\n  - Ran   :{result.testsRun}\n  - Failed:{len(result.failures)}")
        for _failure in result.failures:
            print(f"      - {_failure[0]}")


if __name__ == "__main__":
    run_all_tests()
