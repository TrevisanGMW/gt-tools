"""
Auto Rigger Project Template for Biped Rigs
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_module_arm_biped import ModuleBipedArmRight, ModuleBipedArmLeft
from gt.tools.auto_rigger.rigger_module_leg_biped import ModuleBipedLegRight, ModuleBipedLegLeft
from gt.tools.auto_rigger.rigger_module_spine import ModuleSpine
from gt.tools.auto_rigger.rigger_framework import RigProject
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
    biped_project = RigProject()

    spine = ModuleSpine()
    leg_lf = ModuleBipedLegLeft()
    leg_rt = ModuleBipedLegRight()
    arm_lf = ModuleBipedArmLeft()
    arm_rt = ModuleBipedArmRight()

    spine_hip_uuid = spine.hip.get_uuid()
    leg_lf.set_parent_uuid(spine_hip_uuid)
    leg_rt.set_parent_uuid(spine_hip_uuid)
    spine_chest_uuid = spine.chest.get_uuid()
    arm_lf.set_parent_uuid(spine_chest_uuid)
    arm_rt.set_parent_uuid(spine_chest_uuid)

    biped_project.add_to_modules(spine)
    biped_project.add_to_modules(leg_lf)
    biped_project.add_to_modules(leg_rt)
    biped_project.add_to_modules(arm_lf)
    biped_project.add_to_modules(arm_rt)
    return biped_project


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    a_biped_project = create_template_biped()
    a_biped_project.build_proxy()
    print(a_biped_project)

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
