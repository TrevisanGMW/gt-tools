"""
Auto Rigger Leg Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_framework import Proxy, ModuleGeneric
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
        hip = Proxy(name="hip")
        hip.set_position(y=84.5)
        hip.set_locator_scale(scale=0.4)
        knee = Proxy(name="knee")
        knee.set_position(y=47.05)
        knee.set_locator_scale(scale=0.5)
        ankle = Proxy(name="ankle")
        ankle.set_position(y=9.6)
        ankle.set_locator_scale(scale=0.4)
        ball = Proxy(name="ball")
        ball.set_position(z=13.1)
        ball.set_locator_scale(scale=0.4)
        toe = Proxy(name="toe")
        toe.set_position(z=23.4)
        toe.set_locator_scale(scale=0.4)
        toe.set_parent_uuid(uuid=ball.get_uuid())
        toe.set_parent_uuid_from_proxy(parent_proxy=ball)
        heel_pivot = Proxy(name="heelPivot")
        heel_pivot.set_locator_scale(scale=0.1)
        self.proxies.extend([hip, knee, ankle, ball, toe, heel_pivot])

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig module is valid (can be used)
        """
        # TODO Other checks here
        return super().is_valid()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rigger_framework import RigProject
    a_leg = ModuleBipedLeg()
    a_project = RigProject()
    a_project.add_to_modules(a_leg)
    a_project.build_proxy()
