"""
 GT Morphing to Attributes (a.k.a. Blend Shapes to Attributes)
 github.com/TrevisanGMW/gt-tools - 2022-03-17

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 0.0.1 to 0.0.3 - 2022-03-17 to 2022-07-23
 Created core function
 Created GUI
 Added settings

 1.0.0 to 1.0.1 - 2022-07-24 to 2022-07-24
 Connected UI and main function
 Connected Settings
 Added filter logic
 Added separated text field for undesired filter
 Added undo chunk
 Changed remap node name
 Kept original selection after operation
 Added inView feedback
 Added some docs

 1.1.0 to 1.1.2 - 2022-07-24 to 2022-12-23
 Added "Delete Instead" option
 Added "Sort Attributes" option
 Added more feedback
 Renamed "Ignore Uppercase"
 Minor tweaks to the GUI
 Added help
 Repositioned "Delete Instead"
 Small changes to the system out text behaviour when selecting a blend shape
 Updated icon
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Morphing Attributes.
    """
    from gt.tools.morphing_attributes import morphing_attributes
    morphing_attributes.build_gui_morphing_attributes()


if __name__ == "__main__":
    launch_tool()
