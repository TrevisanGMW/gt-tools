"""
 GT Maya to Discord
 Send images and videos (playblasts) from Maya to Discord using a Discord Webhook to bridge the two programs.
 github.com/TrevisanGMW/gt-tools -  2020-06-28
 Tested on Maya 2018, 2019, 2020 - Windows 10

 1.1 - 2020-07-04
 Added playblast and desktop options
 It now uses http to handle responses
 Fixed error when capturing viewport on Maya 2019
 Added settings and persistent settings

 1.2 - 2020-10-24
 Fixed a few typos in the documentation
 Changed the feedback given by the playblast to use an inViewMessage
 Added a new method of showing the size of the file (it changes the suffix according to the size)
 Updated "capture_desktop_screenshot" to find what monitor is using Maya

 1.3 - 2020-11-01
 Updated "discord_post_message" to accept usernames
 Added option to send a messages
 Updated the name of the settings dictionary to avoid conflicts
 Added in-view feedback to all buttons
 Made main functions temporarily disable buttons to avoid multiple requests
 Added option to control the visibility of inView messages
 Added option to up timestamp or not

 1.4 - 2020-11-03
 Added send OBJ and send FBX functions
 Changed UI
 Buttons were replaced with iconTextButton
 Button icons (base64) are quickly generated before building window
 Removed header image

 1.5 - 2020-11-15
 Changed the color of a few UI elements
 Removed a few unnecessary lines

 1.6 to 1.6.2 - 2021-05-16 to 2021-11-23
 Made script compatible with Python 3 (Maya 2022+)
 Removed a few old unnecessary lines
 Fixed a typo in the status bar
 Fixed missing patch version
 PEP8 Cleanup
 Added logger

 Todo:
    Improve embeds for discord image uploader - Add colors, emojis and more
    Add option to deactivate threading. (This should affect all send functions)
    Add option to keep screenshots and playblasts in a selected folder
    Add checks to overwrite existing images (UI) when there is a new version
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Maya To Discord.
    """
    from gt.tools.maya_to_discord import maya_to_discord
    maya_to_discord.build_gui_maya_to_discord()


if __name__ == "__main__":
    launch_tool()
