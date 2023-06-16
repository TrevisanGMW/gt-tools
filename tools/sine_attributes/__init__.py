"""
 GT Sine Attributes - Create Sine output attributes without using third-party plugins or expressions.
 github.com/TrevisanGMW/gt-tools - 2021-01-25

 1.0 - 2021-01-25
 Initial Release

 1.1 to 1.1.1 - 2021-05-10 to 2021-06-30
 Made script compatible with Python 3 (Maya 2022+)
 Added patch to version
 General cleanup
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Sine Attributes.
    """
    from tools.sine_attributes import sine_attributes
    sine_attributes.build_gui_add_sine_attr()


if __name__ == "__main__":
    launch_tool()
