"""
Auto Rigger Base Framework
github.com/TrevisanGMW/gt-tools

RigProject > Module > Proxy > Joint/Control

Rigging Steps:
    Proxy:
        1: build_proxy
        2: build_proxy_setup
    Rig:
        3: build_skeleton_joints
        4: build_skeleton_hierarchy
        5: build_rig
        6: build_rig_post
"""
from gt.tools.auto_rigger.rig_utils import find_joint_from_uuid, get_proxy_offset, RiggerConstants, add_driver_to_joint
from gt.tools.auto_rigger.rig_utils import parent_proxies, create_proxy_root_curve, create_proxy_visualization_lines
from gt.tools.auto_rigger.rig_utils import find_skeleton_group, create_direction_curve, get_meta_purpose_from_dict
from gt.tools.auto_rigger.rig_utils import find_driver_from_uuid, find_proxy_from_uuid, create_control_root_curve
from gt.tools.auto_rigger.rig_utils import create_utility_groups, create_root_group, find_proxy_root_group
from gt.utils.attr_utils import add_separator_attr, set_attr, add_attr, list_user_defined_attr, get_attr
from gt.utils.uuid_utils import add_uuid_attr, is_uuid_valid, is_short_uuid_valid, generate_uuid
from gt.utils.color_utils import add_side_color_setup, ColorConstants, set_color_viewport
from gt.utils.string_utils import remove_prefix, camel_case_split, remove_suffix
from gt.utils.transform_utils import Transform, match_translate, match_rotate
from gt.utils.curve_utils import Curve, get_curve, add_shape_scale_cluster
from gt.utils.iterable_utils import get_highest_int_from_str_list
from gt.utils.naming_utils import NamingConstants, get_long_name
from gt.utils.uuid_utils import get_object_from_uuid_attr
from gt.utils.control_utils import add_snapping_shape
from gt.utils.node_utils import create_node, Node
from gt.utils.joint_utils import orient_joint
from gt.utils import hierarchy_utils
from gt.ui import resource_library
from dataclasses import dataclass
import maya.cmds as cmds
import logging
import re


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class ProxyData:
    """
    A proxy data class used as the proxy response for when the proxy is built.
    """
    name: str  # Long name of the generated proxy (full Maya path)
    offset: str  # Name of the proxy offset (parent of the proxy)
    setup: tuple  # Name of the proxy setup items (rig setup items)
    uuid: str  # Proxy UUID (Unique string pointing to generated proxy) - Not Maya UUID

    def __repr__(self):
        """
        String conversion returns the name of the proxy
        Returns:
            str: Proxy long name.
        """
        return self.name

    def get_short_name(self):
        """
        Gets the short version of the proxy name (default name is its long name)
        Note, this name might not be unique
        Returns:
            str: Short name of the proxy (short version of self.name) - Last name after "|" characters
        """
        from gt.utils.naming_utils import get_short_name
        return get_short_name(self.name)

    def get_long_name(self):
        """
        Gets the long version of the proxy name.
        Returns:
            str: Long name of the proxy. (a.k.a. Full Path)
        """
        return self.name

    def get_offset(self):
        """
        Gets the long version of the offset proxy group.
        Returns:
            str: Long name of the proxy group. (a.k.a. Full Path)
        """
        return self.offset

    def get_setup(self):
        """
        Gets the setup items tuple from the proxy data. This is a list of objects used to set up the proxy. (rig setup)
        Returns:
            tuple: A tuple with strings (full paths to the rig elements)
        """
        return self.setup

    def get_uuid(self):
        """
        Gets the proxy UUID
        Returns:
            str: Proxy UUID string
        """
        return self.uuid


class OrientationData:
    """
    OrientationData object.
    """
    class Methods:
        """
        List of recognized/accepted methods to apply
        """
        automatic = "automatic"  # Uses the "orient_joint" function to orient joints.
        inherit = "inherit"  # Inherits the joint orientation from the proxy used to generate it.
        world = "world"  # Orients the joint to the world.

    def __init__(self, method=Methods.automatic,
                 aim_axis=(1, 0, 0),
                 up_axis=(0, 1, 0),
                 up_dir=(0, 1, 0)):
        """
        Initializes an OrientationData object.
        Args:
            aim_axis (tuple, optional): The axis the joints should aim at in XYZ. Defaults to X+ (1, 0, 0).
                                        Commonly used as twist joint (aims towards its child)
            up_axis (tuple, optional): The axis pointing upwards for the joints. Defaults to (0, 1, 0).
            up_dir (tuple, optional): The up direction vector. Defaults to (0, 1, 0).
        """
        self.method = None
        self.aim_axis = None
        self.up_axis = None
        self.up_dir = None
        self.set_method(method)
        self.set_aim_axis(aim_axis)
        self.set_up_axis(up_axis)
        self.set_up_dir(up_dir)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_method(self, method):
        """
        This will define how the values are applied or not applied.
        Args:
            method (str, None): Orientation method. This will define how the values are applied or not applied.
        """
        if not method or not isinstance(method, str):
            logger.debug('Unable to set orientation. Method must be a string.')
            return
        available_methods = self.get_available_methods()
        if method not in available_methods:
            valid_orientations_str = '\", "'.join(available_methods)
            logger.debug(
                f'Unable to set orientation. Input must be a recognized string: "{valid_orientations_str}".')
            return
        if method:
            self.method = method

    def set_aim_axis(self, aim_axis):
        """
        Sets the aim axis for the orientation data
        Args:
            aim_axis (tuple, optional): The axis the joints should aim at in XYZ. e.g. for X+ (1, 0, 0).
                                        Commonly used as twist joint (aims towards its child)
        """
        if not aim_axis or not isinstance(aim_axis, tuple) or not len(aim_axis) == 3:
            logger.debug(f'Unable to set aim axis. Input must be a tuple/list with 3 digits.')
            return
        self.aim_axis = aim_axis

    def set_up_axis(self, up_axis):
        """
        Sets the up axis for the orientation data (determines if positive or negative for example)
        Args:
            up_axis (tuple, optional): The axis pointing upwards for the joints in XYZ.
        """
        if not up_axis or not isinstance(up_axis, tuple) or not len(up_axis) == 3:
            logger.debug(f'Unable to set up axis. Input must be a tuple/list with 3 digits.')
            return
        self.up_axis = up_axis

    def set_up_dir(self, up_dir):
        """
        Sets the up direction for the orientation data
        Args:
            up_dir (tuple, optional): The axis pointing upwards for the joints in XYZ.
        """
        if not up_dir or not isinstance(up_dir, tuple) or not len(up_dir) == 3:
            logger.debug(f'Unable to set up direction. Input must be a tuple/list with 3 digits.')
            return
        self.up_dir = up_dir

    def set_data_from_dict(self, orient_dict):
        """
        Gets the orientation data as a dictionary.
        Args:
            orient_dict (dict): A dictionary describing the desired orientation.
        """
        if not orient_dict or not isinstance(orient_dict, dict):
            return

        _method = orient_dict.get("method")
        if _method:
            self.set_method(_method)

        _aim_axis = orient_dict.get("aim_axis")
        if _aim_axis:
            self.set_aim_axis(_aim_axis)

        _up_axis = orient_dict.get("up_axis")
        if _up_axis:
            self.set_up_axis(_up_axis)

        _up_dir = orient_dict.get("up_dir")
        if _up_dir:
            self.set_up_dir(_up_dir)

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_method(self):
        """
        Gets the aim axis (twist) from this orientation data object.
        Returns:
            str: The method defined for this orientation.
        """
        return self.method

    def get_aim_axis(self):
        """
        Gets the aim axis (twist) from this orientation data object.
        Returns:
            tuple: A tuple with three numeric values, (X, Y, Z)
        """
        return self.aim_axis

    def get_up_axis(self):
        """
        Gets the up axis from this orientation data object.
        Returns:
            tuple: A tuple with three numeric values, (X, Y, Z)
        """
        return self.up_axis

    def get_up_dir(self):
        """
        Gets the up direction from this orientation data object.
        Returns:
            tuple: A tuple with three numeric values, (X, Y, Z)
        """
        return self.up_dir

    def get_available_methods(self):
        """
        Gets a list of all available methods. These are the same as the attributes under the subclass "Methods"
        Returns:
            list: A list of available methods (these are strings)
                  Further description for each method can be found under the "Methods" class.
        """
        methods = []
        attrs = vars(self.Methods)
        attrs_keys = [attr for attr in attrs if not (attr.startswith('__') and attr.endswith('__'))]
        for key in attrs_keys:
            methods.append(getattr(self.Methods, key))
        return methods

    def get_data_as_dict(self):
        """
        Gets the orientation data as a dictionary.
        Returns:
            dict: A dictionary containing the entire orientation description.
        """
        _data = {"method": self.method,
                 "aim_axis": self.aim_axis,
                 "up_axis": self.up_axis,
                 "up_dir": self.up_dir}
        return _data

    # -------------------------------------------------- Utils --------------------------------------------------
    def __repr__(self):
        """
        String conversion returns the orientation data
        Returns:
            str: Formatted orientation data.
        """
        return (f'Method: {str(self.method)} ('
                f'aim_axis={str(self.aim_axis)}, '
                f'up_axis={str(self.up_axis)}, '
                f'up_dir={str(self.up_dir)})')

    def apply_automatic_orientation(self, joint_list):
        """
        Orients the provided joints, as long as the defined method is set to automatic.
        Args:
            joint_list (list): A list of joints to be oriented.
        """
        if not self.get_method() == self.Methods.automatic:
            logger.debug(f'Method not set to automatic. Auto orientation call was ignored.')
            return
        orient_joint(joint_list, aim_axis=self.aim_axis, up_axis=self.up_axis, up_dir=self.up_dir)


class Proxy:
    def __init__(self, name=None, uuid=None):

        # Default Values
        self.name = "proxy"
        self.transform = None
        self.offset_transform = None
        self.curve = get_curve('_proxy_joint')
        self.curve.set_name(name=self.name)
        self.uuid = generate_uuid(remove_dashes=True)
        self.parent_uuid = None
        self.locator_scale = 1  # 100% - Initial curve scale
        self.attr_dict = {}
        self.metadata = None

        if name:
            self.set_name(name)
        if uuid:
            self.set_uuid(uuid)

    def is_valid(self):
        """
        Checks if the current proxy element is valid
        """
        if not self.name:
            logger.warning('Invalid proxy object. Missing name.')
            return False
        if not self.curve:
            logger.warning('Invalid proxy object. Missing curve.')
            return False
        return True

    def build(self, prefix=None, suffix=None, apply_transforms=False, optimized=False):
        """
        Builds a proxy object.
        Args:
            prefix (str, optional): If provided, this prefix will be added to the proxy when it's created.
            suffix (str, optional): If provided, this suffix will be added to the proxy when it's created.
            apply_transforms (bool, optional): If True, the creation of the proxy will apply transform values.
                                               Used by modules to only apply transforms after setup. (post script)
            optimized (bool, optional): If True, the module will skip display operations, such as curve creation,
                                        the addition of a snapping shape or the scale cluster and others.
                                        Useful for when building a rig without adjusting the proxy.
        Returns:
            ProxyData: Name of the proxy that was generated/built.
        """
        if not self.is_valid():
            logger.warning(f'Unable to build proxy. Invalid proxy object.')
            return

        name = self.name
        if prefix and isinstance(prefix, str):
            name = f'{prefix}_{name}'
            self.curve.set_name(name)
        if suffix and isinstance(suffix, str):
            name = f'{name}_{suffix}'
            self.curve.set_name(name)

        proxy_offset = cmds.group(name=f'{name}_{NamingConstants.Suffix.OFFSET}', world=True, empty=True)
        if optimized:
            proxy_crv = cmds.group(name=self.curve.get_name(), world=True, empty=True)
        else:
            proxy_crv = self.curve.build()
            add_snapping_shape(proxy_crv)
        if prefix:
            self.curve.set_name(self.name)  # Restore name without prefix
        proxy_crv = cmds.parent(proxy_crv, proxy_offset)[0]
        proxy_offset = get_long_name(proxy_offset)
        proxy_crv = get_long_name(proxy_crv)

        add_separator_attr(target_object=proxy_crv, attr_name=f'proxy{RiggerConstants.SEPARATOR_OPTIONS.title()}')
        uuid_attrs = add_uuid_attr(obj_list=proxy_crv,
                                   attr_name=RiggerConstants.ATTR_PROXY_UUID,
                                   set_initial_uuid_value=False)
        scale_attr = add_attr(obj_list=proxy_crv, attributes=RiggerConstants.ATTR_PROXY_SCALE, default=1) or []
        loc_scale_cluster = None
        if not optimized and scale_attr and len(scale_attr) == 1:
            scale_attr = scale_attr[0]
            loc_scale_cluster = add_shape_scale_cluster(proxy_crv, scale_driver_attr=scale_attr)
        for attr in uuid_attrs:
            set_attr(attribute_path=attr, value=self.uuid)
        # Set Transforms
        if self.offset_transform and apply_transforms:
            self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if self.transform and apply_transforms:
            self.transform.apply_transform(target_object=proxy_crv, world_space=True)
        # Set Locator Scale
        if self.locator_scale and scale_attr:
            set_attr(scale_attr, self.locator_scale)

        return ProxyData(name=proxy_crv, offset=proxy_offset, setup=(loc_scale_cluster,), uuid=self.get_uuid())

    def apply_offset_transform(self):
        """
        Attempts to apply transform values to the offset of the proxy.
        To be used only after proxy is built.
        """
        proxy_crv = find_proxy_from_uuid(uuid_string=self.uuid)
        if proxy_crv:
            proxy_offset = get_proxy_offset(proxy_crv)
            if proxy_offset and self.offset_transform:
                self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)

    def apply_transforms(self, apply_offset=False):
        """
        Attempts to apply offset and parent offset transforms to the proxy elements.
        To be used only after proxy is built.
        Args:
            apply_offset (bool, optional): If True, it will attempt to also apply the offset data. (Happens first)
        """
        proxy_crv = find_proxy_from_uuid(uuid_string=self.uuid)
        if proxy_crv and apply_offset:
            proxy_offset = get_proxy_offset(proxy_crv)
            if proxy_offset and self.offset_transform:
                self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if proxy_crv and self.transform:
            self.transform.apply_transform(target_object=proxy_crv, world_space=True)

    def apply_attr_dict(self, target_obj=None):
        """
        Attempts to apply (set) attributes found under the attribute dictionary of this proxy
        Args:
            target_obj (str, optional): Affected object, this is the object to get its attributes updated.
                                        If not provided it will attempt to retrieve the proxy using its UUID
        """
        if not target_obj:
            target_obj = find_proxy_from_uuid(self.get_uuid())
        if not target_obj or not cmds.objExists(target_obj):
            logger.debug(f"Unable to apply proxy attributes. Failed to find target object.")
            return
        if self.attr_dict:
            for attr, value in self.attr_dict.items():
                set_attr(obj_list=str(target_obj), attr_list=str(attr), value=value)

    def _initialize_transform(self):
        """
        In case a transform is necessary and none is present,
        a default Transform object is created and stored in "self.transform".
        """
        if not self.transform:
            self.transform = Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)

    def _initialize_offset_transform(self):
        """
        In case an offset transform is necessary and none is present,
        a default Transform object is created and stored in "self.offset_transform".
        """
        if not self.offset_transform:
            self.offset_transform = Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new proxy name.
        Args:
            name (str): New name to use on the proxy.
        """
        if name is None or not isinstance(name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(name))}"')
            return
        self.curve.set_name(name)
        self.name = name

    def set_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set proxy transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.transform = transform

    def set_initial_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position and the offset position as the same value causing it to be zeroed. (Initial position)
        Useful to determine where the proxy should initially appear and be able to go back to when zeroed.
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.set_position(x=x, y=y, z=z, xyz=xyz)
        self.set_offset_position(x=x, y=y, z=z, xyz=xyz)

    def set_initial_transform(self, transform):
        """
        Sets the transform and the offset transform as the same value causing it to be zeroed. (Initial position)
        Useful to determine where the proxy should initially appear and be able to go back to when zeroed.
        Args:
            transform (Transform): A transform  describing position, rotation and scale. (Applied to offset and proxy)
        """
        self.set_transform(transform)
        self.set_offset_transform(transform)

    def set_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_offset_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set proxy transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.offset_transform = transform

    def set_offset_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_offset_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_offset_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_curve(self, curve, inherit_curve_name=False):
        """
        Sets the curve used to build the proxy element
        Args:
            curve (Curve) A Curve object to be used for building the proxy element (its shape)
            inherit_curve_name (bool, optional): If active, this function try to extract the name of the curve and
                                                 change the name of the proxy to match it. Does nothing if name is None.
        """
        if not curve or not isinstance(curve, Curve):
            logger.debug(f'Unable to set proxy curve. Invalid input. Must be a valid Curve object.')
            return
        if not curve.is_curve_valid():
            logger.debug(f'Unable to set proxy curve. Curve object failed validation.')
            return
        if inherit_curve_name:
            self.set_name(curve.get_name())
        else:
            curve.set_name(name=self.name)
        self.curve = curve

    def set_locator_scale(self, scale):
        if not isinstance(scale, (float, int)):
            logger.debug(f'Unable to set locator scale. Invalid input.')
        self.locator_scale = scale

    def set_attr_dict(self, attr_dict):
        """
        Sets the attributes dictionary for this proxy. Attributes are any key/value pairs further describing the proxy.
        Args:
            attr_dict (dict): An attribute dictionary where the key is the attribute and value is the attribute value.
                              e.g. {"locatorScale": 1, "isVisible": True}
        """
        if not isinstance(attr_dict, dict):
            logger.warning(f'Unable to set attribute dictionary. '
                           f'Expected a dictionary, but got: "{str(type(attr_dict))}"')
            return
        self.attr_dict = attr_dict

    def add_to_attr_dict(self, attr, value):
        """
        Adds a new item to the attribute dictionary.
        If an element with the same key already exists in the attribute dictionary, it will be overwritten.
        Args:
            attr (str): Attribute name (also used as key on the dictionary)
            value (Any): Value for the attribute
        """
        self.attr_dict[attr] = value

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set proxy metadata. Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten.
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def add_line_parent(self, line_parent):
        """
        Adds a line parent UUID to the metadata dictionary. Initializes it in case it was not yet initialized.
        This is used to created visualization lines or other elements without actually parenting the element.
        Args:
            line_parent (str, Proxy): New meta parent, if a UUID string. If Proxy, it will get the UUID (get_uuid).
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        if isinstance(line_parent, str) and is_uuid_valid(line_parent):
            self.metadata[RiggerConstants.META_PROXY_LINE_PARENT] = line_parent
        if isinstance(line_parent, Proxy):
            self.metadata[RiggerConstants.META_PROXY_LINE_PARENT] = line_parent.get_uuid()

    def add_driver_type(self, driver_type):
        """
        Adds a type/tag to the list of drivers. Initializes metadata in case it was not yet initialized.
        A type/tag is used to determine controls driving the joint generated from this proxy
        A proxy generates a joint, this joint can driven by multiple controls, the tag helps identify them.
        Args:
            driver_type (str, list): New type/tag to add. e.g. "fk", "ik", "offset", etc...
                              Can also be a list of new tags: e.g. ["fk", "ik"]
        """
        if not driver_type:
            logger.debug(f'Invalid tag was provided. Add driver operation was skipped.')
            return
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        if isinstance(driver_type, str):
            driver_type = [driver_type]
        new_tags = self.metadata.get(RiggerConstants.META_PROXY_DRIVERS, [])
        for tag in driver_type:
            if tag and isinstance(tag, str) and tag not in new_tags:
                new_tags.append(tag)
        if new_tags:
            self.metadata[RiggerConstants.META_PROXY_DRIVERS] = new_tags

    def clear_driver_types(self):
        """
        Clears any driver tags found in the metadata.
        """
        if self.metadata:
            self.metadata.pop(RiggerConstants.META_PROXY_DRIVERS, None)

    def add_color(self, rgb_color):
        """
        Adds a color attribute to the metadata dictionary.
        This attribute is used to determine a fixed proxy color (instead of the side setup)
        Args:
            rgb_color (tuple, list): New RGB color. Must be a tuple or a list with 3 floats/integers
        """
        if isinstance(rgb_color, (tuple, list)) and len(rgb_color) >= 3:  # 3 = RGB
            if all(isinstance(item, (int, float)) for item in rgb_color):
                self.attr_dict["autoColor"] = False
                self.attr_dict["colorDefault"] = [rgb_color[0], rgb_color[1], rgb_color[2]]
            else:
                logger.debug(f'Unable to set color. Input must contain only numeric values.')
        else:
            logger.debug(f'Unable to set color. Input must be a tuple or a list with at least 3 elements (RGB).')

    def set_uuid(self, uuid):
        """
        Sets a new UUID for the proxy.
        If no UUID is provided or set a new one will be generated automatically,
        this function is used to force a specific value as UUID.
        Args:
            uuid (str): A new UUID for this proxy
        """
        error_message = f'Unable to set proxy UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.uuid = uuid
        else:
            logger.warning(error_message)

    def set_parent_uuid(self, uuid):
        """
        Sets a new parent UUID for the proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            uuid (str): A new UUID for the parent of this proxy
        """
        error_message = f'Unable to set proxy parent UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

    def set_parent_uuid_from_proxy(self, parent_proxy):
        """
        Sets the provided proxy as the parent  of this proxy. Its UUID  is extracted as parent_UUID for this proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            parent_proxy (Proxy): A proxy object. The UUID for the parent will be extracted from it.
                                  Will be the parent of this proxy when being parented.
        """
        error_message = f'Unable to set proxy parent UUID. Invalid proxy input.'
        if not parent_proxy or not isinstance(parent_proxy, Proxy):
            logger.warning(error_message)
            return
        parent_uuid = parent_proxy.get_uuid()
        self.set_parent_uuid(parent_uuid)

    def clear_parent_uuid(self):
        """
        Clears the parent UUID by setting the "parent_uuid" to None
        """
        self.parent_uuid = None

    def set_meta_purpose(self, value):
        """
        Adds a proxy meta type key and value to the metadata dictionary. Used to define proxy type in modules.
        Args:
            value (str, optional): Type "tag" used to determine overwrites.
                                   e.g. "hip", so the module knows it's a "hip" proxy.
        """
        self.add_to_metadata(key=RiggerConstants.META_PROXY_PURPOSE, value=value)

    def read_data_from_dict(self, proxy_dict):
        """
        Reads the data from a proxy dictionary and updates the values of this proxy to match it.
        Args:
            proxy_dict (dict): A dictionary describing the proxy data. e.g. {"name": "proxy", "parent": "1234...", ...}
        Returns:
            Proxy: This object (self)
        """
        if proxy_dict and not isinstance(proxy_dict, dict):
            logger.debug(f'Unable o read data from dict. Input must be a dictionary.')
            return

        _name = proxy_dict.get('name')
        if _name:
            self.set_name(name=_name)

        _parent = proxy_dict.get('parent')
        if _parent:
            self.set_parent_uuid(uuid=_parent)

        _loc_scale = proxy_dict.get('locatorScale')
        if _loc_scale:
            self.set_locator_scale(scale=_loc_scale)

        transform = proxy_dict.get('transform')
        if transform and len(transform) == 3:
            self._initialize_transform()
            self.transform.set_transform_from_dict(transform_dict=transform)

        offset_transform = proxy_dict.get('offsetTransform')
        if offset_transform and len(offset_transform) == 3:
            self._initialize_offset_transform()
            self.offset_transform.set_transform_from_dict(transform_dict=transform)

        attributes = proxy_dict.get('attributes')
        if attributes:
            self.set_attr_dict(attr_dict=attributes)

        metadata = proxy_dict.get('metadata')
        if metadata:
            self.set_metadata_dict(metadata=metadata)

        _uuid = proxy_dict.get('uuid')
        if _uuid:
            self.set_uuid(uuid=_uuid)
        return self

    def read_data_from_scene(self):
        """
        Attempts to find the proxy in the scene. If found, it reads the data into the proxy object.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Returns:
            Proxy: This object (self)
        """
        ignore_attr_list = [RiggerConstants.ATTR_PROXY_UUID,
                            RiggerConstants.ATTR_PROXY_SCALE]
        proxy = get_object_from_uuid_attr(uuid_string=self.uuid, attr_name=RiggerConstants.ATTR_PROXY_UUID)
        if proxy:
            try:
                self._initialize_transform()
                self.transform.set_transform_from_object(proxy)
                attr_dict = {}
                user_attrs = list_user_defined_attr(proxy, skip_nested=True, skip_parents=False) or []
                for attr in user_attrs:
                    if not cmds.getAttr(f'{proxy}.{attr}', lock=True) and attr not in ignore_attr_list:
                        attr_dict[attr] = get_attr(f'{proxy}.{attr}')
                if attr_dict:
                    self.set_attr_dict(attr_dict=attr_dict)
            except Exception as e:
                logger.debug(f'Unable to read proxy data for "{str(self.name)}". Issue: {str(e)}')
        return self

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_metadata_value(self, key):
        """
        Gets the value stored in the metadata. If not found, returns None.
        Args:
            key (str): The value key.
        Returns:
            any: Value stored in the metadata key. If not found, it returns None
        """
        if not self.metadata or not key:
            return
        return self.metadata.get(key)

    def get_meta_parent_uuid(self):
        """
        Gets the meta parent of this proxy (if present)
        Returns:
            str or None: The UUID set as meta parent, otherwise, None.
        """
        return self.get_metadata_value(RiggerConstants.META_PROXY_LINE_PARENT)

    def get_meta_purpose(self):
        """
        Gets the meta purpose of this proxy (if present)
        Returns:
            str or None: The purpose of this proxy as stored in the metadata, otherwise None.
        """
        return self.get_metadata_value(RiggerConstants.META_PROXY_PURPOSE)

    def get_name(self):
        """
        Gets the name property of the proxy.
        Returns:
            str or None: Name of the proxy, None if it's not set.
        """
        return self.name

    def get_uuid(self):
        """
        Gets the uuid value of this proxy.
        Returns:
            str: uuid string
        """
        return self.uuid

    def get_parent_uuid(self):
        """
        Gets the parent uuid value of this proxy.
        Returns:
            str: uuid string for the potential parent of this proxy.
        """
        return self.parent_uuid

    def get_locator_scale(self):
        """
        Gets the locator scale for this proxy
        Returns:
            float: The locator scale
        """
        return self.locator_scale

    def get_attr_dict(self):
        """
        Gets the attribute dictionary for this proxy
        Returns:
            dict: a dictionary where the key is the attribute name and the value is the value of the attribute.
                  e.g. {"locatorScale": 1, "isVisible": True}
        """
        return self.attr_dict

    def get_driver_types(self):
        """
        Gets a list of available driver types. e.g.  ["fk", "ik", "offset"]
        Returns:
            list or None: A list of driver types (strings) otherwise None.
        """
        if self.metadata:
            return self.metadata.get(RiggerConstants.META_PROXY_DRIVERS, None)

    def get_proxy_as_dict(self, include_uuid=False, include_transform_data=True, include_offset_data=True):
        """
        Returns all necessary information to recreate this proxy as a dictionary
        Args:
            include_uuid (bool, optional): If True, it will also include an "uuid" key and value in the dictionary.
            include_transform_data (bool, optional): If True, it will also export the transform data.
            include_offset_data (bool, optional): If True, it will also export the offset transform data.
        Returns:
            dict: Proxy data as a dictionary
        """
        # Create Proxy Data
        proxy_data = {"name": self.name}

        if include_uuid and self.get_uuid():
            proxy_data["uuid"] = self.get_uuid()

        proxy_data["parent"] = self.get_parent_uuid()  # Add later to determine order
        proxy_data["locatorScale"] = self.locator_scale

        if self.transform and include_transform_data:
            proxy_data["transform"] = self.transform.get_transform_as_dict()

        if self.offset_transform and include_offset_data:
            proxy_data["offsetTransform"] = self.offset_transform.get_transform_as_dict()

        if self.get_attr_dict():
            proxy_data["attributes"] = self.get_attr_dict()

        if self.get_metadata():
            proxy_data["metadata"] = self.get_metadata()

        return proxy_data


class ModuleGeneric:
    __version__ = '0.1.0-beta'
    icon = resource_library.Icon.rigger_module_generic
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name=None, prefix=None, suffix=None):
        # Default Values
        self.name = self.get_module_class_name(remove_module_prefix=True, formatted=True)
        self.uuid = generate_uuid(short=True, short_length=12)
        self.prefix = None
        self.suffix = None
        self.proxies = []
        self.parent_uuid = None
        self.metadata = None
        self.active = True
        self.orientation = OrientationData()

        if name:
            self.set_name(name)
        if prefix:
            self.set_prefix(prefix)
        if suffix:
            self.set_suffix(suffix)

        self.module_children_drivers = []  # Cached elements to be parented to the "parentUUID" driver

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new module name.
        Args:
            name (str): New name to use on the proxy.
        """
        if name is None or not isinstance(name, str):
            logger.warning(f'Unable to set name. Expected string but got "{str(type(name))}"')
            return
        self.name = name

    def set_uuid(self, uuid):
        """
        Sets a new UUID for the module.
        If no UUID is provided or set a new one will be generated automatically,
        this function is used to force a specific value as UUID.
        Args:
            uuid (str): A new UUID for this module (12 length format)
        """
        error_message = f'Unable to set proxy UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_short_uuid_valid(uuid, length=12):
            self.uuid = uuid
        else:
            logger.warning(error_message)

    def set_prefix(self, prefix):
        """
        Sets a new module prefix.
        Args:
            prefix (str): New prefix to use on the proxy.
        """
        if prefix is None or not isinstance(prefix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(prefix))}"')
            return
        self.prefix = prefix

    def set_suffix(self, suffix):
        """
        Sets a new module prefix.
        Args:
            suffix (str): New suffix to use on the proxy.
        """
        if suffix is None or not isinstance(suffix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(suffix))}"')
            return
        self.suffix = suffix

    def set_parent_uuid(self, uuid):
        """
        Sets a new parent UUID for the proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            uuid (str): A new UUID for the parent of this proxy
        """
        error_message = f'Unable to set proxy parent UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

    def set_proxies(self, proxy_list):
        """
        Sets a new proxy name.
        Args:
            proxy_list (str): New name to use on the proxy.
        """
        if not proxy_list or not isinstance(proxy_list, list):
            logger.warning(f'Unable to set new list of proxies. '
                           f'Expected list of proxies but got "{str(proxy_list)}"')
            return
        self.proxies = proxy_list

    def add_to_proxies(self, proxy):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            proxy (Proxy, List[Proxy]): New proxy element to be added to this module or a list of proxies
        """
        if proxy and isinstance(proxy, Proxy):
            proxy = [proxy]
        if proxy and isinstance(proxy, list):
            for obj in proxy:
                if isinstance(obj, Proxy):
                    self.proxies.append(obj)
                else:
                    logger.debug(f'Unable to add "{str(obj)}". Incompatible type.')
            return
        logger.debug(f'Unable to add proxy to module. '
                     f'Must be of the type "Proxy" or a list containing only Proxy elements.')

    def add_new_proxy(self):
        """
        Adds a clear new proxy to the proxies list.
        Returns:
            Proxy: The created proxy
        """
        pattern = r'^proxy\d*$'
        proxy_names = [proxy.get_name() for proxy in self.proxies]
        valid_proxies = [item for item in proxy_names if re.match(pattern, item)]
        highest_proxy_num = get_highest_int_from_str_list(valid_proxies)
        new_proxy = Proxy()
        if valid_proxies:
            new_proxy.set_name(f'proxy{str(highest_proxy_num+1)}')
        self.add_to_proxies(new_proxy)
        return new_proxy

    def remove_from_proxies(self, proxy):
        """
        Removes a proxy object from the proxies list
        Args:
            proxy (Proxy): The proxy to be removed.
        Returns:
            Proxy or None: The removed proxy, None otherwise.
        """
        for _proxy in self.proxies:
            if proxy == _proxy:
                self.proxies.remove(proxy)
                return proxy
        logger.debug(f'Unable to remove proxy from module. Not found.')

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set module metadata. '
                           f'Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

    def set_active_state(self, is_active):
        """
        Sets the "is_active" variable. This variable determines if the module will be skipped while in a project or not.
        Args:
            is_active (bool): True if active, False if inactive. Inactive modules are ignored when in a project.
        """
        if not isinstance(is_active, bool):
            logger.warning(f'Unable to set active state. '
                           f'Expected a boolean, but got: "{str(type(is_active))}"')
            return
        self.active = is_active

    def set_orientation(self, orientation_data):
        """
        Sets orientation by defining a new OrientationData object.
        Args:
            orientation_data (OrientationData): New orientation data object.
        """
        if not orientation_data or not isinstance(orientation_data, OrientationData):
            logger.debug(f'Unable to set orientation data. Input must be a "OrientationData".')
            return
        self.orientation = orientation_data

    def set_orientation_method(self, method):
        """
        Sets the orientation of the joints generated by this proxy.
        Args:
            method (str, None): Orientation method. This will define how the values are applied or not applied.
        """
        self.orientation.set_method(method)

    def set_orientation_direction(self, is_positive, set_aim_axis=True, set_up_axis=True, set_up_dir=True):
        """
        Sets the direction of the orientation.
        If positive, it will use "1" in the desired axis.
        If negative, (not positive) it will use "-1" in the desired axis.
        Args:
            is_positive (bool): If True, it's set to a positive direction, if False to negative.
                                e.g. True = (1, 0, 0) while False (-1, 0, 0)
            set_aim_axis (bool, optional): If True, aim axis is set/affected.
            set_up_axis (bool, optional): If True, up axis is set/affected.
            set_up_dir (bool, optional): If True, up direction is set/affected.
        """
        if is_positive:
            multiplier = 1
        else:
            multiplier = -1
        if set_aim_axis:
            _aim_axis = self.orientation.get_aim_axis()
            _aim_axis = tuple(abs(value)*multiplier for value in _aim_axis)
            self.orientation.set_aim_axis(_aim_axis)
        if set_up_axis:
            _up_axis = self.orientation.get_up_axis()
            _up_axis = tuple(abs(value)*multiplier for value in _up_axis)
            self.orientation.set_up_axis(_up_axis)
        if set_up_dir:
            _up_dir = self.orientation.get_up_dir()
            _up_dir = tuple(abs(value)*multiplier for value in _up_dir)
            self.orientation.set_up_dir(_up_dir)

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def clear_parent_uuid(self):
        """
        Clears the parent UUID by setting the "parent_uuid" attribute to None
        """
        self.parent_uuid = None

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

        self.proxies = []
        for uuid, description in proxy_dict.items():
            _proxy = Proxy()
            _proxy.set_uuid(uuid)
            _proxy.read_data_from_dict(proxy_dict=description)
            self.proxies.append(_proxy)

    def read_data_from_dict(self, module_dict):
        """
        Reads the data from a module dictionary and updates the values of this module to match it.
        Args:
            module_dict (dict): A dictionary describing the module data. e.g. {"name": "generic"}
        Returns:
            ModuleGeneric: This module (self)
        """
        if module_dict and not isinstance(module_dict, dict):
            logger.debug(f'Unable o read data from dict. Input must be a dictionary.')
            return

        _name = module_dict.get('name')
        if _name:
            self.set_name(name=_name)

        _uuid = module_dict.get('uuid')
        if _uuid:
            self.set_uuid(uuid=_uuid)

        _prefix = module_dict.get('prefix')
        if _prefix:
            self.set_prefix(prefix=_prefix)

        _suffix = module_dict.get('suffix')
        if _suffix:
            self.set_suffix(suffix=_suffix)

        _parent = module_dict.get('parent')
        if _parent:
            self.set_parent_uuid(uuid=_parent)

        _orientation = module_dict.get('orientation')
        if _orientation:
            self.orientation.set_data_from_dict(orient_dict=_orientation)

        _proxies = module_dict.get('proxies')
        if _proxies and isinstance(_proxies, dict):
            self.read_proxies_from_dict(proxy_dict=_proxies)

        _is_active = module_dict.get('active')
        if isinstance(_is_active, bool):
            self.set_active_state(is_active=_is_active)

        _metadata = module_dict.get('metadata')
        if _metadata:
            self.set_metadata_dict(metadata=_metadata)
        return self

    def read_purpose_matching_proxy_from_dict(self, proxy_dict):
        """
        Utility used by inherited modules to detect the proxy meta type when reading their dict data.
        Args:
            proxy_dict (dict): A proxy description dictionary. It must match an expected pattern for this to work:
                               Acceptable pattern: {"uuid_str": {<description>}}
                               "uuid_str" being the actual uuid string value of the proxy.
                               "<description>" being the output of the operation "proxy.get_proxy_as_dict()".
        """
        proxies = self.get_proxies()
        proxy_type_link = {}
        for proxy in proxies:
            metadata = proxy.get_metadata()
            meta_type = get_meta_purpose_from_dict(metadata)
            if meta_type and isinstance(meta_type, str):
                proxy_type_link[meta_type] = proxy

        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            meta_type = get_meta_purpose_from_dict(metadata)
            if meta_type in proxy_type_link:
                proxy = proxy_type_link.get(meta_type)
                proxy.set_uuid(uuid)
                proxy.read_data_from_dict(proxy_dict=description)

    def read_data_from_scene(self):
        """
        Attempts to find the proxies in the scene. If found, their data is read into the proxy object.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Returns:
            ModuleGeneric: This object (self)
        """
        for proxy in self.proxies:
            proxy.read_data_from_scene()
        return self

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_name(self):
        """
        Gets the name property of the rig module.
        Returns:
            str or None: Name of the rig module, None if it's not set.
        """
        return self.name

    def get_uuid(self):
        """
        Gets the uuid value of this module.
        Returns:
            str: uuid string (length 12 - short version)
        """
        return self.uuid

    def get_prefix(self):
        """
        Gets the prefix property of the rig module.
        Returns:
            str or None: Prefix of the rig module, None if it's not set.
        """
        return self.prefix

    def get_suffix(self):
        """
        Gets the suffix property of the rig module.
        Returns:
            str or None: Suffix of the rig module, None if it's not set.
        """
        return self.suffix

    def get_parent_uuid(self):
        """
        Gets the parent uuid value of this proxy.
        Returns:
            str: uuid string for the potential parent of this proxy.
        """
        return self.parent_uuid

    def get_proxies(self):
        """
        Gets the proxies in this rig module.
        Returns:
            list: A list of proxies found in this rig module.
        """
        return self.proxies

    def get_proxies_uuids(self):
        """
        Gets a list of UUIDs by extracting the UUIDs of all proxies found in "self.proxies"
        Returns:
            list: A list of proxy UUIDs (strings)
        """
        return [proxy.get_uuid() for proxy in self.proxies]

    def get_proxy_uuid_existence(self, uuid):
        """
        Gets if the provided proxy uuid is within this module or not.
        Returns:
            bool: True if found, False otherwise.
        """
        return True if uuid in self.get_proxies_uuids() else False

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_metadata_value(self, key):
        """
        Gets the value stored in the metadata. If not found, returns None.
        Args:
            key (str): The value key.
        Returns:
            any: Value stored in the metadata key. If not found, it returns None
        """
        if not self.metadata or not key:
            return
        return self.metadata.get(key)

    def is_active(self):
        """
        Gets the active state. (True or False)
        Returns:
            bool: True if module is active, False if not.
        """
        return self.active

    def get_orientation_data(self):
        """
        Gets the orientation data.
        Returns:
            OrientationData: OrientationData object with the module orientation description.
        """
        return self.orientation

    def get_orientation_method(self):
        """
        Gets the orientation method
        Returns:
            str: Orientation method description.
        """
        return self.orientation.get_method()

    def get_module_as_dict(self, include_module_name=True, include_offset_data=True):
        """
        Gets the properties of this module (including proxies) as a dictionary
        Args:
            include_module_name (bool, optional): If True, it will also include the name of the class in the dictionary.
                                                  e.g. "ModuleGeneric"
            include_offset_data (bool, optional): If True, it will include the offset transform data in the dictionary.
        Returns:
            dict: Dictionary describing this module
        """
        module_data = {}
        if include_module_name:
            module_name = self.get_module_class_name(remove_module_prefix=True)
            module_data["module"] = module_name
        if self.name:
            module_data["name"] = self.name
        module_data["uuid"] = self.uuid
        module_data["active"] = self.active
        if self.prefix:
            module_data["prefix"] = self.prefix
        if self.suffix:
            module_data["suffix"] = self.suffix
        if self.parent_uuid:
            module_data["parent"] = self.parent_uuid
        if self.orientation:
            module_data['orientation'] = self.orientation.get_data_as_dict()
        if self.metadata:
            module_data["metadata"] = self.metadata
        module_proxies = {}
        for proxy in self.proxies:
            module_proxies[proxy.get_uuid()] = proxy.get_proxy_as_dict(include_offset_data=include_offset_data)
        module_data["proxies"] = module_proxies
        return module_data

    def get_module_class_name(self, remove_module_prefix=False, formatted=False, remove_side=False):
        """
        Gets the name of this class
        Args:
            remove_module_prefix (bool, optional): If True, it will remove the prefix word "Module" from class name.
                                                   Used to reduce the size of the string in JSON outputs.
            formatted (bool, optional): If True, it will return a formatted version of the module class name.
                                        In this case, a title version of the string. e.g. "Module Generic"
            remove_side (bool, optional): If active, it will remove suffixes that match "Right", "Left"
        Returns:
            str: Class name as a string.
        """
        _module_class_name = str(self.__class__.__name__)
        if remove_module_prefix:
            _module_class_name = remove_prefix(input_string=str(self.__class__.__name__), prefix="Module")
        if formatted:
            _module_class_name = " ".join(camel_case_split(_module_class_name))
        if remove_side:
            _module_class_name = remove_suffix(input_string=_module_class_name, suffix="Right")
            _module_class_name = remove_suffix(input_string=_module_class_name, suffix="Left")
        return _module_class_name

    def get_description_name(self, add_class_len=2):
        """
        Gets the name of the module. If too short or empty, use the class name instead.
        Args:
            add_class_len (bool, optional): Determine the length of the string before the class name is added.
        Returns:
            str: Formatted version of the object's name.
        """
        _module_name = ""
        if self.name and isinstance(self.name, str):
            _module_name = self.name
        _class_name = self.get_module_class_name(remove_module_prefix=True)
        if len(_module_name) == 0:
            _module_name = f'({_class_name})'
        elif len(_module_name) <= add_class_len:
            _module_name = f'{_module_name} ({_class_name})'
        return _module_name

    def find_driver(self, driver_type, proxy_purpose):
        """
        Find driver (a.k.a. Control) is responsible for directly or indirectly driving a joint or a group of joints.
        Args:
            driver_type (str): A driver type (aka tag) used to identify the type of control. e.g. "fk", "ik", "offset".
            proxy_purpose (str, Proxy): The purpose of the control (aka Description) e.g. "shoulder"
                                        This can also be a proxy, in which case the purposed will be extracted.
        Returns:
            Node or None: A Node object pointing to an existing driver/control object, otherwise None.
        """
        uuid = self.uuid
        if driver_type:
            uuid = f'{uuid}-{driver_type}'
        if proxy_purpose and isinstance(proxy_purpose, Proxy):
            proxy_purpose = proxy_purpose.get_meta_purpose()
        if proxy_purpose:
            uuid = f'{uuid}-{proxy_purpose}'
        return find_driver_from_uuid(uuid_string=uuid)

    def find_module_drivers(self):
        """
        Find driver nodes (a.k.a. Controls) that are responsible for directly or indirectly driving the proxy's joint.
        Returns:
            list: A list of transforms used as drivers/controls for this module.
        """
        obj_list = cmds.ls(typ="transform", long=True) or []
        matches = []
        module_uuid = self.uuid
        for obj in obj_list:
            if cmds.objExists(f'{obj}.{RiggerConstants.ATTR_DRIVER_UUID}'):
                uuid_value = cmds.getAttr(f'{obj}.{RiggerConstants.ATTR_DRIVER_UUID}')
                if uuid_value.startswith(module_uuid):
                    matches.append(obj)
        return matches

    def find_proxy_drivers(self, proxy, as_dict=True):
        """
        Find driver nodes (a.k.a. Controls) that are responsible for directly or indirectly driving the proxy's joint.
        Args:
            proxy (Proxy): The proxy, used to get the driver purpose and types.
                           If missing metadata, an empty list is returned.
            as_dict (bool, optional): If True, this function return a dictionary where the key is the driver type and
                                      the value is the driver, if False, then it returns a list of drivers.
        Returns:
            dict, list: A list of transforms used as drivers/controls for the provided proxy.
        """
        proxy_driver_types = proxy.get_driver_types()
        proxy_purpose = proxy.get_meta_purpose()
        if not proxy_driver_types:
            logger.debug(f'Proxy does not have any driver types. No drivers can be found without a type.')
            return []
        if not proxy_purpose:
            logger.debug(f'Proxy does not have a defined purpose. No drivers can be found without a purpose.')
            return []
        driver_uuids = []
        for proxy_type in proxy_driver_types:
            driver_uuids.append(f'{self.uuid}-{proxy_type}-{proxy_purpose}')
        obj_list = cmds.ls(typ="transform", long=True) or []
        module_matches = {}
        module_uuid = self.uuid
        for obj in obj_list:
            if cmds.objExists(f'{obj}.{RiggerConstants.ATTR_DRIVER_UUID}'):
                uuid_value = cmds.getAttr(f'{obj}.{RiggerConstants.ATTR_DRIVER_UUID}')
                if uuid_value.startswith(module_uuid):
                    module_matches[uuid_value] = Node(obj)
        matches = []
        matches_dict = {}
        for driver_uuid in driver_uuids:
            if driver_uuid in module_matches:
                matches.append(module_matches.get(driver_uuid))
                driver_key = str(driver_uuid).split("-")
                if len(driver_key) >= 3:
                    matches_dict[driver_key[1]] = module_matches.get(driver_uuid)
        if len(matches) != driver_uuids:
            logger.debug(f'Not all drivers were found. '
                         f'Driver type list has a different length when compared to the list of matches.')
        if as_dict:
            matches = matches_dict
        return matches

    def _assemble_ctrl_name(self, name, project_prefix=None, overwrite_prefix=None, overwrite_suffix=None):
        """
        Assemble a new control name based on the given parameters and module prefix/suffix.
        This function also automatically adds the control suffix at the end of the generated name.
        Result pattern: "<project_prefix>_<module_prefix>_<name>_<module_suffix>_<control_suffix>"
        Args:
            name (str): The base name of the control.
            project_prefix (str, optional): Prefix specific to the project. Defaults to None.
            overwrite_prefix (str, optional): Prefix to overwrite the module's prefix. Defaults to None (use module)
                                              When provided (even if empty) it will replace the module stored value.
            overwrite_suffix (str, optional): Suffix to overwrite the module's suffix. Defaults to None (use module)
                                              When provided (even if empty) it will replace the module stored value.

        Returns:
            str: The assembled new node name.

        Example:
            instance._assemble_new_node_name(name='NodeName', project_prefix='Project', overwrite_suffix='Custom')
            'Project_NodeName_Custom'
        """
        _suffix = ''
        module_suffix = self.suffix
        if module_suffix:
            module_suffix = f'{module_suffix}_{NamingConstants.Suffix.CTRL}'
        else:
            module_suffix = NamingConstants.Suffix.CTRL
        if isinstance(overwrite_suffix, str):
            module_suffix = overwrite_suffix
        if overwrite_suffix:
            module_suffix = overwrite_suffix
        if module_suffix:
            _suffix = f'_{module_suffix}'
        return self._assemble_new_node_name(name=name,
                                            project_prefix=project_prefix,
                                            overwrite_prefix=overwrite_prefix,
                                            overwrite_suffix=module_suffix)

    def _assemble_new_node_name(self, name, project_prefix=None, overwrite_prefix=None, overwrite_suffix=None):
        """
        Assemble a new node name based on the given parameters and module prefix/suffix.
        Result pattern: "<project_prefix>_<module_prefix>_<name>_<module_suffix>"
        Args:
            name (str): The base name of the node.
            project_prefix (str, optional): Prefix specific to the project. Defaults to None.
            overwrite_prefix (str, optional): Prefix to overwrite the module's prefix. Defaults to None (use module)
                                              When provided (even if empty) it will replace the module stored value.
            overwrite_suffix (str, optional): Suffix to overwrite the module's suffix. Defaults to None (use module)
                                              When provided (even if empty) it will replace the module stored value.

        Returns:
            str: The assembled new node name.

        Example:
            instance._assemble_new_node_name(name='NodeName', project_prefix='Project', overwrite_suffix='Custom')
            'Project_NodeName_Custom'
        """
        prefix_list = []
        module_prefix = self.prefix
        module_suffix = self.suffix
        # Determine Overwrites
        if isinstance(overwrite_prefix, str):
            module_prefix = overwrite_prefix
        if isinstance(overwrite_suffix, str):
            module_suffix = overwrite_suffix
        # Gather Suffixes
        if project_prefix and isinstance(project_prefix, str):
            prefix_list.append(project_prefix)
        if module_prefix and isinstance(module_prefix, str):
            prefix_list.append(module_prefix)
        # Create Parts
        _prefix = ''
        _suffix = ''
        if prefix_list:
            _prefix = '_'.join(prefix_list) + '_'
        if module_suffix:
            _suffix = f'_{module_suffix}'
        # Assemble and Return
        return f'{_prefix}{name}{_suffix}'

    # --------------------------------------------------- Misc ---------------------------------------------------
    def apply_transforms(self, apply_offset=False):
        """
        Attempts to apply offset and parent offset transforms to the proxy elements.
        To be used only after proxy is built.
        Args:
            apply_offset (bool, optional): If True, it will attempt to also apply the offset data. (Happens first)
        """
        for proxy in self.proxies:
            proxy.apply_transforms(apply_offset=apply_offset)

    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        if not self.proxies:
            logger.warning('Missing proxies. A rig module needs at least one proxy to function.')
            return False
        return True

    def add_driver_uuid_attr(self, target, driver_type=None, proxy_purpose=None):
        """
        Adds an attribute to be used as driver UUID to the object.
        The value of the attribute is created using the module uuid, the driver type and proxy purpose combined.
        Following this pattern: "<module_uuid>-<driver_type>-<proxy_purpose>" e.g. "abcdef123456-fk-shoulder"
        Args:
            target (str): Path to the object that will receive the driver attributes.
            driver_type (str, optional): A string or tag use to identify the control type. e.g. "fk", "ik", "offset"
            proxy_purpose (str, Proxy, optional): This is the proxy purpose. It can be a string, e.g. "shoulder" or
                                                  the proxy object (if a Proxy object is provided, then it tries to extract
        """
        uuid = f'{self.uuid}'
        if driver_type:
            uuid = f'{uuid}-{driver_type}'
        if proxy_purpose and isinstance(proxy_purpose, Proxy):
            proxy_purpose = proxy_purpose.get_meta_purpose()
        if proxy_purpose:
            uuid = f'{uuid}-{proxy_purpose}'
        if not target or not cmds.objExists(target):
            logger.debug(f'Unable to add UUID attribute. Target object is missing.')
            return
        uuid_attr = add_attr(obj_list=target, attr_type="string", is_keyable=False,
                             attributes=RiggerConstants.ATTR_DRIVER_UUID, verbose=True)[0]
        if not uuid:
            uuid = generate_uuid(remove_dashes=True)
        set_attr(attribute_path=uuid_attr, value=str(uuid))
        return target

    # --------------------------------------------------- Build ---------------------------------------------------
    def build_proxy(self, project_prefix=None, optimized=False):
        """
        Builds the proxy representation of the rig (for the user to adjust and determine the pose)
        Args:
            project_prefix (str, optional): If provided, this prefix will be added to proxies when they are created.
                                            This is an extra prefix, added on top of the module prefix (self.prefix)
                                            So the final pattern is:
                                                "<project_prefix>_<module_prefix>_<name>_<module_suffix>"
                                            Project prefix is the prefix stored in the project carrying this module.
                                            Module prefix is the prefix stored in this module "self.prefix"
                                            Module suffix is the suffix stored in this module "self.suffix"
            optimized (bool, optional): If True, the module will skip display operations, such as curve creation,
                                        the addition of a snapping shape or the scale cluster and others.
                                        Useful for when building a rig without adjusting the proxy.
                                        Note: This skips happen inside the "proxy.build()" function, the "optimized"
                                        arguments is only fed into this function during this step.
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        logger.debug(f'"build_proxy" function for "{self.get_module_class_name()}" was called.')
        proxy_data = []
        _prefix = ''
        prefix_list = []
        if project_prefix and isinstance(project_prefix, str):
            prefix_list.append(project_prefix)
        if self.prefix and isinstance(self.prefix, str):
            prefix_list.append(self.prefix)
        if prefix_list:
            _prefix = '_'.join(prefix_list)
        for proxy in self.proxies:
            proxy_data.append(proxy.build(prefix=_prefix, suffix=self.suffix,
                                          apply_transforms=False, optimized=optimized))
        return proxy_data

    def build_proxy_setup(self):
        """
        Runs post proxy script. Used to define proxy automation/setup.
        This step runs after the execution of "build_proxy" is complete in all modules.
        Usually used to create extra behavior unique to the module. e.g. Constraints, automations, or limitations.
        """
        logger.debug(f'"build_proxy_setup" function for "{self.get_module_class_name()}" was called.')
        self.apply_transforms()

    def build_skeleton_joints(self):
        """
        Runs build skeleton joints script. Creates joints out of the proxy elements.
        This function should happen after "build_proxy_setup" as it expects proxy elements to be present in the scene.
        """
        logger.debug(f'"build_skeleton" function from "{self.get_module_class_name()}" was called.')
        skeleton_grp = find_skeleton_group()
        for proxy in self.proxies:
            proxy_node = find_proxy_from_uuid(proxy.get_uuid())
            if not proxy_node:
                continue
            joint = create_node(node_type="joint", name=proxy_node.get_short_name())
            locator_scale = proxy.get_locator_scale()
            cmds.setAttr(f'{joint}.radius', locator_scale)
            match_translate(source=proxy_node, target_list=joint)

            # Add proxy reference - Proxy/Joint UUID
            add_attr(obj_list=joint,
                     attributes=RiggerConstants.ATTR_JOINT_UUID,
                     attr_type="string")
            set_attr(obj_list=joint, attr_list=RiggerConstants.ATTR_JOINT_UUID, value=proxy.get_uuid())
            # Add module reference - Module UUID
            add_attr(obj_list=joint,
                     attributes=RiggerConstants.ATTR_MODULE_UUID,
                     attr_type="string")
            set_attr(obj_list=joint, attr_list=RiggerConstants.ATTR_MODULE_UUID, value=self.get_uuid())
            # Add proxy purposes - Meta Purpose
            add_attr(obj_list=joint,
                     attributes=RiggerConstants.ATTR_JOINT_PURPOSE,
                     attr_type="string")
            set_attr(obj_list=joint, attr_list=RiggerConstants.ATTR_JOINT_PURPOSE, value=proxy.get_meta_purpose())
            # Add proxy purposes - Joint Drivers
            add_attr(obj_list=joint,
                     attributes=RiggerConstants.ATTR_JOINT_DRIVERS,
                     attr_type="string")
            drivers = proxy.get_driver_types()
            if drivers:
                add_driver_to_joint(target_joint=joint, new_drivers=drivers)

            set_color_viewport(obj_list=joint, rgb_color=ColorConstants.RigJoint.GENERAL)
            hierarchy_utils.parent(source_objects=joint, target_parent=str(skeleton_grp))

    def build_skeleton_hierarchy(self):
        """
        Runs post skeleton script. Joints are parented and oriented during this step.
        Joint hierarchy (parenting) and orientation are coupled because of their dependency and correlation.
        This step runs after the execution of "build_skeleton_joints" is complete in all modules.
        Note:
            External parenting is executed only after orientation is defined.
            This fixes incorrect aim target orientation, because the last object simply
            inherits the orientation from its parent instead of looking at their children.
        """
        logger.debug(f'"build_skeleton_hierarchy" function from "{self.get_module_class_name()}" was called.')
        module_uuids = self.get_proxies_uuids()
        jnt_nodes = []
        for proxy in self.proxies:
            joint = find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue
            # Inherit Orientation (Before Parenting)
            if self.get_orientation_method() == OrientationData.Methods.inherit:
                proxy_obj_path = find_proxy_from_uuid(proxy.get_uuid())
                match_rotate(source=proxy_obj_path, target_list=joint)
            # Parent Joint (Internal Proxies)
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid in module_uuids:
                parent_joint_node = find_joint_from_uuid(parent_uuid)
                hierarchy_utils.parent(source_objects=joint, target_parent=parent_joint_node)
            jnt_nodes.append(joint)

        # Auto Orientation (After Parenting)
        if self.get_orientation_method() == OrientationData.Methods.automatic:
            self.orientation.apply_automatic_orientation(joint_list=jnt_nodes)

        # Parent Joints (External Proxies)
        for proxy in self.proxies:
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid not in module_uuids:
                joint = find_joint_from_uuid(proxy.get_uuid())
                parent_joint_node = find_joint_from_uuid(parent_uuid)
                hierarchy_utils.parent(source_objects=joint, target_parent=parent_joint_node)
        cmds.select(clear=True)

    def build_rig(self, project_prefix=None):
        """
        Runs build rig script.
        Used to create rig controls, automation and their internal connections.
        An external connection refers to a connection that makes reference to rig elements created in another module.
        Args:
            project_prefix (str, optional): If provided, this prefix will be added to the rig when it's created.
                                            This is an extra prefix, added on top of the module prefix (self.prefix)
                                            So the final pattern is:
                                                "<project_prefix>_<module_prefix>_<name>_<module_suffix>"
                                            Project prefix is the prefix stored in the project carrying this module.
                                            Module prefix is the prefix stored in this module "self.prefix"
                                            Module suffix is the suffix stored in this module "self.suffix"
        """
        logger.debug(f'"build_rig" function from "{self.get_module_class_name()}" was called.')

    def build_rig_post(self):
        """
        Runs post rig creation script.
        This step runs after the execution of "build_rig" is complete in all modules.
        Used to define automation or connections that require external elements to exist.
        """
        logger.debug(f'"build_rig" function from "{self.get_module_class_name()}" was called.')


class RigProject:
    icon = resource_library.Icon.rigger_project

    def __init__(self,
                 name=None,
                 prefix=None,
                 metadata=None):
        # Default Values
        self.name = "Untitled"
        self.prefix = None
        self.modules = []
        self.metadata = None

        if name:
            self.set_name(name=name)
        if prefix:
            self.set_prefix(prefix=prefix)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new project name.
        Args:
            name (str): New name to use on the proxy.
        """
        if name is None or not isinstance(name, str):
            logger.warning(f'Unable to set name. Expected string but got "{str(type(name))}"')
            return
        self.name = name

    def set_prefix(self, prefix):
        """
        Sets a new module prefix.
        Args:
            prefix (str): New name to use on the proxy.
        """
        if prefix is None or not isinstance(prefix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(prefix))}"')
            return
        self.prefix = prefix

    def set_modules(self, modules):
        """
        Sets the modules list directly.
        Args:
            modules (list): A list of modules (ModuleGeneric as base)
        """
        if modules is None or not isinstance(modules, list):
            logger.warning(f'Unable to set modules list. Expected a list but got "{str(type(modules))}"')
            return
        self.modules = modules

    def add_to_modules(self, module):
        """
        Adds a new item to the modules list.
        Args:
            module (ModuleGeneric, List[ModuleGeneric]): New module element to be added to this project.
        """
        from gt.tools.auto_rigger.rig_modules import RigModules
        all_modules = RigModules.get_module_names()
        if module and str(module.__class__.__name__) in all_modules:
            module = [module]
        if module and isinstance(module, list):
            for obj in module:
                if str(obj.__class__.__name__) in all_modules:
                    self.modules.append(obj)
                else:
                    logger.debug(f'Unable to add "{str(obj)}". Provided module not found in "RigModules".')
            return
        logger.debug(f'Unable to add provided module to rig project. '
                     f'Must be of the type "ModuleGeneric" or a list containing only ModuleGeneric elements.')

    def remove_from_modules(self, module):
        """
        Removes a module object from the modules list
        Args:
            module (ModuleGeneric): The module to be removed.
        Returns:
            ModuleGeneric or None: The removed proxy, None otherwise.
        """
        for _module in self.modules:
            if module == _module:
                self.modules.remove(module)
                return module
        logger.debug(f'Unable to remove module from project. Not found.')

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set rig project metadata. '
                           f'Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def read_modules_from_dict(self, modules_list):
        """
        Reads a proxy description dictionary and populates (after resetting) the proxies list with the dict proxies.
        Args:
            modules_list (list): A list of module descriptions.
        """
        if not modules_list or not isinstance(modules_list, list):
            logger.debug(f'Unable to read modules from list. Input must be a list.')
            return

        self.modules = []
        from gt.tools.auto_rigger.rig_modules import RigModules
        available_modules = RigModules.get_dict_modules()
        for module_description in modules_list:
            class_name = module_description.get("module")
            if not class_name.startswith("Module"):
                class_name = f'Module{class_name}'
            if class_name in available_modules:
                _module = available_modules.get(class_name)()
            else:
                _module = ModuleGeneric()
            _module.read_data_from_dict(module_dict=module_description)
            self.modules.append(_module)

    def read_data_from_dict(self, module_dict):
        """
        Reads the data from a project dictionary and updates the values of this project to match it.
        Args:
            module_dict (dict): A dictionary describing the project data. e.g. {"name": "untitled", "modules": ...}
        Returns:
            RigProject: This project (self)
        """
        self.modules = []
        self.metadata = None

        if module_dict and not isinstance(module_dict, dict):
            logger.debug(f'Unable o read data from dict. Input must be a dictionary.')
            return

        _name = module_dict.get('name')
        if _name:
            self.set_name(name=_name)

        _prefix = module_dict.get('prefix')
        if _prefix:
            self.set_prefix(prefix=_prefix)

        _modules = module_dict.get('modules')
        if _modules and isinstance(_modules, list):
            self.read_modules_from_dict(modules_list=_modules)

        metadata = module_dict.get('metadata')
        if metadata:
            self.set_metadata_dict(metadata=metadata)
        return self

    def read_data_from_scene(self):
        """
        Attempts to find the proxies within modules that are present in the scene. If found, their data is extracted.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Returns:
            RigProject: This object (self)
        """
        for module in self.modules:
            module.read_data_from_scene()
        return self

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_name(self):
        """
        Gets the name property of the rig project.
        Returns:
            str or None: Name of the rig project, None if it's not set.
        """
        return self.name

    def get_prefix(self):
        """
        Gets the prefix property of the rig project.
        Returns:
            str or None: Prefix of the rig project, None if it's not set.
        """
        return self.prefix

    def get_modules(self):
        """
        Gets the modules of this rig project.
        Returns:
            list: A list of modules found in this project
        """
        return self.modules

    def get_module_from_proxy_uuid(self, uuid):
        """
        Returns a module in case a proxy with the provided UUID is found within this project.
        Returns:
            ModuleGeneric or None: The module that contains the provided UUID, None otherwise.
        """
        for module in self.modules:
            if module.get_proxy_uuid_existence(uuid):
                return module

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_project_as_dict(self):
        """
        Gets the description for this project (including modules and its proxies) as a dictionary.
        Returns:
            dict: Dictionary describing this project.
        """
        project_modules = []
        for module in self.modules:
            project_modules.append(module.get_module_as_dict())

        project_data = {}
        if self.name:
            project_data["name"] = self.name
        if self.prefix:
            project_data["prefix"] = self.prefix
        project_data["modules"] = project_modules
        if self.metadata:
            project_data["metadata"] = self.metadata
        return project_data

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig project is valid (can be used)
        """
        if not self.modules:
            logger.warning('Missing modules. A rig project needs at least one module to function.')
            return False
        return True

    def build_proxy(self, optimized=False):
        """
        Builds Proxy/Guide Armature. This later becomes the skeleton that is driven by the rig controls.
        """
        cmds.refresh(suspend=True)
        try:
            root_group = create_root_group(is_proxy=True)
            root_transform = create_proxy_root_curve()
            hierarchy_utils.parent(source_objects=root_transform, target_parent=root_group)
            category_groups = create_utility_groups(line=True, target_parent=root_group)
            line_grp = category_groups.get(RiggerConstants.REF_ATTR_LINES)
            attr_to_activate = ['overrideEnabled', 'overrideDisplayType', "hiddenInOutliner"]
            set_attr(obj_list=line_grp, attr_list=attr_to_activate, value=1)
            add_attr(obj_list=str(root_transform),
                     attributes="linesVisibility",
                     attr_type="bool",
                     default=True)
            cmds.connectAttr(f'{root_transform}.linesVisibility', f'{line_grp}.visibility')

            # Build Proxy
            proxy_data_list = []
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                proxy_data_list += module.build_proxy(optimized=optimized)

            for proxy_data in proxy_data_list:
                add_side_color_setup(obj=proxy_data.get_long_name())
                hierarchy_utils.parent(source_objects=proxy_data.get_setup(), target_parent=line_grp)
                hierarchy_utils.parent(source_objects=proxy_data.get_offset(), target_parent=root_transform)

            # Parent Proxy
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                parent_proxies(proxy_list=module.get_proxies())
                if not optimized:
                    create_proxy_visualization_lines(proxy_list=module.get_proxies(), lines_parent=line_grp)
                for proxy in module.get_proxies():
                    proxy.apply_attr_dict()
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                module.build_proxy_setup()

            cmds.select(clear=True)
        except Exception as e:
            raise e
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh()

    def build_rig(self, delete_proxy=True):
        """
        Builds Rig using Proxy/Guide Armature/Skeleton (from previous step (build_proxy)
        """
        cmds.refresh(suspend=True)
        try:
            root_group = create_root_group()
            root_ctrl = create_control_root_curve()
            dir_ctrl = create_direction_curve()
            category_groups = create_utility_groups(geometry=True,
                                                    skeleton=True,
                                                    control=True,
                                                    setup=True,
                                                    target_parent=root_group)
            control_grp = category_groups.get(RiggerConstants.REF_ATTR_CONTROL)
            setup_grp = category_groups.get(RiggerConstants.REF_ATTR_SETUP)
            set_attr(obj_list=setup_grp, attr_list=['overrideEnabled', 'overrideDisplayType'], value=1)
            hierarchy_utils.parent(source_objects=list(category_groups.values()), target_parent=root_group)
            hierarchy_utils.parent(source_objects=root_ctrl, target_parent=control_grp)
            hierarchy_utils.parent(source_objects=dir_ctrl, target_parent=root_ctrl)

            # ------------------------------------- Build Skeleton
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                module.build_skeleton_joints()

            # ------------------------------------- Build Skeleton Hierarchy
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                module.build_skeleton_hierarchy()

            # ------------------------------------- Build Rig
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                module.build_rig()

            # ------------------------------------- Build Rig Post
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                module.build_rig_post()

            # Delete Proxy
            if delete_proxy:
                proxy_root = find_proxy_root_group()
                if proxy_root:
                    cmds.delete(proxy_root)
        except Exception as e:
            raise e
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh()
            cmds.select(clear=True)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    # from gt.tools.auto_rigger.template_biped import create_template_biped
    # a_biped_project = create_template_biped()
    # a_biped_project.build_proxy(optimized=True)
    # a_biped_project.build_rig()

    root = Proxy(name="root")
    root.set_meta_purpose("root")
    a_1st_proxy = Proxy(name="first")
    a_1st_proxy.set_position(y=5, x=-1)
    a_1st_proxy.set_parent_uuid_from_proxy(root)
    a_2nd_proxy = Proxy(name="second")
    a_2nd_proxy.set_position(x=-10)
    a_2nd_proxy.set_rotation(z=-35)
    a_2nd_proxy.set_parent_uuid(a_1st_proxy.get_uuid())

    a_root_module = ModuleGeneric()
    a_root_module.add_to_proxies(root)
    test = cmds.polySphere()
    a_root_module.add_driver_uuid_attr(test[0], "fk", root)

    a_module = ModuleGeneric()
    print(a_module._assemble_ctrl_name(name="test"))
    a_module.add_to_proxies(a_1st_proxy)
    a_module.add_to_proxies(a_2nd_proxy)
    # a_module.set_prefix("prefix")
    a_new_proxy = a_module.add_new_proxy()
    a_new_proxy.set_position(x=-15, y=-5)
    a_new_proxy.set_parent_uuid_from_proxy(a_2nd_proxy)

    another_module = ModuleGeneric()
    another_proxy = Proxy(name="another")
    another_proxy.set_position(y=-5)
    another_module.add_to_proxies(another_proxy)
    # a_module.set_orientation_direction(True)

    a_project = RigProject()
    a_project.add_to_modules(a_root_module)
    a_project.add_to_modules(a_module)
    a_project.add_to_modules(another_module)
    from pprint import pprint
    # pprint(a_project.get_modules())
    a_project.get_project_as_dict()
    a_project.build_proxy()
    a_project.build_rig(delete_proxy=True)
