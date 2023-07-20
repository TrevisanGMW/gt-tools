"""
 GT Transfer Transforms - Script for transferring Translate, Rotate, and Scale between objects.
 A solution for mirroring poses and set driven keys.
 github.com/TrevisanGMW - 2020-06-07

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-06-09
 Added Copy/Paste TRS options

 1.2 - 2020-06-18
 Changed GUI
 Added icons
 Added help menu

 1.3 - 2020-11-15
 Updated a few UI elements and colors
 Removed a few unnecessary lines

 1.4 - 2021-01-30
 Minor adjustments to the GUI
 Updated help to reflect new changes
 Added documentation to all functions
 Removed initial focus from textfield
 Made the use of quotations more consistent
 Create Import and Export Transform Functions
 Updated Copy and Paste Transforms to account for the previous settings
 Fixed issue where set attribute wouldn't follow previously provided instructions
 Changed the inverted behavior for when getting and settings to only apply when setting
 Managed the "get attribute" by storing full 32-bit precision value while showing truncated version (3f)

 1.5 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.6 to 1.6.1 - 2021-08-08 to 2022-07-09
 Fixed an issue where the script would stop execution when failing to change a locked attribute
 Added better feedback for when values are set (with inView error warning)
 Removed a few unnecessary lines
 PEP8 Cleanup
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Transfer Transforms.
    """
    from gt.tools.transfer_transforms import transfer_transforms
    transfer_transforms.build_gui_transfer_transforms()


if __name__ == "__main__":
    launch_tool()
