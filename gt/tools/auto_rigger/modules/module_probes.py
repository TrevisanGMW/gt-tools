"""
Auto Rigger Probe Modules
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.logger as core_log
import gt.core.node as core_node
import gt.core.str as core_str
import maya.cmds as cmds
import logging
import random

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


def create_probe_group(name):
    """
    Detects necessary groups to create and parent a probe group.
    Args:
        name (str): Name of the probe group to create
    Returns:
        Node: A node (str) with the path to the generated probe group.
    """
    # Create Probe Automation Group
    setup_group = tools_rig_utils.find_setup_group()
    setup_group_children = cmds.listRelatives(setup_group, children=True) or []
    probe_ref_group = f"probeReferences"
    if probe_ref_group not in setup_group_children:
        probe_ref_group = core_hrchy.create_group(name=probe_ref_group)
        core_hrchy.parent(source_objects=probe_ref_group, target_parent=setup_group)
        core_color.set_color_outliner(obj_list=probe_ref_group, rgb_color=(0, 1, 0))
    # Probe Group
    probe_group = core_hrchy.create_group(name=name)
    core_hrchy.parent(source_objects=probe_group, target_parent=probe_ref_group)
    for axis in ["X", "Y", "Z"]:
        for attr in ["translate", "rotate", "scale"]:
            attr_name = f"{probe_group}.{attr}{axis}"
            cmds.setAttr(attr_name, keyable=False)
    cmds.setAttr(f"{probe_group}.v", 0)
    cmds.setAttr(f"{probe_group}.v", keyable=False)
    cmds.addAttr(probe_group, ln=tools_rig_const.RiggerConstants.ATTR_PROBE_OUTPUT, at="double", keyable=True)
    return probe_group


class ModuleProbeDistance(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_distance_probe
    allow_parenting = True
    allow_multiple = True

    PROBE_TRANS_STR = "distProbe"  # Determines the name of the probe group. Pattern: "<prefix><PROBE_TRANS_STR>"

    def __init__(self, name="Distance", prefix=None, suffix=None):
        """
        Initializes the ModuleProbeDistance instance.

        Args:
            name (str, optional): The display name for the module. Defaults to "Distance".
            prefix (str, optional): Optional prefix to prepend to node names. Defaults to None.
            suffix (str, optional): Optional suffix to append to node names. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.set_extra_callable_function(self._create_distance_nodes, order=tools_rig_frm.CodeData.Order.post_skeleton)
        self.start = ""
        self.end = ""
        self.chain = True
        self.setup_name = ""

    def _parse_prefix(self):
        """
        Assembles a prefix to be used by this probe.
        Returns:
            str: A prefix to be used by the distance probe. This is used by the created nodes and the probe group.
        """
        if self.setup_name and isinstance(self.setup_name, str):
            _prefix = f"{self.setup_name}_"
        elif self.start and self.end:
            _start_short = core_naming.get_short_name(self.start, remove_namespace=True) or self.start
            _end_short = core_naming.get_short_name(self.end, remove_namespace=True) or self.end
            _prefix = f"{_start_short}_to_{_end_short}_"
        elif self.start:
            _start_short = core_naming.get_short_name(self.start, remove_namespace=True) or self.start
            _prefix = f"{_start_short}_"
        elif self.end:
            _end_short = core_naming.get_short_name(self.end, remove_namespace=True) or self.end
            _prefix = f"{_end_short}_"
        else:
            _prefix = ""
        return _prefix

    def get_probe_output_attr_path(self):
        """
        Gets the output attribute path used as source for other operations.
        Returns:
            str: Maya path to the probe output attribute.
        """
        return f"{self._parse_prefix()}{self.PROBE_TRANS_STR}.{tools_rig_const.RiggerConstants.ATTR_PROBE_OUTPUT}"

    def _create_distance_nodes(self):
        """
        Use maya commands to trigger a new scene without asking if the user wants to save current work.
        If initial scene options were provided, these are set after starting a new scene.
        """
        if not self.start or not self.end:
            logger.warning(f"Distance probe creation skipped. Start or end points not defined.")
            return

        if not cmds.objExists(self.start) or not cmds.objExists(self.end):
            logger.warning(f"Distance probe creation skipped. Start or end points missing.")
            return

        # Define Distance List
        if self.chain:
            dist_source_list = core_hrchy.list_hierarchy_path(start_object=self.start, end_object=self.end)
            if not dist_source_list:
                logger.warning(f"Unable to create chained measurement. Defaulting to source and target method.")
                dist_source_list = [self.start, self.end]
        else:
            dist_source_list = [self.start, self.end]

        # Prefix
        _prefix = self._parse_prefix()

        # Create Probe Automation Group & Probe Group
        probe_group = f"{_prefix}{self.PROBE_TRANS_STR}"
        if cmds.objExists(probe_group):
            logger.warning(
                f"Distance probe creation skipped. Non-unique probe group name detected. "
                f"Change setup name to solve this issue."
            )
            return
        probe_group = create_probe_group(name=probe_group)

        # Measurement Nodes
        dist_data = {}  # [distance_node_transform, start_loc, end_loc]
        for index in range(len(dist_source_list)):
            start_pos = (1, random.random() * 10, 1)
            end_pos = (2, random.random() * 10, 2)
            dist_mid = cmds.distanceDimension(startPoint=start_pos, endPoint=end_pos)
            dist_mid_transform = cmds.listRelatives(dist_mid, parent=True, fullPath=True)[0]
            start_loc, end_loc = cmds.listConnections(dist_mid)
            # Convert To Nodes
            dist_mid = core_node.Node(dist_mid)
            dist_mid_transform = core_node.Node(dist_mid_transform)
            start_loc = core_node.Node(start_loc)
            end_loc = core_node.Node(end_loc)
            # Rename Nodes
            mid_name = f"{_prefix}{core_str.get_int_as_en(index + 1)}_probeDistanceShape"
            dist_mid.rename(mid_name)
            mid_trans_name = f"{_prefix}{core_str.get_int_as_en(index + 1)}_probeDistance"
            dist_mid_transform.rename(mid_trans_name)
            start_loc.rename(f"{_prefix}{core_str.get_int_as_en(index + 1)}_start")
            end_loc.rename(f"{_prefix}{core_str.get_int_as_en(index + 1)}_end")

            cmds.pointConstraint(dist_source_list[index], start_loc)
            if index < (len(dist_source_list) - 1):
                cmds.pointConstraint(dist_source_list[index + 1], end_loc)
            else:
                cmds.pointConstraint(self.end, end_loc)
            dist_data[dist_mid] = [dist_mid_transform, start_loc, end_loc]
            index += 1

        # Organization & Output
        dist_sum_node = core_node.create_node(node_type="plusMinusAverage", name=f"{_prefix}sum")
        index = 0
        for dist_node, dist_transforms in dist_data.items():
            for trans in dist_transforms:
                cmds.setAttr(f"{trans}.overrideEnabled", 1)
                cmds.setAttr(f"{trans}.overrideDisplayType", 1)
            core_hrchy.parent(source_objects=dist_transforms, target_parent=probe_group)
            cmds.connectAttr(f"{dist_node}.distance", f"{dist_sum_node}.input1D[{index}]")
            index += 1
        cmds.connectAttr(
            f"{dist_sum_node}.output1D", f"{probe_group}.{tools_rig_const.RiggerConstants.ATTR_PROBE_OUTPUT}"
        )


class ModuleProbeRotation(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_rot_probe
    allow_parenting = True
    allow_multiple = True

    PROBE_TRANS_STR = "rotProbe"  # Determines the name of the probe group. Pattern: "<prefix><PROBE_TRANS_STR>"

    def __init__(self, name="Rotation", prefix=None, suffix=None):
        """
        Initializes the ModuleProbeRotation instance.

        Args:
            name (str, optional): The display name for the module. Defaults to "Rotation".
            prefix (str, optional): Optional prefix to prepend to node names. Defaults to None.
            suffix (str, optional): Optional suffix to append to node names. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.set_extra_callable_function(
            self._create_rotation_probe_nodes, order=tools_rig_frm.CodeData.Order.post_skeleton
        )
        self.source = ""
        self.setup_name = ""
        self.axis = 0

    def _parse_prefix(self):
        """
        Assembles a prefix to be used by this probe.
        Returns:
            str: A prefix to be used by the distance probe. This is used by the created nodes and the probe group.
        """
        if self.setup_name and isinstance(self.setup_name, str):
            _prefix = f"{self.setup_name}_"
        elif self.source:
            _source_short = core_naming.get_short_name(self.source, remove_namespace=True) or self.source
            _prefix = f"{_source_short}_"
        else:
            _prefix = ""
        return _prefix

    def get_probe_output_attr_path(self):
        """
        Gets the output attribute path used as source for other operations.
        Returns:
            str: Maya path to the probe output attribute.
        """
        return f"{self._parse_prefix()}{self.PROBE_TRANS_STR}.{tools_rig_const.RiggerConstants.ATTR_PROBE_OUTPUT}"

    def _create_rotation_probe_nodes(self):
        """
        Use maya commands to trigger a new scene without asking if the user wants to save current work.
        If initial scene options were provided, these are set after starting a new scene.
        """
        if not self.source:
            logger.warning(f"Rotation probe creation skipped. Source object not defined.")
            return

        if not cmds.objExists(self.source):
            logger.warning(f"Rotation probe creation skipped. Source object is missing.")
            return

        # Prefix
        _prefix = self._parse_prefix()

        # Create Probe Automation Group & Probe Group
        probe_group = f"{_prefix}{self.PROBE_TRANS_STR}"
        if cmds.objExists(probe_group):
            logger.warning(
                f"Rotation probe creation skipped. Non-unique probe group name detected. "
                f"Change setup name to solve this issue."
            )
            return
        probe_group = create_probe_group(name=probe_group)

        twist_swing_node = core_node.create_node(node_type="SwingTwistNode", name=f"{_prefix}SwingTwist")
        decompose_matrix_node = core_node.create_node(node_type="decomposeMatrix", name=f"{_prefix}decomposeMatrix")

        cmds.connectAttr(f"{self.source}.parentMatrix[0]", f"{twist_swing_node}.driverRestMatrix")
        cmds.connectAttr(f"{self.source}.worldMatrix[0]", f"{twist_swing_node}.driverMatrix")
        cmds.connectAttr(f"{twist_swing_node}.outMatrix", f"{decompose_matrix_node}.inputMatrix")

        # Connect Output
        _axis = ["X", "Y", "Z"]
        cmds.connectAttr(
            f"{decompose_matrix_node}.outputRotate{_axis[self.axis]}",
            f"{probe_group}.{tools_rig_const.RiggerConstants.ATTR_PROBE_OUTPUT}",
        )


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)
    from gt.tools.auto_rigger.rig_framework import RigProject, ModuleGeneric

    # Create Test Modules ---------------------------------------------------------------------------------
    a_generic_module = ModuleGeneric()
    a_distance_module = ModuleProbeDistance()
    a_rotation_module = ModuleProbeRotation()

    # Configure Modules -----------------------------------------------------------------------------------
    a_distance_module.start = "L_upperArm_JNT"
    a_distance_module.end = "L_middle03_JNT"
    a_rotation_module.source = "L_lowerArm_JNT"

    # Configure Modules -----------------------------------------------------------------------------------
    p1 = a_generic_module.add_new_proxy()
    p2 = a_generic_module.add_new_proxy()
    p3 = a_generic_module.add_new_proxy()
    p1.set_name("first")
    p2.set_name("second")
    p3.set_name("third")
    p2.set_initial_position(y=15)
    p3.set_initial_position(y=30)
    p2.set_parent_uuid(p1.get_uuid())
    p3.set_parent_uuid(p2.get_uuid())
    p1.set_locator_scale(6)
    p2.set_locator_scale(5)
    p3.set_locator_scale(4)

    # Create Project and Build ----------------------------------------------------------------------------
    a_project = RigProject()
    a_project.set_project_dir_path(r"{desktop-dir}\test_folder")
    a_project.add_to_modules(a_generic_module)
    a_project.add_to_modules(a_distance_module)
    a_project.add_to_modules(a_rotation_module)

    # Build
    a_project.build_proxy()
    a_project.build_rig()

    # Frame all
    cmds.viewFit(all=True)
