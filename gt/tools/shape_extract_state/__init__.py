"""
 GT Extract Shape State - Outputs the python code containing the current shape data for the selected curves
 github.com/TrevisanGMW/gt-tools - 2021-10-01

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.0.0 - 2021-10-01
 Initial Release

 1.1.0 - 2022-03-16
 Added GUI and checks
 Added option to print or just return it

 1.2.0 to 1.2.2 - 2022-07-14 to 2022-07-26
 Added GUI
 Added logger
 Increased the size of the main window
 Added save to shelf
 Updated help
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Extract Curve State.
    """
    from gt.tools.shape_extract_state import shape_extract_state
    shape_extract_state.build_gui_curve_shape_state()


if __name__ == "__main__":
    launch_tool()
