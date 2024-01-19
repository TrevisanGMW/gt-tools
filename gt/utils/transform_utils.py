"""
Transform Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import set_trs_attr, get_multiple_attr, set_attr
from gt.utils.constraint_utils import equidistant_constraints
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.math_utils import matrix_mult
import maya.cmds as cmds
import logging
import sys


# Logging Setup

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Vector3:
    """
    Represents a 3D vector with x, y, and z coordinates.
    """

    def __init__(self, x=0.0, y=0.0, z=0.0, xyz=None):
        """
        Initialize a Vector3 object using x, y, z coordinates

        Args:
            x (float, optional): X coordinate. Defaults to 0.0 if not provided.
            y (float, optional): Y coordinate. Defaults to 0.0 if not provided.
            z (float, optional): Z coordinate. Defaults to 0.0 if not provided.
            xyz (list or tuple, optional): List or tuple containing x, y, z coordinates.
                                           If provided, it overrides x, y, z parameters.
                                           Defaults to None.

        Raises:
            ValueError: If coordinates are not valid or provided in an incorrect format.
        """
        if xyz is not None:
            self.set_from_tuple(xyz)
        else:
            for num in [x, y, z]:
                if not isinstance(num, (int, float)):
                    raise ValueError("Input values must be numbers")
            self.x = x
            self.y = y
            self.z = z

    def __repr__(self):
        """
        Return a formatted string representation of the Vector3 object.

        Returns:
            str: A string representation of the vector in the format "x=value, y=value, z=value".
        """
        return f"(x={self.x}, y={self.y}, z={self.z})"

    def __eq__(self, other):
        """
        Compare Vector3 objects for equality.

        Args:
            other (Vector3): Object to compare.

        Returns:
            bool: True if the two Vector3 objects are equal, False otherwise.
        """
        if isinstance(other, self.__class__):
            return (
                    self.x == other.x and
                    self.y == other.y and
                    self.z == other.z
            )
        return False

    def __lt__(self, other):
        """
        Compare Vector3 objects using the less than operator.

        Args:
            other (Vector3): Object to compare.

        Returns:
            bool: True if self is less than other, False otherwise.
        """
        if isinstance(other, self.__class__):
            return self.magnitude() < other.magnitude()
        raise TypeError("Unsupported operand type for <")

    def __le__(self, other):
        """
        Compare Vector3 objects using the less than or equal to operator.

        Args:
            other (Vector3): Object to compare.

        Returns:
            bool: True if self is less than or equal to other, False otherwise.
        """
        if isinstance(other, self.__class__):
            return self.magnitude() <= other.magnitude()
        raise TypeError("Unsupported operand type for <=")

    def __gt__(self, other):
        """
        Compare Vector3 objects using the greater than operator.

        Args:
            other (Vector3): Object to compare.

        Returns:
            bool: True if self is greater than other, False otherwise.
        """
        if isinstance(other, self.__class__):
            return self.magnitude() > other.magnitude()
        raise TypeError("Unsupported operand type for >")

    def __ge__(self, other):
        """
        Compare Vector3 objects using the greater than or equal to operator.

        Args:
            other (Vector3): Object to compare.

        Returns:
            bool: True if self is greater than or equal to other, False otherwise.
        """
        if isinstance(other, self.__class__):
            return self.magnitude() >= other.magnitude()
        raise TypeError("Unsupported operand type for >=")

    def __add__(self, other):
        """
        Add two Vector3 objects element-wise. If None, operation is ignored.

        Args:
            other (Vector3): The other Vector3 object to add.

        Returns:
            Vector3: A new Vector3 object representing the sum of the two vectors.

        Raises:
            TypeError: If the operand type for addition is not supported.
        """
        if other is None:
            return self
        if not isinstance(other, self.__class__):
            raise TypeError("Unsupported operand type for +")
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        """
        Subtract two Vector3 objects element-wise.

        Args:
            other (Vector3): The other Vector3 object to subtract.

        Returns:
            Vector3: A new Vector3 object representing the difference of the two vectors.

        Raises:
            TypeError: If the operand type for subtraction is not supported.
        """
        if isinstance(other, self.__class__):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, scalar):
        """
        Multiply the Vector3 object by a scalar.

        Args:
            scalar (int or float): The scalar value to multiply the vector by.

        Returns:
            Vector3: A new Vector3 object representing the scaled vector.

        Raises:
            TypeError: If the operand type for multiplication is not supported.
        """
        if isinstance(scalar, (int, float)):
            return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
        raise TypeError("Unsupported operand type for *")

    def magnitude(self):
        """
        Calculate the magnitude (length) of the Vector3 object.

        Returns:
            float: The magnitude of the vector.
        """
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def dot(self, other):
        """
        Calculate the dot product of two Vector3 objects.

        Args:
            other (Vector3): The other Vector3 object for the dot product.

        Returns:
            float: The dot product of the two vectors.

        Raises:
            TypeError: If the operand type for dot product calculation is not supported.
        """
        if isinstance(other, self.__class__):
            return self.x * other.x + self.y * other.y + self.z * other.z
        raise TypeError("Unsupported operand type for dot product")

    def cross(self, other):
        """
        Calculate the cross product of two Vector3 objects.

        Args:
            other (Vector3): The other Vector3 object for the cross product.

        Returns:
            Vector3: A new Vector3 object representing the cross product of the two vectors.

        Raises:
            TypeError: If the operand type for cross product calculation is not supported.
        """
        if isinstance(other, self.__class__):
            return Vector3(
                self.y * other.z - self.z * other.y,
                self.z * other.x - self.x * other.z,
                self.x * other.y - self.y * other.x
            )
        raise TypeError("Unsupported operand type for cross product")

    def get_as_tuple(self):
        """
        Convert the Vector3 object to a list.

        Returns:
            tuple: A list containing x, y, z coordinates from the Vector3 object.
        """
        return self.x, self.y, self.z

    def set_from_tuple(self, values):
        """
        Set the x, y, and z coordinates of the Vector3 object from a list of values.

        Args:
            values (tuple, list, Vector3): A list containing x, y, and z coordinates in that order.

        Raises:
            ValueError: If the provided list does not contain exactly 3 numeric elements.
        """
        if isinstance(values, Vector3):
            values = values.get_as_tuple()
        if isinstance(values, (tuple, list)) and len(values) == 3 and \
                all(isinstance(coord, (int, float)) for coord in values):
            self.x, self.y, self.z = values
        else:
            raise ValueError("Input list must contain exactly 3 numeric values" + str(values))

    def set_x(self, x):
        """
        Sets only the X value for this object.
        Args:
            x (int, float): An integer or float number to be used as new X value.
        """
        if x and not isinstance(x, (float, int)):
            logger.debug(f'Unable to set X value. Input must be a float or integer.')
            return
        self.x = x

    def set_y(self, y):
        """
        Sets only the X value for this object.
        Args:
            y (int, float): An integer or float number to be used as new X value.
        """
        if y and not isinstance(y, (float, int)):
            logger.debug(f'Unable to set Y value. Input must be a float or integer.')
            return
        self.y = y

    def set_z(self, z):
        """
        Sets only the X value for this object.
        Args:
            z (int, float): An integer or float number to be used as new X value.
        """
        if z and not isinstance(z, (float, int)):
            logger.debug(f'Unable to set X value. Input must be a float or integer.')
            return
        self.z = z


# ------------------------------------------------- Transform Start -----------------------------------------------
class Transform:
    def __init__(self, position=None, rotation=None, scale=None):
        """
        Initialize a Transform object using Vector3 objects for position, rotation, and scale

        Args:
            position (Vector3, optional): The position Vector3 object. Defaults to Vector3(0, 0, 0) if not provided.
            rotation (Vector3, optional): The rotation Vector3 object. Defaults to Vector3(0, 0, 0) if not provided.
            scale (Vector3, optional): The scale Vector3 object. Defaults to Vector3(1, 1, 1) if not provided.
        """
        self.position = Vector3(xyz=position) if position is not None else Vector3(0, 0, 0)
        self.rotation = Vector3(xyz=rotation) if rotation is not None else Vector3(0, 0, 0)
        self.scale = Vector3(xyz=scale) if scale is not None else Vector3(1, 1, 1)

    def __repr__(self):
        """
        Return a string representation of the Transform object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"position={str(self.position)}, "
            f"rotation={str(self.rotation)}, "
            f"scale={str(self.scale)}"
        )

    def __eq__(self, other):
        """
        Compare Transform objects for equality.

        Args:
            other (Transform): Object to compare.

        Returns:
            bool: True if the two Transform objects are equal, False otherwise.
        """
        if isinstance(other, self.__class__):
            return (
                    self.position == other.position and
                    self.rotation == other.rotation and
                    self.scale == other.scale
            )
        return False

    def __lt__(self, other):
        """
        Compare Transform objects element-wise for less than.

        Args:
            other (Transform): The other Transform object to compare.

        Returns:
            bool: True if all corresponding components are less than the other Transform's components,
                  False otherwise.
        """
        return (
                self.position < other.position and
                self.rotation < other.rotation and
                self.scale < other.scale
        )

    def __le__(self, other):
        """
        Compare Transform objects element-wise for less than or equal.

        Args:
            other (Transform): The other Transform object to compare.

        Returns:
            bool: True if all corresponding components are less than or equal to the other Transform's components,
                  False otherwise.
        """
        return (
                self.position <= other.position and
                self.rotation <= other.rotation and
                self.scale <= other.scale
        )

    def __gt__(self, other):
        """
        Compare Transform objects element-wise for greater than.

        Args:
            other (Transform): The other Transform object to compare.

        Returns:
            bool: True if all corresponding components are greater than the other Transform's components,
                  False otherwise.
        """
        return (
                self.position > other.position and
                self.rotation > other.rotation and
                self.scale > other.scale
        )

    def __ge__(self, other):
        """
        Compare Transform objects element-wise for greater than or equal.

        Args:
            other (Transform): The other Transform object to compare.

        Returns:
            bool: True if all corresponding components are greater than or equal to the other Transform's components,
                  False otherwise.
        """
        return (
                self.position >= other.position and
                self.rotation >= other.rotation and
                self.scale >= other.scale
        )

    def set_position(self, x=None, y=None, z=None, xyz=None):
        """
        Set the position of the Transform object using x, y, and z coordinates.

        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        if xyz and isinstance(xyz, Vector3):
            self.position = xyz
            return
        if xyz and isinstance(xyz, (list, tuple)):
            self.position = Vector3(xyz=xyz)
            return
        if x is not None and y is not None and z is not None:
            if all(isinstance(val, (float, int)) for val in (x, y, z)):
                self.position = Vector3(x=x, y=y, z=z)
                return
        # Not all channels
        if x is not None or y is not None or z is not None:
            if any(isinstance(val, (float, int)) for val in (x, y, z)):
                if x is not None and isinstance(x, (float, int)):
                    self.position.set_x(x=x)
                if y is not None and isinstance(y, (float, int)):
                    self.position.set_y(y=y)
                if z is not None and isinstance(z, (float, int)):
                    self.position.set_z(z=z)
                return
        logger.warning(f'Unable to set position. Invalid input.')

    def set_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Set the rotation of the Transform object using x, y, and z coordinates.

        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new rotation or a tuple/list with X, Y and Z values.
        """
        if xyz and isinstance(xyz, Vector3):
            self.rotation = xyz
            return
        if xyz and isinstance(xyz, (list, tuple)):
            self.rotation = Vector3(xyz=xyz)
            return
        if x is not None and y is not None and z is not None:
            if all(isinstance(val, (float, int)) for val in (x, y, z)):
                self.rotation = Vector3(x=x, y=y, z=z)
                return
        # Not all channels
        if x is not None or y is not None or z is not None:
            if any(isinstance(val, (float, int)) for val in (x, y, z)):
                if x is not None and isinstance(x, (float, int)):
                    self.rotation.set_x(x=x)
                if y is not None and isinstance(y, (float, int)):
                    self.rotation.set_y(y=y)
                if z is not None and isinstance(z, (float, int)):
                    self.rotation.set_z(z=z)
                return
        logger.warning(f'Unable to set rotation. Invalid input.')

    def set_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Set the scale of the Transform object using x, y, and z coordinates.

        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new scale or a tuple/list with X, Y and Z values.
        """
        if xyz and isinstance(xyz, Vector3):
            self.scale = xyz
            return
        if xyz and isinstance(xyz, (list, tuple)):
            self.scale = Vector3(xyz=xyz)
            return
        if x is not None and y is not None and z is not None:
            if all(isinstance(val, (float, int)) for val in (x, y, z)):
                self.scale = Vector3(x=x, y=y, z=z)
                return
        # Not all channels
        if x is not None or y is not None or z is not None:
            if any(isinstance(val, (float, int)) for val in (x, y, z)):
                if x is not None and isinstance(x, (float, int)):
                    self.scale.set_x(x=x)
                if y is not None and isinstance(y, (float, int)):
                    self.scale.set_y(y=y)
                if z is not None and isinstance(z, (float, int)):
                    self.scale.set_z(z=z)
                return
        logger.warning(f'Unable to set scale. Invalid input.')

    def to_matrix(self):
        """
        Convert the Transform object to a transformation matrix.

        Returns:
            list of lists: A 4x4 transformation matrix representing the combined transformations.
        """
        translation_matrix = [
            [1, 0, 0, self.position.x],
            [0, 1, 0, self.position.y],
            [0, 0, 1, self.position.z],
            [0, 0, 0, 1]
        ]

        rotation_matrix = self.rotation.to_rotation_matrix()  # You'll need to implement this method in Vector3

        scale_matrix = [
            [self.scale.x, 0, 0, 0],
            [0, self.scale.y, 0, 0],
            [0, 0, self.scale.z, 0],
            [0, 0, 0, 1]
        ]

        transformation_matrix = matrix_mult(translation_matrix, rotation_matrix)
        transformation_matrix = matrix_mult(transformation_matrix, scale_matrix)
        return transformation_matrix

    def set_from_tuple(self, position_tuple, rotation_tuple, scale_tuple):
        """
        Set the Transform attributes from tuples.

        Args:
            position_tuple (tuple): Tuple containing x, y, and z position values.
            rotation_tuple (tuple): Tuple containing x, y, and z rotation values.
            scale_tuple (tuple): Tuple containing x, y, and z scale values.

        Raises:
            ValueError: If the provided tuples do not contain exactly 3 numeric elements.
        """
        if len(position_tuple) != 3 or len(rotation_tuple) != 3 or len(scale_tuple) != 3:
            raise ValueError("Input tuples must contain exactly 3 numeric values")

        if all(isinstance(coord, (int, float)) for coord in position_tuple) and \
                all(isinstance(coord, (int, float)) for coord in rotation_tuple) and \
                all(isinstance(coord, (int, float)) for coord in scale_tuple):
            self.position = Vector3(*position_tuple)
            self.rotation = Vector3(*rotation_tuple)
            self.scale = Vector3(*scale_tuple)
        else:
            raise ValueError("Input tuples must contain only numeric values")

    def set_translation_from_tuple(self, position_tuple):
        """
        Set the translation using a tuple.

        Args:
            position_tuple (tuple): Tuple containing x, y, and z position values.

        Raises:
            ValueError: If the provided tuple does not contain exactly 3 numeric elements.
        """
        self.position.set_from_tuple(position_tuple)

    def set_rotation_from_tuple(self, rotation_tuple):
        """
        Set the rotation using a tuple.

        Args:
            rotation_tuple (tuple): Tuple containing x, y, and z rotation values.

        Raises:
            ValueError: If the provided tuple does not contain exactly 3 numeric elements.
        """
        self.rotation.set_from_tuple(rotation_tuple)

    def set_scale_from_tuple(self, scale_tuple):
        """
        Set the scale using a tuple.

        Args:
            scale_tuple (tuple): Tuple containing x, y, and z scale values.

        Raises:
            ValueError: If the provided tuple does not contain exactly 3 numeric elements.
        """
        self.scale.set_from_tuple(scale_tuple)

    def set_transform_from_object(self, obj_name, world_space=True):
        """
        Attempts to extract translation, rotation and scale data from the provided object.
        Updates the transform object with these extracted values.
        No changes in case object is missing or function fails to extract data.
        Args:
            obj_name (str): Name of the object to get the data from.
            world_space (bool, optional): Space used to extract values. True uses world-space, False uses object-space.
        Returns:
            Transform: it returns itself (The updated transform object)
        """
        if obj_name and not cmds.objExists(obj_name):
            logger.debug(f'Unable to extract transform data. Missing provided object: "{str(obj_name)}".')
            return self

        if world_space:
            position = cmds.xform(obj_name, q=True, t=True, ws=True)
            if position and len(position) == 3:
                self.set_position(xyz=position)
            rotation = cmds.xform(obj_name, q=True, ro=True, ws=True)
            if rotation and len(rotation) == 3:
                self.set_rotation(xyz=rotation)
        else:
            position = get_multiple_attr(obj_list=[obj_name], attr_list=['tx', 'ty', 'tz'], verbose=False)
            if position and len(position) == 3:
                self.set_position(xyz=list(position.values()))
            rotation = get_multiple_attr(obj_list=[obj_name], attr_list=['rx', 'ry', 'rz'], verbose=False)
            if rotation and len(rotation) == 3:
                self.set_rotation(xyz=list(rotation.values()))
        scale = get_multiple_attr(obj_list=[obj_name], attr_list=['sx', 'sy', 'sz'], verbose=False)
        if scale and len(scale) == 3:
            self.set_scale(xyz=list(scale.values()))

        return self

    def set_transform_from_dict(self, transform_dict):
        """
        Sets transform data from dictionary
        Args:
            transform_dict (dict): Dictionary with "position", "rotation", and "scale" keys.
                                   Their values should be tuples with three floats or integers each.
        """
        if transform_dict and not isinstance(transform_dict, dict):
            logger.debug(f'Unable to set transform from dictionary. '
                         f'Invalid input, argument must be a dictionary.')
            return
        position = transform_dict.get('position')
        rotation = transform_dict.get('rotation')
        scale = transform_dict.get('scale')
        for data in [position, rotation, scale]:
            if not data or not isinstance(data, (tuple, list)) or len(data) != 3:
                logger.debug(f'Unable to set transform from dictionary. '
                             f'Provide position, rotation and scale keys with tuples as their values.')
                return
        self.set_position(xyz=position)
        self.set_rotation(xyz=rotation)
        self.set_scale(xyz=scale)

    def apply_transform(self, target_object, world_space=True, object_space=False, relative=False):
        if not target_object or not cmds.objExists(target_object):
            logger.warning(f'Unable to apply transform. Missing object: "{target_object}".')
            return
        if world_space:
            cmds.move(self.position.x, self.position.y, self.position.z, target_object,
                      worldSpace=world_space, relative=relative, objectSpace=object_space)
            cmds.rotate(self.rotation.x, self.rotation.y, self.rotation.z, target_object,
                        worldSpace=world_space, relative=relative, objectSpace=object_space)
            set_attr(attribute_path=f'{target_object}.sx', value=self.scale.x)
            set_attr(attribute_path=f'{target_object}.sy', value=self.scale.y)
            set_attr(attribute_path=f'{target_object}.sz', value=self.scale.z)
        else:
            position = self.position.get_as_tuple()
            rotation = self.rotation.get_as_tuple()
            scale = self.scale.get_as_tuple()
            set_trs_attr(target_obj=target_object, value_tuple=position, translate=True)
            set_trs_attr(target_obj=target_object, value_tuple=rotation, rotate=True)
            set_trs_attr(target_obj=target_object, value_tuple=scale, scale=True)

    def get_position(self, as_tuple=False):
        """
        Gets the transform position
        Returns:
            Vector3 or tuple: Position value stored in this transform
        """
        if as_tuple:
            return self.position.get_as_tuple()
        return self.position

    def get_rotation(self, as_tuple=False):
        """
        Gets the transform rotation
        Returns:
            Vector3 or tuple: Rotation value stored in this transform
        """
        if as_tuple:
            return self.rotation.get_as_tuple()
        return self.rotation

    def get_scale(self, as_tuple=False):
        """
        Gets the transform scale
        Returns:
            Vector3 or tuple: Scale value stored in this transform
        """
        if as_tuple:
            return self.scale.get_as_tuple()
        return self.scale

    def get_transform_as_dict(self):
        """
        Gets the transform as a dictionary (used to serialize)
        Returns:
            dict: Dictionary with the transform data. Keys: "position", "rotation", "scale". Values: tuples (3 floats)
        """
        transform_dict = {"position": self.get_position(as_tuple=True),
                          "rotation": self.get_rotation(as_tuple=True),
                          "scale": self.get_scale(as_tuple=True),
                          }
        return transform_dict


# -------------------------------------------------- Transform End ------------------------------------------------


# ------------------------------------------------- Utilities Start -----------------------------------------------
def move_pivot_top():
    """ Moves pivot point to the top of the boundary box """
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)

    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    counter = 0
    errors = ''
    for obj in selection:
        try:
            bbox = cmds.exactWorldBoundingBox(obj)  # extracts bounding box
            top = [(bbox[0] + bbox[3]) / 2, bbox[4], (bbox[2] + bbox[5]) / 2]  # find top
            cmds.xform(obj, piv=top, ws=True)
            counter += 1
        except Exception as e:
            errors += str(e) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)

    pivot_pos = 'top'
    highlight_style = "color:#FF0000;text-decoration:underline;"
    feedback = FeedbackMessage(quantity=counter,
                               singular='pivot was',
                               plural='pivots were',
                               conclusion='moved to the',
                               suffix=pivot_pos,
                               style_suffix=highlight_style)
    if counter == 1:
        feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                   style_intro=highlight_style,
                                   conclusion='pivot was moved to the',
                                   suffix=pivot_pos,
                                   style_suffix=highlight_style)
    feedback.print_inview_message()


def move_pivot_base():
    """ Moves pivot point to the base of the boundary box """
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)

    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    counter = 0
    errors = ''
    for obj in selection:
        try:
            bbox = cmds.exactWorldBoundingBox(obj)  # extracts bounding box
            bottom = [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]  # find bottom
            cmds.xform(obj, piv=bottom, ws=True)  # sends pivot to bottom
            counter += 1
        except Exception as e:
            errors += str(e) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)
    pivot_pos = 'base'
    highlight_style = "color:#FF0000;text-decoration:underline;"
    feedback = FeedbackMessage(quantity=counter,
                               singular='pivot was',
                               plural='pivots were',
                               conclusion='moved to the',
                               suffix=pivot_pos,
                               style_suffix=highlight_style)
    if counter == 1:
        feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                   style_intro=highlight_style,
                                   conclusion='pivot was moved to the',
                                   suffix=pivot_pos,
                                   style_suffix=highlight_style)
    feedback.print_inview_message()


def move_to_origin(obj):
    """
    Moves the provided object to the center of the grid
    Args:
        obj: Name of the object (string)
    """
    cmds.move(0, 0, 0, obj, a=True, rpr=True)  # rpr flag moves it according to the pivot


def move_selection_to_origin():
    """ Moves selected objects back to origin """
    function_name = 'Move to Origin'
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True)
    selection_short = cmds.ls(selection=True)

    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    counter = 0
    errors = ''
    try:
        for obj in selection:
            try:
                move_to_origin(obj=obj)
                counter += 1
            except Exception as e:
                errors += str(e) + '\n'
        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('Some objects could not be moved to the origin. Open the script editor for a list of errors.')

        pivot_pos = 'origin'
        highlight_style = "color:#FF0000;text-decoration:underline;"
        feedback = FeedbackMessage(quantity=counter,
                                   singular='object was',
                                   plural='objects were',
                                   conclusion='moved to the',
                                   suffix=pivot_pos,
                                   style_suffix=highlight_style)
        if counter == 1:
            feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                       style_intro=highlight_style,
                                       conclusion='was moved to the',
                                       suffix=pivot_pos,
                                       style_suffix=highlight_style)
        feedback.print_inview_message()

    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def reset_transforms():
    """
    Reset transforms.
    It checks for incoming connections, then set the attribute to 0 if there are none
    It resets transforms, but ignores translate for joints.
    """
    function_name = 'Reset Transforms'
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    output_errors = ''
    output_counter = 0
    current_selection = cmds.ls(selection=True, long=True) or []
    current_selection_short = cmds.ls(selection=True) or []

    if not current_selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    def reset_trans(selection):
        errors = ''
        counter = 0
        for obj in selection:
            try:
                type_check = cmds.listRelatives(obj, children=True) or []

                if len(type_check) > 0 and cmds.objectType(type_check) != 'joint':
                    obj_connection_tx = cmds.listConnections(obj + '.tx', d=False, s=True) or []
                    if not len(obj_connection_tx) > 0:
                        if cmds.getAttr(obj + '.tx', lock=True) is False:
                            cmds.setAttr(obj + '.tx', 0)
                    obj_connection_ty = cmds.listConnections(obj + '.ty', d=False, s=True) or []
                    if not len(obj_connection_ty) > 0:
                        if cmds.getAttr(obj + '.ty', lock=True) is False:
                            cmds.setAttr(obj + '.ty', 0)
                    obj_connection_tz = cmds.listConnections(obj + '.tz', d=False, s=True) or []
                    if not len(obj_connection_tz) > 0:
                        if cmds.getAttr(obj + '.tz', lock=True) is False:
                            cmds.setAttr(obj + '.tz', 0)

                obj_connection_rx = cmds.listConnections(obj + '.rotateX', d=False, s=True) or []
                if not len(obj_connection_rx) > 0:
                    if cmds.getAttr(obj + '.rotateX', lock=True) is False:
                        cmds.setAttr(obj + '.rotateX', 0)
                obj_connection_ry = cmds.listConnections(obj + '.rotateY', d=False, s=True) or []
                if not len(obj_connection_ry) > 0:
                    if cmds.getAttr(obj + '.rotateY', lock=True) is False:
                        cmds.setAttr(obj + '.rotateY', 0)
                obj_connection_rz = cmds.listConnections(obj + '.rotateZ', d=False, s=True) or []
                if not len(obj_connection_rz) > 0:
                    if cmds.getAttr(obj + '.rotateZ', lock=True) is False:
                        cmds.setAttr(obj + '.rotateZ', 0)

                obj_connection_sx = cmds.listConnections(obj + '.scaleX', d=False, s=True) or []
                if not len(obj_connection_sx) > 0:
                    if cmds.getAttr(obj + '.scaleX', lock=True) is False:
                        cmds.setAttr(obj + '.scaleX', 1)
                obj_connection_sy = cmds.listConnections(obj + '.scaleY', d=False, s=True) or []
                if not len(obj_connection_sy) > 0:
                    if cmds.getAttr(obj + '.scaleY', lock=True) is False:
                        cmds.setAttr(obj + '.scaleY', 1)
                obj_connection_sz = cmds.listConnections(obj + '.scaleZ', d=False, s=True) or []
                if not len(obj_connection_sz) > 0:
                    if cmds.getAttr(obj + '.scaleZ', lock=True) is False:
                        cmds.setAttr(obj + '.scaleZ', 1)
                counter += 1
            except Exception as exception:
                logger.debug(str(exception))
                errors += str(exception) + '\n'
        return errors, counter

    try:
        output_errors, output_counter = reset_trans(current_selection)
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

    if output_counter > 0:
        feedback = FeedbackMessage(quantity=output_counter,
                                   conclusion='transforms were reset.')
        if output_counter == 1:
            feedback = FeedbackMessage(intro=f'"{current_selection_short[0]}"',
                                       style_intro="color:#FF0000;text-decoration:underline;",
                                       conclusion='transforms were reset.')
        feedback.print_inview_message()

    if output_errors != '':
        cmds.warning("Some objects couldn't be reset. Open the script editor for a list of errors.")


def convert_transforms_to_locators():
    """
    Converts transforms to locators without deleting them.
    Essentially places a locator where every transform is.
    """
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)
    errors = ''
    counter = 0
    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    locators_grp = 'transforms_as_locators_grp'
    if not cmds.objExists(locators_grp):
        locators_grp = cmds.group(name=locators_grp, world=True, empty=True)

    for obj in selection:
        try:
            loc = cmds.spaceLocator(name=obj + '_loc')[0]
            cmds.parent(loc, locators_grp)
            cmds.delete(cmds.parentConstraint(obj, loc))
            cmds.delete(cmds.scaleConstraint(obj, loc))
            counter += 1
        except Exception as exception:
            errors += str(exception) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)

    if counter > 0:
        cmds.select(selection)
        feedback = FeedbackMessage(quantity=counter,
                                   singular='locator was',
                                   plural='locators were',
                                   conclusion='created.')
        if counter == 1:
            feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                       style_intro="color:#FF0000;text-decoration:underline;",
                                       conclusion='locator was created.')
        feedback.print_inview_message(system_write=False)
        feedback.conclusion = f'created. Find generated elements in the group "{str(locators_grp)}".'
        sys.stdout.write(f'\n{feedback.get_string_message()}')


def overwrite_xyz_values(passthrough_xyz, overwrite_xyz=(0, 0, 0), overwrite_dimensions=None):
    """
    Helper function to skip/filter dimensions when applying transforms.
    Starts with the original XYZ values and overwrite each dimension with the provided overwrite values.
    If a filter is provided, a value can be ignored, in which case the original value is retained.

    Args:
        passthrough_xyz (tuple, list): A tuple with X, Y and Z floats. These are the return values when not overwritten.
        overwrite_xyz (tuple, list): A tuple/list with overwrite X, Y, Z floats. If no filter (overwrite_dimensions)
                                     is provided, nothing is overwritten. So the return value is the "passthrough_xyz".
                                     Default is (0, 0, 0) - Must contain three dimensions
        overwrite_dimensions (str, tuple, list, optional): Dimensions to overwrite ("x", "y", "z").
                                                           Any other characters are ignored. e.g. "a" does nothing.
                                                           Whatever dimension is provided here is overwritten using the
                                                           "overwrite_xyz" argument.
    Returns:
        tuple: A tuple with 3 float numbers (X, Y and Z) - Return is the original passthrough value, with specified
               dimensions overwritten by the "overwrite_xyz" tuple. (See example below)
    Example:
        original_xyz = [1, 2, 3]
        overwrite_xyz = [4, 5, 6]
        skip_filter = "x"
        print(filter_xyz_dimensions(original_xyz, overwrite_xyz, skip_filter))  # [1, 5, 6]
    """
    if overwrite_dimensions is None:
        return passthrough_xyz
    result_val = list(passthrough_xyz)
    for char in overwrite_dimensions:
        if char == "x":
            result_val[0] = overwrite_xyz[0]
        elif char == "y":
            result_val[1] = overwrite_xyz[1]
        elif char == "z":
            result_val[2] = overwrite_xyz[2]
    return result_val


def match_translate(source, target_list, skip=None):
    """
    Matches the translation values of an object by extracting the values from the source object and applying it to the
    target object(s) - Axis (dimensions) can be skipped (ignored) using the skip argument.
    Similar to point constraint.
    Args:
        source (str): The name of the source object (to extract the translation from)
        target_list (str, list, tuple): The name(s) of the target objects (objects to receive translate updates)
        skip (str, list, tuple, optional): Dimensions to skip for translation ("x", "y", "z").
    """
    if not source or not cmds.objExists(source):
        logger.debug(f'Missing source object "{str(source)}" while matching translate values.')
        return
    if isinstance(target_list, str):
        target_list = [target_list]
    source_translation = cmds.xform(source, query=True, rotatePivot=True, worldSpace=True)
    for target in target_list:
        if not target or not cmds.objExists(target):
            logger.debug(f'Missing target object "{str(target)}" while matching translate values.')
            continue
        target_translation = cmds.xform(target, query=True, translation=True, worldSpace=True)
        target_translation = overwrite_xyz_values(source_translation, target_translation, skip)
        cmds.xform(target, translation=target_translation, worldSpace=True)


def match_rotate(source, target_list, skip=None):
    """
    Matches the rotation (orientation) values of an object by extracting the values from the source object and
    applying it to the target object(s) - Axis (dimensions) can be skipped (ignored) using the skip argument.
    Similar to orient constraint.
    Args:
        source (str): The name of the source object (to extract the rotation from)
        target_list (str, list, tuple): The name(s) of the target objects (objects to receive rotate updates)
        skip (str, list, tuple, optional): Dimensions to skip for translation ("x", "y", "z").
    """
    if not source or not cmds.objExists(source):
        logger.debug(f'Missing source object "{str(source)}" while matching rotate values.')
        return
    if isinstance(target_list, str):
        target_list = [target_list]
    source_rotation = cmds.xform(source, query=True, rotation=True, worldSpace=True)
    for target in target_list:
        if not target or not cmds.objExists(target):
            logger.debug(f'Missing target object "{str(target)}" while matching rotate values.')
            continue
        target_rotation = cmds.xform(target, query=True, rotation=True, worldSpace=True)
        target_rotation = overwrite_xyz_values(source_rotation, target_rotation, skip)
        cmds.xform(target, rotation=target_rotation, worldSpace=True)


def match_scale(source, target_list, skip=None):
    """
    Matches the scale values of an object by extracting the values from the source object and applying it to the
    target object(s) - Axis (dimensions) can be skipped (ignored) using the skip argument.
    Args:
        source (str): The name of the source object (to extract the scale from)
        target_list (str, list, tuple): The name(s) of the target objects (objects to receive scale updates)
        skip (str, list, tuple, optional): Dimensions to skip for translation ("x", "y", "z").
    """
    if not source or not cmds.objExists(source):
        logger.debug(f'Missing source object "{str(source)}" while matching scale values.')
        return
    if isinstance(target_list, str):
        target_list = [target_list]
    source_scale = cmds.xform(source, query=True, scale=True, worldSpace=True)
    for target in target_list:
        if not target or not cmds.objExists(target):
            logger.debug(f'Missing target object "{str(target)}" while matching scale values.')
            continue
        target_scale = cmds.xform(target, query=True, scale=True, worldSpace=True)
        target_scale = overwrite_xyz_values(source_scale, target_scale, skip)
        cmds.xform(target, scale=target_scale, worldSpace=True)


def match_transform(source, target_list, translate=True, rotate=True, scale=True,
                    skip_translate=None, skip_rotate=None, skip_scale=None):
    """
    Match the transform attributes of the target object to the source object.

    Args:
        source (str): The name of the source object (to extract the transform from)
        target_list (str, list, tuple): The name(s) of the target objects (objects to receive transform update)
        translate (bool): Match translation attributes if True.
        rotate (bool): Match rotation attributes if True.
        scale (bool): Match scale attributes if True.
        skip_translate (str or list): Dimensions to skip for translation ("x", "y", "z"). Other strings are ignored.
        skip_rotate (str or list): Dimensions to skip for rotation ("x", "y", "z"). Other strings are ignored.
        skip_scale (str or list): Dimensions to skip for scale ("x", "y", "z"). Other strings are ignored.
    """
    if not source or not cmds.objExists(source):
        logger.debug(f'Missing source object "{str(source)}" while matching transform values.')
        return

    # Match translation
    if translate:
        match_translate(source=source, target_list=target_list, skip=skip_translate)

    # Match rotation
    if rotate:
        match_rotate(source=source, target_list=target_list, skip=skip_rotate)

    # Match scale
    if scale:
        match_scale(source=source, target_list=target_list, skip=skip_scale)


def set_equidistant_transforms(start, end, target_list, skip_start_end=True, constraint='parent'):
    """
    Sets equidistant transforms for a list of objects between a start and end point.
    Args:
        start
        end
        target_list (list, str): A list of objects to affect
        skip_start_end (bool, optional): If True, it will skip the start and end points, which means objects will be
                                         in-between start and end points, but not on top of start/end points.
        constraint (str): Which constraint type should be created. Supported: "parent", "point", "orient", "scale".
    """
    constraints = equidistant_constraints(start,
                                          end,
                                          target_list,
                                          skip_start_end=skip_start_end,
                                          constraint=constraint)
    cmds.delete(constraints)


def translate_shapes(obj_transform, offset):
    """
    Rotates the shape of an object without affecting its transform.
    Args:
        obj_transform (str): The transform node of the object.
        offset (tuple): The rotation offset in degrees (X, Y, Z).
    """
    shapes = cmds.listRelatives(obj_transform, shapes=True, fullPath=True) or []
    if not shapes:
        logger.debug("No shapes found for the given object.")
        return
    for shape in shapes:
        from gt.utils.hierarchy_utils import get_shape_components
        components = get_shape_components(shape)
        cmds.move(*offset, components, relative=True, objectSpace=True)


def rotate_shapes(obj_transform, offset):
    """
    Rotates the shape of an object without affecting its transform.
    Args:
        obj_transform (str): The transform node of the object.
        offset (tuple): The rotation offset in degrees (X, Y, Z).
    """
    shapes = cmds.listRelatives(obj_transform, shapes=True, fullPath=True) or []
    if not shapes:
        logger.debug("No shapes found for the given object.")
        return
    for shape in shapes:
        from gt.utils.hierarchy_utils import get_shape_components
        components = get_shape_components(shape)
        cmds.rotate(*offset, components, relative=True, objectSpace=True)


def scale_shapes(obj_transform, offset):
    """
    Rotates the shape of an object without affecting its transform.
    Args:
        obj_transform (str): The transform node of the object.
        offset (tuple, float, int): The scale offset in degrees (X, Y, Z).
                                          If a float or an integer is provided, it will be used as X, Y and Z.
                                          e.g. 0.5 = (0.5, 0.5, 0.5)
    """
    shapes = cmds.listRelatives(obj_transform, shapes=True, fullPath=True) or []
    if not shapes:
        logger.debug("No shapes found for the given object.")
        return
    if offset and isinstance(offset, (int, float)):
        offset = (offset, offset, offset)
    for shape in shapes:
        from gt.utils.hierarchy_utils import get_shape_components
        components = get_shape_components(shape)
        cmds.scale(*offset, components, relative=True, objectSpace=True)


def get_component_positions_as_dict(obj_transform, full_path=True, world_space=True):
    """
    Retrieves the positions of components (e.g., vertices) of a given object in the specified space.

    Args:
        obj_transform (str): The transform node of the object.
        full_path (bool, optional): Flag indicating whether to use full path names for shapes. Defaults to True.
        world_space (bool, optional): Flag indicating whether to retrieve positions in world space. Defaults to True.
                                      If set to False, function will use object space.

    Raises:
        Exception: If there is an issue getting the position, an exception is logged, and the operation continues.

    Returns:
        dict: A dictionary where component names are keys, and their corresponding positions are values.
              e.g. "{'|mesh.vtx[0]': [0.5, -1, 1]}"
    """
    if not obj_transform or not cmds.objExists(obj_transform):
        logger.warning(f'Unable to get component position dictionary. Missing object: {str(obj_transform)}')
        return {}
    shapes = cmds.listRelatives(obj_transform, shapes=True, fullPath=True) or []
    components = []
    for shape in shapes:
        from gt.utils.hierarchy_utils import get_shape_components
        components.extend(get_shape_components(shape=shape, mesh_component_type="vtx", full_path=full_path))
    component_pos_dict = {}
    for cv in components:
        try:
            if world_space:
                pos = cmds.xform(cv, query=True, worldSpace=True, translation=True)
            else:
                pos = cmds.xform(cv, query=True, objectSpace=True, translation=True)
            component_pos_dict[cv] = pos
        except Exception as e:
            logger.debug(f'Unable to get CV position. Issue: {e}')
    return component_pos_dict


def set_component_positions_from_dict(component_pos_dict, world_space=True):
    """
    Sets the positions of components (e.g., vertices) based on a provided dictionary.
    Provided dictionary should use the component path as keys and a list or tuple with X, Y, and Z floats as value.

    Args:
        component_pos_dict (dict): A dictionary where component names are keys, and their new positions are values.
                              Use "get_component_positions_as_dict" to generate a dictionary from an existing object.
        world_space (bool, optional): Flag indicating whether to set positions in world space. Defaults to True.
                                      If set to False, function will use object space.

    Raises:
        Exception: If there is an issue setting the position, an exception is logged, and the operation continues.

    Note:
        This function utilizes the 'cmds.xform' function to set component positions.
    """
    if not isinstance(component_pos_dict, dict):
        logger.debug(f'Unable to set component positions. Invalid component position dictionary.')
        return
    for cv, pos in component_pos_dict.items():
        try:
            if world_space:
                cmds.xform(cv, worldSpace=True, translation=pos)
            else:
                cmds.xform(cv, objectSpace=True, translation=pos)
        except Exception as e:
            logger.debug(f'Unable to set CV position. Issue: {e}')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # transform = Transform()
    # transform.set_position(0, 10, 0)
    # transform.apply_transform('pSphere1')
    rotate_shapes(cmds.ls(selection=True)[0], offset=(0, 0, -90))

    