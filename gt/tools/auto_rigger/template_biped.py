"""
Auto Rigger Project Template for Biped Rigs
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_module_arm_biped import ModuleBipedArmRight, ModuleBipedArmLeft
from gt.tools.auto_rigger.rig_module_leg_biped import ModuleBipedLegRight, ModuleBipedLegLeft
from gt.tools.auto_rigger.rig_module_digit_biped import ModuleBipedFingersLeft, ModuleBipedFingersRight
from gt.tools.auto_rigger.rig_framework import RigProject, ModuleGeneric, Proxy
from gt.tools.auto_rigger.rig_module_spine import ModuleSpine
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_template_biped():
    """
    Creates a template project for a biped rig
    Returns:
        RigProject: A rig project containing modules used in a biped rig
    """
    biped_project = RigProject(name="Biped Character Template")

    spine = ModuleSpine()
    leg_lf = ModuleBipedLegLeft()
    leg_rt = ModuleBipedLegRight()
    arm_lf = ModuleBipedArmLeft()
    arm_rt = ModuleBipedArmRight()
    fingers_lf = ModuleBipedFingersLeft()
    fingers_rt = ModuleBipedFingersRight()

    # TODO TEMP @@@ ----------------------------------------------------------------------------------------------
    generic = ModuleGeneric(name="this is a temporary test module")
    generic.set_prefix("prefix")
    proxy_one = Proxy(name="named_proxy")
    proxy_two = Proxy()
    proxy_two.set_parent_uuid(proxy_one.get_uuid())
    print(proxy_two.get_parent_uuid())
    generic.add_to_proxies(proxy_one)
    generic.add_to_proxies(proxy_two)
    # TODO TEMP @@@ ----------------------------------------------------------------------------------------------

    spine_hip_uuid = spine.hip.get_uuid()
    leg_lf.set_parent_uuid(spine_hip_uuid)
    leg_rt.set_parent_uuid(spine_hip_uuid)
    spine_chest_uuid = spine.chest.get_uuid()
    arm_lf.set_parent_uuid(spine_chest_uuid)
    arm_rt.set_parent_uuid(spine_chest_uuid)
    wrist_lf_uuid = arm_lf.wrist.get_uuid()
    fingers_lf.set_parent_uuid(wrist_lf_uuid)
    wrist_rt_uuid = arm_rt.wrist.get_uuid()
    fingers_rt.set_parent_uuid(wrist_rt_uuid)

    biped_project.add_to_modules(spine)
    biped_project.add_to_modules(leg_lf)
    biped_project.add_to_modules(leg_rt)
    biped_project.add_to_modules(arm_lf)
    biped_project.add_to_modules(arm_rt)
    biped_project.add_to_modules(fingers_lf)
    biped_project.add_to_modules(fingers_rt)
    biped_project.add_to_modules(generic)  # TODO TEMP @@@ -------------------------------------------------------

    return biped_project


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    a_biped_project = create_template_biped()
    a_biped_project.build_proxy()
    a_biped_project.build_rig()
    #
    # # Modify Proxy
    # cmds.setAttr(f'rt_elbow.tz', -15)
    # cmds.setAttr(f'lf_knee.tz', 15)
    # cmds.setAttr(f'chest.ty', 10)
    #
    # # Re-build
    # print(a_biped_project.get_project_as_dict())
    # a_biped_project.read_data_from_scene()
    # print(a_biped_project.get_project_as_dict())
    # dictionary = a_biped_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # a_project2.build_proxy()

    # Frame all
    cmds.viewFit(all=True)
