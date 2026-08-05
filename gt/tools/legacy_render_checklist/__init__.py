"""
 Render Checklist - Check your Maya scene before submitting to a render farm or simply batch rendering.
 github.com/TrevisanGMW/gt-tools -  2020-06-11
 Tested on Maya 2019, 2020 - Windows 10

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 4, 4)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Render Checklist.
    """
    from gt.tools.legacy_render_checklist import legacy_render_checklist
    legacy_render_checklist.script_version = __version__
    legacy_render_checklist.build_gui_gt_render_checklist()


if __name__ == "__main__":
    launch_tool()
