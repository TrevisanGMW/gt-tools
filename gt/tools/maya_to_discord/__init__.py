"""
 Maya to Discord
 Send images and videos (playblasts) from Maya to Discord using a Discord Webhook to bridge the two programs.
 github.com/TrevisanGMW/gt-tools -  2020-06-28
 Tested on Maya 2018, 2019, 2020 - Windows 10

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 6, 2)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Maya To Discord.
    """
    from gt.tools.maya_to_discord import maya_to_discord
    maya_to_discord.script_version = __version__
    maya_to_discord.build_gui_maya_to_discord()


if __name__ == "__main__":
    launch_tool()
