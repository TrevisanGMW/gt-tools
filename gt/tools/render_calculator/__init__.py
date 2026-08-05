"""
 Render Calculator - Script for calculating the time a render will take
 github.com/TrevisanGMW - 2022-07-18

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 0, 2)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Render Calculator.
    """
    from gt.tools.render_calculator import render_calculator
    render_calculator.script_version = __version__
    render_calculator.build_gui_render_calculator()


if __name__ == "__main__":
    launch_tool()
