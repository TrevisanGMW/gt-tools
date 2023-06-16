"""
 GT Check for Updates - This script compares your current GT Tools version with the latest release.
 github.com/TrevisanGMW/gt-tools - 2020-11-10

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

    Debugging Lines:
        # GT Tools Version Query/Overwrite
        cmds.optionVar(q=("gt_tools_version"))
        cmds.optionVar( sv=('gt_tools_version', str("1.2.3")))

        # Remove optionVars
        cmds.optionVar( remove='gt_check_for_updates_last_date' )
        cmds.optionVar( remove='gt_check_for_updates_auto_active' )
        cmds.optionVar( remove='gt_check_for_updates_interval_days' )

        # Set optionVars
        date_time_str = '2020-01-01 17:08:00'
        cmds.optionVar( sv=('gt_check_for_updates_last_date', str(date_time_str)))
        is_active = True
        cmds.optionVar( iv=('gt_check_for_updates_auto_active', int(is_active)))
        how_often_days = 15
        cmds.optionVar( iv=('gt_check_for_updates_interval_days', int(how_often_days)))

        # Query optionVars
        cmds.optionVar(q=("gt_check_for_updates_last_date"))
        cmds.optionVar(q=("gt_check_for_updates_auto_active"))
        cmds.optionVar(q=("gt_check_for_updates_interval_days"))
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Check for Updates.
    """
    from tools.check_for_updates import check_for_updates
    check_for_updates.build_gui_check_for_updates()


if __name__ == "__main__":
    launch_tool()
