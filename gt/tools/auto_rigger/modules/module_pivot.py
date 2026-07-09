"""
Auto Rigger Pivot Module
"""

import gt.tools.auto_rigger.modules.module_generic_fk as tools_generic_fk
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.naming as core_naming
import gt.core.poses as core_poses
import gt.core.node as core_node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModulePivot(tools_generic_fk.ModuleGenericFK):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_pivot
    allow_parenting = True
    default_shape = "_circle_pos_x"

    def __init__(
        self,
        name="Pivot",
        prefix=None,
        suffix=None,
    ):
        """
        Initializes the pivot module with a default control shape
        and sets the re-parent joints function to run post skeleton build.

        Args:
            name (str): Name of the module.
            prefix (str or None): Optional prefix for naming.
            suffix (str or None): Optional suffix for naming.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.set_extra_callable_function(self._reparent_joints, order=tools_rig_frm.CodeData.Order.post_skeleton)
        self.ctrl_shape = self.default_shape

    def _reparent_joints(self):
        """
        Re-parents all children of joints corresponding to proxies
        to their parent's joint or to world if no parent joint exists.
        """
        _joint_list = []
        _joint_parent_list = []
        _children_list = []

        for proxy in self.proxies:
            _joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            _parent = proxy.get_parent_uuid()
            _joint_parent = tools_rig_utils.find_joint_from_uuid(_parent)

            children = cmds.listRelatives(_joint, children=True, fullPath=True)
            if children is None:
                continue

            if _joint_parent:
                _joint_parent_list.append(_joint_parent)

            # Populate List
            _joint_list.append(_joint)
            _children_list.extend(children)

        if _children_list:
            if _joint_parent_list:
                cmds.parent(_children_list, _joint_parent_list[0])
            else:
                cmds.parent(_children_list, world=True)

    def build_rig_post(self, **kwargs):
        """
        Runs post rig script phase.
        This step runs after the execution of "build_rig" is completed.
        Usually used to define automation or connections that require external elements to exist.
        """
        super().build_rig_post()
        jnt_list = [str(tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())) for proxy in self.proxies]

        # if the Rig Pose (a.k.a. T-pose) is applied, we need to remove the pivot joints from the DAG poses
        if self._project.get_preferences_dict_value(key="apply_control_rig_pose", default=True):
            apose_name = core_naming.NamingConstants.Poses.APOSE
            tpose_name = core_naming.NamingConstants.Poses.TPOSE
            if core_poses.check_main_poses():
                cmds.dagPose(jnt_list, remove=True, n=apose_name)
                cmds.dagPose(jnt_list, remove=True, n=tpose_name)
            else:
                logger.error(f"The pivot module {self.name} cannot find the DAG poses {apose_name} and {tpose_name}.")

        # place the joints under the automation group, outside the main skeleton hierarchy
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        for jnt in jnt_list:
            jnt = core_node.Node(jnt)
            cmds.select(jnt)
            cmds.rename(jnt, f"{jnt.get_short_name()}_pivot_driven")
            cmds.parent(jnt, joint_automation_group)


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
    import gt.tools.auto_rigger.modules.module_generic_fk as tools_rig_mod_gen_fk

    # import gt.tools.auto_rigger.modules.module_biped_leg as tools_rig_mod_leg
    # import gt.tools.auto_rigger.modules.module_arm as tools_rig_mod_arm
    # import gt.tools.auto_rigger.modules.module_head as tools_rig_mod_head
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    a_root = tools_rig_mod_root.ModuleRoot()
    a_gen_fk = tools_rig_mod_gen_fk.ModuleGenericFK()
    a_gen_fk_2 = tools_rig_mod_gen_fk.ModuleGenericFK()
    # a_leg = tools_rig_mod_leg.ModuleBipedLeg()
    # a_arm = tools_rig_mod_arm.ModuleArm()
    # a_head = tools_rig_mod_head.ModuleHead()

    a_generic_ModulePivot = ModulePivot(prefix="sssssdads")
    p1 = a_generic_ModulePivot.add_new_proxy()
    p2 = a_generic_ModulePivot.add_new_proxy()
    # p3 = a_generic_ModulePivot.add_new_proxy()
    extra = a_gen_fk.add_new_proxy()
    fk_start = a_gen_fk_2.add_new_proxy()

    # Set proxy names
    p1.set_name("aaaaa")
    p2.set_name("bbbbb")
    # p3.set_name("ccccc")
    extra.set_name("extra")
    fk_start.set_name("start")

    # Set Initial position
    fk_start.set_initial_position(x=2)
    p1.set_initial_position(x=5)
    p2.set_initial_position(x=10)
    # p3.set_initial_position(x=15)
    extra.set_initial_position(x=15)

    # Create Hierarchy
    fk_start.set_parent_uuid(a_root.root_proxy.get_uuid())
    p1.set_parent_uuid(fk_start.get_uuid())
    p2.set_parent_uuid_from_proxy(p1)
    extra.set_parent_uuid(p2.get_uuid())

    fk_start_uuid = a_gen_fk_2.get_uuid()
    # root_uuid = a_root.root_proxy.get_uuid()
    a_generic_ModulePivot.set_parent_uuid(fk_start_uuid)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_gen_fk)
    # a_project.add_to_modules(a_head)
    # a_project.add_to_modules(a_arm)
    a_project.add_to_modules(a_generic_ModulePivot)
    a_project.add_to_modules(a_gen_fk_2)

    a_project.build_proxy()
    a_project.build_rig()

    # Show all
    cmds.viewFit(all=True)
