"""
Curve Utilities
github.com/TrevisanGMW/gt-tools
"""
from decimal import Decimal

from gt.utils.attribute_utils import add_attr_double_three
from gt.utils.naming_utils import get_short_name
from gt.utils.transform_utils import Transform
import maya.cmds as cmds
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
CURVE_TYPES = ["nurbsCurve", "bezierCurve"]
PROXY_ATTR_COLOR = "autoColor"


def combine_curves_list(curve_list):
    """
    This is a modified version of the GT Utility "Combine Curves"
    It moves the shape objects of all elements in the provided input (curve_list) to a single group (combining them)
    This version was changed to accept a list of objects (instead of selection)

    Args:
        curve_list (list): A string of strings with the name of the curves to be combined.

    """
    errors = ''
    function_name = 'Combine Curves List'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True
        acceptable_types = ['nurbsCurve', 'bezierCurve']
        bezier_in_selection = []

        for crv in curve_list:
            shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == 'bezierCurve':
                    bezier_in_selection.append(crv)
                if cmds.objectType(shape) not in acceptable_types:
                    valid_selection = False
                    cmds.warning('Make sure you selected only curves.')

        if valid_selection and len(curve_list) < 2:
            cmds.warning('You need to select at least two curves.')
            valid_selection = False

        if len(bezier_in_selection) > 0 and valid_selection:
            message = 'A bezier curve was found in your selection.' \
                      '\nWould you like to convert Bezier to NURBS before combining?'
            user_input = cmds.confirmDialog(title='Bezier curve detected!',
                                            message=message,
                                            button=['Yes', 'No'],
                                            defaultButton='Yes',
                                            cancelButton='No',
                                            dismissString='No',
                                            icon='warning')
            if user_input == 'Yes':
                for bezier in bezier_in_selection:
                    logger.debug(str(bezier))
                    cmds.bezierCurveToNurbs()

        if valid_selection:
            shapes = []
            for crv in curve_list:
                extracted_shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
                for ext_shape in extracted_shapes:
                    shapes.append(ext_shape)

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
        errors += str(exception) + '\n'
        cmds.warning('An error occurred when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


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
                 file_name=None,
                 existing_curve=None,
                 name=None,
                 points=None,
                 degree=None,
                 knot=None,
                 periodic=None):
        self.file_name = file_name


class CurveShape:
    # The x, y, z position of a point. "linear" means that this flag can take values with units.
    # The degree of the new curve. Default is 3. Note that you need (degree+1) curve points to create a visible curve span. eg. you must place 4 points for a degree 3 curve.
    # A knot value in a knot vector. One flag per knot value. There must be (numberOfPoints + degree - 1) knots and the knot vector must be non-decreasing.
    # If on, creates a curve that is periodic. Default is off.
    def __init__(self,
                 name=None,
                 points=None,
                 degree=None,
                 knot=None,
                 periodic=None,
                 existing_curve_data=None,
                 extract_existing_shape=None):
        self.name = name
        self.points = points
        self.degree = degree
        self.knot = knot
        self.periodic = periodic

        if extract_existing_shape:
            self.extract_data_from_existing_curve_shape(crv_shape=extract_existing_shape)

        if existing_curve_data:
            self.set_data_from_dict(data_dict=existing_curve_data)

    def is_curve_shape_valid(self):
        if not self.points:
            logger.warning(f'Invalid curve shape. Missing points.')
            return False
        return True

    def extract_data_from_existing_curve_shape(self, crv_shape):
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
        # Extract Data
        crv_info_node = None
        try:
            periodic = cmds.getAttr(crv_shape + '.form')
            knot = None
            if periodic == 2: # 0: Open, 1: Closed: 2: Periodic
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
                    # periodic_end_cvs.extend(cvs_list[i])
                    periodic_end_cvs += [cvs_list[i]]

            points = cvs_list
            if periodic_end_cvs:
                points.extend(periodic_end_cvs)

            degree = cmds.getAttr(crv_shape + '.degree')
            # Store Extracted Values
            self.name = crv_shape
            self.points = points
            self.periodic = periodic
            self.knot = knot
            self.degree = degree
        except Exception as e:
            logger.warning(f'Unable to extract curve shape data. Issue: {str(e)}')
        finally:  # Clean-up temp nodes - In case they were left behind
            to_delete = [crv_info_node]
            for obj in to_delete:
                if obj and cmds.objExists(obj):
                    try:
                        cmds.delete(obj)
                    except Exception as e:
                        logger.debug(f'Unable to clean up scene after exacting curve. Issue: {str(e)}')

    def create(self):
        # Basic elements -----------------------------------------
        if not self.is_curve_shape_valid():
            return
        parameters = {"point": self.points}
        # Extra elements -----------------------------------------
        named_parameters = {'name': get_short_name(self.name),
                            'degree': self.degree,
                            'periodic': self.periodic,
                            'knot': self.knot,
                            }
        for key, value in named_parameters.items():
            if value:
                parameters[key] = value
        cmds.curve(**parameters)

    def get_data_as_dict(self):
        if not self.is_curve_shape_valid():
            return
        return self.__dict__

    def set_data_from_dict(self, data_dict):
        if not isinstance(data_dict, dict):
            logger.warning(f'Unable to ingest curve data. Data must be a dictionary, but was: {str(type(data_dict))}"')
            return
        if not data_dict.get('points'):
            logger.warning(f'Unable to ingest curve data. Missing points. Data: {data_dict}"')
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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    out = None
    test = {'degree': 3,
 'knot': [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
 'name': '|nurbsCircle1|nurbsCircleShape1',
 'periodic': 2,
 'points': [[0.784, 0.0, -0.784],
            [0.0, 0.0, -1.108],
            [-0.784, 0.0, -0.784],
            [-1.108, 0.0, -0.0],
            [-0.784, -0.0, 0.784],
            [-0.0, -0.0, 1.108],
            [0.784, -0.0, 0.784],
            [1.108, -0.0, 0.0],
            [0.784, 0.0, -0.784],
            [0.0, 0.0, -1.108],
            [-0.784, 0.0, -0.784]]}

    out = CurveShape(extract_existing_shape=test)
    # out.create()
    out.create()
    pprint(out)
