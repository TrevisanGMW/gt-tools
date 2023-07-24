"""
 GT Sine Attributes - Create Sine output attributes without using third-party plugins or expressions.
 github.com/TrevisanGMW/gt-tools - 2021-01-25

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.0 - 2021-01-25
 Initial Release

 1.1 to 1.1.1 - 2021-05-10 to 2021-06-30
 Made script compatible with Python 3 (Maya 2022+)
 Added patch to version
 General cleanup
"""
# Tool Version
__version_tuple__ = (1, 1, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Sine Attributes.
    """
    from gt.tools.sine_attributes import sine_attributes
    sine_attributes.script_version = __version__
    sine_attributes.build_gui_add_sine_attr()


if __name__ == "__main__":
    launch_tool()
