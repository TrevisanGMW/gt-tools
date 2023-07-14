"""
 GT Render Calculator - Script for calculating the time a render will take
 github.com/TrevisanGMW - 2022-07-18

 1.0.0 - 2022-07-20
 Initial release

 1.0.1 - 2022-07-21
 Updated help link
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Render Calculator.
    """
    from gt.tools.render_calculator import render_calculator
    render_calculator.build_gui_render_calculator()


if __name__ == "__main__":
    launch_tool()
