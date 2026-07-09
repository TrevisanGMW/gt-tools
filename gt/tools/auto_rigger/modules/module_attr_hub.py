"""
Auto Rigger Utils Modules
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.color as core_color
import gt.core.curve as core_curve
import gt.core.attr as core_attr
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleAttributeHub(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_attr_hub
    allow_parenting = True
    allow_multiple = True

    DEFAULT_SHAPE = "_gear_pos_z"

    def __init__(self, name="Attribute Hub", prefix="C", suffix=None):
        """
        Initializes the Attribute Hub module.

        Args:
            name (str, optional): Display name of the module. Defaults to "Attribute Hub".
            prefix (str, optional): Name prefix to apply to generated nodes. Defaults to None.
            suffix (str, optional): Name suffix to apply to generated nodes. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.set_extra_callable_function(
            self._reroute_and_set_attributes, order=tools_rig_frm.CodeData.Order.post_build
        )

        self.attr_switcher_proxy = tools_rig_frm.Proxy(name="attributeHub")
        self.attr_switcher_proxy.set_meta_purpose("attributeHub")
        self.attr_switcher_proxy.set_locator_scale(2)
        self.attr_switcher_shape = self.DEFAULT_SHAPE  # If available, it becomes the proxy and control shape
        self.attr_mapping = {}
        self.attr_values = {}

        self.parent_constraint_type = core_cnstr.ConstraintTypes.POINT

        self._cached_ctrl_offset = None
        self._cached_ctrl = None

        self.proxies = [self.attr_switcher_proxy]

    def _reroute_and_set_attributes(self):
        """
        Attempts to copy and connect attributes according to "self._reroute_attributes"
        Then attempts to set attributes according to "self._set_attr_values_dict"
        """
        self._reroute_attributes()
        self._set_attr_values_dict()

    def _reroute_attributes(self):
        """
        Attempts to copy and connect attributes according to the set "self.attr_mapping"
        """
        # Sanitize list and give feedback
        sanitized_attr_mapping = {}
        for new_attr, target_list in self.attr_mapping.items():
            if target_list is None:  # SEPARATOR
                sanitized_attr_mapping[new_attr] = None
                continue
            _existing_attrs = []
            for target_attr in target_list:
                if cmds.objExists(target_attr):
                    _existing_attrs.append(target_attr)
                else:
                    logger.warning(f'Missing target attribute was ignored: "{target_attr}".')
            if _existing_attrs:
                sanitized_attr_mapping[new_attr] = _existing_attrs

        # Create attributes and connections
        for new_attr, target_list in sanitized_attr_mapping.items():
            if target_list is None:  # SEPARATOR
                core_attr.add_separator_attr(target_object=self._cached_ctrl, attr_name=new_attr)
                continue
            new_attr = core_attr.copy_attr(
                source_attr_path=target_list[0],
                target_list=self._cached_ctrl,
                override_name=new_attr,
                override_keyable=True,
            )
            core_attr.connect_attr(
                source_attr=new_attr[0],
                target_attr_list=target_list,
                force=True,
                verbose=True,
                log_level=logging.WARNING,
            )

    def _set_attr_values_dict(self):
        """
        Applies/sets the values stored in the value dictionary.
        """
        if self.attr_values:
            for attr, value in self.attr_values.items():
                attr_path = f"{self._cached_ctrl}.{attr}"
                if not cmds.objExists(attr_path):
                    logger.warning(f'Unable to set value. Missing expected attribute: "{str(attr)}"')
                    continue
                core_attr.set_attr(attribute_path=attr_path, value=value)

    def set_attr_mapping(self, attr_dict):
        """
        Sets the attribute mapping dictionary.
        The keys are the name of the attributes that will be created.
        The values are lists of attributes to be affected by the key attribute.
        If the value is set to None, the attribute is considered to be a separator.
        If a target attribute is missing, it is ignored.
        Example:
            attr_dict = {
            "cubesVisibility": ["cube_one.v", "cube_two.v", "cube_three.v"],
            "cubesMovement": None,
            "cubeOneTY": ["cube_one.ty"]
        }

        Args:
            attr_dict: A dictionary describing the mapping of the attributes. Following the pattern described above.
        """
        if not attr_dict or not isinstance(attr_dict, dict):
            logger.warning(f"Unable to set attribute mapping dictionary. Incorrect input type.")
            return
        self.attr_mapping = attr_dict

    def set_attr_values(self, attr_value_dict):
        """
        Sets the attribute value dictionary.
        The keys are the name of the attributes that will be affected.
        The values are applied to the found attributes (keys)
        If a target attribute is missing, it is ignored a warning is logged.
        Example:
            attr_dict = {
            "cubesVisibility": 1,
            "cubesMovement": 5,
            "cubeOneTY": 0
        }

        Args:
            attr_value_dict: A dictionary describing the values of the attributes. Following the pattern described above.
        """
        if not attr_value_dict or not isinstance(attr_value_dict, dict):
            logger.warning(f"Unable to set attribute values dictionary. Incorrect input type.")
            return
        self.attr_values = attr_value_dict

    def set_control_name(self, name):
        """
        Sets the initial name for the control
        Args:
            name: A new name for the control.
        """
        self.attr_switcher_proxy.set_name(name=name)

    def set_control_shape(self, shape):
        """
        Sets a new control shape
        Args:
            shape (str): The name of the control file.
        """
        self.attr_switcher_shape = shape

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
            logger.debug(f"Unable to read proxies from dictionary. Input must be a dictionary.")
            return
        self.read_purpose_matching_proxy_from_dict(proxy_dict)

    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        _user_shape = core_curve.get_curve(self.attr_switcher_shape)
        if _user_shape:
            self.attr_switcher_proxy.set_curve(curve=_user_shape)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        Set default values for the attribute hub control.
        """
        attr_switcher_proxy = tools_rig_utils.find_proxy_from_uuid(self.attr_switcher_proxy.get_uuid())
        attrs_to_zero = ["autoColor", "colorDefaultR", "colorDefaultB"]
        core_attr.set_attr(obj_list=attr_switcher_proxy, attr_list=attrs_to_zero, value=0)
        core_attr.hide_lock_default_attrs(obj_list=attr_switcher_proxy, scale=True)
        self.attr_switcher_proxy.apply_transforms()
        super().build_proxy_setup()

    def build_skeleton_joints(self):
        """
        Runs skeleton joints phase, which creates joints out of the proxy elements.
        This  happens after "build_proxy_setup" and as these are used to create the joints.
        """
        ...

    def build_rig(self, project_prefix=None, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            project_prefix (str, optional): If provided, the created elements receive this string as an extra prefix.
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        # Check shape availability
        _ctrl_shape = self.DEFAULT_SHAPE
        if self.attr_switcher_shape and core_curve.get_curve(self.attr_switcher_shape):
            _ctrl_shape = self.attr_switcher_shape

        # Get Useful Elements
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        attr_hub_proxy = tools_rig_utils.find_proxy_from_uuid(self.attr_switcher_proxy.get_uuid())

        # Get Useful Attributes
        locator_scale = cmds.getAttr(f"{attr_hub_proxy}.{tools_rig_const.RiggerConstants.ATTR_PROXY_SCALE}")
        rot_order = cmds.getAttr(f"{attr_hub_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        color = cmds.getAttr(f"{attr_hub_proxy}.overrideColorRGB")[0]

        attr_hub_ctrl, attr_hub_offset = self.create_rig_control(
            control_base_name=self.attr_switcher_proxy.get_name(),
            curve_file_name=_ctrl_shape,
            parent_obj=global_offset_ctrl,
            match_obj=attr_hub_proxy,
            add_offset_ctrl=False,
            rot_order=rot_order,
            rot_order_expose=False,
            shape_scale=locator_scale,
            separator_attr=None,
            color=color,
        )[:2]

        core_attr.hide_lock_default_attrs(attr_hub_ctrl, translate=True, rotate=True, scale=True, visibility=True)
        self._add_driver_uuid_attr(
            target_driver=attr_hub_ctrl,
            driver_type=None,
            proxy_purpose=self.attr_switcher_proxy,
        )
        self._cached_ctrl_offset = attr_hub_offset
        self._cached_ctrl = attr_hub_ctrl

    def build_rig_post(self, project_prefix=None, **kwargs):
        """
        Runs post rig script phase.
        This step runs after the execution of "build_rig" is completed.
        Usually used to define automation or connections that require external elements to exist.

        Args:
            project_prefix (str, optional): An optional prefix related to the project.
                Not used directly in this method but accepted for extensibility.
            **kwargs: Additional keyword arguments (currently unused).
        """
        parent_joint = tools_rig_utils.find_joint_from_uuid(self.parent_uuid)
        if parent_joint:
            core_cnstr.constraint_targets(
                source_driver=parent_joint,
                target_driven=self._cached_ctrl_offset,
                constraint_type=self.parent_constraint_type,
            )
            self._cached_ctrl_offset = None


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from gt.tools.auto_rigger.rig_framework import RigProject, ModuleGeneric

    # Reload ---------------------------------------------------------------------------------------------
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import gt.tools.auto_rigger.modules.module_attr_hub as module_attr_hub
    import importlib

    importlib.reload(tools_rig_fmr)
    importlib.reload(module_attr_hub)
    importlib.reload(tools_rig_utils)

    cmds.file(new=True, force=True)

    # Create Test Elements --------------------------------------------------------------------------------
    def create_test_cubes():
        """Creates three test cubes and set the viewport for visualization"""
        c1 = cmds.polyCube(name="cube_one", ch=False, w=25, h=25, d=25)[0]
        c2 = cmds.polyCube(name="cube_two", ch=False, w=25, h=25, d=25)[0]
        c3 = cmds.polyCube(name="cube_three", ch=False, w=25, h=25, d=25)[0]
        cmds.setAttr(f"{c1}.tx", -30)
        cmds.setAttr(f"{c3}.tx", 30)
        for cube in [c1, c2, c3]:
            cmds.setAttr(f"{cube}.ty", 12.5)
        cmds.modelEditor(cmds.getPanel(withFocus=True), edit=True, wireframeOnShaded=True)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", True)
        core_color.set_color_viewport(obj_list=c1, rgb_color=(1, 0, 0))
        core_color.set_color_viewport(obj_list=c2, rgb_color=(0, 1, 0))
        core_color.set_color_viewport(obj_list=c3, rgb_color=(0, 0, 1))
        cmds.select(clear=True)

    create_test_cubes()

    # Create Test Modules ---------------------------------------------------------------------------------
    a_generic_module = ModuleGeneric()
    an_attribute_switcher = ModuleAttributeHub()

    # Configure Modules -----------------------------------------------------------------------------------
    p1 = a_generic_module.add_new_proxy()
    p2 = a_generic_module.add_new_proxy()
    p3 = a_generic_module.add_new_proxy()
    p1.set_name("first")
    p2.set_name("second")
    p3.set_name("third")
    p2.set_initial_position(y=15)
    p3.set_initial_position(y=30)
    p2.set_parent_uuid(p1.get_uuid())
    p3.set_parent_uuid(p2.get_uuid())
    p1.set_locator_scale(6)
    p2.set_locator_scale(5)
    p3.set_locator_scale(4)

    attr_map = {
        "cubesVisibility": None,  # Separator
        "generalVisibility": ["cube_one.v", "cube_two.v", "cube_three.v"],
        "cubesMovement": None,  # Separator
        "oneTY": ["cube_one.ty"],
        "twoTY": ["cube_two.ty"],
        "threeTY": ["cube_three.ty"],
    }

    attr_values = {
        "generalVisibility": 1,
        "oneTY": 0,
        "twoTY": 10,
        "threeTY": 20,
    }

    an_attribute_switcher.set_attr_mapping(attr_map)
    an_attribute_switcher.set_attr_values(attr_values)
    an_attribute_switcher.set_control_name("cubesAttributeHub")
    an_attribute_switcher.set_control_shape("_letter_v_pos_z")
    an_attribute_switcher.set_parent_uuid(p3.get_uuid())
    # an_attribute_switcher.set_control_shape(shape="_peanut_pos_z")
    an_attribute_switcher.attr_switcher_proxy.set_position(y=60)

    # Create Project and Build ----------------------------------------------------------------------------
    a_project = RigProject()
    # a_project.add_to_modules(a_generic_module)
    a_project.add_to_modules(an_attribute_switcher)
    a_project.set_project_dir_path(r"{desktop-dir}\test_folder")
    # print(a_project.get_project_dir_path(parse_vars=True))  # Absolute path to Desktop\test_folder
    # a_project.add_to_modules(a_generic_module)  # Should be the only thing in the scene after building

    # Build  ----------------------------------------------------------------------------------------------
    a_project.build_proxy()
    a_project.read_data_from_scene()
    project_as_dict = a_project.get_project_as_dict()
    a_project.build_rig()

    # # Rebuild ---------------------------------------------------------------------------------------------
    # cmds.file(new=True, force=True)
    # a_2nd_project = RigProject()
    # a_2nd_project.read_data_from_dict(project_as_dict)
    # a_2nd_project.build_proxy()
    # create_test_cubes()
    # a_2nd_project.build_rig()

    # Frame all
    cmds.viewFit(all=True)
