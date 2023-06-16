"""
 GT Text Curve Generator -> Script used to quickly create text curves
 github.com/TrevisanGMW/gt-tools -  2020-06-09

 1.1 - 2020-06-17
 Changed UI
 Added help menu
 Added icon

 1.2 - 2020-06-27
 Added font option

 1.3 - 2020-11-15
 Tweaked the color and text for the title and help menu

 1.4 to 1.4.1 - 2021-05-12 to 2022-07-11
 Made script compatible with Python 3 (Maya 2022+)
 PEP8 Cleanup
 Added logging
 Added patch to version
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Text to Curve.
    """
    from tools.shape_text_to_curve import shape_text_to_curve
    shape_text_to_curve.build_gui_generate_text_curve()


if __name__ == "__main__":
    launch_tool()
