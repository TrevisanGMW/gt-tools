"""
Version Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.request_utils import http_request, get_http_response_type
from gt.utils.feedback_utils import print_when_true
from collections import namedtuple
import importlib.util
import logging
import os
import re


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PACKAGE_RELEASE_URL = 'https://api.github.com/repos/TrevisanGMW/gt-tools/releases/latest'
PACKAGE_TAG_RELEASE_URL = 'https://api.github.com/repos/TrevisanGMW/gt-tools/releases/tags/'
VERSION_BIGGER = 1
VERSION_SMALLER = -1
VERSION_EQUAL = 0
SemanticVersion = namedtuple("SemanticVersion", ["major", "minor", "patch"])


def is_semantic_version(version_str, metadata_ok=True):
    """
   Checks if a given string adheres to the semantic versioning pattern.

   Args:
       version_str (str): The version string to be checked.
       metadata_ok (bool, optional): Optionally, it may include build metadata as a suffix,
                                     preceded by a hyphen (e.g., "1.12.3-alpha").

   Returns:
       bool: True if the version string matches the semantic versioning pattern, False otherwise.

   Examples:
       is_semantic_version("1.12.3")  # True
       is_semantic_version("1.2")  # False
       is_semantic_version("1.3.4-alpha", metadata_ok=False)  # False
       is_semantic_version("1.3.4-alpha", metadata_ok=True)  # True
   """

    if metadata_ok:
        pattern = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-]" \
                  r"[0-9a-zA-Z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+" \
                  r"(?:\.[0-9a-zA-Z-]+)*))?$"
    else:
        pattern = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
    return bool(re.match(pattern, str(version_str)))


def parse_semantic_version(version_string):
    """
    Parses semantic version string input into a tuple with major, minor and patch integers.
    Args:
        version_string (str): String describing a version (must be semantic version) e.g. "1.2.3" or "2.14.5"
                                 Only two separating "." are allowed, otherwise it throws a ValueError.
                                 Any extra characters that are not digits will be ignored e.g. "v1.2.3dev" = "1.2.3"
    Returns:
        namedtuple: SemanticVersion: A named tuple with major, minor and patch information for the version.
                    e.g. (1, 2, 3)
                    e.g. (major=1, minor=2, patch=3)
    """
    try:
        version_string = re.sub("[^\d.]", "", version_string)  # Remove non-digits (keeps ".")
        major, minor, patch = map(int, version_string.split('.')[:3])
        return SemanticVersion(major=major, minor=minor, patch=patch)
    except ValueError:
        raise ValueError(f'Invalid version format: "{version_string}". Use semantic versioning: e.g. "1.2.3".')


def compare_versions(version_a, version_b):
    """
    Compare two semantic versions and return the comparison result: newer, older or equal?
    Args:
        version_a (str): String describing a version (must be semantic version) e.g. "1.2.3" or "2.14.5"
        version_b (str): A string describing a version to be compared with version_a
    Returns:
        int: Comparison result
             -1: if older ("a" older than "b")
             0: if equal,
             1: if newer ("a" newer than "b")
    """
    major_a, minor_a, patch_a = parse_semantic_version(version_a)
    major_b, minor_b, patch_b = parse_semantic_version(version_b)

    if major_a > major_b:
        return VERSION_BIGGER
    elif major_a < major_b:
        return VERSION_SMALLER
    elif minor_a > minor_b:
        return VERSION_BIGGER
    elif minor_a < minor_b:
        return VERSION_SMALLER
    elif patch_a > patch_b:
        return VERSION_BIGGER
    elif patch_a < patch_b:
        return VERSION_SMALLER
    else:
        return VERSION_EQUAL


def get_comparison_feedback(version_current, version_expected):
    """
    Compares current version with expected versions and returns a string explaining current status.
    Args:
        version_current (str): String describing the current version (must be semantic version) e.g. "1.2.3" or "2.14.5"
        version_expected (str): A string describing the expected version (so a comparison can happen)
    Returns:
        str: A string describing the comparison result. It can be "unreleased", "outdated", "current" or "unknown"
    """
    if not is_semantic_version(version_current, metadata_ok=False) or \
            not is_semantic_version(version_expected, metadata_ok=False):
        return "unknown"
    comparison_result = compare_versions(version_current, version_expected)
    if comparison_result == VERSION_BIGGER:
        return "updated"
    elif comparison_result == VERSION_SMALLER:
        return "outdated"
    else:
        return "current"


def get_package_version(package_path=None):
    """
    Gets the package version, independently of the package folder name.
    Args:
        package_path (str, optional): If provided, the path will be used to determine the package path.
                                      It assumes that the package is using the same variable name "PACKAGE_VERSION"
    Returns:
        str or None: Package version as a string. "major.minor.patch" e.g. "3.0.0", None if not found.
    """
    package_dir = package_path
    if package_path and not os.path.exists(str(package_path)):
        return
    if package_path is None:
        utils_dir = os.path.dirname(__file__)
        package_dir = os.path.dirname(utils_dir)
    init_path = os.path.join(package_dir, "__init__.py")
    if not os.path.exists(init_path):
        return
    try:
        # Load the module from the specified path
        module_spec = importlib.util.spec_from_file_location('module', init_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module.__version__
    except Exception as e:
        logger.debug(f"Unable to retrieve current version. Issue: {str(e)}")
        return


def get_legacy_package_version():
    """
    Retrieves the legacy version of the package from Maya's optionVar 'gt_tools_version' if it exists and is a valid
    semantic version.

    Returns:
        str or None: The legacy package version as a string if it exists and is a valid semantic version, or None if
        the version is not found or is not a valid semantic version.
    """
    option_var = "gt_tools_version"
    legacy_version = None
    try:
        import maya.cmds as cmds
        legacy_version = cmds.optionVar(query=option_var)
    except Exception as e:
        logger.debug(str(e))
        logger.debug(f'Unable to retrieve legacy version using "cmds". Trying "mel"...')
        try:
            import maya.mel as mel
            legacy_version = mel.eval(f'optionVar -q "{option_var}";')
        except Exception as e:
            logger.debug(str(e))
            logger.debug(f'Unable to retrieve legacy Maya version')
    if legacy_version and is_semantic_version(legacy_version, metadata_ok=False):
        return legacy_version


def get_installed_version(verbose=True):
    """
    Get Installed Package Version
    Args:
        verbose (bool, optional): If active, it will print feedback messages
    Returns:
        str or None: A semantic version string or None if not installed. e.g. "1.2.3"
    """
    from gt.utils.setup_utils import is_legacy_version_install_present, get_installed_core_module_path
    package_core_module = get_installed_core_module_path(only_existing=False)
    if not os.path.exists(package_core_module):
        message = f'Package not installed. Missing path: "{package_core_module}"'
        print_when_true(message, do_print=verbose, use_system_write=True)
        return
    installed_version = get_package_version(package_path=package_core_module)
    if not installed_version and is_legacy_version_install_present():
        installed_version = get_legacy_package_version()
    if installed_version and is_semantic_version(installed_version, metadata_ok=False):
        return installed_version


def get_latest_github_release_version(verbose=True, also_return_response=False):
    response, response_content = http_request(PACKAGE_RELEASE_URL)
    try:
        response_type = get_http_response_type(response.status)
        if response_type != "successful":
            message = f'HTTP response returned unsuccessful status code. ' \
                      f'URL: "{PACKAGE_RELEASE_URL} (Status: "{response.status})'
            print_when_true(message, do_print=verbose, use_system_write=True)
            return
        if not response_content:
            message = f'HTTP requested content is empty or missing. ' \
                      f'URL: "{PACKAGE_RELEASE_URL} (Status: "{response.status})'
            print_when_true(message, do_print=verbose, use_system_write=True)
            return
        from json import loads
        content = loads(response_content)
        return content
    except Exception as e:
        raise e


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    # import maya.standalone
    # maya.standalone.initialize()
    out = None
    out = get_latest_github_release_version()
    pprint(out)
