import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.hierarchy as core_hrchy
import gt.core.rigging as core_rigging
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.skin as core_skin
import gt.core.io as core_io
import maya.cmds as cmds
import traceback
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EnumVariantsKeys:
    """
    Keys used to access the data found in the dictionaries describing enums and offsets.
    """

    ENUM_ATTR_NAME = "attr_name"
    ENUM_TARGETS = "targets"
    ENUM_DISPLAY_NAMES = "display_names"
    ENUM_INDEX = "index"

    OFFSET_MESH = "mesh"
    OFFSET_TRANSFORM = "offset"
    OFFSET_CONDITION = "condition"


class ModuleEnumVariants(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_enum_variants
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Enum Variants", prefix=None, suffix=None):
        """
        Initializes the Enum Variants module.

        Args:
            name (str, optional): The module name.
            prefix (str, optional): Prefix string for naming. Defaults to None.
            suffix (str, optional): Suffix string for naming. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.set_extra_callable_function(self.setup_enum_variants, order=tools_rig_frm.CodeData.Order.post_build)

        # Enum Vars
        self.enum_frame_expanded = False  # Tracks if UI is collapsed/expanded
        self.enum_dicts = []  # {"attr_name": }
        self.enum_target = "C_visibility_CTRL"
        self.none_label = "None"
        self.driven_attr = "visibility"

        # Offset Vars
        self.offset_frame_expanded = False  # Tracks if UI is collapsed/expanded
        self.offset_dicts = []
        self.offset_suffix = "_preview"
        self.offset_export_data = True
        self.offset_export_path = r"{project-dir}\exports\offsets.json"
        # Private Vars
        self._file_format = ".json"  # Enforced this ext
        self._offset_outliner_color = (0.5, 1, 0.21)

    def setup_enum_variants(self):
        """Creates ENUM variants according to module data"""

        # Offsets --------------------------------------------------------------------------------------------
        setup_group = tools_rig_utils.find_setup_group()
        offset_grp = core_hrchy.create_group(name=f"offsetAutomation")
        # Create Hierarchy
        core_hrchy.parent(source_objects=offset_grp, target_parent=setup_group)
        core_color.set_color_outliner(offset_grp, rgb_color=self._offset_outliner_color)

        for offset_dict in self.offset_dicts:
            # Unpack
            condition = offset_dict.get(EnumVariantsKeys.OFFSET_CONDITION)
            mesh = offset_dict.get(EnumVariantsKeys.OFFSET_MESH)
            offset_trans = offset_dict.get(EnumVariantsKeys.OFFSET_TRANSFORM)

            block_sel_attr = tools_rig_const.RiggerConstants.ATTR_BLOCK_SELECTION
            geo_grp = tools_rig_utils.find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_GEOMETRY)

            try:
                mesh_influences = core_skin.get_influences(mesh)
                if not mesh_influences:
                    raise Exception("No influences detected.")
            except Exception as e:
                logging.warning(
                    f"Make sure the offset mesh is bound to at least one joint. " f'Skipped mesh: "{mesh}". Issue: {e}'
                )
                continue

            dupe_mesh, _ = core_rigging.duplicate_and_offset_mesh(
                source_mesh=mesh,
                offset=offset_trans,
                parent=offset_grp,
                block_selection_attr=f"{geo_grp}.{block_sel_attr}",
                driver_joint=mesh_influences[0],
                hide_original=True,
                suffix=self.offset_suffix,
                condition=condition,
            )
            # Edit Enum Data to adjust suffix
            if cmds.objExists(dupe_mesh):
                original_name = core_naming.get_short_name(dupe_mesh).replace(self.offset_suffix, "")
                duplicated_name = core_naming.get_short_name(dupe_mesh)
                for enum_dict in self.enum_dicts:
                    _enum_key = EnumVariantsKeys.ENUM_TARGETS
                    if _enum_key in enum_dict and isinstance(enum_dict[_enum_key], list):
                        # Iterate through each inner list of targets
                        enum_dict[_enum_key] = [
                            (
                                [duplicated_name if target == original_name else target for target in sublist]
                                if isinstance(sublist, list)
                                else sublist
                            )
                            for sublist in enum_dict[_enum_key]
                        ]
        # Enum Dictionaries ----------------------------------------------------------------------------------

        for enum_dict in self.enum_dicts:
            # Unpack
            attr_name = enum_dict.get(EnumVariantsKeys.ENUM_ATTR_NAME)
            targets = enum_dict.get(EnumVariantsKeys.ENUM_TARGETS)
            display_names = enum_dict.get(EnumVariantsKeys.ENUM_DISPLAY_NAMES)
            index = enum_dict.get(EnumVariantsKeys.ENUM_INDEX, 0)

            try:
                core_rigging.create_enum_switch(
                    attribute_holder=self.enum_target,
                    targets=targets,
                    display_names=display_names,
                    attr_name=attr_name,
                    controlled_attrs=self.driven_attr,
                    default_index=index,
                    none_label=self.none_label,
                )
            except Exception as e:
                traceback.print_exc()
                logger.warning(f"Failed to create ENUM. Issue: {e}")

        # Export Offset Data ---------------------------------------------------------------------------------
        if self.offset_dicts and self.offset_export_data:
            _parsed_path = self.parse_path(path=self.offset_export_path)
            if not os.path.isdir(os.path.dirname(_parsed_path)):
                logger.warning("Unable to find offset file directory. Please set a valid directory.")
                return
            if not _parsed_path.lower().endswith(self._file_format):
                logger.warning(f'File path has a wrong extension. Please set a "{self._file_format}" file path.')
                return
            self.warn_if_path_outside_project(_parsed_path)

            # If already present, make it modifiable
            if _parsed_path and os.path.exists(_parsed_path):
                core_io.set_file_permission_modifiable(_parsed_path)

            core_io.write_json(path=_parsed_path, data=self.offset_dicts)
            logger.info(f"Offset data file has been exported: {_parsed_path}")


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

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

    core_scene.force_reload_file()

    # Setup Modules and their data -----------------------------------------------------------
    test_export_path = os.path.join(utils_sys.get_desktop_path(), f"test_dir", "offsets.json")

    an_enum_variant_mod = ModuleEnumVariants()

    an_enum_variant_mod.offset_export_path = test_export_path  # Set test dir

    test_offset_dict = {
        EnumVariantsKeys.OFFSET_MESH: "PW_M_AR01_Muzzle_01",
        EnumVariantsKeys.OFFSET_TRANSFORM: (0, 0, 7.094),
        EnumVariantsKeys.OFFSET_CONDITION: "PW_M_AR01_Barrel_01.v",
    }
    an_enum_variant_mod.offset_dicts = [test_offset_dict]

    test_enum_dict = {
        EnumVariantsKeys.ENUM_ATTR_NAME: "myEnumAttr",
        EnumVariantsKeys.ENUM_TARGETS: [
            None,
            [
                "PW_M_AR01_Mag_00",
                "PW_M_AR01_Barrel_00",
                "PW_M_AR01_Muzzle_00",
                "PW_M_AR01_Sight_00",
                "PW_M_AR01_Stock_00",
            ],
            [
                "PW_M_AR01_Att_01",
                "PW_M_AR01_Barrel_01",
                "PW_M_AR01_Mag_01",
                "PW_M_AR01_Muzzle_01",
                # "PW_M_AR01_Muzzle_01_preview",
                "PW_M_AR01_Stock_01",
                "PW_M_AR01_Sight_01",
            ],
        ],
        EnumVariantsKeys.ENUM_DISPLAY_NAMES: [None, "Group 1", "Group 2"],
    }
    an_enum_variant_mod.enum_dicts = [test_enum_dict]

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(an_enum_variant_mod)

    a_project.build_proxy()
    a_project.build_rig()
