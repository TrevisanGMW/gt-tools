"""
Auto Rigger Arm Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_utils import RiggerConstants, find_objects_with_attr, find_proxy_node_from_uuid
from gt.utils.attr_utils import add_attr, hide_lock_default_attrs, set_attr_state, set_attr
from gt.tools.auto_rigger.rigger_framework import Proxy, ModuleGeneric
from gt.utils.naming_utils import get_short_name, NamingConstants
from gt.tools.auto_rigger.rigger_utils import get_proxy_offset
from gt.utils.transform_utils import match_translate, Vector3
from gt.utils.color_utils import ColorConstants
from gt.utils.curve_utils import get_curve
from gt.utils import hierarchy_utils
from gt.utils.node_utils import Node
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedArm(ModuleGeneric):
    def __init__(self,
                 name="Arm",
                 prefix=None,
                 parent_uuid=None,
                 metadata=None,
                 pos_offset=None):
        super().__init__(name=name, prefix=prefix, parent_uuid=parent_uuid, metadata=metadata)

        # Default Proxies
        self.clavicle = Proxy(name="clavicle")
        self.clavicle.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_clavicle = Vector3(x=3, y=130.4) + pos_offset
        self.clavicle.set_initial_position(xyz=pos_clavicle)
        self.clavicle.set_locator_scale(scale=0.4)
        self.clavicle.set_meta_type(value="clavicle")

        self.shoulder = Proxy(name="shoulder")
        pos_shoulder = Vector3(x=17.2, y=130.4) + pos_offset
        self.shoulder.set_initial_position(xyz=pos_shoulder)
        self.shoulder.set_locator_scale(scale=0.4)
        self.shoulder.set_parent_uuid(self.clavicle.get_uuid())
        self.shoulder.set_meta_type(value="shoulder")

        self.elbow = Proxy(name="elbow")
        self.elbow.set_curve(curve=get_curve('_proxy_joint_arrow_neg_z'))
        pos_elbow = Vector3(x=37.7, y=130.4) + pos_offset
        self.elbow.set_initial_position(xyz=pos_elbow)
        self.elbow.set_locator_scale(scale=0.5)
        self.elbow.add_meta_parent(line_parent=self.shoulder)
        self.elbow.set_meta_type(value="elbow")

        self.wrist = Proxy(name="wrist")
        self.wrist.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_wrist = Vector3(x=58.2, y=130.4) + pos_offset
        self.wrist.set_initial_position(xyz=pos_wrist)
        self.wrist.set_locator_scale(scale=0.4)
        self.wrist.add_meta_parent(line_parent=self.elbow)
        self.wrist.set_meta_type(value="wrist")

        # Update Proxies
        self.proxies = [self.clavicle, self.shoulder, self.elbow, self.wrist]

    def get_module_as_dict(self, **kwargs):
        """
        Overwrite to remove offset data from the export
        Args:
            kwargs: Key arguments, not used for anything
        """
        return super().get_module_as_dict(include_offset_data=False)

    def read_proxies_from_dict(self, proxy_dict):
        """
        Reads a proxy description dictionary and populates (after resetting) the proxies list with the dict proxies.
        Args:
            proxy_dict (dict): A proxy description dictionary. It must match an expected pattern for this to work:
                               Acceptable pattern: {"uuid_str": {<description>}}
                               "uuid_str" being the actual uuid string value of the proxy.
                               "<description>" being the output of the operation "proxy.get_proxy_as_dict()".
        """
        if not proxy_dict or not isinstance(proxy_dict, dict):
            logger.debug(f'Unable to read proxies from dictionary. Input must be a dictionary.')
            return
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.PROXY_META_TYPE)
                if meta_type == "clavicle":
                    self.clavicle.set_uuid(uuid)
                    self.clavicle.read_data_from_dict(proxy_dict=description)
                if meta_type == "shoulder":
                    self.shoulder.set_uuid(uuid)
                    self.shoulder.read_data_from_dict(proxy_dict=description)
                if meta_type == "elbow":
                    self.elbow.set_uuid(uuid)
                    self.elbow.read_data_from_dict(proxy_dict=description)
                if meta_type == "wrist":
                    self.wrist.set_uuid(uuid)
                    self.wrist.read_data_from_dict(proxy_dict=description)

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        is_valid = super().is_valid()  # Passthrough
        return is_valid

    def build_proxy(self):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        proxy = super().build_proxy()  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Creates leg proxy behavior through constraints and offsets.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.ROOT_PROXY_ATTR)
        clavicle = find_proxy_node_from_uuid(self.clavicle.get_uuid())
        shoulder = find_proxy_node_from_uuid(self.shoulder.get_uuid())
        elbow = find_proxy_node_from_uuid(self.elbow.get_uuid())
        wrist = find_proxy_node_from_uuid(self.wrist.get_uuid())

        self.clavicle.apply_offset_transform()
        self.shoulder.apply_offset_transform()
        self.elbow.apply_offset_transform()
        self.wrist.apply_offset_transform()

        # Shoulder -----------------------------------------------------------------------------------
        hide_lock_default_attrs(shoulder, translate=False)

        # Elbow  ---------------------------------------------------------------------------------
        elbow_tag = elbow.get_short_name()
        hide_lock_default_attrs(elbow, translate=False, rotate=False)

        # Elbow Setup
        elbow_offset = get_proxy_offset(elbow)

        elbow_pv_dir = cmds.spaceLocator(name=f'{elbow_tag}_poleVectorDir')[0]
        match_translate(source=elbow, target_list=elbow_pv_dir)
        cmds.move(0, 0, -10, elbow_pv_dir, relative=True)  # More it backwards (in front of the elbow)
        hierarchy_utils.parent(elbow_pv_dir, elbow)

        elbow_dir_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirParent_{NamingConstants.Suffix.LOC}')[0]
        elbow_aim_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirAim_{NamingConstants.Suffix.LOC}')[0]
        elbow_upvec_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirParentUp_{NamingConstants.Suffix.LOC}')[0]
        elbow_upvec_loc_grp = f'{elbow_tag}_dirParentUp_{NamingConstants.Suffix.GRP}'
        elbow_upvec_loc_grp = cmds.group(name=elbow_upvec_loc_grp, empty=True, world=True)

        elbow_dir_loc = Node(elbow_dir_loc)
        elbow_aim_loc = Node(elbow_aim_loc)
        elbow_upvec_loc = Node(elbow_upvec_loc)
        elbow_upvec_loc_grp = Node(elbow_upvec_loc_grp)

        # Hide Reference Elements
        hierarchy_utils.parent(elbow_aim_loc, elbow_dir_loc)
        hierarchy_utils.parent(elbow_dir_loc, root)
        hierarchy_utils.parent(elbow_upvec_loc_grp, root)
        hierarchy_utils.parent(elbow_upvec_loc, elbow_upvec_loc_grp)

        cmds.pointConstraint(shoulder, elbow_dir_loc)
        cmds.pointConstraint([wrist, shoulder], elbow_aim_loc)
        cmds.aimConstraint(wrist, elbow_dir_loc)
        cmds.pointConstraint(shoulder, elbow_upvec_loc_grp, skip=['x', 'z'])

        elbow_divide_node = cmds.createNode('multiplyDivide', name=f'{elbow_tag}_divide')
        cmds.setAttr(f'{elbow_divide_node}.operation', 2)  # Change operation to Divide
        cmds.setAttr(f'{elbow_divide_node}.input2X', -2)
        cmds.connectAttr(f'{wrist}.ty', f'{elbow_divide_node}.input1X')
        cmds.connectAttr(f'{elbow_divide_node}.outputX', f'{elbow_upvec_loc}.tx')


        cmds.pointConstraint(shoulder, elbow_dir_loc)
        cmds.pointConstraint([shoulder, wrist], elbow_aim_loc)

        cmds.connectAttr(f'{elbow_dir_loc}.rotate', f'{elbow_offset}.rotate')
        cmds.pointConstraint([wrist, shoulder], elbow_offset)

        cmds.aimConstraint(wrist, elbow_dir_loc, aimVector=(1, 0, 0), upVector=(1, 0, 0),
                           worldUpType='object', worldUpObject=str(elbow_upvec_loc))
        cmds.aimConstraint(elbow_aim_loc, elbow, aimVector=(0, 0, 1), upVector=(0, 1, 0),
                           worldUpType='none', skip=['y', 'z'])

        cmds.setAttr(f'{elbow}.tz', -0.01)

        # Elbow Limits and Locks
        cmds.setAttr(f'{elbow}.maxTransZLimit', -0.01)
        cmds.setAttr(f'{elbow}.maxTransZLimitEnable', True)

        set_attr_state(obj_list=str(elbow), attr_list="rotate", locked=True)

        # Elbow Hide
        set_attr(obj_list=[elbow_pv_dir, elbow_upvec_loc_grp, elbow_dir_loc],
                 attr_list="visibility", value=0)  # Set Visibility to Off
        set_attr(obj_list=[elbow_pv_dir, elbow_upvec_loc_grp, elbow_dir_loc],
                 attr_list="hiddenInOutliner", value=1)  # Set Outline Hidden to On

        #
        # # Ankle ----------------------------------------------------------------------------------
        # ankle_offset = get_proxy_offset(ankle)
        # add_attr(target_list=ankle.get_long_name(), attributes="followHip", attr_type='bool', default=True)
        # constraint = cmds.pointConstraint(hip, ankle_offset, skip='y')[0]
        # cmds.connectAttr(f'{ankle}.followHip', f'{constraint}.w0')
        # set_attr_state(obj_list=ankle, attr_list=["rx", "rz"], locked=True, hidden=True)
        #
        # # Ball -----------------------------------------------------------------------------------
        # ankle_tag = ankle.get_short_name()
        # ball_offset = get_proxy_offset(ball)
        # ball_driver = cmds.group(empty=True, world=True, name=f'{ankle_tag}_pivot')
        # ball_driver = hierarchy_utils.parent(source_objects=ball_driver, target_parent=root)[0]
        # ankle_pos = cmds.xform(ankle, q=True, ws=True, rp=True)
        # cmds.move(ankle_pos[0], ball_driver, moveX=True)
        # cmds.pointConstraint(ankle, ball_driver, maintainOffset=True, skip=['y'])
        # cmds.orientConstraint(ankle, ball_driver, maintainOffset=True, skip=['x', 'z'])
        # cmds.scaleConstraint(ankle, ball_driver, skip=['y'])
        # hierarchy_utils.parent(ball_offset, ball_driver)

        cmds.select(clear=True)

    def build_rig(self):
        super().build_rig()  # Passthrough


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rigger_framework import RigProject
    a_arm = ModuleBipedArm()
    a_project = RigProject()
    a_project.add_to_modules(a_arm)
    a_project.build_proxy()
    #
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_hip.tx', 10)
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_ankle.tz', 5)
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_knee.tz', 3)
    # print(a_project.get_project_as_dict())
    # a_project.read_data_from_scene()
    # print(a_project.get_project_as_dict())
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # a_project2.build_proxy()
    # Show all
    cmds.viewFit(all=True)
