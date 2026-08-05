"""
 Transfer UVs - Script for exporting/importing or transferring UVs
 github.com/TrevisanGMW - 2021-06-22
 Tested on Maya 2020.4 - Windows 10

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 3, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Transfer UVs.
    """
    from gt.tools.transfer_uvs import transfer_uvs
    transfer_uvs.script_version = __version__
    transfer_uvs.build_gui_uv_transfer()


if __name__ == "__main__":
    launch_tool()
