import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.iterable as core_iter
import gt.core.curve as core_curve
import gt.core.color as core_color
import gt.core.anim as core_anim
import gt.core.uuid as core_uuid
import gt.core.node as core_node
import gt.core.attr as core_attr
import gt.core.io as core_io
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleCorrectiveGeneric(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_corrective_generic
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Corrective Generic", prefix=None, suffix=None):
        """
        Initializes the Corrective Generic module with default parameters and
        registers the import_driven_keys function to be called post control rig build.

        Args:
            name (str, optional): The module name. Defaults to "Corrective Generic".
            prefix (str, optional): Prefix string for naming. Defaults to None.
            suffix (str, optional): Suffix string for naming. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.set_extra_callable_function(self.import_driven_keys, order=tools_rig_frm.CodeData.Order.post_control_rig)
        self.driven_keys_dir = r"{project-dir}\keys\{module-sanitized-name}"
        self.driver_attr_paths = []
        self.clear_target_dir = True

        # Module File Format
        self._file_format = ".json"

        # Multipliers (Affect the values of attributes connected to TRS attributes)
        self.translate_multiplier = 1.0
        self.rotate_multiplier = 1.0
        self.scale_multiplier = 1.0

    def add_new_driver_attr_path(self):
        """Add a new dictionary {None: ""} at the end of the driver_attr_paths list."""
        self.driver_attr_paths.append({None: ""})

    def get_driver_attr_path(self, index):
        """
        Return the dictionary at the given index from self.driver_attr_paths.
        Args:
            index (int): The index of the driver attribute path to retrieve.
        Returns:
            dict: A dictionary found in the provided index.
        """
        if not (0 <= index < len(self.driver_attr_paths)):
            raise IndexError("Index out of range.")

        return self.driver_attr_paths[index]

    def remove_driver_attr_path(self, index):
        """
        Remove a dictionary from the driver_attr_paths list by index.

        Args:
            index (int): Index of the dictionary to remove.

        Raises:
            IndexError: If the index is out of range.
        """
        if 0 <= index < len(self.driver_attr_paths):
            del self.driver_attr_paths[index]
        else:
            raise IndexError(f"Index {index} out of range for driver_attr_paths.")

    def update_driver_attr_path(self, index, new_mapping):
        """
        Update the dictionary at the given index in self.driver_attr_paths.

        Args:
            index (int): The index of the dictionary to update.
            new_mapping (dict): A dictionary with a single key-value pair to replace the existing one.

        Returns:
            bool: True if update succeeded, False otherwise (e.g., index out of range).
        """
        if not isinstance(new_mapping, dict) or len(new_mapping) != 1:
            raise ValueError("new_mapping must be a dictionary with a single key-value pair.")

        if 0 <= index < len(self.driver_attr_paths):
            self.driver_attr_paths[index] = new_mapping
            return True
        return False

    def set_driven_keys_dir(self, driven_keys_dir):
        """
        Sets the directory path used to import driven key files.
        Args:
            driven_keys_dir (str): A file path to be used when writing or reading a list of driven keys.
        """
        if driven_keys_dir is None:
            self.driven_keys_dir = ""
        if not isinstance(driven_keys_dir, str):
            logger.warning("Unable to driven keys directory path. Invalid data type was provided.")
            return
        self.driven_keys_dir = driven_keys_dir

    def get_driven_joints(self):
        """
        Gets built joints matching the UUIDs of this module. Used to get driven joints (joints receiving driven keys)
        Returns:
            list: A list of joints belonging to this module.
        """
        _joints = []
        for proxy in self.proxies:
            joint_node = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if joint_node:
                _joints.append(joint_node)
        return _joints

    def _validate_write_operation(self, clear_target_dir=True):
        """
        Validates the write operation before running it.
        Args:
            clear_target_dir (bool, optional): If True, the target directory will be cleared before writing.
                                               (Any existing files match the module file format  will be deleted)
        """
        rig_root = tools_rig_utils.find_root_group_rig()
        if not rig_root:
            logger.warning(
                f"Rig must be built before writing driven keys. "
                f"(Keys are created manually on a built rig, then saved/written)"
            )
            return
        # Get write directory
        _parsed_path = self.parse_path(path=self.driven_keys_dir)
        if not os.path.exists(_parsed_path):
            os.makedirs(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to write influences. Invalid path: "{str(_parsed_path)}".')
            return

        # Clear existing
        if clear_target_dir:
            core_io.delete_dir_files(directory_path=_parsed_path, file_extension=self._file_format)

        return _parsed_path

    def write_driven_keys(self, clear_target_dir=True):
        """
        Writes driven keys to the defined directory.
        Args:
            clear_target_dir (bool, optional): If True, the target directory will be cleared before writing.
                                               (Any existing files match the module file format  will be deleted)
        """
        _parsed_path = self._validate_write_operation(clear_target_dir=clear_target_dir)
        if not _parsed_path:
            return
        if not os.path.exists(_parsed_path):
            try:
                os.makedirs(_parsed_path, exist_ok=True)
            except (OSError, ValueError):
                return False
        # Find joints and Write Double Keys
        _joints = self.get_driven_joints()
        _export_counter = 0
        for jnt in _joints:
            _short_name = core_naming.get_short_name(jnt)
            _counter = core_anim.export_double_keys_to_directory(
                source_objs=jnt,
                target_dir=_parsed_path,
                file_prefix=f"{_short_name}_",
            )
            _export_counter += _counter
        import gt.core.feedback as core_fback

        feedback = core_fback.FeedbackMessage(
            quantity=_export_counter,
            singular="driven keyframe node was",
            plural="driven keyframe nodes were",
            conclusion="exported.",
            zero_overwrite_message="No driven keyframes were exported.",
        )
        feedback.print_inview_message()
        logger.info(f"{_export_counter} driven key frames exported.")

    def import_driven_keys(self):
        """Imports double keys stored in the driven  key directory"""
        _parsed_path = self.parse_path(path=self.driven_keys_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to import driven keys from missing directory. Path: "{str(_parsed_path)}".')
            return
        self.warn_if_path_outside_project(_parsed_path)
        core_anim.import_double_keys_from_directory(
            source_dir=_parsed_path,
            translate_multiplier=self.translate_multiplier,
            rotate_multiplier=self.rotate_multiplier,
            scale_multiplier=self.scale_multiplier,
        )

    def build_proxy(self, **kwargs):
        """
        Overrides the proxy build phase, allowing proxy names to be customized via attributes.
        """
        return super().build_proxy(use_naming_attrs=True, **kwargs)  # Allow name overrides

    def build_skeleton_joints(self, **kwargs):
        """
        Overrides the skeletal build phase, allowing joint names to be customized via proxy attributes.
        """
        super().build_skeleton_joints(use_naming_attrs=True)  # Allow name overrides


class ModuleCorrectiveFK(ModuleCorrectiveGeneric):
    __version__ = "0.0.1"
    icon = ui_res_lib.Icon.rigger_module_corrective_fk
    allow_parenting = True
    allow_multiple = True

    DEFAULT_SHAPE = "_circle_pos_x"
    DRIVEN_GROUP = "driven"

    def __init__(self, name="Corrective FK", prefix=None, suffix=None):
        """
        Initialize the Corrective FK module with default control shape, color, and scale inclusion.

        Args:
            name (str, optional): Name of the module instance. Defaults to "Corrective FK".
            prefix (str, optional): Naming prefix. Defaults to None.
            suffix (str, optional): Naming suffix. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.ctrl_shape = self.DEFAULT_SHAPE
        self.ctrl_color = None
        self.include_scale = False

    def set_control_shape(self, shape):
        """
        Sets a new control shape
        Args:
            shape (str): The name of the control file.
        """
        self.ctrl_shape = shape

    def set_control_color(self, color):
        """
        Sets a new control color
        Args:
            color (str): The name of the color.
        """
        self.ctrl_color = color

    def get_driven_groups(self):
        """
        Finds all available driven groups (these are offset groups specific for this module)
        Returns:
            list: A list of Nodes (str) describing the path to the driven offset groups for this module.
        """
        _attr = tools_rig_const.RiggerConstants.ATTR_SOURCE_LOOKUP_UUID
        driven_groups = []
        for proxy in self.proxies:
            driven_grp = core_uuid.get_object_from_uuid_attr(
                uuid_string=proxy.get_uuid(),
                attr_name=_attr,
                obj_type="transform",
            )
            driven_groups.append(core_node.Node(driven_grp))
        return driven_groups

    def write_driven_keys(self, clear_target_dir=True):
        """
        Writes driven keys to the defined directory.
        Args:
            clear_target_dir (bool, optional): If True, the target directory will be cleared before writing.
                                               (Any existing files match the module file format  will be deleted)
        """
        _parsed_path = self._validate_write_operation(clear_target_dir=clear_target_dir)
        if not _parsed_path:
            return
        if not os.path.exists(_parsed_path):
            try:
                os.makedirs(_parsed_path, exist_ok=True)
            except (OSError, ValueError):
                return False
        # Find joints and Write Double Keys
        _driven_groups = self.get_driven_groups()
        _export_counter = 0
        for driven_grp in _driven_groups:
            _short_name = core_naming.get_short_name(driven_grp)
            _counter = core_anim.export_double_keys_to_directory(
                source_objs=driven_grp,
                target_dir=_parsed_path,
                file_prefix=f"{_short_name}_",
            )
            _export_counter += _counter
        import gt.core.feedback as core_fback

        feedback = core_fback.FeedbackMessage(
            quantity=_export_counter,
            singular="driven keyframe node was",
            plural="driven keyframe nodes were",
            conclusion="exported.",
            zero_overwrite_message="No driven keyframes were exported.",
        )
        feedback.print_inview_message()
        logger.info(f"{_export_counter} driven key frames exported.")

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        # Helpful Elements
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())

        # Setup groups
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_group)
        cmds.setAttr(f"{joint_automation_group}.visibility", 0)

        # Generate Unique Purpose Dict
        names_list = [proxy.get_name() for proxy in self.proxies]
        purpose_list = core_iter.get_unique_name_list(names_list)
        purpose_dict = dict(zip(self.proxies, purpose_list))

        # Define Shape
        _ctrl_shape = self.DEFAULT_SHAPE
        if self.ctrl_shape and core_curve.get_curve(self.ctrl_shape):
            _ctrl_shape = self.ctrl_shape

        # FK Controls ----------------------------------------------------------------------------------------
        fk_controls = []  # Actual Control Transforms (With Curve Shapes Inside)
        offset_groups = []
        parenting_pairs = {}  # To adjust hierarchy after creating
        _module_prefix = self.prefix
        _module_suffix = self.suffix
        _module_color = self.ctrl_color

        for proxy in self.proxies:
            if proxy.get_attr_dict_value(key="prefix") and not None:
                self.prefix = proxy.get_attr_dict_value(key="prefix")
            if proxy.get_attr_dict_value(key="suffix") and not None:
                self.suffix = proxy.get_attr_dict_value(key="suffix")
            _joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not self.ctrl_color or self.ctrl_color == "INHERIT COLOR":
                self.ctrl_color = core_color.get_directional_color(object_name=_joint)
            else:
                if not isinstance(self.ctrl_color, (list, tuple)):  # Filtering RBG lists/tuples
                    self.ctrl_color = getattr(core_color.ColorConstants.RGB, self.ctrl_color)
            if not _joint:
                continue  # Missing joint
            _purpose = purpose_dict.get(proxy, "")
            _proxy = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            _rotation_order = cmds.getAttr(f"{_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            _ctrl, _parent_groups = self.create_rig_control(
                control_base_name=proxy.get_name(),
                curve_file_name=_ctrl_shape,
                parent_obj=global_offset_ctrl,
                extra_parent_groups=[self.DRIVEN_GROUP],
                match_obj=_joint,
                add_offset_ctrl=False,
                rot_order=_rotation_order,
                color=self.ctrl_color,
            )[:2]
            self._add_driver_uuid_attr(
                target_driver=_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=_purpose,
            )

            # Add Driven Attribute (Lookup)
            driven_grp = _parent_groups[1]
            core_attr.add_attr(
                obj_list=driven_grp,
                attributes=tools_rig_const.RiggerConstants.ATTR_SOURCE_LOOKUP_UUID,
                attr_type="string",
                default=proxy.get_uuid(),
            )

            # Add Turn Off Driven Setup
            prefix_and_name = f"{self.prefix}_{proxy.get_name()}"
            blend_matrix = core_node.create_node(node_type="blendMatrix", name=f"{prefix_and_name}_matrixBlend")
            reverse = core_node.create_node(node_type="reverse", name=f"{prefix_and_name}_reverse")
            cmds.connectAttr(f"{driven_grp}.inverseMatrix", f"{blend_matrix}.target[0].targetMatrix")
            cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{driven_grp}.offsetParentMatrix")
            activation_attr = "drivenActivation"
            core_attr.add_attr(
                obj_list=_ctrl, attributes=activation_attr, attr_type="double", default=1, minimum=0, maximum=1
            )
            cmds.connectAttr(f"{_ctrl}.{activation_attr}", f"{reverse}.inputX")
            cmds.connectAttr(f"{reverse}.outputX", f"{blend_matrix}.envelope")

            # Populate Joint Purpose and Driver
            core_attr.set_attr(
                attribute_path=f"{_joint}.{tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE}", value=_purpose
            )
            tools_rig_utils.add_driver_to_joint(target_joint=_joint, new_drivers=tools_rig_const.RiggerDriverTypes.FK)

            # Adjust and Connect Control
            hide_scale = not self.include_scale  # Invert Add Scale
            core_attr.hide_lock_default_attrs(obj_list=_ctrl, scale=hide_scale, visibility=True)
            core_cnstr.constraint_targets(source_driver=_ctrl, target_driven=_joint)
            if self.include_scale:
                core_cnstr.constraint_targets(
                    source_driver=_ctrl,
                    target_driven=_joint,
                    constraint_type=core_cnstr.ConstraintTypes.SCALE,
                )

            # Populate Lists
            offset_group = _parent_groups[0]
            fk_controls.append(_ctrl)
            offset_groups.append(offset_group)
            parenting_pairs[offset_group] = proxy.get_parent_uuid()

            self.prefix = _module_prefix
            self.suffix = _module_suffix
            self.ctrl_color = _module_color

        # Parent Controls --------------------------------------------------------------------------------------
        for offset_group, parent_uuid in parenting_pairs.items():
            if not parent_uuid:
                continue  # No Parent
            _parent_joint = tools_rig_utils.find_joint_from_uuid(parent_uuid)
            if not _parent_joint:
                continue  # Parent joint not found

            _parent_joint_drivers = tools_rig_utils.find_drivers_from_joint(
                _parent_joint, as_list=True, create_missing_generic=True, skip_block_drivers=True
            )
            if _parent_joint_drivers:
                core_hrchy.parent(source_objects=offset_group, target_parent=_parent_joint_drivers[0])

        # Find Control Offsets without Target Parent -----------------------------------------------------------
        offsets_without_parents = [key for key, value in parenting_pairs.items() if value is None]

        # Set Children Drivers ---------------------------------------------------------------------------------
        self.module_children_drivers = offsets_without_parents


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root
    import gt.utils.system as utils_sys
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    # Setup Modules and their data -----------------------------------------------------------
    test_path = os.path.join(utils_sys.get_desktop_path(), f"test_dir")

    a_root = tools_rig_mod_root.ModuleRoot()
    a_corrective_generic_mod = ModuleCorrectiveGeneric()
    a_corrective_generic_mod = ModuleCorrectiveFK()
    a_corrective_generic_mod.include_scale = True
    a_corrective_generic_mod.driven_keys_dir = test_path  # Set test dir
    p1 = a_corrective_generic_mod.add_new_proxy()
    p2 = a_corrective_generic_mod.add_new_proxy()
    p3 = a_corrective_generic_mod.add_new_proxy()
    extra = a_corrective_generic_mod.add_new_proxy()

    # Set Initial position
    p1.set_initial_position(x=5)
    p2.set_initial_position(x=10)
    p3.set_initial_position(x=15)
    extra.set_initial_position(z=5)

    # Create Hierarchy
    p1.set_parent_uuid(a_root.root_proxy.get_uuid())
    p2.set_parent_uuid_from_proxy(p1)
    p3.set_parent_uuid_from_proxy(p2)

    root_uuid = a_root.root_proxy.get_uuid()
    a_corrective_generic_mod.set_parent_uuid(root_uuid)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_corrective_generic_mod)

    a_project.build_proxy()
    a_project.build_rig()

    # Show all
    cmds.viewFit(all=True)
    cmds.setAttr("skeleton.v", 1)
