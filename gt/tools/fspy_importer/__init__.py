"""
 GT fSpy Importer - Imports a JSON file exported out of fSpy
 github.com/TrevisanGMW/gt-tools -  2020-12-10

 0.1 - 2020-12-10
 Created main function
 Added focal length calculation

 1.0 - 2020-12-11
 Initial Release
 Added GUI
 Added Sanity Checks

 1.1 to 1.1.1 - 2021-05-12 to 2021-07-21
 Made script compatible with Python 3 (Maya 2022+)
 PEP8 Update
 Added patch to version
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT fSpy Importer.
    """
    from gt.tools.fspy_importer import fspy_importer
    fspy_importer.build_gui_fspy_importer()


if __name__ == "__main__":
    launch_tool()