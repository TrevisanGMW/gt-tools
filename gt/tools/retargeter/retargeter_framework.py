"""
Animation Retargeter Framework

Import Line:
    import gt.tools.retargeter.retargeter_framework as tools_rt_frm
"""

import gt.core.constraint as core_cnstr
import gt.core.namespace as core_nspace
import gt.core.feedback as core_fback
import gt.core.iterable as core_iter
import gt.core.naming as core_naming
import gt.core.node as core_node
import gt.core.uuid as core_uuid
import gt.core.attr as core_attr
import gt.core.io as core_io
import maya.cmds as cmds
import importlib
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TargetingMethods:
    """Defines various targeting methods for retargeting animation."""

    skip = "skip"  # Does not create a link, only used to store control data
    absolute = "absolute"  # aka parent without offset (snap to source)
    offset = "offset"  # aka parent with offset
    position = "position"  # Position/Position with Offset
    rotation = "rotation"  # Rotation/Orientation with offset
    position_rotation = "position_rotation"  # Same as applying both position and rotation method at the same

    @staticmethod
    def get_method_function(method):
        """
        Retrieves the function associated with the given targeting method.

        Args:
            method (str): The name of the targeting method. e.g. 'offset', 'position', 'rotation'...

        Returns:
            callable: The function corresponding to the targeting method, or None if the method is not recognized.
        """
        if method == TargetingMethods.skip:
            return lambda *args, **kwargs: None
        if method == TargetingMethods.absolute:
            return TargetingMethods.create_absolute_link
        if method == TargetingMethods.offset:
            return TargetingMethods.create_offset_link
        if method == TargetingMethods.position:
            return TargetingMethods.create_position_link
        if method == TargetingMethods.rotation:
            return TargetingMethods.create_rotation_link
        if method == TargetingMethods.position_rotation:
            return TargetingMethods.create_position_rotation_link

    @staticmethod
    def get_available_methods():
        """
        Gets a list of all available methods. These are the same as the string attributes found above.
        Returns:
            list: A list of available methods (these are strings)
                  Further description for each method can be found next to each method as a comment.
        """
        methods = []
        attrs = vars(TargetingMethods)
        attrs_keys = [attr for attr in attrs if not (attr.startswith("__") and attr.endswith("__"))]

        for key in attrs_keys:
            attr_value = getattr(TargetingMethods, key)
            if isinstance(attr_value, str) and not callable(attr_value):
                methods.append(attr_value)
        return methods

    @staticmethod
    def get_unavailable_rotation_axes(target):
        """
        Gets a list of unavailable rotation axes.
        Checks for locked or connected channels.
        Args:
            target (str): The name of the target transform node to inspect.
        Returns:
            list: A list of unavailable rotations to be skipped. e.g. ["rx", "rz"]
        """
        unavailable_axes = []
        for ax in ("x", "y", "z"):
            if cmds.getAttr(f"{target}.r{ax}", lock=True):
                unavailable_axes.append(ax)
                continue
            if cmds.listConnections(f"{target}.r{ax}", source=True, destination=False):
                unavailable_axes.append(ax)
        return unavailable_axes

    @staticmethod
    def get_unavailable_translate_axes(target):
        """
        Gets a list of unavailable translation channels.
        Checks for locked or connected channels.
        Args:
            target (str): The name of the target transform node to inspect.
        Returns:
            list: A list of unavailable translations to be skipped. e.g. ["tx", "tz"]
        """
        unavailable_axes = []
        for ax in ("x", "y", "z"):
            if cmds.getAttr(f"{target}.t{ax}", lock=True):
                unavailable_axes.append(ax)
                continue
            if cmds.listConnections(f"{target}.t{ax}", source=True, destination=False):
                unavailable_axes.append(ax)
        return unavailable_axes

    # --------------------------------------------- Link Functions ---------------------------------------------
    @staticmethod
    def create_absolute_link(source, target, *args, **kwargs):
        """
        Creates an absolute (aka parent without offset) link between source and target

        Args:
            source (str): The source object that will drive the target.
            target (str): The target object that will be constrained to the source.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list: A list of created constraints/links
        """
        unavailable_translations = TargetingMethods.get_unavailable_translate_axes(target=target)
        unavailable_rotations = TargetingMethods.get_unavailable_rotation_axes(target=target)

        if len(unavailable_translations + unavailable_rotations) >= 6:
            return

        extra_kwargs = {}
        if unavailable_translations:
            extra_kwargs["skipTranslate"] = unavailable_translations

        if unavailable_rotations:
            extra_kwargs["skipRotate"] = unavailable_rotations

        return core_cnstr.constraint_targets(
            source_driver=source,
            target_driven=target,
            maintain_offset=False,
            constraint_type=core_cnstr.ConstraintTypes.PARENT,
            **extra_kwargs,
        )

    @staticmethod
    def create_offset_link(source, target, *args, **kwargs):
        """
        Creates a parent with offset constraint between source and target.

        Args:
            source (str): The source object that will drive the target.
            target (str): The target object that will be constrained to the source.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list: A list of created constraints/links
        """
        unavailable_translations = TargetingMethods.get_unavailable_translate_axes(target=target)
        unavailable_rotations = TargetingMethods.get_unavailable_rotation_axes(target=target)

        if len(unavailable_translations + unavailable_rotations) >= 6:
            return

        extra_kwargs = {}
        if unavailable_translations:
            extra_kwargs["skipTranslate"] = unavailable_translations

        if unavailable_rotations:
            extra_kwargs["skipRotate"] = unavailable_rotations

        return core_cnstr.constraint_targets(
            source_driver=source,
            target_driven=target,
            maintain_offset=True,
            constraint_type=core_cnstr.ConstraintTypes.PARENT,
            **extra_kwargs,
        )

    @staticmethod
    def create_position_link(source, target, *args, **kwargs):
        """
        Creates a position (point) constraint between source and target.

        Args:
            source (str): The source object that will drive the target.
            target (str): The target object that will be constrained to the source.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list: A list of created constraints/links
        """
        unavailable_translations = TargetingMethods.get_unavailable_translate_axes(target=target)

        if len(unavailable_translations) >= 3:
            return

        extra_kwargs = {}
        if unavailable_translations:
            extra_kwargs["skip"] = unavailable_translations

        return core_cnstr.constraint_targets(
            source_driver=source,
            target_driven=target,
            maintain_offset=True,
            constraint_type=core_cnstr.ConstraintTypes.POINT,
            **extra_kwargs,
        )

    @staticmethod
    def create_rotation_link(source, target, *args, **kwargs):
        """
        Creates a rotation (orient) constraint between source and target.

        Args:
            source (str): The source object that will drive the target.
            target (str): The target object that will be constrained to the source.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list: A list of created constraints/links
        """

        unavailable_rotations = TargetingMethods.get_unavailable_rotation_axes(target=target)
        if len(unavailable_rotations) >= 3:
            return

        extra_kwargs = {"skipTranslate": ["x", "y", "z"]}
        if unavailable_rotations:
            extra_kwargs["skipRotate"] = unavailable_rotations

        return core_cnstr.constraint_targets(
            source_driver=source,
            target_driven=target,
            maintain_offset=True,
            constraint_type=core_cnstr.ConstraintTypes.PARENT,
            **extra_kwargs,
        )

    @staticmethod
    def create_position_rotation_link(source, target, *args, **kwargs):
        """
        Creates a rotation (orient) constraint between source and target.

        Args:
            source (str): The source object that will drive the target.
            target (str): The target object that will be constrained to the source.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list: A list of created constraints/links
        """

        unavailable_translations = TargetingMethods.get_unavailable_translate_axes(target=target)
        unavailable_rotations = TargetingMethods.get_unavailable_rotation_axes(target=target)

        if len(unavailable_translations + unavailable_rotations) >= 6:
            return

        extra_kwargs_pos = {}
        if unavailable_translations:
            extra_kwargs_pos["skip"] = unavailable_translations

        extra_kwargs_orient = {}
        if unavailable_rotations:
            extra_kwargs_orient["skip"] = unavailable_rotations

        point_cnstr = []
        if not len(extra_kwargs_pos) >= 3:
            point_cnstr = core_cnstr.constraint_targets(
                source_driver=source,
                target_driven=target,
                maintain_offset=True,
                constraint_type=core_cnstr.ConstraintTypes.POINT,
                **extra_kwargs_pos,
            )
        orient_cnstr = []
        if not len(extra_kwargs_orient) >= 3:
            orient_cnstr = core_cnstr.constraint_targets(
                source_driver=source,
                target_driven=target,
                maintain_offset=True,
                constraint_type=core_cnstr.ConstraintTypes.ORIENT,
                **extra_kwargs_orient,
            )

        return orient_cnstr + point_cnstr


class TargetingLink:
    """Represents a link between a source object and a target object using a specified targeting method."""

    def __init__(self, source="", target="", method=TargetingMethods.rotation):
        """
        Initializes a TargetingLink object.

        Args:
            source (str): The name of the source object. Default is an empty string.
            target (str): The name of the target object. Default is 'None'.
            method (str): The targeting method to be used. Default is TargetingMethods.offset.
        """

        self.source = source
        self.target = target
        self.method = method

        self.target_data = {}  # TRS + User-defined attributes (when not locked or already receiving input)
        self._short_name_fallback = True  # If path is missing, it attempts to find elements using their short name.
        self._source_namespace = ""
        self._target_namespace = ""

    def __repr__(self):
        """Overrides returned string to improve print output"""
        return f"{self.__class__.__name__}(source={self.source!r}, target={self.target!r}, method={self.method!r})"

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_source(self, source):
        """
        Sets the source object name.

        Args:
            source (str): The name of the source object. In most cases a bone from a motion capture skeleton.
        """
        self.source = source

    def set_source_namespace(self, source_namespace):
        """
        Sets the source object name.

        Args:
            source_namespace (str): Namespace used for the source path.
        """
        self._source_namespace = source_namespace

    def set_target(self, target):
        """
        Sets the target object name.

        Args:
            target (str): The name of the target object. In most cases a rig control.
        """
        self.target = target

    def set_target_namespace(self, target_namespace):
        """
        Sets the source object name.

        Args:
            target_namespace (str): Namespace used for the source path.
        """
        self._target_namespace = target_namespace

    def set_short_name_fallback_state(self, state):
        """
        Sets the state of short name fallback system. If True link will also try to find objects using their short path.
        Args:
            state (bool): New state of the system. If True link will also try to find objects using their short path.
        """
        self._short_name_fallback = state

    def set_method(self, method):
        """
        Sets the targeting method to be used.

        Args:
            method (str): The targeting method from TargetingMethods (e.g., rotation, offset, etc...)
        """
        if method not in TargetingMethods.get_available_methods():
            logger.warning(
                f'Unable to set unrecognized method "{method}". Use a method found under "TargetingMethods".'
            )
            return
        self.method = method

    def set_link_from_dict(self, link_dict):
        """
        Modifies this object to match the data received. (Used to export and import preferences)
        Args:
            link_dict (dict): A dictionary with attributes as keys and values for a link object.
                             e.g. {'source': 'base_jnt', 'target': 'base_ctrl', 'method': 'position_rotation'}
        """
        for key, value in link_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_target_data(self, attr_data):
        """
        Manually sets the target attribute data dictionary.
        Keys are the name of the attributes without the name of the object.
        Values are the values to set the attribute to. e.g. 10
        Args:
            attr_data (dict): A dictionary describing attributes and values
        """
        self.target_data = attr_data

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_source(self):
        """
        Gets the source object name.

        Returns:
            str: The name of the source object.
        """
        return self.source

    def get_target(self):
        """
        Gets the target object name.

        Returns:
            str: The name of the target object.
        """
        return self.target

    def get_method(self):
        """
        Gets the targeting method being used.

        Returns:
            str: The targeting method.
        """
        return self.method

    def get_link_as_dict(self):
        """
        Gets all preferences as a dictionary.
        Returns:
            dict: A dictionary describing all preferences listed on this preferences data object.
        """
        _result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if core_io.is_json_serializable(data=value, allow_none=False):
                    _result[key] = value
        return _result

    def get_health_score(self, verbose=True):
        """
        Gets a number representing if this link is healthy/valid.
        This function can only be used when elements are already present in the scene.

        Args:
            verbose (bool, optional): If True, this function logs warnings when result is not green (2).
        Scores:
           -1: Method doesn't require source (skip method)
            0: Unhealthy/invalid. The link was missing basic elements or has invalid data.
            1: Partially valid. This link had to rely on fallback functions to find elements or didn't find attributes.
            2: Healthy/valid. This link is ready to be used for retargeting.
        UI Colors:
           -1: Grey
            0: Red
            1: Yellow
            2: Green
        Note:
            The logic is matched by TargetingLink._find_object_in_scene function.
        """
        import gt.core.namespace as core_nspace

        score = 2  # Green

        # Handle methods
        skip_flag = TargetingMethods.skip
        if self.method == skip_flag:
            _required_objects = {self.target: self._target_namespace}
        else:
            _required_objects = {self.source: self._source_namespace, self.target: self._target_namespace}

        # Green State - matching the data
        for obj, namespace in _required_objects.items():
            if "|" in obj or ":" in obj:
                # Handle Maya long-absolute names or with namespace.
                # Absolute name with namespace should be the default case.
                full_path = obj
            else:
                full_path = f"{namespace}:{obj}"
            if cmds.objExists(full_path):
                continue
            # Yellow State (Failed to find using full path)
            if self._short_name_fallback:
                embedded_nspace = core_nspace.get_namespace(obj)
                if embedded_nspace != namespace:
                    # get rid of existing wrong namespace in the name
                    _short_name = core_naming.get_short_name(obj, remove_namespace=True)
                    expected_path = f"{namespace}:{_short_name}"
                else:
                    _short_name = core_naming.get_short_name(obj)
                    expected_path = _short_name

                if cmds.objExists(expected_path):
                    score = 1  # Had to use fallback
                    if verbose:
                        logger.warning(f'Short name fallback was used to locate required object: "{obj}".')
                    continue
            # Red State
            if verbose:
                logger.warning(f'Unable to locate required object: "{obj}".')
            score = 0

        if self.method == skip_flag and score == 2 or self.method == skip_flag and score == 1:
            return -1  # target exists, return grey, because it is valid but in skip mode

        return score

    # -------------------------------------------------- Utils --------------------------------------------------
    def _find_object_in_scene(self, obj, namespace):
        """
        Attempts to find an object in the scene while taking in consideration the short name fallback variable.

        Args:
            obj (str): Name/path to the object.
            namespace (str): The namespace used for the source object
        Returns:
            str or None: A path to the object in the scene. None when not found
        Note:
            The logic is matched by TargetingLink.get_health_score function.
        """
        import gt.core.namespace as core_nspace

        # recorded namespace embedded in the long-absolute name and the separate
        # associated namespace could be different.
        # 1 - Find the name as it is
        if "|" in obj or ":" in obj:
            expected_path = obj  # obj has long-absolute name or namespace embedded.
        else:
            expected_path = f"{namespace}:{obj}"  # no namespace, apply the link one.
        if cmds.objExists(expected_path):
            return core_naming.get_long_name(expected_path)
        # 2 - Fallback
        if self._short_name_fallback:
            embedded_nspace = core_nspace.get_namespace(obj)
            if embedded_nspace != namespace:
                # get rid of existing wrong namespace in the name
                _short_name = core_naming.get_short_name(obj, remove_namespace=True)
                expected_path = f"{namespace}:{_short_name}"
            else:
                _short_name = core_naming.get_short_name(obj)
                expected_path = _short_name

            if cmds.objExists(expected_path):
                # long and absolute name
                return core_naming.get_long_name(expected_path, absolute=True)
        return None

    def find_source_in_scene(self):
        """
        Attempts to find the source object in the scene.
        Returns:
            str or None: A path to the object in the scene. None when not found
        """
        return self._find_object_in_scene(obj=self.source, namespace=self._source_namespace)

    def find_target_in_scene(self):
        """
        Attempts to find the target object in the scene.

        Returns:
            str or None: A path to the object in the scene. None when not found
        """
        return self._find_object_in_scene(obj=self.target, namespace=self._target_namespace)

    def read_target_data(self, get_default=True, get_user_defined=True, clear_value=True):
        """
        Gets attributes and their values from the target object.
        Attributes and their values are stored in the dictionary "self.target_data".
        Args:
            get_default (bool, optional): If True, translate, rotate, scale and visibility are included.
            get_user_defined (bool, optional): If True, user-defined attributes are included.
            clear_value (bool, optional): If True, all values are cleared before getting new values.
                                          If False, dictionary is simply updated with new queried values.
        """
        target_path = self.find_target_in_scene()
        if not target_path:
            logger.warning(f'Unable to read data from missing target object: "{self._target_namespace}:{self.target}".')
            return
        attr_dict = core_attr.get_attrs_as_dict(
            obj=target_path,
            filter_locked=True,
            filter_connected=True,
            filter_non_keyable=True,
            full_attr_path=False,
            get_default=get_default,
            get_user_defined=get_user_defined,
        )
        if clear_value:
            self.target_data = attr_dict
        else:
            self.target_data.update(attr_dict)

    def apply_target_data(self):
        """Applies target data back to the target object"""
        if not self.target_data:
            return
        target_path = self.find_target_in_scene()
        if not target_path:
            logger.warning(f'Unable to apply data to missing target object: "{self._target_namespace}:{self.target}".')
            return
        for attr, value in self.target_data.items():
            core_attr.set_attr(attribute_path=f"{target_path}.{attr}", value=value, verbose=True)

    def convert_fallback_target_to_long(self):
        """
        Attempts to convert fallback fixes into long paths to address controls with updates paths.
        """
        found_target = self.find_target_in_scene()
        if found_target and self.target != found_target:
            _short_name = core_naming.get_short_name(found_target)
            _absolute_name = cmds.ls(found_target, long=True, absoluteName=True)
            if _absolute_name:
                self.target = _absolute_name[0]
                logger.info(f'Short name target "{_short_name}" updated to: "{self.target}"')

    def convert_fallback_source_to_long(self):
        """
        Attempts to convert fallback fixes into long paths to address joints with updates paths.
        """
        found_source = self.find_source_in_scene()
        if found_source and self.source != found_source:
            _short_name = core_naming.get_short_name(found_source)
            _absolute_name = cmds.ls(found_source, long=True, absoluteName=True)
            if _absolute_name:
                self.source = _absolute_name[0]
                logger.info(f'Short name source "{_short_name}" updated to: "{self.source}"')

    def create_link(self):
        """
        Creates a link (constraint) between the source and target using the specified namespaces.
        """
        if self.method == TargetingMethods.skip:  # No link necessary
            return
        method_function = TargetingMethods.get_method_function(self.method)
        source = self.find_source_in_scene()
        target = self.find_target_in_scene()
        logger.debug(f"SOURCE: {source}, TARGET: {target} - METHOD: {self.method}")
        if not target and self.target is not None:  # A target is defined, but was not found.
            _source_short = self.source.split("|")[-1].split(":")[-1]
            logger.warning(f'Unable to create link. Missing target: "{self.target}" ' f'(Source: "{_source_short}")')
            return
        if not source and self.source is not None:  # A source is defined, but was not found.
            _target_short = self.target.split("|")[-1].split(":")[-1]
            logger.warning(f'Unable to create link. Missing source: "{self.source}" (Target: "{_target_short}")')
            return
        return method_function(source=source, target=target)


class TargetingAddon:
    allow_multiple = True  # If only one is allowed, a definition will reject new items of the same type.

    class Order:
        """
        List of recognized/accepted order to apply
        """

        pre_retarget = "pre_retarget"  # Before anything is done in the scene
        post_import = "post_import"  # After importing files into the scene
        pre_create_links = "pre_create_links"  # Before the retarget links are created
        post_bake = "post_bake"  # After the main retarget bake
        post_retarget = "post_retarget"  # After retargeting

        @staticmethod
        def get_available_order_items():
            """
            Gets a list of all available order items. These are the same as the attributes under the subclass "Order"
            Returns:
                list: A list of available order items (these are strings)
                      Further description for each method can be found under the "Order" class.
            """
            order_items = []
            # Get the class's __dict__
            class_attributes = vars(TargetingAddon.Order)

            # Filter out dunder keys first
            attribute_keys = [
                attr_name
                for attr_name in class_attributes
                if not (attr_name.startswith("__") and attr_name.endswith("__"))
            ]

            for key in attribute_keys:
                value = getattr(TargetingAddon.Order, key)

                # This is the new check: skip if the value is callable (a function/method)
                if not callable(value):
                    order_items.append(value)

            return order_items

    def __init__(self, name="Generic Addon"):
        """
        Initiates a TargetingAddon object.
        This is similar to a module.
        Args:
            name (str, optional): Defined the name of the addon.
        """
        self.addon = self.__class__.__name__
        self.name = name
        self.execution_order = TargetingAddon.Order.pre_retarget  # Default happens before retargeting.
        self._source_path = ""
        self._target_path = ""
        self._source_namespace = ""
        self._target_namespace = ""
        self._short_name_fallback = True
        self._cached_imported_source_nodes = []
        self._cached_imported_target_nodes = []

    # ------------------------------------------------- Setters -------------------------------------------------

    def set_execution_order(self, order):
        """
        Sets the execution order for this addon.
        This determines when this addon is executed during the retargeting process.
        Args:
            order: An order string found inside of this TargetingAddon object. (e.g. TargetingAddon.Order)
        """
        self.execution_order = order

    def set_addon_from_dict(self, addon_dict):
        """
        Modifies this object to match the data received. (Used to export and import as JSON)
        Args:
            addon_dict (dict): A dictionary where keys are the variable names and values are the variable values.
                             e.g. {'execution_order': 'pre_retarget'}
        """
        for key, value in addon_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_source_path(self, path):
        """
        Sets the source path.

        Args:
            path (str): The source file path used by the definition.
        """
        self._source_path = path

    def set_target_path(self, path):
        """
        Sets the target path.

        Args:
            path (str): The target file path used by the definition.
        """
        self._target_path = path

    def set_source_namespace(self, namespace):
        """
        Sets the source namespace.

        Args:
            namespace (str): The namespace used by source objects when importing them.
        """
        self._source_namespace = namespace

    def set_target_namespace(self, namespace):
        """
        Sets the target namespace.

        Args:
            namespace (str): The namespace used by targets objects when importing them.
        """
        self._target_namespace = namespace

    def set_cached_imported_source_nodes(self, obj_list):
        """
        A list of imported source objects.

        Args:
            obj_list (str): A list of imported objects.
        """
        self._cached_imported_source_nodes = obj_list

    def set_cached_imported_target_nodes(self, obj_list):
        """
        A list of imported target objects.

        Args:
            obj_list (str): A list of imported objects.
        """
        self._cached_imported_target_nodes = obj_list

    def set_short_name_fallback_state(self, state):
        """
        Sets the state of short name fallback system. If True link will also try to find objects using their short path.
        Args:
            state (bool): New state of the system. If True link will also try to find objects using their short path.
        """
        self._short_name_fallback = state

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_class_name(self):
        """
        Gets the class name (type) for this addon.
        Returns:
            str: The name of the addon class.
        """
        return self.addon

    def get_execution_order(self):
        """
        Gets the current execution order for this addon.
        Returns:
            str: Execution order string. Used to determine when this code will be executed during the retarget process.
        """
        return self.execution_order

    def get_addon_as_dict(self):
        """
        Gets all serializable variables as a dictionary.
        Returns:
            dict: A dictionary describing all variables listed on this addon object.
        """
        _result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if core_io.is_json_serializable(data=value, allow_none=False):
                    _result[key] = value
        return _result

    def apply_addon_ordered(self, required_order, *args, **kwargs):
        """
        Tries to run the code defined in the addon.
        Args:
            required_order (str): If provided, it becomes a requirement for the function to run.
        Return:
            any: Result received from the addon.
        """
        if self.execution_order == required_order:
            return self.apply_addon(*args, **kwargs)

    # -------------------------------------------------- Core --------------------------------------------------
    def apply_addon(self, *args, **kwargs):
        """
        Applies the changes defined by this addon.
        This function is overwritten by each addon to behave in whatever way it should behave.
        Args:
            *args: Any arguments necessary for this addon to run.
            **kwargs: Any key arguments necessary for this addon to run.

        Returns:
            any: The result depends on what the extended addon defined as a return value.
        """
        logger.debug(f'Addon "{self.name}" was applied.')

    def read_scene_data(self, *args, **kwargs):
        """
        Reads data from the scene.
        A definition may request all addons to read their relevant data from the scene.
        In this case, this function is called.
        So for example, if the definition called
        Args:
            *args: Any arguments necessary for this addon to run.
            **kwargs: Any key arguments necessary for this addon to run.
        """
        logger.debug(f'Addon "{self.name}" read data from the scene.')


class RetargeterDefinition:
    """
    Represents the definition (project) of the retargeting process, including source file, target file, links and more.
    """

    def __init__(self):
        """
        Initializes the RetargeterDefinition object with default values.
        """
        # UUID to identify retarget definition
        self.uuid = core_uuid.generate_uuid(short=True, short_length=12)
        self.name = "retargeter_definition"

        # Path can only point to ".ma", ".mb" or ".fbx" files.
        self.source_path = ""
        self.target_path = ""

        # Namespaces used to identify objects from source and target files (also fixes non-unique naming clashes)
        self.source_namespace = "source"
        self.target_namespace = "target"

        # Preferences
        self.reference_rig = True  # References rig instead of importing it.
        self.delete_source = False  # Deletes source after retargeting.
        self.delete_static_channels = False  # Deletes static animation channels after retargeting.
        self.short_name_fallback = True  # If long name is not found, an attempt using its short name is also done.
        self.oversampling_rate = 1  # Can help fix popping issues from different FPS source files.

        # Create Must Have Addons
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons  # Here to avoid circular import

        # Main Elements (Addons and Links)
        self.addons = [
            tools_rt_addons.Addons.AddonSceneOptions(),
            tools_rt_addons.Addons.AddonSourceSetup(),
            tools_rt_addons.Addons.AddonPostBake(),
            tools_rt_addons.Addons.AddonPythonScript(),
        ]
        self.links = []  # To be filled with "TargetingLink" objects

        # Internal Variables
        self._cached_link_objects = []  # Cached link objects used to connect source to target during retargeting.
        self._cached_imported_source_nodes = []  # All imported nodes from the source file
        self._cached_imported_target_nodes = []  # All imported nodes from the target file

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_uuid(self, uuid):
        """
        Sets the UUID of the RetargeterDefinition.

        Args:
            uuid (str): The unique identifier for the retargeter definition.
        """
        self.uuid = uuid

    def set_name(self, name):
        """
        Sets the name of the RetargeterDefinition.

        Args:
            name (str): A definition/project name.
        """
        self.name = name

    def set_source_path(self, source_path):
        """
        Sets the source file path.

        Args:
            source_path (str): The path to the source file.
        """
        self.source_path = source_path

    def set_target_path(self, target_path):
        """
        Sets the target file path.

        Args:
            target_path (str): The path to the target file.
        """
        self.target_path = target_path

    def set_source_namespace(self, namespace):
        """
        Sets the namespace for the source file when importing.

        Args:
            namespace (str): The namespace to be used for source objects when importing them.
        """
        self.source_namespace = namespace

    def set_target_namespace(self, namespace):
        """
        Sets the namespace for the target file when importing.

        Args:
            namespace (str): The namespace to be used for targets objects when importing them.
        """
        self.target_namespace = namespace

    def set_links(self, links):
        """
        Directly sets the links list. Used to override all existing links.
        In most cases the "add_link" function will be used instead.

        Args:
            links (list): A list of TargetingLink objects.
        """
        if not links or not isinstance(links, list):
            logger.warning(f"Unable to set new links list. Provided argument was not a list.")
            return
        self.links = links

    def set_reference_rig_status(self, reference_rig):
        """
        Sets whether the target file should be referenced as a rig.

        Args:
            reference_rig (bool): If True, the target will be referenced; otherwise, it will be imported.
        """
        self.reference_rig = reference_rig

    def set_delete_source_status(self, delete_source):
        """
        Sets whether the source file should be deleted after the retargeting process.

        Args:
            delete_source (bool): If True, the source file will be deleted after retargeting.
        """
        self.delete_source = delete_source

    def set_delete_static_channels_status(self, delete_static_channels):
        """
        Sets whether the static animation channels should be deleted after the retargeting process.

        Args:
            delete_static_channels (bool): If True, the static animation channels will be deleted after retargeting.
        """
        self.delete_static_channels = delete_static_channels

    def set_shortname_fallback_status(self, shortname_fallback):
        """
        Sets whether the source file should be deleted after the retargeting process.

        Args:
            shortname_fallback (bool): If True, when ong name is not found,
                                       an attempt using its short name is considered.
        """
        self.short_name_fallback = shortname_fallback

    def set_addon_patches(self, patch_list=None):
        """
        Sets the addon patches for the definition.
        Args:
            patch_list (list): list of strings, the patches names defined in retargeter_patches.Patches that
                               need to be added in the current definition.
                               If None, the function clears the addon patches that exist in the definition.
        """
        import gt.tools.retargeter.retargeter_patches as tools_rt_patches

        _available_patches_names = tools_rt_patches.Patches.get_patches_dict().keys()

        # Remove Addon Patches from the definition - clear
        for i, p_addon in reversed(list(enumerate(self.addons))):
            if p_addon.__class__.__name__ in _available_patches_names:
                del self.addons[i]

        # Add the active Addon Patches to the definition
        if patch_list:
            for new_patch_name in _available_patches_names:
                if new_patch_name in patch_list:
                    # Add the Addon Patch to the definition
                    _addon_patch_obj = self.get_addons(filter_type=new_patch_name)
                    if not _addon_patch_obj:
                        # Instantiate a new one
                        _patches_module = importlib.import_module("gt.tools.retargeter.retargeter_patches")
                        _addon_patch_obj = eval(f"_patches_module.Patches.{new_patch_name}()")
                        self.add_addon(_addon_patch_obj)
                    _addon_patch_obj.active = True

    def read_data_from_dict(self, definition_dict):
        """
        Modifies this definition to match the data received. (Used to export and import preferences)
        Args:
            definition_dict (dict): A dictionary with definition keys and values.
                             e.g. {'source': 'base_jnt', 'target': 'base_ctrl', 'method': 'position_rotation'}
        """
        links_key = "links"
        addons_key = "addons"
        keys_to_skip = [links_key, addons_key]
        for key, value in definition_dict.items():
            if hasattr(self, key) and key not in keys_to_skip:
                setattr(self, key, value)

        # Links ------------------------------------------
        _serialized_links = definition_dict.get(links_key)
        new_links = []
        for link_data in _serialized_links:
            new_link = TargetingLink()
            new_link.set_link_from_dict(link_data)
            new_links.append(new_link)
        self.links = new_links

        # Addons -----------------------------------------
        _serialized_addons = definition_dict.get(addons_key)
        new_addons = []
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons
        import gt.tools.retargeter.retargeter_patches as tools_rt_patches

        available_addons = tools_rt_addons.Addons.get_addons_dict()
        available_addons.update(tools_rt_patches.Patches.get_patches_dict())
        for addon_data in _serialized_addons:
            addon_class = addon_data.get("addon")
            if addon_class not in available_addons:
                logger.warning(f'Unable to read unknown addon: "{addon_class}".')
                continue
            new_addon = _module = available_addons.get(addon_class)()
            new_addon.set_addon_from_dict(addon_data)
            new_addons.append(new_addon)
        self.addons = new_addons

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_uuid(self):
        """
        Gets the UUID of the RetargeterDefinition.

        Returns:
            str: The unique identifier of the retargeter definition.
        """
        return self.uuid

    def get_name(self):
        """
        Gets the definition name from the RetargeterDefinition object.

        Returns:
            str: The definition name.
        """
        return self.name

    def get_source_path(self):
        """
        Gets the source file path.

        Returns:
            str: The path to the source file. In most cases an FBX file with motion capture animation data.
        """
        return self.source_path

    def get_target_path(self):
        """
        Gets the target file path.

        Returns:
            str: The path to the target file. In most cases a Maya "MA" file containing a character rig.
        """
        return self.target_path

    def get_source_namespace(self):
        """
        Gets the namespace for the source objects.

        Returns:
            str: The namespace to be used for source imported objects.
        """
        return self.source_namespace

    def get_target_namespace(self):
        """
        Gets the namespace for the target objects.

        Returns:
            str: The namespace to be used for target imported objects.
        """
        return self.target_namespace

    def get_links(self):
        """
        Gets the list of targeting links.

        Returns:
            list: A list of TargetingLink objects.
        """
        return self.links

    def get_links_sources(self):
        """
        Gets a list of all existing sources.
        Returns:
            list: all current sources.
        """
        return [link.get_source() for link in self.links]

    def get_links_targets(self):
        """
        Gets a list of all existing targets.
        Returns:
            list: all current targets.
        """
        return [link.get_target() for link in self.links]

    def get_links_from_source(self, source):
        """
        Gets a list of TargetingLink objects matching the requested source string.
        Args:
            source (str): The name or identifier of the source object to match.
        Returns:
            list: TargetingLink objects matching the requested source string.
        """
        found_links = []
        for link in self.links:
            if source == link.get_source():
                found_links.append(link)
        return found_links

    def get_links_from_target(self, target):
        """
        Gets the first TargetingLink object matching the requested target string.
        Args:
            target (str): The name of the target transform node to inspect.
        Returns:
            list: TargetingLink objects matching the requested target string.
        """
        found_links = []
        for link in self.links:
            if target == link.get_target():
                found_links.append(link)
        return found_links

    def get_links_health_score(self, verbose=True):
        """
        Gets a dictionary where the key is a link object and the value is the health score for the key link.
        e.g. {TargetingLink: 2, TargetingLink: 0}  # The first one is healthy, the second one is not.
        Args:
            verbose (bool, optional): If True, the logger will print warning when issues are detected.

        Returns:
            dict: A dictionary where the key is a link and the value is its health score.
                  2 = healthy (green), 1 = required fallback (yellow), 0 = unhealthy (red)
        """
        link_scores = {}
        for link in self.links:
            link_scores[link] = link.get_health_score(verbose=verbose)
        return link_scores

    def get_addons(self, filter_type=None):
        """
        Gets the list of targeting addons.

        Args:
            filter_type (str): Name of the type of addons to retrieve. Can be used to easily retrieve unique addons.

        Returns:
            list: A list of TargetingAddons objects.
        """
        if filter_type is None:
            return self.addons
        found_addons = []
        for addon in self.addons:
            class_name = addon.get_class_name()
            if class_name == filter_type:
                found_addons.append(addon)
        return found_addons

    def get_addon_source_setup(self):
        """
        Gets the unique source setup addons from this definition.
        Returns:
            AddonSourceSetup: The unique source setup addon found in this definition.
        """
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons

        addon_name = tools_rt_addons.Addons.AddonSourceSetup.__name__
        return self.get_addons(filter_type=addon_name)[0]

    def get_addon_scene_options(self):
        """
        Gets the unique source setup addons from this definition.
        Returns:
            AddonSceneOptions: The unique scene options addon found in this definition.
        """
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons

        addon_name = tools_rt_addons.Addons.AddonSceneOptions.__name__
        return self.get_addons(filter_type=addon_name)[0]

    def get_addon_post_bake(self):
        """
        Gets the unique post bake addon from this definition.
        Returns:
            AddonPostBake: The unique post bake addon found in this definition.
        """
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons

        addon_name = tools_rt_addons.Addons.AddonPostBake.__name__
        found_addon = self.get_addons(filter_type=addon_name)
        if not found_addon:
            # Instantiate a new one
            self.add_addon(tools_rt_addons.Addons.AddonPostBake())

        return self.get_addons(filter_type=addon_name)[0]

    def get_addon_python_script(self):
        """
        Gets the python script addons from this definition.
        Returns:
            AddonPythonScripts (list): The python script addons list found in this definition.
        """
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons

        addon_name = tools_rt_addons.Addons.AddonPythonScript.__name__
        found_addon = self.get_addons(filter_type=addon_name)
        if not found_addon:
            # Instantiate a new one
            self.add_addon_python_script()

        return self.get_addons(filter_type=addon_name)

    def add_addon_python_script(self, script_name=None):
        """
        Adds the python script addons from this definition.
        Args:
            script_name (str): the name of the new python script
        """
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons

        self.add_addon(tools_rt_addons.Addons.AddonPythonScript(name=script_name))

    def remove_addon_python_script_by_name(self, script_name=None):
        """
        Removes the python script addon with the supplied name from this definition.
        Args:
            script_name (str): the name of the python script addon to remove.
        """
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons

        if not script_name:
            logger.warning("Please provide a name.")
            return

        _addon_script_type = tools_rt_addons.Addons.AddonPythonScript.__name__
        for i, _addon in reversed(list(enumerate(self.addons))):
            _addon_type = _addon.get_class_name()
            if _addon_type == _addon_script_type and _addon.name == script_name:
                del self.addons[i]
                logger.info(f"Removed the Python Script named '{script_name}'")

    def get_addon_patches(self):
        """
        Gets the active patches addons for this definition.
        Returns:
            list: addon patches found in this definition.
        """
        import gt.tools.retargeter.retargeter_patches as tools_rt_patches

        _available_patches_names = tools_rt_patches.Patches.get_patches_dict().keys()
        patches_list = []

        for patch_name in _available_patches_names:
            found_addon = self.get_addons(filter_type=patch_name)
            if found_addon:
                patches_list.append(found_addon[0])

        return patches_list

    def get_definition_as_dict(self):
        """
        Gets definition as a JSON ready dictionary.
        Returns:
            dict: A dictionary describing this definition.
        """
        # Ordered Basic Variables
        definition_as_dict = {
            "uuid": self.get_uuid(),
            "name": self.get_name(),
            "source_path": self.get_source_path(),
            "target_path": self.get_target_path(),
        }

        # Remaining Variables (Auto Serialization)
        for key, value in self.__dict__.items():
            if not key.startswith("_") and key not in definition_as_dict.keys():
                if core_io.is_json_serializable(data=value, allow_none=False):
                    definition_as_dict[key] = value
        # Links
        links_as_dict = []
        for link in self.links:
            links_as_dict.append(link.get_link_as_dict())
        definition_as_dict["links"] = links_as_dict
        # Addons
        addons_as_dict = []
        for addon in self.addons:
            addons_as_dict.append(addon.get_addon_as_dict())
        definition_as_dict["addons"] = addons_as_dict
        return definition_as_dict

    # -------------------------------------------------- Utils --------------------------------------------------
    def add_link(self, link, reject_existing_targets=True):
        """
        Adds a TargetingLink to the list of links.

        Args:
            link (TargetingLink): The link to be added.
            reject_existing_targets (bool, optional): If True it will reject links carrying targets that are
                                                      already present in this definition.
        """
        if reject_existing_targets and link.get_target() in self.get_links_targets():
            logger.warning(
                f"Unable to add link as its target is already present in this definition. Rejected link: {link}"
            )
            return
        self.links.append(link)

    def clear_links(self):
        """
        Clears all links from the list of links.
        """
        self.links = []

    def remove_link(self, link):
        """
        Removes a specific TargetingLink from the list of links.

        Args:
            link (TargetingLink): The link to be removed.

        Returns:
            bool: True if it was removed, False otherwise
        """
        if link in self.links:
            self.links.remove(link)
            return True
        return False

    def get_available_targets(self):
        """Gets the available targets from the definition links.

        Returns:
            list: available targets from the scene
        """
        found_targets = []

        for link in self.links:
            target_name = link.get_target()
            target_path = link.find_target_in_scene()
            if not cmds.objExists(target_path):
                logger.warning(f'Unable to bake missing target object: "{target_name}".')
            found_targets.append(target_path)

        return found_targets

    def remove_flat_animations(self):
        """Deletes static animation channels (flat animations) from the rig controls."""
        links_target = self.get_available_targets()  # rig controls
        if links_target:
            cmds.delete(
                links_target,
                staticChannels=True,
                unitlessAnimationCurves=False,
                hierarchy="none",
                controlPoints=False,
                shape=True,
            )

    def read_links_target_data(self, get_user_defined=True):
        """
        Attempts to find link target objects in the scene and reads their transforms and user-defined data.
        This data is stored inside each link as a variable called "target_data".

        Args:
            get_user_defined (bool, optional): If True, user-defined attributes are included.
        """
        for link in self.links:
            link.read_target_data(get_user_defined=get_user_defined)

    def read_addons_and_links_scene_data(self, get_user_defined=True, exclude_addon=None):
        """
        Iterates through all addons and runs their read scene data function.

        Args:
            get_user_defined (bool, optional): If True, user-defined attributes are included.
            exclude_addon (list or str): one or multiple Addons to ignore
        """
        if not exclude_addon:
            exclude_addon = []
        if exclude_addon:
            if isinstance(exclude_addon, str):
                exclude_addon = [exclude_addon]
        self.read_links_target_data(get_user_defined=get_user_defined)
        for addon in self.addons:
            if addon.name not in exclude_addon:
                addon.read_scene_data()

    def convert_link_fallbacks_to_long(self, targets=True, sources=False):
        """
        Detects links that are relying on fallback operations to locate their elements.
        If this is the case, updates the long path to the correct long path.
        Args:
            targets (bool, optional): If True, operation updates the targets of all links.
            sources (bool, optional): If True, operation updates the sources of all links.
        """
        for link in self.links:
            if targets:
                link.convert_fallback_target_to_long()
            if sources:
                link.convert_fallback_source_to_long()

    def add_addon(self, addon):
        """
        Adds a TargetingLink to the list of links.

        Args:
            addon (TargetingAddon): The link to be added.
        """
        found_addon_types = [addon.get_class_name() for addon in self.get_addons()]

        if not addon.allow_multiple and addon.get_class_name() in found_addon_types:
            logger.warning(
                f"Unable to add addon as multiples of this type are not allowed. "
                f"Rejected addon: {addon.get_class_name()}"
            )
            return
        self.addons.append(addon)

    def apply_addons(self, required_order, ignore_types=None):
        """
        Tries to run any addon that matches the required order.

        Args:
            required_order (str, None): If provided, the code will only run when matching the provided order
                                        according to the CodeData object.
            ignore_types (list, optional): A list of addon types to be ignored.
                                           e.g. [AddonPostBake] will ignore the post bake step.
        """
        # Default to an empty list if no ignore types are provided
        if ignore_types is None:
            ignore_types = []

        for addon in self.addons:
            # Skip this addon if its class/type is in the ignore list
            if type(addon) in ignore_types:
                continue
            addon.apply_addon_ordered(required_order=required_order)

    # ---------------------------------------------- Retarget Steps ----------------------------------------------
    def retarget_import_files(self):
        """
        Imports the source and target files for the retargeting process.
        """
        # Import Target ---------------------------------
        imported_target_nodes = cmds.file(
            self.target_path,
            ignoreVersion=True,
            reference=self.reference_rig,
            namespace=self.target_namespace,
            returnNewNodes=True,
        )
        # Import Source ---------------------------------
        if self.source_path.lower().endswith(".fbx"):  # lower is essential to get both fbx and FBX cases
            if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
                cmds.loadPlugin("fbxmaya")
            import gt.utils.fbx as utils_fbx

            fbx_import = utils_fbx.FbxImporter()
            with fbx_import as fbx:
                fbx.set_preferences_animation()
                imported_source_nodes = fbx.import_file(path=self.source_path, namespace=self.source_namespace)
        else:
            imported_source_nodes = cmds.file(
                self.source_path,
                i=True,
                namespace=self.source_namespace,
                ignoreVersion=True,
                importTimeRange="override",
                returnNewNodes=True,
            )
        # Store Imported Nodes
        self._cached_imported_target_nodes = [core_node.Node(obj) for obj in imported_target_nodes]
        self._cached_imported_source_nodes = [core_node.Node(obj) for obj in imported_source_nodes]

        # force source namespace - source file could have double namespaces --------------------
        if not cmds.namespace(ex=self.source_namespace):
            cmds.namespace(add=self.source_namespace)
            cmds.namespace(set=":")
        for node in self._cached_imported_source_nodes:
            short_name = str(node).split("|")[-1]
            short_name_namespace = core_nspace.get_namespace(short_name)
            short_name_without_namespace = core_naming.get_short_name(str(node), remove_namespace=True)
            if short_name_namespace != self.source_namespace:
                node.rename(f"{self.source_namespace}:{short_name_without_namespace}")

    def retarget_refresh_links_data(self):
        """Populates links with shared preferences such as namespaces and fallback methods"""
        for link in self.links:
            link.set_source_namespace(self.source_namespace)
            link.set_target_namespace(self.target_namespace)
            link.set_short_name_fallback_state(self.short_name_fallback)

    def retarget_refresh_addons_data(self):
        """Populates addons with shared preferences such as namespaces and fallback methods"""
        for addon in self.addons:
            addon.set_source_path(self.source_path)
            addon.set_target_path(self.target_path)
            addon.set_source_namespace(self.source_namespace)
            addon.set_target_namespace(self.target_namespace)
            addon.set_short_name_fallback_state(self.short_name_fallback)
            addon.set_cached_imported_source_nodes(self._cached_imported_source_nodes)
            addon.set_cached_imported_target_nodes(self._cached_imported_target_nodes)

    def retarget_apply_link_attr_data(self):
        """Applies any attribute data stored in a link (source and target"""
        for link in self.links:
            link.apply_target_data()

    def retarget_create_links(self):
        """
        Creates the targeting links between the source and target objects based on the defined links.
        Stores link returned objects in "self._cached_link_objects". e.g. constraint transforms.
        """
        for link in self.links:
            link_objects = link.create_link()
            # Cache Link Objects (Constraints in Most Cases)
            if link_objects and isinstance(link_objects, list):
                self._cached_link_objects.extend(link_objects)

    def retarget_bake_animation(self):
        """Bake constraint targets"""
        found_targets = self.get_available_targets()

        if not found_targets:
            logger.warning(f"No target objects were found. Bake operation was skipped.")
            return

        # Suspend refresh
        cmds.refresh(suspend=True)

        start_frame = cmds.playbackOptions(query=True, minTime=True)
        end_frame = cmds.playbackOptions(query=True, maxTime=True)
        cmds.bakeResults(
            found_targets,
            simulation=True,
            t=(start_frame, end_frame + 1),
            sampleBy=1,
            oversamplingRate=1,
            disableImplicitControl=True,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=True,
            removeBakedAttributeFromLayer=False,
            removeBakedAnimFromLayer=False,
            bakeOnOverrideLayer=False,
            minimizeRotation=True,
            controlPoints=False,
            shape=True,
        )

        # Re-enable refresh
        cmds.refresh(suspend=False)

    def retarget_cleanup(self):
        """Cleanup step. Depending on settings it deletes the source and other elements in the scene."""
        _cached_link_objects = core_iter.sanitize_maya_list(
            input_list=self._cached_link_objects,
            filter_existing=True,
            convert_to_nodes=False,
        )
        cmds.delete(_cached_link_objects)
        if self.delete_source:
            self.get_addon_source_setup().delete_source()
        if self.delete_static_channels:
            self.remove_flat_animations()

    def set_xsens_proportions(self):
        """Sets the skeleton leg proportions from the source xsens animation."""
        xsens_ref_namespace = "temp_xsens_source"
        source_offset_scale = cmds.getAttr(f"{self.source_namespace}:offset.sx")

        # Get the legs translation values from the source animation
        hips_y = cmds.getAttr(f"{self.source_namespace}:Hips.ty")
        cmds.file(self.source_path, reference=True, namespace=xsens_ref_namespace)
        r_upperleg_tx = cmds.getAttr(f"{xsens_ref_namespace}:RightUpLeg.tx") / source_offset_scale
        r_lowerleg_ty = cmds.getAttr(f"{xsens_ref_namespace}:RightLeg.ty") / source_offset_scale
        r_foot_ty = cmds.getAttr(f"{xsens_ref_namespace}:RightFoot.ty") / source_offset_scale
        l_upperleg_tx = -r_upperleg_tx
        l_lowerleg_ty = r_lowerleg_ty
        l_foot_ty = r_foot_ty
        cmds.file(self.source_path, removeReference=True)

        # Set leg proportion values
        prev_lowerleg_ty = cmds.getAttr(f"{self.source_namespace}:RightLeg.ty")
        prev_foot_ty = cmds.getAttr(f"{self.source_namespace}:RightFoot.ty")
        cmds.setAttr(f"{self.source_namespace}:RightUpLeg.tx", r_upperleg_tx)
        cmds.setAttr(f"{self.source_namespace}:RightLeg.ty", r_lowerleg_ty)
        cmds.setAttr(f"{self.source_namespace}:RightFoot.ty", r_foot_ty)
        cmds.setAttr(f"{self.source_namespace}:LeftUpLeg.tx", l_upperleg_tx)
        cmds.setAttr(f"{self.source_namespace}:LeftLeg.ty", l_lowerleg_ty)
        cmds.setAttr(f"{self.source_namespace}:LeftFoot.ty", l_foot_ty)

        # Restore Initial Hips
        cmds.setAttr(f"{self.source_namespace}:Hips.ty", hips_y)

        # Adjust the height based on the new leg length
        prev_leg_length = prev_lowerleg_ty + prev_foot_ty
        xsens_anim_leg_length = r_lowerleg_ty + r_foot_ty
        length_diff = -((xsens_anim_leg_length - prev_leg_length) / source_offset_scale)
        prev_offset_ty = cmds.getAttr(f"{self.source_namespace}:offset.ty")
        new_ty_value = prev_offset_ty + length_diff
        cmds.setAttr(f"{self.source_namespace}:offset.ty", new_ty_value)

    # ---------------------------------------------- Retarget Main ----------------------------------------------
    def retarget_edit_mode(self, linked_mode=False):
        """
        Function used to edit retarget elements in the scene.
        Args:
        linked_mode (bool, optional): Whether to apply linked retargeting (e.g., linking
                                      source and target elements). Defaults to False.
        """
        # Create Must Have Addons
        import gt.tools.retargeter.retargeter_addons as tools_rt_addons  # Here to avoid circular import
        import gt.tools.retargeter.retargeter_patches as tools_rt_patches

        addons_to_ignore = [tools_rt_addons.Addons.AddonPostBake, tools_rt_addons.Addons.AddonPythonScript]
        _addons_patches_dict = tools_rt_patches.Patches.get_patches_dict()
        if _addons_patches_dict:
            addons_to_ignore.extend(list(_addons_patches_dict.values()))

        cmds.file(new=True, force=True)
        self.retarget_refresh_addons_data()  # Give namespaces to addons
        self.apply_addons(required_order=TargetingAddon.Order.pre_retarget, ignore_types=addons_to_ignore)
        self.retarget_import_files()
        self.retarget_refresh_addons_data()  # Give Cached objects to Addons
        self.apply_addons(required_order=TargetingAddon.Order.post_import, ignore_types=addons_to_ignore)
        self.retarget_refresh_links_data()  # Gives namespaces and other data to links
        self.retarget_apply_link_attr_data()  # Import Pose and Initial values
        self.apply_addons(required_order=TargetingAddon.Order.pre_create_links, ignore_types=addons_to_ignore)
        if linked_mode:  # Create links and apply addons
            self.retarget_create_links()
            self.apply_addons(required_order=TargetingAddon.Order.post_bake, ignore_types=addons_to_ignore)
            self.apply_addons(required_order=TargetingAddon.Order.post_retarget, ignore_types=addons_to_ignore)
            cmds.currentTime(1, edit=True)  # Set Timeline Frame to 1
            cmds.select(clear=True)

    def retarget(self, verbose=False, callbacks=None):
        """
        Main function used to retarget from source to target
        Args:
            verbose (bool, optional): If True, the retargeting operation will print feedback after each step.
            callbacks (list, callable, optional): A list of callable functions that will be called with the
                                                  feedback of the retarget process as their first argument.
                                                  e.g. If I provide [my_func], then the script will call
                                                  my_func("Retargeting...") and so on as it goes through the operation.
        """
        cmds.file(new=True, force=True)

        # Handling the auto-key - store the status, disable during the retarget and apply back at the end.
        _autokey_state = cmds.autoKeyframe(state=True, query=True)
        # -- force autokey to off
        if _autokey_state:
            cmds.autoKeyframe(state=False)

        self.retarget_refresh_addons_data()  # Gives namespaces and other data to addons
        self.apply_addons(required_order=TargetingAddon.Order.pre_retarget)
        core_fback.print_when_true(input_string="Importing Files.", do_print=verbose, callbacks=callbacks)
        self.retarget_import_files()
        self.retarget_refresh_addons_data()  # Give Cached objects to Addons
        self.apply_addons(required_order=TargetingAddon.Order.post_import)
        self.retarget_refresh_links_data()  # Gives namespaces and other data to links
        self.retarget_apply_link_attr_data()  # Import Pose and Initial values
        self.apply_addons(required_order=TargetingAddon.Order.pre_create_links)
        core_fback.print_when_true(input_string="Linking Source to Target.", do_print=verbose, callbacks=callbacks)
        self.retarget_create_links()
        core_fback.print_when_true(input_string="Baking Animation.", do_print=verbose, callbacks=callbacks)
        self.retarget_bake_animation()
        core_fback.print_when_true(input_string="Running post processing.", do_print=verbose, callbacks=callbacks)
        self.apply_addons(required_order=TargetingAddon.Order.post_bake)
        self.apply_addons(required_order=TargetingAddon.Order.post_retarget)
        core_fback.print_when_true(input_string="Configuring Scene.", do_print=verbose, callbacks=callbacks)
        self.retarget_cleanup()
        self.get_addon_source_setup().set_retargeted_status(True)  # Change status to retargeted
        cmds.select(clear=True)

        # -- Set back the autokey
        if _autokey_state:
            cmds.autoKeyframe(state=True)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    cmds.file(new=True, force=True)

    # Get Test Files -------------------------------------------------------------------------------
    import gt.tests.test_retargeter as test_retargeter
    import inspect
    import os

    # Reset Scene and Create Test Paths ------------------------------------------------------------
    cmds.file(new=True, force=True)
    module_path = inspect.getfile(test_retargeter)
    module_dir = os.path.dirname(module_path)
    data_dir = os.path.join(module_dir, "data")
    cylinder_rig = os.path.join(data_dir, "cylinder_rig.mb")

    # Test A: Same starting pose, moves, rotates
    cylinder_anim_a_mb = os.path.join(data_dir, "cylinder_anim_a.mb")
    cylinder_anim_a_fbx = os.path.join(data_dir, "cylinder_anim_a.fbx")
    # Test B: Different starting position, moves, rotates
    cylinder_anim_b_mb = os.path.join(data_dir, "cylinder_anim_b.mb")
    cylinder_anim_b_fbx = os.path.join(data_dir, "cylinder_anim_b.fbx")
    # Test C: Different starting position and rotation, moves, rotates
    cylinder_anim_c_mb = os.path.join(data_dir, "cylinder_anim_c.mb")
    cylinder_anim_c_fbx = os.path.join(data_dir, "cylinder_anim_c.fbx")
    # Test D: Different starting scale (smaller) - moves, rotates
    cylinder_anim_d_mb = os.path.join(data_dir, "cylinder_anim_d.mb")
    cylinder_anim_d_fbx = os.path.join(data_dir, "cylinder_anim_d.fbx")

    # Create Definition and Links ------------------------------------------------------------------
    a_definition = RetargeterDefinition()
    a_definition.source_path = cylinder_anim_d_fbx
    a_definition.target_path = cylinder_rig

    # Create Links
    link_a = TargetingLink(source="base_jnt", target="base_ctrl", method=TargetingMethods.offset)  # Green
    link_b = TargetingLink(source="mid_jnt", target="|mid_ctrl", method=TargetingMethods.offset)  # Yellow

    # Add links
    a_definition.add_link(link=link_a)
    a_definition.add_link(link=link_b)

    # # Add invalid link for testing
    # link_c = TargetingLink(source="mid_jnt", target="mocked_ctrl", method=TargetingMethods.absolute)
    # a_definition.add_link(link=link_c)

    # Modify Addon
    source_setup = a_definition.get_addon_source_setup()
    source_offset_data = {"sx": 5, "sy": 5, "sz": 5}
    source_setup.set_transform_data(source_offset_data)

    # Re-create Definition from dict ---------------------------------------------------------------
    a_definition.set_delete_source_status(True)  # Delete Source After Baking
    a_definition_as_dict = a_definition.get_definition_as_dict()

    a_2nd_definition = RetargeterDefinition()
    a_2nd_definition.read_data_from_dict(a_definition_as_dict)

    # Enter Edit Mode to Update Transform Data
    a_2nd_definition.retarget_edit_mode()
    a_2nd_definition.read_links_target_data()
    a_2nd_definition_as_dict = a_2nd_definition.get_definition_as_dict()

    # Retarget
    cmds.file(new=True, force=True)
    # a_definition.retarget_edit_mode()
    a_definition.retarget()
    # a_2nd_definition.retarget()

    # JSON Output Test
    desktop_path = os.path.join(os.path.expanduser(os.getenv("USERPROFILE")), "Desktop")
    test_json_path = os.path.join(desktop_path, r"retarget_definition.json")
    core_io.write_json(path=test_json_path, data=a_2nd_definition_as_dict)

    # Try to re-crete it from JSON file
    cmds.file(new=True, force=True)
    a_definition_dict = core_io.read_json_dict(path=test_json_path)
    a_clean_definition = RetargeterDefinition()
    a_clean_definition.read_data_from_dict(a_definition_dict)
    a_clean_definition.retarget()
