"""
Auto Rigger Base Framework module.

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

Import Line:
    import gt.tools.auto_rigger.rig_framework as tools_rig_frm
"""

import gt.tools.auto_rigger.control_rig_pose as tools_control_pose
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.transform as core_trans
import gt.core.iterable as core_iter
import gt.core.rigging as core_rigging
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.utils.system as utils_sys
import gt.core.control as core_ctrl
import gt.core.curve as core_curve
import gt.core.joint as core_joint
import gt.core.pose as core_pose
import gt.core.color as core_color
import gt.core.logger as core_log
import gt.core.attr as core_attr
import gt.core.node as core_node
import gt.core.uuid as core_uuid
import gt.core.str as core_str
import gt.core.io as core_io
from dataclasses import dataclass
import maya.cmds as cmds
import dataclasses
import datetime
import logging
import socket
import json
import copy
import re
import os

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, console_level=logging.INFO, propagate=False)
core_log.add_custom_log_levels()


# ----------------------------------------------- Data Objects -----------------------------------------------
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
        from gt.core.naming import get_short_name

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

    def __init__(
        self, method=Methods.automatic, aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 1, 0), world_aligned=False
    ):
        """
        Initializes an OrientationData object.

        Args:
            method (Methods, optional): The method used for orientation calculation. Defaults to Methods.automatic.
            aim_axis (tuple, optional): The axis the joints should aim at in XYZ. Defaults to X+ (1, 0, 0).
                Commonly used as twist joint (aims towards its child).
            up_axis (tuple, optional): The axis pointing upwards for the joints. Defaults to (0, 1, 0).
            up_dir (tuple, optional): The up direction vector. Defaults to (0, 1, 0).
            world_aligned (bool, optional): Whether the orientation should be world aligned. Defaults to False.
        """
        self.method = None
        self.aim_axis = None
        self.up_axis = None
        self.up_dir = None
        self.world_aligned = False
        self.set_method(method)
        self.set_aim_axis(aim_axis)
        self.set_up_axis(up_axis)
        self.set_up_dir(up_dir)
        self.set_world_aligned(world_aligned)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_method(self, method):
        """
        This will define how the values are applied or not applied.
        Args:
            method (str, None): Orientation method. This will define how the values are applied or not applied.
        """
        if not method or not isinstance(method, str):
            logger.debug("Unable to set orientation. Method must be a string.")
            return
        available_methods = self.get_available_methods()
        if method not in available_methods:
            valid_orientations_str = '", "'.join(available_methods)
            logger.debug(f'Unable to set orientation. Input must be a recognized string: "{valid_orientations_str}".')
            return
        if method:
            self.method = method

    def set_aim_axis(self, aim_axis):
        """
        Sets the aim axis for the orientation data
        Args:
            aim_axis (tuple): The axis the joints should aim at in XYZ. e.g. for X+ (1, 0, 0).
                                        Commonly used as twist joint (aims towards its child)
        """
        if not aim_axis or not isinstance(aim_axis, tuple) or not len(aim_axis) == 3:
            logger.debug(f"Unable to set aim axis. Input must be a tuple/list with 3 digits.")
            return
        self.aim_axis = aim_axis

    def set_up_axis(self, up_axis):
        """
        Sets the up axis for the orientation data (determines if positive or negative for example)
        Args:
            up_axis (tuple): The axis pointing upwards for the joints in XYZ.
        """
        if not up_axis or not isinstance(up_axis, tuple) or not len(up_axis) == 3:
            logger.debug(f"Unable to set up axis. Input must be a tuple/list with 3 digits.")
            return
        self.up_axis = up_axis

    def set_up_dir(self, up_dir):
        """
        Sets the up direction for the orientation data
        Args:
            up_dir (tuple): The axis pointing upwards for the joints in XYZ.
        """
        if not up_dir or not isinstance(up_dir, tuple) or not len(up_dir) == 3:
            logger.debug(f"Unable to set up direction. Input must be a tuple/list with 3 digits.")
            return
        self.up_dir = up_dir

    def set_world_aligned(self, world_aligned):
        """
        Sets the world align flag. This aligns the joint to the world (not its orientation)
        Args:
            world_aligned (bool): If True, joints will be aligned to the world.
        """
        if not isinstance(world_aligned, bool):
            logger.debug(f"Unable to set world aligned flag. Input must be a boolean. (True or False)")
            return
        self.world_aligned = world_aligned

    def set_data_from_dict(self, orient_dict):
        """
        Sets the orientation data from a dictionary.
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

        _world_aligned = orient_dict.get("world_aligned")
        if _world_aligned:
            self.set_world_aligned(_world_aligned)

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

    def get_world_aligned(self):
        """
        Gets the world aligned value (True or False)
        Returns:
            bool: A boolean with the value stored for the flag "world_aligned"
        """
        return self.world_aligned

    def get_available_methods(self):
        """
        Gets a list of all available methods. These are the same as the attributes under the subclass "Methods"
        Returns:
            list: A list of available methods (these are strings)
                  Further description for each method can be found under the "Methods" class.
        """
        methods = []
        attrs = vars(self.Methods)
        attrs_keys = [attr for attr in attrs if not (attr.startswith("__") and attr.endswith("__"))]
        for key in attrs_keys:
            methods.append(getattr(self.Methods, key))
        return methods

    def get_data_as_dict(self):
        """
        Gets the orientation data as a dictionary.
        Returns:
            dict: A dictionary containing the entire orientation description.
        """
        _data = {
            "method": self.method,
            "aim_axis": self.aim_axis,
            "up_axis": self.up_axis,
            "up_dir": self.up_dir,
            "world_aligned": self.world_aligned,
        }
        return _data

    # -------------------------------------------------- Utils --------------------------------------------------
    def __repr__(self):
        """
        String conversion returns the orientation data
        Returns:
            str: Formatted orientation data.
        """
        return (
            f"Method: {str(self.method)} ("
            f"aim_axis={str(self.aim_axis)}, "
            f"up_axis={str(self.up_axis)}, "
            f"up_dir={str(self.up_dir)}), "
            f"world_aligned={str(self.world_aligned)})"
        )

    def apply_automatic_orientation(self, joint_list):
        """
        Orients the provided joints, as long as the defined method is set to automatic.
        Args:
            joint_list (list): A list of joints to be oriented.
        """
        if not self.get_method() == self.Methods.automatic:
            logger.debug(f"Method not set to automatic. Auto orientation call was ignored.")
            return
        core_joint.orient_joint(
            joint_list,
            aim_axis=self.aim_axis,
            up_axis=self.up_axis,
            up_dir=self.up_dir,
            world_aligned=self.world_aligned,
        )


class CodeData:
    """
    CodeData object.
    """

    class Order:
        """
        List of recognized/accepted order to apply
           "pre_proxy", : Before the creation of the proxy (or the entire rig)
           "post_proxy", After the creation of the proxy
           "pre_skeleton", Before the creation of the skeleton
           "post_skeleton", After the creation of the skeleton
           "pre_control_rig", Before the creation of the control rig
           "post_control_rig" After the creation of the control rig
           "post_build" After the creation of the rig is complete (all phases)
        """

        # Build Proxy Phase
        pre_proxy = "pre_proxy"
        post_proxy = "post_proxy"
        # Build Skeleton Phase
        pre_skeleton = "pre_skeleton"
        post_skeleton = "post_skeleton"
        # Build Pose Phase - Always executed in the bind pose and final control-build pose respectively
        pre_control_pose = "pre_control_pose"  # Bind pose
        post_control_pose = "post_control_pose"  # Final pose used to build controls
        # Build Control Rig Phase - Not executed if control rig is not created
        pre_control_rig = "pre_control_rig"
        post_control_rig = "post_control_rig"
        # Outside Build Phase - Executed even if build control rig is deactivated
        post_build = "post_build"

    def __init__(self, order=Order.pre_proxy, code=""):
        """
        Initializes a CodeData object with the specified execution order and code.

        Args:
            order (Order, optional): The execution order for the code. Defaults to Order.pre_proxy.
            code (str, optional): The code to execute. Defaults to an empty string.
        """
        self.order = None
        self.code = ""
        self.set_order(order=order)
        self.set_execution_code(code=code)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_order(self, order):
        """
        This will define the order when the code is executed
        Args:
            order (str, None): Order method. This will when the code is executed when the rig is built.
        """
        if not order or not isinstance(order, str):
            logger.debug("Unable to set order. Order must be a string.")
            return
        available_order_items = self.get_available_order_items()
        if order not in available_order_items:
            valid_orientations_str = '", "'.join(available_order_items)
            logger.debug(f'Unable to set order. Input must be a recognized string: "{valid_orientations_str}".')
            return
        if order:
            self.order = order

    def set_execution_code(self, code):
        """
        Sets the code to be executed.
        Args:
            code (str, callable): A string written in python to be executed according to the set order
                                     or a function to be called.
        """
        if callable(code):
            self.code = code
            return
        if isinstance(code, str):
            self.code = code
            return
        logger.warning(f"Unable to set execution code. Input must be a string or a callable object.")

    def set_data_from_dict(self, code_dict):
        """
        Sets the code data from a dictionary.
        Args:
            code_dict (dict): A dictionary describing the desired code and order.
        """
        if not code_dict or not isinstance(code_dict, dict):
            return

        _order = code_dict.get("order")
        if _order:
            self.set_order(_order)

        _code = code_dict.get("code")
        if _code:
            self.set_execution_code(_code)

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_order(self):
        """
        Gets the current order execution order for this CodeData object. See the class "Order" for more details.
        Returns:
            str: The method defined for this orientation.
        """
        return self.order

    def get_execution_code(self):
        """
        Gets the stored execution code.
        Returns:
            str or callable: A string with the stored code or a function to be called.
        """
        return self.code

    @staticmethod
    def get_available_order_items():
        """
        Gets a list of all available order items. These are the same as the attributes under the subclass "Order"
        Returns:
            list: A list of available order items (these are strings)
                  Further description for each method can be found under the "Order" class.
        """
        order_items = []
        attrs = vars(CodeData.Order)
        attrs_keys = [attr for attr in attrs if not (attr.startswith("__") and attr.endswith("__"))]
        for key in attrs_keys:
            order_items.append(getattr(CodeData.Order, key))
        return order_items

    def get_data_as_dict(self):
        """
        Gets the code data as a dictionary.
        Returns:
            dict or None: A dictionary containing the entire code data description or None if it's a callable object.
        """
        if callable(self.code):
            _data = {
                "order": self.order,
            }
        else:
            _data = {
                "order": self.order,
                "code": self.code,
            }
        return _data

    # -------------------------------------------------- Utils --------------------------------------------------
    def __repr__(self):
        """
        String conversion returns the code data
        Returns:
            str: Formatted code data.
        """
        return f"order={str(self.order)}/ncode={str(self.code)}"

    def execute_code(self, use_maya_warning=False, verbose=True, log_level=logging.WARNING, raise_errors=False):
        """
        Executes the given Python code string in the Maya environment.

        Args:
            use_maya_warning (bool, optional): If active it will log using a "cmds.warning()"
            verbose (bool, optional): If active, it will return messages
            log_level (int, optional): Logging level (only used if verbose is active)
            raise_errors (bool, optional): If active, it will raise errors instead of just giving messages.
        Return:
            any or None: When using a callable function it can potentially return whatever the called function returns.
                         When using a string, nothing is returned.
        """
        if callable(self.code):
            return self.code()
        utils_sys.execute_python_code(
            code=self.code,
            custom_logger=logger,
            use_maya_warning=use_maya_warning,
            log_level=log_level,
            verbose=verbose,
            import_cmds=True,
            exec_globals=globals,
            raise_errors=raise_errors,
        )


@dataclass
class RigPreferencesData:
    """RigPreferencesData describes preferences to be used by a RigProject"""

    build_control_rig: bool = dataclasses.field(default=True)  # If True, Control rig is built
    delete_proxy_after_build: bool = dataclasses.field(default=True)  # If True, proxy is deleted after build
    apply_control_rig_pose: bool = dataclasses.field(default=False)  # If True, pose proxy/joints before building rig
    control_rig_pose_mode: str = dataclasses.field(default=tools_control_pose.ControlRigPoseMode.DISABLED)
    hide_skeleton: bool = dataclasses.field(default=True)  # If True, hides skeleton group during build
    view_fit_skeleton: bool = dataclasses.field(default=True)  # If True, viewFit the skeleton after creation
    export_anim_blendshapes: bool = dataclasses.field(default=False)  # If True, include BS in the anim export process
    control_rig_pose_name: str = dataclasses.field(default=core_naming.NamingConstants.Poses.TPOSE)
    project_dir: str = dataclasses.field(
        default="{project-file-dir}"
    )  # Path to the current project. (Used for environment variable)
    alias: str = dataclasses.field(default=None)  # Project alias.

    def get_data_as_dict(self):
        """
        Gets all preferences as a dictionary.
        Returns:
            dict: A dictionary describing all preferences listed on this preferences data object.
        """
        return dataclasses.asdict(self)

    def read_data_from_dict(self, data):
        """
        Modifies this object to match the data received. (Used to export and import preferences)
        Args:
            data (dict): A dictionary with attributes as keys and values for the preferences as their value.
                        e.g. {"build_control_rig": True}
        """
        if not isinstance(data, dict):
            return

        for key, value in data.items():
            if key == "project_dir" and not value:
                value = "{project-file-dir}"
            if hasattr(self, key):
                setattr(self, key, value)

        mode = data.get("control_rig_pose_mode")
        if not tools_control_pose.ControlRigPoseMode.is_valid(mode):
            apply_pose = data.get("apply_control_rig_pose", self.apply_control_rig_pose)
            mode = (
                tools_control_pose.ControlRigPoseMode.AUTOMATIC
                if apply_pose
                else tools_control_pose.ControlRigPoseMode.DISABLED
            )
        self.control_rig_pose_mode = mode
        self.apply_control_rig_pose = mode != tools_control_pose.ControlRigPoseMode.DISABLED

    def list_available_preferences(self):
        """
        Lists available attributes (preferences)
        Returns:
            list: A list of the attributes found in this class, which is also the list of available preferences.
        """
        return list(self.__dict__.keys())


# ------------------------------------------------- Framework -------------------------------------------------
class Proxy:
    def __init__(self, name=None, uuid=None):
        """
        Initialize a Proxy object representing a proxy item in the rig.

        Args:
            name (str, optional): Name of the proxy. Defaults to "proxy" if not provided.
            uuid (str, optional): UUID to assign to the proxy. Generated if not provided.
        """
        # Default Values
        self.name = "proxy"
        self.transform = None
        self.offset_transform = None
        self.curve = core_curve.get_curve("_proxy_joint")
        self.curve.set_name(name=self.name)
        self.uuid = core_uuid.generate_uuid(remove_dashes=True)
        # parent_uuid defines a parent relation, used to define the skeleton hierarchy later in the rig process.
        self.parent_uuid = None
        self.attr_dict = {}
        self.set_locator_scale(scale=1)  # 100% - Initial curve scale
        self.metadata = None
        # _setup_driver_uuid defines the parent relation between the proxy items, according to how they drive
        # each other. It doesn't need to be defined, in that case inherits the parent_uuid relation.
        self._setup_driver_uuid = None

        if name:
            self.set_name(name)
        if uuid:
            self.set_uuid(uuid)

    def is_valid(self):
        """
        Checks if the current proxy element is valid
        """
        if not self.name:
            logger.warning("Invalid proxy object. Missing name.")
            return False
        if not self.curve:
            logger.warning("Invalid proxy object. Missing curve.")
            return False
        return True

    def build(self, prefix=None, suffix=None, apply_transforms=False, use_naming_attrs=False, optimized=False):
        """
        Builds a proxy object.
        Args:
            prefix (str, optional): If provided, this prefix will be added to the proxy when it's created.
            suffix (str, optional): If provided, this suffix will be added to the proxy when it's created.
            apply_transforms (bool, optional): If True, the creation of the proxy will apply transform values.
                                               Used by modules to only apply transforms after setup. (post script)
            use_naming_attrs (bool, optional): If true, it will check the proxy data for a suffix and prefix
                                               attribute, which allows for overrides.
            optimized (bool, optional): If True, the module will skip display operations, such as curve creation,
                                        the addition of a snapping shape or the scale cluster and others.
                                        Useful for when building a rig without adjusting the proxy.
        Returns:
            ProxyData: Name of the proxy that was generated/built.
        """
        if not self.is_valid():
            logger.warning(f"Unable to build proxy. Invalid proxy object.")
            return

        # Resolve Full Name
        resolved_name = self.name
        # Is using Proxy Unique prefix/suffix override?
        unique_prefix = self.get_attr_dict_value(key="prefix")
        if unique_prefix and use_naming_attrs is True:
            prefix = unique_prefix
        unique_suffix = self.get_attr_dict_value(key="suffix")
        if unique_suffix and use_naming_attrs is True:
            suffix = unique_suffix
        # Is it using module prefix/suffix? (Unique prefix/suffix has priority.
        if prefix and isinstance(prefix, str):
            resolved_name = f"{prefix}_{resolved_name}"
            self.curve.set_name(resolved_name)
        if suffix and isinstance(suffix, str):
            resolved_name = f"{resolved_name}_{suffix}"
            self.curve.set_name(resolved_name)

        # Create Offset
        proxy_offset = cmds.group(
            name=f"{resolved_name}_{core_naming.NamingConstants.Suffix.OFFSET}",
            world=True,
            empty=True,
        )

        if optimized:
            proxy_crv = cmds.group(name=self.curve.get_name(), world=True, empty=True)
        else:
            proxy_crv = self.curve.build()
            core_ctrl.add_snapping_shape(proxy_crv)
        if prefix:
            self.curve.set_name(self.name)  # Restore name without prefix
        proxy_crv = cmds.parent(proxy_crv, proxy_offset)[0]
        proxy_offset = core_naming.get_long_name(proxy_offset)
        proxy_crv = core_node.Node(proxy_crv)

        # Enforce Name (Fixes issues with merged shapes or reserved strings)
        if resolved_name != proxy_crv.get_short_name():
            proxy_crv.rename(resolved_name)
            logger.debug(f'Curve was renamed to match proxy: From "{proxy_crv}" to "{resolved_name}".')

        # Store Base Metadata ----------------------------------------------------------------------------------
        core_attr.add_attr(
            obj_list=proxy_crv,
            attributes=tools_rig_const.RiggerConstants.ATTR_BASE_NAME,
            attr_type="string",
            verbose=False,
            default=self.name,
        )
        core_attr.add_attr(
            obj_list=proxy_crv,
            attributes=tools_rig_const.RiggerConstants.ATTR_PREFIX,
            attr_type="string",
            verbose=False,
            default=prefix or "",
        )
        core_attr.add_attr(
            obj_list=proxy_crv,
            attributes=tools_rig_const.RiggerConstants.ATTR_SUFFIX,
            attr_type="string",
            verbose=False,
            default=suffix or "",
        )
        uuid_attrs = core_uuid.add_uuid_attr(
            obj_list=str(proxy_crv),
            attr_name=tools_rig_const.RiggerConstants.ATTR_PROXY_UUID,
            set_initial_uuid_value=False,
        )
        # Keyable Attributes -------------------------------------------------------------------------------------
        core_attr.add_separator_attr(
            target_object=proxy_crv,
            attr_name=f"proxy{core_str.upper_first_char(core_rigging.RiggingConstants.SEPARATOR_CONTROL)}",
        )
        rot_order_attr = (
            core_attr.add_attr(
                obj_list=proxy_crv,
                attributes=tools_rig_const.RiggerConstants.ATTR_ROT_ORDER,
                attr_type="enum",
                enum="xyz:yzx:zxy:xzy:yxz:zyx",
                default=0,
            )
            or []
        )
        scale_attr = (
            core_attr.add_attr(
                obj_list=proxy_crv, attributes=tools_rig_const.RiggerConstants.ATTR_PROXY_SCALE, default=1
            )
            or []
        )
        loc_scale_cluster = None
        if not optimized and scale_attr and len(scale_attr) == 1:
            scale_attr = scale_attr[0]
            loc_scale_cluster = core_curve.add_shape_scale_cluster(proxy_crv, scale_driver_attr=scale_attr)
        for attr in uuid_attrs:
            core_attr.set_attr(attribute_path=attr, value=self.uuid)
        # Set Transforms
        if self.offset_transform and apply_transforms:
            self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if self.transform and apply_transforms:
            self.transform.apply_transform(target_object=proxy_crv, world_space=True)
        # Set Rotation Order
        if self.get_attr_dict_value(tools_rig_const.RiggerConstants.ATTR_ROT_ORDER) is not None:
            _rot_order = self.get_rotation_order()
            core_attr.set_attr(rot_order_attr, _rot_order)
        # Set Locator Scale
        if self.get_attr_dict_value(tools_rig_const.RiggerConstants.ATTR_PROXY_SCALE) is not None:
            _locator_scale = self.get_locator_scale()
            core_attr.set_attr(scale_attr, _locator_scale)

        return ProxyData(name=str(proxy_crv), offset=proxy_offset, setup=(loc_scale_cluster,), uuid=self.get_uuid())

    def apply_offset_transform(self):
        """
        Attempts to apply transform values to the offset of the proxy.
        To be used only after proxy is built.
        """
        proxy_crv = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.uuid)
        if proxy_crv:
            proxy_offset = tools_rig_utils.get_proxy_offset(proxy_crv)
            if proxy_offset and self.offset_transform:
                self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)

    def apply_transforms(self, apply_offset=False):
        """
        Attempts to apply offset and parent offset transforms to the proxy elements.
        To be used only after proxy is built.
        Args:
            apply_offset (bool, optional): If True, it will attempt to also apply the offset data. (Happens first)
        """
        proxy_crv = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.uuid)
        if proxy_crv and apply_offset:
            proxy_offset = tools_rig_utils.get_proxy_offset(proxy_crv)
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
            target_obj = tools_rig_utils.find_proxy_from_uuid(self.get_uuid())
        if not target_obj or not cmds.objExists(target_obj):
            logger.debug(f"Unable to apply proxy attributes. Failed to find target object.")
            return
        if self.attr_dict:
            for attr, value in self.attr_dict.items():
                core_attr.set_attr(obj_list=str(target_obj), attr_list=str(attr), value=value)

    def _initialize_transform(self):
        """
        In case a transform is necessary and none is present,
        a default Transform object is created and stored in "self.transform".
        """
        if not self.transform:
            self.transform = core_trans.Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)

    def _initialize_offset_transform(self):
        """
        In case an offset transform is necessary and none is present,
        a default Transform object is created and stored in "self.offset_transform".
        """
        if not self.offset_transform:
            self.offset_transform = core_trans.Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)

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
        if not transform or not isinstance(transform, core_trans.Transform):
            logger.warning(
                f"Unable to set proxy transform. " f'Must be a "Transform" object, but got "{str(type(transform))}".'
            )
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
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
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
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
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
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
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
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_offset_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, core_trans.Transform):
            logger.warning(
                f"Unable to set proxy transform. " f'Must be a "Transform" object, but got "{str(type(transform))}".'
            )
            return
        self.offset_transform = transform

    def set_offset_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
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
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
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
            xyz (Vector3, list, tuple): A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_curve(self, curve, inherit_curve_name=False):
        """
        Sets the curve used to build the proxy element
        Args:
            curve (Curve): A Curve object to be used for building the proxy element (its shape)
            inherit_curve_name (bool, optional): If active, this function try to extract the name of the curve and
                                                 change the name of the proxy to match it. Does nothing if name is None.
        """
        if not curve or not isinstance(curve, core_curve.Curve):
            logger.debug(f"Unable to set proxy curve. Invalid input. Must be a valid Curve object.")
            return
        if not curve.is_curve_valid():
            logger.debug(f"Unable to set proxy curve. Curve object failed validation.")
            return
        if inherit_curve_name:
            self.set_name(curve.get_name())
        else:
            curve.set_name(name=self.name)
        self.curve = curve

    def set_locator_scale(self, scale):
        """
        Defines the locator scale by creating a locatorScale attribute with the provided value.
        Args:
            scale (int, float): locator scale value, this value also determines the radius of the joint.
        """
        if not isinstance(scale, (float, int)):
            logger.debug(f"Unable to set locator scale. Invalid input.")
        self.add_to_attr_dict(attr=tools_rig_const.RiggerConstants.ATTR_PROXY_SCALE, value=scale)

    def set_rotation_order(self, rotation_order):
        """
        Defines the rotation order by creating a rotationOrder attribute with the provided value.
        Args:
            rotation_order (int, str): The rotation order from 0 to 5 or a string describing the rotation order.
                                       e.g. "xyz", "yzx", "zxy", "xzy", "yxz", "zyx"
        """
        _rot_order_str_list = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]

        if isinstance(rotation_order, int):
            if 0 <= rotation_order < len(_rot_order_str_list):
                _rot_order = rotation_order
            else:
                logger.warning("Invalid integer for rotation order. Must be between 0 and 5.")
                return
        elif isinstance(rotation_order, str):
            rotation_order = rotation_order.lower()
            if rotation_order in _rot_order_str_list:
                _rot_order = _rot_order_str_list.index(rotation_order)
            else:
                logger.warning(f"Invalid string for rotation order. Must be one of {_rot_order_str_list}.")
                return
        else:
            logger.warning("Rotation order must be either an integer or a string.")
            return

        self.add_to_attr_dict(attr=tools_rig_const.RiggerConstants.ATTR_ROT_ORDER, value=_rot_order)

    def set_attr_dict(self, attr_dict):
        """
        Sets the attributes dictionary for this proxy. Attributes are any key/value pairs further describing the proxy.
        Args:
            attr_dict (dict): An attribute dictionary where the key is the attribute and value is the attribute value.
                              e.g. {"locatorScale": 1, "isVisible": True}
        """
        if not isinstance(attr_dict, dict):
            logger.warning(
                f"Unable to set attribute dictionary. " f'Expected a dictionary, but got: "{str(type(attr_dict))}"'
            )
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
        if isinstance(line_parent, str) and core_uuid.is_uuid_valid(line_parent):
            self.metadata[tools_rig_const.RiggerConstants.META_PROXY_LINE_PARENT] = line_parent
        if isinstance(line_parent, Proxy):
            self.metadata[tools_rig_const.RiggerConstants.META_PROXY_LINE_PARENT] = line_parent.get_uuid()

    def add_driver_type(self, driver_type):
        """
        Adds a type/tag to the list of drivers. Initializes metadata in case it was not yet initialized.
        A type/tag is used to determine controls driving the joint generated from this proxy
        A proxy generates a joint, this joint can driven by multiple controls, the tag helps identify them.
        Args:
            driver_type (str, list): New type/tag to add. e.g. "fk", "ik", "offset", etc...
                              Can also be a list of new tags: e.g. ["fk", "ik"]
        """
        if isinstance(driver_type, str):
            driver_type = [driver_type]
        if not isinstance(driver_type, list) or driver_type is None:
            logger.debug(f"Invalid data type was provided. Add driver operation was skipped.")
            return
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        if isinstance(driver_type, str):
            driver_type = [driver_type]
        new_drivers = self.metadata.get(tools_rig_const.RiggerConstants.META_PROXY_DRIVERS, [])
        for driver_tag in driver_type:
            if driver_tag and isinstance(driver_tag, str) and driver_tag not in new_drivers:
                new_drivers.append(driver_tag)
        if new_drivers:
            self.metadata[tools_rig_const.RiggerConstants.META_PROXY_DRIVERS] = new_drivers

    def clear_driver_types(self):
        """
        Clears any driver tags found in the metadata.
        """
        if self.metadata:
            self.metadata.pop(tools_rig_const.RiggerConstants.META_PROXY_DRIVERS, None)

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
                logger.debug(f"Unable to set color. Input must contain only numeric values.")
        else:
            logger.debug(f"Unable to set color. Input must be a tuple or a list with at least 3 elements (RGB).")

    def set_uuid(self, uuid):
        """
        Sets a new UUID for the proxy.
        If no UUID is provided or set a new one will be generated automatically,
        this function is used to force a specific value as UUID.
        Args:
            uuid (str): A new UUID for this proxy
        """
        error_message = f"Unable to set proxy UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_uuid_valid(uuid) or core_uuid.is_short_uuid_valid(uuid):
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
        error_message = f"Unable to set proxy parent UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_uuid_valid(uuid) or core_uuid.is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

    def set_setup_driver_uuid(self, uuid):
        """
        Sets a setup driver UUID for the proxy.
        If a setup driver UUID is set, the hierarchy of the proxy items can be retrieved,
        it describes how they are linked together.
        Args:
            uuid (str): the UUID of the setup driver of this proxy
        """
        error_message = f"Unable to set proxy setup driver UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_uuid_valid(uuid) or core_uuid.is_short_uuid_valid(uuid):
            self._setup_driver_uuid = uuid
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
        error_message = f"Unable to set proxy parent UUID. Invalid proxy input."
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

    def clear_setup_driver_uuid(self):
        """
        Clears the driver UUID by setting the "driver_uuid" to None
        """
        self._setup_driver_uuid = None

    def set_meta_purpose(self, value):
        """
        Adds a proxy meta type key and value to the metadata dictionary. Used to define proxy type in modules.
        Args:
            value (str, optional): Type "tag" used to determine overwrites.
                                   e.g. "hip", so the module knows it's a "hip" proxy.
        """
        self.add_to_metadata(key=tools_rig_const.RiggerConstants.META_PROXY_PURPOSE, value=value)

    def read_data_from_dict(self, proxy_dict):
        """
        Reads the data from a proxy dictionary and updates the values of this proxy to match it.
        Args:
            proxy_dict (dict): A dictionary describing the proxy data. e.g. {"name": "proxy", "parent": "1234...", ...}
        Returns:
            Proxy: This object (self)
        """
        if proxy_dict and not isinstance(proxy_dict, dict):
            logger.debug(f"Unable o read data from dict. Input must be a dictionary.")
            return

        _name = proxy_dict.get("name")
        if _name:
            self.set_name(name=_name)

        _parent = proxy_dict.get("parent")
        if _parent:
            self.set_parent_uuid(uuid=_parent)

        transform = proxy_dict.get("transform")
        if transform and len(transform) == 3:
            self._initialize_transform()
            self.transform.set_transform_from_dict(transform_dict=transform)

        offset_transform = proxy_dict.get("offsetTransform")
        if offset_transform and len(offset_transform) == 3:
            self._initialize_offset_transform()
            self.offset_transform.set_transform_from_dict(transform_dict=transform)

        attributes = proxy_dict.get("attributes")
        if attributes:
            self.set_attr_dict(attr_dict=attributes)

        metadata = proxy_dict.get("metadata")
        if metadata:
            self.set_metadata_dict(metadata=metadata)

        _uuid = proxy_dict.get("uuid")
        if _uuid:
            self.set_uuid(uuid=_uuid)
        return self

    def read_data_from_scene(self, obj_path=None):
        """
        Attempts to find the proxy in the scene. If found, it reads the data into the proxy object.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Args:
            obj_path (str, optional): If provided, it reads the data from the provided object
                                      instead of trying to find it in the scene.
        Returns:
            Proxy: This object (self)
        """
        ignore_attr_list = [
            tools_rig_const.RiggerConstants.ATTR_PROXY_UUID,
        ]
        proxy = core_uuid.get_object_from_uuid_attr(
            uuid_string=self.uuid, attr_name=tools_rig_const.RiggerConstants.ATTR_PROXY_UUID
        )
        if obj_path:
            proxy = obj_path
        if proxy:
            try:
                self._initialize_transform()
                self.transform.set_transform_from_object(proxy)
                attr_dict = {}
                user_attrs = core_attr.list_user_defined_attr(proxy, skip_nested=True, skip_parents=False) or []
                for attr in user_attrs:
                    if not cmds.getAttr(f"{proxy}.{attr}", lock=True) and attr not in ignore_attr_list:
                        attr_dict[attr] = core_attr.get_attr(f"{proxy}.{attr}")
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
        return self.get_metadata_value(tools_rig_const.RiggerConstants.META_PROXY_LINE_PARENT)

    def get_meta_purpose(self):
        """
        Gets the meta purpose of this proxy (if present)
        Returns:
            str or None: The purpose of this proxy as stored in the metadata, otherwise None.
        """
        return self.get_metadata_value(tools_rig_const.RiggerConstants.META_PROXY_PURPOSE)

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

    def get_setup_driver_uuid(self):
        """
        Gets the driver uuid value of this proxy.
        Returns:
            str: uuid string for the potential driver of this proxy.
        """
        return self._setup_driver_uuid

    def get_attr_dict(self):
        """
        Gets the attribute dictionary for this proxy
        Returns:
            dict: a dictionary where the key is the attribute name and the value is the value of the attribute.
                  e.g. {"locatorScale": 1, "isVisible": True}
        """
        return self.attr_dict

    def get_attr_dict_value(self, key, default=None):
        """
        Gets a value from the attribute dictionary. If not found, the default value is returned instead.
        Args:
            key: (str): The attribute key. e.g. "locatorScale"
            default (any, optional): What is returned when a value is not found (missing key)
        Returns:
            any: Any data stored as a value for the provided key. If a key is not found the default
            parameter is returned instead.
        """
        return self.attr_dict.get(key, default)

    def get_locator_scale(self):
        """
        Gets the locator scale for this proxy. (a.k.a. Radius)
        Returns:
            float: The locator scale. If the key is not found the default of 1 is returned instead.
        """
        return self.get_attr_dict_value(tools_rig_const.RiggerConstants.ATTR_PROXY_SCALE, default=float(1))

    def get_rotation_order(self):
        """
        Gets the rotation order for this proxy.
        Returns:
            int: The rotation order. If the key is not found the default of 0 is returned instead.
        """
        return self.get_attr_dict_value(tools_rig_const.RiggerConstants.ATTR_ROT_ORDER, default=int(0))

    def get_driver_types(self):
        """
        Gets a list of available driver types. e.g.  ["fk", "ik", "offset"]
        Returns:
            list or None: A list of driver types (strings) otherwise None.
        """
        if self.metadata:
            return self.metadata.get(tools_rig_const.RiggerConstants.META_PROXY_DRIVERS, None)

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

        if self.transform and include_transform_data:
            proxy_data["transform"] = self.transform.get_transform_as_dict()

        if self.offset_transform and include_offset_data:
            proxy_data["offsetTransform"] = self.offset_transform.get_transform_as_dict()

        if self.get_attr_dict():
            proxy_data["attributes"] = self.get_attr_dict()

        if self.get_metadata():
            proxy_data["metadata"] = self.get_metadata()

        return proxy_data

    def get_mirrored_transform(self, plane="YZ", rotate_order="xyz", behaviour=True):
        """
        Gets the mirrored transform values in form of a Transform object.

        Args:
            plane (str): hyperplane used to mirror. Accepted values: "XY", "YZ", "XZ".
            rotate_order (str): the rotate order used to decompose the matrix in euler rotations.
                                Accepted values: "xyz", "yzx", "zxy", "xzy", "yxz", "zyx".
            behaviour (bool): if True sets the opposite orientation

        Returns:
            Transform object: instance of Transform
        """
        if plane not in ["XY", "YZ", "XZ"]:
            logger.warning("Given plane not valid. Please choose between 'XY', 'YZ', 'XZ'.")
            return
        if not rotate_order:
            logger.warning("Given rotate order is empty.")
            return
        if not isinstance(rotate_order, str):
            logger.warning("Given rotate order is not a string.")
            return

        rotate_order_options = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
        if rotate_order not in rotate_order_options:
            logger.warning(f"Rotate order must be one of the following values: {str(rotate_order_options)}")
            return

        matrix = self.transform.to_matrix(rotate_order=rotate_order)
        mirrored_matrix = core_trans.mirror_transform_matrix(matrix, plane=plane, behaviour=behaviour)
        mirrored_transform = core_trans.get_transform_from_matrix(mirrored_matrix, rotate_order=rotate_order)

        return mirrored_transform


class ModuleGeneric:
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_generic
    allow_parenting = True
    allow_multiple = True
    bypass_activation = False  # If True, this module cannot be activated/deactivated.

    def __init__(self, name=None, prefix=None, suffix=None):
        """
        Initialize a new module instance with optional name, prefix, and suffix.
        Sets default values for various attributes related to the module’s identity,
        hierarchy, proxies, and state.

        Args:
            name (str, optional): Custom name for the module. Defaults to None.
            prefix (str, optional): Prefix string for the module. Defaults to None.
            suffix (str, optional): Suffix string for the module. Defaults to None.
        """
        # Default Values
        self._project = None  # When assigned to a project. This becomes a reference to the project
        self.name = self.get_module_class_name(remove_module_prefix=True, formatted=True)
        self.uuid = core_uuid.generate_uuid(short=True, short_length=12)
        self.prefix = None
        self.suffix = None
        self.proxies = []
        self.parent_uuid = None
        self.mirror_uuid = None
        self.metadata = None
        self.active = True
        self.orientation = OrientationData()
        self.code = None
        self.expanded = True  # Tree Item State Collapsed/Expanded

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
        error_message = f"Unable to set module UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_short_uuid_valid(uuid, length=12):
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
        error_message = f"Unable to set proxy parent UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_uuid_valid(uuid) or core_uuid.is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

    def set_mirror_uuid(self, uuid):
        """
        Sets the module UUID used to mirror the proxies.

        Args:
            uuid (str): module UUID used to mirror
        """
        error_message = f"Unable to set the mirror module UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_uuid_valid(uuid) or core_uuid.is_short_uuid_valid(uuid):
            self.mirror_uuid = uuid
        else:
            logger.warning(error_message)

    def set_proxies(self, proxy_list):
        """
        Sets a proxy list for this module.
        Args:
            proxy_list (List[Proxy]): New list of proxies.
        """
        if not proxy_list or not isinstance(proxy_list, list):
            logger.warning(
                f"Unable to set new list of proxies. " f'Expected list of proxies but got "{str(proxy_list)}"'
            )
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
        logger.debug(
            f"Unable to add proxy to module. " f'Must be of the type "Proxy" or a list containing only Proxy elements.'
        )

    def add_new_proxy(self):
        """
        Adds a clear new proxy to the proxies list.
        Returns:
            Proxy: The created proxy
        """
        pattern = r"^proxy\d*$"
        proxy_names = [proxy.get_name() for proxy in self.proxies]
        valid_proxies = [item for item in proxy_names if re.match(pattern, item)]
        highest_proxy_num = core_iter.get_highest_int_from_str_list(valid_proxies)
        new_proxy = Proxy()
        if valid_proxies:
            new_proxy.set_name(f"proxy{str(highest_proxy_num + 1)}")
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
        logger.debug(f"Unable to remove proxy from module. Not found.")

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(
                f"Unable to set module metadata. " f'Expected a dictionary, but got: "{str(type(metadata))}"'
            )
            return
        self.metadata = metadata

    def set_active_state(self, is_active):
        """
        Sets the "is_active" variable. This variable determines if the module will be skipped while in a project or not.
        Args:
            is_active (bool): True if active, False if inactive. Inactive modules are ignored when in a project.
        """
        if not isinstance(is_active, bool):
            logger.warning(f"Unable to set active state. " f'Expected a boolean, but got: "{str(type(is_active))}"')
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
            _aim_axis = tuple(abs(value) * multiplier for value in _aim_axis)
            self.orientation.set_aim_axis(_aim_axis)
        if set_up_axis:
            _up_axis = self.orientation.get_up_axis()
            _up_axis = tuple(abs(value) * multiplier for value in _up_axis)
            self.orientation.set_up_axis(_up_axis)
        if set_up_dir:
            _up_dir = self.orientation.get_up_dir()
            _up_dir = tuple(abs(value) * multiplier for value in _up_dir)
            self.orientation.set_up_dir(_up_dir)

    def set_expanded_state(self, is_expanded):
        """
        Sets the "is_expanded" variable. This variable determines if the module tree item will expand when building UI.
        Args:
            is_expanded (bool): True if expanded, False if collapsed.
        """
        if not isinstance(is_expanded, bool):
            logger.warning(f"Unable to set expanded state. " f'Expected a boolean, but got: "{str(type(is_expanded))}"')
            return
        self.expanded = is_expanded

    def set_code_data(self, code_data):
        """
        Sets a CodeData object to be used by this module.
        Args:
            code_data (CodeData): A code data object describing order and python code to be executed
        """
        self.code = code_data

    def clear_code_data(self):
        """Clears the module CodeData object so no extra functions or code run"""
        self.code = None

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

    def set_extra_callable_function(self, callable_func, order=CodeData.Order.post_build):
        """
        Adds an extra function to be called through this module using the CodeData object.
        Args:
            callable_func (callable): A callable function.
            order (str, optional): The order in which the function will be called.
                                   By default, it will run after the control rig is fully built. (post_control_rig)
                                   Use CodeData.Order variables to set it to a different order or strings:
                                   "pre_proxy", : Before the creation of the proxy (or the entire rig)
                                   "post_proxy", After the creation of the proxy
                                   "pre_skeleton", Before the creation of the skeleton
                                   "post_skeleton", After the creation of the skeleton
                                   "pre_control_rig", Before the creation of the control rig
                                   "post_control_rig" After the creation of the control rig
                                   "post_build" After the creation of the rig is complete (all phases)
        """
        if not callable(callable_func):
            logger.warning(f"Unable to set callable function. Provided object is not callable.")
            return
        _code_data = CodeData()
        _code_data.set_order(order=order)
        _code_data.set_execution_code(callable_func)
        self.set_code_data(_code_data)

    def set_execution_code_order(self, order):
        """
        Changes the loading order used by this module
        Args:
            order (str, optional): The order in which the function will be called.
                                   By default, it will run after the control rig is fully built. (post_control_rig)
                                   Use CodeData.Order variables to set it to a different order or strings:
                                   "pre_proxy", : Before the creation of the proxy (or the entire rig)
                                   "post_proxy", After the creation of the proxy
                                   "pre_skeleton", Before the creation of the skeleton
                                   "post_skeleton", After the creation of the skeleton
                                   "pre_control_rig", Before the creation of the control rig
                                   "post_control_rig" After the creation of the control rig
                                   "post_build" After the creation of the rig is complete (all phases)
        """
        if self.code is not None and isinstance(self.code, CodeData):
            self.code.set_order(order=order)

    def set_parent_project(self, rig_project):
        """
        Sets a relationship with the project that contains this module. Set to None to remove relationship.
        Args:
            rig_project (RigProject, None): A RigProject (usually the one containing this module)
        """
        if rig_project is None:
            self._project = None
            return
        self._project = rig_project

    def _set_serialized_attrs(self, data):
        """
        Sets non-manually determined class attributes that exists in the class and in the provided data.
        Args:
            data (dict): A dictionary with attributes as keys and values for the preferences as their value.
                        e.g. {"build_control_rig": True}
        """
        if not isinstance(data, dict):
            logger.debug(f"Unable to read serialized extra attributes. Incorrect argument data type.")
            return
        _manually_serialized = tools_rig_const.RiggerConstants.CLASS_ATTR_SKIP_AUTO_SERIALIZATION
        for key, value in data.items():
            if hasattr(self, key) and key not in _manually_serialized:
                setattr(self, key, value)

    # ---------------------------------------------- Read Setters -----------------------------------------------
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
            logger.debug(f"Unable to read proxies from dictionary. Input must be a dictionary.")
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
            logger.debug(f"Unable o read data from dict. Input must be a dictionary.")
            return

        _name = module_dict.get("name")
        if _name:
            self.set_name(name=_name)

        _uuid = module_dict.get("uuid")
        if _uuid:
            self.set_uuid(uuid=_uuid)

        _prefix = module_dict.get("prefix")
        if _prefix is not None:
            self.set_prefix(prefix=_prefix)

        _suffix = module_dict.get("suffix")
        if _suffix is not None:
            self.set_suffix(suffix=_suffix)

        _parent = module_dict.get("parent")
        if _parent is not None:
            self.set_parent_uuid(uuid=_parent)

        _orientation = module_dict.get("orientation")
        if _orientation:
            self.orientation.set_data_from_dict(orient_dict=_orientation)

        _code = module_dict.get("code")
        if _code:
            if not isinstance(self.code, CodeData):
                _new_code_data = CodeData()
                _new_code_data.set_data_from_dict(code_dict=_code)
                self.set_code_data(code_data=_new_code_data)
            else:
                self.code.set_data_from_dict(code_dict=_code)

        # Load serialized configuration flags before rebuilding specialized proxy lists.
        # Modules such as Head use these flags to decide whether optional proxies belong
        # to the loaded project.
        self._set_serialized_attrs(module_dict)

        _proxies = module_dict.get("proxies")
        if _proxies and isinstance(_proxies, dict):
            self.read_proxies_from_dict(proxy_dict=_proxies)

        _is_active = module_dict.get("active")
        if isinstance(_is_active, bool):
            self.set_active_state(is_active=_is_active)

        _metadata = module_dict.get("metadata")
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
            meta_type = tools_rig_utils.get_meta_purpose_from_dict(metadata)
            if meta_type and isinstance(meta_type, str):
                proxy_type_link[meta_type] = proxy

        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            meta_type = tools_rig_utils.get_meta_purpose_from_dict(metadata)
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

    def get_proxies(self, sort_by=None):
        """
        Gets the proxies in this rig module.
        Args:
            sort_by (str): Accepted None, "parent" or "setup_driver". If parent the list will be sorted hierarchically.
        Returns:
            list: A list of proxies found in this rig module.
        """
        if not self.proxies:
            return self.proxies

        if sort_by == "setup_driver":
            driver_uuids = [prx.get_setup_driver_uuid() for prx in self.proxies]
            if any(driver_uuids):
                map_uuid_proxy = {prx.get_uuid(): prx for prx in self.proxies}
                map_uuid_proxy_driver = {}
                for prx in self.proxies:
                    if prx.get_setup_driver_uuid():
                        map_uuid_proxy_driver[prx.get_uuid()] = prx.get_setup_driver_uuid()
                    else:  # inherit parent_uuid
                        map_uuid_proxy_driver[prx.get_uuid()] = prx.get_parent_uuid()
                uuids_sorted_by_parent = core_hrchy.dict_parent_sort(map_uuid_proxy_driver)
                proxies_sorted_by_driver = [map_uuid_proxy[uuid] for uuid in uuids_sorted_by_parent]
                return proxies_sorted_by_driver
            else:
                sort_by = "parent"

        if sort_by == "parent":
            parent_uuids = [prx.get_parent_uuid() for prx in self.proxies]
            if any(parent_uuids):
                map_uuid_proxy = {prx.get_uuid(): prx for prx in self.proxies}
                map_uuid_proxy_parent = {prx.get_uuid(): prx.get_parent_uuid() for prx in self.proxies}
                uuids_sorted_by_parent = core_hrchy.dict_parent_sort(map_uuid_proxy_parent)
                proxies_sorted_by_parent = [map_uuid_proxy[uuid] for uuid in uuids_sorted_by_parent]
                return proxies_sorted_by_parent
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
        Args:
            uuid (str): The UUID to check.

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
            str or None: Orientation method description or None if an orientation was not set.
        """
        if isinstance(self.orientation, OrientationData):
            return self.orientation.get_method()
        else:
            return None

    def is_expanded(self):
        """
        Gets the expanded state. (True or False)
        Returns:
            bool: True if module is expanded, False if not.
        """
        return self.expanded

    def get_code_data(self):
        """
        Gets the stored CodeData object.
        Returns:
            CodeData or None: if defined, it will return a CodeData object describing how to run code using this module.
        """
        return self.code

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
            module_name = self.get_module_class_name(remove_module_prefix=False)
            module_data["module"] = module_name
        if self.name is not None:
            module_data["name"] = self.name
        module_data["uuid"] = self.uuid
        module_data["active"] = self.active
        if self.prefix is not None:
            module_data["prefix"] = self.prefix
        if self.suffix is not None:
            module_data["suffix"] = self.suffix
        if self.parent_uuid is not None:
            module_data["parent"] = self.parent_uuid
        if self.mirror_uuid:
            module_data["mirror"] = self.mirror_uuid
        if self.orientation is not None:
            module_data["orientation"] = self.orientation.get_data_as_dict()
        if self.code:
            module_data["code"] = self.code.get_data_as_dict()
        if self.metadata:
            module_data["metadata"] = self.metadata
        module_data.update(self._get_serialized_attrs())  # Gets any extra attributes defined in extended modules
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
            _module_class_name = core_str.remove_prefix(input_string=str(self.__class__.__name__), prefix="Module")
        if formatted:
            _module_class_name = " ".join(core_str.camel_case_split(_module_class_name))
        if remove_side:
            _module_class_name = core_str.remove_suffix(input_string=_module_class_name, suffix="Right")
            _module_class_name = core_str.remove_suffix(input_string=_module_class_name, suffix="Left")
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
            _module_name = f"({_class_name})"
        elif len(_module_name) <= add_class_len:
            _module_name = f"{_module_name} ({_class_name})"
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
            uuid = f"{uuid}-{driver_type}"
        if proxy_purpose and isinstance(proxy_purpose, Proxy):
            proxy_purpose = proxy_purpose.get_meta_purpose()
        if proxy_purpose:
            uuid = f"{uuid}-{proxy_purpose}"
        return tools_rig_utils.find_driver_from_uuid(uuid_string=uuid)

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
            if cmds.objExists(f"{obj}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}"):
                uuid_value = cmds.getAttr(f"{obj}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}")
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
            logger.debug(f"Proxy does not have any driver types. No drivers can be found without a type.")
            return []
        if not proxy_purpose:
            logger.debug(f"Proxy does not have a defined purpose. No drivers can be found without a purpose.")
            return []
        driver_uuids = []
        for proxy_type in proxy_driver_types:
            driver_uuids.append(f"{self.uuid}-{proxy_type}-{proxy_purpose}")
        obj_list = cmds.ls(typ="transform", long=True) or []
        module_matches = {}
        module_uuid = self.uuid
        for obj in obj_list:
            if cmds.objExists(f"{obj}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}"):
                uuid_value = cmds.getAttr(f"{obj}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}")
                if uuid_value.startswith(module_uuid):
                    module_matches[uuid_value] = core_node.Node(obj)
        matches = []
        matches_dict = {}
        for driver_uuid in driver_uuids:
            if driver_uuid in module_matches:
                matches.append(module_matches.get(driver_uuid))
                driver_key = str(driver_uuid).split("-")
                if len(driver_key) >= 3:
                    matches_dict[driver_key[1]] = module_matches.get(driver_uuid)
        if len(matches) != driver_uuids:
            logger.debug(
                f"Not all drivers were found. "
                f"Driver type list has a different length when compared to the list of matches."
            )
        if as_dict:
            matches = matches_dict
        return matches

    def _get_serialized_attrs(self):
        """
        Gets a dictionary containing the name and value for all class attributes except the manually serialized ones.
        Private variables starting with an underscore are ignored. e.g. "self._private" will not be returned.
        Returns:
            dict: A dictionary containing any attributes and their values.
            e.g. A class has an attribute "self.ctrl_visibility" set to True. This function will return:
            {"ctrl_visibility": True}, which can be serialized.
        """
        _manually_serialized = tools_rig_const.RiggerConstants.CLASS_ATTR_SKIP_AUTO_SERIALIZATION
        _result = {}
        for key, value in self.__dict__.items():
            if key not in _manually_serialized and not key.startswith("_"):
                if core_io.is_json_serializable(data=value, allow_none=False):  # Skip proxies and other elements.
                    _result[key] = value
        return _result

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
        _suffix = ""
        module_suffix = self.suffix
        if module_suffix:
            module_suffix = f"{module_suffix}_{core_naming.NamingConstants.Suffix.CTRL}"
        else:
            module_suffix = core_naming.NamingConstants.Suffix.CTRL
        if isinstance(overwrite_suffix, str):
            module_suffix = overwrite_suffix
        if overwrite_suffix:
            module_suffix = overwrite_suffix
        if module_suffix:
            _suffix = f"_{module_suffix}"
        return self._assemble_node_name(
            name=name, project_prefix=project_prefix, overwrite_prefix=overwrite_prefix, overwrite_suffix=module_suffix
        )

    def _assemble_node_name(self, name, project_prefix=None, overwrite_prefix=None, overwrite_suffix=None):
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
            instance._assemble_node_name(name='NodeName', project_prefix='Project', overwrite_suffix='Custom')
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
        _prefix = ""
        _suffix = ""
        if prefix_list:
            _prefix = "_".join(prefix_list) + "_"
        if module_suffix:
            _suffix = f"_{module_suffix}"
        # Assemble and Return
        return f"{_prefix}{name}{_suffix}"

    def duplicate(self):
        """
        Duplicates the module by creating a copy of it and updating the proxy UUIDs while retaining their hierarchy.
        Returns:
            ModuleGeneric: Duplicated copy of the module with proxy UUIDs reinitialized.
        """
        _duplicated_mod = copy.deepcopy(self)
        uuid_mapping = {proxy.uuid: core_uuid.generate_uuid(remove_dashes=True) for proxy in _duplicated_mod.proxies}
        updated_data = tools_rig_utils.update_uuids_in_dict(self.get_module_as_dict(), uuid_mapping)
        _duplicated_mod.read_data_from_dict(updated_data)  # Read updated data (Proxy UUIDs)
        _duplicated_mod.set_uuid(core_uuid.generate_uuid(short=True, short_length=12))  # Randomized Duplicated UUID
        return _duplicated_mod

    # --------------------------------------------------- Misc ---------------------------------------------------
    def apply_transforms(self, apply_offset=False):
        """
        Attempts to apply offset and parent offset transforms to the proxy elements.
        To be used only after proxy is built.
        Args:
            apply_offset (bool, optional): If True, it will attempt to also apply the offset data. (Happens first)
        """
        for proxy in self.get_proxies(sort_by="setup_driver"):
            proxy.apply_transforms(apply_offset=apply_offset)

    def align_proxies_to_joints(self):
        """
        Aligns the proxies to the joints.
        This operates with the hierarchy retrieved using get_proxies sort by "setup_driver".
        This step runs after the execution of "build_control_rig_pose" is complete in all modules,
        and after the creation of the rig dag pose.
        It is necessary to ensure that the proxies are matching the rig pose.
        """
        proxies_sorted_by_driver = self.get_proxies(sort_by="setup_driver")
        for prx in proxies_sorted_by_driver:
            proxy_id = prx.get_uuid()
            joint = tools_rig_utils.find_joint_from_uuid(proxy_id)
            proxy_item = tools_rig_utils.find_proxy_from_uuid(proxy_id)
            if joint:
                core_trans.match_translate(source=joint, target_list=proxy_item)

    def get_proxies_mirrored(self, plane="YZ", rotate_order="xyz", behaviour=False, specular=True):
        """
        Mirrors proxies through the self.mirror_uuid, if defined.

        Args:
            plane (str): hyperplane used to mirror. Accepted values: "XY", "YZ", "XZ".
            rotate_order (str): the rotate order used to decompose the matrix in euler rotations.
                                Accepted values: "xyz", "yzx", "zxy", "xzy", "yxz", "zyx".
            behaviour (bool): if True sets the opposite orientation
            specular (bool): if True sets a specular rotation
        """
        if not self.mirror_uuid:
            logger.warning(f"Cannot mirror the module {self.name}, mirror_uuid not defined.")
            return
        if plane not in ["XY", "YZ", "XZ"]:
            logger.warning("Given plane not valid. Please choose between 'XY', 'YZ', 'XZ'.")
            return
        if not rotate_order:
            logger.warning("Given rotate order is empty.")
            return
        if not isinstance(rotate_order, str):
            logger.warning("Given rotate order is not a string.")
            return

        # Get the proxies, sorted by driver_uuid in order to move them following the right sequence
        target_proxies = self.get_proxies(sort_by="setup_driver")

        # Mirror if there is a matching proxy
        for target_proxy in target_proxies:
            target_purpose = target_proxy.get_meta_purpose()
            if not target_purpose:
                # name fallback
                target_purpose = target_proxy.name

            # -- get the target proxy items from the module identified by mirror_uuid
            item_to_use = tools_rig_utils.find_drivers_from_module(
                source_uuid=self.mirror_uuid,
                filter_driver_type=tools_rig_const.RiggerDriverTypes.PROXY,
                filter_driver_purpose=target_purpose,
            )
            if not item_to_use:
                logger.warning(
                    f"Skipped mirror for '{target_proxy.name}', "
                    f"no suitable item found in linked module '{self.mirror_uuid}'.",
                )
                continue

            # -- calculate the mirrored transformations from the identified opposite item
            item_to_use = item_to_use[0]
            matrix_to_use = cmds.xform(item_to_use, q=True, m=True, ws=True)
            mirrored_matrix = core_trans.mirror_transform_matrix(matrix_to_use, plane=plane, behaviour=behaviour)
            mirrored_transform = core_trans.get_transform_from_matrix(mirrored_matrix, rotate_order=rotate_order)

            # -- apply mirrored transforms to the main proxy
            pos = mirrored_transform.position
            rot = mirrored_transform.rotation

            if specular:
                rot.y = -rot.y
                rot.z = -rot.z

            target_proxy_item = tools_rig_utils.find_proxy_from_uuid(target_proxy.get_uuid())
            if cmds.getAttr(target_proxy_item + ".rotate", l=True):
                # apply only translation
                cmds.xform(target_proxy_item, t=(pos.x, pos.y, pos.z), ws=True)
            else:
                # apply position and rotation
                cmds.xform(target_proxy_item, t=(pos.x, pos.y, pos.z), ws=True)
                cmds.xform(target_proxy_item, ro=(rot.x, rot.y, rot.z), ws=True)

    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        if not self.proxies:
            logger.warning("Missing proxies. A rig module needs at least one proxy to function.")
            return False
        return True

    def _add_driver_uuid_attr(self, target_driver, driver_type=None, proxy_purpose=None):
        """
        Adds an attribute to be used as driver UUID to the object.
        The value of the attribute is created using the module uuid, the driver type and proxy purpose combined.
        Following this pattern: "<module_uuid>-<driver_type>-<proxy_purpose>" e.g. "abcdef123456-fk-shoulder"
        Args:
            target_driver (str, Node): Path to the object that will receive the driver attributes.
            driver_type (str, optional): A string or tag use to identify the control type. e.g. "fk", "ik", "offset"
            proxy_purpose (str, Proxy, optional): This is the proxy purpose. It can be a string,
                    e.g. "shoulder" or the proxy object. If a Proxy object is provided, then the function tries to
                    extract the meta "purpose" value. If not present, this portion of the data is ignored.
        Returns:
        str: target UUID value created by the operation.
             Pattern: "<module_uuid>-<driver_type>-<proxy_purpose>" e.g. "abcdef123456-fk-shoulder"
        """
        module_uuid = f"{self.uuid}"
        return tools_rig_utils.add_driver_uuid_attr(
            target_driver=target_driver, module_uuid=module_uuid, driver_type=driver_type, proxy_purpose=proxy_purpose
        )

    def _parent_module_children_drivers(self):
        """
        Checks if the module parent joint exists, if it does, checks if it has a control ready to accept children.
        If all of these is true, then parent the module children drivers to this found control.
        Essentially, parent module controls to parent proxy controls.
        Summary:
        Condition: all elements must exist.
        Source objects: module children drivers (usually base control of the module)
        Target object: driver of the module parent joint
        """
        module_parent_jnt = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
        if module_parent_jnt:
            drivers = tools_rig_utils.find_drivers_from_joint(
                module_parent_jnt, as_list=True, create_missing_generic=True, skip_block_drivers=True
            )
            if drivers:
                core_hrchy.parent(source_objects=self.module_children_drivers, target_parent=drivers[0])

    def get_module_environment_variables(self):
        """
        Gets environment variables with their actual values. See "get_environment_variables" for more information
        on what is being replaced, then adds the module data to it, so it's complete.

        Returns:
            dict: A dictionary where keys are variables and values are the paths.
        """
        environment_vars_dict = get_environment_variables(rig_project=self._project)
        # Update Module Name vars
        _mod_name = self.get_name()
        environment_vars_dict["{module-name}"] = _mod_name
        _lower_snake_name = _mod_name.lower().replace(" ", "_")
        environment_vars_dict["{module-sanitized-name}"] = utils_sys.sanitize_filename(_lower_snake_name)
        return environment_vars_dict

    def parse_path(self, path, normalize_path=True):
        """
        Replaces environment variables with their actual values. See "get_environment_variables" for more information
        on what is being replaced.

        Args:
            path (str): A path that gets environment variables replaced with their actual values. For example:
                        "{temp-dir}/dir" would become "C:/Users/<user>/AppData/Local/Temp/dir"
            normalize_path (bool, optional): Normalizes the path by fixing all slashes according to the operating
                                             system's convention.

        Returns:
            str: A path string with the environment variables replaced with their actual paths.
        """
        if path is None:
            logger.debug('"None" was parsed as a path for the environment variables.')
            return ""
        environment_vars_dict = self.get_module_environment_variables()
        # Parse Path
        path = core_str.replace_keys_with_values(path, environment_vars_dict)  # Replace Variables with actual values
        if normalize_path:
            return os.path.normpath(path)
        return path

    def parse_absolute_project_path_to_relative(self, absolute_path):
        """
        When receiving a path contained by the resolved {project-dir}, it replaces the project directory with the
        environment variable. See example below.

        Args:
            absolute_path (str): A path to have the project dir environment variable injected into.

        Returns:
            str: A path where the long path for the project directory is replaced by an env var "{project-dir}".
                 This only happens if the path is contained by the resolved {project-dir} value.
                 If None is provided, it simply returns the same value of None.
                 Same thing in case a project is not available.

        Example:
            # {project-dir} = "C:/a_project"
            my_path = "C:/a_project/folder"
            output = self.parse_absolute_project_path_to_relative()
            print(output)  # {project-dir}/folder
        """
        if not absolute_path:
            return absolute_path
        if not self._project:
            return absolute_path
        project_dir = self._project.get_project_dir_path(parse_vars=True)
        if not project_dir:
            return absolute_path
        try:
            normalized_path = os.path.normpath(absolute_path)
            if not os.path.isabs(normalized_path):
                return absolute_path
            normalized_path = os.path.abspath(normalized_path)
            normalized_project_dir = os.path.abspath(os.path.normpath(project_dir))
            common_path = os.path.commonpath([normalized_project_dir, normalized_path])
            if os.path.normcase(common_path) != os.path.normcase(normalized_project_dir):
                return absolute_path
            relative_path = os.path.relpath(normalized_path, normalized_project_dir)
        except (TypeError, ValueError):
            return absolute_path
        if relative_path == os.curdir:
            return "{project-dir}"
        relative_path = relative_path.replace("\\", "/")
        return f"{{project-dir}}/{relative_path}"

    def warn_if_path_outside_project(self, path):
        """
        Sends a warning when the provided path is outside the set project folder.
        Args:
            path (str): A path to check if it's inside or not the project directory.
        """
        if not path:
            return
        if not self._project:
            return
        project_dir = self._project.get_project_dir_path(parse_vars=True)
        project_dir = os.path.abspath(project_dir)
        project_dir = os.path.join(project_dir, "")  # Add trailing separator to ensure proper containment
        check_path = os.path.abspath(path)
        if not os.path.commonprefix([project_dir, check_path]) == project_dir:
            logging.warning(f'Module "{self.get_name()}" is referencing a path outside the project directory.')

    def execute_module_python_code(self, required_order=None):
        """
        Tries to run code stored in the module.
        Args:
            required_order (str, None): If provided, it becomes a requirement for the code to run.
        """
        if self.code is None:
            return
        if required_order is None:
            self.code.execute_code()
        else:
            if self.code.get_order() == required_order:
                pretty_order_name = core_str.snake_to_title(required_order)
                logger.info(f"({pretty_order_name} Call): {self.get_name()}")
                self.code.execute_code()

        # build_rig - build common elements --------------------

    # -------------------------------------------------- Create --------------------------------------------------
    def create_offset_control(
        self,
        control,
        control_base_name=None,
        overwrite_prefix=None,
        control_scale=0.8,
    ):
        """
        Builds the offset control directly underneath the given control.

        Args:
            control (Node): main control of the offset control that you are building.
            control_base_name (str): type/s of the control, the main part of the name, the entire name will be assembled
                                inside this function (e.g. "root", "upperArm", "lowerLegTwist", etc.)
            overwrite_prefix (str): None by default. Control name prefix comes from the module prefix, which usually
                                    it's the side. There are cases in which you need to change it.
            control_scale (float): scale value in relation to the main control, by default 0.8.

        Returns:
            offset_control (Node)
        """

        # get offset control name
        offset_suffix = core_naming.NamingConstants.Control.OFFSET
        offset_control_base_name = f"{control_base_name}{offset_suffix}"
        offset_control_name = self._assemble_ctrl_name(name=offset_control_base_name, overwrite_prefix=overwrite_prefix)

        # build offset control
        offset_control = core_hrchy.duplicate_object(control, name=offset_control_name, parent_to_world=False)
        core_hrchy.parent(source_objects=offset_control, target_parent=control)

        # set offset control
        rig_const = core_rigging.RiggingConstants
        core_color.set_color_viewport(obj_list=offset_control, rgb_color=core_color.ColorConstants.RigJoint.OFFSET)
        core_attr.set_attr_state(attribute_path=f"{offset_control}.v", hidden=True)  # Hide and Lock Visibility
        core_attr.add_separator_attr(target_object=offset_control, attr_name=rig_const.SEPARATOR_CONTROL)

        # rotation order
        core_rigging.expose_rotation_order(offset_control)
        rot_order = cmds.getAttr(f"{control}.rotateOrder")
        cmds.setAttr(f"{offset_control}.rotationOrder", rot_order)
        core_attr.set_attr_state(attribute_path=f"{offset_control}.rotationOrder", locked=True)

        # -- set scale
        pivot_pos = cmds.xform(offset_control, q=True, worldSpace=True, rotatePivot=True)
        cmds.xform(offset_control, centerPivots=1)
        core_trans.scale_shapes(obj_transform=offset_control, offset=control_scale)
        cmds.xform(offset_control, worldSpace=True, rotatePivot=pivot_pos)

        # -- connections
        cmds.addAttr(control, ln="showOffsetCtrl", at="bool", k=True)
        cmds.connectAttr(f"{control}.showOffsetCtrl", f"{offset_control}.v")

        return offset_control

    def create_control_groups(
        self,
        control,
        control_base_name=None,
        overwrite_prefix=None,
        parent_obj=None,
        suffix_list=None,
    ):
        """
        Builds sequence of groups related to the given control.

        Args:
            control (Node): main control to which the groups are related.
            control_base_name (str): type/s of the control, the main part of the name, the entire name will be assembled
                                inside this function (e.g. "root", "upperArm", "lowerLegTwist", etc.)
            overwrite_prefix (str): None by default. Control name prefix comes from the module prefix, which usually
                                    it's the side. There are cases in which you need to change it.
            parent_obj (Node, optional): None by default. If None, the given control will be the parent.
            suffix_list (string or list, optional): list of suffix, the order will determine the hierarchy
                                                    of the groups. If None, the creation of the groups is skipped.

        Returns:
            list of Nodes: the created groups
        """
        group_list = []

        if not suffix_list:
            return
        if not parent_obj:
            parent_obj = control
        if not control_base_name:
            control_base_name = core_naming.get_short_name(control)
            current_suffix = control_base_name.split("_")[-1]
            if any(current_suffix == value for key, value in core_naming.NamingConstants.Suffix.__dict__.items()):
                control_base_name = control_base_name.replace(f"_{current_suffix}", "")

        rot_order = cmds.getAttr(f"{control}.rotateOrder")

        if isinstance(suffix_list, str):
            suffix_list = [suffix_list]
        if not isinstance(suffix_list, list):
            logger.warning(f"Skipped the creation of groups for {control}, given value is not a list.")
        else:
            for grp_suffix in suffix_list:
                group_name = self._assemble_node_name(control_base_name, overwrite_prefix=overwrite_prefix)
                group_name = f"{group_name}_{grp_suffix}"
                group = core_hrchy.create_group(name=group_name)
                group = core_node.Node(group)

                # parent
                core_hrchy.parent(source_objects=group, target_parent=parent_obj)
                # rotate order from control
                cmds.setAttr(f"{group}.rotateOrder", rot_order)
                # match control
                core_trans.match_transform(source=control, target_list=group)

                group_list.append(group)
                parent_obj = group

        return group_list

    def create_rig_control(
        self,
        control_base_name,
        curve_file_name,
        parent_obj,
        overwrite_prefix=None,
        extra_parent_groups=None,
        add_offset_ctrl=False,
        separator_attr=core_rigging.RiggingConstants.SEPARATOR_CONTROL,
        match_obj=None,
        match_obj_rot=None,
        match_obj_pos=None,
        rot_order=None,
        rot_order_expose=True,
        shape_pos_offset=None,
        shape_rot_offset=None,
        shape_scale=None,
        color=None,
        line_width=None,
        shape_vis_expose=True,
    ):
        """
        Builds the control, sets the parent, matches the transformations of a given object, the rotation order,
        the shape position, rotation and scale, the color and the line width.

        Args:
            control_base_name (str): type/s of the control, the main part of the name, the entire name will be assembled
                                inside this function (e.g. "root", "upperArm", "lowerLegTwist", etc.)
            curve_file_name (str): file name of the curve.
            parent_obj (Node): object to use as parent.
            overwrite_prefix (str): None by default. Control name prefix comes from the module prefix, which usually
                                    it's the side. There are cases in which you need to change it.
            add_offset_ctrl (bool): if True, it creates an offset control underneath the control.
                                    It will also create an offset_data group to carry the offset transformation.
            separator_attr (str, optional): Locked attribute used to identify user-defined attributes.
                                            If None, it doesn't get created.
            extra_parent_groups (str, list): list of extra suffixes used to create new parent groups above the control
                                                and under the main offset control created by default. None by default.
            match_obj (Node): object to use to match the transformations.
            match_obj_pos (Node): object to use to match the translation. If given, it overwrites match_obj
            match_obj_rot (Node): object to use to match the translation. If given, it overwrites match_obj
            rot_order (int): index to the Maya enum that defines the rotation order.
                             If not given, it takes the one of the parent_obj.
            rot_order_expose (bool, optional): If True, the rotation order of the control is exposed as an attribute.
            shape_pos_offset (float 3): if given, set shape position offset.
            shape_rot_offset (float 3): if given, set shape rotation offset.
            shape_scale (int, float): if given, set shape scale offset.
            color (tuple, optional): tuple describing RGB color. If provided, it set the color. Pattern: (R, G, B)
            line_width (int, optional): if given, set the line width.
            shape_vis_expose (bool, optional): If active, it creates a hidden attribute used to control the visibility
                                               of the control shape.

        Returns:
            control (Node)
            control_parent_groups (Node list)
            offset_control (Node)
            offset_data_group (Node): this will be created automatically if the offset_control is requested
            pivot_control (Node)
        """
        if not match_obj:
            match_obj = parent_obj
        if rot_order is None:
            rot_order = cmds.getAttr(f"{parent_obj}.rotateOrder")
        if overwrite_prefix:
            if not isinstance(overwrite_prefix, str):
                logger.warning("overwrite_prefix must be a string. Skipped.")
                overwrite_prefix = None

        # -- create the control
        control_name = self._assemble_ctrl_name(name=control_base_name, overwrite_prefix=overwrite_prefix)
        control = tools_rig_utils.create_ctrl_default(name=control_name, curve_file_name=curve_file_name)

        # -- expose shape visibility as an attribute
        if shape_vis_expose:
            attr_shape_vis = tools_rig_const.RiggerConstants.ATTR_SHAPE_VIS
            core_rigging.expose_shapes_visibility(target=control, attr_name=attr_shape_vis, default_value=True)

        # -- separator attribute
        if separator_attr and isinstance(separator_attr, str):
            core_attr.add_separator_attr(target_object=control, attr_name=separator_attr)

        # -- set rotation order
        cmds.setAttr(f"{control}.rotateOrder", rot_order)
        if rot_order_expose:
            core_rigging.expose_rotation_order(control)
            core_attr.set_attr_state(attribute_path=f"{control}.rotationOrder", locked=True)

        # -- match transformations
        core_trans.match_transform(source=match_obj, target_list=control)
        # -- match position
        if match_obj_pos:
            core_trans.match_translate(source=match_obj_pos, target_list=control)

        # -- match rotation
        if match_obj_rot:
            core_trans.match_rotate(source=match_obj_rot, target_list=control)

        # -- adjust shape
        if isinstance(shape_scale, (int, float)):
            core_trans.scale_shapes(obj_transform=control, offset=shape_scale)
        if shape_pos_offset:
            core_trans.translate_shapes(obj_transform=control, offset=shape_pos_offset)
        if shape_rot_offset:
            core_trans.rotate_shapes(obj_transform=control, offset=shape_rot_offset)
        if color:
            core_color.set_color_viewport(obj_list=control, rgb_color=color)
        if isinstance(line_width, (int, float)):
            core_curve.set_curve_width(obj_list=control, line_width=line_width)

        # Create the default groups
        parent_grp_suffix_list = core_rigging.get_control_parent_group_name_list()
        default_grps = self.create_control_groups(
            control,
            control_base_name=control_base_name,
            overwrite_prefix=overwrite_prefix,
            parent_obj=parent_obj,
            suffix_list=parent_grp_suffix_list,
        )
        control_parent_groups = [default_grps[0]]

        # Create extra parent groups
        extra_parents = self.create_control_groups(
            control,
            control_base_name=control_base_name,
            overwrite_prefix=overwrite_prefix,
            parent_obj=parent_obj,
            suffix_list=extra_parent_groups,
        )
        if extra_parents:
            # parent the extra groups to the default groups, extra groups come after
            core_hrchy.parent(source_objects=extra_parents[0], target_parent=default_grps[-1])
            # add extra groups to the main group list
            control_parent_groups.extend(extra_parents)

        # -- parent the control under the last parent group
        core_hrchy.parent(source_objects=control, target_parent=control_parent_groups[-1])
        # -- freeze
        cmds.makeIdentity(control, apply=True, translate=True, rotate=True)

        # Create offset control - if needed, before child groups
        offset_control = None
        if add_offset_ctrl:
            offset_control = self.create_offset_control(
                control,
                control_base_name=control_base_name,
                overwrite_prefix=overwrite_prefix,
            )

        # Create offset data group if the offset control is requested
        offset_data_group = None
        if offset_control:
            offset_data_suffix = core_naming.NamingConstants.Description.OFFSET_DATA
            offset_data_group = self.create_control_groups(
                control,
                control_base_name=control_base_name,
                overwrite_prefix=overwrite_prefix,
                suffix_list=offset_data_suffix,
            )[0]

            # -- connections
            cmds.connectAttr(f"{offset_control}.translate", f"{offset_data_group}.translate")
            cmds.connectAttr(f"{offset_control}.rotate", f"{offset_data_group}.rotate")

        return control, control_parent_groups, offset_control, offset_data_group

    # --------------------------------------------------- Build ---------------------------------------------------
    def build_proxy(self, project_prefix=None, optimized=False, use_naming_attrs=None):
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
            use_naming_attrs (bool, optional): If true, it will check the proxy for a suffix and prefix
                                               attribute instead of the module, which allows for overrides.
                                               If not provided, this defaults to True for ModuleGeneric and
                                               False for inheriting modules.
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        logger.debug(f'"build_proxy" function for "{self.get_module_class_name()}" was called.')
        proxy_data = []
        _prefix = ""
        prefix_list = []

        # Define use of attribute names (data stored in the proxy object)
        # If the default is used, determine the correct value based on the class type.
        # This allows ModuleGeneric to behave differently than its children.
        if use_naming_attrs is None:
            use_naming_attrs = self.get_module_class_name() == "ModuleGeneric"

        # Define Prefix
        if project_prefix and isinstance(project_prefix, str):
            prefix_list.append(project_prefix)
        if self.prefix and isinstance(self.prefix, str):
            prefix_list.append(self.prefix)
        if prefix_list:
            _prefix = "_".join(prefix_list)
        # Build Proxies
        for proxy in self.proxies:
            proxy_data.append(
                proxy.build(
                    prefix=_prefix,
                    suffix=self.suffix,
                    apply_transforms=False,
                    use_naming_attrs=use_naming_attrs,
                    optimized=optimized,
                )
            )

        # Add the driver uuid to identify the proxies through the module_uuid
        for proxy in self.proxies:
            proxy_item = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            self._add_driver_uuid_attr(
                target_driver=proxy_item,
                driver_type=tools_rig_const.RiggerDriverTypes.PROXY,
                proxy_purpose=proxy.get_meta_purpose(),
            )

        return proxy_data

    def build_proxy_setup(self):
        """
        Runs post proxy script. Used to define proxy automation/setup.
        This step runs after the execution of "build_proxy" is complete in all modules.
        Usually used to create extra behavior unique to the module. e.g. Constraints, automations, or limitations.
        """
        logger.debug(f'"build_proxy_setup" function for "{self.get_module_class_name()}" was called.')
        self.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton_joints(self, use_naming_attrs=None):
        """
        Runs build skeleton joints script. Creates joints out of the proxy elements.
        This function should happen after "build_proxy_setup" as it expects proxy elements to be present in the scene.
        Args:
            use_naming_attrs (bool, optional): If true, it will check the proxy for a suffix and prefix
                                               attribute instead of the module, which allows for overrides.
                                               If not provided, this defaults to True for ModuleGeneric and
                                               False for inheriting modules.
        """
        _module_prefix = self.prefix
        _module_suffix = self.suffix

        # If the default is used, determine the correct value based on the class type.
        # This allows ModuleGeneric to behave differently than its children.
        if use_naming_attrs is None:
            use_naming_attrs = self.get_module_class_name() == "ModuleGeneric"

        logger.debug(f'"build_skeleton" function from "{self.get_module_class_name()}" was called.')
        skeleton_grp = tools_rig_utils.find_skeleton_group()
        for proxy in self.proxies:
            # If not found skip it
            proxy_node = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            if not proxy_node:
                continue

            # Check for prefix/suffix attributes
            if use_naming_attrs:
                if proxy.get_attr_dict_value(key="prefix") and not None:
                    self.prefix = proxy.get_attr_dict_value(key="prefix")
                if proxy.get_attr_dict_value(key="suffix") and not None:
                    self.suffix = proxy.get_attr_dict_value(key="suffix")

            # Enforce Resolved Name (Fixes reserved strings issue)
            resolved_name = proxy_node.get_short_name()
            base_name_attr = f"{proxy_node}.{tools_rig_const.RiggerConstants.ATTR_BASE_NAME}"
            prefix_attr = f"{proxy_node}.{tools_rig_const.RiggerConstants.ATTR_PREFIX}"
            suffix_attr = f"{proxy_node}.{tools_rig_const.RiggerConstants.ATTR_SUFFIX}"
            if all(cmds.objExists(attr) for attr in [base_name_attr, prefix_attr, suffix_attr]):
                _base_name = str(cmds.getAttr(base_name_attr))
                _prefix = self.prefix
                _suffix = self.suffix
                resolved_name = "_".join(filter(None, [_prefix, _base_name, _suffix]))

            joint_name = f"{resolved_name}_{core_naming.NamingConstants.Suffix.JNT}"
            joint = core_node.create_node(node_type="joint", name=joint_name)

            _locator_scale = proxy.get_locator_scale()
            cmds.setAttr(f"{joint}.radius", _locator_scale)
            _rot_order = proxy.get_rotation_order()
            cmds.setAttr(f"{joint}.rotateOrder", _rot_order)
            core_trans.match_translate(source=proxy_node, target_list=joint)

            # Add proxy base name - Proxy/Joint Name
            core_attr.add_attr(
                obj_list=joint, attributes=tools_rig_const.RiggerConstants.ATTR_BASE_NAME, attr_type="string"
            )
            core_attr.set_attr(
                obj_list=joint, attr_list=tools_rig_const.RiggerConstants.ATTR_BASE_NAME, value=proxy.get_name()
            )
            # Add proxy reference - Proxy/Joint UUID
            core_attr.add_attr(
                obj_list=joint, attributes=tools_rig_const.RiggerConstants.ATTR_JOINT_UUID, attr_type="string"
            )
            core_attr.set_attr(
                obj_list=joint, attr_list=tools_rig_const.RiggerConstants.ATTR_JOINT_UUID, value=proxy.get_uuid()
            )
            # Add module reference - Module UUID
            core_attr.add_attr(
                obj_list=joint, attributes=tools_rig_const.RiggerConstants.ATTR_MODULE_UUID, attr_type="string"
            )
            core_attr.set_attr(
                obj_list=joint, attr_list=tools_rig_const.RiggerConstants.ATTR_MODULE_UUID, value=self.get_uuid()
            )
            # Add proxy purposes - Meta Purpose
            core_attr.add_attr(
                obj_list=joint, attributes=tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE, attr_type="string"
            )
            core_attr.set_attr(
                obj_list=joint,
                attr_list=tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE,
                value=proxy.get_meta_purpose(),
            )
            # Add proxy purposes - Joint Drivers
            core_attr.add_attr(
                obj_list=joint, attributes=tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVERS, attr_type="string"
            )
            drivers = proxy.get_driver_types()
            if drivers:
                tools_rig_utils.add_driver_to_joint(target_joint=joint, new_drivers=drivers)

            core_color.set_color_viewport(obj_list=joint, rgb_color=core_color.ColorConstants.RigJoint.GENERAL)
            core_hrchy.parent(source_objects=joint, target_parent=str(skeleton_grp))

            self.prefix = _module_prefix
            self.suffix = _module_suffix

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
            joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue

            proxy_obj_path = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            # Inherit Rotation Order
            proxy_rotation_order = cmds.getAttr(f"{proxy_obj_path}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            cmds.setAttr(f"{joint}.rotateOrder", proxy_rotation_order)
            # Inherit Orientation (Before Parenting)
            if self.get_orientation_method() == OrientationData.Methods.inherit:
                cmds.delete(cmds.orientConstraint(proxy_obj_path, joint))
        for proxy in self.proxies:
            joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue
            # Parent Joint (Internal Proxies)
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid in module_uuids:
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=joint, target_parent=parent_joint_node)
            jnt_nodes.append(joint)
        # Auto Orientation (After Parenting)
        if self.get_orientation_method() == OrientationData.Methods.automatic:
            self.orientation.apply_automatic_orientation(joint_list=jnt_nodes)
        # Parent Joints (External Proxies)
        for proxy in self.proxies:
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid not in module_uuids:
                joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=joint, target_parent=parent_joint_node)
        cmds.select(clear=True)

    def build_control_rig_pose(self):
        """
        Build function used to pose the proxy/skeleton in a new pose before creating the control rig.
        This allows for the bind pose to be different from the control rig pose.
        e.g. A character could be bound in A pose, but the control rig is generated in T pose.

        TODO: add an option to activate/deactivate it per module. For example, if we need to build three arms,
              but we don't want to apply the rig pose on one of them.
        """
        logger.debug(f'"build_control_rig_pose" function from "{self.get_module_class_name()}" was called.')

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
        Runs post rig script phase.
        This step runs after the execution of "build_rig" is completed.
        Usually used to define automation or connections that require external elements to exist.
        """
        logger.debug(f'"build_rig" function from "{self.get_module_class_name()}" was called.')
        self._parent_module_children_drivers()


class RigProject:
    icon = ui_res_lib.Icon.rigger_project

    def __init__(self, name=None, prefix=None, preferences=None):
        """
        Initialize the object with optional name, prefix, and preferences.

        Args:
            name (str, optional): Name of the instance. Defaults to "Untitled" if not provided.
            prefix (str, optional): Prefix string to set.
            preferences (RigPreferencesData, optional): Preferences object to set.
        """
        # Default Values
        self.uuid = core_uuid.generate_uuid(short=True, short_length=6)
        self.project_file_path = None
        self.name = "Untitled"
        self.prefix = None
        self.modules = []
        self.preferences = RigPreferencesData()  # Initialize Preferences
        self.control_rig_pose_data = tools_control_pose.ControlRigPoseData()

        if name:
            self.set_name(name=name)
        if prefix:
            self.set_prefix(prefix=prefix)
        if preferences:
            self.set_preferences(preferences=preferences)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_uuid(self, uuid):
        """
        Sets a new UUID for the project.
        If no UUID is provided or set a new one will be generated automatically,
        this function is used to force a specific value as UUID.
        Args:
            uuid (str): A new UUID for this module (6 length format)
        """
        error_message = f"Unable to set project UUID. Invalid UUID input."
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if core_uuid.is_short_uuid_valid(uuid, length=6):
            self.uuid = uuid
        else:
            logger.warning(error_message)

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
        self.refresh_modules_project_reference()

    def set_control_rig_pose_name(self, pose):
        """
        Sets the control rig pose name.
        Args:
            pose (str): name to use for the control rig dag pose.
        """
        if not isinstance(pose, str):
            logger.warning(f'Unable to set the control rig pose name. Expected string but got "{str(type(pose))}"')
            return
        self.set_preference_value_using_key(key="control_rig_pose_name", value=pose)

    def add_to_modules(self, module, set_parent_project=True):
        """
        Adds a new item to the modules list.
        Args:
            module (ModuleGeneric, List[ModuleGeneric]): New module element to be added to this project.
            set_parent_project (bool, optional): If True, the function also update the rig project parent,
                                                 otherwise only add to the project.
        """
        from gt.tools.auto_rigger.rig_modules import RigModules

        all_modules = RigModules.get_module_names()
        if module and str(module.__class__.__name__) in all_modules:
            module = [module]
        if module and isinstance(module, list):
            for mod in module:
                if str(mod.__class__.__name__) in all_modules:
                    self.modules.append(mod)
                    if set_parent_project:
                        mod.set_parent_project(rig_project=self)
                else:
                    logger.debug(f'Unable to add "{str(mod)}". Provided module not found in "RigModules".')
            return
        logger.debug(
            f"Unable to add provided module to rig project. "
            f'Must be of the type "ModuleGeneric" or a list containing only ModuleGeneric elements.'
        )

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
                module.set_parent_project(rig_project=None)
                return module
        logger.debug(f"Unable to remove module from project. Not found.")

    def duplicate_module(self, module=None, must_be_present=True):
        """
                Duplicates a provided module
                Args:
                    module (ModuleGeneric): A module object to be duplicated.
                    must_be_present (bool, optional): If True, only allow duplication if module is present in project.

                Returns:
        `           ModuleGeneric: The duplicated module object.
        """
        if not module or not isinstance(module, ModuleGeneric):
            logger.warning(f"Unable to duplicate module. Incorrect data type provided.")
            return
        if must_be_present and module not in self.modules:
            logger.warning(f"Module cannot be duplicated as it is not present in the project.")
            return

        # Create a new instance (assuming ModuleGeneric has a copy or clone method)
        duplicated_module = module.duplicate()

        # If the module is present, insert next to the original
        if module in self.modules:
            index = self.modules.index(module)
            self.modules.insert(index + 1, duplicated_module)
        else:
            # If not present, append to the end
            self.modules.append(duplicated_module)

        logger.info(f"Module '{module.get_name()}' duplicated successfully.")
        return duplicated_module

    def set_preferences(self, preferences):
        """
        Sets the preferences data object. The RigPreferencesData carries all preferences used by the RigProject object.
        Args:
            preferences (dict, RigPreferencesData): A dictionary describing a RigProject preference object.
        """
        if not isinstance(preferences, (dict, RigPreferencesData)):
            logger.warning(
                f"Unable to set rig project metadata. "
                f'Expected a dictionary or a RigPreferencesData object, but got: "{str(type(preferences))}"'
            )
            return
        if isinstance(preferences, RigPreferencesData):
            self.preferences = preferences
        else:
            self.preferences = RigPreferencesData()
            self.preferences.read_data_from_dict(preferences)

    def set_preference_value_using_key(self, key, value):
        """
        Sets the value of a preference. For this to work the key must be a valid attribute. See RigPreferencesData to
        find what attributes are available.
        Args:
            key: The key (which is the name of the attribute found in RigPreferencesData) to receive the new data.
            value: The new value to set the preference to.
        """
        if not isinstance(key, str):
            logger.warning(f"Unable to set preference value using key. Key must be a string")
            return
        if key not in self.preferences.list_available_preferences():
            logger.warning(
                f"Unable to set preference value using key. Key not found in preferences. "
                f'Please check the "RigPreferencesData" for available keys or to add a new one.'
            )
            return
        _current_prefs = self.preferences.get_data_as_dict()
        _current_prefs[key] = value
        if key == "apply_control_rig_pose":
            _current_prefs["control_rig_pose_mode"] = (
                tools_control_pose.ControlRigPoseMode.AUTOMATIC
                if value
                else tools_control_pose.ControlRigPoseMode.DISABLED
            )
        elif key == "control_rig_pose_mode" and tools_control_pose.ControlRigPoseMode.is_valid(value):
            _current_prefs["apply_control_rig_pose"] = value != tools_control_pose.ControlRigPoseMode.DISABLED
        self.preferences.read_data_from_dict(_current_prefs)

    def set_control_rig_pose_mode(self, mode):
        """Sets the method used to determine the project's control rig pose.

        Args:
            mode (str): Automatic, custom, or disabled mode string.

        Returns:
            bool: True when the mode was accepted.
        """
        if not tools_control_pose.ControlRigPoseMode.is_valid(mode):
            logger.warning(f'Unable to set unsupported control rig pose mode: "{mode}".')
            return False
        self.set_preference_value_using_key(key="control_rig_pose_mode", value=mode)
        return True

    def set_control_rig_pose_data(self, pose_data):
        """Sets custom control rig pose data for the project.

        Args:
            pose_data (ControlRigPoseData, dict): Custom pose data or its serialized form.

        Returns:
            bool: True when the pose data was accepted.
        """
        if isinstance(pose_data, tools_control_pose.ControlRigPoseData):
            self.control_rig_pose_data = copy.deepcopy(pose_data)
            return True
        if isinstance(pose_data, dict):
            self.control_rig_pose_data = tools_control_pose.ControlRigPoseData()
            self.control_rig_pose_data.read_data_from_dict(pose_data)
            return True
        logger.warning(f'Unable to set control rig pose data from type "{type(pose_data)}".')
        return False

    def clear_control_rig_pose_data(self):
        """Clears the stored custom control rig pose data."""
        self.control_rig_pose_data.clear()

    def set_project_dir_path(self, dir_path):
        """
        Sets the preference for the project path (key: "project_dir")
        This function does the same as calling: self.set_preference_value_using_key(key="project_dir", value=dir_path)
        The difference is some validation before accepting the new preference value, and the creation missing folders.
        Args:
            dir_path: A directory path to be used as project directory. (Saved in the project preferences)
        """
        if not isinstance(dir_path, str):
            logger.warning("Invalid project directory path provided. Input must be a string.")
            return
        self.set_preference_value_using_key(key="project_dir", value=dir_path)

    def add_module_from_dict(self, module_dict, reinitialize_uuids=True):
        """
        Adds a module to the project from a dictionary description.
        Args:
            module_dict (dict): A dictionary describing a module.
            reinitialize_uuids (bool, optional): If True, UUIDs are reinitialized, useful when copying & pasting data.
                                                 (only the ones belonging to the module)
        Returns:
            ModuleGeneric: An object using module generic as a base. This is the module added from the dictionary.
        """
        if not module_dict or not isinstance(module_dict, dict) or not module_dict.get("module"):
            return

        from gt.tools.auto_rigger.rig_modules import RigModules

        available_modules = RigModules.get_modules_dict()
        class_name = module_dict.get("module")
        if class_name in available_modules:
            _module = available_modules.get(class_name)()
        else:
            _module = ModuleGeneric()
        _module.read_data_from_dict(module_dict=module_dict)
        # Reinitialize UUIDs
        if reinitialize_uuids:
            uuid_mapping = {proxy.uuid: core_uuid.generate_uuid(remove_dashes=True) for proxy in _module.proxies}
            updated_data = tools_rig_utils.update_uuids_in_dict(module_dict, uuid_mapping)
            _module.read_data_from_dict(module_dict=updated_data)
        self.add_to_modules(_module)
        return _module

    def read_modules_from_dict(self, modules_list):
        """
        Reads a proxy description dictionary and populates (after resetting) the proxies list with the dict proxies.
        Args:
            modules_list (list): A list of module descriptions.
        """

        if not modules_list or not isinstance(modules_list, list):
            logger.debug(f"Unable to read modules from list. Input must be a list.")
            return

        self.modules = []
        from gt.tools.auto_rigger.rig_modules import RigModules

        available_modules = RigModules.get_modules_dict()
        for module_description in modules_list:
            class_name = module_description.get("module")
            if class_name in available_modules:
                _module = available_modules.get(class_name)()
            else:
                _module = ModuleGeneric()

            _module.read_data_from_dict(module_dict=module_description)
            self.modules.append(_module)
        self.refresh_modules_project_reference()

    def read_data_from_dict(self, module_dict, clear_modules=True):
        """
        Reads the data from a project dictionary and updates the values of this project to match it.
        Args:
            module_dict (dict): A dictionary describing the project data. e.g. {"name": "untitled", "modules": ...}
            clear_modules (bool, optional): When active, the modules list is cleared before importing new data.
        Returns:
            RigProject: This project (self)
        """
        if clear_modules:
            self.modules = []
            self.control_rig_pose_data = tools_control_pose.ControlRigPoseData()
        self.preferences = RigPreferencesData()

        if module_dict and not isinstance(module_dict, dict):
            logger.debug(f"Unable o read data from dict. Input must be a dictionary.")
            return

        _uuid = module_dict.get("uuid")
        if _uuid:
            self.set_uuid(uuid=_uuid)

        _name = module_dict.get("name")
        if _name is not None:
            self.set_name(name=_name)

        _prefix = module_dict.get("prefix")
        if _prefix is not None:
            self.set_prefix(prefix=_prefix)

        _modules = module_dict.get("modules")
        if _modules and isinstance(_modules, list):
            self.read_modules_from_dict(modules_list=_modules)

        _prefs = module_dict.get("preferences")
        if _prefs:
            self.set_preferences(preferences=_prefs)

        if "control_rig_pose" in module_dict:
            self.set_control_rig_pose_data(module_dict.get("control_rig_pose"))
        self.refresh_modules_project_reference()
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
    def get_uuid(self):
        """
        Gets the uuid value of this project.
        Returns:
            str: uuid string
        """
        return self.uuid

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
        Args:
            uuid (str): The UUID of the proxy to search for.
        Returns:
            ModuleGeneric or None: The module that contains the provided UUID, None otherwise.
        """
        for module in self.modules:
            if module.get_proxy_uuid_existence(uuid):
                return module

    def get_preferences(self):
        """
        Gets the RigPreferencesData object for this project.
        Returns:
            RigPreferencesData: prefs dictionary
        """
        return self.preferences

    def get_preferences_dict_value(self, key, default=None):
        """
        Gets a value from the preferences' dictionary. If not found, the default value is returned instead.
        Args:
            key: (str): The preference key. e.g. "buildControlSkip"
            default (any, optional): What is returned when a value is not found (missing key)
        Returns:
            any: Any data stored as a value for the provided key. If a key is not found the default
            parameter is returned instead.
        """
        return self.preferences.get_data_as_dict().get(key, default)

    def get_control_rig_pose_mode(self):
        """Gets the project's control rig pose mode.

        Returns:
            str: Automatic, custom, or disabled mode string.
        """
        mode = self.get_preferences_dict_value(key="control_rig_pose_mode")
        if tools_control_pose.ControlRigPoseMode.is_valid(mode):
            return mode
        apply_pose = self.get_preferences_dict_value(key="apply_control_rig_pose", default=True)
        if apply_pose:
            return tools_control_pose.ControlRigPoseMode.AUTOMATIC
        return tools_control_pose.ControlRigPoseMode.DISABLED

    def is_control_rig_pose_enabled(self):
        """Checks whether the project builds a distinct control rig pose.

        Returns:
            bool: True for automatic and custom modes.
        """
        return self.get_control_rig_pose_mode() != tools_control_pose.ControlRigPoseMode.DISABLED

    def is_control_rig_pose_automatic(self):
        """Checks whether automatic module pose helpers are active.

        Returns:
            bool: True when the project uses automatic pose helpers.
        """
        return self.get_control_rig_pose_mode() == tools_control_pose.ControlRigPoseMode.AUTOMATIC

    def get_control_rig_pose_data(self):
        """Gets the custom control rig pose data object.

        Returns:
            ControlRigPoseData: Project custom control rig pose data.
        """
        return self.control_rig_pose_data

    def get_control_rig_pose_proxy_signature_data(self):
        """Gets skeleton-relevant project data used to detect stale custom poses.

        Returns:
            list: JSON-compatible module and proxy data.
        """
        modules_data = [module.get_module_as_dict(include_offset_data=True) for module in self.modules]
        return tools_control_pose.get_proxy_signature_data({"modules": modules_data})

    def get_control_rig_pose_proxy_signature(self):
        """Gets a stable signature for the active proxy configuration.

        Returns:
            str: SHA-256 signature of skeleton-relevant project data.
        """
        signature_data = self.get_control_rig_pose_proxy_signature_data()
        return tools_control_pose.build_data_signature(signature_data)

    def validate_control_rig_pose_data(self):
        """Validates stored custom pose data against the current project.

        Returns:
            dict: Validation result containing valid, errors, warnings, and transform_count keys.
        """
        return self.control_rig_pose_data.validate(
            project_uuid=self.get_uuid(),
            proxy_signature=self.get_control_rig_pose_proxy_signature(),
        )

    def validate_control_rig_pose_for_build(self):
        """Validates that the configured control rig pose can be used for a build.

        Returns:
            dict: Validation result. Non-custom modes always return a valid result.
        """
        if self.get_control_rig_pose_mode() != tools_control_pose.ControlRigPoseMode.CUSTOM:
            return {"valid": True, "errors": [], "warnings": [], "transform_count": 0}
        return self.validate_control_rig_pose_data()

    def raise_for_invalid_control_rig_pose(self):
        """Raises when a custom control rig pose is not valid for this project.

        Raises:
            RuntimeError: If custom mode is active and the stored pose is missing or stale.
        """
        validation = self.validate_control_rig_pose_for_build()
        if not validation.get("valid"):
            message = " ".join(validation.get("errors") or ["The custom control rig pose is invalid."])
            raise RuntimeError(message)

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
        if self.uuid:
            project_data["uuid"] = self.uuid
        if self.name is not None:
            project_data["name"] = self.name
        if self.prefix is not None:
            project_data["prefix"] = self.prefix
        project_data["modules"] = project_modules
        if self.preferences:
            project_data["preferences"] = self.preferences.get_data_as_dict()
        if self.control_rig_pose_data.has_pose():
            project_data["control_rig_pose"] = self.control_rig_pose_data.get_data_as_dict()
        return project_data

    def get_project_dir_path(self, parse_vars=False):
        """
        Gets the configured project directory. Defaults to the loaded project
        file directory through the {project-file-dir} environment variable.
        This path is often used to replace environment variables and automatically parse paths.
        Args:
            parse_vars (bool, optional): If True, the returned path will have the environment variables replaced
                                         with actual values. e.g.
                                         "{temp-dir}/dir" would become "C:/Users/<user>/AppData/Local/Temp/dir"
        Returns:
            str: Path to the configured project directory or its environment
                variable template.
        """
        _project_dir_path = self.get_preferences_dict_value(
            key="project_dir", default="{project-file-dir}"
        )
        if not _project_dir_path:
            _project_dir_path = "{project-file-dir}"
        if parse_vars:
            environment_vars_dict = get_environment_variables(rig_project=self)
            _project_dir_path = core_str.replace_keys_with_values(_project_dir_path, environment_vars_dict)
        return _project_dir_path

    def get_project_file_dir_path(self):
        """Gets the directory containing the current rig project file.

        Returns:
            str: Existing rig project file directory, or an empty string when
                the project has not been saved or its file no longer exists.
        """
        if not self.project_file_path:
            return ""

        project_file_path = os.path.abspath(str(self.project_file_path))
        if not os.path.isfile(project_file_path):
            return ""

        return os.path.normpath(os.path.dirname(project_file_path))

    def get_alias(self):
        """
        Gets a project alias (alternative name)
        Returns:
            str: A project alias. Empty string "" if never defined.
        """
        _project_alias = self.get_preferences_dict_value(key="alias", default="")
        if _project_alias is None:
            _project_alias = ""
        return _project_alias

    def get_control_rig_pose_name(self):
        """
        Gets the control rig pose name. If not found a default value is returned instead.
        Returns:
            str: A name for the control rig pose.
        """
        _control_rig_pose_name = self.get_preferences_dict_value(
            key="control_rig_pose_name", default=core_naming.NamingConstants.Poses.TPOSE
        )
        return _control_rig_pose_name

    def get_modules_proxies(self):
        """
        Gets all proxies found in the project

        Return:
            list[Proxy]: A list of all proxies found in the project.
        """
        proxies = []
        for module in self.modules:
            proxies.extend(module.get_proxies())
        return proxies

    def get_potential_drivers(self, filter_modules=None, add_global_drivers=True):
        """
        Get potential drivers/controls that will be generated only after the build rig step.
        This can be used to determine interactions between elements even before they were built.
        Args:
            filter_modules (ModuleGeneric, List[ModuleGeneric] optional): If provided only drivers from this module(s)
                                                                         are returned.
            add_global_drivers (bool, optional): If True, both global and global offset controls will be included.

        Returns:
            dict: A dictionary where the key is the source object (e.g. module or project), and the value is a list of
                  potential drivers/controls. If not adding global all source objects will be Modules.
                  e.g. { ModuleGeneric: ["module_uuid-fk-spine03", "module_uuid-ik-spine03", ...]}
        """
        _unacceptable_drivers = [tools_rig_const.RiggerDriverTypes.BLOCK]
        driver_dict = {}
        if add_global_drivers and filter_modules is None:
            global_purpose = tools_rig_const.RiggerConstants.REF_VALUE_PURPOSE_GLOBAL
            global_uuid = f"{self.get_uuid()}-{tools_rig_const.RiggerDriverTypes.FK}-{global_purpose}"
            global_offset_uuid = f"{self.get_uuid()}-{tools_rig_const.RiggerDriverTypes.OFFSET}-{global_purpose}"
            driver_dict[self] = [global_uuid, global_offset_uuid]
        # All modules or only provided one?
        _modules = self.modules
        if filter_modules and isinstance(filter_modules, list):
            _modules = filter_modules
        if filter_modules and isinstance(filter_modules, ModuleGeneric):
            _modules = [filter_modules]
        for filter_modules in _modules:
            # --- Proxies ---
            proxies = filter_modules.get_proxies()
            if not proxies:
                continue  # No proxies, go to the next module...
            # --- Drivers ---
            module_drivers_uuids = []
            for proxy in proxies:
                purpose = proxy.get_meta_purpose()
                driver_types = proxy.get_driver_types()
                if driver_types is None:
                    continue  # No drivers
                for drv_type in driver_types:
                    if drv_type in _unacceptable_drivers:
                        continue  # Ignore unacceptable drivers
                    driver_uuid = f"{filter_modules.get_uuid()}-{drv_type}-{purpose}"
                    module_drivers_uuids.append(driver_uuid)
            # -- Potential Controls Found ---
            if module_drivers_uuids:
                driver_dict[filter_modules] = module_drivers_uuids
        return driver_dict

    def get_built_drivers(self, filter_source=None, filter_driver_type=None, filter_driver_purpose=None):
        """
        Finds and returns a list of drivers found in this scene.
        This function should be used only after the build otherwise it will always return an empty result.
        Args:
            filter_source (ModuleGeneric, RigProject, optional): If provided only drivers from this module are returned.
            filter_driver_type (str, optional): If provided, only drivers of this type are returned.
            filter_driver_purpose (str, optional): If provided, only drivers of this purpose are returned.

        Returns:
            List[Node]: A list of Node objects. Each object is the path to a found driver.
        """
        # Filters
        _sources = self.modules + [self]  # All modules and the project (project carries the global controls)
        if filter_source:
            _sources = [filter_source]
        if filter_source and isinstance(filter_source, list):
            _sources = filter_source
        # Lookup
        found_drivers_list = []
        for source in _sources:

            detected_drivers = tools_rig_utils.find_drivers_from_module(
                source_uuid=source, filter_driver_type=filter_driver_type, filter_driver_purpose=filter_driver_purpose
            )
            if detected_drivers:
                found_drivers_list.extend(detected_drivers)
        return found_drivers_list

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig project is valid (can be used)
        """
        if not self.modules:
            logger.warning("Missing modules. A rig project needs at least one module to function.")
            return False
        return True

    def execute_modules_code(self, required_order):
        """
        Tries to run any code that matches the required order.
        Args:
            required_order (str, None): If provided, the code will only run when matching the provided order
            according to the CodeData object.
        """
        for module in self.modules:
            if not module.is_active():  # If not active, skip
                continue
            module.execute_module_python_code(required_order=required_order)

    def refresh_modules_project_reference(self):
        """
        Updates a private variable called "_project" found under the current modules with a reference to the project
        containing them.
        """
        for module in self.modules:
            module.set_parent_project(rig_project=self)

    def update_modules_order(self):
        """
        Refreshes the order of the modules topologically to make sure children modules come after their parents
        """
        # Create Topological Hierarchy
        updated_modules = self.get_modules()
        for module in self.get_modules():
            parent_proxy_uuid = module.get_parent_uuid()
            if not parent_proxy_uuid or not isinstance(parent_proxy_uuid, str):
                continue
            parent_module = self.get_module_from_proxy_uuid(parent_proxy_uuid)
            if module == parent_module:
                continue
            if parent_module:
                moving_module_index = updated_modules.index(module)
                moving_module_popped = updated_modules.pop(moving_module_index)
                parent_index = updated_modules.index(parent_module)
                updated_modules.insert(parent_index + 1, moving_module_popped)
        self.set_modules(updated_modules)

    def align_module_proxies_to_joints(self):
        """
        Aligns the proxies to the joints.
        """
        for module in self.modules:
            if not module.is_active():  # If not active, skip
                continue
            module.align_proxies_to_joints()

    def print_modules_order(self, get_name=True):
        """
        Utility function used to print the list of modules along with their index.
        Format: <index>: <module_name> e.g. 0: Root
        Args:
            get_name (bool, optional): If True, it will get the stored module name. If False, it's type instead.
        """
        _modules = self.get_modules()
        _index_width = len(str(len(_modules) - 1))  # -1 to account for 0 based array
        _separator_line = f"{'#' * 20} {self.get_name()} Modules: {'#' * 20}"
        print(_separator_line)
        for index, module in enumerate(_modules):
            formatted_index = f"{str(index).zfill(_index_width)}"
            _line = f"{formatted_index}: {module.get_module_class_name(remove_module_prefix=True, formatted=True)}"
            if get_name:
                _line = f"{formatted_index}: {module.get_name()}"
            print(_line)
        print("#" * len(_separator_line))

    # --------------------------------------------------- Build --------------------------------------------------
    def build_proxy(self, optimized=False):
        """
        Builds Proxy/Guide Armature. This later becomes the skeleton that is driven by the rig controls.
        Args:
            optimized (bool, optional):
                If True, skips creating lines or shapes to speed up the build process.
                This is useful when the user is actively building the rig rather than editing the proxy visually.
        """
        cmds.refresh(suspend=True)
        try:
            self.execute_modules_code(CodeData.Order.pre_proxy)  # Try to run any pre-proxy code.
            logger.operation("Building Proxy" + (" (optimized)" if optimized else ""))
            root_group = tools_rig_utils.create_root_group(is_proxy=True)
            root_transform = tools_rig_utils.create_ctrl_proxy_global()
            core_hrchy.parent(source_objects=root_transform, target_parent=root_group)
            category_groups = tools_rig_utils.create_utility_groups(line=True, target_parent=root_group)
            line_grp = category_groups.get(tools_rig_const.RiggerConstants.REF_ATTR_LINES)
            attr_to_activate = ["overrideEnabled", "overrideDisplayType", "hiddenInOutliner"]
            core_attr.set_attr(obj_list=line_grp, attr_list=attr_to_activate, value=1)
            core_attr.add_attr(
                obj_list=str(root_transform), attributes="linesVisibility", attr_type="bool", default=True
            )
            cmds.connectAttr(f"{root_transform}.linesVisibility", f"{line_grp}.visibility")

            # Build Proxy
            proxy_data_list = []
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                proxy_data_list += module.build_proxy(optimized=optimized)

            for proxy_data in proxy_data_list:
                core_color.add_side_color_setup(obj=proxy_data.get_long_name())
                core_hrchy.parent(source_objects=proxy_data.get_setup(), target_parent=line_grp)
                core_hrchy.parent(source_objects=proxy_data.get_offset(), target_parent=root_transform)

            # Parent Proxy
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                tools_rig_utils.parent_proxies(proxy_list=module.get_proxies())
                if not optimized:
                    tools_rig_utils.create_proxy_visualization_lines(
                        proxy_list=module.get_proxies(), lines_parent=line_grp
                    )
                for proxy in module.get_proxies():
                    proxy.apply_attr_dict()
            for module in self.modules:
                if not module.is_active():  # If not active, skip
                    continue
                module.build_proxy_setup()

            cmds.select(clear=True)
            self.execute_modules_code(CodeData.Order.post_proxy)  # Try to run any post-proxy code.

            # Fit View (Focus on Proxy)
            if self.get_preferences_dict_value(key="view_fit_skeleton", default=True) and not optimized:
                try:
                    cmds.viewFit(all=True)
                except Exception as e:
                    logger.debug(e)

        except Exception as e:
            raise e
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh()

    def build_skeleton(self):
        """
        Builds project skeleton.
        """
        self.raise_for_invalid_control_rig_pose()
        self.execute_modules_code(CodeData.Order.pre_skeleton)  # Try to run any pre-skeleton code.

        logger.operation("Building Skeleton")

        # builds module joints
        for module in self.modules:
            if not module.is_active():  # If not active, skip
                continue
            module.build_skeleton_joints()

        # builds module skeleton hierarchy
        for module in self.modules:
            if not module.is_active():  # If not active, skip
                continue
            module.build_skeleton_hierarchy()

        # Fit View (Focus on Created Skeleton)
        if self.get_preferences_dict_value(key="view_fit_skeleton", default=True):
            skeleton_grp = tools_rig_utils.find_skeleton_group()
            if skeleton_grp:
                children = cmds.listRelatives(skeleton_grp, allDescendents=True, fullPath=True) or []
                try:
                    cmds.viewFit(children)
                except Exception as e:
                    logger.warning(f"Unable to fit view for created skeleton. Issue: {e}")

        # Freeze the rotations of the skeleton
        cmds.select(tools_rig_utils.get_single_skeleton_root_joint(), hi=True)
        joint_list = cmds.ls(sl=True, type="joint")
        cmds.select(clear=True)
        [cmds.makeIdentity(jnt, apply=True, rotate=True) for jnt in joint_list]

        self.execute_modules_code(CodeData.Order.post_skeleton)  # Try to run any post-skeleton code.

        control_pose_mode = self.get_control_rig_pose_mode()
        if self.is_control_rig_pose_enabled():
            logger.operation(f'Applying Control Rig Pose ({control_pose_mode.title()})')

            # Store the bind pose before transitioning to a distinct control rig pose.
            root_joint = tools_rig_utils.get_single_skeleton_root_joint()
            core_pose.delete_dagpose()
            core_pose.create_apose(root=root_joint)

            if control_pose_mode == tools_control_pose.ControlRigPoseMode.CUSTOM:
                from gt.tools.auto_rigger import control_rig_pose_service

                control_rig_pose_service.apply_project_control_rig_pose(self)
            else:
                # Biped module helpers generally resolve the skeleton to a T-pose.
                for module in self.modules:
                    if not module.is_active():
                        continue
                    module.build_control_rig_pose()

            # Legacy DAG pose names remain stable for existing modules and rig consumers.
            core_pose.create_dagpose(root=root_joint, pose_name=self.get_control_rig_pose_name())
            core_pose.zero_out_pose(root=root_joint, tpose_name=self.get_control_rig_pose_name())

            # Match proxy positions to the control pose before control construction.
            self.align_module_proxies_to_joints()
            core_pose.set_apose()

        # Bind-pose operations, such as skin loading, run even when the control pose is disabled.
        self.execute_modules_code(CodeData.Order.pre_control_pose)

        if self.is_control_rig_pose_enabled():
            core_pose.set_dagpose(pose_name=self.get_control_rig_pose_name())

        # This phase always represents the final pose used to construct the control rig.
        self.execute_modules_code(CodeData.Order.post_control_pose)

    def build_rig(self):
        """
        Builds Rig using Proxy/Guide Armature/Skeleton from previous step (build_proxy)
        """
        self.raise_for_invalid_control_rig_pose()
        cmds.refresh(suspend=True)
        try:
            root_group = tools_rig_utils.create_root_group()
            global_ctrl = tools_rig_utils.create_ctrl_global()
            global_offset_ctrl = tools_rig_utils.create_ctrl_global_offset()
            category_groups = tools_rig_utils.create_utility_groups(
                geometry=True, skeleton=True, control=True, setup=True, target_parent=root_group
            )
            geometry_grp = category_groups.get(tools_rig_const.RiggerConstants.REF_ATTR_GEOMETRY)
            control_grp = category_groups.get(tools_rig_const.RiggerConstants.REF_ATTR_CONTROL)
            skeleton_grp = category_groups.get(tools_rig_const.RiggerConstants.REF_ATTR_SKELETON)
            setup_grp = category_groups.get(tools_rig_const.RiggerConstants.REF_ATTR_SETUP)
            core_hrchy.parent(source_objects=list(category_groups.values()), target_parent=root_group)
            core_hrchy.parent(source_objects=global_ctrl, target_parent=control_grp)
            core_hrchy.parent(source_objects=global_offset_ctrl, target_parent=global_ctrl)

            # Geometry Selectable Behaviour
            core_attr.add_separator_attr(target_object=geometry_grp, attr_name=f"geometryOptions")
            block_sel_attr = tools_rig_const.RiggerConstants.ATTR_BLOCK_SELECTION
            core_attr.add_attr(obj_list=geometry_grp, attr_type="bool", is_keyable=True, attributes=block_sel_attr)
            cmds.setAttr(f"{geometry_grp}.{block_sel_attr}", 1)
            cmds.setAttr(f"{geometry_grp}.overrideDisplayType", 2)
            cmds.connectAttr(f"{geometry_grp}.{block_sel_attr}", f"{geometry_grp}.overrideEnabled")

            # Add Project Metadata Attributes
            _rig_meta_lookup_attr = tools_rig_const.RiggerConstants.REF_ATTR_ROOT_RIG
            _rig_meta_attr_name = tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_NAME
            _rig_meta_attr_data = tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA
            _rig_meta_attr_geo_grp = tools_rig_const.RiggerConstants.ATTR_RIG_GEOMETRY_GRP
            _rig_meta_attr_sk_grp = tools_rig_const.RiggerConstants.ATTR_RIG_SKELETON_GRP
            _rig_meta_attr_ctrl_grp = tools_rig_const.RiggerConstants.ATTR_RIG_CONTROL_GRP
            _rig_meta_attr_setup_grp = tools_rig_const.RiggerConstants.ATTR_RIG_SETUP_GRP
            _rig_meta_attr_tpose_data = tools_rig_const.RiggerConstants.ATTR_RIG_TPOSE_DATA
            _rig_meta_attr_apose_data = tools_rig_const.RiggerConstants.ATTR_RIG_APOSE_DATA
            _rig_meta_attr_export_anim_bs = tools_rig_const.RiggerConstants.ATTR_RIG_EXPORT_ANIM_BS
            _meta_attrs = [
                _rig_meta_attr_name,
                _rig_meta_attr_data,
                _rig_meta_attr_tpose_data,
                _rig_meta_attr_apose_data,
            ]
            core_attr.add_attr(obj_list=root_group, attr_type="string", is_keyable=False, attributes=_meta_attrs)
            core_attr.add_attr(
                obj_list=root_group, attr_type="bool", is_keyable=False, attributes=_rig_meta_attr_export_anim_bs
            )
            cmds.addAttr(root_group, longName=_rig_meta_attr_geo_grp, attributeType="message")
            cmds.addAttr(root_group, longName=_rig_meta_attr_sk_grp, attributeType="message")
            cmds.addAttr(root_group, longName=_rig_meta_attr_ctrl_grp, attributeType="message")
            cmds.addAttr(root_group, longName=_rig_meta_attr_setup_grp, attributeType="message")
            # Set/Connect Project Metadata Attributes
            _project_as_str = json.dumps(self.get_project_as_dict())
            _root_joint = tools_rig_utils.get_single_skeleton_root_joint()
            core_attr.set_attr(f"{root_group}.{_rig_meta_lookup_attr}", self.get_uuid())
            core_attr.set_attr(f"{root_group}.{_rig_meta_attr_name}", self.get_name())
            core_attr.set_attr(f"{root_group}.{_rig_meta_attr_data}", _project_as_str)
            _export_anim_bs_value = self.get_preferences_dict_value(key="export_anim_blendshapes", default=False)
            core_attr.set_attr(f"{root_group}.{_rig_meta_attr_export_anim_bs}", _export_anim_bs_value)
            cmds.connectAttr(
                f"{root_group}.{_rig_meta_attr_geo_grp}",
                f"{geometry_grp}.{tools_rig_const.RiggerConstants.REF_ATTR_GEOMETRY}",
            )
            cmds.connectAttr(
                f"{root_group}.{_rig_meta_attr_sk_grp}",
                f"{skeleton_grp}.{tools_rig_const.RiggerConstants.REF_ATTR_SKELETON}",
            )
            cmds.connectAttr(
                f"{root_group}.{_rig_meta_attr_ctrl_grp}",
                f"{control_grp}.{tools_rig_const.RiggerConstants.REF_ATTR_CONTROL}",
            )
            cmds.connectAttr(
                f"{root_group}.{_rig_meta_attr_setup_grp}",
                f"{setup_grp}.{tools_rig_const.RiggerConstants.REF_ATTR_SETUP}",
            )

            # Connect Scale
            cmds.connectAttr(f"{global_ctrl}.scale", f"{skeleton_grp}.scale")
            cmds.connectAttr(f"{global_ctrl}.scale", f"{setup_grp}.scale")

            # Hide Skeleton
            if self.get_preferences_dict_value(key="hide_skeleton", default=True):
                cmds.setAttr(f"{skeleton_grp}.v", 0)

            # Add Global Control Driver UUIDs
            tools_rig_utils.add_driver_uuid_attr(
                target_driver=global_ctrl,
                module_uuid=self.get_uuid(),
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=tools_rig_const.RiggerConstants.REF_VALUE_PURPOSE_GLOBAL,
            )
            tools_rig_utils.add_driver_uuid_attr(
                target_driver=global_offset_ctrl,
                module_uuid=self.get_uuid(),
                driver_type=tools_rig_const.RiggerDriverTypes.OFFSET,
                proxy_purpose=tools_rig_const.RiggerConstants.REF_VALUE_PURPOSE_GLOBAL,
            )

            # Build Skeleton
            self.build_skeleton()

            # Build Rig
            if self.get_preferences_dict_value(key="build_control_rig", default=True):  # Key from RigPreferencesData
                self.execute_modules_code(CodeData.Order.pre_control_rig)  # Try to run any pre-control-rig code.

                logger.operation("Building Control Rig")
                for module in self.modules:
                    if not module.is_active():  # If not active, skip
                        continue
                    is_override = utils_sys.is_method_overridden(
                        base_class=ModuleGeneric, target_class_or_instance=module, method_name="build_rig"
                    )
                    if is_override:
                        logger.info(f"(Building): {module.get_name()}")
                    else:
                        logger.debug(f"(Building): {module.get_name()} (Not overridden, skipped)")

                    module.build_rig()

                # build rig post
                logger.operation("Building Control Rig (Post)")
                for module in self.modules:
                    if not module.is_active():  # If not active, skip
                        continue
                    is_override = utils_sys.is_method_overridden(
                        base_class=ModuleGeneric, target_class_or_instance=module, method_name="build_rig_post"
                    )
                    if is_override:
                        logger.info(f"(Post Script): {module.get_name()}")
                    else:
                        logger.debug(f"(Post Script): {module.get_name()} (Not overridden)")
                    module.build_rig_post()

                self.execute_modules_code(CodeData.Order.post_control_rig)  # Try to run any pre-control-rig code.

            # Delete proxy
            if self.get_preferences_dict_value(key="delete_proxy_after_build", default=True):
                proxy_root = tools_rig_utils.find_root_group_proxy()
                if proxy_root:
                    cmds.delete(proxy_root)
                    logger.operation(f"Deleting Proxy")

            # Store the control rig pose and bind pose as metadata after the build. Legacy T/A metadata attribute
            # names remain unchanged for compatibility. At this point the rig should be at rest, in FK, with
            # automations at zero.
            generated_poses = tools_rig_utils.get_control_rig_control_pose_and_bind_pose_as_dict(
                control_pose_name=self.get_control_rig_pose_name()
            )
            if generated_poses:
                _tpose_as_dict, _apose_as_dict = generated_poses
                _tpose_as_string = json.dumps(_tpose_as_dict)
                _apose_as_string = json.dumps(_apose_as_dict)
                core_attr.set_attr(f"{root_group}.{_rig_meta_attr_tpose_data}", _tpose_as_string)
                core_attr.set_attr(f"{root_group}.{_rig_meta_attr_apose_data}", _apose_as_string)

            removed_compensation_transforms = core_hrchy.cleanup_joint_parent_compensation_transforms()
            if removed_compensation_transforms:
                logger.debug(
                    f"Removed {len(removed_compensation_transforms)} temporary joint parenting "
                    "compensation transform(s)."
                )

            self.execute_modules_code(CodeData.Order.post_build)  # Try to run any post_build code.

        except Exception as e:
            logger.critical(f"Error while building rig! Issue: {e}")
            raise e
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh()
            cmds.select(clear=True)


def get_environment_variables(rig_project=None):
    """
    Gets a dictionary where the keys are the variables and the values are the run-time determined paths.
    These are used to determine what variables should represent when updating a path. For example:
    "{temp-dir}/dir" would become "C:/Users/<user>/AppData/Local/Temp/dir"
    Variables:
        "{project-name}": The name of the project.
        "{project-alias}": An alias for the project. (if defined)
        "{project-sanitized-name}": Sanitized name of project.
        "{temp-dir}": is the "temp" folder.
        "{home-dir}": is the home folder. e.g. "Documents" on Windows.
        "{desktop-dir}": is the path to the desktop folder.
        "{tests-data-dir}": The package "tests" folder.
        "{project-dir}": is the latest known project folder. Empty when no project is available.
        "{project-file-dir}": is the directory containing the loaded rig project file.
        "{scene-dir}": is the directory of the current scene. (Only available when saved, otherwise "")
        "{year}": Current year (e.g. 2025)
        "{month}": Current month (e.g. 05)
        "{day}": Current day (e.g. 15)
        "{time}": Current time (e.g. 14-30-59)
        "{hostname}": Name of the machine/host. (e.g. "My-PC")
        "{module-name}": Name of the module (Only available when called from a module, not this function)
        "{module-sanitized-name}": Sanitized name of module.
    Args:
        rig_project (RigProject, optional): If a rig project is provided, user-defined variables will be available.
        For example, the "{project-dir}" is always empty when no project is available.
    Returns:
        dict: A dictionary where keys are variables and values are the paths.
    """
    # Get Initial Values
    now = datetime.datetime.now()
    environment_vars_dict = {
        "{project-name}": "",
        "{project-alias}": "",
        "{project-sanitized-name}": "",
        "{temp-dir}": utils_sys.get_temp_dir(),
        "{home-dir}": utils_sys.get_home_dir(),
        "{desktop-dir}": utils_sys.get_desktop_path(),
        "{tests-data-dir}": "",
        "{scene-dir}": "",
        "{project-dir}": "",
        "{project-file-dir}": "",
        "{year}": now.strftime("%Y"),
        "{month}": now.strftime("%m"),
        "{day}": now.strftime("%d"),
        "{time}": now.strftime("%H-%M-%S"),
        "{hostname}": socket.gethostname(),
        "{module-name}": "",  # Only available when called from a module (outside this function)
        "{module-sanitized-name}": "",  # Only available when called from a module (outside this function)
    }
    # Check Project Availability
    if rig_project:
        environment_vars_dict["{project-name}"] = rig_project.get_name()
        environment_vars_dict["{project-alias}"] = rig_project.get_alias()
        _lower_snake_name = rig_project.get_name().lower().replace(" ", "_")
        environment_vars_dict["{project-sanitized-name}"] = utils_sys.sanitize_filename(_lower_snake_name)

    # Check Scene Availability
    _current_scene_file = cmds.file(query=True, sceneName=True) or ""
    if _current_scene_file:
        environment_vars_dict["{scene-dir}"] = os.path.dirname(_current_scene_file)
    # Get Tests Data Dir
    import gt.tests.test_auto_rigger as test_auto_rigger
    import inspect

    _test_module_path = inspect.getfile(test_auto_rigger)
    _tests_dir = os.path.dirname(_test_module_path)
    environment_vars_dict["{tests-data-dir}"] = os.path.join(_tests_dir, "data")
    # Check Project Availability
    if rig_project is not None and isinstance(rig_project, RigProject):
        project_file_dir = rig_project.get_project_file_dir_path()
        environment_vars_dict["{project-file-dir}"] = project_file_dir
        _project_dir_path = rig_project.get_project_dir_path()
        _project_dir_path = core_str.replace_keys_with_values(_project_dir_path, environment_vars_dict)
        if _project_dir_path:
            _project_dir_path = os.path.normpath(_project_dir_path)  # Normalize Path
        environment_vars_dict["{project-dir}"] = _project_dir_path

    # Return Environment Variables Dictionary
    return environment_vars_dict


if __name__ == "__main__":
    # logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    # from gt.tools.auto_rigger.templates.template_biped import create_template_biped
    # a_biped_project = create_template_biped()
    # a_biped_project.build_proxy(optimized=True)
    # a_biped_project.build_rig()

    # -----------------------------------------------------------------------------------------------------
    # Proxy Example
    root = Proxy(name="root")  # Create a proxy to be used as root
    root.set_meta_purpose("root")  # Can be used to identify what is the general purpose of this joint

    a_1st_proxy = Proxy(name="first")
    a_1st_proxy.set_position(z=1, x=-1)  # Actual position (user input in case they move it)
    a_1st_proxy.set_parent_uuid_from_proxy(root)  # Makes it a child of the previously created proxy
    a_1st_proxy.add_to_attr_dict("prefix", "test")

    a_2nd_proxy = Proxy(name="second")  # If a name is not given it becomes the default "proxy"
    a_2nd_proxy.set_rotation_order("zxy")
    a_2nd_proxy.set_initial_position(y=2, x=-1)  # Initial position is the "Zero" value of the proxy (for modules)
    a_2nd_proxy.set_position(x=-1)  # Both initial position and position are world values, not object space
    a_2nd_proxy.set_parent_uuid(a_1st_proxy.get_uuid())

    a_3rd_proxy = Proxy(name="third")
    a_3rd_proxy.set_position(y=3, x=-1, z=-2)
    a_3rd_proxy.set_parent_uuid_from_proxy(a_2nd_proxy)  # Something as set parent uuid, but it uses a proxy as input

    # # CODE BELOW IS NOT DONE MANUALLY, THIS IS JUST AN EXAMPLE OF WHAT HAPPENS WHEN A MODULE CREATES IT !!!
    # # These are automatically executed through the "build_proxy" and "build_proxy_setup" functions (Module)
    # a_1st_proxy.build()
    # a_1st_proxy.apply_transforms()
    #
    # a_2nd_proxy.build()  # Creates the proxy, nothing else
    # a_2nd_proxy.apply_offset_transform()  # Set zero/initial position
    # a_2nd_proxy.apply_transforms()  # Set position
    #
    # a_3rd_proxy.build()
    # a_3rd_proxy.apply_transforms()

    # -----------------------------------------------------------------------------------------------------
    # Module Example
    a_root_module = ModuleGeneric(name="a_root_module")
    a_root_module.add_to_proxies(root)
    a_root_module.set_orientation_method(method="world")  # Determines auto orientation (more about it later)

    a_1st_module = ModuleGeneric(name="a_1st_module")
    a_1st_module.add_to_proxies(a_1st_proxy)  # Add previously created proxies
    a_1st_module.add_to_proxies(a_2nd_proxy)
    a_1st_module.add_to_proxies(a_3rd_proxy)

    a_2nd_module = ModuleGeneric(name="a_2nd_module")  # These are generic, but they could be a leg, or an arm...
    a_2nd_module.set_prefix("my_prefix")
    a_new_proxy = a_2nd_module.add_new_proxy()  # Automatically creates a new proxy inside the module
    a_new_proxy.set_name("my_new_proxy")
    a_new_proxy.set_position(x=-1, y=5, z=-3)
    a_new_proxy.set_parent_uuid_from_proxy(a_3rd_proxy)  # Makes a proxy inside another module its parent

    a_3rd_module = ModuleGeneric(name="a_3rd_module")
    another_proxy = Proxy(name="yet_another_proxy")
    another_proxy.set_position(z=-5)
    a_3rd_module.add_to_proxies(another_proxy)
    a_3rd_module.set_orientation_direction(is_positive=True)

    # # # CODE BELOW IS NOT DONE MANUALLY, THIS IS JUST AN EXAMPLE OF WHAT HAPPENS WHEN A PROJECT CREATES IT !!!
    # # # These are automatically executed through the "build_proxy" and "build_rig" functions (Module)
    # a_1st_module.build_proxy()
    # a_1st_module.build_proxy_setup()
    #
    # a_2nd_module.build_proxy()
    # a_2nd_module.build_proxy_setup()  # Position and  logic (check docstring. Hover)
    #
    # a_3rd_module.build_proxy()
    # a_3rd_module.build_proxy_setup()

    # -----------------------------------------------------------------------------------------------------
    # Project Example
    import gt.tools.auto_rigger.modules.module_biped_arm as arm

    a_project = RigProject()
    a_project.add_to_modules(a_root_module)
    a_project.add_to_modules(a_1st_module)
    # a_project.add_to_modules(a_2nd_module)
    # a_project.add_to_modules(a_3rd_module)
    # a_project.add_to_modules(a_root_module)
    # a_project.add_to_modules(arm.ModuleBipedArmLeft())

    # Main functions
    a_project.build_proxy()
    # a_project.build_rig()

    # # Misc
    # a_project.print_modules_order()
    # a_project_modules = a_project.get_modules()
    # a_project_as_dict = a_project.get_project_as_dict()

    # # Rebuild Project
    # cmds.file(new=True, force=True)
    # a_project_2 = RigProject()
    # a_project_2.read_data_from_dict(a_project_as_dict)
    # a_project_2.build_proxy()
    # a_project_2.build_rig()
