"""
Curve Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attribute_utils import add_attr_double_three, add_separator_attr
from gt.utils.data_utils import read_json_dict, write_json
from gt.utils.transform_utils import Transform, Vector3
from gt.utils.system_utils import DataDirConstants
from gt.utils.naming_utils import get_short_name
from decimal import Decimal
import maya.cmds as cmds
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
CURVE_TYPE_NURBS = "nurbsCurve"
CURVE_TYPE_BEZIER = "bezierCurve"
CURVE_TYPES = [CURVE_TYPE_NURBS, CURVE_TYPE_BEZIER]
CURVE_ATTR_COLOR = "autoColor"
CURVE_FILE_EXTENSION = "crv"
PROJECTION_AXIS_KEY = 'projectionAxis'
PROJECTION_SCALE_KEY = 'projectionScale'
PROJECTION_FIT_KEY = 'projectionFit'


def get_curve_path(curve_file):
    """
    Get the path to a curve data file. This file should exist inside the utils/data/curves folder.
    Args:
        curve_file (str): Name of the file. It doesn't need to contain its extension as it will always be "crv"
    Returns:
        str or None: Path to the curve description file. None if not found.
    """
    if not isinstance(curve_file, str):
        logger.debug(f'Unable to retrieve curve file. Incorrect argument type: "{str(type(curve_file))}".')
        return
    if not curve_file.endswith(f'.{CURVE_FILE_EXTENSION}'):
        curve_file = f'{curve_file}.{CURVE_FILE_EXTENSION}'
    path_to_curve = os.path.join(DataDirConstants.DIR_CURVES, curve_file)
    return path_to_curve


def get_curve_preview_image_path(curve_name):
    """
    Get the path to a curve data file. This file should exist inside the utils/data/curves folder.
    Args:
        curve_name (str): Name of the curve (same as curve file). It doesn't need to contain extension.
                          Function will automatically look for JPG or PNG files.
    Returns:
        str or None: Path to the curve preview image file. None if not found.
    """
    if not isinstance(curve_name, str):
        logger.debug(f'Unable to retrieve curve preview image. Incorrect argument type: "{str(type(curve_name))}".')
        return

    for ext in ["jpg", "png"]:
        path_to_curve = os.path.join(DataDirConstants.DIR_CURVES, f'{curve_name}.{ext}')
        if os.path.exists(path_to_curve):
            return path_to_curve


def combine_curves_list(curve_list, convert_bezier_to_nurbs=True):
    """
    Moves the shape objects of all elements in the provided input (curve_list) to a single group
    (essentially combining them under one transform)

    Args:
        curve_list (list): A list of strings with the name of the curves to be combined.
        convert_bezier_to_nurbs (bool, optional): If active, "bezier" curves will automatically be converted to "nurbs".
    Returns:
        str: Name of the generated curve when combining or name of the first curve in the list when only one found.
    """
    function_name = 'Combine Curves List'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        nurbs_shapes = []
        bezier_shapes = []

        for crv in curve_list:
            shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                    bezier_shapes.append(shape)
                if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                    nurbs_shapes.append(shape)

        if not nurbs_shapes and not bezier_shapes:  # No valid shapes
            logger.warning(f'Unable to combine curves. No valid shapes were found under the provided objects.')
            return

        if len(curve_list) == 1:  # Only one curve in provided list
            return curve_list[0]

        if len(bezier_shapes) > 0 and convert_bezier_to_nurbs:
            for bezier in bezier_shapes:
                logger.debug(str(bezier))
                cmds.select(bezier)
                cmds.bezierCurveToNurbs()

        shapes = nurbs_shapes + bezier_shapes
        for crv in range(len(curve_list)):
            cmds.makeIdentity(curve_list[crv], apply=True, rotate=True, scale=True, translate=True)

        group = cmds.group(empty=True, world=True, name=curve_list[0])
        cmds.select(shapes[0])
        for crv in range(1, (len(shapes))):
            cmds.select(shapes[crv], add=True)

        cmds.select(group, add=True)
        cmds.parent(relative=True, shape=True)
        cmds.delete(curve_list)
        combined_curve = cmds.rename(group, curve_list[0])
        return combined_curve
    except Exception as exception:
        logger.warning(f'An error occurred when combining the curves. Issue: {str(exception)}')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def separate_curve_shapes_into_transforms(curve_name):
    """
    Moves the shapes instead of a curve to individual transforms (separating curves)
    Args:
        curve_name (str): Name of the transform holding multiple shapes.
    Returns:
        list or None: List of transforms generated out of the operation or None if the operation failed.
    """
    function_name = 'Separate Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        nurbs_shapes = []
        bezier_shapes = []
        parent_transforms = []

        if not curve_name or not isinstance(curve_name, str) or not cmds.objExists(curve_name):
            logger.warning(f'Unable to separate curve shapes. Missing provided curve: "{curve_name}".')
            return

        new_transforms = []

        shapes = cmds.listRelatives(curve_name, shapes=True, fullPath=True) or []
        for shape in shapes:
            if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                bezier_shapes.append(shape)
            if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                nurbs_shapes.append(shape)

        if not nurbs_shapes and not bezier_shapes:  # No valid shapes
            logger.warning(f'Unable to separate curves. No valid shapes were found under the provided object.')
            return

        if len(shapes) == 1:  # Only one curve in provided object
            logger.debug('Provided curve contains only one shape. Nothing to separate.')
            return curve_name

        for obj in nurbs_shapes + bezier_shapes:
            parent = cmds.listRelatives(obj, parent=True) or []
            for par in parent:
                if par not in parent_transforms:
                    parent_transforms.append(par)
                cmds.makeIdentity(par, apply=True, rotate=True, scale=True, translate=True)
            group = cmds.group(empty=True, world=True, name=get_short_name(obj).replace('Shape', ''))
            cmds.parent(obj, group, relative=True, shape=True)
            new_transforms.append(group)

        for obj in parent_transforms:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            if cmds.objExists(obj) and cmds.objectType(obj) == 'transform' and len(shapes) == 0:
                cmds.delete(obj)
        return new_transforms
    except Exception as e:
        logger.warning(f'An error occurred when separating the curve. Issue: {e}')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def selected_curves_combine(convert_bezier_to_nurbs=False, show_bezier_conversion_dialog=True):
    """
    Moves the shape objects of all selected curves under a single group (combining them)

    Args:
        convert_bezier_to_nurbs (bool, optional): If active, the script will not show a dialog when "bezier" curves
                                                  are found and will automatically convert them to nurbs.
        show_bezier_conversion_dialog (bool, optional): If a "bezier" curve is found and this option is active,
                                                        a dialog will ask the user if they want to convert "bezier"
                                                        curves to "nurbs".
    Returns:
        str or None: Name of the generated combined curve. None if it failed to generate it.
    """
    errors = ''
    function_name = 'Combine Selected Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl=True, absoluteName=True)
        nurbs_shapes = []
        bezier_shapes = []

        if len(selection) < 2:
            logger.warning('You need to select at least two curves.')
            return

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                    bezier_shapes.append(shape)
                if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                    nurbs_shapes.append(shape)

        if not nurbs_shapes and not bezier_shapes:  # No valid shapes
            logger.warning(f'Unable to combine curves. No valid shapes were found under the provided objects.')
            return

        # Determine if converting Bezier curves
        if len(bezier_shapes) > 0 and show_bezier_conversion_dialog:
            user_input = cmds.confirmDialog(title='Bezier curve detected!',
                                            message='A bezier curve was found in your selection.\n'
                                                    'Would you like to convert Bezier to NURBS before combining?',
                                            button=['Yes', 'No'],
                                            defaultButton='Yes',
                                            cancelButton='No',
                                            dismissString='No',
                                            icon="warning")
            convert_bezier_to_nurbs = True if user_input == 'Yes' else False

        # Freeze Curves
        for obj in range(len(selection)):
            try:
                cmds.makeIdentity(selection[obj], apply=True, rotate=True, scale=True, translate=True)
            except Exception as e:
                logger.debug(f'Unable to freeze curves when combining them. Issue: {e}')

        # Combine
        combined_crv = combine_curves_list(selection, convert_bezier_to_nurbs=convert_bezier_to_nurbs)
        sys.stdout.write('\nSelected curves were combined into: "' + combined_crv + '".')
        cmds.select(combined_crv)
        return combined_crv

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def selected_curves_separate():
    """
    Moves the shapes instead of a curve to individual transforms (separating curves)
    Returns:
        list: List of transforms generated out of the operation (each separated shape goes under a new transform)
    """
    function_name = 'Separate Selected Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl=True, long=True) or []

        if len(selection) < 1:
            logger.warning('You need to select at least one curve.')
            return

        parent_transforms = []
        for obj in selection:
            nurbs_shapes = []
            bezier_shapes = []
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                    bezier_shapes.append(shape)
                if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                    nurbs_shapes.append(shape)

            curve_shapes = nurbs_shapes + bezier_shapes
            if len(curve_shapes) == 0:
                logger.warning(f'Unable to separate "{obj}". No valid shapes were found under this object.')
            elif len(curve_shapes) > 1:
                parent_transforms.extend(separate_curve_shapes_into_transforms(obj))
            else:
                cmds.warning('The selected curve contains only one shape.')

        cmds.select(parent_transforms)
        sys.stdout.write('\n' + str(len(parent_transforms)) + ' shapes extracted.')
        return parent_transforms
    except Exception as e:
        logger.warning(f'An error occurred when separating the curves. Issue: {e}')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def add_snapping_shape(target_object):
    """
    Parents a locator shape to the target object so objects can be snapped to it.
    The parented locator shape has a scale of 0, so it doesn't change the look of the target object.
    Args:
        target_object (str): Name of the object to add the locator shape.
    Returns:
        str: Name of the added invisible locator shape
    """
    if not target_object or not cmds.objExists(target_object):
        return
    locator = cmds.spaceLocator(name=target_object + "Point")[0]
    locator_shape = cmds.listRelatives(locator, s=True, f=True) or []
    cmds.setAttr(locator_shape[0] + ".localScaleX", 0)
    cmds.setAttr(locator_shape[0] + ".localScaleY", 0)
    cmds.setAttr(locator_shape[0] + ".localScaleZ", 0)
    cmds.select(locator_shape)
    cmds.select(target_object, add=True)
    cmds.parent(relative=True, shape=True)
    cmds.delete(locator)
    return locator_shape[0]


def add_side_color_setup(obj, left_clr=(0, 0.5, 1), right_clr=(1, 0.5, 0.5)):
    """
    This function sets up a side color setup for the specified object in the Maya scene.
    It creates connections and attributes to control the color of the object based on its position in the scene.

    Parameters:
        obj (str): The name of the object to set up the color for.
        left_clr (tuple, optional): The RGB color values for the left side of the object. Default is (0, 0.5, 1).
        right_clr (tuple, optional): The RGB color values for the right side of the object. Default is (1, 0.5, 0.5).

    Example:
        # Example usage in Maya Python script editor:
        add_side_color_setup("pCube1", left_clr=(0, 1, 0), right_clr=(1, 0, 0))
    """
    if not obj or not cmds.objExists(obj):
        return

    # Setup Base Connections
    default_clr = (1, 1, 0.65)
    cmds.setAttr(obj + ".overrideEnabled", 1)
    cmds.setAttr(obj + ".overrideRGBColors", 1)
    clr_side_condition = cmds.createNode("condition", name=obj + "_clr_side_condition")
    clr_center_condition = cmds.createNode("condition", name=obj + "_clr_center_condition")
    decompose_matrix = cmds.createNode("decomposeMatrix", name=obj + "_decompose_matrix")
    cmds.connectAttr(obj + ".worldMatrix[0]", decompose_matrix + ".inputMatrix")
    cmds.connectAttr(decompose_matrix + ".outputTranslateX", clr_side_condition + ".firstTerm")
    cmds.connectAttr(decompose_matrix + ".outputTranslateX", clr_center_condition + ".firstTerm")
    cmds.connectAttr(clr_side_condition + ".outColor", clr_center_condition + ".colorIfFalse")
    cmds.setAttr(clr_side_condition + ".operation", 2)

    # Create Auto Color Attribute
    cmds.addAttr(obj, ln=CURVE_ATTR_COLOR, at='bool', k=True)
    cmds.setAttr(obj + "." + CURVE_ATTR_COLOR, 1)
    clr_auto_blend = cmds.createNode("blendColors", name=obj + "_clr_auto_blend")
    cmds.connectAttr(clr_auto_blend + ".output", obj + ".overrideColorRGB")
    cmds.connectAttr(clr_center_condition + ".outColor", clr_auto_blend + ".color1")
    cmds.connectAttr(obj + "." + CURVE_ATTR_COLOR, clr_auto_blend + ".blender")

    # Setup Color Attributes
    clr_attr = "colorDefault"
    add_attr_double_three(obj, clr_attr, keyable=False)
    cmds.setAttr(obj + "." + clr_attr + "R", default_clr[0])
    cmds.setAttr(obj + "." + clr_attr + "G", default_clr[1])
    cmds.setAttr(obj + "." + clr_attr + "B", default_clr[2])
    cmds.connectAttr(obj + "." + clr_attr + "R", clr_center_condition + ".colorIfTrueR")
    cmds.connectAttr(obj + "." + clr_attr + "G", clr_center_condition + ".colorIfTrueG")
    cmds.connectAttr(obj + "." + clr_attr + "B", clr_center_condition + ".colorIfTrueB")
    cmds.connectAttr(obj + "." + clr_attr, clr_auto_blend + ".color2")  # Blend node input
    r_clr_attr = "colorRight"
    add_attr_double_three(obj, r_clr_attr, keyable=False)
    cmds.setAttr(obj + "." + r_clr_attr + "R", left_clr[0])
    cmds.setAttr(obj + "." + r_clr_attr + "G", left_clr[1])
    cmds.setAttr(obj + "." + r_clr_attr + "B", left_clr[2])
    cmds.connectAttr(obj + "." + r_clr_attr + "R", clr_side_condition + ".colorIfTrueR")
    cmds.connectAttr(obj + "." + r_clr_attr + "G", clr_side_condition + ".colorIfTrueG")
    cmds.connectAttr(obj + "." + r_clr_attr + "B", clr_side_condition + ".colorIfTrueB")
    l_clr_attr = "colorLeft"
    add_attr_double_three(obj, l_clr_attr, keyable=False)
    cmds.setAttr(obj + "." + l_clr_attr + "R", right_clr[0])
    cmds.setAttr(obj + "." + l_clr_attr + "G", right_clr[1])
    cmds.setAttr(obj + "." + l_clr_attr + "B", right_clr[2])
    cmds.connectAttr(obj + "." + l_clr_attr + "R", clr_side_condition + ".colorIfFalseR")
    cmds.connectAttr(obj + "." + l_clr_attr + "G", clr_side_condition + ".colorIfFalseG")
    cmds.connectAttr(obj + "." + l_clr_attr + "B", clr_side_condition + ".colorIfFalseB")


class Curve:
    def __init__(self,
                 name=None,
                 transform=None,
                 shapes=None,
                 metadata=None,
                 read_existing_curve=None,
                 data_from_dict=None,
                 data_from_file=None):
        """
        Initializes a Curve object
        Args:
            name (str, optional): Curve transform name (shapes names are determined by the CurveShape objects)
            transform (Transform, optional): TRS Transform data used to determine initial position of the curve.
                                             If not provided, it's created at the origin.
            shapes (list, optional): A list of shapes (CurveShape) objects used to describe the curve visuals.
                                     Only optional so the curve can be generated using a file, ultimately required.
            metadata (dict, optional): A dictionary with any extra information used to further describe the curve.
            read_existing_curve (str, optional): Extracts data from an existing curve in the scene.
            data_from_dict (dict, optional): If provided, this dictionary is used to populate the curve data.
            data_from_file (str, optional): Path to a JSON file describing the curve.
                                                       It reads the JSON content as a "read_curve_data" dictionary.
        """
        self.name = name
        self.transform = transform
        self.shapes = shapes
        self.metadata = None

        if metadata:
            self.set_metadata_dict(new_metadata=metadata)

        if read_existing_curve:
            self.read_data_from_existing_curve(read_existing_curve)

        if data_from_dict:
            self.set_data_from_dict(data_dict=data_from_dict)

        if data_from_file:
            self.read_curve_from_file(file_path=data_from_file)

    def is_curve_valid(self):
        """
        Checks if the Curve object has enough data to create/generate a curve.
        Returns:
            bool: True if it's valid (can create a curve), False if invalid.
        """
        if not self.shapes:
            logger.warning(f'Invalid curve. Missing shapes.')
            return False
        if self.name and not isinstance(self.name, str):
            logger.warning(f'Invalid curve. Current name is not a string. Name type: {str(type(self.name))}')
            return False
        return True

    def build(self):
        """
        Use the loaded values (shapes) of the object to generate/create a Maya curve.
        Returns:
            str: Name of the transform of the newly generated curve.
        """
        # Basic elements -----------------------------------------
        if not self.is_curve_valid():
            return
        generated_shapes = []
        for shape in self.shapes:
            generated_shapes.append(shape.build())
        generated_curve = combine_curves_list(generated_shapes)
        if self.name:
            generated_curve = cmds.rename(generated_curve, self.name)
        if self.transform:
            self.apply_curve_transform(generated_curve)
        cmds.select(clear=True)
        return generated_curve

    def apply_curve_transform(self, target_object):
        """
        Uses the provided Transform data to set the TRS data of the curve object.
        Args:
            target_object (str): Name of the curve to set with stored Transform data
        """
        if not target_object:
            logger.warning(f'Unable to apply curve transform. Missing transform data.')
            return
        if not isinstance(self.transform, Transform):
            logger.warning(f'Unable to apply curve transform. '
                           f'Expected "Transform", but got "{str(type(self.transform))}".')
            return
        self.transform.apply_transform(target_object=target_object)

    def read_data_from_existing_curve(self, existing_curve):
        """
        Initializes Curve object using the data found in an existing curve.
        Args:
            existing_curve (str): The name of the curve object to extract the data from (must exist)
        """
        if not isinstance(existing_curve, str):
            logger.warning(f'Unable to extract curve data. Expected string but got "{str(type(existing_curve))}"')
            return

        # Check Existence
        if not existing_curve or not cmds.objExists(existing_curve):
            logger.warning(f'Unable to extract curve data. Missing curve: "{str(existing_curve)}"')
            return

        # Get Relatives
        nurbs_shapes = []
        bezier_shapes = []
        shapes = cmds.listRelatives(existing_curve, shapes=True, fullPath=True) or []
        for shape in shapes:
            if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                bezier_shapes.append(shape)
            if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                nurbs_shapes.append(shape)
        if not nurbs_shapes and not bezier_shapes:  # No valid shapes
            logger.warning(f'Unable to extract curve data. No valid shapes were found under the provided curve.')
            return

        # Extra Shapes
        extracted_shapes = []
        for crv_shapes in nurbs_shapes + bezier_shapes:
            extracted_shapes.append(CurveShape(read_existing_shape=crv_shapes))

        # Extra Transform
        transform = None
        position = cmds.getAttr(f'{existing_curve}.translate')[0]
        rotation = cmds.getAttr(f'{existing_curve}.rotate')[0]
        scale = cmds.getAttr(f'{existing_curve}.scale')[0]
        if any(position) or any(rotation) and scale != [1, 1, 1]:
            position = Vector3(position[0], position[1], position[2])
            rotation = Vector3(rotation[0], rotation[1], rotation[2])
            scale = Vector3(scale[0], scale[1], scale[2])
            transform = Transform(position=position, rotation=rotation, scale=scale)

        # Store Data
        self.name = existing_curve
        self.shapes = extracted_shapes
        self.transform = transform

    def get_data_as_dict(self):
        """
        Gets the object values as a dictionary
        Returns:
            dict: The Curve object properties and its values.
        """
        if not self.is_curve_valid():
            return
        shapes_data = []
        for shape in self.shapes:
            shapes_data.append(shape.get_data_as_dict())
        transform_data = None
        if self.transform:
            pos_data = [self.transform.position.x, self.transform.position.y, self.transform.position.z]
            rot_data = [self.transform.position.x, self.transform.position.y, self.transform.position.z]
            sca_data = [self.transform.position.x, self.transform.position.y, self.transform.position.z]
            transform_data = {"position": pos_data,
                              "rotation": rot_data,
                              "scale": sca_data}
        curve_data = {"name": self.name,
                      "transform": transform_data,
                      "shapes": shapes_data,
                      }
        if self.metadata:
            curve_data['metadata'] = self.metadata
        return curve_data

    def set_data_from_dict(self, data_dict):
        """
        Sets the object values from a dictionary
        Args:
            data_dict (dict): A dictionary with property names and values describing a Curve object.
        """
        if not isinstance(data_dict, dict):
            logger.warning(f'Unable to ingest curve data. Data must be a dictionary, but was: {str(type(data_dict))}"')
            return
        if not data_dict.get('shapes'):
            logger.warning(f'Unable to ingest curve data. Missing shapes. Shapes data: {str(data_dict.get("shapes"))}"')
            return
        shapes = []
        input_shapes = data_dict.get('shapes')
        if input_shapes:
            for shape in input_shapes:
                shapes.append(CurveShape(read_curve_shape_data=shape))
        self.shapes = shapes
        if data_dict.get('name'):
            self.name = data_dict.get('name')
        transform_data = data_dict.get('transform')
        if transform_data:
            position = Vector3(transform_data[0], transform_data[1], transform_data[2])
            rotation = Vector3(transform_data[3], transform_data[4], transform_data[5])
            scale = Vector3(transform_data[6], transform_data[7], transform_data[8])
            self.transform = Transform(position, rotation, scale)
        metadata = data_dict.get('metadata')
        if data_dict.get('metadata'):
            self.metadata = metadata

    def set_name(self, new_name):
        """
        Sets a new curve name. Useful when ingesting data from dictionary or file with undesired name.
        Args:
            new_name (str): New name to use on the curve.
        """
        if not new_name or not isinstance(new_name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(new_name))}"')
            return
        self.name = new_name

    def set_metadata_dict(self, new_metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            new_metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(new_metadata, dict):
            logger.warning(f'Unable to set curve metadata. Expected a dictionary, but got: "{str(type(new_metadata))}"')
            return
        self.metadata = new_metadata

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

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_name(self, formatted=False):
        """
        Gets the name property of the curve.
        Args:
            formatted (bool, optional): If active, it will convert snake_case names to Title Sentences
                                        e.g. "circle_arrow" will become "Circle Arrow"
        Returns:
            str or None: Name of the curve, None if it's not set.
        """
        if formatted and self.name:
            return self.name.replace("_", " ").title()
        return self.name

    def read_curve_from_file(self, file_path):
        """
        Reads the data from a file.
        Args:
            file_path (str): Path to an existing file containing a curve description.
        """
        received_data = read_json_dict(file_path)
        self.set_data_from_dict(received_data)

    def write_curve_to_file(self, file_path):
        """
        Writes data necessary to re-create this curve to a file.
        Args:
            file_path (str): Path to the file where the data is going to be stored.
        """
        if not self.is_curve_valid():
            return
        write_json(path=file_path, data=self.get_data_as_dict())


class CurveShape:
    def __init__(self,
                 name=None,
                 points=None,
                 degree=None,
                 knot=None,
                 periodic=None,
                 is_bezier=False,
                 read_curve_shape_data=None,
                 read_existing_shape=None):
        """
        Initializes a curve shape object.

        Args:
            name (str, optional): Name of the curve shape.
            points (list, optional):  The x, y, z position of a point. This flag can take values with units.
            degree (int, optional): The degree of the new curve. Default is "None" which becomes 3 during creation.
                                    Note that you need (degree+1) curve points to create a visible curve span.
                                    e.g. you must place 4 points for a degree 3 curve.
            knot (list, optional): A knot value in a knot vector. One flag per knot value.
                                   There must be (numberOfPoints + degree - 1) knots and
                                   the knot vector must be non-decreasing.
            periodic (bool, optional):  If on, creates a curve that is periodic. Default is (None) off.
            is_bezier= (bool, optional): Determines the curve type. If active, the curve is bezier, off (default) nurbs.
            read_curve_shape_data (dict, optional): A dictionary describing the curve shape.
                                                       It populates the properties according to the values found in it.
            read_existing_shape (str, optional): Uses an existing shape in the scene to initialize the CurveShape.
        """
        self.name = name
        self.points = points
        self.degree = degree
        self.knot = knot
        self.periodic = periodic
        self.is_bezier = is_bezier

        if read_existing_shape:
            self.read_data_from_existing_curve_shape(crv_shape=read_existing_shape)

        if read_curve_shape_data:
            self.set_data_from_dict(data_dict=read_curve_shape_data)

    def __repr__(self):
        """
        Generates a custom string message to return a proper sentence when printing or casting this object to string.
        """
        obj_dict = self.__dict__
        output_lines = []
        for key, value in obj_dict.items():
            output_lines.append(f'"{key}": {value}')
        output_string = 'CurveShape:\n'
        print_data = "\n\t".join(output_lines)
        return f'{output_string}\t{print_data}'

    def is_curve_shape_valid(self):
        """
        Checks if the CurveShape object has enough data to create a curve.
        Returns:
            bool: True if it's valid (can create a curve), False if invalid.
        """
        if not self.points:
            logger.warning(f'Invalid curve shape. Missing points.')
            return False
        return True

    def read_data_from_existing_curve_shape(self, crv_shape):
        """
        Reads/Extracts data from an existing curve.

        Args:
            crv_shape (str): Name of the curve. (Must exist in the Maya scene - with unique or long name)

        Example:
            curve_shape_b = CurveShape()
            curve_shape_b.read_data_from_existing_curve_shape(crv_shape="my_curve")
            curve_shape_b.build()  # Creates the same curve

            curve_shape = CurveShape(read_existing_shape="my_curve")
            curve_shape.build()  # Creates the same curve provided above
        """
        if not isinstance(crv_shape, str):
            logger.warning(f'Unable to extract curve data. Expected string but got "{str(type(crv_shape))}"')
            return
        # Check Existence
        if not crv_shape or not cmds.objExists(crv_shape):
            logger.warning(f'Unable to extract curve data. Missing shape: "{str(crv_shape)}"')
            return
        # Get Full Path
        crv_shape = cmds.ls(crv_shape, long=True)[0]
        # Check Type
        if cmds.objectType(crv_shape) not in CURVE_TYPES:
            logger.warning(f'Unable to extract curve data. Missing acceptable curve shapes. '
                           f'Acceptable shape types: {CURVE_TYPES}')
            return
        is_bezier = False
        if cmds.objectType(crv_shape) == CURVE_TYPE_BEZIER:
            is_bezier = True
        # Extract Data
        crv_info_node = None
        try:
            periodic = cmds.getAttr(crv_shape + '.form')
            knot = None
            if is_bezier or periodic == 2:  # 0: Open, 1: Closed: 2: Periodic
                crv_info_node = cmds.arclen(crv_shape, ch=True)
                knot = cmds.getAttr(crv_info_node + '.knots[*]')
                cmds.delete(crv_info_node)

            cvs = cmds.getAttr(crv_shape + '.cv[*]')
            cvs_list = []

            for c in cvs:
                data = [float(Decimal("%.3f" % c[0])), float(Decimal("%.3f" % c[1])), float(Decimal("%.3f" % c[2]))]
                cvs_list.append(data)

            periodic_end_cvs = []
            if periodic == 2 and len(cvs) > 2:
                for i in range(3):
                    periodic_end_cvs += [cvs_list[i]]

            points = cvs_list
            if periodic_end_cvs:
                points.extend(periodic_end_cvs)

            degree = cmds.getAttr(crv_shape + '.degree')
            # Store Extracted Values
            self.name = get_short_name(crv_shape)
            self.points = points
            self.periodic = periodic
            self.knot = knot
            self.degree = degree
            self.is_bezier = is_bezier
        except Exception as e:
            logger.warning(f'Unable to extract curve shape data. Issue: {str(e)}')
        finally:  # Clean-up temp nodes - In case they were left behind
            to_delete = [crv_info_node]
            for obj in to_delete:
                if obj and cmds.objExists(obj):
                    try:
                        cmds.delete(obj)
                    except Exception as e:
                        logger.debug(f'Unable to clean up scene after extracting curve. Issue: {str(e)}')

    def build(self, replace_crv=None):
        """
        Use the loaded values of the object to generate/create a Maya curve.
        Since a shape can't exist on its own, a transform (group) is created for it.
        When a name is provided, it uses the name variable followed by "_transform" as the name of the transform group.
        Args:
            replace_crv (str): Name of the curve to replace
        Returns:
            str: Name of the generated shape
        """
        # Basic elements -----------------------------------------
        if not self.is_curve_shape_valid():
            return

        # Check if knots are valid
        knot = self.knot
        periodic = self.periodic
        if self.degree and self.points and self.knot:
            expected_knot_length = len(self.points) + self.degree - 1
            if len(self.knot) != expected_knot_length:  # Invalid knots - Must have length (#CVs + degree - 1)
                knot = None
                periodic = None
                logger.debug(f'CurveShape had an invalid number of knots:\n{self}')

        parameters = {"point": self.points}
        # Extra elements -----------------------------------------
        named_parameters = {'degree': self.degree,
                            'periodic': periodic,
                            'knot': knot,
                            }
        if self.name:
            named_parameters['name'] = f'{self.name}_transform'
        if self.is_bezier:
            named_parameters['bezier'] = True
        for key, value in named_parameters.items():
            if value:
                parameters[key] = value
        if replace_crv:
            curve_output = cmds.curve(replace_crv, replace=True, **parameters)
            for shape in cmds.listRelatives(curve_output, shapes=True) or []:
                cmds.rename(shape, self.name)
            return curve_output
        else:
            curve_output = cmds.curve(**parameters)
            for shape in cmds.listRelatives(curve_output, shapes=True) or []:
                cmds.rename(shape, self.name)
            return curve_output

    def get_data_as_dict(self):
        """
        Gets the object values as a dictionary
        Returns:
            dict: The CurveShape object properties and its values.
        """
        if not self.is_curve_shape_valid():
            return
        return self.__dict__

    def set_data_from_dict(self, data_dict):
        """
        Sets the object values from a dictionary
        Args:
            data_dict (dict): A dictionary with property names and values describing the properties of a CurveShape.
            e.g.
            {'degree': 1,
             'is_bezier': False,
             'knot': None,
             'name': 'curveShape1',
             'periodic': 0,
             'points': [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        """
        if not isinstance(data_dict, dict):
            logger.warning(f'Unable to ingest curve data. Data must be a dictionary, but was: {str(type(data_dict))}"')
            return
        if not data_dict.get('points'):
            logger.warning(f'Unable to ingest curve data. Missing points. Points data: {str(data_dict.get("points"))}"')
            return
        if data_dict.get('points'):
            self.points = data_dict.get('points')
        if data_dict.get('name'):
            self.name = data_dict.get('name')
        if data_dict.get('degree'):
            self.degree = data_dict.get('degree')
        if data_dict.get('knot'):
            self.knot = data_dict.get('knot')
        if data_dict.get('periodic'):
            self.periodic = data_dict.get('periodic')

    def set_name(self, new_name):
        """
        Sets a new curve shape name. Useful when ingesting data from dictionary with undesired name.
        Args:
            new_name (str): New name to use on the curve shape.
        """
        if not new_name or not isinstance(new_name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(new_name))}"')
            return
        self.name = new_name

    def replace_target_curve(self, target_curve):
        """
        Replaces the target curve with the current stored data
        Args:
            target_curve (str): Name of the target curve transform or shape (the one that will be replaced/overwritten)
        Returns::
            str: Output of the cmds.curve(target_curve, replace=True) operation.
        """
        if not isinstance(target_curve, str):
            logger.warning(f'Unable to replace curve. Expected string as input, but got "{str(type(target_curve))}"')
            return
        if not self.is_curve_shape_valid():
            return
        return self.build(replace_crv=target_curve)


class Curves:
    def __init__(self):
        """
        A library of curve objects
        Use "build()" to create them in Maya.
        """
    arrow_circle_to_head = Curve(data_from_file=get_curve_path("arrow_circle_to_head"))
    arrow_content_moved = Curve(data_from_file=get_curve_path("arrow_content_moved"))
    arrow_corner_broken = Curve(data_from_file=get_curve_path("arrow_corner_broken"))
    arrow_curved_converge = Curve(data_from_file=get_curve_path("arrow_curved_converge"))
    arrow_curved_return = Curve(data_from_file=get_curve_path("arrow_curved_return"))
    arrow_direction_eight_sides = Curve(data_from_file=get_curve_path("arrow_direction_eight_sides"))
    arrow_direction_four_sides = Curve(data_from_file=get_curve_path("arrow_direction_four_sides"))
    arrow_direction_four_sides_skinny = Curve(data_from_file=get_curve_path("arrow_direction_four_sides_skinny"))
    arrow_direction_two_sides = Curve(data_from_file=get_curve_path("arrow_direction_two_sides"))
    arrow_direction_two_sides_skinny = Curve(data_from_file=get_curve_path("arrow_direction_two_sides_skinny"))
    arrow_direction_two_sides_skinny_heads = Curve(
        data_from_file=get_curve_path("arrow_direction_two_sides_skinny_heads"))
    arrow_direction_two_sides_small = Curve(data_from_file=get_curve_path("arrow_direction_two_sides_small"))
    arrow_direction_two_sides_smaller = Curve(data_from_file=get_curve_path("arrow_direction_two_sides_smaller"))
    arrow_eight_detailed = Curve(data_from_file=get_curve_path("arrow_eight_detailed"))
    arrow_fletching_nock_flat = Curve(data_from_file=get_curve_path("arrow_fletching_nock_flat"))
    arrow_four_maximize = Curve(data_from_file=get_curve_path("arrow_four_maximize"))
    arrow_head_aim_flat_four_sides = Curve(data_from_file=get_curve_path("arrow_head_aim_flat_four_sides"))
    arrow_head_candy_corn_smooth = Curve(data_from_file=get_curve_path("arrow_head_candy_corn_smooth"))
    arrow_head_flat_aim = Curve(data_from_file=get_curve_path("arrow_head_flat_aim"))
    arrow_head_flat_concave = Curve(data_from_file=get_curve_path("arrow_head_flat_concave"))
    arrow_head_flat_triangle = Curve(data_from_file=get_curve_path("arrow_head_flat_triangle"))
    arrow_head_flat_triangle_small = Curve(data_from_file=get_curve_path("arrow_head_flat_triangle_small"))
    arrow_head_outline_no_base = Curve(data_from_file=get_curve_path("arrow_head_outline_no_base"))
    arrow_head_stylized = Curve(data_from_file=get_curve_path("arrow_head_stylized"))
    arrow_long = Curve(data_from_file=get_curve_path("arrow_long"))
    arrow_loop_infinite = Curve(data_from_file=get_curve_path("arrow_loop_infinite"))
    arrow_skinny = Curve(data_from_file=get_curve_path("arrow_skinny"))
    arrow_small = Curve(data_from_file=get_curve_path("arrow_small"))
    arrow_suit_spades_beet = Curve(data_from_file=get_curve_path("arrow_suit_spades_beet"))
    arrow_symbol_refresh = Curve(data_from_file=get_curve_path("arrow_symbol_refresh"))
    arrow_symbol_return = Curve(data_from_file=get_curve_path("arrow_symbol_return"))
    arrow_two_compressing = Curve(data_from_file=get_curve_path("arrow_two_compressing"))
    asterisk = Curve(data_from_file=get_curve_path("asterisk"))
    circle = Curve(data_from_file=get_curve_path("circle"))
    circle_arrow = Curve(data_from_file=get_curve_path("circle_arrow"))
    circle_arrow_rotation_half = Curve(data_from_file=get_curve_path("circle_arrow_rotation_half"))
    circle_arrow_rotation_half_skinny = Curve(data_from_file=get_curve_path("circle_arrow_rotation_half_skinny"))
    circle_arrow_rotation_half_thick = Curve(data_from_file=get_curve_path("circle_arrow_rotation_half_thick"))
    circle_arrow_rotation_short = Curve(data_from_file=get_curve_path("circle_arrow_rotation_short"))
    circle_arrow_rotation_short_skinny = Curve(data_from_file=get_curve_path("circle_arrow_rotation_short_skinny"))
    circle_arrow_rotation_short_thick = Curve(data_from_file=get_curve_path("circle_arrow_rotation_short_thick"))
    circle_four_arrows = Curve(data_from_file=get_curve_path("circle_four_arrows"))
    circle_four_arrows_detached = Curve(data_from_file=get_curve_path("circle_four_arrows_detached"))
    circle_four_arrows_stylized = Curve(data_from_file=get_curve_path("circle_four_arrows_stylized"))
    circle_four_arrows_thick = Curve(data_from_file=get_curve_path("circle_four_arrows_thick"))
    circle_pipe = Curve(data_from_file=get_curve_path("circle_pipe"))
    circle_rotation_arrow_skinny = Curve(data_from_file=get_curve_path("circle_rotation_arrow_skinny"))
    circle_wavy_eight_sides = Curve(data_from_file=get_curve_path("circle_wavy_eight_sides"))
    circle_wavy_eight_sides_sun = Curve(data_from_file=get_curve_path("circle_wavy_eight_sides_sun"))
    circle_wavy_hips = Curve(data_from_file=get_curve_path("circle_wavy_hips"))
    circle_wavy_ten_sides = Curve(data_from_file=get_curve_path("circle_wavy_ten_sides"))
    concave_half_moon = Curve(data_from_file=get_curve_path("concave_half_moon"))
    concave_half_moon_handle = Curve(data_from_file=get_curve_path("concave_half_moon_handle"))
    concave_half_moon_skinny = Curve(data_from_file=get_curve_path("concave_half_moon_skinny"))
    creature_paw = Curve(data_from_file=get_curve_path("creature_paw"))
    creature_paw_four_toes = Curve(data_from_file=get_curve_path("creature_paw_four_toes"))
    creature_tentacle = Curve(data_from_file=get_curve_path("creature_tentacle"))
    cross_circle_heads = Curve(data_from_file=get_curve_path("cross_circle_heads"))
    cross_plus = Curve(data_from_file=get_curve_path("cross_plus"))
    cross_plus_small = Curve(data_from_file=get_curve_path("cross_plus_small"))
    gear_crown_eight_sides = Curve(data_from_file=get_curve_path("gear_crown_eight_sides"))
    gear_eight_sides = Curve(data_from_file=get_curve_path("gear_eight_sides"))
    gear_four_sides = Curve(data_from_file=get_curve_path("gear_four_sides"))
    gear_sixteen_sides = Curve(data_from_file=get_curve_path("gear_sixteen_sides"))
    gear_six_sides = Curve(data_from_file=get_curve_path("gear_six_sides"))
    gear_twelve_sides = Curve(data_from_file=get_curve_path("gear_twelve_sides"))
    gear_twenty_sides = Curve(data_from_file=get_curve_path("gear_twenty_sides"))
    human_ear = Curve(data_from_file=get_curve_path("human_ear"))
    human_face_side_view = Curve(data_from_file=get_curve_path("human_face_side_view"))
    human_fist = Curve(data_from_file=get_curve_path("human_fist"))
    human_foot_outline = Curve(data_from_file=get_curve_path("human_foot_outline"))
    human_foot_shoe_heel = Curve(data_from_file=get_curve_path("human_foot_shoe_heel"))
    human_hand_cartoon = Curve(data_from_file=get_curve_path("human_hand_cartoon"))
    human_hand_cartoon_swirl = Curve(data_from_file=get_curve_path("human_hand_cartoon_swirl"))
    human_hand_squared = Curve(data_from_file=get_curve_path("human_hand_squared"))
    human_head = Curve(data_from_file=get_curve_path("human_head"))
    human_mouth_lips = Curve(data_from_file=get_curve_path("human_mouth_lips"))
    icon_apple = Curve(data_from_file=get_curve_path("icon_apple"))
    icon_autodesk = Curve(data_from_file=get_curve_path("icon_autodesk"))
    icon_blender = Curve(data_from_file=get_curve_path("icon_blender"))
    icon_code_c_plus_plus = Curve(data_from_file=get_curve_path("icon_code_c_plus_plus"))
    icon_code_c_sharp = Curve(data_from_file=get_curve_path("icon_code_c_sharp"))
    icon_code_js_javascript = Curve(data_from_file=get_curve_path("icon_code_js_javascript"))
    icon_cursor = Curve(data_from_file=get_curve_path("icon_cursor"))
    icon_hand_click_index = Curve(data_from_file=get_curve_path("icon_hand_click_index"))
    icon_houdini_sidefx = Curve(data_from_file=get_curve_path("icon_houdini_sidefx"))
    icon_maya_autodesk_retro_word = Curve(data_from_file=get_curve_path("icon_maya_autodesk_retro_word"))
    icon_python = Curve(data_from_file=get_curve_path("icon_python"))
    icon_review_star = Curve(data_from_file=get_curve_path("icon_review_star"))
    icon_review_star_half = Curve(data_from_file=get_curve_path("icon_review_star_half"))
    icon_unity_logo = Curve(data_from_file=get_curve_path("icon_unity_logo"))
    icon_unity_logo_old = Curve(data_from_file=get_curve_path("icon_unity_logo_old"))
    icon_unreal_engine = Curve(data_from_file=get_curve_path("icon_unreal_engine"))
    icon_windows = Curve(data_from_file=get_curve_path("icon_windows"))
    icon_zbrush_maxon = Curve(data_from_file=get_curve_path("icon_zbrush_maxon"))
    line_two_points = Curve(data_from_file=get_curve_path("line_two_points"))
    locator = Curve(data_from_file=get_curve_path("locator"))
    locator_handle_xyz = Curve(data_from_file=get_curve_path("locator_handle_xyz"))
    locator_with_axis = Curve(data_from_file=get_curve_path("locator_with_axis"))
    peanut = Curve(data_from_file=get_curve_path("peanut"))
    pin = Curve(data_from_file=get_curve_path("pin"))
    pin_arrow_to_circle = Curve(data_from_file=get_curve_path("pin_arrow_to_circle"))
    pin_arrow_to_target = Curve(data_from_file=get_curve_path("pin_arrow_to_target"))
    pin_circle_to_arrow = Curve(data_from_file=get_curve_path("pin_circle_to_arrow"))
    pin_diamond_six_sides = Curve(data_from_file=get_curve_path("pin_diamond_six_sides"))
    pin_flag = Curve(data_from_file=get_curve_path("pin_flag"))
    pin_four_sides_flat_pyramids = Curve(data_from_file=get_curve_path("pin_four_sides_flat_pyramids"))
    pin_hollow_two_sides = Curve(data_from_file=get_curve_path("pin_hollow_two_sides"))
    pin_large = Curve(data_from_file=get_curve_path("pin_large"))
    pin_large_four_sides = Curve(data_from_file=get_curve_path("pin_large_four_sides"))
    pin_large_two_sides = Curve(data_from_file=get_curve_path("pin_large_two_sides"))
    pin_speech_bubble = Curve(data_from_file=get_curve_path("pin_speech_bubble"))
    pin_target_to_arrow = Curve(data_from_file=get_curve_path("pin_target_to_arrow"))
    primitive_cone = Curve(data_from_file=get_curve_path("primitive_cone"))
    primitive_cube = Curve(data_from_file=get_curve_path("primitive_cube"))
    primitive_hexagonal_tube = Curve(data_from_file=get_curve_path("primitive_hexagonal_tube"))
    primitive_pyramid = Curve(data_from_file=get_curve_path("primitive_pyramid"))
    primitive_pyramid_half = Curve(data_from_file=get_curve_path("primitive_pyramid_half"))
    primitive_tube = Curve(data_from_file=get_curve_path("primitive_tube"))
    primitive_tube_half = Curve(data_from_file=get_curve_path("primitive_tube_half"))
    primitive_tube_ring = Curve(data_from_file=get_curve_path("primitive_tube_ring"))
    rhombus = Curve(data_from_file=get_curve_path("rhombus"))
    rhombus_long = Curve(data_from_file=get_curve_path("rhombus_long"))
    sphere_dome = Curve(data_from_file=get_curve_path("sphere_dome"))
    sphere_four_directions = Curve(data_from_file=get_curve_path("sphere_four_directions"))
    sphere_half_arrow = Curve(data_from_file=get_curve_path("sphere_half_arrow"))
    sphere_half_double_arrows = Curve(data_from_file=get_curve_path("sphere_half_double_arrows"))
    sphere_half_double_arrows_skinny = Curve(data_from_file=get_curve_path("sphere_half_double_arrows_skinny"))
    sphere_half_four_arrows = Curve(data_from_file=get_curve_path("sphere_half_four_arrows"))
    sphere_half_top_four_arrows = Curve(data_from_file=get_curve_path("sphere_half_top_four_arrows"))
    sphere_half_two_arrows = Curve(data_from_file=get_curve_path("sphere_half_two_arrows"))
    sphere_joint = Curve(data_from_file=get_curve_path("sphere_joint"))
    sphere_joint_loc = Curve(data_from_file=get_curve_path("sphere_joint_loc"))
    sphere_joint_smooth = Curve(data_from_file=get_curve_path("sphere_joint_smooth"))
    sphere_two_directions = Curve(data_from_file=get_curve_path("sphere_two_directions"))
    spring = Curve(data_from_file=get_curve_path("spring"))
    spring_high_frequency = Curve(data_from_file=get_curve_path("spring_high_frequency"))
    spring_low_frequency = Curve(data_from_file=get_curve_path("spring_low_frequency"))
    square = Curve(data_from_file=get_curve_path("square"))
    square_corner_flat = Curve(data_from_file=get_curve_path("square_corner_flat"))
    square_corner_flat_skinny = Curve(data_from_file=get_curve_path("square_corner_flat_skinny"))
    swirl_five_spaces = Curve(data_from_file=get_curve_path("swirl_five_spaces"))
    swirl_thick_round_four_spaces = Curve(data_from_file=get_curve_path("swirl_thick_round_four_spaces"))
    swirl_thick_squared_four_spaces = Curve(data_from_file=get_curve_path("swirl_thick_squared_four_spaces"))
    swirl_two_spaces = Curve(data_from_file=get_curve_path("swirl_two_spaces"))
    switch_ik_fk_left = Curve(data_from_file=get_curve_path("switch_ik_fk_left"))
    switch_ik_fk_right = Curve(data_from_file=get_curve_path("switch_ik_fk_right"))
    symbol_attach_clip = Curve(data_from_file=get_curve_path("symbol_attach_clip"))
    symbol_attach_clip_squared = Curve(data_from_file=get_curve_path("symbol_attach_clip_squared"))
    symbol_bell = Curve(data_from_file=get_curve_path("symbol_bell"))
    symbol_bomb = Curve(data_from_file=get_curve_path("symbol_bomb"))
    symbol_bug_low_res_retro = Curve(data_from_file=get_curve_path("symbol_bug_low_res_retro"))
    symbol_bug_smoth = Curve(data_from_file=get_curve_path("symbol_bug_smoth"))
    symbol_camera_front = Curve(data_from_file=get_curve_path("symbol_camera_front"))
    symbol_camera_hollow = Curve(data_from_file=get_curve_path("symbol_camera_hollow"))
    symbol_camera_simple = Curve(data_from_file=get_curve_path("symbol_camera_simple"))
    symbol_canada_maple_leaf = Curve(data_from_file=get_curve_path("symbol_canada_maple_leaf"))
    symbol_card_suits_clover_clubs = Curve(data_from_file=get_curve_path("symbol_card_suits_clover_clubs"))
    symbol_card_suits_spades_pikes = Curve(data_from_file=get_curve_path("symbol_card_suits_spades_pikes"))
    symbol_code = Curve(data_from_file=get_curve_path("symbol_code"))
    symbol_computer_desktop = Curve(data_from_file=get_curve_path("symbol_computer_desktop"))
    symbol_controller_old = Curve(data_from_file=get_curve_path("symbol_controller_old"))
    symbol_control_pad = Curve(data_from_file=get_curve_path("symbol_control_pad"))
    symbol_cube_vertex_connected = Curve(data_from_file=get_curve_path("symbol_cube_vertex_connected"))
    symbol_danger_energy = Curve(data_from_file=get_curve_path("symbol_danger_energy"))
    symbol_diamond = Curve(data_from_file=get_curve_path("symbol_diamond"))
    symbol_dollar_sign_money = Curve(data_from_file=get_curve_path("symbol_dollar_sign_money"))
    symbol_emoji_one_hundred = Curve(data_from_file=get_curve_path("symbol_emoji_one_hundred"))
    symbol_emoji_poop = Curve(data_from_file=get_curve_path("symbol_emoji_poop"))
    symbol_emoji_robot = Curve(data_from_file=get_curve_path("symbol_emoji_robot"))
    symbol_emoji_skull = Curve(data_from_file=get_curve_path("symbol_emoji_skull"))
    symbol_emoji_smiley_face = Curve(data_from_file=get_curve_path("symbol_emoji_smiley_face"))
    symbol_emoji_smiley_ghost = Curve(data_from_file=get_curve_path("symbol_emoji_smiley_ghost"))
    symbol_emoji_smiley_missing = Curve(data_from_file=get_curve_path("symbol_emoji_smiley_missing"))
    symbol_emoji_thumbs_up = Curve(data_from_file=get_curve_path("symbol_emoji_thumbs_up"))
    symbol_eye = Curve(data_from_file=get_curve_path("symbol_eye"))
    symbol_eye_inactive = Curve(data_from_file=get_curve_path("symbol_eye_inactive"))
    symbol_female = Curve(data_from_file=get_curve_path("symbol_female"))
    symbol_filter = Curve(data_from_file=get_curve_path("symbol_filter"))
    symbol_flag_brazil = Curve(data_from_file=get_curve_path("symbol_flag_brazil"))
    symbol_flag_canada = Curve(data_from_file=get_curve_path("symbol_flag_canada"))
    symbol_flag_usa = Curve(data_from_file=get_curve_path("symbol_flag_usa"))
    symbol_flag_usa_simplified = Curve(data_from_file=get_curve_path("symbol_flag_usa_simplified"))
    symbol_focus_a = Curve(data_from_file=get_curve_path("symbol_focus_a"))
    symbol_four_loops = Curve(data_from_file=get_curve_path("symbol_four_loops"))
    symbol_game_controller_retro = Curve(data_from_file=get_curve_path("symbol_game_controller_retro"))
    symbol_heart = Curve(data_from_file=get_curve_path("symbol_heart"))
    symbol_key = Curve(data_from_file=get_curve_path("symbol_key"))
    symbol_letter = Curve(data_from_file=get_curve_path("symbol_letter"))
    symbol_lighting_energy_simple = Curve(data_from_file=get_curve_path("symbol_lighting_energy_simple"))
    symbol_lighting_energy_smooth = Curve(data_from_file=get_curve_path("symbol_lighting_energy_smooth"))
    symbol_locked = Curve(data_from_file=get_curve_path("symbol_locked"))
    symbol_magic_wand = Curve(data_from_file=get_curve_path("symbol_magic_wand"))
    symbol_male = Curve(data_from_file=get_curve_path("symbol_male"))
    symbol_misc_connected_four = Curve(data_from_file=get_curve_path("symbol_misc_connected_four"))
    symbol_misc_connected_three = Curve(data_from_file=get_curve_path("symbol_misc_connected_three"))
    symbol_music_two_notes = Curve(data_from_file=get_curve_path("symbol_music_two_notes"))
    symbol_music_two_notes_same = Curve(data_from_file=get_curve_path("symbol_music_two_notes_same"))
    symbol_omega = Curve(data_from_file=get_curve_path("symbol_omega"))
    symbol_paint_bucket = Curve(data_from_file=get_curve_path("symbol_paint_bucket"))
    symbol_pirate = Curve(data_from_file=get_curve_path("symbol_pirate"))
    symbol_plug = Curve(data_from_file=get_curve_path("symbol_plug"))
    symbol_puzzle = Curve(data_from_file=get_curve_path("symbol_puzzle"))
    symbol_question_mark = Curve(data_from_file=get_curve_path("symbol_question_mark"))
    symbol_radioactive = Curve(data_from_file=get_curve_path("symbol_radioactive"))
    symbol_radioactive_circle = Curve(data_from_file=get_curve_path("symbol_radioactive_circle"))
    symbol_snowflake = Curve(data_from_file=get_curve_path("symbol_snowflake"))
    symbol_snowflake_complex = Curve(data_from_file=get_curve_path("symbol_snowflake_complex"))
    symbol_snowflake_simplified = Curve(data_from_file=get_curve_path("symbol_snowflake_simplified"))
    symbol_speech_bubble = Curve(data_from_file=get_curve_path("symbol_speech_bubble"))
    symbol_sun_light = Curve(data_from_file=get_curve_path("symbol_sun_light"))
    symbol_sword = Curve(data_from_file=get_curve_path("symbol_sword"))
    symbol_tag_simple = Curve(data_from_file=get_curve_path("symbol_tag_simple"))
    symbol_tag_x = Curve(data_from_file=get_curve_path("symbol_tag_x"))
    symbol_three_hexagons = Curve(data_from_file=get_curve_path("symbol_three_hexagons"))
    symbol_uv_unwrapped = Curve(data_from_file=get_curve_path("symbol_uv_unwrapped"))
    symbol_wrench = Curve(data_from_file=get_curve_path("symbol_wrench"))
    symbol_zoom_in_plus = Curve(data_from_file=get_curve_path("symbol_zoom_in_plus"))
    target_aim_circle = Curve(data_from_file=get_curve_path("target_aim_circle"))
    target_aim_circle_drain = Curve(data_from_file=get_curve_path("target_aim_circle_drain"))
    target_circle = Curve(data_from_file=get_curve_path("target_circle"))
    target_circle_barrel_detailed = Curve(data_from_file=get_curve_path("target_circle_barrel_detailed"))
    target_squared = Curve(data_from_file=get_curve_path("target_squared"))
    target_squared_thick = Curve(data_from_file=get_curve_path("target_squared_thick"))
    triangle_pyramid_flat_four_arrows = Curve(data_from_file=get_curve_path("triangle_pyramid_flat_four_arrows"))
    triangle_pyramid_flat_two_arrows = Curve(data_from_file=get_curve_path("triangle_pyramid_flat_two_arrows"))


def add_thumbnail_metadata_attr_to_selection():
    """
    Adds projection attributes to the selected objects.
    These attributes are used to determine if metadata should be added to the curve file.
    This metadata is later used to automatically generate thumbnails for the curve.
    """
    selection = cmds.ls(selection=True, long=True) or []
    if not selection:
        logger.warning("Nothing selected!")
        return
    for obj in selection:
        path_axis_attr = f'{obj}.{PROJECTION_AXIS_KEY}'
        path_scale_attr = f'{obj}.{PROJECTION_SCALE_KEY}'
        path_fit_attr = f'{obj}.{PROJECTION_FIT_KEY}'
        initial_axis = None
        initial_scale = None
        initial_fit = None

        # Extract and delete if existing
        if cmds.objExists(path_axis_attr):
            cmds.setAttr(path_axis_attr, lock=False)
            initial_axis = cmds.getAttr(path_axis_attr)
            cmds.deleteAttr(path_axis_attr)
        if cmds.objExists(path_scale_attr):
            cmds.setAttr(path_scale_attr, lock=False)
            initial_scale = cmds.getAttr(path_scale_attr)
            cmds.deleteAttr(path_scale_attr)
        if cmds.objExists(path_fit_attr):
            cmds.setAttr(path_fit_attr, lock=False)
            initial_fit = cmds.getAttr(path_fit_attr)
            cmds.deleteAttr(path_fit_attr)

        # Create
        add_separator_attr(target_object=obj, attr_name='projectionAttributes')
        if not cmds.objExists(path_axis_attr):
            cmds.addAttr(obj, longName=PROJECTION_AXIS_KEY, at='enum', en="persp:x:y:z", keyable=True)
        if not cmds.objExists(path_scale_attr):
            cmds.addAttr(obj, longName=PROJECTION_SCALE_KEY, at='double', k=True, minValue=0)
        if not cmds.objExists(path_fit_attr):
            cmds.addAttr(obj, longName=PROJECTION_FIT_KEY, at='bool', k=True)

        # Set Extracted
        if initial_axis:
            cmds.setAttr(path_axis_attr, initial_axis)
        if initial_scale:
            cmds.setAttr(path_scale_attr, initial_scale)
        if initial_fit:
            cmds.setAttr(path_fit_attr, initial_fit)

    # Feedback
    sys.stdout.write('Metadata attributes were added to selection.\n')


def write_curve_files_from_selection(target_dir=None,
                                     projection_axis=None,
                                     projection_scale=None,
                                     projection_fit=None,
                                     overwrite=True):
    """
    Internal function used to extract curve files from selection
    Args:
        target_dir (str, optional): Path to a folder where the curve file is going to be written to.
        projection_axis (str, optional): Project axis stored as metadata in the curve file.
                                         Later used to automatically generate thumbnails
                                         Can be "x", "y", "z" or "persp". If set to "None", then default is "persp".
                                         Similar to UV projection, that's the direction where the camera will be.
                                         Note: If an attribute with the name "projection_axis" exists on the object,
                                         this function will attempt to retrieve it automatically.
        projection_scale (float, optional): Scale of the curve as a magnitude starting at the origin.
                                            Used to determine camera position when creating thumbnails.
                                            Bigger means that the camera will be further away.
                                            Note: If an attribute with the name "projection_scale" exists on the object,
                                            this function will attempt to retrieve it automatically.
                                            If set to None, then default is "5".
        projection_fit (bool, optional): Fit view metadata. Later used to determine if a fit view operation should run
                                         during thumbnail creation. Default is None/False (not created)
        overwrite (bool, optional): If active, it will overwrite existing files.
    """
    if not target_dir or not os.path.exists(target_dir):
        from gt.utils.system_utils import get_desktop_path
        target_dir = os.path.join(get_desktop_path(), "curves_data")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        from gt.utils.system_utils import open_file_dir
        open_file_dir(target_dir)

    for crv in cmds.ls(selection=True):
        curve = Curve(read_existing_curve=crv)
        # Get projection axis ----------------------------
        projection_axis_value = projection_axis
        if not projection_axis:
            if cmds.objExists(f'{crv}.{PROJECTION_AXIS_KEY}'):
                projection_axis_value = cmds.getAttr(f'{crv}.{PROJECTION_AXIS_KEY}', asString=True) or "persp"
            if not projection_axis_value:
                projection_axis_value = "persp"
        # Get projection scale ----------------------------
        projection_scale_value = projection_scale
        if not projection_scale:
            if cmds.objExists(f'{crv}.{PROJECTION_SCALE_KEY}'):
                projection_scale_value = cmds.getAttr(f'{crv}.{PROJECTION_SCALE_KEY}')
            if not projection_scale_value:
                projection_scale_value = 5
        # Get projection fit view ----------------------------
        projection_fit_value = projection_fit
        if not projection_fit:
            if cmds.objExists(f'{crv}.{PROJECTION_FIT_KEY}'):
                projection_fit_value = cmds.getAttr(f'{crv}.{PROJECTION_FIT_KEY}')
            if not projection_scale_value:
                projection_fit_value = None
        curve.add_to_metadata(key=PROJECTION_AXIS_KEY, value=projection_axis_value)  # x, y, z or persp
        curve.add_to_metadata(key=PROJECTION_SCALE_KEY, value=projection_scale_value)  # int
        curve.add_to_metadata(key=PROJECTION_FIT_KEY, value=projection_fit_value)  # bool
        file_path = os.path.join(target_dir, f'{crv}.crv')
        if os.path.exists(file_path) and not overwrite:
            sys.stdout.write(f'Existing file was skipped: "{file_path}".')
        else:
            curve.write_curve_to_file(file_path)
            sys.stdout.write(f'Curve exported to: "{file_path}". '
                             f'(Axis:{projection_axis_value}, Scale: {projection_scale_value})\n')


def generate_curve_thumbnail(target_dir, curve, image_format="jpg", line_width=5, rgb_color=(1, 1, 0.1)):
    """
    Generate curve thumbnail
    Args:
        target_dir (str): Path to a directory where the curve thumbnails will be stored.
        curve (Curve): The curve object to be displayed in the thumbnail
        image_format (str, optional): Format of the output file. Can be "jpg" or "png". Default: "jpg"
        line_width (float, optional): Width of the line used for the rendered curves.
        rgb_color (tuple, optional): A tuple representing red, green and blue values. e.g. (1, 0, 0) = Red
                                     This is used to set the color of the curve.
    Returns:
        str: Target directory
    """
    # Create New Scene
    cmds.file(new=True, force=True)

    # Unpack or Generate Projection Values
    projection_axis = "persp"
    projection_scale = 5
    projection_fit = False
    metadata = curve.get_metadata() or {}
    stored_projection_axis = metadata.get(PROJECTION_AXIS_KEY)
    stored_projection_scale = metadata.get(PROJECTION_SCALE_KEY)
    stored_projection_fit = metadata.get(PROJECTION_FIT_KEY)
    if stored_projection_axis and isinstance(stored_projection_axis, str):
        projection_axis = stored_projection_axis
    if stored_projection_scale:
        try:
            projection_scale = float(stored_projection_scale)
        except Exception as e:
            logger.debug(f'Unable to retrieve projection scale data. Failed to cast to integer. Issue: {str(e)}')
    if stored_projection_fit and isinstance(stored_projection_fit, bool):
        projection_fit = stored_projection_fit

    # Prepare Curve
    curve_name = curve.build()
    from gt.utils.color_utils import set_color_override_viewport
    set_color_override_viewport(obj=curve_name, rgb_color=rgb_color)
    for shape in cmds.listRelatives(curve_name, shapes=True) or []:
        cmds.setAttr(f'{shape}.lineWidth', line_width)

    # Create Camera
    orthographic = False
    if projection_axis == "y" or projection_axis == "x" or projection_axis == "z":
        orthographic = True
    cam_and_shape = cmds.camera(orthographic=orthographic)
    cam_name = cam_and_shape[0]
    cam_shape = cam_and_shape[1]
    cmds.lookThru(cam_shape)

    # Projection Scale
    translation_value = projection_scale*2
    # Projection Axis
    if projection_axis == "y":
        cmds.setAttr(f'{cam_name}.rx', -90)
        cmds.setAttr(f'{cam_name}.ty', translation_value)
        cmds.setAttr(f'{cam_name}.orthographicWidth', translation_value)
    elif projection_axis == "x":
        cmds.setAttr(f'{cam_name}.ry', 90)
        cmds.setAttr(f'{cam_name}.tx', translation_value)
        cmds.setAttr(f'{cam_name}.orthographicWidth', translation_value)
    elif projection_axis == "z":
        cmds.setAttr(f'{cam_name}.tz', translation_value)
        cmds.setAttr(f'{cam_name}.orthographicWidth', translation_value)
    else:  # Persp
        cmds.setAttr(f'{cam_name}.tx', 500)
        cmds.setAttr(f'{cam_name}.ty', 500)
        cmds.setAttr(f'{cam_name}.tz', 500)
        cmds.setAttr(f'{cam_name}.rx', -30)
        cmds.setAttr(f'{cam_name}.ry', 40)
        cmds.viewFit(all=True)

    if projection_fit:
        cmds.viewFit(all=True)

    # Setup Viewport and Render Image
    cmds.setAttr(f'hardwareRenderingGlobals.lineAAEnable', 1)
    cmds.setAttr(f'hardwareRenderingGlobals.multiSampleEnable', 1)
    cmds.setAttr(f'hardwareRenderingGlobals.multiSampleCount', 16)
    cmds.refresh()
    image_file = os.path.join(target_dir, f'{curve_name}.{image_format}')
    current_image_format = cmds.getAttr("defaultRenderGlobals.imageFormat")
    if image_format == "jpg" or image_format == "jpeg":
        cmds.setAttr("defaultRenderGlobals.imageFormat", 8)  # JPEG
    elif image_format == "png":
        cmds.setAttr("defaultRenderGlobals.imageFormat", 32)  # PNG
    cmds.playblast(completeFilename=image_file, startTime=True, endTime=True, forceOverwrite=True, showOrnaments=False,
                   viewer=0, format="image", qlt=100, p=100, framePadding=0, w=512, h=512)
    cmds.setAttr("defaultRenderGlobals.imageFormat", current_image_format)
    sys.stdout.write(f'Thumbnail Generated: "{image_file}". (Axis: "{projection_axis}", Scale: "{projection_scale}")')
    return target_dir


def generate_curves_thumbnails(target_dir=None, force=False):
    """
    Iterates through the Curves class attributes rendering a thumbnail for each one of the found Curves.
    At the end of the operation, it opens the target directory.
    Args:
        target_dir (str, optional): Path to a directory where the thumbnails will be stored.
                                    If not provided, they are rendered to Desktop/curves_thumbnails
        force (bool, optional): If activated, it will skip the unsaved changes detected dialog and run.
    """
    if cmds.file(q=True, modified=True) and not force:
        user_input = cmds.confirmDialog(title='Unsaved changes detected.',
                                        message='Unsaved changes detected.\n'
                                                'This operation will close the scene.\n'
                                                'Are you sure you want to proceed?\n'
                                                '(Unsaved changes will be lost)',
                                        button=['Yes', 'No'],
                                        defaultButton='No',
                                        cancelButton='No',
                                        dismissString='No',
                                        icon="warning")
        if user_input == 'No':
            logger.warning("Thumbnail generation cancelled.")
            return

    if not target_dir or not os.path.exists(target_dir):
        from gt.utils.system_utils import get_desktop_path
        target_dir = os.path.join(get_desktop_path(), "curves_thumbnails")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

    curve_attributes = vars(Curves)
    curve_keys = [attr for attr in curve_attributes if not (attr.startswith('__') and attr.endswith('__'))]
    for curve_key in curve_keys:
        curve_obj = getattr(Curves, curve_key)
        if not curve_obj:
            raise Exception(f'Missing curve: {curve_key}')
        if not curve_obj.shapes:
            raise Exception(f'Missing shapes for a curve: {curve_obj}')
        generate_curve_thumbnail(target_dir=target_dir, curve=curve_obj)
    from gt.utils.system_utils import open_file_dir
    open_file_dir(target_dir)
    cmds.file(new=True, force=True)


def print_code_for_crv_files(target_dir=None):
    """
    Internal function used to create Python code lines for every ".crv" file found in the "target_dir"
    It prints all lines, so they can be copied/pasted into the Curves class.
    Args:
        target_dir (str, optional): If provided, this path will be used instead of the default "utils/data/curves" path.\
    Returns:
        list: List of printed lines
    """
    if not target_dir:
        target_dir = DataDirConstants.DIR_CURVES
    printed_lines = []
    for file in os.listdir(target_dir):
        if file.endswith(".crv"):
            file_stripped = file.replace('.crv', '')
            line = f'{file_stripped} = Curve(data_from_file=get_curve_path("{file_stripped}"))'
            printed_lines.append(line)
            print(line)
    sys.stdout.write(f'Python lines for "Curves" class were printed. (If in Maya, open the script editor)')
    return printed_lines


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    # add_thumbnail_metadata_attr_to_selection()
    # print_code_for_crv_files()
    # write_curve_files_from_selection(target_dir=DataDirConstants.DIR_CURVES, overwrite=True)  # Extract Curve
    # generate_curves_thumbnails(target_dir=None, force=True)  # Generate Thumbnails - (target_dir=None = Desktop)

    test = ComplexCurves.scalable_arrow
    test.build()
    print(test.get_last_callable_output())

    pprint(out)
