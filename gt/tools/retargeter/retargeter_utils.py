"""
Retargeter Utilities
"""

import gt.tools.retargeter.retargeter_constants as tools_rt_const
import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import gt.core.str as core_str
import gt.core.io as core_io
import maya.cmds as cmds
import pathlib
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_retargeter_definitions_from_directory(directory_path):
    """
    Loads and sets up RetargeterDefinition objects from matched FBX/definition file pairs in the given directory.
    It's expected that they both have the same name. e.g. "male_poses_01.fbx" and "male_poses_01.rtg"
    The definition file is used as data for the retarget definition and the FBX becomes its source.

    Args:
        directory_path (str or Path): Directory containing .rtg or legacy .json files and matching .fbx files.

    Returns:
        dict[str, RetargeterDefinition]: Dictionary mapping base filenames (without extension)
                                         to fully set up RetargeterDefinition instances.
    """
    directory_path = pathlib.Path(directory_path)
    retargeter_definitions = {}

    # Find all definition and fbx files
    definition_files = {f.stem: f for f in directory_path.glob("*.json")}
    definition_files.update({f.stem: f for f in directory_path.glob("*.rtg")})
    fbx_files = {f.stem: f for f in directory_path.glob("*.fbx")}

    # Intersect keys to find valid pairs
    valid_keys = set(definition_files) & set(fbx_files)

    for key in valid_keys:
        definition_path = definition_files[key]
        fbx_path = fbx_files[key]

        _definition_dict = core_io.read_json_dict(path=str(definition_path))

        definition = tools_rt_frm.RetargeterDefinition()
        definition.read_data_from_dict(_definition_dict)
        definition.set_source_path(str(fbx_path))

        retargeter_definitions[key] = definition

    return retargeter_definitions


def get_configured_definition_from_directory(directory_path, target_definition, target_rig):
    """
    Configures a pre-existing definition and sets the source/target paths for use.

    Args:
        directory_path (str or Path): Directory containing .rtg or legacy .json files and matching .fbx files.
        target_definition (str): Name of the profile used for the retargeting process.
                                 It must be available in the provided directory or operation will fail.
        target_rig (str): A path to the target rig to be used in the retarget operation.
                          Must be compatible with the definition used.

    Return:
        RetargeterDefinition: A preconfigured definition with the provided source and target paths.
    """
    _definition_dict = load_retargeter_definitions_from_directory(directory_path)
    _definition = _definition_dict.get(target_definition)
    if not _definition:
        logger.warning(
            f'Requested definition "{target_definition}" not found in the source directory: "{directory_path}".'
        )
        return

    _definition.set_target_path(target_rig)
    return _definition


def show_dialog_retarget_using_definition_from_directory(directory_path, target_definition):
    """
    Shows a dialog asking for a rig file.
    If one is provided, it's retargeted using the detected definition.

    Args:
        directory_path (str or Path): Directory containing .rtg or legacy .json files and matching .fbx files.
        target_definition (str): Name of the profile used for the retargeting process.
                                 It must be available in the provided directory or operation will fail.
    """
    import gt.ui.file_dialog as ui_file_dialog

    # File Path
    file_path = ui_file_dialog.file_dialog(
        write_mode=False,
        file_filter=tools_rt_const.RetargeterConstants.RETARGET_FILTER,
        ok_caption="Source Rig File",
        cancel_caption="Cancel",
    )
    if not file_path:
        return  # Cancel operation

    _definition = get_configured_definition_from_directory(
        directory_path=directory_path, target_definition=target_definition, target_rig=file_path
    )
    if not _definition:
        return

    _definition.retarget()

    logging.info(f'Definition "{core_str.snake_to_title(str(target_definition))}" retargeted to: "{file_path}".')


if __name__ == "__main__":
    import gt.tests.test_retargeter as test_retargeter
    import inspect

    # --------------------------------- Get Test File Paths --------------------------------
    cmds.file(new=True, force=True)
    desktop_path = os.path.join(os.path.expanduser(os.getenv("USERPROFILE")), "Desktop")
    module_path = inspect.getfile(test_retargeter)
    module_dir = os.path.dirname(module_path)
    test_data_dir = os.path.join(module_dir, "data")
    rom_a_file = os.path.join(test_data_dir, "rom_a.fbx")
    rom_b_file = os.path.join(test_data_dir, "rom_b.fbx")
    rig_file = os.path.join(test_data_dir, "male_rig.ma")

    from pprint import pprint

    test_dir = r"C:\external\assets\auto_rigger_rom_data"
    pprint(load_retargeter_definitions_from_directory(test_dir))
    show_dialog_retarget_using_definition_from_directory(test_dir, target_definition="male_poses_01")
