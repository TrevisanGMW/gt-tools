"""
 GT Mirror Cluster Tool - Tool to mirror cluster weights
 github.com/TrevisanGMW/gt-tools -  2020-06-16

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-11-15
 Tweaked the color and text for the title and help menu

 1.2 to 1.2.1 - 2021-05-12 to 2022-07-04
 Made script compatible with Python 3 (Maya 2022+)
 Added logger
 Added patch version
 PEP8 General cleanup

 Todo:
     Add option to mirror other deformers
     Mirror multiple clusters and meshes at the same time
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Mirror Cluster Tool.
    """
    from gt.tools.mirror_cluster_tool import mirror_cluster_tool
    mirror_cluster_tool.build_gui_mirror_cluster_tool()


if __name__ == "__main__":
    launch_tool()
