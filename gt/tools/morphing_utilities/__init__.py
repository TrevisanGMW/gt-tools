"""
 GT Morphing Utilities
 github.com/TrevisanGMW/gt-tools - 2020-11-15

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 0.0.1 to 0.0.4 - 2022-11-15 to 2022-12-23
 Added "delete_blends_target"
 Added "delete_blends_targets"
 Added "delete_all_blend_targets"
 Created initial GUI
 Added search and replace
 Added window icon

 1.0.0 - 2022-12-23
 Initial release (basic utilities)

 1.0.1 to 1.1.1 - 2023-02-13
 Added "get_target_mesh", "bake_current_state", "set_targets_value"
 Added set all target values button and floatField
 Added Extract Targets at current values button

 1.1.2 to 1.2.1 - 2023-02-21
 Updated duplicate functions and added a few helper functions
 Created add_target function (requires an extracted mesh)
 Renamed search and replace while flipping button

 1.2.2 to 1.3.2 - 2023-02-22
 Fixed an issue where search replace while duplicating and flipping wouldn't work properly
 Added duplicate and mirror function
 Added duplicate and mirror button
 Added operation help buttons
 Added mirror direction and symmetry axis drop-down menus
"""
# Tool Version
__version_tuple__ = (1, 3, 2)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Morphing Utilities.
    """
    from gt.tools.morphing_utilities import morphing_utilities
    morphing_utilities.script_version = __version__
    morphing_utilities.build_gui_morphing_utilities()


if __name__ == "__main__":
    launch_tool()
