"""
 GT Rigger Utilities - Common functions used by the auto rigger scripts
 github.com/TrevisanGMW - 2021-12-10

 2022-01-31
 Added distalMultiplier attributes to toggle attribute

 2022-03-22
 Added "enforce_parent" function

"""
from gt_utilities import make_flat_list
from gt_rigger_data import *
from functools import partial
import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import logging
import random
import json
import math
import re

# Logger Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_utilities")
logger.setLevel(logging.DEBUG)


def dist_center_to_center(obj_a, obj_b):
    """
    Calculates the position between the center of one object (A)  to the center of another object (B)

    Args:
        obj_a (string) : Name of object A
        obj_b (string) : Name of object B

    Returns:
        distance (float): A distance value between object A and B. For example : 4.0
    """

    def dist_position_to_position(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
        """
            Calculates the distance between XYZ position A and XYZ position B
            
                        Parameters:
                                pos_a_x (float) : Object A Position X
                                pos_a_y (float) : Object A Position Y
                                pos_a_z (float) : Object A Position Z
                                pos_b_x (float) : Object B Position X
                                pos_b_y (float) : Object B Position Y
                                pos_b_z (float) : Object B Position Z
                                
                        Returns:
                            distance (float): A distance value between object A and B. For example : 4.0
            """
        dx = pos_a_x - pos_b_x
        dy = pos_a_y - pos_b_y
        dz = pos_a_z - pos_b_z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    # WS Center to Center Distance:
    cmds.select(obj_a, r=True)
    ws_pos_a = cmds.xform(q=True, ws=True, t=True)
    cmds.select(obj_b, r=True)
    ws_pos_b = cmds.xform(q=True, ws=True, t=True)
    return dist_position_to_position(ws_pos_a[0], ws_pos_a[1], ws_pos_a[2], ws_pos_b[0], ws_pos_b[1], ws_pos_b[2])


def combine_curves_list(curve_list):
    """
    This is a modified version of the GT Utility "Combine Curves"
    It moves the shape objects of all elements in the provided input (curve_list) to a single group (combining them)
    This version was changed to accept a list of objects (instead of selection)
    
            Parameters:
                    curve_list (list): A string of strings with the name of the curves to be combined.
    
    """
    errors = ''
    function_name = 'GTU Combine Curves List'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True
        acceptable_types = ['nurbsCurve', 'bezierCurve']
        bezier_in_selection = []

        for obj in curve_list:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == 'bezierCurve':
                    bezier_in_selection.append(obj)
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
                for obj in bezier_in_selection:
                    cmds.bezierCurveToNurbs()

        if valid_selection:
            shapes = []
            for obj in curve_list:
                extracted_shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for ext_shape in extracted_shapes:
                    shapes.append(ext_shape)

            for obj in range(len(curve_list)):
                cmds.makeIdentity(curve_list[obj], apply=True, rotate=True, scale=True, translate=True)

            group = cmds.group(empty=True, world=True, name=curve_list[0])
            cmds.select(shapes[0])
            for obj in range(1, (len(shapes))):
                cmds.select(shapes[obj], add=True)

            cmds.select(group, add=True)
            cmds.parent(relative=True, shape=True)
            cmds.delete(curve_list)
            combined_curve = cmds.rename(group, curve_list[0])
            return combined_curve

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occured when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def change_outliner_color(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object 
    
    Args:
        obj (str): Name (path) of the object to change.
        rgb_color (tuple) : A tuple of 3 floats, RGB values. e.g. Red = (1, 0, 0)
    
    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.useOutlinerColor', lock=True) is False:
        cmds.setAttr(obj + '.useOutlinerColor', 1)
        cmds.setAttr(obj + '.outlinerColorR', rgb_color[0])
        cmds.setAttr(obj + '.outlinerColorG', rgb_color[1])
        cmds.setAttr(obj + '.outlinerColorB', rgb_color[2])


def change_viewport_color(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object

    Args:
        obj (str): Name (path) of the object to change.
        rgb_color (tuple) : A tuple of 3 floats, RGB values. e.g. Red = (1, 0, 0)

    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.overrideEnabled', lock=True) is False:
        cmds.setAttr(obj + '.overrideEnabled', 1)
        cmds.setAttr(obj + '.overrideRGBColors', 1)
        cmds.setAttr(obj + '.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])


def add_node_note(obj, note_string):
    """
    Adds a note to the provided node (It can be seen at the bottom of the attribute editor)
    
    Args:
        obj (string): Name of the object.
        note_string (string): A string to be used as the note.
    
    """
    if not cmds.attributeQuery('notes', n=obj, ex=True):
        cmds.addAttr(obj, ln='notes', sn='nts', dt='string')
        cmds.setAttr('%s.notes' % obj, note_string, type='string')
    else:
        cmds.warning('%s already has a notes attribute' % obj)


def make_stretchy_ik(ik_handle, stretchy_name='temp', attribute_holder=None, jnt_scale_channel='X'):
    """
    Creates two measure tools and use them to determine when the joints should be scaled up causing a stretchy effect.
    
    Args:
        ik_handle (string) : Name of the IK Handle (joints will be extracted from it)
        stretchy_name (string): Name to be used when creating system (optional, if not provided it will be "temp")
        attribute_holder (string): The name of an object. If it exists, custom attributes will be added to it.
                                   These attributes allow the user to control whether or not the system is active,
                                   as well as its operation.
                                   For a more complete stretchy system you have to provide a valid object in this
                                   parameter as without it volume preservation is skipped

    Returns:
        list (list): A list with the end locator one (to be attached to the IK control) the stretchy_grp
        (system elements) and the end_ik_jnt (joint under the ikHandle)
    """

    def calculate_distance(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
        """
        Calculates the magnitude (in this case distance) between two objects
        
                Parameters:
                    pos_a_x (float): Position X for object A
                    pos_a_y (float): Position Y for object A
                    pos_a_z (float): Position Z for object A
                    pos_b_x (float): Position X for object B
                    pos_b_y (float): Position Y for object B
                    pos_b_z (float): Position Z for object B
                   
                Returns:
                    magnitude (float): Distance between two objects
        
        """
        dx = pos_a_x - pos_b_x
        dy = pos_a_y - pos_b_y
        dz = pos_a_z - pos_b_z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def int_to_en(num):
        """
        Given an int32 number, returns an English word for it.
        
                Parameters:
                    num (int) and integer to be converted to English words.
                    
                Returns:
                    number (string): The input number as words
        
        
        """
        d = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
             6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
             11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
             15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
             19: 'nineteen', 20: 'twenty',
             30: 'thirty', 40: 'forty', 50: 'fifty', 60: 'sixty',
             70: 'seventy', 80: 'eighty', 90: 'ninety'}
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert (0 <= num)

        if num < 20:
            return d[num]

        if num < 100:
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + '-' + d[num % 10]

        if num < k:
            if num % 100 == 0:
                return d[num // 100] + ' hundred'
            else:
                return d[num // 100] + ' hundred and ' + int_to_en(num % 100)

        if num < m:
            if num % k == 0:
                return int_to_en(num // k) + ' thousand'
            else:
                return int_to_en(num // k) + ' thousand, ' + int_to_en(num % k)

        if num < b:
            if (num % m) == 0:
                return int_to_en(num // m) + ' million'
            else:
                return int_to_en(num // m) + ' million, ' + int_to_en(num % m)

        if num < t:
            if (num % b) == 0:
                return int_to_en(num // b) + ' billion'
            else:
                return int_to_en(num // b) + ' billion, ' + int_to_en(num % b)

        if num % t == 0:
            return int_to_en(num // t) + ' trillion'
        else:
            return int_to_en(num // t) + ' trillion, ' + int_to_en(num % t)

        # raise AssertionError('num is too large: %s' % str(num))

    # ########## Start of Make Stretchy Function ##########
    scale_channels = ['X', 'Y', 'Z']
    ik_handle_joints = cmds.ikHandle(ik_handle, q=True, jointList=True)
    children_last_jnt = cmds.listRelatives(ik_handle_joints[-1], children=True, type='joint') or []

    # Find end joint
    end_ik_jnt = ''
    if len(children_last_jnt) == 1:
        end_ik_jnt = children_last_jnt[0]
    elif len(children_last_jnt) > 1:  # Find Joint Closest to ikHandle
        jnt_magnitude_pairs = []
        for jnt in children_last_jnt:
            ik_handle_ws_pos = cmds.xform(ik_handle, q=True, t=True, ws=True)
            jnt_ws_pos = cmds.xform(jnt, q=True, t=True, ws=True)
            mag = calculate_distance(ik_handle_ws_pos[0], ik_handle_ws_pos[1], ik_handle_ws_pos[2], jnt_ws_pos[0],
                                     jnt_ws_pos[1], jnt_ws_pos[2])
            jnt_magnitude_pairs.append([jnt, mag])
        # Find Lowest Distance
        curent_jnt = jnt_magnitude_pairs[1:][0]
        curent_closest = jnt_magnitude_pairs[1:][1]
        for pair in jnt_magnitude_pairs:
            if pair[1] < curent_closest:
                curent_closest = pair[1]
                curent_jnt = pair[0]
        end_ik_jnt = curent_jnt

    distance_one = cmds.distanceDimension(sp=(1, random.random() * 10, 1), ep=(2, random.random() * 10, 2))
    distance_one_transform = cmds.listRelatives(distance_one, parent=True, f=True) or [][0]
    distance_one_locators = cmds.listConnections(distance_one)
    cmds.delete(cmds.pointConstraint(ik_handle_joints[0], distance_one_locators[0]))
    cmds.delete(cmds.pointConstraint(ik_handle, distance_one_locators[1]))

    # Rename Distance One Nodes
    distance_node_one = cmds.rename(distance_one_transform, stretchy_name + '_stretchyTerm_strechyDistance')
    start_loc_one = cmds.rename(distance_one_locators[0], stretchy_name + '_stretchyTerm_start')
    end_loc_one = cmds.rename(distance_one_locators[1], stretchy_name + '_stretchyTerm_end')

    distance_nodes = {}  # [distance_node_transform, start_loc, end_loc, ik_handle_joint]
    index = 0
    for index in range(len(ik_handle_joints)):
        distance_node = cmds.distanceDimension(sp=(1, random.random() * 10, 1), ep=(2, random.random() * 10, 2))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, f=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)

        distance_node = cmds.rename(distance_node, stretchy_name + '_defaultTerm' + int_to_en(
            index + 1).capitalize() + '_strechyDistanceShape')
        distance_node_transform = cmds.rename(distance_node_transform, stretchy_name + '_defaultTerm' + int_to_en(
            index + 1).capitalize() + '_strechyDistance')
        start_loc = cmds.rename(distance_node_locators[0],
                                stretchy_name + '_defaultTerm' + int_to_en(index + 1).capitalize() + '_start')
        end_loc = cmds.rename(distance_node_locators[1],
                              stretchy_name + '_defaultTerm' + int_to_en(index + 1).capitalize() + '_end')

        cmds.delete(cmds.pointConstraint(ik_handle_joints[index], start_loc))
        if index < (len(ik_handle_joints) - 1):
            cmds.delete(cmds.pointConstraint(ik_handle_joints[index + 1], end_loc))
        else:
            cmds.delete(cmds.pointConstraint(end_ik_jnt, end_loc))

        distance_nodes[distance_node] = [distance_node_transform, start_loc, end_loc, ik_handle_joints[index]]

        index += 1

    # Organize Basic Hierarchy
    stretchy_grp = cmds.group(name=stretchy_name + '_stretchy_grp', empty=True, world=True)
    cmds.parent(distance_node_one, stretchy_grp)
    cmds.parent(start_loc_one, stretchy_grp)
    cmds.parent(end_loc_one, stretchy_grp)

    # Connect, Colorize and Organize Hierarchy
    default_distance_sum_node = cmds.createNode('plusMinusAverage', name=stretchy_name + '_defaultTermSum_plus')
    index = 0
    for node in distance_nodes:
        cmds.connectAttr('%s.distance' % node, '%s.input1D' % default_distance_sum_node + '[' + str(index) + ']')
        for obj in distance_nodes.get(node):
            if cmds.objectType(obj) != 'joint':
                change_outliner_color(obj, (1, .5, .5))
                cmds.parent(obj, stretchy_grp)
        index += 1

    # Outliner Color
    for obj in [distance_node_one, start_loc_one, end_loc_one]:
        change_outliner_color(obj, (.5, 1, .2))

    # Connect Nodes
    nonzero_stretch_condition_node = cmds.createNode('condition', name=stretchy_name + '_strechyNonZero_condition')
    nonzero_multiply_node = cmds.createNode('multiplyDivide', name=stretchy_name + '_onePctDistCondition_multiply')
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input1X' % nonzero_multiply_node)
    cmds.setAttr(nonzero_multiply_node + '.input2X', 0.01)
    cmds.connectAttr('%s.outputX' % nonzero_multiply_node, '%s.colorIfTrueR' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.outputX' % nonzero_multiply_node, '%s.secondTerm' % nonzero_stretch_condition_node)
    cmds.setAttr(nonzero_stretch_condition_node + '.operation', 5)

    stretch_normalization_node = cmds.createNode('multiplyDivide', name=stretchy_name + '_distNormalization_divide')
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.firstTerm' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.colorIfFalseR' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node, '%s.input1X' % stretch_normalization_node)

    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input2X' % stretch_normalization_node)

    cmds.setAttr(stretch_normalization_node + '.operation', 2)

    stretch_condition_node = cmds.createNode('condition', name=stretchy_name + '_strechyAutomation_condition')
    cmds.setAttr(stretch_condition_node + '.operation', 3)
    cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node,
                     '%s.firstTerm' % stretch_condition_node)  # Distance One
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.secondTerm' % stretch_condition_node)
    cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.colorIfTrueR' % stretch_condition_node)

    # Constraints
    cmds.pointConstraint(ik_handle_joints[0], start_loc_one)
    for node in distance_nodes:
        if distance_nodes.get(node)[3] == ik_handle_joints[0:][0]:
            start_loc_condition = cmds.pointConstraint(ik_handle_joints[0], distance_nodes.get(node)[1])

    # Attribute Holder Setup
    if attribute_holder:
        if cmds.objExists(attribute_holder):
            cmds.pointConstraint(attribute_holder, end_loc_one)
            cmds.addAttr(attribute_holder, ln='stretch', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(attribute_holder + '.stretch', 1)
            cmds.addAttr(attribute_holder, ln='squash', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln='stretchFromSource', at='bool', k=True)
            cmds.addAttr(attribute_holder, ln='saveVolume', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln='baseVolumeMultiplier', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(attribute_holder + '.baseVolumeMultiplier', .5)
            cmds.addAttr(attribute_holder, ln='minimumVolume', at='double', k=True, minValue=0.01, maxValue=1)
            cmds.addAttr(attribute_holder, ln='maximumVolume', at='double', k=True, minValue=0)
            cmds.setAttr(attribute_holder + '.minimumVolume', .4)
            cmds.setAttr(attribute_holder + '.maximumVolume', 2)
            cmds.setAttr(attribute_holder + '.stretchFromSource', 1)

            # Stretch From Body
            from_body_reverse_node = cmds.createNode('reverse', name=stretchy_name + '_stretchFromSource_reverse')
            cmds.connectAttr('%s.stretchFromSource' % attribute_holder, '%s.inputX' % from_body_reverse_node)
            cmds.connectAttr('%s.outputX' % from_body_reverse_node, '%s.w0' % start_loc_condition[0])

            # Squash
            squash_condition_node = cmds.createNode('condition', name=stretchy_name + '_squashAutomation_condition')
            cmds.setAttr(squash_condition_node + '.secondTerm', 1)
            cmds.setAttr(squash_condition_node + '.colorIfTrueR', 1)
            cmds.setAttr(squash_condition_node + '.colorIfFalseR', 3)
            cmds.connectAttr('%s.squash' % attribute_holder, '%s.firstTerm' % squash_condition_node)
            cmds.connectAttr('%s.outColorR' % squash_condition_node, '%s.operation' % stretch_condition_node)

            # Stretch
            activation_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + '_strechyActivation_blend')
            cmds.setAttr(activation_blend_node + '.input[0]', 1)
            cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.input[1]' % activation_blend_node)
            cmds.connectAttr('%s.stretch' % attribute_holder, '%s.attributesBlender' % activation_blend_node)

            for jnt in ik_handle_joints:
                cmds.connectAttr('%s.output' % activation_blend_node, jnt + '.scale' + jnt_scale_channel)

            # Save Volume
            save_volume_condition_node = cmds.createNode('condition', name=stretchy_name + '_saveVolume_condition')
            volume_normalization_divide_node = cmds.createNode('multiplyDivide',
                                                               name=stretchy_name + '_volumeNormalization_divide')
            volume_value_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + '_volumeValue_divide')
            xy_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + '_volumeXY_divide')
            volume_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + '_volumeActivation_blend')
            volume_clamp_node = cmds.createNode('clamp', name=stretchy_name + '_volumeLimits_clamp')
            volume_base_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + '_volumeBase_blend')

            cmds.setAttr(save_volume_condition_node + '.secondTerm', 1)
            cmds.setAttr(volume_normalization_divide_node + '.operation', 2)  # Divide
            cmds.setAttr(volume_value_divide_node + '.operation', 2)  # Divide
            cmds.setAttr(xy_divide_node + '.operation', 2)  # Divide

            cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node,
                             '%s.input2X' % volume_normalization_divide_node)  # Distance One
            cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input1X' % volume_normalization_divide_node)

            cmds.connectAttr('%s.outputX' % volume_normalization_divide_node, '%s.input2X' % volume_value_divide_node)
            cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.input1X' % volume_value_divide_node)

            cmds.connectAttr('%s.outputX' % volume_value_divide_node, '%s.input2X' % xy_divide_node)
            cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.input1X' % xy_divide_node)

            cmds.setAttr(volume_blend_node + '.input[0]', 1)
            cmds.connectAttr('%s.outputX' % xy_divide_node, '%s.input[1]' % volume_blend_node)

            cmds.connectAttr('%s.saveVolume' % attribute_holder, '%s.attributesBlender' % volume_blend_node)

            cmds.connectAttr('%s.output' % volume_blend_node, '%s.inputR' % volume_clamp_node)
            cmds.connectAttr('%s.outputR' % volume_clamp_node, '%s.colorIfTrueR' % save_volume_condition_node)

            cmds.connectAttr('%s.stretch' % attribute_holder, '%s.firstTerm' % save_volume_condition_node)
            cmds.connectAttr('%s.minimumVolume' % attribute_holder, '%s.minR' % volume_clamp_node)
            cmds.connectAttr('%s.maximumVolume' % attribute_holder, '%s.maxR' % volume_clamp_node)

            # Base Multiplier
            cmds.setAttr(volume_base_blend_node + '.input[0]', 1)
            cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.input[1]' % volume_base_blend_node)
            cmds.connectAttr('%s.baseVolumeMultiplier' % attribute_holder,
                             '%s.attributesBlender' % volume_base_blend_node)

            # Connect to Joints
            for channel in scale_channels:
                if jnt_scale_channel != channel:
                    cmds.connectAttr('%s.output' % volume_base_blend_node, ik_handle_joints[0] + '.scale' + channel)

            for jnt in ik_handle_joints[1:]:
                for channel in scale_channels:
                    if jnt_scale_channel != channel:
                        cmds.connectAttr('%s.outColorR' % save_volume_condition_node, jnt + '.scale' + channel)

        else:
            for jnt in ik_handle_joints:
                cmds.connectAttr('%s.outColorR' % stretch_condition_node, jnt + '.scale' + jnt_scale_channel)
    else:
        for jnt in ik_handle_joints:
            cmds.connectAttr('%s.outColorR' % stretch_condition_node, jnt + '.scale' + jnt_scale_channel)

    return [end_loc_one, stretchy_grp, end_ik_jnt]


def add_sine_attributes(obj, sine_prefix='sine', tick_source_attr='time1.outTime', hide_unkeyable=True,
                        add_absolute_output=False, nice_name_prefix=True):
    """
    Create Sine function without using third-party plugins or expressions
    
            Parameters:
                obj (string): Name of the object
                sine_prefix (string): Prefix given to the name of the attributes (default is "sine")
                tick_source_attr (string): Name of the attribute used as the source for time.
                                            It uses the default "time1" node if nothing else is specified
                hide_unkeyable (bool): Hides the tick and output attributes
                add_absolute_output (bool): Also creates an output version that gives only positive numbers much like
                                            the abs() expression

            Returns:
                sine_output_attrs (list): String with the name of the object and the name of the sine output attribute.
                                          E.g. "pSphere1.sineOutput"
                                          In case an absolute output is added, it will be the second object in the list.
                                          E.g. ["pSphere1.sineOutput", "pSphere1.sineAbsOutput"]
                                          If add_absolute_output is False the second attribute is None
    """
    # Load Required Plugins
    required_plugin = 'quatNodes'
    if not cmds.pluginInfo(required_plugin, q=True, loaded=True):
        cmds.loadPlugin(required_plugin, qt=False)

    # Set Variables
    influence_suffix = 'Time'
    amplitude_suffix = 'Amplitude'
    frequency_suffix = 'Frequency'
    offset_suffix = 'Offset'
    output_suffix = 'Output'
    tick_suffix = 'Tick'
    abs_suffix = 'AbsOutput'

    influence_attr = sine_prefix + influence_suffix
    amplitude_attr = sine_prefix + amplitude_suffix
    frequency_attr = sine_prefix + frequency_suffix
    offset_attr = sine_prefix + offset_suffix
    output_attr = sine_prefix + output_suffix
    tick_attr = sine_prefix + tick_suffix
    abs_attr = sine_prefix + abs_suffix

    # Create Nodes
    mdl_node = cmds.createNode('multDoubleLinear', name=obj + '_multDoubleLiner')
    quat_node = cmds.createNode('eulerToQuat', name=obj + '_eulerToQuat')
    multiply_node = cmds.createNode('multiplyDivide', name=obj + '_amplitude_multiply')
    sum_node = cmds.createNode('plusMinusAverage', name=obj + '_offset_sum')
    influence_multiply_node = cmds.createNode('multiplyDivide', name=obj + '_influence_multiply')

    # Add Attributes
    if nice_name_prefix:
        cmds.addAttr(obj, ln=influence_attr, at='double', k=True, maxValue=1, minValue=0)
        cmds.addAttr(obj, ln=amplitude_attr, at='double', k=True)
        cmds.addAttr(obj, ln=frequency_attr, at='double', k=True)
        cmds.addAttr(obj, ln=offset_attr, at='double', k=True)
        cmds.addAttr(obj, ln=tick_attr, at='double', k=True)
        cmds.addAttr(obj, ln=output_attr, at='double', k=True)
        if add_absolute_output:
            cmds.addAttr(obj, ln=abs_attr, at='double', k=True)
    else:
        cmds.addAttr(obj, ln=influence_attr, at='double', k=True, maxValue=1, minValue=0, nn=influence_suffix)
        cmds.addAttr(obj, ln=amplitude_attr, at='double', k=True, nn=amplitude_suffix)
        cmds.addAttr(obj, ln=frequency_attr, at='double', k=True, nn=frequency_suffix)
        cmds.addAttr(obj, ln=offset_attr, at='double', k=True, nn=offset_suffix)
        cmds.addAttr(obj, ln=tick_attr, at='double', k=True, nn=tick_suffix)
        cmds.addAttr(obj, ln=output_attr, at='double', k=True, nn=output_suffix)
        if add_absolute_output:
            cmds.addAttr(obj, ln=abs_attr, at='double', k=True, nn=re.sub(r'(\w)([A-Z])', r'\1 \2', abs_suffix))

    cmds.setAttr(obj + '.' + amplitude_attr, 1)
    cmds.setAttr(obj + '.' + frequency_attr, 10)

    if hide_unkeyable:
        cmds.setAttr(obj + '.' + tick_attr, k=False)
        cmds.setAttr(obj + '.' + output_attr, k=False)
    if add_absolute_output and hide_unkeyable:
        cmds.setAttr(obj + '.' + abs_attr, k=False)

    cmds.connectAttr(tick_source_attr, influence_multiply_node + '.input1X')
    cmds.connectAttr(influence_multiply_node + '.outputX', obj + '.' + tick_attr)
    cmds.connectAttr(obj + '.' + influence_attr, influence_multiply_node + '.input2X')

    cmds.connectAttr(obj + '.' + amplitude_attr, multiply_node + '.input2X')
    cmds.connectAttr(obj + '.' + frequency_attr, mdl_node + '.input1')
    cmds.connectAttr(obj + '.' + tick_attr, mdl_node + '.input2')
    cmds.connectAttr(obj + '.' + offset_attr, sum_node + '.input1D[0]')
    cmds.connectAttr(mdl_node + '.output', quat_node + '.inputRotateX')

    cmds.connectAttr(quat_node + '.outputQuatX', multiply_node + '.input1X')
    cmds.connectAttr(multiply_node + '.outputX', sum_node + '.input1D[1]')
    cmds.connectAttr(sum_node + '.output1D', obj + '.' + output_attr)

    if add_absolute_output:  # abs()
        squared_node = cmds.createNode('multiplyDivide', name=obj + '_abs_squared')
        reverse_squared_node = cmds.createNode('multiplyDivide', name=obj + '_reverseAbs_multiply')
        cmds.setAttr(squared_node + '.operation', 3)  # Power
        cmds.setAttr(reverse_squared_node + '.operation', 3)  # Power
        cmds.setAttr(squared_node + '.input2X', 2)
        cmds.setAttr(reverse_squared_node + '.input2X', .5)
        cmds.connectAttr(obj + '.' + output_attr, squared_node + '.input1X')
        cmds.connectAttr(squared_node + '.outputX', reverse_squared_node + '.input1X')
        cmds.connectAttr(reverse_squared_node + '.outputX', obj + '.' + abs_attr)
        return [(obj + '.' + output_attr), (obj + '.' + abs_attr)]
    else:
        return [(obj + '.' + output_attr), None]


def get_inverted_hierarchy_tree(obj_list, return_short_name=True):
    """
    Receives a list (usually a Maya selection) and returns a sorted version of it 
    starting with objects at the bottom of the hierarchy then working its way up to
    the top parents. It extracts the number of "|" symbols in the full path to the file
    to determine its position in the hierarchy before sorting it.
    
            Parameters:
                obj_list (list): A list of strings with the name of the Maya elements (Usually a maya selection)
                return_short_name (optional, bool): Determines if the return list will return the full path or just the short name.
                
            Returns:
                inverted_hierarchy_tree (list) : A list containing the same elements, but sorted from lowest child to top parent.
    
    """
    # Find hierarchy position and create pair
    sorted_pairs = []
    for obj in obj_list:
        if cmds.objExists(obj):
            long_name = cmds.ls(obj, l=True) or []
            number_of_parents = len(long_name[0].split('|'))
            sorted_pairs.append((long_name[0], number_of_parents))

    sorted_pairs.sort(key=lambda x: x[1], reverse=True)

    # Extract elements and return them
    inverted_hierarchy_tree = []
    for pair in sorted_pairs:
        if return_short_name:
            short_name = ''
            split_path = pair[0].split('|')
            if len(split_path) >= 1:
                short_name = split_path[len(split_path) - 1]
            inverted_hierarchy_tree.append(short_name)
        else:
            inverted_hierarchy_tree.append(pair[0])
    return inverted_hierarchy_tree


def get_short_name(obj):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

            Parameters:
                    obj (string) : object to extract short name
                    
            Returns:
                    short_name (string) : Name of the object without its full path
    """
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path) - 1]
    return short_name


def create_visualization_line(object_a, object_b):
    """
    Creates a curve attached to two objects so you can easily visualize hierarchies 
    
                Parameters:
                    object_a (string): Name of the object driving the start of the curve
                    object_b (string): Name of the object driving end of the curve (usually a child of object_a)
                    
                Returns:
                    list (list): A list with the generated curve, cluster_a, and cluster_b
    
    """
    crv = cmds.curve(p=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], d=1)
    cluster_a = cmds.cluster(crv + '.cv[0]')
    cluster_b = cmds.cluster(crv + '.cv[1]')

    if cmds.objExists(object_a):
        cmds.pointConstraint(object_a, cluster_a[1])

    if cmds.objExists(object_a):
        cmds.pointConstraint(object_b, cluster_b[1])

    crv = cmds.rename(crv, object_a + '_to_' + object_b)
    cluster_a = cmds.rename(cluster_a[1], object_a + '_cluster')
    cluster_b = cmds.rename(cluster_b[1], object_b + '_cluster')
    cmds.setAttr(cluster_a + '.v', 0)
    cmds.setAttr(cluster_b + '.v', 0)

    return [crv, cluster_a, cluster_b]


def create_joint_curve(name='jointCurve', scale=1, initial_position=(0, 0, 0)):
    """
    Creates a curve that looks like a joint to be used as a proxy 
    
    Args:
        name (string): Name of the generated curve
        scale (optional, float): The desired initial scale of the curve
        initial_position (tuple): A tuple of three floats. Used to determine initial position of the curve.

    Returns:
        curve_crv (string): Name of the generated curve (in case it was changed during creation)
    
    """
    curve_crv = cmds.curve(name=name, p=[[0.0, 2.428, 0.0], [0.0, 2.246, 0.93], [0.0, 1.72, 1.72], [0.0, 0.93, 2.246],
                                         [0.0, 0.0, 2.428], [0.0, -0.93, 2.246], [0.0, -1.72, 1.72],
                                         [0.0, -2.246, 0.93], [0.0, -2.428, 0.0], [0.0, -2.246, -0.93],
                                         [0.0, -1.72, -1.72], [0.0, -0.93, -2.246], [0.0, 0.0, -2.428],
                                         [0.0, 0.93, -2.246], [0.0, 1.72, -1.72], [0.0, 2.246, -0.93],
                                         [0.0, 2.428, 0.0], [0.93, 2.246, 0.0], [1.72, 1.72, 0.0], [2.246, 0.93, 0.0],
                                         [2.428, 0.0, 0.0], [2.246, -0.93, 0.0], [1.72, -1.72, 0.0],
                                         [0.93, -2.246, 0.0], [0.0, -2.428, 0.0], [-0.93, -2.246, 0.0],
                                         [-1.72, -1.72, 0.0], [-2.246, -0.93, 0.0], [-2.428, 0.0, 0.0],
                                         [-2.246, 0.93, 0.0], [-1.72, 1.72, 0.0], [-0.93, 2.246, 0.0],
                                         [0.0, 2.428, 0.0], [0.0, 2.246, -0.93], [0.0, 1.72, -1.72],
                                         [0.0, 0.93, -2.246], [0.0, 0.0, -2.428], [-0.93, 0.0, -2.246],
                                         [-1.72, 0.0, -1.72], [-2.246, 0.0, -0.93], [-2.428, 0.0, 0.0],
                                         [-2.246, 0.0, 0.93], [-1.72, 0.0, 1.72], [-0.93, 0.0, 2.246],
                                         [0.0, 0.0, 2.428], [0.93, 0.0, 2.246], [1.72, 0.0, 1.72], [2.246, 0.0, 0.93],
                                         [2.428, 0.0, 0.0], [2.246, 0.0, -0.93], [1.72, 0.0, -1.72],
                                         [0.93, 0.0, -2.246], [0.0, 0.0, -2.428]], d=1)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.move(initial_position[0], initial_position[1], initial_position[2], curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)
    # Rename Shapes
    for shape in cmds.listRelatives(curve_crv, s=True, f=True) or []:
        shape = cmds.rename(shape, '{0}Shape'.format(name))
    return curve_crv


def create_loc_joint_curve(name, scale, initial_position=(0, 0, 0)):
    """
    Creates a curve that looks like a joint and a locator to be used as a proxy 
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve
                initial_position (tuple): A tuple of three floats. Used to determine initial position of the curve.

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    """
    curve_assembly = []
    joint_crv = cmds.curve(name=name, p=[[0.0, 2.428, 0.0], [0.0, 2.246, 0.93], [0.0, 1.72, 1.72], [0.0, 0.93, 2.246],
                                         [0.0, 0.0, 2.428], [0.0, -0.93, 2.246], [0.0, -1.72, 1.72],
                                         [0.0, -2.246, 0.93], [0.0, -2.428, 0.0], [0.0, -2.246, -0.93],
                                         [0.0, -1.72, -1.72], [0.0, -0.93, -2.246], [0.0, 0.0, -2.428],
                                         [0.0, 0.93, -2.246], [0.0, 1.72, -1.72], [0.0, 2.246, -0.93],
                                         [0.0, 2.428, 0.0], [0.93, 2.246, 0.0], [1.72, 1.72, 0.0], [2.246, 0.93, 0.0],
                                         [2.428, 0.0, 0.0], [2.246, -0.93, 0.0], [1.72, -1.72, 0.0],
                                         [0.93, -2.246, 0.0], [0.0, -2.428, 0.0], [-0.93, -2.246, 0.0],
                                         [-1.72, -1.72, 0.0], [-2.246, -0.93, 0.0], [-2.428, 0.0, 0.0],
                                         [-2.246, 0.93, 0.0], [-1.72, 1.72, 0.0], [-0.93, 2.246, 0.0],
                                         [0.0, 2.428, 0.0], [0.0, 2.246, -0.93], [0.0, 1.72, -1.72],
                                         [0.0, 0.93, -2.246], [0.0, 0.0, -2.428], [-0.93, 0.0, -2.246],
                                         [-1.72, 0.0, -1.72], [-2.246, 0.0, -0.93], [-2.428, 0.0, 0.0],
                                         [-2.246, 0.0, 0.93], [-1.72, 0.0, 1.72], [-0.93, 0.0, 2.246],
                                         [0.0, 0.0, 2.428], [0.93, 0.0, 2.246], [1.72, 0.0, 1.72], [2.246, 0.0, 0.93],
                                         [2.428, 0.0, 0.0], [2.246, 0.0, -0.93], [1.72, 0.0, -1.72],
                                         [0.93, 0.0, -2.246], [0.0, 0.0, -2.428]], d=1)
    curve_assembly.append(joint_crv)
    loc_crv = cmds.curve(name=name + '_loc',
                         p=[[0.0, 0.0, 0.158], [0.0, 0.0, -0.158], [0.0, 0.0, 0.0], [0.158, 0.0, 0.0],
                            [-0.158, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.158, 0.0], [0.0, -0.158, 0.0]], d=1)
    curve_assembly.append(loc_crv)
    curve_crv = combine_curves_list(curve_assembly)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.move(initial_position[0], initial_position[1], initial_position[2], curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)

    # Rename Shapes
    shapes = cmds.listRelatives(curve_crv, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(curve_crv + 'Joint'))
    cmds.rename(shapes[1], '{0}Shape'.format(curve_crv + 'Loc'))

    return curve_crv


def create_aim_joint_curve(name, scale):
    """
    Creates a curve that looks like a joint with an arrow to be used as a proxy 
    It needs the function "gtu_combine_curves_list()" and "create_joint_curve" to properly work.
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    """
    curve_assembly = []
    curve_crv_a = create_joint_curve(name, 1)
    curve_assembly.append(curve_crv_a)
    curve_crv_b = cmds.curve(name='arrow_temp_crv',
                             p=[[-2.428, 0.0, 0.0], [2.428, 0.0, 0.0], [2.428, 0.0, -11.7], [4.85, 0.0, -11.7],
                                [0.0, 0.0, -19.387], [-4.85, 0.0, -11.7], [-2.428, 0.0, -11.7], [-2.428, 0.0, 0.0]],
                             d=1)
    curve_assembly.append(curve_crv_b)
    curve_crv = combine_curves_list(curve_assembly)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)

    # Rename Shapes
    shapes = cmds.listRelatives(curve_crv, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(curve_crv + 'Joint'))
    cmds.rename(shapes[1], '{0}Shape'.format(curve_crv + 'Arrow'))

    return curve_crv


def create_directional_joint_curve(name, scale):
    """
    Creates a curve that looks like a joint with an up direction to be used as a proxy 
    It needs the function "gtu_combine_curves_list()" and "create_joint_curve" to properly work.
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    """
    curve_assembly = []
    curve_crv_a = create_joint_curve(name, 1)
    curve_assembly.append(curve_crv_a)
    curve_crv_b = cmds.curve(name='arrow_tip_temp_crv',
                             p=[[-0.468, 5.517, 0.807], [0.0, 7.383, 0.0], [0.468, 5.517, 0.807],
                                [-0.468, 5.517, 0.807], [-0.936, 5.517, 0.0], [0.0, 7.383, 0.0], [-0.936, 5.517, 0.0],
                                [-0.468, 5.517, -0.807], [0.0, 7.383, 0.0], [0.468, 5.517, -0.807],
                                [-0.468, 5.517, -0.807], [0.468, 5.517, -0.807], [0.0, 7.383, 0.0], [0.936, 5.517, 0.0],
                                [0.468, 5.517, -0.807], [0.936, 5.517, 0.0], [0.468, 5.517, 0.807]], d=1)
    curve_assembly.append(curve_crv_b)
    curve_crv_c = cmds.curve(name='arrow_base_temp_crv',
                             p=[[-0.468, 5.517, 0.807], [0.0, 5.517, 0.0], [0.468, 5.517, 0.807],
                                [-0.468, 5.517, 0.807], [-0.936, 5.517, 0.0], [0.0, 5.517, 0.0], [-0.936, 5.517, 0.0],
                                [-0.468, 5.517, -0.807], [0.0, 5.517, 0.0], [0.468, 5.517, -0.807],
                                [-0.468, 5.517, -0.807], [0.468, 5.517, -0.807], [0.0, 5.517, 0.0], [0.936, 5.517, 0.0],
                                [0.468, 5.517, -0.807], [0.936, 5.517, 0.0], [0.468, 5.517, 0.807]], d=1)
    curve_assembly.append(curve_crv_c)
    curve_crv_d = cmds.curve(name='arrow_line_temp_crv', p=[[0.0, 5.517, 0.0], [0.0, 2.428, 0.0]], d=1)
    curve_assembly.append(curve_crv_d)
    curve_crv = combine_curves_list(curve_assembly)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)

    # Rename Shapes
    shapes = cmds.listRelatives(curve_crv, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(curve_crv + 'Joint'))
    cmds.rename(shapes[1], '{0}Shape'.format(curve_crv + 'ArrowTip'))
    cmds.rename(shapes[2], '{0}Shape'.format(curve_crv + 'ArrowBase'))
    cmds.rename(shapes[3], '{0}Shape'.format(curve_crv + 'ArrowLine'))

    return curve_crv


def create_main_control(name):
    """
    Creates a main control with an arrow pointing to +Z (Direction character should be facing)
    
        Parameters:
            name (string): Name of the new control
            
        Returns:
            main_crv (string): Name of the generated control (in case it was different than what was provided)
    
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


def create_scalable_arrow(curve_name='arrow', initial_scale=1, custom_shape=None, start_cv_list=None, end_cv_list=None):
    """
    Creates a curve in the shape of an arrow and rigs it so when scaling it up the curve doesn't lose its shape
    
            Parameters:
                curve_name (string): Name of the generated curve
                initial_scale (float): Initial Scale of the curve
                custom_shape (string): Doesn't generate an arrow. Use the provided shape instead. N
                                       ame of a curve shape. (Use "start_cv_list" and "end_cv_list" to set cvs)
                start_cv_list (list): A list of strings. In case you want to overwrite the original curve,
                                      you might want to provide new cvs. e.g "["cv[0:2]", "cv[8:10]"]"
                end_cv_list (list):  A list of strings. In case you want to overwrite the original curve,
                                     you might want to provide new cvs. e.g "["cv[0:2]", "cv[8:10]"]"
                
            Returns:
                generated_elements (list): A list with the generated elements: [curve_name, curve_scale_handle, rig_grp]
    
    """
    # Create Arrow
    if custom_shape:
        curve_transform = cmds.listRelatives(custom_shape, p=True, f=True)[0]
        curve_shape = custom_shape
    else:
        curve_transform = cmds.curve(name=curve_name,
                                     p=[[0.0, 0.0, -1.428], [0.409, 0.0, -1.0], [0.205, 0.0, -1.0], [0.205, 0.0, 1.0],
                                        [0.409, 0.0, 1.0], [0.0, 0.0, 1.428], [-0.409, 0.0, 1.0], [-0.205, 0.0, 1.0],
                                        [-0.205, 0.0, -1.0], [-0.409, 0.0, -1.0], [0.0, 0.0, -1.428]], d=1)
        curve_shape = cmds.listRelatives(curve_transform, s=True, f=True)[0]
        curve_shape = cmds.rename(curve_shape, '{0}Shape'.format(curve_transform))
    # Set Initial Scale
    cmds.setAttr(curve_transform + '.sx', initial_scale)
    cmds.setAttr(curve_transform + '.sy', initial_scale)
    cmds.setAttr(curve_transform + '.sz', initial_scale)
    cmds.makeIdentity(curve_transform, apply=True, scale=True, rotate=True)

    # Create Scale Curve
    curve_scale_crv = cmds.curve(name=curve_name + '_scaleCrv',
                                 p=[[0.0, 0.0, -1.0], [0.0, 0.0, -0.333], [0.0, 0.0, 0.333], [0.0, 0.0, 1.0]], d=3)
    curve_scale_shape = cmds.listRelatives(curve_scale_crv, s=True, f=True)[0]
    curve_scale_shape = cmds.rename(curve_scale_shape, '{0}Shape'.format(curve_scale_crv))
    # Set Initial Scale
    cmds.setAttr(curve_scale_crv + '.sx', initial_scale)
    cmds.setAttr(curve_scale_crv + '.sy', initial_scale)
    cmds.setAttr(curve_scale_crv + '.sz', initial_scale)
    cmds.makeIdentity(curve_scale_crv, apply=True, scale=True, rotate=True)

    # Create Clusters
    if start_cv_list:
        cmds.select(d=True)
        for cv in start_cv_list:
            cmds.select(curve_transform + '.' + cv, add=True)
    else:
        cmds.select([curve_transform + '.cv[0:2]', curve_transform + '.cv[8:10]'], r=True)
    cluster_start = cmds.cluster(name=curve_name + '_start', bs=1)

    if end_cv_list:
        cmds.select(d=True)
        for cv in end_cv_list:
            cmds.select(curve_transform + '.' + cv, add=True)
    else:
        cmds.select(curve_transform + '.cv[3:7]', r=True)
    cluster_end = cmds.cluster(name=curve_name + '_end', bs=1)

    # Create Mechanics
    start_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_name + '_start_pointOnCurve')
    end_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_name + '_end_pointOnCurve')
    cmds.setAttr(start_point_on_curve_node + '.parameter', 0)
    cmds.setAttr(end_point_on_curve_node + '.parameter', 1)

    cmds.connectAttr(curve_scale_shape + '.worldSpace', start_point_on_curve_node + '.inputCurve')
    cmds.connectAttr(curve_scale_shape + '.worldSpace', end_point_on_curve_node + '.inputCurve')

    start_curve_scale_grp = cmds.group(name=curve_name + '_curveScale_start_grp', world=True, empty=True)
    end_curve_scale_grp = cmds.group(name=curve_name + '_curveScale_end_grp', world=True, empty=True)

    cmds.delete(cmds.pointConstraint(cluster_start, start_curve_scale_grp))
    cmds.delete(cmds.pointConstraint(cluster_end, end_curve_scale_grp))

    cmds.connectAttr(start_point_on_curve_node + '.result.position', start_curve_scale_grp + '.translate')
    cmds.connectAttr(end_point_on_curve_node + '.result.position', end_curve_scale_grp + '.translate')

    curve_rig_grp = cmds.group(name=curve_name + '_setup_grp', world=True, empty=True)

    start_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_name + '_start_pointOnCurve')

    # Setup Hierarchy
    cmds.parent(cluster_start[1], start_curve_scale_grp)
    cmds.parent(cluster_end[1], end_curve_scale_grp)
    cmds.parent(curve_scale_crv, curve_rig_grp)
    cmds.parent(start_curve_scale_grp, curve_rig_grp)
    cmds.parent(end_curve_scale_grp, curve_rig_grp)

    # Set Visibility
    cmds.setAttr(cluster_start[1] + '.v', 0)
    cmds.setAttr(cluster_end[1] + '.v', 0)
    cmds.setAttr(curve_scale_crv + '.v', 0)

    # Clean Selection
    cmds.select(d=True)

    return [curve_transform, curve_scale_crv, curve_rig_grp]


def create_finger_curl_ctrl(ctrl_name, parent='world', scale_multiplier=1, x_offset=0, z_offset=0):
    """
    Creates a finger curl control. This function was made for a very specific use, so it already orients the control
    accordingly.
    
            Parameters:
                ctrl_name (string) : Name of the control (thumb, index, middle, ring, pinky)
                parent (optional, string) : Name of the parent object. If not provided, it will be left in the world.
                scale_multiplier (optional, float) : Number to multiply when scaling it.
                x_offset (optional, float) : Number to multiply the scale offset into X
                z_offset (optional, float) : Number to multiply the scale offset into Z
                
            Returns:
                curl_ctrl (string) : Name of the generated curl ctrl.
            
    """
    finger_curl_a = cmds.curve(name=ctrl_name, p=[[0.0, 0.127, -0.509], [0.047, 0.194, -0.474], [0.079, 0.237, -0.449],
                                                  [0.123, 0.292, -0.418], [0.158, 0.332, -0.383], [0.204, 0.364, -0.34],
                                                  [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.17, 0.374, -0.33],
                                                  [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33],
                                                  [0.129, 0.347, -0.368], [0.091, 0.311, -0.402],
                                                  [0.062, 0.269, -0.429], [0.062, 0.269, -0.429],
                                                  [0.062, 0.269, -0.429], [0.062, 0.454, -0.268], [0.062, 0.519, 0.024],
                                                  [0.062, 0.445, 0.232], [0.062, 0.355, 0.343], [0.062, 0.224, 0.445],
                                                  [0.062, 0.0, 0.509], [0.062, -0.224, 0.445], [0.062, -0.355, 0.343],
                                                  [0.062, -0.445, 0.232], [0.062, -0.519, 0.024],
                                                  [0.062, -0.454, -0.268], [0.062, -0.269, -0.429],
                                                  [0.062, -0.269, -0.429], [0.062, -0.269, -0.429],
                                                  [0.091, -0.311, -0.402], [0.129, -0.347, -0.368],
                                                  [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33],
                                                  [0.17, -0.374, -0.33], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34],
                                                  [0.204, -0.364, -0.34], [0.158, -0.332, -0.383],
                                                  [0.123, -0.292, -0.418], [0.079, -0.237, -0.449],
                                                  [0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    finger_curl_b = cmds.curve(name=ctrl_name + '_tempShape_b',
                               p=[[0.0, 0.127, -0.509], [-0.047, 0.194, -0.474], [-0.079, 0.237, -0.449],
                                  [-0.123, 0.292, -0.418], [-0.158, 0.332, -0.383], [-0.204, 0.364, -0.34],
                                  [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.17, 0.374, -0.33],
                                  [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33],
                                  [-0.129, 0.347, -0.368], [-0.091, 0.311, -0.402], [-0.062, 0.269, -0.429],
                                  [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.454, -0.268],
                                  [-0.062, 0.519, 0.024], [-0.062, 0.445, 0.232], [-0.062, 0.355, 0.343],
                                  [-0.062, 0.224, 0.445], [-0.062, 0.0, 0.509], [-0.062, -0.224, 0.445],
                                  [-0.062, -0.355, 0.343], [-0.062, -0.445, 0.232], [-0.062, -0.519, 0.024],
                                  [-0.062, -0.454, -0.268], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429],
                                  [-0.062, -0.269, -0.429], [-0.091, -0.311, -0.402], [-0.129, -0.347, -0.368],
                                  [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33],
                                  [-0.17, -0.374, -0.33], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34],
                                  [-0.204, -0.364, -0.34], [-0.158, -0.332, -0.383], [-0.123, -0.292, -0.418],
                                  [-0.079, -0.237, -0.449], [-0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    finger_curl_ctrl = combine_curves_list([finger_curl_a, finger_curl_b])
    shapes = cmds.listRelatives(finger_curl_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('arrow_l'))
    cmds.rename(shapes[1], '{0}Shape'.format('arrow_r'))
    cmds.setAttr(finger_curl_ctrl + '.rotateY', -90)
    cmds.setAttr(finger_curl_ctrl + '.scaleX', scale_multiplier * .1)
    cmds.setAttr(finger_curl_ctrl + '.scaleY', scale_multiplier * .1)
    cmds.setAttr(finger_curl_ctrl + '.scaleZ', scale_multiplier * .1)
    cmds.makeIdentity(finger_curl_ctrl, apply=True, scale=True, rotate=True)
    if parent != 'world':
        cmds.parent(finger_curl_ctrl, parent)

    cmds.move(scale_multiplier * z_offset, finger_curl_ctrl, z=True, relative=True, objectSpace=True)
    cmds.move(scale_multiplier * x_offset, finger_curl_ctrl, x=True, relative=True, objectSpace=True)
    return finger_curl_ctrl


def gtu_uniform_jnt_label_toggle():
    """
    Makes the visibility of the Joint Labels uniform according to the current state of the majority of them.  
    """

    function_name = 'GTU Uniform Joint Label Toggle'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        errors = ''
        joints = cmds.ls(type='joint', long=True)

        inactive_label = []
        active_label = []

        for obj in joints:
            try:
                current_label_state = cmds.getAttr(obj + '.drawLabel')
                if current_label_state:
                    active_label.append(obj)
                else:
                    inactive_label.append(obj)
            except Exception as e:
                errors += str(e) + '\n'

        if len(active_label) == 0:
            for obj in inactive_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 1)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(inactive_label) == 0:
            for obj in active_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 0)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(active_label) > len(inactive_label):
            for obj in inactive_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 1)
                except Exception as e:
                    errors += str(e) + '\n'
        else:
            for obj in active_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 0)
                except Exception as e:
                    errors += str(e) + '\n'

        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning(
                'The script couldn\'t read or write some "drawLabel" states. Open script editor for more info.')
    except:
        pass
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def create_shelf_button(command,
                        label='',
                        name=None,
                        tooltip='',
                        image=None,  # Default Python Icon
                        label_color=(1, 0, 0),  # Default Red
                        label_bgc_color=(0, 0, 0, 1),  # Default Black
                        bgc_color=None
                        ):
    """
    Add a shelf button to the current shelf (according to the provided parameters)
    
            Parameters:
                command (str): A string containing the code or command you want the button to run when clicking on it. E.g. "print("Hello World")"
                label (str): The label of the button. This is the text you see below it.
                name (str): The name of the button as seen inside the shelf editor.
                tooltip (str): The help message you get when hovering the button.
                image (str): The image used for the button (defaults to Python icon if none)
                label_color (tuple): A tuple containing three floats, these are RGB 0 to 1 values to determine the color of the label.
                label_bgc_color (tuple): A tuple containing four floats, these are RGBA 0 to 1 values to determine the background of the label.
                bgc_color (tuple):  A tuple containing three floats, these are RGB 0 to 1 values to determine the background of the icon
    
    """
    maya_version = int(cmds.about(v=True))

    shelf_top_level = mel.eval('$temp=$gShelfTopLevel')
    if not cmds.tabLayout(shelf_top_level, exists=True):
        cmds.warning('Shelf is not visible')
        return

    if not image:
        image = 'pythonFamily.png'

    shelf_tab = cmds.shelfTabLayout(shelf_top_level, query=True, selectTab=True)
    shelf_tab = shelf_top_level + '|' + shelf_tab

    # Populate extra arguments according to the current Maya version
    kwargs = {}
    if maya_version >= 2009:
        kwargs['commandRepeatable'] = True
    if maya_version >= 2011:
        kwargs['overlayLabelColor'] = label_color
        kwargs['overlayLabelBackColor'] = label_bgc_color
        if bgc_color:
            kwargs['enableBackground'] = bool(bgc_color)
            kwargs['backgroundColor'] = bgc_color

    return cmds.shelfButton(parent=shelf_tab, label=label, command=command,
                            imageOverlayLabel=label, image=image, annotation=tooltip,
                            width=32, height=32, align='center', **kwargs)


def add_rig_interface_button():
    """
    Create a button for a custom rig interface to the current shelf.
    It contains seamless FK/IK switchers and pose and animation management tools.
    """
    create_shelf_button(
        "import gt_biped_rig_interface\ngt_biped_rig_interface.build_gui_custom_rig_interface()",
        label='GTRig', tooltip='This button opens the Custom Rig Interface for GT Biped Rigger.',
        image='out_timeEditorAnimSource.png', label_color=(1, 0.45, 0))
    cmds.inViewMessage(
        amg='<span style=\"color:#FFFF00;\">Custom Rig Interface</span> button was added to your current shelf.',
        pos='botLeft', fade=True, alpha=.9)


def toggle_rigging_attr():
    """
    Toggles the visibility of custom attributes that are usually used only during the creation of a rig.
    For example, the limit attributes for the fingers or the option to automate the FK/IK switch visibility.

    """
    controls_fingers = ['left_fingers_ctrl', 'right_fingers_ctrl']
    attributes_fingers = ['fingersAutomation',
                          'autoRotation',
                          'thumbFistPoseLimit',
                          'thumbMultiplier',
                          'indexFistPoseLimit',
                          'indexMultiplier',
                          'middleFistPoseLimit',
                          'middleMultiplier',
                          'ringFistPoseLimit',
                          'ringMultiplier',
                          'pinkyFistPoseLimit',
                          'pinkyMultiplier',
                          'fingersAbduction',
                          'arrowVisibility',
                          'abductionInfluence',
                          'rotMultiplierThumb',
                          'rotMultiplierIndex',
                          'rotMultiplierMiddle',
                          'rotMultiplierRing',
                          'rotMultiplierPinky',
                          'knucklesAutomation',
                          'autoCompression',
                          'transCompression',
                          'rotCompression',
                          'transMultiplierIndex',
                          'rotCompMultiplierIndexY',
                          'rotCompMultiplierIndexX',
                          'transMultiplierMiddle',
                          'rotCompMultiplierMiddleY',
                          'rotCompMultiplierMiddleX',
                          'transMultiplierRing',
                          'rotCompMultiplierRingY',
                          'rotCompMultiplierRingX',
                          'transMultiplierPinky',
                          'rotCompMultiplierPinkyY',
                          'rotCompMultiplierPinkyX',
                          'maximumRotationZ',
                          'minimumRotationZ',
                          'rotateShape',
                          'distalMultiplierThumb',
                          'distalMultiplierIndex',
                          'distalMultiplierMiddle',
                          'distalMultiplierRing',
                          'distalMultiplierPinky',
                          ]

    controls_arm_switch = ['left_arm_switch_ctrl', 'right_arm_switch_ctrl']
    attributes_arm_switch = ['fingerAutomation',
                             'systemVisibility',
                             'autoVisibility',
                             'ctrlVisibility']

    controls_legs_switch = ['left_leg_switch_ctrl', 'right_leg_switch_ctrl', 'cog_ctrl']
    attributes_legs_switch = ['systemVisibility',
                              'autoVisibility',
                              'minimumVolume',
                              'maximumVolume',
                              ]

    attributes_main = ['jointCtrlsScaleInfluence',
                       'breathingTime',
                       'maxScaleSpine01',
                       'maxScaleSpine02',
                       'maxScaleSpine03',
                       'maxScaleSpine04',
                       'maxTranslateLClavicle',
                       'maxTranslateRClavicle',
                       ]

    current_state = cmds.getAttr(controls_fingers[0] + '.' + attributes_fingers[0],
                                 keyable=True)  # Use first attribute available to determine state

    # Finger Automation
    for ctrl in controls_fingers:
        for attr in attributes_fingers:
            # try:
            cmds.setAttr(ctrl + '.' + attr, keyable=(not current_state))
            # except:
            #     pass

    # Arm Switch
    for ctrl in controls_arm_switch:
        for attr in attributes_arm_switch:
            try:
                cmds.setAttr(ctrl + '.' + attr, keyable=(not current_state))
            except:
                pass

    # Legs Switch
    for ctrl in controls_legs_switch:
        for attr in attributes_legs_switch:
            try:
                cmds.setAttr(ctrl + '.' + attr, keyable=(not current_state))
            except:
                pass

    # Main Control
    for attr in attributes_main:
        try:
            cmds.setAttr('main_ctrl' + '.' + attr, keyable=(not current_state))
        except:
            pass

    # Print Feedback
    unique_message = '<' + str(random.random()) + '>'
    state_message = 'visible'
    if current_state:
        state_message = 'hidden'
    cmds.inViewMessage(
        amg=unique_message + '<span style=\"color:#FFFFFF;\">Rigging attributes are now </span><span style=\"color:#FF0000;text-decoration:underline;\">' + state_message + '</span>',
        pos='botLeft', fade=True, alpha=.9)


def attach_no_ssc_skeleton(duplicated_joints,
                           realtime_root_jnt,
                           current_root_jnt,
                           root_scale_constraint_ctrl,
                           new_skeleton_suffix='game',
                           jnt_suffix='jnt',
                           swap_names=True,
                           driver_suffix='driver'):
    """
    Attaches a previously generated game skeleton (no ssc skeleton)
    to follow and mimic the scale of the original gt auto biped rigger skeleton

    Args:
        duplicated_joints (list): A list of string containing all generated real-time joints
        realtime_root_jnt (string): The name of the root joint (usually the top parent) of the new skeleton
        current_root_jnt (string): The name of the root joint (usually the top parent) of the current skeleton
        root_scale_constraint_ctrl (string): Control used to drive the scale constraint of the game root joint
                                             (usually main_ctrl)
        new_skeleton_suffix (optional, string): expected in-between string for game skeleton.
                                                Used to pair with original skeleton
        jnt_suffix (optional, string): The suffix the script expects
                                       to find at the end of every joint
        swap_names (optional, bool): Whether or not to overwrite the original skeleton (use same name)
        driver_suffix (optional, string) : String added to the original skeleton in case swapping.
                                         This is joint_name + driver_suffix + jnt_suffix
                                         e.g. joint_driver_jnt
    Returns:
        sorted_no_ssc_joints (list): A list containing game skeleton joints

    Dependencies:
        get_short_name()
        generate_no_ssc_skeleton()
        get_inverted_hierarchy_tree()
        mimic_segment_scale_compensate_behaviour()
    """
    cmds.select(realtime_root_jnt, hierarchy=True)  # Sync selection order
    duplicated_joints = cmds.ls(selection=True, type='joint')

    cmds.select(current_root_jnt, hierarchy=True)
    original_joints = cmds.ls(selection=True, type='joint')

    sorted_original_joints = get_inverted_hierarchy_tree(original_joints)
    sorted_no_ssc_joints = get_inverted_hierarchy_tree(duplicated_joints)
    mimic_segment_scale_compensate(sorted_original_joints, sorted_no_ssc_joints)

    # Parent Constraint new system
    remove_new_str = '_' + new_skeleton_suffix + '_' + jnt_suffix
    remove_old_str = '_' + jnt_suffix

    remove_dupe_end_str = '_' + new_skeleton_suffix + '_end' + jnt_suffix.capitalize()
    remove_org_end_str = '_end' + jnt_suffix.capitalize()

    # Parent Constraint Real-time Skeleton
    for jnt in sorted_original_joints:
        for realtime_jnt in sorted_no_ssc_joints:
            joint_org = jnt.replace(remove_old_str, '')
            joint_dupe = realtime_jnt.replace(remove_new_str, '')
            if joint_org == joint_dupe:
                cmds.parentConstraint(jnt, realtime_jnt)

    for jnt in sorted_original_joints:
        for realtime_jnt in sorted_no_ssc_joints:
            joint_org = jnt.replace(remove_org_end_str, '')
            joint_dupe = realtime_jnt.replace(remove_dupe_end_str, '')
            if joint_org == joint_dupe:
                cmds.parentConstraint(jnt, realtime_jnt)

    # Scale Constraint Root
    cmds.scaleConstraint(root_scale_constraint_ctrl, realtime_root_jnt)

    # Swap Names (Real-time skeleton becomes the standard skeleton)
    if swap_names:

        # Make original invisible
        cmds.setAttr(current_root_jnt + '.v', 0)

        # Move Game Skeleton To Top
        cmds.reorder(realtime_root_jnt, front=True)

        to_rename = []
        # Search RT
        search_end_jnt = '_' + new_skeleton_suffix + '_end' + jnt_suffix.capitalize()
        search_jnt = '_' + new_skeleton_suffix + '_' + jnt_suffix
        # Replace RT
        new_suffix = '_' + jnt_suffix
        new_suffix_end_jnt = '_end' + jnt_suffix.capitalize()
        for jnt in sorted_no_ssc_joints:
            object_short_name = get_short_name(jnt)
            new_name = str(object_short_name).replace(search_jnt, new_suffix).replace(search_end_jnt,
                                                                                      new_suffix_end_jnt)
            if cmds.objExists(jnt) and 'shape' not in cmds.nodeType(jnt, inherited=True) and jnt != new_name:
                to_rename.append([jnt, new_name])
        # Search
        search_end_jnt = '_end' + jnt_suffix.capitalize()
        search_jnt = '_' + jnt_suffix
        # Replace
        new_suffix = '_' + driver_suffix + '_' + jnt_suffix
        new_suffix_end_jnt = '_' + driver_suffix + '_end' + jnt_suffix.capitalize()
        for jnt in sorted_original_joints:
            object_short_name = get_short_name(jnt)
            new_name = str(object_short_name).replace(search_jnt, new_suffix).replace(search_end_jnt,
                                                                                      new_suffix_end_jnt)
            if cmds.objExists(jnt) and 'shape' not in cmds.nodeType(jnt, inherited=True) and jnt != new_name:
                to_rename.append([jnt, new_name])

        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                cmds.rename(pair[0], pair[1])

    return sorted_no_ssc_joints


def generate_no_ssc_skeleton(new_suffix='game', jnt_suffix='jnt', skeleton_root='root_jnt'):
    """
    Uses other functions to build a secondary skeleton that doesn't rely
    on Maya's segment scale compensate system. It insteads bakes the scale
    on to the children joints.

            Parameters:
                new_suffix (optional, string): The in-between word used to create a new suffix.
                                               The new one will be new_suffix + "_" + jnt_suffix.
                                               e.g. myJoint_jnt => myJOint_game_jnt
                jnt_suffix (optional, string): The suffix the script expects
                                               to find at the end of every joint
                skeleton_root (optional, string): Root of the skeleton
            Returns:
                duplicated_joints (string): Generated joints
                no_ssc_root_jnt (string): Root joint for the generated joints

            Dependencies:
                get_short_name()
                mimic_segment_scale_compensate_behaviour()
                get_inverted_hierarchy_tree()
                jnt_suffix : string variable
                gt_ab_joints_default : list of joints

    """
    cmds.select(skeleton_root)
    game_skeleton = cmds.duplicate(renameChildren=True)
    for obj in game_skeleton:
        if cmds.objectType(obj) != 'joint':
            cmds.delete(obj)

    # Rename new skeleton
    to_rename = []
    search_jnt = '_' + jnt_suffix + '1'  # Automatic renamed during duplication
    search_end_jnt = '_end' + jnt_suffix.capitalize() + '1'
    new_suffix_end_jnt = '_' + new_suffix + '_end' + jnt_suffix.capitalize()
    new_suffix = '_' + new_suffix + '_' + jnt_suffix
    for jnt in game_skeleton:
        object_short_name = get_short_name(jnt)
        new_name = str(object_short_name).replace(search_jnt, new_suffix).replace(search_end_jnt, new_suffix_end_jnt)
        if cmds.objExists(jnt) and 'shape' not in cmds.nodeType(jnt, inherited=True) and jnt != new_name:
            to_rename.append([jnt, new_name])

    duplicated_joints = []
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            duplicated_joints.append(cmds.rename(pair[0], pair[1]))

    # Turn off SSC
    for jnt in duplicated_joints:
        cmds.setAttr(jnt + '.segmentScaleCompensate', 0)

    return duplicated_joints, cmds.ls(selection=True)[0]


def mimic_segment_scale_compensate(joints_with_ssc, joints_no_ssc):
    """
    Mimics the behaviour of segment scale compensate tranform system present in Maya
    transfering the baked values to a secondary joint chain.
    The secondary skeleton is compatible with real-time engines as it calculates and bakes
    scale values directly into the joints.

    Args:
        joints_with_ssc (list): A list of joints with segment scale compensate active (default joints)
        joints_no_ssc (list): A duplicated version of the "joints_with_ssc" list with the attribute
        segment scale compensate inactive.
        Use the function "generate_no_ssc_skeleton" to duplicate it.

    """
    # Check if lists are identical, name length and names?

    scale_compensate_multiply_prefix = 'ssc_scale_multiplier_'
    scale_compensate_divide_prefix = 'ssc_scale_divide_'

    for index in range(len(joints_no_ssc)):
        if index != len(joints_no_ssc) - 1:  # Don't apply it to the last one as it doesn't have children

            joint_parent = cmds.listRelatives(joints_no_ssc[index], parent=True)

            scale_compensate_multiply_node = scale_compensate_multiply_prefix + joints_no_ssc[index]
            scale_compensate_multiply_node = cmds.createNode('multiplyDivide', name=scale_compensate_multiply_node)

            cmds.connectAttr(scale_compensate_multiply_node + '.output', joints_no_ssc[index] + '.scale', f=True)
            cmds.connectAttr(joints_with_ssc[index] + '.scale', scale_compensate_multiply_node + '.input2', f=True)

            scale_compensate_divide_node = scale_compensate_divide_prefix + joint_parent[0]
            if not cmds.objExists(scale_compensate_divide_node):
                scale_compensate_divide_node = cmds.createNode('multiplyDivide', name=scale_compensate_divide_node)
                cmds.setAttr(scale_compensate_divide_node + '.operation', 2)
                cmds.setAttr(scale_compensate_divide_node + '.input1X', 1)
                cmds.setAttr(scale_compensate_divide_node + '.input1Y', 1)
                cmds.setAttr(scale_compensate_divide_node + '.input1Z', 1)

            try:
                if not cmds.isConnected(joint_parent[0] + '.scale', scale_compensate_divide_node + '.input2'):
                    cmds.connectAttr(joint_parent[0] + '.scale', scale_compensate_divide_node + '.input2', f=True)
                if not cmds.isConnected(scale_compensate_divide_node + '.output',
                                        scale_compensate_multiply_node + '.input1'):
                    cmds.connectAttr(scale_compensate_divide_node + '.output',
                                     scale_compensate_multiply_node + '.input1', f=True)
            except:
                pass

    # Try to connect hierarchy divide nodes
    for index in range(len(joints_no_ssc)):
        if index != len(joints_no_ssc) - 1:  # Ignore top parent
            joint_parent = cmds.listRelatives(joints_no_ssc[index], parent=True) or []

            try:
                cmds.connectAttr(scale_compensate_divide_prefix + joint_parent[0] + '.output',
                                 scale_compensate_divide_prefix + joints_no_ssc[index] + '.input1', f=True)
            except:
                pass


def create_limit_lock_attributes(obj, lock_attr='lockXY', primary_rotation_channel='Z', ignore_rot=False):
    """
    Creates two custom attributes. One for locking translate and another for locking two rotate channels.
    The primary rotation channels is left unlocked as it's assumed it will be used for animation

            Parameters:
                obj (string): Name of the target object
                lock_attr (string) : Name of the rotation lock attribute
                primary_rotation_channel (string) : Name of the rotation channel to be ignored (left unlocked)
                ignore_rot (bool): Ignores rotate channels and creates online lock translate attribute
    """
    available_channels = ['X', 'Y', 'Z']
    cmds.addAttr(obj, ln='lockTranslate', at='bool', k=True)
    cmds.setAttr(obj + '.lockTranslate', 1)
    if not ignore_rot:
        cmds.addAttr(obj, ln=lock_attr, at='bool', k=True)
        cmds.setAttr(obj + '.' + lock_attr, 1)

    for channel in available_channels:
        if not ignore_rot:
            if channel != primary_rotation_channel:  # Ignore Primary Rotation
                cmds.setAttr(obj + '.minRot' + channel + 'Limit', 0)
                cmds.setAttr(obj + '.maxRot' + channel + 'Limit', 0)
                cmds.connectAttr(obj + '.' + lock_attr, obj + '.minRot' + channel + 'LimitEnable', f=True)
                cmds.connectAttr(obj + '.' + lock_attr, obj + '.maxRot' + channel + 'LimitEnable', f=True)

        cmds.setAttr(obj + '.minTrans' + channel + 'Limit', 0)
        cmds.setAttr(obj + '.maxTrans' + channel + 'Limit', 0)

        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTrans' + channel + 'LimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTrans' + channel + 'LimitEnable', f=True)


def lock_hide_default_attr(obj, translate=True, rotate=True, scale=True, visibility=True):
    """
    Lock and Hide default attributes

            Parameters:
                obj (string): Name of the object to be locked
                translate (bool): Whether to lock and hide translate
                rotate (bool): Whether to lock and hide rotate
                scale (bool): Whether to lock and hide scale
                visibility (bool): Whether to lock and hide visibility

    """
    if translate:
        cmds.setAttr(obj + '.tx', lock=True, k=False, channelBox=False)
        cmds.setAttr(obj + '.ty', lock=True, k=False, channelBox=False)
        cmds.setAttr(obj + '.tz', lock=True, k=False, channelBox=False)

    if rotate:
        cmds.setAttr(obj + '.rx', lock=True, k=False, channelBox=False)
        cmds.setAttr(obj + '.ry', lock=True, k=False, channelBox=False)
        cmds.setAttr(obj + '.rz', lock=True, k=False, channelBox=False)

    if scale:
        cmds.setAttr(obj + '.sx', lock=True, k=False, channelBox=False)
        cmds.setAttr(obj + '.sy', lock=True, k=False, channelBox=False)
        cmds.setAttr(obj + '.sz', lock=True, k=False, channelBox=False)

    if visibility:
        cmds.setAttr(obj + '.v', lock=True, k=False, channelBox=False)


def setup_shape_switch(control, attr='controlShape', shape_names=['box', 'semiCircle', 'pin'],
                       shape_enum=['Box', 'Semi-Circle', 'Pin']):
    """
    Creates the nodes and connections necessary to switch between three shapes.
    One is the default 3D shape, another is a flat 2D shape and the third is a pin for when constraining
            Dependencies:
                CONSTANTS from gt_rigger_data
            Parameters:
                control (string): Name of the control to create the switch
                attr (optional, string): Attribute name, default is "controlShape"
                shape_names (optional, list): A list of three elements with the expected names of the shapes,
                                             [3D, 2D, PIN] If using only two, the third one will be ignored.
                shape_enum (optional, list): A list of three elements with the enum names of the shapes,
                                            [3D, 2D, PIN]
    """
    enum_string = ''
    for string in shape_enum:
        enum_string += string + ':'

    if not cmds.attributeQuery(attr, node=control, exists=True):
        cmds.addAttr(control, ln=attr, at='enum', en=enum_string, keyable=True)

    condition_pairs = []

    for index in range(len(shape_names)):
        condition_pairs.append([cmds.createNode('condition',
                                                name=control.replace(CTRL_SUFFIX, '') + 'shape' + shape_names[
                                                    index].capitalize() + '_condition'), shape_names[index]])

    for index in range(len(condition_pairs)):
        condition_node = condition_pairs[index][0]
        cmds.setAttr(condition_node + '.colorIfTrueR', 1)
        cmds.setAttr(condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(condition_node + '.colorIfTrueG', 1)
        cmds.setAttr(condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(condition_node + '.colorIfTrueB', 1)
        cmds.setAttr(condition_node + '.colorIfFalseB', 0)
        cmds.setAttr(condition_node + '.secondTerm', index)
        cmds.connectAttr(control + '.' + attr, condition_node + '.firstTerm', f=True)

    available_shapes = cmds.listRelatives(control, s=True, f=True) or []
    for shape in available_shapes:
        for condition_pair in condition_pairs:
            if condition_pair[1] + 'Shape' in shape:
                cmds.connectAttr(condition_pair[0] + '.outColorR', shape + '.v', f=True)


def force_center_pivot(obj):
    """
    Moves the provided object to the center of the grid
    Args:
        obj: Name of the object (string)
    """
    cmds.move(0, 0, 0, obj, a=True, rpr=True)


def create_text(text, font='MS Shell Dlg 2'):
    """
    Creates a nurbs curve with the shape of the provided text.
    Args:
        text: Text to be generated (string)
        font: Font used to create the text (string, optional)

    Returns:
        string: Name of the curve object (string)
    """
    cmds.textCurves(ch=0, t=text, font=font)
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
    cmds.rename(text.lower().replace('/', '_') + "_crv")
    print(' ')  # Clear Warnings
    return cmds.ls(sl=True)[0]


def rescale(obj, scale, freeze=True):
    """
    Sets the scaleXYZ to the provided scale value, then freezes the object so it has a new scale
    Args:
        obj (string) Name of the object, for example "pSphere1"
        scale (float) The new scale value,, for example 0.5
                      (this would cause it to be half of its initial size in case it was previously one)
        freeze: (bool) Determines if the object scale should be frozen after updated
    """
    cmds.setAttr(obj + '.scaleX', scale)
    cmds.setAttr(obj + '.scaleY', scale)
    cmds.setAttr(obj + '.scaleZ', scale)
    if freeze:
        cmds.makeIdentity(obj, apply=True, scale=True)


def create_slider_control(name, initial_position='middle', lock_unused_channels=True):
    """

    Args:
        name:  Object name (string)
        initial_position:  "middle", "top" or "bottom" (string)
        lock_unused_channels:  locks and hides unused channels (TX, TZ, ROT...)

    Returns:
        ctrl_elements: A list with the control name and control group name
    """
    default_ctrl_line_width = 3

    # Validate Name
    if not name:
        cmds.warning('Control name cannot be empty')
        return

    # Create Elements
    ctrl = cmds.curve(name=name,
                      p=[[-1.0, -1.0, 0.0], [-1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [-1.0, -1.0, 0.0]],
                      d=1)
    ctrl_bg = cmds.curve(name=name + '_bg_' + CRV_SUFFIX,
                         p=[[-1.0, -6.0, 0.0], [-1.0, 6.0, 0.0], [1.0, 6.0, 0.0], [1.0, -6.0, 0.0], [-1.0, -6.0, 0.0]],
                         d=1)
    ctrl_grp = cmds.group(name=ctrl + GRP_SUFFIX.capitalize(), world=True, empty=True)
    cmds.parent(ctrl, ctrl_grp)
    cmds.parent(ctrl_bg, ctrl_grp)

    # Handle Shape
    shape = ''
    for shape in cmds.listRelatives(ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, '{0}Shape'.format(name))

    # Determine initial position
    if initial_position.lower() == 'top':
        cmds.setAttr(ctrl + '.ty', 5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 0)
        cmds.setAttr(ctrl + '.minTransYLimit', -10)
    elif initial_position.lower() == 'bottom':
        cmds.setAttr(ctrl + '.ty', -5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 10)
        cmds.setAttr(ctrl + '.minTransYLimit', 0)
    else:
        cmds.setAttr(ctrl + '.maxTransYLimit', 5)
        cmds.setAttr(ctrl + '.minTransYLimit', -5)

    # Determine Look
    cmds.setAttr(shape + '.lineWidth', default_ctrl_line_width)
    cmds.setAttr(ctrl_bg + '.overrideEnabled', 1)
    cmds.setAttr(ctrl_bg + '.overrideDisplayType', 2)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.minTransYLimitEnable', 1)

    if lock_unused_channels:
        axis = ['x', 'y', 'z']
        attrs = ['t', 'r', 's']
        for ax in axis:
            for attr in attrs:
                if (attr + ax) != 'ty':
                    cmds.setAttr(ctrl + '.' + attr + ax, lock=True, k=False, channelBox=False)
        cmds.setAttr(ctrl + '.v', lock=True, k=False, channelBox=False)

    return [ctrl, ctrl_grp]


def create_2d_slider_control(name, initial_position_y='middle', initial_position_x='middle', lock_unused_channels=True,
                             ignore_range=None):
    """

    Args:
        name:  Object name (string)
        initial_position_y:  "middle", "top" or "bottom" (string)
        initial_position_x:  "middle", "right" or "left" (string)
        lock_unused_channels:  locks and hides unused channels (TX, TZ, ROT...)
        ignore_range: TODO

    Returns:
        ctrl_elements: A list with the control name and control group name
    """
    default_ctrl_line_width = 3

    # Validate Name
    if not name:
        cmds.warning('Control name cannot be empty')
        return

    # Create Elements
    ctrl = cmds.curve(name=name,
                      p=[[-1.0, -1.0, 0.0], [-1.0, 1.0, 0], [1.0, 1.0, 0], [1.0, -1.0, 0], [-1.0, -1.0, 0]],
                      d=1)
    ctrl_bg = cmds.curve(name=name + '_bg_' + CRV_SUFFIX,
                         p=[[-6.0, -6.0, 0.0], [-6.0, 6.0, 0.0], [6.0, 6.0, 0.0], [6.0, -6.0, 0.0], [-6.0, -6.0, 0.0]],
                         d=1)
    ctrl_grp = cmds.group(name=ctrl + GRP_SUFFIX.capitalize(), world=True, empty=True)
    cmds.parent(ctrl, ctrl_grp)
    cmds.parent(ctrl_bg, ctrl_grp)

    # Handle Shape
    shape = ''
    for shape in cmds.listRelatives(ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, '{0}Shape'.format(name))

    # Determine initial Y position
    if initial_position_y.lower() == 'top':
        cmds.setAttr(ctrl + '.ty', 5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 0)
        cmds.setAttr(ctrl + '.minTransYLimit', -10)
    elif initial_position_y.lower() == 'bottom':
        cmds.setAttr(ctrl + '.ty', -5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 10)
        cmds.setAttr(ctrl + '.minTransYLimit', 0)
    else:
        cmds.setAttr(ctrl + '.maxTransYLimit', 5)
        cmds.setAttr(ctrl + '.minTransYLimit', -5)

    # Determine initial X position
    if initial_position_x.lower() == 'right':
        cmds.setAttr(ctrl + '.tx', 5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransXLimit', 0)
        cmds.setAttr(ctrl + '.minTransXLimit', -10)
    elif initial_position_x.lower() == 'left':
        cmds.setAttr(ctrl + '.tx', -5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransXLimit', 10)
        cmds.setAttr(ctrl + '.minTransXLimit', 0)
    else:
        cmds.setAttr(ctrl + '.maxTransXLimit', 5)
        cmds.setAttr(ctrl + '.minTransXLimit', -5)

    # Determine Look
    cmds.setAttr(shape + '.lineWidth', default_ctrl_line_width)
    cmds.setAttr(ctrl_bg + '.overrideEnabled', 1)
    cmds.setAttr(ctrl_bg + '.overrideDisplayType', 2)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.minTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransXLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransXLimitEnable', 1)
    cmds.setAttr(ctrl + '.minTransXLimitEnable', 1)

    if lock_unused_channels:
        axis = ['x', 'y', 'z']
        attrs = ['t', 'r', 's']
        for ax in axis:
            for attr in attrs:
                if (attr + ax) != 'ty' and (attr + ax) != 'tx':
                    cmds.setAttr(ctrl + '.' + attr + ax, lock=True, k=False, channelBox=False)
        cmds.setAttr(ctrl + '.v', lock=True, k=False, channelBox=False)

    if ignore_range:
        if ignore_range == 'right':
            cmds.move(-5, ctrl_bg + '.cv[2:3]', moveX=True, relative=True)
            cmds.setAttr(ctrl + '.maxTransXLimit', 0)
        elif ignore_range == 'left':
            cmds.move(5, ctrl_bg + '.cv[0:1]', moveX=True, relative=True)
            cmds.move(5, ctrl_bg + '.cv[4]', moveX=True, relative=True)
            cmds.setAttr(ctrl + '.minTransXLimit', 0)
        elif ignore_range == 'bottom':
            cmds.move(5, ctrl_bg + '.cv[0]', moveY=True, relative=True)
            cmds.move(5, ctrl_bg + '.cv[3:4]', moveY=True, relative=True)
            cmds.setAttr(ctrl + '.minTransYLimit', 0)
        elif ignore_range == 'top':
            cmds.move(-5, ctrl_bg + '.cv[1:2]', moveY=True, relative=True)
            cmds.setAttr(ctrl + '.maxTransYLimit', 0)

    return [ctrl, ctrl_grp]


def create_mouth_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])
    """
    # Containers
    controls = []
    background = []

    # Top Label
    mouth_crv = create_text('MOUTH')
    force_center_pivot(mouth_crv)
    rescale(mouth_crv, 1.75)
    cmds.setAttr(mouth_crv + '.ty', 10.5)
    cmds.setAttr(mouth_crv + '.overrideDisplayType', 2)
    background.append(mouth_crv)

    # 1D Controls
    mid_upper_lip_ctrl = create_slider_control('mid_upperLip_offset_ctrl')
    mid_lower_lip_ctrl = create_slider_control('mid_lowerLip_offset_ctrl')
    left_upper_outer_lip_ctrl = create_slider_control('left_upperOuterLip_offset_ctrl')
    left_lower_outer_lip_ctrl = create_slider_control('left_lowerOuterLip_offset_ctrl')
    left_upper_corner_lip_ctrl = create_slider_control('left_upperCornerLip_offset_ctrl')
    left_lower_corner_lip_ctrl = create_slider_control('left_lowerCornerLip_offset_ctrl')
    right_upper_outer_lip_ctrl = create_slider_control('right_upperOuterLip_offset_ctrl')
    right_lower_outer_lip_ctrl = create_slider_control('right_lowerOuterLip_offset_ctrl')
    right_upper_corner_lip_ctrl = create_slider_control('right_upperCornerLip_offset_ctrl')
    right_lower_corner_lip_ctrl = create_slider_control('right_lowerCornerLip_offset_ctrl')
    main_mouth_offset_ctrl = create_slider_control('mainMouth_offset_ctrl')
    in_out_tongue_ctrl = create_slider_control('inOutTongue_offset_ctrl', initial_position='top')

    # TY
    cmds.setAttr(mid_upper_lip_ctrl[1] + '.ty', 6)
    cmds.setAttr(mid_lower_lip_ctrl[1] + '.ty', -5)
    cmds.setAttr(left_upper_outer_lip_ctrl[1] + '.ty', 5)
    cmds.setAttr(left_lower_outer_lip_ctrl[1] + '.ty', -4)
    cmds.setAttr(left_upper_corner_lip_ctrl[1] + '.ty', 4)
    cmds.setAttr(left_lower_corner_lip_ctrl[1] + '.ty', -3)
    cmds.setAttr(right_upper_outer_lip_ctrl[1] + '.ty', 5)
    cmds.setAttr(right_lower_outer_lip_ctrl[1] + '.ty', -4)
    cmds.setAttr(right_upper_corner_lip_ctrl[1] + '.ty', 4)
    cmds.setAttr(right_lower_corner_lip_ctrl[1] + '.ty', -3)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.tx', 13)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.ty', -13.8)
    cmds.setAttr(in_out_tongue_ctrl[1] + '.ty', -9.5)

    # TX
    cmds.setAttr(left_upper_outer_lip_ctrl[1] + '.tx', 2)
    cmds.setAttr(left_lower_outer_lip_ctrl[1] + '.tx', 2)
    cmds.setAttr(left_upper_corner_lip_ctrl[1] + '.tx', 4)
    cmds.setAttr(left_lower_corner_lip_ctrl[1] + '.tx', 4)
    cmds.setAttr(right_upper_outer_lip_ctrl[1] + '.tx', -2)
    cmds.setAttr(right_lower_outer_lip_ctrl[1] + '.tx', -2)
    cmds.setAttr(right_upper_corner_lip_ctrl[1] + '.tx', -4)
    cmds.setAttr(right_lower_corner_lip_ctrl[1] + '.tx', -4)
    cmds.setAttr(in_out_tongue_ctrl[1] + '.tx', -13)

    # Misc
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sx', 0.8)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sy', 0.8)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sz', 0.8)
    cmds.setAttr(in_out_tongue_ctrl[1] + '.rz', 90)


    half_size_ctrls = [left_upper_outer_lip_ctrl, left_lower_outer_lip_ctrl, left_upper_corner_lip_ctrl,
                       left_lower_corner_lip_ctrl, right_upper_outer_lip_ctrl, right_lower_outer_lip_ctrl,
                       right_upper_corner_lip_ctrl, right_lower_corner_lip_ctrl, mid_upper_lip_ctrl, mid_lower_lip_ctrl,
                       in_out_tongue_ctrl]

    for ctrl in half_size_ctrls:
        cmds.setAttr(ctrl[1] + '.sx', 0.5)
        cmds.setAttr(ctrl[1] + '.sy', 0.5)
        cmds.setAttr(ctrl[1] + '.sz', 0.5)

    # 2D Controls
    left_corner_lip_ctrl = create_2d_slider_control('left_cornerLip_offset_ctrl')
    right_corner_lip_ctrl = create_2d_slider_control('right_cornerLip_offset_ctrl')
    jaw_ctrl = create_2d_slider_control('jaw_offset_ctrl')
    tongue_ctrl = create_2d_slider_control('tongue_offset_ctrl')

    # Inverted Right Controls
    cmds.setAttr(right_corner_lip_ctrl[1] + '.ry', 180)

    cmds.setAttr(left_corner_lip_ctrl[1] + '.tx', 12)
    cmds.setAttr(right_corner_lip_ctrl[1] + '.tx', -12)
    cmds.setAttr(jaw_ctrl[1] + '.ty', -15)
    rescale(tongue_ctrl[1], 0.5, freeze=False)
    cmds.setAttr(tongue_ctrl[1] + '.ty', -15)
    cmds.setAttr(tongue_ctrl[1] + '.tx', -13)

    # Determine Grp Order
    controls.append(left_corner_lip_ctrl)
    controls.append(left_upper_outer_lip_ctrl)
    controls.append(left_lower_outer_lip_ctrl)
    controls.append(left_upper_corner_lip_ctrl)
    controls.append(left_lower_corner_lip_ctrl)
    controls.append(right_corner_lip_ctrl)
    controls.append(right_upper_outer_lip_ctrl)
    controls.append(right_lower_outer_lip_ctrl)
    controls.append(right_upper_corner_lip_ctrl)
    controls.append(right_lower_corner_lip_ctrl)
    controls.append(main_mouth_offset_ctrl)
    controls.append(mid_upper_lip_ctrl)
    controls.append(mid_lower_lip_ctrl)
    controls.append(jaw_ctrl)
    controls.append(tongue_ctrl)
    controls.append(in_out_tongue_ctrl)

    # Jaw Label
    jaw_crv = create_text('JAW')
    force_center_pivot(jaw_crv)
    cmds.setAttr(jaw_crv + '.ty', -20.5)
    cmds.setAttr(jaw_crv + '.overrideDisplayType', 2)
    background.append(jaw_crv)

    # Tongue Label
    tongue_crv = create_text('TONGUE')
    force_center_pivot(tongue_crv)
    cmds.setAttr(tongue_crv + '.ty', -20.5)
    cmds.setAttr(tongue_crv + '.tx', -15)
    cmds.setAttr(tongue_crv + '.overrideDisplayType', 2)
    background.append(tongue_crv)

    # Tongue Label
    tongue_crv = create_text('UP/DOWN')
    force_center_pivot(tongue_crv)
    cmds.setAttr(tongue_crv + '.ty', -20.5)
    cmds.setAttr(tongue_crv + '.tx', 10.75)
    cmds.setAttr(tongue_crv + '.overrideDisplayType', 2)
    background.append(tongue_crv)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_mouth_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_mouth_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_mouth_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 9)
    cmds.setAttr(r_crv + '.ty', 9)
    background.append(l_crv)
    background.append(r_crv)

    # Parent Groups
    gui_grp = cmds.group(name='mouth_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='mouth_background_grp', world=True, empty=True)

    # General Background
    mouth_bg_crv = cmds.curve(name='mouth_bg_crv', p=[[-20.0, 13.0, 0.0], [-20.0, -23.0, 0.0], [20.0, -23.0, 0.0],
                                                      [20.0, 13.0, 0.0], [-20.0, 13.0, 0.0]], d=1)

    cmds.setAttr(mouth_bg_crv + '.overrideDisplayType', 1)
    background.append(mouth_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    # Final Color Adjustments
    change_viewport_color(main_mouth_offset_ctrl[0], (1, 0.35, 0.55))
    change_viewport_color(tongue_ctrl[0], (1, 0.35, 0.55))
    change_viewport_color(in_out_tongue_ctrl[0], (1, 0.35, 0.55))

    return (gui_grp, controls)


def create_eyebrow_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])

    """
    # Containers
    controls = []
    background = []

    # Top Label
    eyebrows_crv = create_text('EYEBROWS')
    force_center_pivot(eyebrows_crv)
    rescale(eyebrows_crv, 1.75)
    cmds.setAttr(eyebrows_crv + '.ty', 7.3)
    cmds.setAttr(eyebrows_crv + '.overrideDisplayType', 2)
    background.append(eyebrows_crv)

    # 1D Controls
    left_mid_brow_ctrl = create_slider_control('left_midBrow_offset_ctrl')
    left_outer_brow_ctrl = create_slider_control('left_outerBrow_offset_ctrl')
    right_mid_brow_ctrl = create_slider_control('right_midBrow_offset_ctrl')
    right_outer_brow_ctrl = create_slider_control('right_outerBrow_offset_ctrl')

    # TY
    cmds.setAttr(left_mid_brow_ctrl[1] + '.tx', 11)
    cmds.setAttr(left_outer_brow_ctrl[1] + '.tx', 15)
    cmds.setAttr(right_mid_brow_ctrl[1] + '.tx', -11)
    cmds.setAttr(right_outer_brow_ctrl[1] + '.tx', -15)

    left_inner_brow_ctrl = create_2d_slider_control('left_innerBrow_offset_ctrl', ignore_range='right')
    right_inner_brow_ctrl = create_2d_slider_control('right_innerBrow_offset_ctrl', ignore_range='right')

    # Invert Right Side
    cmds.setAttr(right_inner_brow_ctrl[1] + '.ry', 180)

    cmds.setAttr(left_inner_brow_ctrl[1] + '.tx', 7)
    cmds.setAttr(right_inner_brow_ctrl[1] + '.tx', -7)

    # Determine Grp Order
    controls.append(left_inner_brow_ctrl)
    controls.append(left_mid_brow_ctrl)
    controls.append(left_outer_brow_ctrl)
    controls.append(right_inner_brow_ctrl)
    controls.append(right_mid_brow_ctrl)
    controls.append(right_outer_brow_ctrl)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_eyebrow_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_eyebrow_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_eyebrow_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 7.3)
    cmds.setAttr(r_crv + '.ty', 7.3)
    cmds.setAttr(l_crv + '.tx', 3)
    cmds.setAttr(r_crv + '.tx', -3)
    background.append(l_crv)
    background.append(r_crv)

    # Parent Groups
    gui_grp = cmds.group(name='eyebrow_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='eyebrow_background_grp', world=True, empty=True)

    # General Background
    eyebrow_bg_crv = cmds.curve(name='eyebrow_bg_crv', p=[[-20.0, 10.0, 0.0], [-20.0, -8.0, 0.0], [20.0, -8.0, 0.0],
                                                          [20.0, 10.0, 0.0], [-20.0, 10.0, 0.0]], d=1)

    cmds.setAttr(eyebrow_bg_crv + '.overrideDisplayType', 1)
    background.append(eyebrow_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    return (gui_grp, controls)


def create_eye_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])

    """
    # Containers
    controls = []
    background = []

    # Top Label
    eyebrows_crv = create_text('EYES')
    force_center_pivot(eyebrows_crv)
    rescale(eyebrows_crv, 1.75)
    cmds.setAttr(eyebrows_crv + '.ty', 8.6)
    cmds.setAttr(eyebrows_crv + '.overrideDisplayType', 2)
    background.append(eyebrows_crv)

    # 1D Controls
    left_upper_eyelid_ctrl = create_slider_control('left_upperEyelid_offset_ctrl')
    left_lower_eyelid_ctrl = create_slider_control('left_lowerEyelid_offset_ctrl')
    left_blink_eyelid_ctrl = create_slider_control('left_blinkEyelid_ctrl')
    right_upper_eyelid_ctrl = create_slider_control('right_upperEyelid_offset_ctrl')
    right_lower_eyelid_ctrl = create_slider_control('right_lowerEyelid_offset_ctrl')
    right_blink_eyelid_ctrl = create_slider_control('right_blinkEyelid_ctrl')

    offset_slider_range(left_upper_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(left_lower_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(left_blink_eyelid_ctrl, offset_thickness=1)
    #
    offset_slider_range(right_upper_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(right_lower_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(right_blink_eyelid_ctrl, offset_thickness=1)

    # to_scale_down = [left_upper_eyelid_ctrl, left_lower_eyelid_ctrl, left_blink_eyelid_ctrl,
    #                  right_upper_eyelid_ctrl, right_lower_eyelid_ctrl, right_blink_eyelid_ctrl]
    to_scale_down = [left_blink_eyelid_ctrl, right_blink_eyelid_ctrl]
    for ctrl in to_scale_down:
        cmds.setAttr(ctrl[1] + '.sx', 0.5)
        cmds.setAttr(ctrl[1] + '.sy', 0.5)
        cmds.setAttr(ctrl[1] + '.sz', 0.5)

    # TY
    rescale(left_upper_eyelid_ctrl[1], 0.25, freeze=False)
    rescale(left_lower_eyelid_ctrl[1], 0.25, freeze=False)
    cmds.setAttr(left_upper_eyelid_ctrl[1] + '.tx', 15)
    cmds.setAttr(left_lower_eyelid_ctrl[1] + '.tx', 15)
    cmds.setAttr(left_upper_eyelid_ctrl[1] + '.ty', 3)
    cmds.setAttr(left_lower_eyelid_ctrl[1] + '.ty', -4)
    cmds.setAttr(left_blink_eyelid_ctrl[1] + '.tx', 5)

    rescale(right_upper_eyelid_ctrl[1], 0.25, freeze=False)
    rescale(right_lower_eyelid_ctrl[1], 0.25, freeze=False)
    cmds.setAttr(right_upper_eyelid_ctrl[1] + '.tx', -15)
    cmds.setAttr(right_lower_eyelid_ctrl[1] + '.tx', -15)
    cmds.setAttr(right_upper_eyelid_ctrl[1] + '.ty', 3)
    cmds.setAttr(right_lower_eyelid_ctrl[1] + '.ty', -4)
    cmds.setAttr(right_blink_eyelid_ctrl[1] + '.tx', -5)

    # Determine Grp Order
    controls.append(left_upper_eyelid_ctrl)
    controls.append(left_lower_eyelid_ctrl)
    controls.append(left_blink_eyelid_ctrl)
    controls.append(right_upper_eyelid_ctrl)
    controls.append(right_lower_eyelid_ctrl)
    controls.append(right_blink_eyelid_ctrl)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_eyes_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_eyes_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_eyes_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 8.6)
    cmds.setAttr(r_crv + '.ty', 8.6)
    cmds.setAttr(l_crv + '.tx', 3)
    cmds.setAttr(r_crv + '.tx', -3)
    background.append(l_crv)
    background.append(r_crv)

    # Main Label
    blink_crv = create_text('BLINK')
    blink_crv = cmds.rename(blink_crv, 'left_eye_' + blink_crv)
    force_center_pivot(blink_crv)
    rescale(blink_crv, .7)
    cmds.setAttr(blink_crv + '.ty', -7.3)
    cmds.setAttr(blink_crv + '.tx', 3.615)
    cmds.setAttr(blink_crv + '.overrideDisplayType', 2)
    right_blink_crv = cmds.duplicate(blink_crv, name=blink_crv.replace('left', 'right'))[0]
    cmds.setAttr(right_blink_crv + '.tx', -6.385)
    background.append(blink_crv)
    background.append(right_blink_crv)

    # Parent Groups
    gui_grp = cmds.group(name='eyes_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='eyes_background_grp', world=True, empty=True)

    # General Background
    eyebrow_bg_crv = cmds.curve(name='eyes_bg_crv', p=[[-20.0, 11.0, 0.0], [-20.0, -9.0, 0.0], [20.0, -9.0, 0.0],
                                                       [20.0, 11.0, 0.0], [-20.0, 11.0, 0.0]], d=1)

    cmds.setAttr(eyebrow_bg_crv + '.overrideDisplayType', 1)
    background.append(eyebrow_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    return (gui_grp, controls)


def create_facial_side_gui():
    parent_grp = cmds.group(empty=True, world=True, name='facial_side_gui_grp')
    eyebrow_ctrls = create_eyebrow_controls()
    eye_ctrls = create_eye_controls()
    mouth_ctrls = create_mouth_controls()
    cmds.move(43, eyebrow_ctrls[0], moveY=True)
    cmds.move(23, eye_ctrls[0], moveY=True)
    cmds.parent(eyebrow_ctrls[0], parent_grp)
    cmds.parent(eye_ctrls[0], parent_grp)
    cmds.parent(mouth_ctrls[0], parent_grp)
    return parent_grp


def offset_slider_range(create_slider_output, offset_by=5, offset_thickness=0):
    """
    Offsets the slider range updating its limits and shapes to conform to the new values
    Args:
        create_slider_output (tuple): The tuple output returned from the function "create_slider_control"
        offset_by: How much to offset, use positive numbers to make it bigger or negative to make it smaller
        offset_thickness: Amount to updates the shape curves so it continue to look proportional after the offset.

    """
    ctrl = create_slider_output[0]
    ctrl_grp = create_slider_output[1]

    current_min_trans_y_limit = cmds.getAttr(ctrl + '.minTransYLimit')
    current_max_trans_y_limit = cmds.getAttr(ctrl + '.maxTransYLimit')

    cmds.setAttr(ctrl + '.minTransYLimit', current_min_trans_y_limit - offset_by)
    cmds.setAttr(ctrl + '.maxTransYLimit', current_max_trans_y_limit + offset_by)

    children = cmds.listRelatives(ctrl_grp, children=True) or []
    for child in children:
        if '_bg_crv' in child:
            # Top
            cmds.move(offset_by, child + '.cv[1]', moveY=True, relative=True)
            cmds.move(offset_by, child + '.cv[2]', moveY=True, relative=True)
            # Bottom
            cmds.move(-offset_by, child + '.cv[3]', moveY=True, relative=True)
            cmds.move(-offset_by, child + '.cv[4]', moveY=True, relative=True)
            cmds.move(-offset_by, child + '.cv[0]', moveY=True, relative=True)

    if offset_thickness:
        for child in children:
            # Left
            cmds.move(-offset_thickness, child + '.cv[1]', moveX=True, relative=True)
            cmds.move(-offset_thickness, child + '.cv[4]', moveX=True, relative=True)
            cmds.move(-offset_thickness, child + '.cv[0]', moveX=True, relative=True)
            # Right
            cmds.move(offset_thickness, child + '.cv[2]', moveX=True, relative=True)
            cmds.move(offset_thickness, child + '.cv[3]', moveX=True, relative=True)

            # Top
            cmds.move(offset_thickness, child + '.cv[1]', moveY=True, relative=True)
            cmds.move(offset_thickness, child + '.cv[2]', moveY=True, relative=True)
            # Bottom
            cmds.move(-offset_thickness, child + '.cv[3]', moveY=True, relative=True)
            cmds.move(-offset_thickness, child + '.cv[4]', moveY=True, relative=True)
            cmds.move(-offset_thickness, child + '.cv[0]', moveY=True, relative=True)


def create_inbetween(obj, offset_suffix='Offset'):
    """
    Creates a in-between group usually used as offset
    Args:
        obj: Name of the control or object (string)
        offset_suffix: Suffix used for when creating the control (string)

    Returns:
        offset_grp (string)
    """
    obj_parent = cmds.listRelatives(obj, parent=True) or []
    if not obj_parent:
        cmds.warning('"' + obj + '" doesn\'t have a parent. Script cannot create an in-between group.')
        return

    offset_grp = cmds.group(
        name=obj_parent[0].replace(GRP_SUFFIX.capitalize(), offset_suffix + GRP_SUFFIX.capitalize()),
        world=True, empty=True)
    cmds.delete(cmds.parentConstraint(obj, offset_grp))
    cmds.parent(offset_grp, obj_parent[0])
    cmds.parent(obj, offset_grp)
    return offset_grp


def get_named_attr(object_name, attribute_name):
    """
    return the attribute if it exists
    Args:
        object_name: <str>
        attribute_name: <str>

    Returns:

    """
    if not cmds.objExists(f"{object_name}.{attribute_name}"):
        logger.warning(f"Couldn't find {object_name}.{attribute_name} in the scene")
        return
    return cmds.getAttr(f"{object_name}.{attribute_name}")


def get_metadata(object_name):
    """
    Looks for the metadata attribute on an object and then returns it as a dictionary
    Args:
        object_name:<str> name of the object to use as a search basis

    Returns:
        <dict> the metadata
        if the object doesnt exists, returns None
    """
    _metadata_string = get_named_attr(object_name, 'metadata')
    if not _metadata_string:
        logger.warning("Can't get the metadata to decode")
        return
    return json.loads(str(_metadata_string))


def find_item(name, item_type, log_fail=True):
    """
    Find object according to name and type
    Args:
        name: Name of the object to search for
        item_type: Type of the object (to narrow search)
        log_fail: Whether or not it should log a fail message

    Returns: Object name (if found) or NOne if it doesn't exist

    """
    all_of_type = cmds.ls(type=item_type) or []
    for obj in all_of_type:
        if obj.split(':')[-1] == name:
            return obj
    if log_fail:
        logger.warning("Couldn't find {item} of type {typ}".format(item=name, typ=item_type))


# Find item variations
find_transform = partial(find_item, item_type='transform')
find_joint = partial(find_item, item_type='joint')


def get_plus_minus_average_available_slot(node, input_type='input3D'):
    """
    Returns the number for the next available slot in a multi-input node of the type plusMinusAverage
    Args:
        node: Name of the node
        input_type: "input1D", "input2D" or "input3D"

    Returns:
        next_available_slot_index: (int) If there are no connections, then it returns zero
    """
    attributes = cmds.listAttr(node + '.' + input_type, multi=True) or []
    used_slots = []
    for attr in attributes:
        if len(attr.split('.')) == 1:
            used_slots.append(attr)
    return len(used_slots)


def select_items(*args):
    to_select = make_flat_list(args)
    cmds.select(to_select)


def get_children(root):
    return cmds.listRelatives(root, children=True)


def create_pin_control(jnt_name, scale_offset, create_offset_grp=True):
        """
        Creates a simple fk control. Used to quickly iterate through the creation of the finger controls

        Arg:
            jnt_name (string): Name of the joint that will be controlled
            scale_offset (float): The scale offset applied to the control before freezing it
            create_offset_grp (bool): Whether or not an offset group will be created
        Returns:
            control_name_and_group (tuple): The name of the generated control and the name of its ctrl group

        """
        fk_ctrl = cmds.curve(name=jnt_name.replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                             p=[[0.0, 0.0, 0.0], [0.0, 0.897, 0.0], [0.033, 0.901, 0.0], [0.064, 0.914, 0.0],
                                [0.091, 0.935, 0.0], [0.111, 0.961, 0.0], [0.124, 0.992, 0.0], [0.128, 1.025, 0.0],
                                [0.0, 1.025, 0.0], [0.0, 0.897, 0.0], [-0.033, 0.901, 0.0], [-0.064, 0.914, 0.0],
                                [-0.091, 0.935, 0.0], [-0.111, 0.961, 0.0], [-0.124, 0.992, 0.0], [-0.128, 1.025, 0.0],
                                [-0.124, 1.058, 0.0], [-0.111, 1.089, 0.0], [-0.091, 1.116, 0.0], [-0.064, 1.136, 0.0],
                                [-0.033, 1.149, 0.0], [0.0, 1.153, 0.0], [0.033, 1.149, 0.0], [0.064, 1.136, 0.0],
                                [0.091, 1.116, 0.0], [0.111, 1.089, 0.0], [0.124, 1.058, 0.0], [0.128, 1.025, 0.0],
                                [-0.128, 1.025, 0.0], [0.0, 1.025, 0.0], [0.0, 1.153, 0.0]], d=1)
        fk_ctrl_grp = cmds.group(name=fk_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

        fk_ctrl_offset_grp = ''
        if create_offset_grp:
            fk_ctrl_offset_grp = cmds.group(name=fk_ctrl + 'Offset' + GRP_SUFFIX.capitalize(), empty=True, world=True)
            cmds.parent(fk_ctrl, fk_ctrl_offset_grp)
            cmds.parent(fk_ctrl_offset_grp, fk_ctrl_grp)
        else:
            cmds.parent(fk_ctrl, fk_ctrl_grp)

        cmds.setAttr(fk_ctrl + '.scaleX', scale_offset)
        cmds.setAttr(fk_ctrl + '.scaleY', scale_offset)
        cmds.setAttr(fk_ctrl + '.scaleZ', scale_offset)
        cmds.makeIdentity(fk_ctrl, apply=True, scale=True)

        cmds.delete(cmds.parentConstraint(jnt_name, fk_ctrl_grp))
        if 'left_' in jnt_name:
            change_viewport_color(fk_ctrl, LEFT_CTRL_COLOR)
        elif 'right_' in jnt_name:
            change_viewport_color(fk_ctrl, RIGHT_CTRL_COLOR)

        for shape in cmds.listRelatives(fk_ctrl, s=True, f=True) or []:
            cmds.rename(shape, '{0}Shape'.format(fk_ctrl))

        return fk_ctrl, fk_ctrl_grp, fk_ctrl_offset_grp


def _get_object_namespaces(objectName):
    """
    Returns only the namespace of the object
    Args:
        objectName (string): Name of the object to extract the namespace from
    Returns:
        namespaces (string): Extracted namespaces combined into a string (without the name of the object)
                             e.g. Input = "One:Two:pSphere" Output = "One:Two:"
    """
    namespaces_list = objectName.split(':')
    object_namespace = ''
    for namespace in namespaces_list:
        if namespace != namespaces_list[-1]:
            object_namespace += namespace + ':'

    return object_namespace

class StripNamespace(object):
    """
    Context manager use to temporarily strip a namespace from all dependency nodes within a namespace.

    This allows nodes to masquerade as if they never had namespace, including those considered read-only
    due to file referencing.

    Usage:

        with StripNamespace('someNamespace') as stripped_nodes:
            print cmds.ls(stripped_nodes)
    """

    @classmethod
    def as_name(cls, uuid):
        """
        Convenience method to extract the name from uuid

        :type uuid: basestring
        :rtype: unicode|None
        """
        names = cmds.ls(uuid)
        return names[0] if names else None

    def __init__(self, namespace):
        if cmds.namespace(exists=namespace):
            self.original_names = {}  # (UUID, name_within_namespace)
            self.namespace = cmds.namespaceInfo(namespace, fn=True)
        else:
            raise ValueError('Could not locate supplied namespace, "{0}"'.format(namespace))

    def __enter__(self):
        for absolute_name in cmds.namespaceInfo(self.namespace, listOnlyDependencyNodes=True, fullName=True):

            # Ensure node was *not* auto-renamed (IE: shape nodes)
            if cmds.objExists(absolute_name):

                # get an api handle to the node
                try:
                    api_obj = om.MGlobal.getSelectionListByName(absolute_name).getDependNode(0)
                    api_node = om.MFnDependencyNode(api_obj)

                    # Remember the original name to return upon exit
                    uuid = api_node.uuid().asString()
                    self.original_names[uuid] = api_node.name()

                    # Strip namespace by renaming via api, bypassing read-only restrictions
                    without_namespace = api_node.name().replace(self.namespace, '')
                    api_node.setName(without_namespace)

                except RuntimeError:
                    pass  # Ignores Unrecognized objects (kFailure) Internal Errors

        return [self.as_name(uuid) for uuid in self.original_names]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for uuid, original_name in self.original_names.items():
            current_name = self.as_name(uuid)
            api_obj = om.MGlobal.getSelectionListByName(current_name).getDependNode(0)
            api_node = om.MFnDependencyNode(api_obj)
            api_node.setName(original_name)


def enforce_parent(obj_name, desired_parent):
    """
    Makes sure that the provided object is really parented under the desired parent element.
    Args:
        obj_name (string): Name of the source object enforce parenting (e.g. "pSphere1")
        desired_parent (string): Name of the desired parent element. You would expect to find obj_name inside it.

    Returns: True if re-parented, false if not re-parented or not found
    """
    if not cmds.objExists(obj_name):
        return False  # Source Object doesn't exist
    current_parent = cmds.listRelatives(obj_name, parent=True) or []
    if current_parent:
        current_parent = current_parent[0]
        if current_parent != desired_parent:
            cmds.parent(obj_name, desired_parent)
    else:
        cmds.parent(obj_name, desired_parent)


def is_entire_list_available(obj_list):
    """
    Checks if all objects are available (it exists) in Maya and return True or False accordingly
    Args:
        obj_list (list): List of strings (object names) or None objects

    Returns:
        True if all objects were found, False if one or more are missing.

    """
    for obj in obj_list:
        if obj:
            if not cmds.objExists(obj):
                return False
        else:
            return False
    return True


def orient_offset(obj_name, rot_offset, apply=True):
    """
    Rotates the target then freezes its transformation (used to quickly re-orient an object)

    Args:
        obj_name (string): Name of the object to orient (usually a joint)
        rot_offset (tuple): A tuple containing three floats (XYZ), used as rotate offset.
        apply (optional, bool): Whether to execute the function
    """
    if apply:
        cmds.setAttr(obj_name + '.rotateX', rot_offset[0])
        cmds.setAttr(obj_name + '.rotateY', rot_offset[1])
        cmds.setAttr(obj_name + '.rotateZ', rot_offset[2])
        cmds.makeIdentity(obj_name, apply=True, rotate=True)


# Tests
if __name__ == '__main__':
    # enforce_parent('pSphere1', 'head_offsetCtrl')
    output = ''
    # if cmds.objExists('slider_2dGrp'):
    #     cmds.delete('slider_2dGrp')
    # create_slider_control('1d_slider', initial_position='bottom')
    # output = create_2d_slider_control('slider_2d',
    #                                   initial_position_y='middle',
    #                                   initial_position_x='middle',
    #                                   ignore_range='top')
    # create_facial_controls()
    # print(output)
    # toggle_rigging_attr()
    # create_facial_controls()
    pass
