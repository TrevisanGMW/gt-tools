import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.ui.resource_library as ui_res_lib
import gt.core.io as core_io
import maya.cmds as cmds
import logging
import json
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Attributes
ATTR_DW_PICKER_DATA = "_dwpicker_data"
ATTR_DW_PICKER_DATA_RIG = "_dwpicker_rig_data"  # Unchanging backup data
ATTR_DW_IGNORE_REF_EDITS = "ignoreReferenceEdits"


class ModulePickerData(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_picker_data
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Picker Data", prefix=None, suffix=None):
        """
        Initializes the Enum Variants module.

        Args:
            name (str, optional): The module name.
            prefix (str, optional): Prefix string for naming. Defaults to None.
            suffix (str, optional): Suffix string for naming. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.set_extra_callable_function(self.add_picker_data, order=tools_rig_frm.CodeData.Order.post_build)

        self.pickers = [r"{pipeline-assets-dir}\control_pickers\standard_humanoid_body.json"]

    def add_picker_data(self):
        """Adds control picker data to the rig"""

        try:
            import dwpicker

            _picker_data_node = dwpicker.scenedata.get_picker_holder_node()
            _picker_data_list = []

            for picker_path in self.pickers:
                _parsed_path = self.parse_path(path=picker_path)
                if not os.path.exists(_parsed_path):
                    logger.warning(f'Unable add missing picker data file: "{_parsed_path}".')
                    continue
                _picker_dict = core_io.read_json_dict(_parsed_path)
                _picker_data_list.append(_picker_dict)
                _name = "Untitled"
                # Try to get name:
                _general_data = _picker_dict.get("general")
                if _general_data and isinstance(_general_data, dict):
                    _name = _general_data.get("name", "Untitled")
                # Log that Picker Data was added
                logger.info(f'Picker Data "{_name}" was added to the scene.')
            if _picker_data_list and _picker_data_node:
                cmds.setAttr(
                    f"{_picker_data_node}.{dwpicker.scenedata.PICKER_HOLDER_ATTRIBUTE}",
                    json.dumps(_picker_data_list),
                    typ="string",
                )
                cmds.setAttr(
                    f"{_picker_data_node}.{ATTR_DW_IGNORE_REF_EDITS}",
                    1,  # Ignore Reference Edits
                )
                # --------------- Add Rig Backup Attribute ---------------
                full_backup_attr_name = f"{_picker_data_node}.{ATTR_DW_PICKER_DATA_RIG}"
                if not cmds.attributeQuery(ATTR_DW_PICKER_DATA_RIG, node=_picker_data_node, exists=True):
                    cmds.addAttr(_picker_data_node, longName=ATTR_DW_PICKER_DATA_RIG, dataType="string")
                    cmds.setAttr(full_backup_attr_name, "", type="string")  # initialize empty
                cmds.setAttr(
                    full_backup_attr_name,
                    json.dumps(_picker_data_list),
                    type="string",
                )

        except Exception as e:
            cmds.warning(f"Unable to add control picker data. Issue: {e}")
            return


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

    cmds.file(new=True, force=True)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    import gt.core.session as core_session
    import gt.core.scene as core_scene

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import gt.utils.system as utils_sys
    import importlib

    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    # core_scene.force_reload_file()

    # Setup Modules and their data -----------------------------------------------------------
    test_picker = os.path.join(utils_sys.get_desktop_path(), "standard_humanoid_body.json")
    test_picker_b = os.path.join(utils_sys.get_desktop_path(), "test_picker.json")

    a_picker_data_mod = ModulePickerData()
    a_picker_data_mod.pickers = [test_picker, test_picker_b]

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_picker_data_mod)

    a_project.build_proxy()
    a_project.build_rig()
