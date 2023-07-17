"""
 GT Biped Rigger
 github.com/TrevisanGMW - 2020-12-08

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 TODO:
    Updated pattern to MVC
"""
# Tool Version
__version_tuple__ = (1, 12, 6)
__version__ = '.'.join(str(n) for n in __version_tuple__)


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Biped Rigger.
    """
    from gt.tools.auto_rigger import rigger_biped_gui
    rigger_biped_gui.build_gui_auto_biped_rig()


def launch_biped_rig_interface():
    """.
    Entry point for when using the GT Biped Rig Interface.
    """
    from gt.tools.auto_rigger import biped_rig_interface
    biped_rig_interface.build_gui_custom_rig_interface()


def launch_retarget_assistant():
    """.
    Entry point for when using the GT Retarget Assistant.
    """
    from gt.tools.auto_rigger import rigger_retarget_assistant
    rigger_retarget_assistant.build_gui_mocap_rig()


def launch_game_exporter():
    """.
    Entry point for when using the GT Game FBX Exporter.
    """
    from gt.tools.auto_rigger import rigger_game_exporter
    rigger_game_exporter.build_gui_fbx_exporter()


if __name__ == "__main__":
    launch_tool()
