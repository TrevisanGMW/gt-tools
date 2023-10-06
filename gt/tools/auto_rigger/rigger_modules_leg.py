"""
Auto Rigger Leg Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_framework import Proxy, ModuleGeneric
from gt.tools.auto_rigger.rigger_utils import find_proxy_with_uuid
from gt.utils.naming_utils import get_short_name
from gt.utils.color_utils import ColorConstants
from gt.utils.curve_utils import get_curve
from gt.utils import hierarchy_utils
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedLeg(ModuleGeneric):
    def __init__(self,
                 name="Leg",
                 prefix=None,
                 parent_uuid=None,
                 metadata=None):
        super().__init__(name=name, prefix=prefix, parent_uuid=parent_uuid, metadata=metadata)

        # Default Proxies
        self.hip = Proxy(name="hip")
        self.hip.set_position(y=84.5)
        self.hip.set_locator_scale(scale=0.4)

        self.knee = Proxy(name="knee")
        self.knee.set_curve(curve=get_curve('_proxy_joint_arrow'))
        self.knee.set_position(y=47.05)
        self.knee.set_locator_scale(scale=0.5)
        self.knee.add_meta_parent(line_parent=self.hip)

        self.ankle = Proxy(name="ankle")
        self.ankle.set_position(y=9.6)
        self.ankle.set_locator_scale(scale=0.4)
        self.ankle.add_meta_parent(line_parent=self.knee)

        self.ball = Proxy(name="ball")
        self.ball.set_position(z=13.1)
        self.ball.set_locator_scale(scale=0.4)
        self.ball.add_meta_parent(line_parent=self.ankle)

        self.toe = Proxy(name="toe")
        self.toe.set_position(z=23.4)
        self.toe.set_locator_scale(scale=0.4)
        self.toe.set_parent_uuid(uuid=self.ball.get_uuid())
        self.toe.set_parent_uuid_from_proxy(parent_proxy=self.ball)

        self.heel_pivot = Proxy(name="heelPivot")
        self.heel_pivot.set_locator_scale(scale=0.1)
        self.heel_pivot.add_meta_parent(line_parent=self.ankle)
        self.heel_pivot.add_color(rgb_color=ColorConstants.RigProxy.PIVOT)

        # Update Proxies
        self.proxies.extend([self.hip, self.knee, self.ankle, self.ball, self.toe, self.heel_pivot])

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig module is valid (can be used)
        """
        # TODO Other checks here
        return super().is_valid()

    def proxy_post(self):
        """ Proxy Post Overwrite (Called after proxy is created and parented """
        hip = find_proxy_with_uuid(self.hip.get_uuid())
        ankle = find_proxy_with_uuid(self.ankle.get_uuid())
        knee = find_proxy_with_uuid(self.knee.get_uuid())
        cmds.pointConstraint([hip, ankle], knee)

        ball = find_proxy_with_uuid(self.ball.get_uuid())
        print(ball)
        offset = cmds.listRelatives(ball, parent=True, typ="transform", fullPath=True) or []
        print(offset)
        ball_pivot_grp = cmds.group(empty=True, world=True, name=f'{str(get_short_name(ball))}_pivot')
        hierarchy_utils.parent(source_objects=offset, target_parent=ball_pivot_grp)

    def build_rig(self):
        print('"build_rig" executed.')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rigger_framework import RigProject
    a_leg = ModuleBipedLeg()
    a_project = RigProject()
    a_project.add_to_modules(a_leg)
    a_project.build_proxy()
    # get_curve('_proxy_joint_arrow').build()

    cmds.viewFit(all=True)
