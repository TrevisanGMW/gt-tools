"""
Curve Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attribute_utils import add_attr_double_three
from gt.utils.data_utils import read_json_dict, write_json
from gt.utils.transform_utils import Transform, Vector3
from gt.utils.naming_utils import get_short_name
from decimal import Decimal
import maya.cmds as cmds
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
CURVE_TYPE_NURBS = "nurbsCurve"
CURVE_TYPE_BEZIER = "bezierCurve"
CURVE_TYPES = [CURVE_TYPE_NURBS, CURVE_TYPE_BEZIER]
PROXY_ATTR_COLOR = "autoColor"


def combine_curves_list(curve_list, convert_bezier_to_nurbs=True):
    """
    Moves the shape objects of all elements in the provided input (curve_list) to a single group
    (essentially combining them under one transform)

    Args:
        curve_list (list): A string of strings with the name of the curves to be combined.
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


def add_snapping_shape(target_object):
    """
    Parents a locator shape to the target object so objects can be snapped to it.
    The parented locator shape has a scale of 0, so it doesn't change the look of the target object.
    Args:
        target_object (str): Name of the object to add the locator shape.
    Returns:
        Name of the added shape
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
    cmds.addAttr(obj, ln=PROXY_ATTR_COLOR, at='bool', k=True)
    cmds.setAttr(obj + "." + PROXY_ATTR_COLOR, 1)
    clr_auto_blend = cmds.createNode("blendColors", name=obj + "_clr_auto_blend")
    cmds.connectAttr(clr_auto_blend + ".output", obj + ".overrideColorRGB")
    cmds.connectAttr(clr_center_condition + ".outColor", clr_auto_blend + ".color1")
    cmds.connectAttr(obj + "." + PROXY_ATTR_COLOR, clr_auto_blend + ".blender")

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


def create_main_control(name):
    """
    Creates a main control with an arrow pointing to +Z (Direction character should be facing)

    Args:
        name (str): Name of the new control

    Returns:
        main_crv (str): Name of the generated control (in case it was different from what was provided)
    """
    main_crv_assembly = []
    main_crv_a = cmds.curve(name=name, p=[[-11.7, 0.0, 45.484], [-16.907, 0.0, 44.279], [-25.594, 0.0, 40.072],
                                          [-35.492, 0.0, 31.953], [-42.968, 0.0, 20.627], [-47.157, 0.0, 7.511],
                                          [-47.209, 0.0, -6.195], [-43.776, 0.0, -19.451], [-36.112, 0.0, -31.134],
                                          [-26.009, 0.0, -39.961], [-13.56, 0.0, -45.63], [0.0, 0.0, -47.66],
                                          [13.56, 0.0, -45.63], [26.009, 0.0, -39.961], [36.112, 0.0, -31.134],
                                          [43.776, 0.0, -19.451], [47.209, 0.0, -6.195], [47.157, 0.0, 7.511],
                                          [42.968, 0.0, 20.627], [35.492, 0.0, 31.953], [25.594, 0.0, 40.072],
                                          [16.907, 0.0, 44.279], [11.7, 0.0, 45.484]], d=3)
    main_crv_assembly.append(main_crv_a)
    main_crv_b = cmds.curve(name=name + 'direction',
                            p=[[-11.7, 0.0, 45.484], [-11.7, 0.0, 59.009], [-23.4, 0.0, 59.009], [0.0, 0.0, 82.409],
                               [23.4, 0.0, 59.009], [11.7, 0.0, 59.009], [11.7, 0.0, 45.484]], d=1)
    main_crv_assembly.append(main_crv_b)
    main_crv = combine_curves_list(main_crv_assembly)

    # Rename Shapes
    shapes = cmds.listRelatives(main_crv, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('main_ctrlCircle'))
    cmds.rename(shapes[1], '{0}Shape'.format('main_ctrlArrow'))

    return main_crv


def selected_curves_combine():
    """ Moves the shape objects of all selected curves under a single group (combining them) """
    errors = ''
    function_name = 'Combine Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl=True, absoluteName=True)
        valid_selection = True
        acceptable_types = ['nurbsCurve', 'bezierCurve']
        bezier_in_selection = []

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == 'bezierCurve':
                    bezier_in_selection.append(obj)
                if cmds.objectType(shape) not in acceptable_types:
                    valid_selection = False
                    cmds.warning('Make sure you selected only curves.')

        if valid_selection and len(selection) < 2:
            cmds.warning('You need to select at least two curves.')
            valid_selection = False

        if len(bezier_in_selection) > 0 and valid_selection:
            user_input = cmds.confirmDialog(title='Bezier curve detected!',
                                            message='A bezier curve was found in your selection.\n'
                                                    'Would you like to convert Bezier to NURBS before combining?',
                                            button=['Yes', 'No'],
                                            defaultButton='Yes',
                                            cancelButton='No',
                                            dismissString='No',
                                            icon="warning")
            if user_input == 'Yes':
                for obj in bezier_in_selection:
                    logger.debug(str(obj))
                    cmds.bezierCurveToNurbs()

        if valid_selection:
            shapes = cmds.listRelatives(shapes=True, fullPath=True)
            for obj in range(len(selection)):
                cmds.makeIdentity(selection[obj], apply=True, rotate=True, scale=True, translate=True)

            group = cmds.group(empty=True, world=True, name=selection[0])
            cmds.refresh()
            cmds.select(shapes[0])
            for obj in range(1, (len(shapes))):
                cmds.select(shapes[obj], add=True)

            cmds.select(group, add=True)
            cmds.parent(relative=True, shape=True)
            cmds.delete(selection)
            sys.stdout.write('\nSelected curves were combined into: "' + group + '".')
            cmds.select(group)

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
    """
    errors = ''
    acceptable_types = ['nurbsCurve', 'bezierCurve']
    function_name = 'Separate Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl=True, long=True)
        valid_selection = True

        curve_shapes = []
        parent_transforms = []

        if len(selection) < 1:
            valid_selection = False
            cmds.warning('You need to select at least one curve.')

        if valid_selection:
            new_transforms = []
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for shape in shapes:
                    if cmds.objectType(shape) in acceptable_types:
                        curve_shapes.append(shape)

            if len(curve_shapes) == 0:
                cmds.warning('You need to select at least one curve.')
            elif len(curve_shapes) > 1:
                for obj in curve_shapes:
                    parent = cmds.listRelatives(obj, parent=True) or []
                    for par in parent:
                        if par not in parent_transforms:
                            parent_transforms.append(par)
                        cmds.makeIdentity(par, apply=True, rotate=True, scale=True, translate=True)
                    group = cmds.group(empty=True, world=True, name=get_short_name(obj).replace('Shape', ''))
                    cmds.parent(obj, group, relative=True, shape=True)
                    new_transforms.append(group)
            else:
                cmds.warning('The selected curve contains only one shape.')

            for obj in parent_transforms:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                if cmds.objExists(obj) and cmds.objectType(obj) == 'transform' and len(shapes) == 0:
                    cmds.delete(obj)
            cmds.select(new_transforms)
            sys.stdout.write('\n' + str(len(curve_shapes)) + ' shapes extracted.')

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when separating the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


class Curve:
    def __init__(self,
                 name=None,
                 transform=None,
                 shapes=None,
                 read_curve_data=None,
                 read_curve_data_from_file=None):
        """
        Initializes a Curve object
        Args:
            name (str, optional): Curve transform name (shapes names are determined by the CurveShape objects)
            transform (Transform, optional): TRS Transform data used to determine initial position of the curve.
                                             If not provided, it's created at the origin.
            shapes (list, optional): A list of shapes (CurveShape) objects used to describe the curve visuals.
                                     Only optional so the curve can be generated using a file, ultimately required.
            read_curve_data (dict, optional): If provided, this dictionary is used to populate the curve data.
            read_curve_data_from_file (str, optional): Path to a JSON file describing the curve.
                                                       It reads the JSON content as a "read_curve_data" dictionary.
        """
        self.name = name
        self.transform = transform
        self.shapes = shapes

        if read_curve_data:
            self.set_data_from_dict(data_dict=read_curve_data)

        if read_curve_data_from_file:
            self.read_curve_from_file(file_path=read_curve_data_from_file)

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

    def create(self):
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
            generated_shapes.append(shape.create())
        generated_curve = combine_curves_list(generated_shapes)
        if self.name:
            generated_curve = cmds.rename(generated_curve, self.name)
        if self.transform:
            self.apply_curve_transform(generated_curve)
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

    def get_data_as_dict(self):
        """
        Gets the object values as a dictionary
        Returns:
            dict: The CurveShape object properties and its values.
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
            curve_shape_b.create()  # Creates the same curve

            curve_shape = CurveShape(read_existing_shape="my_curve")
            curve_shape.create()  # Creates the same curve provided above
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
                           f'Acceptable types: {CURVE_TYPES}')
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

    def create(self, replace_crv=None):
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
        parameters = {"point": self.points}
        # Extra elements -----------------------------------------
        named_parameters = {'degree': self.degree,
                            'periodic': self.periodic,
                            'knot': self.knot,
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
        return self.create(replace_crv=target_curve)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    sel = cmds.ls(selection=True)
    combine_curves_list(sel)
    pprint(out)
