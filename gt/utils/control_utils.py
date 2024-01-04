"""
Control Utilities (a.k.a. Complex Curves)
github.com/TrevisanGMW/gt-tools

Dependencies: "gt.utils.curve_utils" and "gt.utils.data.controls"
"""
from gt.utils.color_utils import set_color_viewport, get_directional_color
from gt.utils.attr_utils import set_attr, set_attr_state, rescale
from gt.utils.naming_utils import NamingConstants, get_short_name
from gt.utils.data.controls import cluster_driven, slider
from gt.utils.iterable_utils import sanitize_maya_list
from gt.utils.transform_utils import match_transform
from gt.utils.data_utils import DataDirConstants
from gt.utils.curve_utils import Curve
from gt.utils.node_utils import Node
from gt.utils import iterable_utils
from gt.utils import system_utils
import maya.cmds as cmds
import logging
import ast
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def add_snapping_shape(target_object):
    """
    Parents a locator shape to the target object so objects can be snapped to it.
    The parented locator shape has a scale of 0, so it doesn't change the look of the target object.
    Args:
        target_object (str): Name of the object to add the locator shape.
    Returns:
        str or None: Name of the added invisible locator shape or None in case it fails.
    """
    if not target_object or not cmds.objExists(target_object):
        logger.debug(f'Unable to add snapping shape. Missing target object "{target_object}".')
        return
    # See if it already exists
    snapping_shape = "snappingPoint"
    target_shapes = cmds.listRelatives(target_object, shapes=True, fullPath=True) or []
    for shape in target_shapes:
        if get_short_name(shape) == f'{snapping_shape}Shape':
            logger.debug(f'Unable to add snapping shape. Missing target already has a shape named "{snapping_shape}".')
            return
    selection = cmds.ls(selection=True) or []
    locator = cmds.spaceLocator(name="snappingPoint")[0]
    locator_shape = cmds.listRelatives(locator, shapes=True, fullPath=True) or []
    if len(locator_shape) != 1:
        locator_shape = locator_shape[0]
    set_attr(obj_list=locator_shape, attr_list=["localScaleX", "localScaleY", "localScaleZ"], value=0)
    set_attr_state(obj_list=locator_shape, attr_list=["lpx", "lpy", "lpz", "lsx", "lsy", "lsz"], hidden=True)
    cmds.parent(locator_shape, target_object, relative=True, shape=True)
    cmds.delete(locator)
    if selection:
        try:
            cmds.select(clear=True)
            cmds.select(selection)
        except Exception as e:
            logger.debug(f'Unable to retrieve previous selection. Issue: "{e}".')
    target_shapes = cmds.listRelatives(target_object, shapes=True, fullPath=True) or []
    return target_shapes[-1]


def get_control_preview_image_path(control_name):
    """
    Get the path to a curve data file. This file should exist inside the utils/data/curves folder.
    Args:
        control_name (str): Name of the curve (same as curve file). It doesn't need to contain extension.
                          Function will automatically look for JPG or PNG files.
    Returns:
        str or None: Path to the curve preview image file. None if not found.
    """
    if not isinstance(control_name, str):
        logger.debug(f'Unable to retrieve control preview image. Incorrect argument type: "{str(type(control_name))}".')
        return

    for ext in ["jpg", "png"]:
        path_to_image = os.path.join(DataDirConstants.DIR_CONTROLS, "preview_images", f'{control_name}.{ext}')
        if os.path.exists(path_to_image):
            return path_to_image


class Control(Curve):
    def __init__(self, name=None, build_function=None):
        """
        Initializes a Control (Curve) object. Essentially a complex Curve with extra logic and elements.
        Args:
            name (str, optional): Control transform name (shapes names are determined by the Callable function)
                                  If not provided, it will attempt to extract it from the arguments of the build
                                  function. If it's also not found there, it will be None.
                                  If provided at the same time as the "build_function" name arg will take priority.
                                  Priority order: 1: name, 2: build_function keyword argument.
            build_function (callable): function used to build the curve.
        """
        super().__init__()  # Call the parent class constructor
        self._original_parameters = {}
        self.parameters = {}
        self.build_function = None
        self.set_build_function(build_function=build_function)
        self.last_callable_output = None
        if name:
            self.set_name(name=name)

    def _set_original_parameters(self, parameters):
        """
        Sets the original control parameters (a copy to be compared for validation)
        Args:
            parameters (dict, str): A dictionary with the keyword arguments of the control.
                                    It can also be a JSON formatted string.
        """
        if parameters and isinstance(parameters, dict):
            self._original_parameters = parameters

    def reset_parameters(self):
        """ Resets parameters to the original value """
        self.parameters = self._original_parameters

    def set_parameters(self, parameters):
        """
        Sets the control parameters
        Args:
            parameters (dict, str): A dictionary with the keyword arguments of the control.
                                        It can also be a JSON formatted string.
        """
        if parameters and isinstance(parameters, dict):
            self.parameters = parameters
        if parameters and isinstance(parameters, str):
            try:
                _parameters = ast.literal_eval(parameters)
                self.parameters = _parameters
            except Exception as e:
                logger.warning(f'Unable to set control parameters. Invalid dictionary. Issue: {str(e)}')

    def get_parameters(self):
        """
        Gets the control parameters
        Returns:
            dict: Parameters used to create the control
        """
        return self.parameters

    def get_docstrings(self, strip=True, strip_new_lines=True):
        """
        Returns the docstrings from the build function.
        Args:
            strip (bool, optional): If True, leading empty space will be removed from each line of the docstring.
            strip_new_lines (bool, optional): If True, it will remove new lines from start and end.
        Returns:
            str or None: Docstring of the build function.
                         None in case no function was set or function doesn't have a docstring
        """
        if not self.build_function:
            logger.debug(f'Build function was not yet set. Returning None as docstrings.')
            return
        return system_utils.get_docstring(func=self.build_function, strip=strip, strip_new_lines=strip_new_lines)

    def validate_parameters(self):
        """
        Validates parameters before building curve
        If parameters have new keys or different value types, the validation fails.
        Returns:
            bool: True if valid, False if invalid
        """
        if not iterable_utils.compare_identical_dict_keys(self.parameters, self._original_parameters):
            logger.debug(f"Invalid parameters, new unrecognized keys were added.")
            return False
        if not iterable_utils.compare_identical_dict_values_types(self.parameters,
                                                                  self._original_parameters,
                                                                  allow_none=True):
            logger.debug(f"Invalid parameters, values were assign new types.")
            return False
        return True

    def set_build_function(self, build_function):
        """
        Sets the build function for this complex curve
        Args:
            build_function (callable): A function used to build the curve
        """
        if callable(build_function):
            self.build_function = build_function
            try:
                _args, _kwargs = system_utils.get_function_arguments(build_function, kwargs_as_dict=True)
                if _kwargs and len(_kwargs) > 0:
                    self.set_parameters(_kwargs)
                    self._set_original_parameters(_kwargs)
                    self.extract_name_from_parameters()
            except Exception as e:
                logger.debug(f'Unable to extract parameters from build function. Issue: {str(e)}')

    def build(self):
        """
        Use the provided callable function to generate/create a Maya curve.
        Returns:
            str or Any: Name of the transform of the newly generated curve. (Result of the callable function)
                       "None" if curve is invalid (does not have a callable function)
        """
        if not self.is_curve_valid():
            logger.warning("Control object is missing a callable function.")
            return
        try:
            if self.validate_parameters():
                callable_result = self.build_function(**self.parameters)
            else:
                callable_result = self.build_function(**self._original_parameters)
                logger.warning(f'Invalid custom parameters. Original parameters were used instead. '
                               f'Original: {self._original_parameters}')
            self.last_callable_output = callable_result
            return callable_result
        except Exception as e:
            logger.warning(f'Unable to build control. Build function raised an error: {e}')

    def is_curve_valid(self):
        """
        Checks if the Curve object has enough data to create/generate a curve.
        Returns:
            bool: True if it's valid (can create a curve), False if invalid.
                  In this case it's valid if it has a callable function.
        """
        if self.build_function is not None:
            return True
        return False

    def get_last_callable_output(self):
        """
        Returns the last output received from the build call
        Returns:
            any: Anything received as the last output from the callable function. If it was never called, it is None.
        """
        return self.last_callable_output

    def set_name(self, name):
        """
        Sets a new Curve name (Control in this case).
        This function is an overwriting the original function for Controls.
        Used to also update the parameter "name" in case it exists.

        Args:
            name (str): New name to use on the curve/control. (Also used in the control parameter)
        """
        if name and isinstance(name, str) and "name" in self.get_parameters():
            self.parameters["name"] = name
        super().set_name(name)

    def extract_name_from_parameters(self):
        """
        Checks to see if the keyword "name" exists in the parameters' dictionary.
        If it does, overwrite the control name with it.
        """
        parameters = self.get_parameters()
        if "name" in parameters:
            param_name = parameters.get("name")
            if param_name:
                self.set_name(param_name)


class Controls:
    def __init__(self):
        """
        A library of controls (complex curves) objects. These are created using a callable function.
        Use "build()" to create them in Maya.
        """
    scalable_one_side_arrow = Control(build_function=cluster_driven.create_scalable_one_side_arrow)
    scalable_two_sides_arrow = Control(build_function=cluster_driven.create_scalable_two_sides_arrow)
    slider_squared_one_dimension = Control(name="slider_squared_one_dimension",
                                           build_function=slider.create_slider_squared_one_dimension)
    slider_squared_two_dimensions = Control(name="slider_squared_two_dimensions",
                                            build_function=slider.create_slider_squared_two_dimensions)
    sliders_squared_mouth = Control(name="sliders_squared_mouth", build_function=slider.create_sliders_squared_mouth)
    sliders_squared_eyebrows = Control(name="sliders_squared_eyebrows",
                                       build_function=slider.create_sliders_squared_eyebrows)
    sliders_squared_cheek_nose = Control(name="sliders_squared_cheek_nose",
                                         build_function=slider.create_sliders_squared_cheek_nose)
    sliders_squared_eyes = Control(name="sliders_squared_eyes",
                                   build_function=slider.create_sliders_squared_eyes)
    sliders_squared_facial_side_gui = Control(name="sliders_squared_facial_side_gui",
                                              build_function=slider.create_sliders_squared_facial_side_gui)


def create_fk(target_list,
              curve_shape=None,
              scale_multiplier=1,
              colorize=True,
              constraint_joint=True,
              mimic_joint_hierarchy=True,
              filter_type="joint",
              filter_string=f"_{NamingConstants.Suffix.END}",
              suffix_ctrl=f"_{NamingConstants.Suffix.CTRL}",
              suffix_offset=f"_{NamingConstants.Suffix.OFFSET}",
              suffix_joint=f"_{NamingConstants.Suffix.JNT}",
              ):
    """
    Creates FK controls for the given joint list.

    Args:
        target_list (str or list): The list of targets (usually joints) or a single target as a string.
                                   When using a type,
        curve_shape (Curve or None): The curve shape to use for the control, if None, a default circle curve is used.
        scale_multiplier (float): The scale multiplier for the control.
        colorize (bool): Flag to enable colorizing the control based on directional color. (X+ or X-)
        constraint_joint (bool): Flag to enable constraint the joint to the control using a parent constraint.
        mimic_joint_hierarchy (bool): Flag to enable automatically parenting new controls to mimic joint hierarchy.
        filter_type (str, optional): A string describing the accepted type. (e.g. "joint")
        filter_string (str, optional): The filter string to apply when sanitizing the joint list. (e.g. "_end")
        suffix_ctrl (str, optional): The suffix for the control's name. (e.g. "_ctrl")
        suffix_offset (str, optional): The suffix for the offset group's name. (e.g. "_grp")
        suffix_joint (str, optional): The suffix for the joint's name. (e.g. "_jnt")

    Returns:
        list: A list of created FK controls.
    """
    if isinstance(target_list, str):
        target_list = [target_list]
    if not target_list:
        return

    stored_selection = cmds.ls(selection=True) or []

    # Sanitize Input List
    filtered_list = sanitize_maya_list(input_list=target_list,
                                       filter_existing=True,
                                       convert_to_nodes=True,
                                       filter_type=filter_type,
                                       filter_string=filter_string,
                                       filter_unique=True,
                                       sort_list=True)
    fk_controls = []
    for jnt in filtered_list:
        if len(suffix_joint) != 0:
            joint_name = get_short_name(jnt).replace(suffix_joint, '')
        else:
            joint_name = get_short_name(jnt)
        ctrl_name = joint_name + suffix_ctrl
        ctrl_grp_name = joint_name + suffix_offset

        if curve_shape is not None and isinstance(curve_shape, Curve):
            ctrl = curve_shape.build()
            ctrl = Node(ctrl)
            ctrl.rename(ctrl_name)
            rescale(obj=ctrl, scale=scale_multiplier)
        else:
            ctrl = cmds.circle(name=ctrl_name,
                               normal=[1, 0, 0],
                               radius=scale_multiplier,
                               ch=False)[0]  # Default Circle Curve
            ctrl = Node(ctrl)

        fk_controls.append(ctrl)
        offset = Node(cmds.group(name=ctrl_grp_name, empty=True))
        cmds.parent(ctrl.get_long_name(), offset.get_long_name())
        match_transform(source=jnt, target_list=offset)

        # Colorize Control ------------------------------------------------------
        if colorize:
            color = get_directional_color(jnt)
            if isinstance(color, tuple) and len(color) == 3:
                set_color_viewport(ctrl.get_long_name(), rgb_color=color)

        # Constraint Joint ------------------------------------------------------
        if constraint_joint:
            cmds.parentConstraint(ctrl_name, jnt)

        # Mimic Hierarchy -------------------------------------------------------
        if mimic_joint_hierarchy:
            try:
                # Auto parents new controls
                jnt_parent = cmds.listRelatives(jnt, allParents=True) or []
                if jnt_parent:
                    if suffix_joint and isinstance(suffix_joint, str):
                        parent_ctrl = (jnt_parent[0].replace(suffix_joint, "") + suffix_ctrl)
                    else:
                        parent_ctrl = (jnt_parent[0] + suffix_ctrl)
                    if cmds.objExists(parent_ctrl):
                        cmds.parent(offset, parent_ctrl)
            except Exception as e:
                logger.debug(f'Unable to mimic hierarchy. Issue: {e}')
    cmds.select(clear=True)
    if stored_selection:
        try:
            cmds.select(stored_selection)
        except Exception as e:
            logger.debug(f'Unable to retrieve previous selection. Issue: {e}')
    return fk_controls


def selected_create_fk():
    """
    Creates FK controls for the selected joints.
    Returns:
        list: A list of created FK controls.
    Raises:
        Warning: If an error occurs during the process.
    """
    undo_chunk_name = "Create FK Controls"
    cmds.undoInfo(openChunk=True, chunkName=undo_chunk_name)
    try:
        selection = cmds.ls(selection=True, typ="joint") or []
        return create_fk(target_list=selection)
    except Exception as e:
        logger.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=undo_chunk_name)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from gt.utils.scene_utils import force_reload_file

    force_reload_file()

    a_list = ['|joint1', '|joint1|joint2', '|joint1|joint2|joint3',
              '|joint1|joint2|joint3|joint4', 'joint1', 'joint1',
              'joint1', 'joint1', 'joint1', None, 2, 'abc_end']
    from gt.utils.curve_utils import Curves
    create_fk(target_list=a_list, curve_shape=Curves.primitive_cube, scale_multiplier=.5)
