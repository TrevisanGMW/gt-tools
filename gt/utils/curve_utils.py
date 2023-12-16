"""
Curve Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.naming_utils import get_short_name, NamingConstants
from gt.utils.attr_utils import add_separator_attr, set_attr
from gt.utils.data_utils import read_json_dict, write_json
from gt.utils.transform_utils import Transform, Vector3
from gt.utils.system_utils import DataDirConstants
from gt.utils.math_utils import remap_value
import maya.OpenMaya as OpenMaya
from gt.utils import attr_utils
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
CURVE_FILE_EXTENSION = "crv"
PROJECTION_AXIS_KEY = 'projectionAxis'
PROJECTION_SCALE_KEY = 'projectionScale'
PROJECTION_FIT_KEY = 'projectionFit'


def get_curve_file_path(file_name):
    """
    Get the path to a curve data file. This file should exist inside the utils/data/curves folder.
    Args:
        file_name (str): Name of the file. It doesn't need to contain its extension as it will always be "crv"
    Returns:
        str or None: Path to the curve description file. None if not found.
    """
    if not isinstance(file_name, str):
        logger.debug(f'Unable to retrieve curve file. Incorrect argument type: "{str(type(file_name))}".')
        return
    if not file_name.endswith(f'.{CURVE_FILE_EXTENSION}'):
        file_name = f'{file_name}.{CURVE_FILE_EXTENSION}'
    path_to_curve = os.path.join(DataDirConstants.DIR_CURVES, file_name)
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
        path_to_image = os.path.join(DataDirConstants.DIR_CURVES, f'{curve_name}.{ext}')
        if os.path.exists(path_to_image):
            return path_to_image


def get_curve(file_name, curve_dir=None):
    """
    Get the curve object from the path to a curve data file. This file should exist inside the utils/data/curves folder.
    Args:
        file_name (str): File name (not path). It doesn't need to contain its extension as it will always be "crv"
        curve_dir (str, optional): Path to the curve folder where it should look for the file. Default is None
                                   When not provided, it's assumed to be the package "curves" directory.
                                   e.g. "../gt/utils/data/curves"
    Returns:
        Curve or None: Curve object for a private curve. None if not found.
    """
    if not isinstance(file_name, str):
        logger.debug(f'Unable to retrieve curve file. Incorrect argument type: "{str(type(file_name))}".')
        return
    if not file_name.endswith(f'.{CURVE_FILE_EXTENSION}'):
        file_name = f'{file_name}.{CURVE_FILE_EXTENSION}'
    _curve_dir = DataDirConstants.DIR_CURVES
    if curve_dir and isinstance(curve_dir, str):
        if os.path.exists(curve_dir):
            _curve_dir = curve_dir
        else:
            logger.debug(f'Missing custom directory curve directory. Attempting to use package directory instead.')
    path_to_curve = os.path.join(_curve_dir, file_name)
    if os.path.exists(path_to_curve):
        return Curve(data_from_file=path_to_curve)


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
        valid_curve_transforms = set()

        for crv in curve_list:
            shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                    bezier_shapes.append(shape)
                    valid_curve_transforms.add(crv)
                if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                    nurbs_shapes.append(shape)
                    valid_curve_transforms.add(crv)

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

        attr_utils.freeze_channels(list(valid_curve_transforms))
        # Re-parent Shapes
        shapes = nurbs_shapes + bezier_shapes
        group = cmds.group(empty=True, world=True, name=curve_list[0])
        cmds.refresh()  # Without a refresh, Maya ignores the freeze operation
        for shape in shapes:
            cmds.select(clear=True)
            cmds.parent(shape, group, relative=True, shape=True)
        # Delete empty transforms
        for transform in valid_curve_transforms:
            children = cmds.listRelatives(transform, children=True) or []
            if not children and cmds.objExists(transform):
                cmds.delete(transform)
        # Clean-up
        combined_curve = cmds.rename(group, curve_list[0])
        if cmds.objExists(combined_curve):
            cmds.select(combined_curve)
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
        valid_curve_transforms = set()

        if len(selection) < 2:
            logger.warning('You need to select at least two curves.')
            return

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                    bezier_shapes.append(shape)
                    valid_curve_transforms.add(obj)
                if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                    nurbs_shapes.append(shape)
                    valid_curve_transforms.add(obj)

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
        attr_utils.freeze_channels(list(valid_curve_transforms))

        # Combine
        combined_crv = combine_curves_list(selection, convert_bezier_to_nurbs=convert_bezier_to_nurbs)
        sys.stdout.write(f'\nSelected curves were combined into: "{combined_crv}".')
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


def create_text(text, font="MS Shell Dlg 2"):
    """
    Creates a nurbs curve with the shape of the provided text.
    Args:
        text (str): Text to be converted into a curve.
        font (str, optional): Font used to create the text. e.g. "MS Shell Dlg 2".

    Returns:
        str: Name of the curve object.
    """
    if font and isinstance(font, str):
        cmds.textCurves(ch=0, t=text, font=font)
    else:
        cmds.textCurves(ch=0, t=text)
    cmds.ungroup()
    cmds.ungroup()
    curves = cmds.ls(sl=True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    shapes = curves[1:]
    cmds.select(shapes, r=True)
    cmds.pickWalk(d='Down')
    cmds.select(curves[0], tgl=True)
    cmds.parent(r=True, s=True)
    cmds.pickWalk(d='up')
    cmds.delete(shapes)
    cmds.xform(cp=True)
    _clean_text = text.lower().replace('/', '_')
    curve = cmds.rename(f'{_clean_text}_{NamingConstants.Suffix.CRV}')
    shapes = cmds.listRelatives(curve, shapes=True) or []
    for index, shape in enumerate(shapes):
        cmds.rename(shape, f'{curve}_{index+1:02d}Shape')
    print(' ')  # Clear Warnings
    return curve


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
            self.transform.apply_transform(target_object=generated_curve, world_space=True)
        cmds.select(clear=True)
        return generated_curve

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
            try:
                pos_data = transform_data.get("position")
                rot_data = transform_data.get("rotation")
                sca_data = transform_data.get("scale")
                position = Vector3(pos_data)
                rotation = Vector3(rot_data)
                scale = Vector3(sca_data)
                self.transform = Transform(position, rotation, scale)
            except Exception as e:
                logger.debug(f'Unable to read transform data. Issue: "{e}".')
        metadata = data_dict.get('metadata')
        if data_dict.get('metadata'):
            self.metadata = metadata

    def set_name(self, name):
        """
        Sets a new curve name. Useful when ingesting data from dictionary or file with undesired name.
        Args:
            name (str): New name to use on the curve.
        """
        if not name or not isinstance(name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(name))}"')
            return
        self.name = name

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

    def set_transform(self, transform):
        """
        Sets the transform for this curve object
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set curve transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.transform = transform

    def set_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the curve object.
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        if not self.transform:
            self.transform = Transform()
        self.transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the curve object.
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        if not self.transform:
            self.transform = Transform()
        self.transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the curve object.
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        if not self.transform:
            self.transform = Transform()
        self.transform.set_scale(x=x, y=y, z=z, xyz=xyz)

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

    def get_transform(self):
        """
        Gets the name property of the curve.

        Returns:
            Transform or None: The transform for this curve. None if it hasn't been initialized.
        """
        return self.transform

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

    def get_parameters(self):
        """
        Gets the Maya command parameters used to build the curve.
        Returns:
            dict or None: Dictionary with parameters or None if the curve is invalid.
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
        return parameters

    def build(self, replace_crv=None):
        """
        Use the loaded values of the object to generate/create a Maya curve.
        Since a shape can't exist on its own, a transform (group) is created for it.
        When a name is provided, it uses the name variable followed by "_transform" as the name of the transform group.
        Args:
            replace_crv (str): Name of the curve to replace
        Returns:
            str: Name of the generated shape or python code to generate the curve.
        """
        parameters = self.get_parameters()
        if not parameters:
            return
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
        A library of curve objects.
        Use "build()" to create them in Maya.
        """
    arrow_circle_to_head = get_curve(file_name="arrow_circle_to_head")
    arrow_content_moved = get_curve(file_name="arrow_content_moved")
    arrow_corner_broken = get_curve(file_name="arrow_corner_broken")
    arrow_curved_converge = get_curve(file_name="arrow_curved_converge")
    arrow_curved_return = get_curve(file_name="arrow_curved_return")
    arrow_direction_eight_sides = get_curve(file_name="arrow_direction_eight_sides")
    arrow_direction_four_sides = get_curve(file_name="arrow_direction_four_sides")
    arrow_direction_four_sides_skinny = get_curve(file_name="arrow_direction_four_sides_skinny")
    arrow_direction_two_sides = get_curve(file_name="arrow_direction_two_sides")
    arrow_direction_two_sides_skinny = get_curve(file_name="arrow_direction_two_sides_skinny")
    arrow_direction_two_sides_skinny_heads = get_curve(file_name="arrow_direction_two_sides_skinny_heads")
    arrow_direction_two_sides_small = get_curve(file_name="arrow_direction_two_sides_small")
    arrow_direction_two_sides_smaller = get_curve(file_name="arrow_direction_two_sides_smaller")
    arrow_eight_detailed = get_curve(file_name="arrow_eight_detailed")
    arrow_fletching_nock_flat = get_curve(file_name="arrow_fletching_nock_flat")
    arrow_four_maximize = get_curve(file_name="arrow_four_maximize")
    arrow_head_aim_flat_four_sides = get_curve(file_name="arrow_head_aim_flat_four_sides")
    arrow_head_candy_corn_smooth = get_curve(file_name="arrow_head_candy_corn_smooth")
    arrow_head_flat_aim = get_curve(file_name="arrow_head_flat_aim")
    arrow_head_flat_concave = get_curve(file_name="arrow_head_flat_concave")
    arrow_head_flat_triangle = get_curve(file_name="arrow_head_flat_triangle")
    arrow_head_flat_triangle_small = get_curve(file_name="arrow_head_flat_triangle_small")
    arrow_head_outline_no_base = get_curve(file_name="arrow_head_outline_no_base")
    arrow_head_stylized = get_curve(file_name="arrow_head_stylized")
    arrow_long = get_curve(file_name="arrow_long")
    arrow_loop_infinite = get_curve(file_name="arrow_loop_infinite")
    arrow_return_squared_back = get_curve(file_name="arrow_return_squared_back")
    arrow_return_squared_full = get_curve(file_name="arrow_return_squared_full")
    arrow_skinny = get_curve(file_name="arrow_skinny")
    arrow_suit_spades_beet = get_curve(file_name="arrow_suit_spades_beet")
    arrow_symbol_refresh = get_curve(file_name="arrow_symbol_refresh")
    arrow_symbol_refresh1 = get_curve(file_name="arrow_symbol_refresh1")
    arrow_symbol_return = get_curve(file_name="arrow_symbol_return")
    arrow_thick_small = get_curve(file_name="arrow_thick_small")
    arrow_two_compressing = get_curve(file_name="arrow_two_compressing")
    circle = get_curve(file_name="circle")
    circle_arrow = get_curve(file_name="circle_arrow")
    circle_arrow_rotation_half = get_curve(file_name="circle_arrow_rotation_half")
    circle_arrow_rotation_half_skinny = get_curve(file_name="circle_arrow_rotation_half_skinny")
    circle_arrow_rotation_half_thick = get_curve(file_name="circle_arrow_rotation_half_thick")
    circle_arrow_rotation_short = get_curve(file_name="circle_arrow_rotation_short")
    circle_arrow_rotation_short_skinny = get_curve(file_name="circle_arrow_rotation_short_skinny")
    circle_arrow_rotation_short_thick = get_curve(file_name="circle_arrow_rotation_short_thick")
    circle_flower_six_sides = get_curve(file_name="circle_flower_six_sides")
    circle_four_arrows = get_curve(file_name="circle_four_arrows")
    circle_four_arrows_detached = get_curve(file_name="circle_four_arrows_detached")
    circle_four_arrows_stylized = get_curve(file_name="circle_four_arrows_stylized")
    circle_four_arrows_thick = get_curve(file_name="circle_four_arrows_thick")
    circle_fractal_hexagon = get_curve(file_name="circle_fractal_hexagon")
    circle_pipe = get_curve(file_name="circle_pipe")
    circle_pizza_missing_slice = get_curve(file_name="circle_pizza_missing_slice")
    circle_rotation_arrow_skinny = get_curve(file_name="circle_rotation_arrow_skinny")
    circle_saw_detailed = get_curve(file_name="circle_saw_detailed")
    circle_saw_eight_sides = get_curve(file_name="circle_saw_eight_sides")
    circle_six_blobs = get_curve(file_name="circle_six_blobs")
    circle_sun_eight_triangles = get_curve(file_name="circle_sun_eight_triangles")
    circle_wavy_eight_sides = get_curve(file_name="circle_wavy_eight_sides")
    circle_wavy_eight_sides_sun = get_curve(file_name="circle_wavy_eight_sides_sun")
    circle_wavy_hips = get_curve(file_name="circle_wavy_hips")
    circle_wavy_ten_sides = get_curve(file_name="circle_wavy_ten_sides")
    coffee_mug_plate_side = get_curve(file_name="coffee_mug_plate_side")
    concave_half_moon = get_curve(file_name="concave_half_moon")
    concave_half_moon_handle = get_curve(file_name="concave_half_moon_handle")
    concave_half_moon_skinny = get_curve(file_name="concave_half_moon_skinny")
    creature_batman_symbol = get_curve(file_name="creature_batman_symbol")
    creature_bat_simplified = get_curve(file_name="creature_bat_simplified")
    creature_bat_simplified_two = get_curve(file_name="creature_bat_simplified_two")
    creature_bird_seagull_side = get_curve(file_name="creature_bird_seagull_side")
    creature_bird_side_stylized = get_curve(file_name="creature_bird_side_stylized")
    creature_bird_symbol_side = get_curve(file_name="creature_bird_symbol_side")
    creature_bull_side = get_curve(file_name="creature_bull_side")
    creature_butterfly_top = get_curve(file_name="creature_butterfly_top")
    creature_cat_side = get_curve(file_name="creature_cat_side")
    creature_cat_stylized_front = get_curve(file_name="creature_cat_stylized_front")
    creature_claw_horny_nail_bird = get_curve(file_name="creature_claw_horny_nail_bird")
    creature_cow_front = get_curve(file_name="creature_cow_front")
    creature_crab_top = get_curve(file_name="creature_crab_top")
    creature_deer_side = get_curve(file_name="creature_deer_side")
    creature_dinosaur_pterodactyl = get_curve(file_name="creature_dinosaur_pterodactyl")
    creature_dinosaur_trex = get_curve(file_name="creature_dinosaur_trex")
    creature_dog_face_front = get_curve(file_name="creature_dog_face_front")
    creature_dog_schnauzer = get_curve(file_name="creature_dog_schnauzer")
    creature_dog_side = get_curve(file_name="creature_dog_side")
    creature_dog_sitting_side = get_curve(file_name="creature_dog_sitting_side")
    creature_dragonfly_top = get_curve(file_name="creature_dragonfly_top")
    creature_dragon_bat_wing = get_curve(file_name="creature_dragon_bat_wing")
    creature_dragon_side = get_curve(file_name="creature_dragon_side")
    creature_dragon_side_body = get_curve(file_name="creature_dragon_side_body")
    creature_duck_stylized = get_curve(file_name="creature_duck_stylized")
    creature_evil_boss_blood = get_curve(file_name="creature_evil_boss_blood")
    creature_evil_cell_virus = get_curve(file_name="creature_evil_cell_virus")
    creature_fish_eating = get_curve(file_name="creature_fish_eating")
    creature_fish_side_small = get_curve(file_name="creature_fish_side_small")
    creature_frog_persp = get_curve(file_name="creature_frog_persp")
    creature_frog_webbed_feet_paw = get_curve(file_name="creature_frog_webbed_feet_paw")
    creature_gecko_lizard_top = get_curve(file_name="creature_gecko_lizard_top")
    creature_giraffe_persp = get_curve(file_name="creature_giraffe_persp")
    creature_gorilla = get_curve(file_name="creature_gorilla")
    creature_heads_hydra_dragon = get_curve(file_name="creature_heads_hydra_dragon")
    creature_horse_head_front = get_curve(file_name="creature_horse_head_front")
    creature_lion_side = get_curve(file_name="creature_lion_side")
    creature_llama_side = get_curve(file_name="creature_llama_side")
    creature_long_dragon = get_curve(file_name="creature_long_dragon")
    creature_lower_teeth_vampire = get_curve(file_name="creature_lower_teeth_vampire")
    creature_octopus = get_curve(file_name="creature_octopus")
    creature_paw = get_curve(file_name="creature_paw")
    creature_paw_claw = get_curve(file_name="creature_paw_claw")
    creature_paw_four_toes = get_curve(file_name="creature_paw_four_toes")
    creature_pig_side = get_curve(file_name="creature_pig_side")
    creature_rabbit_side = get_curve(file_name="creature_rabbit_side")
    creature_rabbit_side_outline = get_curve(file_name="creature_rabbit_side_outline")
    creature_reptile_lizard_side = get_curve(file_name="creature_reptile_lizard_side")
    creature_shark_teeth = get_curve(file_name="creature_shark_teeth")
    creature_sheep_side = get_curve(file_name="creature_sheep_side")
    creature_side_bird_dove = get_curve(file_name="creature_side_bird_dove")
    creature_snake_front = get_curve(file_name="creature_snake_front")
    creature_snake_side = get_curve(file_name="creature_snake_side")
    creature_snake_top = get_curve(file_name="creature_snake_top")
    creature_spider_top = get_curve(file_name="creature_spider_top")
    creature_tentacle = get_curve(file_name="creature_tentacle")
    creature_tentacle_inside_suckers = get_curve(file_name="creature_tentacle_inside_suckers")
    creature_tentacle_spiky = get_curve(file_name="creature_tentacle_spiky")
    creature_tentacle_suckers = get_curve(file_name="creature_tentacle_suckers")
    creature_three_heads_hydra = get_curve(file_name="creature_three_heads_hydra")
    creature_tutle_top = get_curve(file_name="creature_tutle_top")
    creature_unicorn = get_curve(file_name="creature_unicorn")
    creature_whale_side = get_curve(file_name="creature_whale_side")
    creature_wings_angel = get_curve(file_name="creature_wings_angel")
    creature_wings_fairy = get_curve(file_name="creature_wings_fairy")
    creature_wing_bat_dragon = get_curve(file_name="creature_wing_bat_dragon")
    creature_wing_thin_side = get_curve(file_name="creature_wing_thin_side")
    creature_wolf_side_dog = get_curve(file_name="creature_wolf_side_dog")
    creature_wolf_stylized = get_curve(file_name="creature_wolf_stylized")
    cross_circle_heads = get_curve(file_name="cross_circle_heads")
    cross_plus_add = get_curve(file_name="cross_plus_add")
    cross_plus_small = get_curve(file_name="cross_plus_small")
    dice_die_six_four = get_curve(file_name="dice_die_six_four")
    dice_die_six_give = get_curve(file_name="dice_die_six_give")
    dice_die_six_one = get_curve(file_name="dice_die_six_one")
    dice_die_six_six = get_curve(file_name="dice_die_six_six")
    dice_die_six_three = get_curve(file_name="dice_die_six_three")
    dice_die_six_two = get_curve(file_name="dice_die_six_two")
    extrude_profile_baseboard_a = get_curve(file_name="extrude_profile_baseboard_a")
    extrude_profile_faucet_pipe_a = get_curve(file_name="extrude_profile_faucet_pipe_a")
    four_leaf_clover = get_curve(file_name="four_leaf_clover")
    gear_crown_eight_sides = get_curve(file_name="gear_crown_eight_sides")
    gear_eight_sides = get_curve(file_name="gear_eight_sides")
    gear_eight_sides_smooth = get_curve(file_name="gear_eight_sides_smooth")
    gear_four_sides = get_curve(file_name="gear_four_sides")
    gear_sharp_smooth = get_curve(file_name="gear_sharp_smooth")
    gear_sixteen_sides = get_curve(file_name="gear_sixteen_sides")
    gear_six_sides = get_curve(file_name="gear_six_sides")
    gear_twelve_sides = get_curve(file_name="gear_twelve_sides")
    gear_twenty_sides = get_curve(file_name="gear_twenty_sides")
    human_arm_strong_side = get_curve(file_name="human_arm_strong_side")
    human_baby_symbol = get_curve(file_name="human_baby_symbol")
    human_ear = get_curve(file_name="human_ear")
    human_enlight_shine_man = get_curve(file_name="human_enlight_shine_man")
    human_eye_front_active = get_curve(file_name="human_eye_front_active")
    human_eye_front_inactive = get_curve(file_name="human_eye_front_inactive")
    human_eye_iris_closeup = get_curve(file_name="human_eye_iris_closeup")
    human_face_side = get_curve(file_name="human_face_side")
    human_foot_outline = get_curve(file_name="human_foot_outline")
    human_foot_shoe_heel = get_curve(file_name="human_foot_shoe_heel")
    human_foot_stylized = get_curve(file_name="human_foot_stylized")
    human_hand_fist_stylized = get_curve(file_name="human_hand_fist_stylized")
    human_hand_open_fingers = get_curve(file_name="human_hand_open_fingers")
    human_hand_raising = get_curve(file_name="human_hand_raising")
    human_hand_side = get_curve(file_name="human_hand_side")
    human_hand_simplified = get_curve(file_name="human_hand_simplified")
    human_hand_squared = get_curve(file_name="human_hand_squared")
    human_hand_stylized = get_curve(file_name="human_hand_stylized")
    human_head_gears_thinking = get_curve(file_name="human_head_gears_thinking")
    human_head_outline_front = get_curve(file_name="human_head_outline_front")
    human_head_outline_side = get_curve(file_name="human_head_outline_side")
    human_man_open_arms = get_curve(file_name="human_man_open_arms")
    human_man_running = get_curve(file_name="human_man_running")
    human_man_torso_front = get_curve(file_name="human_man_torso_front")
    human_man_walking = get_curve(file_name="human_man_walking")
    human_man_wc = get_curve(file_name="human_man_wc")
    human_man_ws_short = get_curve(file_name="human_man_ws_short")
    human_mouth_lips = get_curve(file_name="human_mouth_lips")
    human_skull_side = get_curve(file_name="human_skull_side")
    human_strong_man_front = get_curve(file_name="human_strong_man_front")
    human_symbol_eye_side = get_curve(file_name="human_symbol_eye_side")
    human_walking_dog = get_curve(file_name="human_walking_dog")
    human_woman_outline_front = get_curve(file_name="human_woman_outline_front")
    human_woman_running = get_curve(file_name="human_woman_running")
    human_woman_walking = get_curve(file_name="human_woman_walking")
    human_woman_wc = get_curve(file_name="human_woman_wc")
    icon_apple = get_curve(file_name="icon_apple")
    icon_autodesk = get_curve(file_name="icon_autodesk")
    icon_blender = get_curve(file_name="icon_blender")
    icon_code_c_plus_plus = get_curve(file_name="icon_code_c_plus_plus")
    icon_code_c_sharp = get_curve(file_name="icon_code_c_sharp")
    icon_code_js_javascript = get_curve(file_name="icon_code_js_javascript")
    icon_cursor = get_curve(file_name="icon_cursor")
    icon_github_octocat = get_curve(file_name="icon_github_octocat")
    icon_github_octocat_detailed = get_curve(file_name="icon_github_octocat_detailed")
    icon_godot_logo = get_curve(file_name="icon_godot_logo")
    icon_hand_click_index = get_curve(file_name="icon_hand_click_index")
    icon_houdini_sidefx = get_curve(file_name="icon_houdini_sidefx")
    icon_maya_autodesk_retro_word = get_curve(file_name="icon_maya_autodesk_retro_word")
    icon_python = get_curve(file_name="icon_python")
    icon_raspberry_pi = get_curve(file_name="icon_raspberry_pi")
    icon_review_star = get_curve(file_name="icon_review_star")
    icon_review_star_half = get_curve(file_name="icon_review_star_half")
    icon_splash = get_curve(file_name="icon_splash")
    icon_unity_logo = get_curve(file_name="icon_unity_logo")
    icon_unity_logo_retro = get_curve(file_name="icon_unity_logo_retro")
    icon_unreal_engine = get_curve(file_name="icon_unreal_engine")
    icon_windows = get_curve(file_name="icon_windows")
    icon_zbrush_maxon = get_curve(file_name="icon_zbrush_maxon")
    letter_asterisk = get_curve(file_name="letter_asterisk")
    line_two_points = get_curve(file_name="line_two_points")
    locator = get_curve(file_name="locator")
    locator_handle_arrows = get_curve(file_name="locator_handle_arrows")
    locator_handle_xyz = get_curve(file_name="locator_handle_xyz")
    locator_with_axis = get_curve(file_name="locator_with_axis")
    peanut = get_curve(file_name="peanut")
    pin = get_curve(file_name="pin")
    pin_arrow_to_circle = get_curve(file_name="pin_arrow_to_circle")
    pin_arrow_to_target = get_curve(file_name="pin_arrow_to_target")
    pin_circle_to_arrow = get_curve(file_name="pin_circle_to_arrow")
    pin_diamond_six_sides = get_curve(file_name="pin_diamond_six_sides")
    pin_flag = get_curve(file_name="pin_flag")
    pin_four_sides_flat_pyramids = get_curve(file_name="pin_four_sides_flat_pyramids")
    pin_hollow_two_sides = get_curve(file_name="pin_hollow_two_sides")
    pin_large = get_curve(file_name="pin_large")
    pin_large_four_sides = get_curve(file_name="pin_large_four_sides")
    pin_large_two_sides = get_curve(file_name="pin_large_two_sides")
    pin_speech_bubble = get_curve(file_name="pin_speech_bubble")
    pin_target_to_arrow = get_curve(file_name="pin_target_to_arrow")
    primitive_cone = get_curve(file_name="primitive_cone")
    primitive_cube = get_curve(file_name="primitive_cube")
    primitive_hexagonal_tube = get_curve(file_name="primitive_hexagonal_tube")
    primitive_pyramid = get_curve(file_name="primitive_pyramid")
    primitive_pyramid_half = get_curve(file_name="primitive_pyramid_half")
    primitive_tube = get_curve(file_name="primitive_tube")
    primitive_tube_half = get_curve(file_name="primitive_tube_half")
    primitive_tube_ring = get_curve(file_name="primitive_tube_ring")
    revolve_profile_bottle_a = get_curve(file_name="revolve_profile_bottle_a")
    revolve_profile_bowl_a = get_curve(file_name="revolve_profile_bowl_a")
    revolve_profile_bowl_b = get_curve(file_name="revolve_profile_bowl_b")
    revolve_profile_cork_a = get_curve(file_name="revolve_profile_cork_a")
    revolve_profile_faucet_base_a = get_curve(file_name="revolve_profile_faucet_base_a")
    revolve_profile_faucet_head_a = get_curve(file_name="revolve_profile_faucet_head_a")
    revolve_profile_plate_b = get_curve(file_name="revolve_profile_plate_b")
    revolve_profile_plate_c = get_curve(file_name="revolve_profile_plate_c")
    rhombus = get_curve(file_name="rhombus")
    rhombus_long = get_curve(file_name="rhombus_long")
    sphere_dome = get_curve(file_name="sphere_dome")
    sphere_four_directions = get_curve(file_name="sphere_four_directions")
    sphere_half_arrow = get_curve(file_name="sphere_half_arrow")
    sphere_half_double_arrows = get_curve(file_name="sphere_half_double_arrows")
    sphere_half_double_arrows_skinny = get_curve(file_name="sphere_half_double_arrows_skinny")
    sphere_half_four_arrows = get_curve(file_name="sphere_half_four_arrows")
    sphere_half_top_four_arrows = get_curve(file_name="sphere_half_top_four_arrows")
    sphere_half_two_arrows = get_curve(file_name="sphere_half_two_arrows")
    sphere_joint = get_curve(file_name="sphere_joint")
    sphere_joint_loc = get_curve(file_name="sphere_joint_loc")
    sphere_joint_smooth = get_curve(file_name="sphere_joint_smooth")
    sphere_two_directions = get_curve(file_name="sphere_two_directions")
    spring = get_curve(file_name="spring")
    spring_high_frequency = get_curve(file_name="spring_high_frequency")
    spring_low_frequency = get_curve(file_name="spring_low_frequency")
    square = get_curve(file_name="square")
    squares_connected = get_curve(file_name="squares_connected")
    square_corner_flat = get_curve(file_name="square_corner_flat")
    square_corner_flat_skinny = get_curve(file_name="square_corner_flat_skinny")
    swirl_five_spaces = get_curve(file_name="swirl_five_spaces")
    swirl_thick_round_four_spaces = get_curve(file_name="swirl_thick_round_four_spaces")
    swirl_thick_squared_four_spaces = get_curve(file_name="swirl_thick_squared_four_spaces")
    swirl_two_spaces = get_curve(file_name="swirl_two_spaces")
    switch_ik_fk_left = get_curve(file_name="switch_ik_fk_left")
    switch_ik_fk_right = get_curve(file_name="switch_ik_fk_right")
    symbol_attach_clip = get_curve(file_name="symbol_attach_clip")
    symbol_attach_clip_squared = get_curve(file_name="symbol_attach_clip_squared")
    symbol_batman_simplified = get_curve(file_name="symbol_batman_simplified")
    symbol_bell = get_curve(file_name="symbol_bell")
    symbol_bones_crossed = get_curve(file_name="symbol_bones_crossed")
    symbol_bones_crossed_bottom = get_curve(file_name="symbol_bones_crossed_bottom")
    symbol_bone_simple = get_curve(file_name="symbol_bone_simple")
    symbol_bug_low_res_retro = get_curve(file_name="symbol_bug_low_res_retro")
    symbol_bug_smoth = get_curve(file_name="symbol_bug_smoth")
    symbol_camera_front = get_curve(file_name="symbol_camera_front")
    symbol_camera_hollow = get_curve(file_name="symbol_camera_hollow")
    symbol_camera_simple = get_curve(file_name="symbol_camera_simple")
    symbol_canada_maple_leaf = get_curve(file_name="symbol_canada_maple_leaf")
    symbol_card_suits_clover_clubs = get_curve(file_name="symbol_card_suits_clover_clubs")
    symbol_card_suits_spades_pikes = get_curve(file_name="symbol_card_suits_spades_pikes")
    symbol_chain_constraint = get_curve(file_name="symbol_chain_constraint")
    symbol_chess_pawn_side = get_curve(file_name="symbol_chess_pawn_side")
    symbol_chess_tower_rook = get_curve(file_name="symbol_chess_tower_rook")
    symbol_code = get_curve(file_name="symbol_code")
    symbol_computer_desktop = get_curve(file_name="symbol_computer_desktop")
    symbol_connected_four = get_curve(file_name="symbol_connected_four")
    symbol_connected_three_webhook = get_curve(file_name="symbol_connected_three_webhook")
    symbol_controller_old = get_curve(file_name="symbol_controller_old")
    symbol_control_pad = get_curve(file_name="symbol_control_pad")
    symbol_cube_vertex_connected = get_curve(file_name="symbol_cube_vertex_connected")
    symbol_danger_energy = get_curve(file_name="symbol_danger_energy")
    symbol_diamond = get_curve(file_name="symbol_diamond")
    symbol_dollar_sign_money = get_curve(file_name="symbol_dollar_sign_money")
    symbol_eighteen_plus = get_curve(file_name="symbol_eighteen_plus")
    symbol_emoji_one_hundred = get_curve(file_name="symbol_emoji_one_hundred")
    symbol_emoji_poop = get_curve(file_name="symbol_emoji_poop")
    symbol_emoji_robot = get_curve(file_name="symbol_emoji_robot")
    symbol_emoji_skull = get_curve(file_name="symbol_emoji_skull")
    symbol_emoji_smiley_face = get_curve(file_name="symbol_emoji_smiley_face")
    symbol_emoji_smiley_ghost = get_curve(file_name="symbol_emoji_smiley_ghost")
    symbol_emoji_smiley_missing = get_curve(file_name="symbol_emoji_smiley_missing")
    symbol_emoji_thumbs_up = get_curve(file_name="symbol_emoji_thumbs_up")
    symbol_family_holding_hands = get_curve(file_name="symbol_family_holding_hands")
    symbol_female = get_curve(file_name="symbol_female")
    symbol_filter = get_curve(file_name="symbol_filter")
    symbol_flag_brazil = get_curve(file_name="symbol_flag_brazil")
    symbol_flag_canada = get_curve(file_name="symbol_flag_canada")
    symbol_flag_usa = get_curve(file_name="symbol_flag_usa")
    symbol_flag_usa_simplified = get_curve(file_name="symbol_flag_usa_simplified")
    symbol_flames = get_curve(file_name="symbol_flames")
    symbol_focus_a = get_curve(file_name="symbol_focus_a")
    symbol_food_fork_knife = get_curve(file_name="symbol_food_fork_knife")
    symbol_four_loops = get_curve(file_name="symbol_four_loops")
    symbol_frame_photo = get_curve(file_name="symbol_frame_photo")
    symbol_game_controller_retro = get_curve(file_name="symbol_game_controller_retro")
    symbol_heart = get_curve(file_name="symbol_heart")
    symbol_heart_squared_smooth = get_curve(file_name="symbol_heart_squared_smooth")
    symbol_hold_weapon_sword = get_curve(file_name="symbol_hold_weapon_sword")
    symbol_human_dress = get_curve(file_name="symbol_human_dress")
    symbol_human_man_touch = get_curve(file_name="symbol_human_man_touch")
    symbol_human_shirt = get_curve(file_name="symbol_human_shirt")
    symbol_icon_keyframe = get_curve(file_name="symbol_icon_keyframe")
    symbol_infinite = get_curve(file_name="symbol_infinite")
    symbol_key = get_curve(file_name="symbol_key")
    symbol_key_front_simple = get_curve(file_name="symbol_key_front_simple")
    symbol_key_side_detailed = get_curve(file_name="symbol_key_side_detailed")
    symbol_key_side_round = get_curve(file_name="symbol_key_side_round")
    symbol_key_side_squared = get_curve(file_name="symbol_key_side_squared")
    symbol_key_squared = get_curve(file_name="symbol_key_squared")
    symbol_kunai_knife = get_curve(file_name="symbol_kunai_knife")
    symbol_letter = get_curve(file_name="symbol_letter")
    symbol_lighting_energy_simple = get_curve(file_name="symbol_lighting_energy_simple")
    symbol_lighting_energy_smooth = get_curve(file_name="symbol_lighting_energy_smooth")
    symbol_lock_locked = get_curve(file_name="symbol_lock_locked")
    symbol_lock_unlocked = get_curve(file_name="symbol_lock_unlocked")
    symbol_magic_wand = get_curve(file_name="symbol_magic_wand")
    symbol_male = get_curve(file_name="symbol_male")
    symbol_man_fencing_sword = get_curve(file_name="symbol_man_fencing_sword")
    symbol_man_front = get_curve(file_name="symbol_man_front")
    symbol_man_strong = get_curve(file_name="symbol_man_strong")
    symbol_music_two_notes = get_curve(file_name="symbol_music_two_notes")
    symbol_music_two_notes_same = get_curve(file_name="symbol_music_two_notes_same")
    symbol_old_sign = get_curve(file_name="symbol_old_sign")
    symbol_omega = get_curve(file_name="symbol_omega")
    symbol_paint_bucket = get_curve(file_name="symbol_paint_bucket")
    symbol_parameters = get_curve(file_name="symbol_parameters")
    symbol_pirate = get_curve(file_name="symbol_pirate")
    symbol_pirate_skull_bones_crossed = get_curve(file_name="symbol_pirate_skull_bones_crossed")
    symbol_pirate_sword_skull = get_curve(file_name="symbol_pirate_sword_skull")
    symbol_plant_fin_grow = get_curve(file_name="symbol_plant_fin_grow")
    symbol_plug = get_curve(file_name="symbol_plug")
    symbol_plug_side = get_curve(file_name="symbol_plug_side")
    symbol_pointy_sun = get_curve(file_name="symbol_pointy_sun")
    symbol_puzzle = get_curve(file_name="symbol_puzzle")
    symbol_question_mark = get_curve(file_name="symbol_question_mark")
    symbol_radioactive = get_curve(file_name="symbol_radioactive")
    symbol_radioactive_circle = get_curve(file_name="symbol_radioactive_circle")
    symbol_shield_simple = get_curve(file_name="symbol_shield_simple")
    symbol_smelly_poop = get_curve(file_name="symbol_smelly_poop")
    symbol_snowflake = get_curve(file_name="symbol_snowflake")
    symbol_snowflake_complex = get_curve(file_name="symbol_snowflake_complex")
    symbol_snowflake_simplified = get_curve(file_name="symbol_snowflake_simplified")
    symbol_speech_bubble = get_curve(file_name="symbol_speech_bubble")
    symbol_squared_lock_locked = get_curve(file_name="symbol_squared_lock_locked")
    symbol_squared_lock_unlocked = get_curve(file_name="symbol_squared_lock_unlocked")
    symbol_sun_light = get_curve(file_name="symbol_sun_light")
    symbol_sword = get_curve(file_name="symbol_sword")
    symbol_tag_simple = get_curve(file_name="symbol_tag_simple")
    symbol_tag_x = get_curve(file_name="symbol_tag_x")
    symbol_tech_fan = get_curve(file_name="symbol_tech_fan")
    symbol_tech_fan_case = get_curve(file_name="symbol_tech_fan_case")
    symbol_three_hexagons = get_curve(file_name="symbol_three_hexagons")
    symbol_tool_hammer = get_curve(file_name="symbol_tool_hammer")
    symbol_uv_unwrapped = get_curve(file_name="symbol_uv_unwrapped")
    symbol_virus_proteins = get_curve(file_name="symbol_virus_proteins")
    symbol_wand_magic_star = get_curve(file_name="symbol_wand_magic_star")
    symbol_wc_woman_front = get_curve(file_name="symbol_wc_woman_front")
    symbol_woman_arms_up = get_curve(file_name="symbol_woman_arms_up")
    symbol_wrench = get_curve(file_name="symbol_wrench")
    symbol_zoom_in_plus = get_curve(file_name="symbol_zoom_in_plus")
    target_aim_circle = get_curve(file_name="target_aim_circle")
    target_aim_circle_drain = get_curve(file_name="target_aim_circle_drain")
    target_circle = get_curve(file_name="target_circle")
    target_circle_barrel_detailed = get_curve(file_name="target_circle_barrel_detailed")
    target_squared = get_curve(file_name="target_squared")
    target_squared_thick = get_curve(file_name="target_squared_thick")
    target_square_circle_thick = get_curve(file_name="target_square_circle_thick")
    target_wheel_helm_complex = get_curve(file_name="target_wheel_helm_complex")
    target_wheel_helm_simple = get_curve(file_name="target_wheel_helm_simple")
    tool_dial_caliper_measure = get_curve(file_name="tool_dial_caliper_measure")
    tool_grass_cutter = get_curve(file_name="tool_grass_cutter")
    tool_magnet = get_curve(file_name="tool_magnet")
    tool_pair_scissors = get_curve(file_name="tool_pair_scissors")
    tool_pickaxe = get_curve(file_name="tool_pickaxe")
    tool_robot_arm_side = get_curve(file_name="tool_robot_arm_side")
    tool_ruler = get_curve(file_name="tool_ruler")
    tool_screwdriver = get_curve(file_name="tool_screwdriver")
    tool_shovel = get_curve(file_name="tool_shovel")
    tool_wrench = get_curve(file_name="tool_wrench")
    triangle_pyramid_flat_four_arrows = get_curve(file_name="triangle_pyramid_flat_four_arrows")
    triangle_pyramid_flat_two_arrows = get_curve(file_name="triangle_pyramid_flat_two_arrows")
    ui_attention_exclamation = get_curve(file_name="ui_attention_exclamation")
    weapon_battle_axe_side = get_curve(file_name="weapon_battle_axe_side")
    weapon_dagger_top = get_curve(file_name="weapon_dagger_top")
    weapon_grenade_launcher = get_curve(file_name="weapon_grenade_launcher")
    weapon_hook_lance_teeth_thorn = get_curve(file_name="weapon_hook_lance_teeth_thorn")
    weapon_mp4_rifle = get_curve(file_name="weapon_mp4_rifle")
    weapon_pistols_crossed = get_curve(file_name="weapon_pistols_crossed")
    weapon_pistol_modern_side = get_curve(file_name="weapon_pistol_modern_side")
    weapon_pistol_side = get_curve(file_name="weapon_pistol_side")
    weapon_rifle_modern = get_curve(file_name="weapon_rifle_modern")
    weapon_shrunken_five = get_curve(file_name="weapon_shrunken_five")
    weapon_shrunken_four = get_curve(file_name="weapon_shrunken_four")
    weapon_shrunken_four_blades = get_curve(file_name="weapon_shrunken_four_blades")
    weapon_sword_rapier = get_curve(file_name="weapon_sword_rapier")
    weapon_symbol_bomb = get_curve(file_name="weapon_symbol_bomb")
    weapon_symbol_bomb_two = get_curve(file_name="weapon_symbol_bomb_two")
    weapon_symbol_grenade = get_curve(file_name="weapon_symbol_grenade")


# ------------------------------ Curves Class Utilities Start ------------------------------


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


def generate_package_curve_thumbnail(target_dir, curve, image_format="jpg", line_width=5, rgb_color=(1, 1, 0.1)):
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
    from gt.utils.color_utils import set_color_viewport
    set_color_viewport(obj_list=curve_name, rgb_color=rgb_color)
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


def generate_package_curves_thumbnails(target_dir=None, force=False):
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
        generate_package_curve_thumbnail(target_dir=target_dir, curve=curve_obj)
    from gt.utils.system_utils import open_file_dir
    open_file_dir(target_dir)
    cmds.file(new=True, force=True)


def print_code_for_crv_files(target_dir=None, ignore_private=True, use_output_window=False):
    """
    Internal function used to create Python code lines for every ".crv" file found in the "target_dir"
    It prints all lines, so they can be copied/pasted into the Curves class.
    Curves starting with underscore "_" will be ignored as these are considered private curves (usually used for ctrls)
    Args:
        target_dir (str, optional): If provided, this path will be used instead of the default "utils/data/curves" path.
        ignore_private (bool, optional): If active, curve files starting with "_" will be not be included.
        use_output_window (bool, optional): If active, an output window will be used instead of simple prints.
    Returns:
        str: Generated code (lines)
    """
    if not target_dir:
        target_dir = DataDirConstants.DIR_CURVES
    print_lines = []
    for file in os.listdir(target_dir):
        if file.endswith(".crv"):
            file_stripped = file.replace('.crv', '')
            line = f'{file_stripped} = get_curve(file_name="{file_stripped}")'
            if file.startswith("_") and ignore_private:
                continue
            print_lines.append(line)

    output = ''
    for line in print_lines:
        output += f'{line}\n'
    if output.endswith('\n'):  # Removes unnecessary new line at the end
        output = output[:-1]

    if use_output_window:
        from gt.ui.python_output_view import PythonOutputView
        from gt.ui import qt_utils

        with qt_utils.QtApplicationContext():
            window = PythonOutputView()  # View
            window.set_python_output_text(text=output)
            window.show()
        sys.stdout.write(f'Python lines for "Curves" class were printed to output window.')
    else:
        print("_"*80)
        print(output)
        print("_"*80)
        sys.stdout.write(f'Python lines for "Curves" class were printed. (If in Maya, open the script editor)')
    return output

# ------------------------------ Curves Collection Utilities End ------------------------------


def add_shape_scale_cluster(obj, scale_driver_attr, reset_pivot=True):
    """
    Creates a cluster to control the scale of the provided curve.

    Parameters:
    curve (str): Name of the curve.
    scale_driver_attr (str): The object name and attribute used to drive the scale.
                             Example: "curveName.locatorScale"
                             This attribute will control the scale of the curve shape.
    create_driver (bool, optional): If active, it will create a group and snap to the object instead of using

    Returns:
        str or None: Cluster handle if successful, None if it failed.
    """
    cluster = cmds.cluster(f'{obj}.cv[*]', name=f'{get_short_name(obj)}_LocScale')
    if not cluster:
        logger.debug(f'Failed to create scale cluster. Missing "{str(obj)}".')
        return
    else:
        cluster_handle = cluster[1]
        if reset_pivot:
            set_attr(obj_list=cluster_handle,
                     attr_list=["scalePivotX", "scalePivotY", "scalePivotZ",
                                "rotatePivotX", "rotatePivotY", "rotatePivotZ"],
                     value=0)
        cmds.setAttr(f'{cluster_handle}.v', 0)
        cmds.connectAttr(scale_driver_attr, f'{cluster_handle}.sx')
        cmds.connectAttr(scale_driver_attr, f'{cluster_handle}.sy')
        cmds.connectAttr(scale_driver_attr, f'{cluster_handle}.sz')
        return cluster_handle


def filter_curve_shapes(obj_list, get_transforms=False):
    """
    Filters transforms and shapes from object list into a list of acceptable objects (only "Nurbs" or "Bezier" curves)
    Args:
        obj_list (list): List of objects to filter.
        get_transforms (bool, optional): If active, it will return the transforms of valid objects. If False, shapes.
    Returns:
        list: Filtered shapes (not the transforms, but the shapes) - (only "Nurbs" or "Bezier" curves)
    """
    nurbs_shapes = []
    bezier_shapes = []
    valid_curve_transforms = set()

    for obj in obj_list:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        for shape in shapes:
            if cmds.objectType(shape) == CURVE_TYPE_BEZIER:
                bezier_shapes.append(shape)
                valid_curve_transforms.add(obj)
            if cmds.objectType(shape) == CURVE_TYPE_NURBS:
                nurbs_shapes.append(shape)
                valid_curve_transforms.add(obj)
    if get_transforms:
        return list(valid_curve_transforms)
    return nurbs_shapes + bezier_shapes


def get_python_shape_code(crv_list):
    """
    Extracts the Python code necessary to reshape an existing curve. (its current state)
    Args:
        crv_list (list, str): Transforms carrying curve shapes inside them (nurbs or bezier)
                              Strings are automatically converted to a list with a single item.

    Returns:
        str: Python code with the current state of the selected curves (their shape)
    """
    shapes = filter_curve_shapes(obj_list=crv_list)
    output = ''

    for shape in shapes:
        curve_data = zip(cmds.ls(f'{shape}.cv[*]', flatten=True), cmds.getAttr(f'{shape}.cv[*]'))
        curve_data_list = list(curve_data)
        # Assemble command:
        if curve_data_list:
            output += '# Shape state for "' + str(shape).split('|')[-1] + '":\n'
            output += 'for cv in ' + str(curve_data_list) + ':\n'
            output += '    cmds.xform(cv[0], os=True, t=cv[1])\n\n'

    if output.endswith('\n\n'):  # Removes unnecessary spaces at the end
        output = output[:-2]
    return output


def get_python_curve_code(crv_list):
    """
    Extracts the Python code necessary to reshape an existing curve. (its current state)
    Args:
        crv_list (list, str): Transforms carrying curve shapes inside them (nurbs or bezier)
                              Strings are automatically converted to a list with a single item.

    Returns:
        str: Python code with the current state of the selected curves (their shape)
    """
    shapes = filter_curve_shapes(obj_list=crv_list)
    output = ''

    for shape in shapes:
        shape_obj = CurveShape(read_existing_shape=shape)
        parameters = shape_obj.get_parameters()
        args = ", ".join(f"{key}={repr(value)}" for key, value in parameters.items())
        output += '# Curve data for "' + str(shape).split('|')[-1] + '":\n'
        output += f'cmds.curve({args})\n\n'

    if output.endswith('\n\n'):  # Removes unnecessary spaces at the end
        output = output[:-2]
    return output


def set_curve_width(obj_list, line_width=-1):
    """
    Changes the curve shape width (lineWidth) of all shapes found under a transform or the shape directly.
    Args:
        obj_list (str, list): A list of transform  or curve shapes to have their lineWidth attributes updated.
        line_width (float, int, optional): New line width. Default -1 (Same as Maya's default)
    Returns:
        list: A list of affected shapes.
    """
    shapes = []
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    if not isinstance(obj_list, list):
        logger.debug(f'Unable to set curve width. Input must be a list of strings.')
        return
    for obj in obj_list:
        if obj and isinstance(obj, str) and cmds.objExists(obj):
            if cmds.objectType(obj) in CURVE_TYPES:
                shapes.append(obj)
            if cmds.objectType(obj) == "transform":
                shapes += cmds.listRelatives(obj, shapes=True, fullPath=True, typ=CURVE_TYPES) or []
    affected_shapes = []
    for shape in shapes:
        try:
            cmds.setAttr(f'{shape}.lineWidth', line_width)
            affected_shapes.append(shape)
        except Exception as e:
            logger.debug(f'Unable to set lineWidth for "{shape}". Issue: {str(e)}')
    return affected_shapes


def create_connection_line(object_a, object_b, constraint=True):
    """
    Creates a curve attached to two objects, often used to better visualize hierarchies

    Args:
        object_a (str): Name of the object driving the start of the curve
        object_b (str): Name of the object driving end of the curve (usually a child of object_a)
        constraint (bool, optional): If True, it will constrain the clusters to "object_a" and "object_b".

    Returns:
        tuple: A list with the generated curve, cluster_a, and cluster_b

    """
    crv = cmds.curve(p=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], d=1)
    cluster_a = cmds.cluster(crv + '.cv[0]')
    cluster_b = cmds.cluster(crv + '.cv[1]')

    if cmds.objExists(object_a):
        cmds.pointConstraint(object_a, cluster_a[1])

    if cmds.objExists(object_a):
        cmds.pointConstraint(object_b, cluster_b[1])

    object_a_short = object_a.split('|')[-1]
    object_b_short = object_b.split('|')[-1]
    crv = cmds.rename(crv, object_a_short + '_to_' + object_b_short)
    cluster_a = cmds.rename(cluster_a[1], object_a_short + '_cluster')
    cluster_b = cmds.rename(cluster_b[1], object_b_short + '_cluster')
    cmds.setAttr(cluster_a + '.v', 0)
    cmds.setAttr(cluster_b + '.v', 0)

    if constraint and cmds.objExists(object_a):
        cmds.pointConstraint(object_a, cluster_a)

    if constraint and cmds.objExists(object_b):
        cmds.pointConstraint(object_b, cluster_b)

    shapes = cmds.listRelatives(crv, s=True, f=True) or []
    cmds.setAttr(shapes[0] + ".lineWidth", 3)

    return crv, cluster_a, cluster_b


def get_positions_from_curve(curve, count, periodic=True, space="uv", normalized=True):
    """
    Retrieves positions along a curve based on specified parameters.

    Args:
        curve (str): The name of the curve to sample positions from.
        count (int): The number of positions to retrieve along the curve.
        periodic (bool, optional): If True, considers the curve as "periodic", otherwise "open".
        space (str, optional): The coordinate space for the positions ('uv' or 'world'). Defaults to "uv".
        normalized (bool, optional): If True, normalizes the positions between 0 and 1. Defaults to True.

    Returns:
        list: A list of positions along the curve.
        e.g. [0, 0.5, 1]  # space="uv"
        e.g. [[0, 0, 0], [0, 0.5, 0], [0, 1, 0]]  # space="world"

    Example:
        positions = get_position_from_curve_length("curve1", 10, periodic=True, space="world", normalized=True)
    """
    if periodic:
        divide_value = count
    else:
        divide_value = count - 1
    if divide_value == 0:
        divide_value = 1

    dag = OpenMaya.MDagPath()
    obj = OpenMaya.MObject()
    crv = OpenMaya.MSelectionList()
    crv.add(curve)
    crv.getDagPath(0, dag, obj)

    crv_fn = OpenMaya.MFnNurbsCurve(dag)
    length = crv_fn.length()
    pos_list = [crv_fn.findParamFromLength(index * ((1/float(divide_value)) * length)) for index in range(count)]

    if space == "world":
        output_list = []
        space = OpenMaya.MSpace.kWorld
        point = OpenMaya.MPoint()
        for pos in pos_list:
            crv_fn.getPointAtParam(pos, point, space)
            output_list.append([point[0], point[1], point[2]])  # X, Y, Z
    elif normalized is True:
        max_v = cmds.getAttr(curve + ".minMaxValue.maxValue")
        min_v = cmds.getAttr(curve + ".minMaxValue.minValue")
        output_list = [remap_value(value=pos, old_range=[min_v, max_v], new_range=[0, 1]) for pos in pos_list]
    else:
        output_list = pos_list
    return output_list


def rescale_curve(curve_transform, scale):
    """
    Rescales the control points of the specified curve transform.

    Args:
        curve_transform (str): The name of the curve transform to be rescaled.
        scale (float): The scaling factor to be applied uniformly to the control points.

    Example:
        rescale_curve("myCurve", 2.0)
    """
    if not curve_transform or not cmds.objExists(curve_transform):
        logger.debug(f'Unable to re-scale')
        return
    all_shapes = cmds.listRelatives(curve_transform, shapes=True) or []
    crv_shapes = [shape for shape in all_shapes if cmds.objectType(shape) in CURVE_TYPES]
    for shape in crv_shapes:
        cvs_count = cmds.getAttr(f"{shape}.controlPoints", size=True)
        cmds.scale(scale, scale, scale, f"{shape}.cv[0:{cvs_count - 1}]", relative=True, objectCenterPivot=True)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # add_thumbnail_metadata_attr_to_selection()
    # print_code_for_crv_files()
    # write_curve_files_from_selection(target_dir=DataDirConstants.DIR_CURVES, overwrite=True)  # Extract Curve
    # generate_curves_thumbnails(target_dir=None, force=True)  # Generate Thumbnails - (target_dir=None = Desktop)
