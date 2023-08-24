"""
Control Utilities (a.k.a. Complex Curves)
github.com/TrevisanGMW/gt-tools

Dependencies: "gt.utils.curve_utils" and "gt.utils.data.controls"
"""
from gt.utils.data.controls import cluster_driven, slider
from gt.utils.attr_utils import set_attr, set_attr_state
from gt.utils.naming_utils import get_short_name
from gt.utils.data_utils import DataDirConstants
from gt.utils.curve_utils import Curve
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
                                  If provided at the same time as the "build_function" it will take priority.
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
        if not iterable_utils.compare_identical_dict_values_types(self.parameters, self._original_parameters):
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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # out = Controls.scalable_two_sides_arrow
    # out.build()
    add_snapping_shape('pSphere1')

