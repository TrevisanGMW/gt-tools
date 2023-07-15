"""
 Inbetween Generator - Script used to create Inbetween Transforms (An object in-between the hierarchy)
 github.com/TrevisanGMW/gt-tools -  2020-02-04

 1.1 - 2020-02-18
 Added Color Picker

 1.2 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Changed Script Name. (Previously rigLayer Generator)
 Fixed random window widthHeight issue.

 1.3 - 2020-06-16
 Updated UI
 Added icon
 Added help menu

 1.4 - 2020-11-15
 Tweaked the color and text for the title and help menu

 1.5 to 1.5.2 - 2021-05-12 to 2022-07-21
 Made script compatible with Python 3.0 (Maya 2022+)
 Changed default suffix from "_rigLayer" to "_offset"
 PEP8 Cleanup
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Generate Inbetween.
    """
    from gt.tools.generate_inbetween import generate_inbetween
    generate_inbetween.build_gui_generate_inbetween()


if __name__ == "__main__":
    launch_tool()