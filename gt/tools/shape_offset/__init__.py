"""
GT Offset Shape - Offsets the CVs of a curve shape
github.com/TrevisanGMW/gt-tools - 2022-03-16

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

0.0.1 - 2022-03-16
Work in progress, core function
"""
# Tool Version
__version_tuple__ = (0, 0, 1)
__version_suffix__ = '-wip'
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Shape Offset.
    """
    from gt.tools.shape_offset import shape_offset
    print("Tool is still a work in progress.")


if __name__ == "__main__":
    launch_tool()
