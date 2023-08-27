"""
Transform Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.attr_utils import set_trs_attr
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
        Add two Vector3 objects element-wise.

        Args:
            other (Vector3): The other Vector3 object to add.

        Returns:
            Vector3: A new Vector3 object representing the sum of the two vectors.

        Raises:
            TypeError: If the operand type for addition is not supported.
        """
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

    def apply_transform(self, target_object, world_space=True, object_space=False, relative=False):
        if not target_object or not cmds.objExists(target_object):
            logger.warning(f'Unable to apply transform. Missing object: "{target_object}".')
            return
        if world_space:
            cmds.move(self.position.x, self.position.y, self.position.z, target_object,
                      worldSpace=world_space, relative=relative, objectSpace=object_space)
            cmds.rotate(self.rotation.x, self.rotation.y, self.rotation.z, target_object,
                        worldSpace=world_space, relative=relative, objectSpace=object_space)
            cmds.setAttr(f'{target_object}.sx', self.scale.x)
            cmds.setAttr(f'{target_object}.sy', self.scale.y)
            cmds.setAttr(f'{target_object}.sz', self.scale.z)
        else:
            position = self.position.get_as_tuple()
            rotation = self.rotation.get_as_tuple()
            scale = self.scale.get_as_tuple()
            set_trs_attr(target_obj=target_object, value_tuple=position, translate=True)
            set_trs_attr(target_obj=target_object, value_tuple=rotation, rotate=True)
            set_trs_attr(target_obj=target_object, value_tuple=scale, scale=True)

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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    transform = Transform()
    transform.set_position(0, 10, 0)
    transform.apply_transform('pSphere1')
