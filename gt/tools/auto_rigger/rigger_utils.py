"""
Auto Rigger Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attrs, connect_attr, add_attr
from gt.utils.curve_utils import get_curve, set_curve_width, create_connection_line
from gt.utils.color_utils import set_color_viewport, ColorConstants
from gt.utils.uuid_utils import find_object_with_uuid
from gt.utils.naming_utils import NamingConstants
from gt.utils.attr_utils import set_attr_state
from gt.utils.hierarchy_utils import parent
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerConstants:
    def __init__(self):
        """
        Constant values used by the auto rigging system.
        e.g. Attribute names, dictionary keys or initial values.
        """
    JOINT_ATTR_UUID = "jointUUID"
    PROXY_ATTR_UUID = "proxyUUID"
    PROXY_ATTR_SCALE = "locatorScale"
    PROXY_META_PARENT = "metaParentUUID"  # Metadata key, may be different from actual parent (e.g. for lines)
    PROXY_META_TYPE = "proxyType"  # Metadata key, used to recognize rigged proxies within modules
    PROXY_CLR = "color"  # Metadata key, describes color to be used instead of side setup.
    SEPARATOR_STD_SUFFIX = "Options"  # Standard (Std) Separator attribute name (a.k.a. header attribute)
    SEPARATOR_BEHAVIOR = "Behavior"
    ROOT_PROXY_ATTR = "proxyData"
    ROOT_RIG_ATTR = "rigData"


def find_proxy_with_uuid(uuid_string):
    """
    Return a proxy if the provided UUID is present in the attribute RiggerConstants.PROXY_ATTR_UUID
    Args:
        uuid_string (string): UUID to look for (if it matches, then the proxy is found)
    Returns:
        str or None: If found, the proxy with the matching UUID, otherwise None
    """
    return find_object_with_uuid(uuid_string=uuid_string,
                                 attr_name=RiggerConstants.PROXY_ATTR_UUID,
                                 obj_type="transform")


def parent_proxies(proxy_list):
    """
    Parent proxy elements (and their offset groups) according to their parent UUID
    Args:
        proxy_list (list): A list of Proxy objects to be parented.
                           UUID and parent UUID fields are required for the operation.
                           Objects without it will be ignored.
    """
    # Parent Joints
    for proxy in proxy_list:
        built_proxy = find_proxy_with_uuid(proxy.get_uuid())
        parent_proxy = find_proxy_with_uuid(proxy.get_parent_uuid())
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            offset = cmds.listRelatives(built_proxy, parent=True, fullPath=True)
            if offset:
                parent(source_objects=offset, target_parent=parent_proxy)


def create_proxy_visualization_lines(proxy_list, lines_parent=None):
    """
    Creates visualization lines according to the proxy UUID parent attribute.
    If a proxy meta parent is found, this is used instead.
    Args:
        proxy_list (list): A list of Proxy objects to be parented.
                           UUID and parent UUID fields are required for the operation.
                           Objects without it will be ignored.
        lines_parent (str, optional): If provided, it will automatically parent all generated elements to this object.
                                      Must exist and allow objects to be parented to it. e.g. "pSphere1"
    Returns:
        list: List of generated elements.
    """
    for proxy in proxy_list:
        built_proxy = find_proxy_with_uuid(proxy.get_uuid())
        parent_proxy = find_proxy_with_uuid(proxy.get_parent_uuid())

        # Check for Meta Parent - OVERWRITES parent!
        metadata = proxy.get_metadata()
        if metadata:
            meta_parent = metadata.get(RiggerConstants.PROXY_META_PARENT, None)
            if meta_parent:
                parent_proxy = find_proxy_with_uuid(meta_parent)

        # Create Line
        generated_objects = []
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            try:
                line_objects = create_connection_line(object_a=built_proxy,
                                                      object_b=parent_proxy) or []
                if lines_parent and cmds.objExists(lines_parent):
                    generated_objects += parent(source_objects=line_objects, target_parent=lines_parent) or []
                else:
                    generated_objects += line_objects
            except Exception as e:
                logger.debug(f'Failed to create visualization line. Issue: {str(e)}')


def create_root_curve(name="root", group_name="root"):
    """
    Creates a circle/arrow curve to be used as the root of a control rig or a proxy guide
    Args:
        name (str, optional): Name of the curve transform
        group_name (str, optional): Name of the parent group (transform) of the curve
    Returns:
        tuple: A tuple with the name of the curve transform and the name of the parent group
    """
    selection = cmds.ls(selection=True)
    root_crv = get_curve('_rig_root')
    root_crv.set_name(name=name)
    root_transform = root_crv.build()
    root_grp = cmds.group(empty=True, world=True, name=f"{group_name}_{NamingConstants.Suffix.GRP}")
    hide_lock_default_attrs(obj=root_grp)
    connect_attr(source_attr=f'{root_transform}.sy', target_attr_list=[f'{root_transform}.sx', f'{root_transform}.sz'])
    set_attr_state(obj_list=root_transform, attr_list=['sx', 'sz'], hidden=True)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigProxy.CENTER)
    cmds.parent(root_transform, root_grp)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f'Unable to restore initial selection. Issue: {str(e)}')
    return root_transform, root_grp


def create_proxy_root_curve():
    """
    Creates a curve to be used as the root of a proxy skeleton
    Returns:
        tuple: A tuple with the name of the curve transform and the name of the parent group
    """
    root_transform, root_group = create_root_curve(name="root", group_name="rigger_proxy")
    hide_lock_default_attrs(obj=root_transform, scale=False)
    add_separator_attr(target_object=root_transform, attr_name=f'proxy{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.ROOT_PROXY_ATTR, verbose=True)
    set_curve_width(obj_list=root_transform, line_width=2)
    return root_transform, root_group


def create_control_root_curve():
    """
    Creates a curve to be used as the root of a control rig skeleton
    Returns:
        tuple: A tuple with the name of the curve transform and the name of the parent group
    """
    root_transform, root_group = create_root_curve(name="root_ctrl", group_name="rig")
    add_separator_attr(target_object=root_transform, attr_name=f'rig{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.ROOT_RIG_ATTR, verbose=True)
    set_curve_width(obj_list=root_transform, line_width=3)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigControl.ROOT)
    return root_transform, root_group


def find_objects_with_attr(attr_name, obj_type="transform"):
    """
    Return object if provided UUID is present in it
    Args:
        attr_name (string): Name of the attribute where the UUID is stored.
        obj_type (optional, string): Type of objects to look for (default is "transform")
    Returns:
        str, None: If found, the object with a matching UUID, otherwise None
    """
    obj_list = cmds.ls(typ=obj_type, long=True) or []
    result_list = []
    for obj in obj_list:
        if cmds.objExists(f'{obj}.{attr_name}'):
            result_list.append(obj)
    return result_list


def get_proxy_offset(proxy_name):
    """
    Return the offset transform (parent) of the provided proxy object. If not found, it returns "None"
    Args:
        proxy_name (string): Name of the attribute where the UUID is stored.
    Returns:
        str, None: If found, the offset object (parent of the proxy), otherwise None
    """
    if not proxy_name or not cmds.objExists(proxy_name):
        logger.debug(f'Unable to find offset for "{str(proxy_name)}".')
        return
    offset_list = cmds.listRelatives(proxy_name, parent=True, typ="transform", fullPath=True) or []
    for offset in offset_list:
        return offset


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
    create_proxy_root_curve()
    cmds.viewFit(all=True)
