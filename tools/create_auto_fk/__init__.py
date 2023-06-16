"""
 GT Auto FK - Creates FK controls and move them to expected hierarchy.
 github.com/TrevisanGMW/gt-tools - 2020-01-03

 1.2 - 2020-05-10
 Fixed an issue where not using a suffix wouldn't build the hierarchy.

 1.3 - 2020-06-06
 Added CtrlGrp, Ctrl, Jnt suffix text fields.
 Removed joint length button.
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)

 1.4 - 2020-06-17
 Added help button
 Changed GUI
 Added radius option
 Added icon
 Fixed offset bug on custom python curve

 1.5 - 2020-08-06
 Added persistent settings
 Fixed minor bugs
 Added a better error handling system
 Changed settings management to a dictionary
 Made the color for the custom curve button update when used

 1.6 - 2020-08-24
 Added undo chunk for main fk portion

 1.7 - 2020-11-15
 Tweaked the color and text for the title and help menu

 1.8 - 2021-05-11
 Made script compatible with Python 3 (Maya 2022+)

 1.9.0 to 1.9.2 - 2022-06-27 to 2022-06-29
 Added cube as an option for the custom curve dialog
 Replace "Tag" with "Suffix" for the UI text
 A bit of clean up in the code
 Added logger
 Added pin as an option for the custom curve dialog
 Small clean up to the code and docs
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Create Auto FK.
    """
    from tools.create_auto_fk import create_auto_fk
    create_auto_fk.build_gui_auto_fk()


if __name__ == "__main__":
    launch_tool()
