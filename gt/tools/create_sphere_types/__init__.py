"""
 GT Sphere Types - Sphere Types is a simple reminder for Modeling students that they don't need to only use the
 standard sphere for everything.
 github.com/TrevisanGMW/gt-tools -  2020-11-04
 Tested on Maya 2020 - Windows 10

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-11-22
 Minor changes to the UI

 1.2 - 2020-12-03
 Platonic Sphere A is now created with soft normals

 1.3 - 2021-01-25
 Adjusted the size of the spacing between buttons

 1.3.1 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.3.2 - 2021-06-22
 Fixed a little inconsistency on the size of the window

 1.3.3 - 2022-07-10
 PEP8 Cleanup

 To do:
 Improve generated window to give better feedback
 Add more sphere options
 Add sliders to control subdivision level
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Sphere Types.
    """
    from gt.tools.create_sphere_types import create_sphere_types
    create_sphere_types.build_gui_sphere_type()


if __name__ == "__main__":
    launch_tool()
