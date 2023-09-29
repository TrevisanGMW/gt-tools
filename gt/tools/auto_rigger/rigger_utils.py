"""
Auto Rigger Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attributes, connect_attr
from gt.utils.color_utils import set_color_viewport, ColorConstants
from gt.utils.uuid_utils import find_object_with_uuid
from gt.utils.naming_utils import NamingConstants
from gt.utils.attr_utils import set_attr_state
from gt.utils.hierarchy_utils import parent
from gt.utils.curve_utils import get_curve
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerConstants:
    def __init__(self):
        """
        Constant values used by all proxy elements.
        """
    JOINT_ATTR_UUID = "jointUUID"
    PROXY_ATTR_UUID = "proxyUUID"
    PROXY_ATTR_SCALE = "locatorScale"
    PROXY_MAIN_CRV = "proxy_main_crv"  # Main control that holds many proxies
    SEPARATOR_ATTR = "proxyPreferences"  # Locked attribute at the top of the proxy options


def parent_proxies(proxy_list):
    # Parent Joints
    for proxy in proxy_list:
        built_proxy = find_object_with_uuid(proxy.get_uuid(), RiggerConstants.PROXY_ATTR_UUID)
        parent_proxy = find_object_with_uuid(proxy.get_parent_uuid(), RiggerConstants.PROXY_ATTR_UUID)
        print(f'built_proxy: {built_proxy}')
        print(f'parent_proxy: {parent_proxy}')
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            offset = cmds.listRelatives(built_proxy, parent=True, fullPath=True)
            if offset:
                parent(source_objects=offset, target_parent=parent_proxy)


def create_root_curve(name="main", separator_name="options", top_group_name="rigger"):
    """

    """
    selection = cmds.ls(selection=True)
    root_crv = get_curve('_rig_root')
    root_crv.set_name(name=name)
    root_transform = root_crv.build()
    root_grp = cmds.group(empty=True, world=True, name=f"{top_group_name}_{NamingConstants.Suffix.GRP}")
    hide_lock_default_attributes(obj=root_grp)
    add_separator_attr(target_object=root_transform, attr_name=separator_name)
    connect_attr(source_attr=f'{root_transform}.sy', target_attr_list=[f'{root_transform}.sx', f'{root_transform}.sz'])
    hide_lock_default_attributes(obj=root_transform, scale=False)
    set_attr_state(obj_list=root_transform, attr_list=['sx', 'sz'], hidden=True)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigProxy.CENTER)
    cmds.parent(root_transform, root_grp)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f'Unable to restore initial selection. Issue: {str(e)}')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
