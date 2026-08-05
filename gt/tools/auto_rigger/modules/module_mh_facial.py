"""
Auto Rigger MetaHuman Face Module
"""

import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleMetaHumanFace(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_facial_mh
    allow_parenting = True

    def __init__(self, name="Face MH", prefix=None, suffix=None):
        """
        Initialize a MetaHuman Face module.

        Args:
            name (str): Module name.
            prefix (str or None): Optional naming prefix.
            suffix (str or None): Optional naming suffix.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Default Values
        self.face_root_jnt = "FACIAL_C_FacialRoot"
        self.file_path = ""
        self.file_namespace = "face_rig"
        self.driver_prefix = "driver_"
        self.set_extra_callable_function(
            callable_func=self._parent_facial_root, order=tools_rig_frm.CodeData.Order.post_build
        )

    def build_skeleton_hierarchy(self):
        """
        Runs skeletal hierarchy phase (post skeleton). Joints are parented and oriented during this step.
        Happens after the "build_skeleton_joints" function in a project.
        """
        """Imports MetaHuman face and connects to existing skeleton"""
        # import file
        _parsed_path = self.parse_path(path=self.file_path)
        self.warn_if_path_outside_project(_parsed_path)
        cmds.file(_parsed_path, i=True)
        main_grp = "head_grp"
        head_rig_grp = "headRig_grp"
        constraint_setup = []

        # Find module setup
        _valid_parent_module = False
        face_automation_group = tools_rig_utils.get_automation_group(f"faceAutomation")
        head_jnt = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
        if head_jnt:
            neck02_jnt = cmds.listRelatives(head_jnt, parent=True, type="joint")[0]
            constraint_setup.append(head_jnt)
            if neck02_jnt:
                neck01_jnt = cmds.listRelatives(neck02_jnt, parent=True, type="joint")[0]
                constraint_setup.append(neck02_jnt)
                if neck01_jnt:
                    _valid_parent_module = True
                    constraint_setup.append(neck01_jnt)

        # Duplicate Joints
        cmds.namespace(add="face_rig")
        face_jnts = ["head", "neck_02", "neck_01", self.face_root_jnt]
        all_jnts = cmds.listRelatives(head_rig_grp, ad=True, type="joint")
        for remove_jnt in face_jnts:
            try:
                all_jnts.remove(remove_jnt)
            except:
                logger.warning("Please make sure that the face joints are inside the headRig_grp")
            cmds.rename(remove_jnt, f"{self.file_namespace}:{remove_jnt}")
            if remove_jnt == face_jnts[-1]:
                self._facial_root_joint = cmds.duplicate(f"{self.file_namespace}:{remove_jnt}", po=True)

        for jnt in all_jnts:
            jnt = cmds.rename(jnt, f"{self.file_namespace}:{jnt}")
            if cmds.listConnections(jnt, d=True, type="skinCluster"):
                new_jnt = cmds.duplicate(jnt, po=True)
                core_hrchy.parent(source_objects=new_jnt, target_parent=self.face_root_jnt)
                cmds.parentConstraint(jnt, new_jnt)
                cmds.setAttr(f"{new_jnt[0]}.radius", 0.2)

        # Finalize setup
        if _valid_parent_module:
            for setup_jnt in constraint_setup:
                cmds.parentConstraint(
                    setup_jnt, f"{self.file_namespace}:{face_jnts[constraint_setup.index(setup_jnt)]}", mo=True
                )
        cmds.parent(head_rig_grp, face_automation_group)
        cmds.setAttr(f"{self.file_namespace}:neck_01.visibility", 0)
        cmds.delete(main_grp)

        # Remove Temp Namespace
        ns_joints = core_hrchy.get_hierarchy(root=f"{self.file_namespace}:neck_01", full_path=True)
        ns_joints.sort(key=len, reverse=True)
        for jnt in ns_joints:
            new_name = core_naming.get_short_name(jnt).replace(f"{self.file_namespace}:", self.driver_prefix)
            cmds.rename(jnt, new_name)
        if cmds.namespace(exists=self.file_namespace):
            cmds.namespace(removeNamespace=self.file_namespace)

    def _parent_facial_root(self):
        """
        Parents the generated facial root.
        """
        parent_jnt = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
        general_automation_grp = tools_rig_utils.get_automation_group()
        if parent_jnt:
            core_hrchy.parent(source_objects=self._facial_root_joint, target_parent=parent_jnt)
        else:
            core_hrchy.parent(source_objects=self._facial_root_joint, target_parent=general_automation_grp)

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_file_path(self, file_path):
        """
        Sets the path used to import a file.
        Args:
            file_path (str): A file path to be imported. it overwrites the value even if an empty string.
        """
        if file_path is None:
            self.file_path = ""
        if not isinstance(file_path, str):
            logger.warning("Unable to set file path. Invalid data type was provided.")
            return
        self.file_path = file_path


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.modules.module_head as mod_head
    import gt.core.constraint as core_cnstr
    import gt.core.rigging as core_rigging
    import importlib

    importlib.reload(tools_rig_fmr)
    importlib.reload(core_cnstr)
    importlib.reload(core_rigging)

    a_face = ModuleMetaHumanFace()

    a_head = mod_head.ModuleHead()
    head_uuid = a_head.head_proxy.get_uuid()
    a_face.set_parent_uuid(head_uuid)
    a_face.set_file_path(
        file_path=r"R:\Rubicon\Plugins\GameFeatures\Game\Character\Common\Human\Bodies\Male\Rig\face_rig\face_rig_a.ma"
    )
    a_head.set_jaw_build_status(False)
    a_head.set_eyes_build_status(False)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_head)
    a_project.add_to_modules(a_face)
    a_project.build_proxy()

    # Transform Data for "C_headEnd":
    cmds.setAttr("C_headEnd.ty", 0.54)

    # Transform Data for "C_neck01":
    cmds.setAttr("C_neck01.ty", 20.44)
    cmds.setAttr("C_neck01.tz", -4.09)

    # Transform Data for "C_head":
    cmds.setAttr("C_head.ty", 27.37)
    cmds.setAttr("C_head.tz", -0.61)

    # Transform Data for "C_neck02":
    cmds.setAttr("C_neck02.ty", -1.26)
    cmds.setAttr("C_neck02.tz", -0.73)

    a_project.build_rig()
    # Show all
    cmds.viewFit(all=True)
