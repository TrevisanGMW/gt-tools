"""
 GT Startup Booster - A script for managing which plugins get loaded when starting Maya.
 github.com/TrevisanGMW/gt-tools - 2020-11-20

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 to 1.1.1 - 2021-05-12 to 2022-07-11
 Made script compatible with Python 3 (Maya 2022+)
 Added logging
 Added patch to version
 PEP8 Cleanup
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Startup Booster.
    """
    from gt.tools.startup_booster import startup_booster
    startup_booster.build_gui_startup_booster()


if __name__ == "__main__":
    launch_tool()
