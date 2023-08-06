"""
 GT Check for Updates - This script compares your current GT Tools version with the latest release.
 github.com/TrevisanGMW/gt-tools - 2020-11-10

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-11-11
 Fixed a few issues with the color of the UI.
 Updated link to show only latest release.
 The "Update" button now is disabled after refreshing.

 1.2 - 2020-11-13
 Added code to try to retrieve the three latest releases

 1.3 - 2020-11-15
 Changed title background color to grey
 Added dates to changelog

 1.4 - 2020-12-04
 Added a text for when the version is higher than expected (Unreleased Version)
 Added an auto check for updates so user's don't forget to update
 Added threading support (so the http request doesn't slow things down)

 1.5 - 2021-05-11
 Made script compatible with Python 3 (Maya 2022+)

 1.6 - 2021-10-21
 Updated parsing mechanism to be fully compatible with semantic versioning
 Updated the silent update checker

 1.7.0 to 1.7.1 - 2022-07-07 to 2022-10-27
 PEP8 Cleanup
 Added patch to version
 Changed a few variable names
 Added output message for when changing auto check or interval values
 Fixed an issue where it wouldn't be able to make an HTTP request on Maya 2023+
"""
# Tool Version
__version_tuple__ = (1, 7, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Check for Updates.
    """
    from gt.tools.package_updater import package_updater_legacy
    package_updater_legacy.script_version = __version__
    package_updater_legacy.build_gui_check_for_updates()


if __name__ == "__main__":
    launch_tool()
