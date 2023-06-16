"""
 GT Attributes to Python - Tools for extracting attributes as python code.
 github.com/TrevisanGMW/gt-tools - 2021-12-01

 0.0.2 to 0.0.5 - 2022-03-31 to 2022-07-22
 Re-created script after losing it to hard drive corruption
 Added option to strip zeroes
 Added auto conversion of "-0"s into "0"s for clarity
 Added GUI
 Added logger
 Increased the size of the UI
 Added "Extract User-Defined Attributes" function

 1.0.0 to 1.0.1- 2022-07-26 to 2022-10-06
 Added save to shelf
 Updated help
 Added triple quote to string attributes

 TODO:
    Add options
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Attributes to Python.
    """
    from tools.attributes_to_python import attributes_to_python
    attributes_to_python.build_gui_attr_to_python()


if __name__ == "__main__":
    launch_tool()
