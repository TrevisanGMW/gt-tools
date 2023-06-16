"""
 GT Render Checklist - Check your Maya scene before submitting to a render farm or simply batch rendering.
 github.com/TrevisanGMW/gt-tools -  2020-06-11
 Tested on Maya 2019, 2020 - Windows 10

 1.1 - 2020-07-25
    User no longer needs to remove slashes from custom path. Script manages it.
    Settings are now persistent. (You can reset them in the help menu)
    New function added: "Other Network Paths" checks for paths for the following nodes
        Audio Nodes, Mash Audio Nodes, nCache Nodes,Maya Fluid Cache Nodes,
        Arnold Volumes/Standins/Lights, Redshift Proxy/Volume/Normal/Lights,
        Alembic/BIF/GPU Cache, Golaem Common and Cache Nodes

 1.2 - 2020-11-15
    Changed a few UI elements and colors

 1.3 - 2020-12-05
    Fixed issue where checklist wouldn't update without bifrost loaded
    Added support for non-unique objects to non-manifold checks
    Fixed typos in the help text
    Fixed issue where spaces would cause resolution check to fail

 1.4 to 1.4.4 - 2021-05-12 to 2022-07-21
    Made script compatible with Python 3 (Maya 2022+)
    Added PATCH field to the version 11.11.(11)
    Changed default expected network path and file paths
    Added import line for fileTexturePathResolver
    Some PEP8 Cleanup
    A bit more PEP8 Cleanup
    Fixed settings issue where the UI would get bigger
    Simplified some expressions

 Todo:
    Add checks for xgen
    Create a better error handling option for the total texture count function
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Render Checklist.
    """
    from tools.render_checklist import render_checklist
    render_checklist.build_gui_gt_render_checklist()


if __name__ == "__main__":
    launch_tool()
