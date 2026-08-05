"""
Auto Rigger Center of Mass Reference Module
"""

import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.transform as core_trans
import gt.core.hierarchy as core_hrchy
import gt.core.outliner as core_outlnr
import gt.core.naming as core_naming
import gt.core.material as core_mat
import gt.core.color as core_color
import gt.core.node as core_node
import gt.core.skin as core_skin
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleAnimMassReferences(tools_rig_frm.ModuleGeneric):
    __version__ = "0.1.3"
    icon = ui_res_lib.Icon.rigger_module_ref_mass
    allow_parenting = True
    allow_multiple = False

    default_shape = "_gear_pos_z"

    def __init__(self, name="COM References", prefix=None, suffix=None):
        """
        Initialize the ModuleAnimMassReferences module.

        Args:
            name (str): Name of the module instance. Defaults to "COM References".
            prefix (str or None): Optional prefix for naming conventions.
            suffix (str or None): Optional suffix for naming conventions.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.set_extra_callable_function(self._create_anim_references, order=tools_rig_frm.CodeData.Order.post_build)

        # Center of Mass Reference
        self.add_com_to_skeleton = False  # Adds a COM joint to skeleton so it gets imported in engine
        self.com_locator_scale = 35
        # Reference Objects ---------------------------------------------
        self.head = "C_head_JNT"
        self.thorax = "C_spine03_JNT"  # Chest FK
        self.abdomen = "C_hips_JNT"  # COG/Pelvis
        # Left Side
        self.left_arm_upper = "L_upperArm_JNT"
        self.left_arm_lower = "L_lowerArm_JNT"
        self.left_hand = "L_hand_JNT"
        self.left_hand_end = "L_middle03_JNT"  # Used to understand hand size
        self.left_leg_upper = "L_upperLeg_JNT"
        self.left_leg_lower = "L_lowerLeg_JNT"
        self.left_foot = "L_foot_JNT"
        self.left_ball = "L_ball_JNT"
        self.left_heel_pivot = "L_heel_pivot_grp"
        self.left_toe_pivot = "L_toe_pivot_grp"
        # Right Side
        self.right_arm_upper = "R_upperArm_JNT"
        self.right_arm_lower = "R_lowerArm_JNT"
        self.right_hand = "R_hand_JNT"
        self.right_hand_end = "R_middle03_JNT"  # Used to understand hand size
        self.right_leg_upper = "R_upperLeg_JNT"
        self.right_leg_lower = "R_lowerLeg_JNT"
        self.right_foot = "R_foot_JNT"
        self.right_ball = "R_ball_JNT"
        self.right_heel_pivot = "R_heel_pivot_grp"
        self.right_toe_pivot = "R_toe_pivot_grp"
        # Reference Weights ---------------------------------------------
        # Rounded according to # https://www.researchgate.net/figure/Human-body-mass-distribution_tbl2_303379664
        self.head_weight = 12.5
        self.thorax_weight = 33
        self.abdomen_weight = 25
        self.arm_upper_weight = 9
        self.arm_lower_weight = 5
        self.hand_weight = 2
        self.leg_upper_weight = 15
        self.leg_lower_weight = 7
        self.foot_weight = 3
        # Other Preferences
        self.viewport_color = (0, 1, 0)
        self.outliner_color = (0.5, 1, 0.21)

    def _create_anim_references(self):
        """
        Attempts to copy and connect attributes according to "self._reroute_attributes"
        Then attempts to set attributes according to "self._set_attr_values_dict"
        """
        if self._validate_parameters():
            body_mass_locators, heel_toe_locators = self._create_tracking_locators()

            # Organize Hierarchy/Groups
            setup_group = tools_rig_utils.find_setup_group()
            mass_reference_grp = core_hrchy.create_group(name=f"comReference")
            body_mass_locators_grp = core_hrchy.create_group(name=f"body_mass_locators_grp")
            heel_toe_locators_grp = core_hrchy.create_group(name=f"heel_toe_locators_grp")
            reference_joints_grp = core_hrchy.create_group(name=f"com_reference_joints_grp")
            reference_geo_grp = core_hrchy.create_group(name=f"com_reference_geo_grp")
            # Create Hierarchy
            core_hrchy.parent(source_objects=mass_reference_grp, target_parent=setup_group)
            core_hrchy.parent(source_objects=body_mass_locators_grp, target_parent=mass_reference_grp)
            core_hrchy.parent(source_objects=heel_toe_locators_grp, target_parent=mass_reference_grp)
            core_hrchy.parent(source_objects=reference_joints_grp, target_parent=mass_reference_grp)
            core_hrchy.parent(source_objects=reference_geo_grp, target_parent=mass_reference_grp)
            # Parent Locators
            core_hrchy.parent(source_objects=body_mass_locators, target_parent=body_mass_locators_grp)
            core_hrchy.parent(source_objects=heel_toe_locators, target_parent=heel_toe_locators_grp)
            core_color.set_color_outliner(mass_reference_grp, rgb_color=self.outliner_color)
            cmds.setAttr(f"{body_mass_locators_grp}.v", 0)
            cmds.setAttr(f"{heel_toe_locators_grp}.v", 0)
            cmds.setAttr(f"{reference_joints_grp}.v", 0)

            # Create COM Setup -----------------------------------------------
            com_loc, com_jnt, floor_com_jnt, ref_geometry = self._create_com_setup(body_mass_locators)  # Unpack
            core_hrchy.parent(source_objects=com_loc, target_parent=mass_reference_grp)
            core_outlnr.reorder_front(target_list=com_loc)
            core_color.set_color_outliner(obj_list=com_loc, rgb_color=self.outliner_color)
            core_hrchy.parent(source_objects=[com_jnt, floor_com_jnt], target_parent=reference_joints_grp)
            core_hrchy.parent(source_objects=ref_geometry, target_parent=reference_geo_grp)
            if self.add_com_to_skeleton:
                skeleton_grp = tools_rig_utils.find_skeleton_group()
                # Move COM joint to skeleton group
                core_hrchy.parent(source_objects=com_jnt, target_parent=skeleton_grp)
                # In case the module is parented, use the parent (e.g. root module)
                module_parent_jnt = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
                if module_parent_jnt:
                    core_hrchy.parent(source_objects=com_jnt, target_parent=module_parent_jnt)

            # Create Floor Setup ----------------------------------------------
            floor_joints, plane = self._create_floor_setup(heel_toe_locators)
            core_hrchy.parent(source_objects=floor_joints, target_parent=reference_joints_grp)
            core_hrchy.parent(source_objects=plane, target_parent=reference_geo_grp)

    def _create_tracking_locators(self):
        """
        Creates the reference locators used to define the character floor and center of gravity
        Returns:
            tuple: A tuple with two lists, first is a list of locators used to calculate the mass.
                   Second is a list of locators used to determine the start and end of the foot.
        """
        body_mass_locators = []
        heel_toe_locators = []
        basic_refs = {"head": self.head, "thorax": self.thorax, "abdomen": self.abdomen}
        # Basic Refs (Same Transforms) --------------------------------
        for name, obj_path in basic_refs.items():
            loc = cmds.spaceLocator(name=f"{name}_massRef_LOC")[0]
            core_trans.match_translate(source=obj_path, target_list=loc)
            body_mass_locators.append(loc)
            core_cnstr.constraint_targets(
                source_driver=obj_path,
                target_driven=loc,
                maintain_offset=False,
            )

        # Arms ------------------------------------
        arms = {
            "L": (self.left_arm_upper, self.left_arm_lower, self.left_hand, self.left_hand_end),
            "R": (self.right_arm_upper, self.right_arm_lower, self.right_hand, self.right_hand_end),
        }
        for side, arm_data in arms.items():
            arm_upper, arm_lower, hand, hand_end = arm_data  # Unpack
            # Create Locators
            upper_arm_loc = cmds.spaceLocator(name=f"{side}_upperArm_massRef_LOC")[0]
            lower_arm_loc = cmds.spaceLocator(name=f"{side}_lowerArm_massRef_LOC")[0]
            hand_loc = cmds.spaceLocator(name=f"{side}_hand_massRef_LOC")[0]
            # Position Locators
            core_trans.set_equidistant_transforms(start=arm_upper, end=arm_lower, target_list=upper_arm_loc)
            core_trans.set_equidistant_transforms(start=arm_lower, end=hand, target_list=lower_arm_loc)
            core_trans.match_transform(source=hand, target_list=hand_loc)
            hand_pos_constraint = core_cnstr.constraint_targets(
                source_driver=[hand, hand_end],
                target_driven=hand_loc,
                constraint_type=core_cnstr.ConstraintTypes.POINT,
                maintain_offset=False,
            )[0]
            cmds.setAttr(f"{hand_pos_constraint}.w1", 0.4)
            cmds.delete(hand_pos_constraint)
            # Constraint Locators
            core_cnstr.constraint_targets(
                source_driver=arm_upper,
                target_driven=upper_arm_loc,
                maintain_offset=True,
            )
            core_cnstr.constraint_targets(
                source_driver=arm_lower,
                target_driven=lower_arm_loc,
                maintain_offset=True,
            )
            core_cnstr.constraint_targets(
                source_driver=hand,
                target_driven=hand_loc,
                maintain_offset=True,
            )
            # Add Locators
            body_mass_locators.append(upper_arm_loc)
            body_mass_locators.append(lower_arm_loc)
            body_mass_locators.append(hand_loc)

        # Arms ------------------------------------
        legs = {
            "L": (
                self.left_leg_upper,
                self.left_leg_lower,
                self.left_foot,
                self.left_ball,
                self.left_heel_pivot,
                self.left_toe_pivot,
            ),
            "R": (
                self.right_leg_upper,
                self.right_leg_lower,
                self.right_foot,
                self.right_ball,
                self.right_heel_pivot,
                self.right_toe_pivot,
            ),
        }

        for side, leg_data in legs.items():
            leg_upper, leg_lower, foot, ball, heel_pivot, toe_pivot = leg_data  # Unpack
            # Create Locators
            upper_leg_loc = cmds.spaceLocator(name=f"{side}_upperLeg_massRef_LOC")[0]
            lower_leg_loc = cmds.spaceLocator(name=f"{side}_lowerLeg_massRef_LOC")[0]
            foot_loc = cmds.spaceLocator(name=f"{side}_foot_massRef_LOC")[0]
            heel_loc = cmds.spaceLocator(name=f"{side}_heel_massRef_LOC")[0]
            toe_loc = cmds.spaceLocator(name=f"{side}_toe_massRef_LOC")[0]
            # Position Locators
            core_trans.set_equidistant_transforms(start=leg_upper, end=leg_lower, target_list=upper_leg_loc)
            core_trans.set_equidistant_transforms(start=leg_lower, end=foot, target_list=lower_leg_loc)
            core_trans.match_transform(source=ball, target_list=foot_loc)
            foot_pos_constraint = core_cnstr.constraint_targets(
                source_driver=[foot, toe_pivot],
                target_driven=foot_loc,
                constraint_type=core_cnstr.ConstraintTypes.POINT,
                maintain_offset=False,
                skip="y",
            )[0]
            cmds.setAttr(f"{foot_pos_constraint}.w1", 0.4)
            cmds.delete(foot_pos_constraint)
            heel_pos_constraint = core_cnstr.constraint_targets(
                source_driver=heel_pivot,
                target_driven=heel_loc,
                constraint_type=core_cnstr.ConstraintTypes.POINT,
                maintain_offset=False,
                skip="y",
            )[0]
            cmds.delete(heel_pos_constraint)
            toe_pos_constraint = core_cnstr.constraint_targets(
                source_driver=toe_pivot,
                target_driven=toe_loc,
                constraint_type=core_cnstr.ConstraintTypes.POINT,
                maintain_offset=False,
                skip="y",
            )[0]
            cmds.delete(toe_pos_constraint)
            # Constraint Locators
            core_cnstr.constraint_targets(
                source_driver=leg_upper,
                target_driven=upper_leg_loc,
                maintain_offset=True,
            )
            core_cnstr.constraint_targets(
                source_driver=leg_lower,
                target_driven=lower_leg_loc,
                maintain_offset=True,
            )
            core_cnstr.constraint_targets(
                source_driver=foot,
                target_driven=foot_loc,
                maintain_offset=True,
            )
            core_cnstr.constraint_targets(
                source_driver=foot,
                target_driven=heel_loc,
                maintain_offset=True,
            )
            core_cnstr.constraint_targets(
                source_driver=ball,
                target_driven=toe_loc,
                maintain_offset=True,
            )
            # Add Locators to Lists
            body_mass_locators.append(upper_leg_loc)
            body_mass_locators.append(lower_leg_loc)
            body_mass_locators.append(foot_loc)
            heel_toe_locators.append(heel_loc)
            heel_toe_locators.append(toe_loc)

        # Define Locators Look -----------------------------
        for loc in body_mass_locators:
            self._define_loc_shape_look(loc)
        for loc in heel_toe_locators:
            self._define_loc_shape_look(loc, scale=1)
        return body_mass_locators, heel_toe_locators

    def _create_com_setup(self, body_mass_locators):
        """
        Creates the center of mass setup.
        Args:
            body_mass_locators (list): A list of locators used to determine the center of mass.
        Returns:
            tuple: A tuple with the path to the created locator and the created reference mesh.
        """
        loc = cmds.spaceLocator(name=f"com_LOC")[0]
        mass_constraint = cmds.pointConstraint(body_mass_locators, loc)[0]
        self._define_loc_shape_look(loc, scale=self.com_locator_scale)
        # Set Center of Mass values
        cmds.setAttr(f"{mass_constraint}.w0", self.head_weight)
        cmds.setAttr(f"{mass_constraint}.w1", self.thorax_weight)
        cmds.setAttr(f"{mass_constraint}.w2", self.abdomen_weight)
        cmds.setAttr(f"{mass_constraint}.w3", self.arm_upper_weight)
        cmds.setAttr(f"{mass_constraint}.w4", self.arm_lower_weight)
        cmds.setAttr(f"{mass_constraint}.w5", self.hand_weight)
        cmds.setAttr(f"{mass_constraint}.w6", self.arm_upper_weight)
        cmds.setAttr(f"{mass_constraint}.w7", self.arm_lower_weight)
        cmds.setAttr(f"{mass_constraint}.w8", self.hand_weight)
        cmds.setAttr(f"{mass_constraint}.w9", self.leg_upper_weight)
        cmds.setAttr(f"{mass_constraint}.w10", self.leg_lower_weight)
        cmds.setAttr(f"{mass_constraint}.w11", self.foot_weight)
        cmds.setAttr(f"{mass_constraint}.w12", self.leg_upper_weight)
        cmds.setAttr(f"{mass_constraint}.w13", self.leg_lower_weight)
        cmds.setAttr(f"{mass_constraint}.w14", self.foot_weight)
        # Create com floor reference geometry
        cylinder = cmds.polyCylinder(
            subdivisionsAxis=6,
            subdivisionsHeight=1,
            subdivisionsCaps=0,
            createUVs=0,
            name="com_reference_GEO",
            radius=0.8,
            constructionHistory=False,
        )[0]
        cmds.delete(f"{cylinder}.f[7]")  # Top Cap
        cmds.delete(f"{cylinder}.f[6]")  # Bottom Cap
        position_y_top = cmds.xform(f"{cylinder}.vtx[6]", query=True, worldSpace=True, translation=True)[1]
        position_y_bottom = cmds.xform(f"{cylinder}.vtx[0]", query=True, worldSpace=True, translation=True)[1]
        cmds.polySoftEdge(cylinder, angle=180, ch=False)
        # Shrink Top
        top_scale = 0.8
        cmds.scale(top_scale, top_scale, top_scale, f"{cylinder}.vtx[6:11]", pivot=(0, position_y_top, 0))

        com_jnt = core_node.create_node(node_type="joint", name="com_JNT")
        cmds.setAttr(f"{com_jnt}.ty", position_y_top)
        cmds.setAttr(f"{com_jnt}.radius", 0.1)
        floor_com_jnt = core_node.create_node(node_type="joint", name="com_floor_JNT")
        cmds.setAttr(f"{floor_com_jnt}.ty", position_y_bottom)
        cmds.setAttr(f"{floor_com_jnt}.radius", 0.1)
        core_skin.bind_skin(joints=[com_jnt, floor_com_jnt], objects=cylinder, maximum_influences=1)
        cmds.setAttr(f"{floor_com_jnt}.ty", 0)

        mat_name = f"{core_naming.NamingConstants.Prefix.MAT}_CenterOfMass_Tube"
        mat_name = core_mat.assign_material(obj_list=cylinder, rgb_color=(0, 1, 0), material_name=mat_name)

        # Constraint joints
        cmds.pointConstraint(loc, com_jnt)
        cmds.pointConstraint(loc, floor_com_jnt, skip="y")

        # Make geo a reference
        cmds.setAttr(f"{cylinder}.overrideEnabled", 1)
        cmds.setAttr(f"{cylinder}.overrideDisplayType", 2)

        return loc, com_jnt, floor_com_jnt, cylinder

    @staticmethod
    def _create_floor_setup(heel_toe_locators):
        """
        Creates the center of mass floor setup.
        Args:
            heel_toe_locators (list): A list with two locators determining the start and end of the foot.
        Returns:
            tuple: A tuple with a list of created
        """
        left_heel_loc, left_toe_loc, right_heel_loc, right_toe_loc = heel_toe_locators  # Unpack
        plane = cmds.polyPlane(width=2, height=2, sx=1, sy=1, createUVs=0, name="floor_reference_GEO")[0]

        left_heel_jnt = core_node.create_node(node_type="joint", name="left_heel_floor_JNT")
        left_toe_jnt = core_node.create_node(node_type="joint", name="left_toe_floor_JNT")
        right_heel_jnt = core_node.create_node(node_type="joint", name="right_heel_floor_JNT")
        right_toe_jnt = core_node.create_node(node_type="joint", name="right_toe_floor_JNT")
        # Pose Joints
        cmds.setAttr(f"{left_heel_jnt}.tx", 1)
        cmds.setAttr(f"{left_heel_jnt}.tz", -1)
        cmds.setAttr(f"{left_toe_jnt}.tx", 1)
        cmds.setAttr(f"{left_toe_jnt}.tz", 1)
        cmds.setAttr(f"{right_heel_jnt}.tx", -1)
        cmds.setAttr(f"{right_heel_jnt}.tz", -1)
        cmds.setAttr(f"{right_toe_jnt}.tx", -1)
        cmds.setAttr(f"{right_toe_jnt}.tz", 1)
        floor_joints = [left_heel_jnt, left_toe_jnt, right_heel_jnt, right_toe_jnt]
        for jnt in floor_joints:
            cmds.setAttr(f"{jnt}.radius", 0.1)
        core_skin.bind_skin(joints=floor_joints, objects=plane, maximum_influences=1)

        mat_name = f"{core_naming.NamingConstants.Prefix.MAT}_CenterOfMass_Floor"
        mat_name = core_mat.assign_material(obj_list=plane, rgb_color=(0, 0, 1), material_name=mat_name)

        cmds.pointConstraint(left_heel_loc, left_heel_jnt, skip="y")
        cmds.pointConstraint(left_toe_loc, left_toe_jnt, skip="y")
        cmds.pointConstraint(right_heel_loc, right_heel_jnt, skip="y")
        cmds.pointConstraint(right_toe_loc, right_toe_jnt, skip="y")

        # Make geo a reference
        cmds.setAttr(f"{plane}.overrideEnabled", 1)
        cmds.setAttr(f"{plane}.overrideDisplayType", 2)

        return floor_joints, plane

    def _define_loc_shape_look(self, loc_transform, scale=7):
        """
        Adjusts the provided locator to match a unified look.
        This is done by setting the local scale and color to a predefined value.
        Args:
        loc_transform (str): The name or path of the locator transform node.
        scale (int, optional): Uniform scale value applied to the locator shapes.
        """
        for shape in cmds.listRelatives(loc_transform, shapes=True):
            scale_attrs = [f"{shape}.localScaleX", f"{shape}.localScaleY", f"{shape}.localScaleZ"]
            for scale_attr in scale_attrs:
                cmds.setAttr(scale_attr, scale)
        core_color.set_color_viewport(loc_transform, rgb_color=self.viewport_color)

    def _validate_parameters(self):
        """
        Checks if the provided elements are available in the scene.
        In case something is missing this module operation is cancelled.
        Returns:
            bool: True if valid, False otherwise.
        """
        required_elements = [
            self.head,
            self.thorax,
            self.abdomen,
            self.left_arm_upper,
            self.left_arm_lower,
            self.left_hand,
            self.left_hand_end,
            self.left_leg_upper,
            self.left_leg_lower,
            self.left_foot,
            self.left_ball,
            self.left_heel_pivot,
            self.right_arm_upper,
            self.right_arm_lower,
            self.right_hand,
            self.right_hand_end,
            self.right_leg_upper,
            self.right_leg_lower,
            self.right_foot,
            self.right_ball,
            self.right_heel_pivot,
        ]
        is_valid = True
        for obj in required_elements:
            if not obj or not cmds.objExists(obj):
                logger.warning(f"Biped Animation Reference Module cannot be build due to missing element: {obj}")
                is_valid = False
        return is_valid


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from gt.tools.auto_rigger.rig_framework import RigProject, ModuleGeneric

    # Reload ---------------------------------------------------------------------------------------------
    import gt.tools.auto_rigger.modules.module_ref_mass as module_mass_refs
    import gt.tools.auto_rigger.templates.template_biped as template_biped
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import importlib

    importlib.reload(tools_rig_fmr)
    importlib.reload(module_mass_refs)
    importlib.reload(tools_rig_utils)

    # Reset Scene -----------------------------------------------------------------------------------------
    cmds.file(new=True, force=True)

    # Create Test Modules ---------------------------------------------------------------------------------
    an_anim_ref_mod = ModuleAnimMassReferences()

    # Configure Modules -----------------------------------------------------------------------------------

    # Create Project and Build ----------------------------------------------------------------------------
    a_biped_project = template_biped.create_template_biped()
    a_biped_project.add_to_modules(an_anim_ref_mod)

    # Build  ----------------------------------------------------------------------------------------------
    a_biped_project.build_proxy()
    a_biped_project.read_data_from_scene()
    project_as_dict = a_biped_project.get_project_as_dict()
    a_biped_project.build_rig()

    # # Rebuild --------------------------------------------------------------------------------------------
    # cmds.file(new=True, force=True)
    # a_2nd_project = RigProject()
    # a_2nd_project.read_data_from_dict(project_as_dict)
    # a_2nd_project.build_proxy()
    # create_test_cubes()
    # a_2nd_project.build_rig()

    cmds.setAttr(f"skeleton.v", 1)

    # Frame all
    cmds.viewFit(all=True)
