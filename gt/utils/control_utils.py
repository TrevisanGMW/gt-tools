"""
Control Utilities (a.k.a. Complex Curves)
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.data.controls import cluster_driven
from gt.utils.curve_utils import Curve
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Control(Curve):
    def __init__(self, name=None, build_function=None):
        """
        Initializes a Control (Curve) object. Essentially a complex Curve with extra logic and elements.
        Args:
            name (str, optional): Control transform name (shapes names are determined by the Callable function)
        """
        super().__init__(name=name)  # Call the parent class constructor
        self.build_function = None
        self.set_build_function(build_function=build_function)
        self.last_callable_output = None

    def set_build_function(self, build_function):
        """
        Sets the build function for this complex curve
        Args:
            build_function (callable): A function used to build the curve
        """
        if callable(build_function):
            self.build_function = build_function

    def build(self, *args, **kwargs):
        """
        Use the provided callable function to generate/create a Maya curve.
        Also renames the generated curve using the string stored in "self.name"
        If a list is returned from the "self.build_function" the parent transform is assumed to be the first object.
        e.g. ["parent_transform", "curve_shape", "something_else"] = Returns "parent_transform"
        Args:
            args (any): Arguments to give the complex curve callable object.
            kwargs (any): Keyword arguments to give the complex curve callable object.
        Returns:
            str or Any: Name of the transform of the newly generated curve. (Result of the callable function)
                        "None" if curve is invalid (does not have a callable function)
                        Any if "return_callable_output" is active.
        """
        if not self.is_curve_valid():
            logger.warning("Control object is missing a callable function.")
            return
        try:
            callable_result = self.build_function(*args, **kwargs)
            self.last_callable_output = callable_result
        except Exception as e:
            logger.warning(f'Unable to build complex curve. Build function raised an error: {e}')
            raise e
            return
        parent_transform = None
        if isinstance(callable_result, list) and len(callable_result) > 0:
            parent_transform = callable_result[0]
        elif isinstance(callable_result, str):
            parent_transform = callable_result
        if self.name and parent_transform:
            parent_transform = cmds.rename(parent_transform, self.name)
        return parent_transform

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


class Controls:
    def __init__(self):
        """
        A library of controls (complex curves) objects. These are created using a callable function.
        Use "build()" to create them in Maya.
        """
    scalable_arrow = Control(build_function=cluster_driven.create_scalable_arrow)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = Controls.scalable_arrow
    out.build()
    out = None
