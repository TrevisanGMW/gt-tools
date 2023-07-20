"""
Version Utilities
"""
from collections import namedtuple
import logging
import sys
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


VERSION_BIGGER = 1
VERSION_SMALLER = -1
VERSION_EQUAL = 0
SemanticVersion = namedtuple("SemanticVersion", ["major", "minor", "patch"])


def parse_semantic_version(version_string):
    """
    Parses semantic version string input into a tuple with major, minor and patch integers.
    Parameters:
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
        major, minor, patch = map(int, version_string.split('.'))
        return SemanticVersion(major=major, minor=minor, patch=patch)
    except ValueError:
        raise ValueError(f'Invalid version format: "{version_string}". Use semantic versioning: e.g. "1.2.3".')


def compare_versions(version_a, version_b):
    """
    Compare two semantic versions and return the comparison result: newer, older or equal?
    Parameters:
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
    Parameters:
        version_current (str): String describing the current version (must be semantic version) e.g. "1.2.3" or "2.14.5"
        version_expected (str): A string describing the expected version (so a comparison can happen
    Returns:
        str: A string describing the comparison result. It can be "unreleased", "outdated" or "current"
    """
    comparison_result = compare_versions(version_current, version_expected)
    if comparison_result == VERSION_BIGGER:
        return "unreleased"
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
        str: Package version as a string. "major.minor.patch"
        e.g. "3.0.0"
    """
    package_dir = package_path
    if package_path and os.path.exists(str(package_path)) is False:
        return "0.0.0"
    if package_path is None:
        utils_dir = os.path.dirname(__file__)
        package_dir = os.path.dirname(utils_dir)
    package_basename = os.path.basename(package_dir)
    package_parent_dir = os.path.dirname(package_dir)
    # Ensure package parent path is available
    if package_parent_dir not in sys.path:
        sys.path.append(package_parent_dir)
    try:
        imported_package = __import__(package_basename)
        return imported_package.__version__
    except Exception as e:
        logger.debug(f"Unable to retrieve current version. Issue: {str(e)}")
        return "0.0.0"


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    # out = get_comparison_feedback("1.6.7", "1.6.7")
    out = get_package_version()
    pprint(out)

