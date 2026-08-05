"""
 Make IK Stretchy - Solution for making simple IK systems stretchy.
 github.com/TrevisanGMW/gt-tools -  2020-03-13

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 5, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Make IK Stretchy.
    """
    from gt.tools.make_ik_stretchy import make_ik_stretchy
    make_ik_stretchy.script_version = __version__
    make_ik_stretchy.build_gui_make_ik_stretchy()


if __name__ == "__main__":
    launch_tool()
