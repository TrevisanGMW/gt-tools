"""
 GT Rigger Utilities - Common functions used by the auto rigger scripts
 github.com/TrevisanGMW - 2021-12-10
"""
from gt_rigger_data import *
import maya.cmds as cmds
import maya.mel as mel
import random
import math
import re


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
    
            Parameters:
                obj (str): Name (path) of the object to change.
    
    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.useOutlinerColor', lock=True) is False:
        cmds.setAttr(obj + '.useOutlinerColor', 1)
        cmds.setAttr(obj + '.outlinerColorR', rgb_color[0])
        cmds.setAttr(obj + '.outlinerColorG', rgb_color[1])
        cmds.setAttr(obj + '.outlinerColorB', rgb_color[2])


def change_viewport_color(obj, rgb_color=(1, 1, 1)):
    """
    Changes the color of an object by changing the drawing override settings
            
            Parameters:
                    obj (string): Name of the object to change color
                    rgb_color (tuple): RGB color 
                        
    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.overrideEnabled', lock=True) is False:
        cmds.setAttr(obj + '.overrideEnabled', 1)
        cmds.setAttr(obj + '.overrideRGBColors', 1)
        cmds.setAttr(obj + '.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])


def add_node_note(obj, note_string):
    """ Addes a note to the provided node (It can be seen at the bottom of the attribute editor)
    
            Parameters:
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

    def caculate_distance(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
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

        if (num < 20):
            return d[num]

        if (num < 100):
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + '-' + d[num % 10]

        if (num < k):
            if num % 100 == 0:
                return d[num // 100] + ' hundred'
            else:
                return d[num // 100] + ' hundred and ' + int_to_en(num % 100)

        if (num < m):
            if num % k == 0:
                return int_to_en(num // k) + ' thousand'
            else:
                return int_to_en(num // k) + ' thousand, ' + int_to_en(num % k)

        if (num < b):
            if (num % m) == 0:
                return int_to_en(num // m) + ' million'
            else:
                return int_to_en(num // m) + ' million, ' + int_to_en(num % m)

        if (num < t):
            if (num % b) == 0:
                return int_to_en(num // b) + ' billion'
            else:
                return int_to_en(num // b) + ' billion, ' + int_to_en(num % b)

        if (num % t == 0):
            return int_to_en(num // t) + ' trillion'
        else:
            return int_to_en(num // t) + ' trillion, ' + int_to_en(num % t)

        # raise AssertionError('num is too large: %s' % str(num))

    ########## Start of Make Stretchy Function ##########
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
            mag = caculate_distance(ik_handle_ws_pos[0], ik_handle_ws_pos[1], ik_handle_ws_pos[2], jnt_ws_pos[0],
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


def create_joint_curve(name, scale, initial_position=(0, 0, 0)):
    """
    Creates a curve that looks like a joint to be used as a proxy 
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve
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
                custom_shape (string): Doesn't generate an arrow. Use the provided shape instead. Name of a curve shape. (Use "start_cv_list" and "end_cv_list" to set cvs)
                start_cv_list (list): A list of strings. In case you want to overwrite the original curve, you might want to provide new cvs. e.g "["cv[0:2]", "cv[8:10]"]"
                end_cv_list (list):  A list of strings. In case you want to overwrite the original curve, you might want to provide new cvs. e.g "["cv[0:2]", "cv[8:10]"]"
                
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
    Creates a finger curl control. This function was made for a very specific use, so it already orients the control accordingly.
    
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
    Create a button for a custom rig interface to the current shelf. It contains seamless FK/IK swtichers and pose management tools.
    """
    create_shelf_button(
        "\"\"\"\n Custom Rig Interface for GT Auto Biped Rigger.\n github.com/TrevisanGMW/gt-tools - 2021-01-05\n \n 1.0 - 2021-01-05\n Initial Release\n\n 1.1 - 2021-05-11\n Made script compatible with Python 3.0 (Maya 2022)\n\n 1.2 - 2021-10-28\n Added mirror IK functions\n Added reset pose function\n Changed it to accept namespaces with or without \":\"\n  \n 1.3 - 2021-10-29\n Changed the name from \"Seamless IK/FK Switch\" to \"Custom Rig Interface\"\n Added functions to mirror and reset FK controls\n Added center controls to reset pose function\n Added custom rig name (if not empty, it will display a message describing unique rig target)\n Added system to get and set persistent settings to store the namespace input\n Added warning message reminding user to check their namespace in case elements are not found\n \n 1.3.1 - 2021-11-01\n Changed versioning system to semantic to account for patches\n Fixed some typos in the \"locked\" message for when trying to mirror\n Added scale mirroring functions (fixes finger abduction pose)\n Included curl controls in the mirroring list\n \n 1.3.2 - 2021-11-03\n Added IK fingers to mirroring functions\n \n 1.3.3 - 2021-11-04\n Added animation import/export functions. (\".anim\" with \".json\" data)\n Changed the pose file extension to \".pose\" instead of \".json\" to avoid confusion\n Added animation mirroring functions\n \n 1.3.4 - 2021-11-08\n Add settings menu\n Made UI aware of FK/IK state\n Recreated part of the UI to use Tabs\n Improved switch functions with a mechanism to auto create keyframes (sparse or bake)\n Added inView feedback explaining switch information\n Fixed issue where the arm pole vector wouldn't mirror properly\n Added option to reset persistent settings\n \n 1.3.5 - 2021-11-10\n Added animation and pose reset\n Updates animation functions to account for tangents and other key properties\n \n 1.3.6 - 2021-11-12\n Allowed for multiple instances (in case animating multiple characters)\n Changed icons and assigned an alternative one for extra instances\n Added a missing import for \"sys\"\n \n 1.3.7 - 2021-11-23\n Updated switcher to be compatible with new offset controls\n Added inView message for when auto clavicle is active so the user doesn't think the control is popping\n \n 1.3.8 - 2021-11-23\n Included a few missing controls to the pose and animation management control lists\n  \n 1.3.9 - 2021-11-30\n Updated the script so it works with the new offset controls\n Accounted for new wrist reference control\n \n 1.3.10 - 2021-12-01\n Added option to define whether or not to transfer data to offset control or control\n \n 1.3.11 - 2021-12-02\n Made most functions private\n Added function to extract rig metadata and update behaviour according to orientation used\n \n TODO:\n    Include function to extract character's metadata\n    Created flip pose function\n    Convert GUI to QT\n    Add Flip options\n    Overwrite keys for animation functions\n    Add Namespace picker (button to the right of the namespace textfield)\n    Option to save pose thumbnail when exporting it \n    Add option to open multiple instances\n    \n\"\"\"\ntry:\n    from shiboken2 import wrapInstance\nexcept ImportError:\n    from shiboken import wrapInstance\n    \ntry:\n    from PySide2.QtGui import QIcon\n    from PySide2.QtWidgets import QWidget\nexcept ImportError:\n    from PySide.QtGui import QIcon, QWidget\n\nfrom maya import OpenMayaUI as omui\nimport maya.cmds as cmds\nimport random\nimport json\nimport copy\nimport sys\nimport os\n\n\n# Script Name\nscript_name = 'GT Custom Rig Interface'\nunique_rig = '' # If provided, it will be used in the window title\n\n# Version:\nscript_version = \"1.3.11\"\n\n# Python Version\npython_version = sys.version_info.major\n\n# FK/IK Swticher Elements                    \nleft_arm_seamless_dict = { 'switch_ctrl' : 'left_arm_switch_ctrl', # Switch Ctrl\n                           'end_ik_ctrl' : 'left_wrist_ik_offsetCtrl', # IK Elements\n                           'pvec_ik_ctrl' : 'left_elbow_ik_ctrl',\n                           'base_ik_jnt' :  'left_shoulder_ik_jnt',\n                           'mid_ik_jnt' : 'left_elbow_ik_jnt',\n                           'end_ik_jnt' : 'left_wrist_ik_jnt',\n                           'base_fk_ctrl' : 'left_shoulder_ctrl', # FK Elements\n                           'mid_fk_ctrl' : 'left_elbow_ctrl',\n                           'end_fk_ctrl' : 'left_wrist_ctrl' ,\n                           'base_fk_jnt' :  'left_shoulder_fk_jnt',\n                           'mid_fk_jnt' : 'left_elbow_fk_jnt',\n                           'end_fk_jnt' : 'left_wrist_fk_jnt',\n                           'mid_ik_reference' : 'left_elbowSwitch_loc',\n                           'end_ik_reference' : 'left_wristSwitch_loc',\n                           'incompatible_attr_holder' : 'left_wrist_ik_ctrl', # Auto Clavicle\n                         }\n\nright_arm_seamless_dict = { 'switch_ctrl' : 'right_arm_switch_ctrl', # Switch Ctrl\n                            'end_ik_ctrl' : 'right_wrist_ik_offsetCtrl', # IK Elements\n                            'pvec_ik_ctrl' : 'right_elbow_ik_ctrl',\n                            'base_ik_jnt' :  'right_shoulder_ik_jnt',\n                            'mid_ik_jnt' : 'right_elbow_ik_jnt',\n                            'end_ik_jnt' : 'right_wrist_ik_jnt',\n                            'base_fk_ctrl' : 'right_shoulder_ctrl', # FK Elements\n                            'mid_fk_ctrl' : 'right_elbow_ctrl',\n                            'end_fk_ctrl' : 'right_wrist_ctrl' ,\n                            'base_fk_jnt' :  'right_shoulder_fk_jnt',\n                            'mid_fk_jnt' : 'right_elbow_fk_jnt',\n                            'end_fk_jnt' : 'right_wrist_fk_jnt',\n                            'mid_ik_reference' : 'right_elbowSwitch_loc',\n                            'end_ik_reference' : 'right_wristSwitch_loc',\n                            'incompatible_attr_holder' : 'right_wrist_ik_ctrl', # Auto Clavicle\n                           }\n                            \nleft_leg_seamless_dict = { 'switch_ctrl' : 'left_leg_switch_ctrl', # Switch Ctrl\n                           'end_ik_ctrl' : 'left_foot_ik_offsetCtrl', # IK Elements\n                           'pvec_ik_ctrl' : 'left_knee_ik_ctrl',\n                           'base_ik_jnt' :  'left_hip_ik_jnt',\n                           'mid_ik_jnt' : 'left_knee_ik_jnt',\n                           'end_ik_jnt' : 'left_ankle_ik_jnt',\n                           'base_fk_ctrl' : 'left_hip_ctrl', # FK Elements\n                           'mid_fk_ctrl' : 'left_knee_ctrl',\n                           'end_fk_ctrl' : 'left_ankle_ctrl' , \n                           'base_fk_jnt' :  'left_hip_fk_jnt',\n                           'mid_fk_jnt' : 'left_knee_fk_jnt',\n                           'end_fk_jnt' : 'left_ankle_fk_jnt',\n                           'mid_ik_reference' : 'left_kneeSwitch_loc',\n                           'end_ik_reference' : 'left_ankleSwitch_loc', #left_ankleSwitch_loc\n                           'incompatible_attr_holder' : '',\n                          }\n                           \nright_leg_seamless_dict = { 'switch_ctrl' : 'right_leg_switch_ctrl', # Switch Ctrl\n                            'end_ik_ctrl' : 'right_foot_ik_offsetCtrl', # IK Elements\n                            'pvec_ik_ctrl' : 'right_knee_ik_ctrl',\n                            'base_ik_jnt' :  'right_hip_ik_jnt',\n                            'mid_ik_jnt' : 'right_knee_ik_jnt',\n                            'end_ik_jnt' : 'right_ankle_ik_jnt',\n                            'base_fk_ctrl' : 'right_hip_ctrl', # FK Elements\n                            'mid_fk_ctrl' : 'right_knee_ctrl',\n                            'end_fk_ctrl' : 'right_ankle_ctrl' ,\n                            'base_fk_jnt' :  'right_hip_fk_jnt',\n                            'mid_fk_jnt' : 'right_knee_fk_jnt',\n                            'end_fk_jnt' : 'right_ankle_fk_jnt',\n                            'mid_ik_reference' : 'right_kneeSwitch_loc',\n                            'end_ik_reference' : 'right_ankleSwitch_loc',\n                            'incompatible_attr_holder' : '',\n                          }\n                          \nseamless_elements_dictionaries = [right_arm_seamless_dict, left_arm_seamless_dict, left_leg_seamless_dict, right_leg_seamless_dict]\n\n# Mirror Elements\nnamespace_separator = ':'\nleft_prefix = 'left'\nright_prefix = 'right'\nnot_inverted = (False, False, False)\ninvert_x = (True, False, False)\ninvert_y = (False, True, False)\ninvert_z = (False, False, True)\ninvert_yz = (False, True, True)\ninvert_all = (True, True, True)\n\n\n# Dictionary Pattern:\n# Key: Control name (if not in the center, remove prefix)\n# Value: A list with two tuples. [(Is Translate XYZ inverted?), (Is Rotate XYZ inverted?), Is mirroring scale?]\n# Value Example: '_fingers_ctrl': [not_inverted, not_inverted, True] = Not inverting Translate XYZ. Not inverting Rotate XYZ. Yes, mirroring scale.\ngt_ab_general_ctrls = {# Fingers Automation\n                   '_fingers_ctrl': [not_inverted, not_inverted, True],\n                   '_thumbCurl_ctrl': [not_inverted, not_inverted],\n                   '_indexCurl_ctrl': [not_inverted, not_inverted],\n                   '_middleCurl_ctrl': [not_inverted, not_inverted],\n                   '_ringCurl_ctrl': [not_inverted, not_inverted],\n                   '_pinkyCurl_ctrl': [not_inverted, not_inverted],\n                   \n                   # Fingers FK\n                   '_thumb03_ctrl': [not_inverted, not_inverted],\n                   '_thumb02_ctrl': [not_inverted, not_inverted],\n                   '_thumb01_ctrl': [not_inverted, not_inverted],\n                   '_index01_ctrl': [not_inverted, not_inverted],\n                   '_middle02_ctrl': [not_inverted, not_inverted],\n                   '_middle01_ctrl': [not_inverted, not_inverted],\n                   '_index03_ctrl': [not_inverted, not_inverted],\n                   '_index02_ctrl': [not_inverted, not_inverted],\n                   '_ring03_ctrl': [not_inverted, not_inverted],\n                   '_ring02_ctrl': [not_inverted, not_inverted],\n                   '_ring01_ctrl': [not_inverted, not_inverted],\n                   '_middle03_ctrl': [not_inverted, not_inverted],\n                   '_pinky03_ctrl': [not_inverted, not_inverted],\n                   '_pinky02_ctrl': [not_inverted, not_inverted],\n                   '_pinky01_ctrl': [not_inverted, not_inverted],\n                   \n                   # Finger IK\n                   '_thumb_ik_ctrl': [invert_z, invert_x],\n                   '_index_ik_ctrl': [invert_z, invert_x],\n                   '_middle_ik_ctrl': [invert_z, invert_x],\n                   '_ring_ik_ctrl': [invert_z, invert_x],\n                   '_pinky_ik_ctrl': [invert_z, invert_x],\n                   # Clavicle\n                   '_clavicle_ctrl': [not_inverted, not_inverted],\n                   # Eyes\n                   '_eye_ctrl': [invert_x, not_inverted],\n                 }   \n\ngt_ab_ik_ctrls = { # Arm\n                   '_elbow_ik_ctrl': [invert_x, not_inverted], \n                   '_wrist_ik_ctrl': [invert_all, not_inverted],\n                   '_wrist_ik_offsetCtrl': [invert_all, not_inverted],\n                   # Leg\n                   '_heelRoll_ctrl': [invert_x, not_inverted],\n                   '_ballRoll_ctrl': [invert_x, not_inverted],\n                   '_toeRoll_ctrl': [invert_x, not_inverted],\n                   '_toe_upDown_ctrl': [invert_x, not_inverted],\n                   '_foot_ik_ctrl': [invert_x, invert_yz],\n                   '_foot_ik_offsetCtrl': [invert_x, invert_yz],\n                   '_knee_ik_ctrl': [invert_x, not_inverted],\n                 }\n                 \ngt_ab_ik_ctrls_default = copy.deepcopy(gt_ab_ik_ctrls) #@@@\n                   \ngt_ab_fk_ctrls = {# Arm\n                   '_shoulder_ctrl': [invert_all, not_inverted],\n                   '_elbow_ctrl': [invert_all, not_inverted],\n                   '_wrist_ctrl': [invert_all, not_inverted],\n                  # Leg\n                   '_hip_ctrl': [invert_x, invert_yz],\n                   '_knee_ctrl': [invert_all, not_inverted],\n                   '_ankle_ctrl': [invert_all, not_inverted],\n                   '_ball_ctrl': [invert_all, not_inverted],\n                 }\n                       \ngt_ab_center_ctrls = ['cog_ctrl', \n                      'cog_offsetCtrl', \n                      'hip_ctrl', \n                      'hip_offsetCtrl', \n                      'spine01_ctrl', \n                      'spine02_ctrl', \n                      'spine03_ctrl', \n                      'spine04_ctrl', \n                      'cog_ribbon_ctrl', \n                      'chest_ribbon_offsetCtrl', \n                      'spine_ribbon_ctrl', \n                      'chest_ribbon_ctrl',\n                      'neckBase_ctrl',\n                      'neckMid_ctrl',\n                      'head_ctrl',\n                      'head_offsetCtrl',\n                      'jaw_ctrl',\n                      'main_eye_ctrl',\n                      'left_eye_ctrl',\n                      'right_eye_ctrl',\n                      ]            \n\ngt_custom_rig_interface_settings = {\n                                    'namespace' : '',\n                                    'auto_key_switch' : True,\n                                    'auto_key_method_bake' : True,\n                                    'auto_key_start_frame' : 1,\n                                    'auto_key_end_frame' : 10,\n                                    'pose_export_thumbnail' : False,\n                                    'allow_multiple_instances' : False,\n                                    'offset_target' : True,\n                                   }\n                   \ngt_custom_rig_interface_settings_default = copy.deepcopy(gt_custom_rig_interface_settings)\n\n\n# Manage Persistent Settings\ndef _get_persistent_settings_rig_interface():\n    ''' \n    Checks if persistant settings for GT Auto Biped Rig Interface exists and loads it if this is the case.\n    It assumes that persistent settings were stored using the cmds.optionVar function.\n    '''\n    # Check if there is anything stored\n    stored_setup_exists = cmds.optionVar(exists=(\"gt_auto_biped_rig_interface_setup\"))\n  \n    if stored_setup_exists:\n        stored_settings = {}\n        try:\n            stored_settings = eval(str(cmds.optionVar(q=(\"gt_auto_biped_rig_interface_setup\"))))\n            for stored_item in stored_settings:\n                for item in gt_custom_rig_interface_settings:\n                    if stored_item == item:\n                        gt_custom_rig_interface_settings[item] = stored_settings.get(stored_item)\n        except:\n            print('Couldn\\'t load persistent settings, try resetting it in the help menu.')\n\n\ndef _set_persistent_settings_rig_interface():\n    ''' \n    Stores persistant settings for GT Auto Biped Rig Interface.\n    It converts the dictionary into a list for easy storage. (The get function converts it back to a dictionary)\n    It assumes that persistent settings were stored using the cmds.optionVar function.\n    '''\n    cmds.optionVar( sv=('gt_auto_biped_rig_interface_setup', str(gt_custom_rig_interface_settings)))\n\n\ndef _reset_persistent_settings_rig_interface():\n    ''' Resets persistant settings for GT Auto Biped Rig Interface '''\n    cmds.optionVar( remove='gt_auto_biped_rig_interface_setup' )\n    gt_custom_rig_interface_settings =  gt_custom_rig_interface_settings_default\n    cmds.optionVar( sv=('gt_auto_biped_rig_interface_setup', str(gt_custom_rig_interface_settings_default)))\n    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')\n    try:\n        cmds.evalDeferred('build_gui_custom_rig_interface()')\n    except:\n        try:\n            build_gui_custom_rig_interface()\n        except:\n            try:\n                cmds.evalDeferred('gt_biped_rig_interface.build_gui_custom_rig_interface()')\n            except:\n                pass\n\ndef _get_metadata(namespace):\n    ''' \n    Attempts to retrieve metadata from the rig. \n    It can be found under the \"main_ctrl.metadata\" as a string. The string is in json format.\n    This is useful when an different settings were used, such as different skeleton or orientation.\n    \n        Parameters:\n            namespace (string): Expected namespace for when looking for main_ctrl\n    \n        Returns:\n            dictionary or None: Returns data if available (JSON format becomes a dictionary)\n    '''\n    _main_ctrl = namespace + 'main_ctrl'\n    if not cmds.objExists(_main_ctrl):\n        return None    \n    try:\n        metadata_str = cmds.getAttr(_main_ctrl + '.metadata')\n        return json.loads(str(metadata_str))\n    except:\n        return None\n\n             \n# Main Window ============================================================================\ndef build_gui_custom_rig_interface():\n    \n    # Retrieve Persistent Settings\n    _get_persistent_settings_rig_interface()\n    \n    rig_interface_window_name = 'build_gui_custom_rig_interface'\n    is_secondary_instance = False\n    if cmds.window(rig_interface_window_name, exists=True) and not gt_custom_rig_interface_settings.get('allow_multiple_instances'):\n        cmds.deleteUI(rig_interface_window_name)  \n    # In case it's a secondary instance \n    if gt_custom_rig_interface_settings.get('allow_multiple_instances'):\n        if cmds.window(rig_interface_window_name, exists=True):\n            rig_interface_window_name = rig_interface_window_name + '_' + str(random.random()).replace('.','')\n            is_secondary_instance = True\n            \n            gt_custom_rig_interface_settings_instanced = copy.deepcopy(gt_custom_rig_interface_settings)\n   \n\n\n    # Main GUI Start Here =================================================================================\n    def update_fk_ik_buttons():\n        '''\n        Updates the background color of the FK/IK buttons according to the value of the current influenceSwitch attribute.\n        This attempts to make the UI \"aware\" of the current state of the controls.\n        '''\n        active_color = (.6,.6,.6)\n        inactive_color = (.36,.36,.36)\n        ctrl_btn_lists = [\n                          [right_arm_seamless_dict, right_arm_fk_btn, right_arm_ik_btn],\n                          [left_arm_seamless_dict, left_arm_fk_btn, left_arm_ik_btn],\n                          [right_leg_seamless_dict, right_leg_fk_btn, right_leg_ik_btn],\n                          [left_leg_seamless_dict, left_leg_fk_btn, left_leg_ik_btn]\n                         ]\n        for ctrl_btns in ctrl_btn_lists:\n            if cmds.objExists(gt_custom_rig_interface_settings.get('namespace') + namespace_separator + ctrl_btns[0].get('switch_ctrl')):\n                try:\n                    current_system = cmds.getAttr(gt_custom_rig_interface_settings.get('namespace') + namespace_separator + ctrl_btns[0].get('switch_ctrl') + '.influenceSwitch')\n                    if current_system < 0.5:\n                        cmds.button(ctrl_btns[1], e=True, bgc=active_color) # FK Button\n                        cmds.button(ctrl_btns[2], e=True, bgc=inactive_color) # IK Button\n                    else:\n                        cmds.button(ctrl_btns[2], e=True, bgc=active_color) # FK Button\n                        cmds.button(ctrl_btns[1], e=True, bgc=inactive_color) # IK Button\n                except:\n                    pass\n            else:\n                cmds.button(ctrl_btns[2], e=True, bgc=inactive_color) # FK Button\n                cmds.button(ctrl_btns[1], e=True, bgc=inactive_color) # IK Button\n    \n\n    def update_stored_settings(is_instance=False):\n        '''\n        Extracts the namespace used and stores it as a persistent variable\n        This function also calls \"update_fk_ik_buttons()\" so it updates the UI\n        \n                    Parameters:\n                        is_instance (optional, bool): Allow a bool argument to determine if the settings are supposed to be stored or not\n                                                      This is used for secondary instances (multiple windows)\n                                              \n        '''\n        gt_custom_rig_interface_settings['namespace'] = cmds.textField(namespace_txt, q=True, text=True)\n        gt_custom_rig_interface_settings['auto_key_switch'] = cmds.checkBox(auto_key_switch_chk, q=True, value=True)\n        gt_custom_rig_interface_settings['auto_key_switch'] = cmds.checkBox(auto_key_switch_chk, q=True, value=True)\n        gt_custom_rig_interface_settings['auto_key_method_bake'] = cmds.radioButton(auto_key_method_rb1, query=True, select=True)\n        gt_custom_rig_interface_settings['auto_key_start_frame'] = cmds.intField(auto_key_start_int_field, q=True, value=0)\n        gt_custom_rig_interface_settings['auto_key_end_frame'] = cmds.intField(auto_key_end_int_field, q=True, value=0)\n        \n        if not gt_custom_rig_interface_settings.get('offset_target'):\n            for data in seamless_elements_dictionaries:\n                data['end_ik_ctrl'] = data.get('end_ik_ctrl').replace('offsetCtrl','ctrl')\n        else:\n            for data in seamless_elements_dictionaries:\n                data['end_ik_ctrl'] = data.get('end_ik_ctrl').replace('ctrl','offsetCtrl')\n                \n        metadata = _get_metadata(gt_custom_rig_interface_settings.get('namespace'))\n        if metadata: \n            if metadata.get('worldspace_ik_orient'):\n                print('yes')\n                gt_ab_ik_ctrls['_wrist_ik_ctrl'] = [(True, False, False), (False, True, True)]\n                gt_ab_ik_ctrls['_wrist_ik_offsetCtrl'] = [(True, False, False), (False, True, True)]\n            else:\n                gt_ab_ik_ctrls['_wrist_ik_ctrl'] = gt_ab_ik_ctrls_default.get('_wrist_ik_ctrl')\n                gt_ab_ik_ctrls['_wrist_ik_offsetCtrl'] = gt_ab_ik_ctrls_default.get('_wrist_ik_offsetCtrl')\n\n        if gt_custom_rig_interface_settings.get('auto_key_switch'):\n            cmds.radioButton(auto_key_method_rb1, e=True, en=True)\n            cmds.radioButton(auto_key_method_rb2, e=True, en=True)\n            cmds.rowColumnLayout(switch_range_column, e=True, en=True)\n        else:\n            cmds.radioButton(auto_key_method_rb1, e=True, en=False)\n            cmds.radioButton(auto_key_method_rb2, e=True, en=False)\n            cmds.rowColumnLayout(switch_range_column, e=True, en=False)\n        \n        if not is_instance: # Doesn't update persistent settings for secondary instances\n            _set_persistent_settings_rig_interface()\n        update_fk_ik_buttons()\n\n\n    def update_switch(ik_fk_dict, direction='ik_to_fk', is_auto_switch=False):\n        '''\n        Runs the switch function using the parameters provided in the UI\n        Also updates the UI to keep track of the FK/IK state.\n        \n                Parameters:\n                     ik_fk_dict (dict): A dicitionary containg the elements that are part of the system you want to switch\n                     direction (optinal, string): Either \"fk_to_ik\" or \"ik_to_fk\". It determines what is the source and what is the target.\n        '''\n        method = 'bake' if gt_custom_rig_interface_settings.get('auto_key_method_bake') else 'sparse' \n        \n        if is_auto_switch:\n            _fk_ik_switch_auto(ik_fk_dict, \n                                             namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator,\n                                             keyframe=gt_custom_rig_interface_settings.get('auto_key_switch'),\n                                             start_time=int(gt_custom_rig_interface_settings.get('auto_key_start_frame')), \n                                             end_time=int(gt_custom_rig_interface_settings.get('auto_key_end_frame')), \n                                             method=method\n                                             )\n\n        else:\n            _fk_ik_switch(ik_fk_dict, \n                                        direction, \n                                        namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator,\n                                        keyframe=gt_custom_rig_interface_settings.get('auto_key_switch'),\n                                        start_time=int(gt_custom_rig_interface_settings.get('auto_key_start_frame')), \n                                        end_time=int(gt_custom_rig_interface_settings.get('auto_key_end_frame')), \n                                        method=method\n                                        )\n\n        update_fk_ik_buttons()\n\n    def invert_stored_setting(key_string):\n        '''\n        Used for boolean values, it inverts the value, so if True it becomes False and vice-versa.\n        It also stores the new values after they are changed so future instances remember it.\n        \n                Parameters:\n                    key_string (string) : Key name, used to determine what bool value to flip\n        '''\n        gt_custom_rig_interface_settings[key_string] = not gt_custom_rig_interface_settings.get(key_string)\n        _set_persistent_settings_rig_interface()\n        update_stored_settings()\n                       \n    def get_auto_key_current_frame(target_integer_field='start', is_instance=False):\n        '''\n        Gets the current frame and auto fills an integer field.\n        \n                Parameters:\n                    target_integer_field (optional, string) : Gets the current timeline frame and feeds it into the start or end integer field.\n                                                              Can only be \"start\" or \"end\". Anything else will be understood as \"end\".\n                    is_instance (optional, bool): Allow a bool argument to determine if the settings are supposed to be stored or not\n                                                      This is used for secondary instances (multiple windows)\n        \n        '''\n        current_time = cmds.currentTime(q=True)\n        if target_integer_field == 'start':\n            cmds.intField(auto_key_start_int_field, e=True, value=current_time)\n        else:\n            cmds.intField(auto_key_end_int_field, e=True, value=current_time)\n\n        update_stored_settings(is_instance)\n    \n    \n    def mirror_fk_ik_pose(source_side='right'):\n        '''\n        Runs a full pose mirror function.\n        \n                Parameters:\n                     source_side (optinal, string): Either \"right\" or \"left\". It determines what is the source and what is the target of the mirror.\n        '''\n        update_stored_settings()\n        _pose_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls, gt_ab_fk_ctrls], source_side, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)\n        \n    def mirror_animation(source_side='right'): #@@@\n        '''\n        Runs a full pose mirror function.\n        \n                Parameters:\n                     source_side (optinal, string): Either \"right\" or \"left\". It determines what is the source and what is the target of the mirror.\n        '''\n        update_stored_settings()\n        _anim_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls, gt_ab_fk_ctrls], source_side, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)\n        \n        \n    def reset_animation_and_pose():\n        '''\n        Deletes Keyframes and Resets pose back to default\n        '''\n        _anim_reset(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)\n        _pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)\n    \n\n    def build_custom_help_window(input_text, help_title=''):\n        ''' \n        Creates a help window to display the provided text\n\n                Parameters:\n                    input_text (string): Text used as help, this is displayed in a scroll fields.\n                    help_title (optinal, string)\n        '''\n        window_name = help_title.replace(\" \",\"_\").replace(\"-\",\"_\").lower().strip() + \"_help_window\"\n        if cmds.window(window_name, exists=True):\n            cmds.deleteUI(window_name, window=True)\n\n        cmds.window(window_name, title= help_title + \" Help\", mnb=False, mxb=False, s=True)\n        cmds.window(window_name, e=True, s=True, wh=[1,1])\n\n        main_column = cmds.columnLayout(p= window_name)\n       \n        # Title Text\n        cmds.separator(h=12, style='none') # Empty Space\n        cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment\n        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column\n        cmds.text(help_title + ' Help', bgc=(.4, .4, .4),  fn='boldLabelFont', align='center')\n        cmds.separator(h=10, style='none', p=main_column) # Empty Space\n\n        # Body ====================       \n        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)\n        \n        help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn='smallPlainLabelFont')\n     \n        cmds.scrollField(help_scroll_field, e=True, ip=0, it=input_text)\n        cmds.scrollField(help_scroll_field, e=True, ip=1, it='') # Bring Back to the Top\n        \n        # Close Button \n        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)\n        cmds.separator(h=10, style='none')\n        cmds.button(l='OK', h=30, c=lambda args: close_help_gui())\n        cmds.separator(h=8, style='none')\n        \n        # Show and Lock Window\n        cmds.showWindow(window_name)\n        cmds.window(window_name, e=True, s=False)\n        \n        # Set Window Icon\n        qw = omui.MQtUtil.findWindow(window_name)\n        if python_version == 3:\n            widget = wrapInstance(int(qw), QWidget)\n        else:\n            widget = wrapInstance(long(qw), QWidget)\n        icon = QIcon(':/question.png')\n        widget.setWindowIcon(icon)\n        \n        def close_help_gui():\n            ''' Closes help windows '''\n            if cmds.window(window_name, exists=True):\n                cmds.deleteUI(window_name, window=True)\n        # Custom Help Dialog Ends Here =================================================================================\n        \n    # Build UI.\n    script_title = script_name\n    if unique_rig != '':\n        script_title = 'GT - Rig Interface for ' + unique_rig\n      \n    if is_secondary_instance:\n      script_version_title = '  (Extra Instance)'\n    else:\n      script_version_title = '  (v' + script_version + ')'\n      \n    build_gui_custom_rig_interface = cmds.window(rig_interface_window_name, title=script_title + script_version_title,\\\n                          titleBar=True, mnb=False, mxb=False, sizeable =True)\n\n    cmds.window(rig_interface_window_name, e=True, s=True, wh=[1,1])\n\n    content_main = cmds.columnLayout(adj = True)\n\n    # Title Text\n    title_bgc_color = (.4, .4, .4)\n    cmds.separator(h=10, style='none') # Empty Space\n    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment\n    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column\n    cmds.text(\" \", bgc=title_bgc_color) # Tiny Empty Green Space\n    cmds.text(script_title, bgc=title_bgc_color,  fn=\"boldLabelFont\", align=\"left\")\n    cmds.button( l =\"Help\", bgc=title_bgc_color, c=lambda x:_open_gt_tools_documentation())\n    cmds.separator(h=5, style='none') # Empty Space\n        \n    # Body ====================\n    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)\n    \n    cmds.text('Namespace:')\n    namespace_txt = cmds.textField(text=gt_custom_rig_interface_settings.get('namespace'), pht='Namespace:: (Optional)', cc=lambda x:update_stored_settings(is_secondary_instance))\n    \n    cmds.separator(h=10, style='none') # Empty Space\n    \n    form = cmds.formLayout()\n    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)\n    cmds.formLayout(form, edit=True, attachForm=((tabs, 'top', 0), (tabs, 'left', 0), (tabs, 'bottom', 0), (tabs, 'right', 0)) )\n\n    ############# FK/IK Switch Tab #############\n    btn_margin = 5\n    fk_ik_switch_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 246)], cs=[(1,0)], p=tabs)\n\n    fk_ik_btn_width = 59\n    cw_fk_ik_states = [(1, fk_ik_btn_width),(2, fk_ik_btn_width),(3, fk_ik_btn_width),(4, fk_ik_btn_width)]\n    cs_fk_ik_states = [(1,2), (2,2), (3,3), (4,2)]\n    \n    switch_btn_width = 120\n    cw_fk_ik_switches = [(1, switch_btn_width),(2, switch_btn_width)]\n    cs_fk_ik_switches = [(1,2), (2,3)]\n    \n    arms_text = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=fk_ik_switch_tab)\n    cmds.separator(h=2, style='none') # Empty Space\n    cmds.separator(h=2, style='none') # Empty Space\n    cmds.text('Right Arm:', p=arms_text) #R\n    cmds.text('Left Arm:', p=arms_text) #L\n    \n    arms_switch_state_column = cmds.rowColumnLayout(nc=4, cw=cw_fk_ik_states, cs=cs_fk_ik_states, p=fk_ik_switch_tab)\n    right_arm_fk_btn = cmds.button(l =\"FK\", c=lambda x:update_switch(right_arm_seamless_dict, 'ik_to_fk'), p=arms_switch_state_column) #R\n    right_arm_ik_btn = cmds.button(l =\"IK\", c=lambda x:update_switch(right_arm_seamless_dict, 'fk_to_ik'), p=arms_switch_state_column) #L\n    left_arm_fk_btn = cmds.button(l =\"FK\", c=lambda x:update_switch(left_arm_seamless_dict, 'ik_to_fk'), p=arms_switch_state_column) #R\n    left_arm_ik_btn = cmds.button(l =\"IK\", c=lambda x:update_switch(left_arm_seamless_dict, 'fk_to_ik'), p=arms_switch_state_column) #L\n    \n    arms_switch_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=fk_ik_switch_tab)\n    cmds.button(l =\"Switch\", c=lambda x:update_switch(right_arm_seamless_dict, is_auto_switch=True), p=arms_switch_column) #R\n    cmds.button(l =\"Switch\", c=lambda x:update_switch(left_arm_seamless_dict, is_auto_switch=True), p=arms_switch_column) #L\n    \n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.text('Right Leg:', p=arms_switch_column) #R\n    cmds.text('Left Leg:', p=arms_switch_column) #L\n\n    legs_switch_state_column = cmds.rowColumnLayout(nc=4, cw=cw_fk_ik_states, cs=cs_fk_ik_states, p=fk_ik_switch_tab)\n    right_leg_fk_btn = cmds.button(l =\"FK\", c=lambda x:update_switch(right_leg_seamless_dict, 'ik_to_fk'), p=legs_switch_state_column) #R\n    right_leg_ik_btn = cmds.button(l =\"IK\", c=lambda x:update_switch(right_leg_seamless_dict, 'fk_to_ik'), p=legs_switch_state_column) #L\n    left_leg_fk_btn = cmds.button(l =\"FK\", c=lambda x:update_switch(left_arm_seamless_dict, 'ik_to_fk'), p=legs_switch_state_column) #R\n    left_leg_ik_btn = cmds.button(l =\"IK\", c=lambda x:update_switch(left_arm_seamless_dict, 'fk_to_ik'), p=legs_switch_state_column) #L\n    \n    legs_switch_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=fk_ik_switch_tab)\n    cmds.button(l =\"Switch\", c=lambda x:update_switch(right_leg_seamless_dict, is_auto_switch=True), p=legs_switch_column) #R\n    cmds.button(l =\"Switch\", c=lambda x:update_switch(left_leg_seamless_dict, is_auto_switch=True), p=legs_switch_column) #L\n    \n    # Auto Key Settings (Switch Settings)\n    switch_settings_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=[(1, 6)], p=fk_ik_switch_tab)\n    cmds.separator(h=15) # Empty Space\n    switch_auto_key_column = cmds.rowColumnLayout(nc=3, cw=[(1, 80),(2, 130),(3, 60)], cs=[(1, 25)], p=fk_ik_switch_tab)\n    auto_key_switch_chk = cmds.checkBox( label='Auto Key',  value=gt_custom_rig_interface_settings.get('auto_key_switch'), cc=lambda x:update_stored_settings(is_secondary_instance))\n    \n    method_container = cmds.rowColumnLayout( p=switch_auto_key_column, numberOfRows=1)\n    auto_key_method_rc = cmds.radioCollection()\n    auto_key_method_rb1 = cmds.radioButton( p=method_container, label=' Bake  ', sl=gt_custom_rig_interface_settings.get('auto_key_method_bake'), cc=lambda x:update_stored_settings(is_secondary_instance))\n    auto_key_method_rb2 = cmds.radioButton( p=method_container,  label=' Sparse ', sl=(not gt_custom_rig_interface_settings.get('auto_key_method_bake')), cc=lambda x:update_stored_settings(is_secondary_instance))\n    cmds.separator(h=5, style='none', p=fk_ik_switch_tab) # Empty Space\n    \n    switch_range_column = cmds.rowColumnLayout(nc=6, cw=[(1, 40),(2, 40),(3, 30),(4, 30),(5, 40),(6, 30)], cs=[(1, 10), (4, 10)], p=fk_ik_switch_tab)\n    cmds.text('Start:', p=switch_range_column)\n    auto_key_start_int_field = cmds.intField(value=int(gt_custom_rig_interface_settings.get('auto_key_start_frame')), p=switch_range_column, cc=lambda x:update_stored_settings(is_secondary_instance))\n    cmds.button(l =\"Get\", c=lambda x:get_auto_key_current_frame(), p=switch_range_column, h=5) #L\n    cmds.text('End:', p=switch_range_column)\n    auto_key_end_int_field = cmds.intField(value=int(gt_custom_rig_interface_settings.get('auto_key_end_frame')),p=switch_range_column, cc=lambda x:update_stored_settings(is_secondary_instance))\n    cmds.button(l =\"Get\", c=lambda x:get_auto_key_current_frame('end'), p=switch_range_column, h=5) #L\n    cmds.separator(h=10, style='none', p=fk_ik_switch_tab) # Empty Space\n    \n\n    ############# Pose Management Tab #############\n    pose_management_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 246)], cs=[(1,0)], p=tabs)\n\n    btn_margin = 2\n    \n    cmds.separator(h=5, style='none') # Empty Space\n    pose_title_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=pose_management_tab)\n    cmds.text('Mirror Pose:', p=pose_title_column)\n    cmds.separator(h=5, style='none', p=pose_title_column) # Empty Space\n    \n    \n    mirror_pose_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=pose_management_tab)\n    \n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    \n    cmds.text('Right to Left:', p=mirror_pose_column) #R\n    cmds.text('Left to Right:', p=mirror_pose_column) #L\n    \n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    \n    cmds.button(l =\"Mirror ->\", c=lambda x:mirror_fk_ik_pose('right'), p=mirror_pose_column) #R\n    cmds.button(l =\"<- Mirror\", c=lambda x:mirror_fk_ik_pose('left'), p=mirror_pose_column) #L\n    \n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    \n    pose_mirror_ik_fk_column = cmds.rowColumnLayout(nc=4, cw=cw_fk_ik_states, cs=cs_fk_ik_states, p=pose_management_tab)\n    \n    # IK Pose Mirror\n    cmds.button(l =\"IK Only >\", c=lambda x:_pose_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #R\n    cmds.button(l =\"FK Only >\", c=lambda x:_pose_mirror([gt_ab_general_ctrls, gt_ab_fk_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #R\n    \n    \n    # FK Pose Mirror\n    cmds.button(l =\"< IK Only\", c=lambda x:_pose_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #L\n    cmds.button(l =\"< FK Only\", c=lambda x:_pose_mirror([gt_ab_general_ctrls, gt_ab_fk_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #L\n    \n\n    # Reset Pose\n    pose_management_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=pose_management_tab)\n    cmds.separator(h=15, style='none', p=pose_management_column) # Empty Space\n    cmds.text('Reset Pose:', p=pose_management_column) #R\n    cmds.separator(h=btn_margin, style='none', p=pose_management_column) # Empty Space\n    cmds.button(l =\"Reset Back to Default Pose\", c=lambda x:_pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_management_column)\n\n    # Export Import Pose\n    cmds.separator(h=btn_margin, style='none', p=pose_management_column) # Empty Space\n    cmds.separator(h=15, style='none', p=pose_management_column) # Empty Space\n    cmds.text('Import/Export Poses:', p=pose_management_column) \n    \n    import_export_pose_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=pose_management_tab)\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.button(l =\"Import Current Pose\", c=lambda x:_pose_import(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column)\n    cmds.button(l =\"Export Current Pose\", c=lambda x:_pose_export(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column) \n\n\n    ############# Animation Management Tab #############\n    anim_management_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 246)], cs=[(1,0)], p=tabs)\n    \n    cmds.separator(h=5, style='none') # Empty Space\n    anim_title_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=anim_management_tab)\n    cmds.text('Mirror Animation:', p=anim_title_column)\n    cmds.separator(h=5, style='none', p=anim_title_column) # Empty Space\n    \n    mirror_anim_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=anim_management_tab)\n    \n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    \n    cmds.text('Right to Left:', p=mirror_anim_column) #R\n    cmds.text('Left to Right:', p=mirror_anim_column) #L\n    \n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    \n    cmds.button(l =\"Mirror ->\", c=lambda x:mirror_animation('right'), p=mirror_anim_column) #R\n    cmds.button(l =\"<- Mirror\", c=lambda x:mirror_animation('left'), p=mirror_anim_column) #L\n    \n    # Reset Animation\n    anim_management_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=anim_management_tab)\n    cmds.separator(h=15, style='none', p=anim_management_column) # Empty Space\n    cmds.text('Reset Animation:', p=anim_management_column) #R\n    cmds.separator(h=btn_margin, style='none', p=anim_management_column) # Empty Space\n    cmds.button(l =\"Reset Animation (Delete Keyframes)\", c=lambda x:_anim_reset(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=anim_management_column)\n    cmds.separator(h=btn_margin, style='none', p=anim_management_column) # Empty Space\n    cmds.button(l =\"Reset Animation and Pose\", c=lambda x:reset_animation_and_pose(), p=anim_management_column)\n    \n    # Export Import Pose\n    cmds.separator(h=17, style='none', p=anim_management_column) # Empty Space\n    cmds.text('Import/Export Animation:', p=anim_management_column) \n\n    import_export_pose_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=anim_management_tab)\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.button(l =\"Import Animation\", c=lambda x:_anim_import(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column)\n    cmds.button(l =\"Export Animation\", c=lambda x:_anim_export(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column) \n    \n    ############# Settings Tab #############\n    settings_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,0)], p=tabs)\n    \n    if not is_secondary_instance:\n        # General Settings\n        enabled_bgc_color = (.4, .4, .4)\n        disabled_bgc_color = (.3,.3,.3)\n        cmds.separator(h=5, style='none') # Empty Space\n        cmds.text('General Settings:', font='boldLabelFont')\n        cmds.separator(h=5, style='none') # Empty Space\n        cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 20)], cs=[(1,10)]) \n        \n        # Allow Multiple Instances\n        is_option_enabled = True\n        cmds.text(' ', bgc=(enabled_bgc_color if is_option_enabled else disabled_bgc_color), h=20) # Tiny Empty Spac\n        cmds.checkBox( label='  Allow Multiple Instances', value=gt_custom_rig_interface_settings.get('allow_multiple_instances'), ebg=True, cc=lambda x:invert_stored_setting('allow_multiple_instances'), en=is_option_enabled) \n\n        multiple_instances_help_message = 'This option will allow you to open multiple instances of this script. (multiple windows)\\nThis can be helpful in case you are animating more than one character at the same time.\\n\\nThe extra instance will not be allowed to change settings or to set persistent options, so make sure to change these in your main (primary) instance of the script.'\n        multiple_instances_help_title = 'Allow Multiple Instances'\n        cmds.button(l ='?', bgc=enabled_bgc_color, c=lambda x:build_custom_help_window(multiple_instances_help_message, multiple_instances_help_title))\n        \n        # Transfer Data to Offset Control\n        is_option_enabled = True\n        cmds.text(' ', bgc=(enabled_bgc_color if is_option_enabled else disabled_bgc_color), h=20) # Tiny Empty Spac\n        cmds.checkBox( label='  Transfer Data to Offset Control', value=gt_custom_rig_interface_settings.get('offset_target'), ebg=True, cc=lambda x:invert_stored_setting('offset_target'), en=is_option_enabled) \n        ''' TODO, create better description '''\n        offset_target_thumbnail_help_message = 'Use this option to transfer the data to the IK offset control instead of transfering it directly to the IK control.'\n        offset_target_thumbnail_help_title = 'Transfer Data to Offset Control'\n        cmds.button(l ='?', bgc=enabled_bgc_color, c=lambda x:build_custom_help_window(offset_target_thumbnail_help_message, offset_target_thumbnail_help_title))\n        \n        # Export Thumbnail With Pose\n        is_option_enabled = False\n        cmds.text(' ', bgc=(enabled_bgc_color if is_option_enabled else disabled_bgc_color), h=20) # Tiny Empty Spac\n        cmds.checkBox( label='  Export Thumbnail with Pose', value=gt_custom_rig_interface_settings.get('pose_export_thumbnail'), ebg=True, cc=lambda x:invert_stored_setting('pose_export_thumbnail'), en=is_option_enabled) \n\n        export_pose_thumbnail_help_message = 'This option will be included in future versions, thank you for your patience.\\n\\nExports a thumbnail \".jpg\" file together with your \".pose\" file.\\nThis extra thumbnail file can be used to quickly undestand what you pose looks like before importing it.\\n\\nThe thumbnail is a screenshot of you active viewport at the moment of exporting the pose. If necessary, export it again to generate another thumbnail.'\n        export_pose_thumbnail_help_title = 'Export Thumbnail with Pose'\n        cmds.button(l ='?', bgc=enabled_bgc_color, c=lambda x:build_custom_help_window(export_pose_thumbnail_help_message, export_pose_thumbnail_help_title))\n       \n        # Reset Persistent Settings\n        cmds.separator(h=btn_margin, style='none', p=settings_tab) # Empty Space\n        settings_buttons_column = cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,10)], p=settings_tab) \n        cmds.button(l =\"Reset Persistent Settings\", c=lambda x:_reset_persistent_settings_rig_interface(), p=settings_buttons_column)\n    else:\n        # Secondary Instance Can't change settings\n        cmds.rowColumnLayout(settings_tab, e=True, cw=[(1, 250)], cs=[(1,0)])\n        cmds.separator(h=100, style='none') # Empty Space\n        cmds.text('Use main instance for settings', font='boldLabelFont', en=False)\n\n  \n    ################# END TABS #################\n    cmds.tabLayout( tabs, edit=True, tabLabel=((fk_ik_switch_tab, ' FK/IK '), (pose_management_tab, ' Pose '), (anim_management_tab, 'Animation'), (settings_tab, ' Settings ')))\n\n    # Outside Margin\n    cmds.separator(h=10, style='none', p=content_main) # Empty Space\n \n    # Show and Lock Window\n    cmds.showWindow(build_gui_custom_rig_interface)\n    cmds.window(rig_interface_window_name, e=True, s=False)\n    \n    # Set Window Icon\n    qw = omui.MQtUtil.findWindow(rig_interface_window_name)\n    if python_version == 3:\n        widget = wrapInstance(int(qw), QWidget)\n    else:\n        widget = wrapInstance(long(qw), QWidget)\n    icon = QIcon(':/out_timeEditorAnimSource.png')\n    if is_secondary_instance:\n        icon = QIcon(':/animateSnapshot.png')\n    widget.setWindowIcon(icon)\n\n    # Update FK/IK States and Settings for the first run time\n    update_fk_ik_buttons()\n    update_stored_settings(is_secondary_instance)\n\n    # Remove the focus from the textfield and give it to the window\n    cmds.setFocus(rig_interface_window_name)\n\n    # Main GUI Ends Here =================================================================================\n    \n\ndef _open_gt_tools_documentation():\n    ''' Opens a web browser with the the auto rigger docs  '''\n    cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-auto-biped-rigger-', absolute=True) \n\ndef _fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace='', keyframe=False, start_time=0, end_time=0, method='sparse'):\n    '''\n    Transfer the position of the FK to IK or IK to FK systems in a seamless way, so the animator can easily switch between one and the other\n    \n            Parameters:\n                ik_fk_dict (dict): A dicitionary containg the elements that are part of the system you want to switch\n                direction (optinal, string): Either \"fk_to_ik\" or \"ik_to_fk\". It determines what is the source and what is the target.\n                namespace (optinal, string): In case the rig has a namespace, it will be used to properly select the controls.\n                \n                \n                keyframe (optinal, bool): If active it will created a keyframe at the current frame, move to the\n                start_time (optinal, int): Where to create the first keyframe\n                end_time (optinal, int): Where to create the last keyframe\n                method (optinal, string): Method used for creating the keyframes. Either 'sparse' or 'bake'.\n    '''\n    def switch(match_only=False):\n        '''\n        Performs the switch operation.\n        Commands were wrapped into a function to be used during the bake operation.\n        \n                Parameters:\n                    match_only (optional, bool) If active (True) it will only match the pose, but not switch\n        \n                Returns:\n                    attr_value (float): Value which the influence attribute was set to. Either 1 (fk_to_ik) or 0 (ik_to_fk).\n                                        This value is returned only if \"match_only\" is False. Otherwise, expect None.\n        '''\n        try:\n            ik_fk_ns_dict = {}\n            for obj in ik_fk_dict:\n                ik_fk_ns_dict[obj] = namespace + ik_fk_dict.get(obj)\n            \n            fk_pairs = [[ik_fk_ns_dict.get('base_ik_jnt'), ik_fk_ns_dict.get('base_fk_ctrl')],\n                        [ik_fk_ns_dict.get('mid_ik_jnt'), ik_fk_ns_dict.get('mid_fk_ctrl')],\n                        [ik_fk_ns_dict.get('end_ik_jnt'), ik_fk_ns_dict.get('end_fk_ctrl')]]            \n                                    \n            if direction == 'fk_to_ik':\n                if ik_fk_dict.get('end_ik_reference') != '':\n                    cmds.matchTransform(ik_fk_ns_dict.get('end_ik_ctrl'), ik_fk_ns_dict.get('end_ik_reference'), pos=1, rot=1)\n                else:\n                    cmds.matchTransform(ik_fk_ns_dict.get('end_ik_ctrl'), ik_fk_ns_dict.get('end_fk_jnt'), pos=1, rot=1)\n                cmds.matchTransform(ik_fk_ns_dict.get('pvec_ik_ctrl'), ik_fk_ns_dict.get('mid_ik_reference'), pos=1, rot=1)\n\n                if not match_only:\n                    cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 1)\n                return 1\n            if direction == 'ik_to_fk':\n                for pair in fk_pairs:\n                    cmds.matchTransform(pair[1], pair[0], pos=1, rot=1)\n                    pass\n                if not match_only:\n                    cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 0)\n                return 0\n        except Exception as e:\n            cmds.warning('An error occurred. Please check if a namespace is necessary or if a control was deleted.     Error: ' + str(e))\n    \n    \n    def print_inview_feedback():\n        '''\n        Prints feedback using inView messages so the user knows what operation was executed.\n        '''\n                \n        is_valid_message = True\n        message_target = 'IK' if direction == 'fk_to_ik' else 'FK'\n        \n        # Try to figure it out system:\n        message_direction = ''\n        pvec_ik_ctrl = ik_fk_dict.get(next(iter(ik_fk_dict)))\n        if pvec_ik_ctrl.startswith('right_'):\n            message_direction = 'right'\n        elif pvec_ik_ctrl.startswith('left_'):\n            message_direction = 'left'\n        else:\n            is_valid_message = False\n        \n        message_limb = ''\n        if 'knee' in pvec_ik_ctrl:\n            message_limb = 'leg'\n        elif 'elbow' in pvec_ik_ctrl:\n            message_limb = 'arm'\n        else:\n            is_valid_message = False\n        \n        message_range = ''\n        if keyframe:\n            message_range = '(Start: <span style=\\\"color:#FFFFFF;\\\">' + str(start_time) + '</span> End: <span style=\\\"color:#FFFFFF;\\\">' + str(end_time) + '</span> Method: <span style=\\\"color:#FFFFFF;\\\">' + method.capitalize() + '</span> )'\n        \n\n        if is_valid_message:\n            # Print Feedback\n            unique_message = '<' + str(random.random()) + '>'\n            cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Switched ' + message_direction + ' ' + message_limb + ' to </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\">' + message_target +'</span>  ' + message_range, pos='botLeft', fade=True, alpha=.9)\n    \n\n\n    # Find Available Controls\n    available_ctrls = []\n\n    for key in ik_fk_dict:\n        if cmds.objExists(namespace + ik_fk_dict.get(key)):\n            available_ctrls.append(ik_fk_dict.get(key))\n        if cmds.objExists(namespace + key):\n            available_ctrls.append(key)\n    \n    # No Controls were found\n    if len(available_ctrls) == 0:\n        is_valid=False\n        cmds.warning('No controls were found. Make sure you are using the correct namespace.')\n\n    else:\n        if ik_fk_dict.get('incompatible_attr_holder'):\n            auto_clavicle_value = cmds.getAttr(ik_fk_dict.get('incompatible_attr_holder') + '.autoClavicleInfluence')\n            cmds.setAttr(ik_fk_dict.get('incompatible_attr_holder') + '.autoClavicleInfluence', 0)\n\n        if keyframe:\n            if method.lower() == 'sparse': # Only Influence Switch\n                original_time = cmds.currentTime(q=True)\n                cmds.currentTime(start_time)\n                cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=start_time, attribute='influenceSwitch')\n                cmds.currentTime(end_time)\n                switch()\n                cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=end_time, attribute='influenceSwitch')\n                cmds.currentTime(original_time)\n                print_inview_feedback()\n            elif method.lower() == 'bake':\n                if start_time >= end_time:\n                    cmds.warning('Invalid range. Please review the stard and end frame and try again.')\n                else:\n                    original_time = cmds.currentTime(q=True)\n                    cmds.currentTime(start_time)\n                    current_time = cmds.currentTime(q=True)\n                    cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=current_time, attribute='influenceSwitch') # Start Switch\n                    for index in range(end_time - start_time):\n                        cmds.currentTime(current_time)\n                        switch(match_only=True)\n                        if direction == 'fk_to_ik':\n                            for channel in ['t','r']:\n                                for dimension in ['x', 'y', 'z']:\n                                    cmds.setKeyframe(namespace + ik_fk_dict.get('end_ik_ctrl'), time=current_time, attribute=channel+dimension) # Wrist IK Ctrl\n                                    cmds.setKeyframe(namespace + ik_fk_dict.get('pvec_ik_ctrl'), time=current_time, attribute=channel+dimension) # PVec Elbow IK Ctrl\n\n                        if direction == 'ik_to_fk':\n                            for channel in ['t','r']:\n                                for dimension in ['x', 'y', 'z']:\n                                    cmds.setKeyframe(namespace + ik_fk_dict.get('base_fk_ctrl'), time=current_time, attribute=channel+dimension) # Shoulder FK Ctrl\n                                    cmds.setKeyframe(namespace + ik_fk_dict.get('end_fk_ctrl'), time=current_time, attribute=channel+dimension) # Wrist FK Ctrl\n                                    cmds.setKeyframe(namespace + ik_fk_dict.get('mid_fk_ctrl'), time=current_time, attribute=channel+dimension) # Elbow FK Ctrl\n                        current_time += 1\n                    switch()\n                    cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=current_time, attribute='influenceSwitch') # End Switch\n                    cmds.currentTime(original_time)\n                    print_inview_feedback()\n            else:\n                cmds.warning('Invalid method was provided. Must be either \"sparse\" or \"bake\", but got ' + method)\n        else:\n            switch()\n            print_inview_feedback()\n            \n        if ik_fk_dict.get('incompatible_attr_holder'):\n            cmds.setAttr(ik_fk_dict.get('incompatible_attr_holder') + '.autoClavicleInfluence', auto_clavicle_value)\n            if auto_clavicle_value != 0:\n                # Print Feedback\n                cmds.inViewMessage(amg='</span><span style=\\\"color:#FF0000;text-decoration:underline;\\\">Warning:</span><span style=\\\"color:#FFFFFF;\\\"> Auto clavicle was activated, any unexpected pose offset is likely coming from this automation.', pos='botLeft', fade=True, alpha=.9, fadeStayTime=2000)\n    \n            \n\ndef _fk_ik_switch_auto(ik_fk_dict, namespace='', keyframe=False, start_time=0, end_time=0, method='sparse'):\n    ''' \n    Calls _fk_ik_switch, but switches (toggles) between FK and IK based on the current influence number. \n    It automatically checks the influenceSwitch value attribute and determines what direction to take it. \"0-0.5\":IK and \"0.5-1\":FK\n    \n            Parameters:\n                ik_fk_dict (dictionary): A dicitionary containg the elements that are part of the system you want to switch\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n                \n                keyframe (optinal, bool): If active it will created a keyframe at the current frame, move to the\n                start_time (optinal, int): Where to create the first keyframe\n                end_time (optinal, int): Where to create the last keyframe\n                method (optinal, string): Method used for creating the keyframes. Either 'sparse' or 'bake'.    \n    '''\n    try:\n        if cmds.objExists(namespace + ik_fk_dict.get('switch_ctrl')):\n            current_system = cmds.getAttr(namespace + ik_fk_dict.get('switch_ctrl') + '.influenceSwitch')\n            if current_system < 0.5:\n                _fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace=namespace, keyframe=keyframe, start_time=start_time, end_time=end_time, method=method)\n            else:\n                _fk_ik_switch(ik_fk_dict, direction='ik_to_fk', namespace=namespace, keyframe=keyframe, start_time=start_time, end_time=end_time, method=method)\n        else:\n            cmds.warning('Switch control was not found. Please check if a namespace is necessary.')\n    except Exception as e:\n        cmds.warning('An error occurred. Please check if a namespace is necessary.     Error: ' + str(e))\n\n\n\n\ndef _pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=''):\n    '''\n    Reset transforms list of controls back to 0 Transalte and Rotate values. \n\n        Parameters:\n                gt_ab_ik_ctrls (dict, list) : A list or dictionary of IK controls without their side prefix (e.g. \"_wrist_ctrl\")\n                gt_ab_fk_ctrls (dict, list) : A list or dictionary of FK controls without their side prefix (e.g. \"_wrist_ctrl\")\n                gt_ab_center_ctrls (dict, list) : A list or dictionary of center controls (full names) (e.g. \"spine01_ctrl\")\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    '''\n    available_ctrls = []\n    for obj in gt_ab_ik_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_fk_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_general_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_center_ctrls:\n        if cmds.objExists(namespace + obj):\n            available_ctrls.append(obj)\n    \n    if len(available_ctrls) == 0:\n        cmds.warning('No controls were found. Please check if a namespace is necessary.')\n    else:\n        unique_message = '<' + str(random.random()) + '>'\n        cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Pose </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\"> Reset!</span>', pos='botLeft', fade=True, alpha=.9)\n    \n    for ctrl in available_ctrls:\n        dimensions = ['x','y','z']\n        transforms = ['t', 'r', 's']\n        for transform in transforms:\n            for dimension in dimensions:\n                try:\n                    if cmds.getAttr(namespace + ctrl + '.' + transform + dimension, lock=True) is False:\n                        cmds.setAttr(namespace + ctrl + '.' + transform + dimension, 0)\n                except:\n                    pass\n    \n    # Special Cases\n    special_case_ctrls = ['left_fingers_ctrl', 'right_fingers_ctrl']\n    for ctrl in special_case_ctrls:\n        if cmds.objExists(namespace + ctrl):\n            if cmds.getAttr(namespace + ctrl + '.' + 'sz', lock=True) is False:\n                    cmds.setAttr(namespace + ctrl + '.' + 'sz', 2)\n                    \ndef _pose_mirror(gt_ab_ctrls, source_side, namespace=''):\n    '''\n    Mirrors the character pose from one side to the other\n\n        Parameters:\n                gt_ab_ctrls (dict) : A list of dictionaries of controls without their side prefix (e.g. \"_wrist_ctrl\")\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    '''\n    # Merge Dictionaries\n    gt_ab_ctrls_dict = {}\n    for ctrl_dict in gt_ab_ctrls:\n        gt_ab_ctrls_dict.update(ctrl_dict)\n   \n    # Find available Ctrls\n    available_ctrls = []\n    for obj in gt_ab_ctrls_dict:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    # Start Mirroring\n    if len(available_ctrls) != 0:\n     \n        errors = []\n            \n        right_side_objects = []\n        left_side_objects = []\n\n        for obj in available_ctrls:  \n            if right_prefix in obj:\n                right_side_objects.append(obj)\n                \n        for obj in available_ctrls:  \n            if left_prefix in obj:\n                left_side_objects.append(obj)\n                \n        for left_obj in left_side_objects:\n            for right_obj in right_side_objects:\n                remove_side_tag_left = left_obj.replace(left_prefix,'')\n                remove_side_tag_right = right_obj.replace(right_prefix,'')\n                if remove_side_tag_left == remove_side_tag_right:\n                    # print(right_obj + ' was paired with ' + left_obj)\n                    \n                    key = gt_ab_ctrls_dict.get(remove_side_tag_right) # TR = [(ivnerted?,ivnerted?,ivnerted?),(ivnerted?,ivnerted?,ivnerted?)]\n                    transforms = []\n\n                    # Mirroring Transform?, Inverting it? (X,Y,Z), Transform name.\n                    transforms.append([True, key[0][0], 'tx']) \n                    transforms.append([True, key[0][1], 'ty'])\n                    transforms.append([True, key[0][2], 'tz'])\n                    transforms.append([True, key[1][0], 'rx'])\n                    transforms.append([True, key[1][1], 'ry'])\n                    transforms.append([True, key[1][2], 'rz'])\n                    \n                    if len(key) > 2: # Mirroring Scale?\n                        transforms.append([True, False, 'sx'])\n                        transforms.append([True, False, 'sy'])\n                        transforms.append([True, False, 'sz'])\n                    \n                    # Transfer Right to Left\n                    if source_side is 'right':\n                        for transform in transforms:\n                            if transform[0]: # Using Transform?\n                                if transform[1]: # Inverted?\n                                    source_transform = (cmds.getAttr(namespace + right_obj + '.' + transform[2]) * -1)\n                                else:\n                                    source_transform = cmds.getAttr(namespace + right_obj + '.' + transform[2])\n\n                                if not cmds.getAttr(namespace + left_obj + '.' + transform[2], lock=True):\n                                    cmds.setAttr(namespace + left_obj + '.' + transform[2], source_transform)\n                                else:\n                                    errors.append(namespace + left_obj + ' \"' + transform[2]+'\" is locked.' )\n                                \n                    # Transfer Left to Right\n                    if source_side is 'left':\n                        for transform in transforms:\n                            if transform[0]: # Using Transform?\n                                if transform[1]: # Inverted?\n                                    source_transform = (cmds.getAttr(namespace + left_obj + '.' + transform[2]) * -1)\n                                else:\n                                    source_transform = cmds.getAttr(namespace + left_obj + '.' + transform[2])\n                                \n                                if not cmds.getAttr(namespace + right_obj + '.' + transform[2], lock=True):\n                                    cmds.setAttr(namespace + right_obj + '.' + transform[2], source_transform)\n                                else:\n                                    errors.append(namespace + right_obj + ' \"' + transform[2]+'\" is locked.' )\n                    \n        # Print Feedback\n        unique_message = '<' + str(random.random()) + '>'\n        source_message = '(Left to Right)'\n        if source_side == 'right':\n            source_message = '(Right to Left)'\n        cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Pose </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\"> mirrored!</span> ' + source_message, pos='botLeft', fade=True, alpha=.9)\n                        \n        if len(errors) != 0:\n            unique_message = '<' + str(random.random()) + '>'\n            if len(errors) == 1:\n                is_plural = 'attribute was'\n            else:\n                is_plural = 'attributes were'\n            for error in errors:\n                print(str(error))\n            sys.stdout.write(str(len(errors)) + ' locked '+ is_plural + ' ignored. (Open Script Editor to see a list)\\n')\n    else:\n        cmds.warning('No controls were found. Please check if a namespace is necessary.')\n    cmds.setFocus(\"MayaWindow\")\n    \n    \ndef _pose_export(namespace =''):\n    ''' \n    Exports a Pose (JSON) file containing the translate, rotate and scale data from the rig controls (used to export a pose)\n    Added a variable called \"gt_auto_biped_export_method\" after v1.3, so the extraction method can be stored.\n    \n        Parameters:\n            namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    ''' \n    # Validate Operation and Write file\n    is_valid = True\n    successfully_created_file = False\n\n    # Find Available Controls\n    available_ctrls = []\n    for obj in gt_ab_ik_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_fk_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_general_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_center_ctrls:\n        if cmds.objExists(namespace + obj):\n            available_ctrls.append(obj)\n    \n    # No Controls were found\n    if len(available_ctrls) == 0:\n        is_valid=False\n        cmds.warning('No controls were found. Make sure you are using the correct namespace.')\n\n\n    if is_valid:\n        file_name = cmds.fileDialog2(fileFilter=script_name + \" - POSE File (*.pose)\", dialogStyle=2, okCaption= 'Export', caption= 'Exporting Rig Pose for \"' + script_name + '\"') or []\n        if len(file_name) > 0:\n            pose_file = file_name[0]\n            successfully_created_file = True\n            \n\n    if successfully_created_file and is_valid:\n        export_dict = {'gt_interface_version' : script_version, 'gt_export_method' : 'object-space'}\n        for obj in available_ctrls:\n            translate = cmds.getAttr(obj + '.translate')[0]\n            rotate = cmds.getAttr(obj + '.rotate')[0]\n            scale = cmds.getAttr(obj + '.scale')[0]\n            to_save = [obj, translate, rotate, scale]\n            export_dict[obj] = to_save\n    \n        try: \n            with open(pose_file, 'w') as outfile:\n                json.dump(export_dict, outfile, indent=4)\n\n            unique_message = '<' + str(random.random()) + '>'\n            cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Current Pose exported to </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\">' + os.path.basename(file_name[0]) +'</span><span style=\\\"color:#FFFFFF;\\\">.</span>', pos='botLeft', fade=True, alpha=.9)\n            sys.stdout.write('Pose exported to the file \"' + pose_file + '\".')\n        except Exception as e:\n            print (e)\n            successfully_created_file = False\n            cmds.warning('Couldn\\'t write to file. Please make sure the exporting directory is accessible.')\n\n\n\n\ndef _pose_import(debugging=False, debugging_path='', namespace=''):\n    ''' \n    Imports a POSE (JSON) file containing the translate, rotate and scale data for the rig controls (exported using the \"_pose_export\" function)\n    Uses the imported data to set the translate, rotate and scale position of every control curve\n    \n            Parameters:\n                debugging (bool): If debugging, the function will attempt to auto load the file provided in the \"debugging_path\" parameter\n                debugging_path (string): Debugging path for the import function\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    TODO\n        Check import method to use the proper method when setting attributes.\n        Exporting using the export button uses \"setAttr\", extract functions will use \"xform\" instead.\n    \n    ''' \n    def set_unlocked_os_attr(target, attr, value):\n        ''' \n        Sets an attribute to the provided value in case it's not locked (Uses \"cmds.setAttr\" function so object space)\n        \n                Parameters:\n                    target (string): Name of the target object (object that will receive transforms)\n                    attr (string): Name of the attribute to apply (no need to add \".\", e.g. \"rx\" would be enough)\n                    value (float): Value used to set attribute. e.g. 1.5, 2, 5...\n        \n        '''\n        try:\n            if not cmds.getAttr(target + '.' + attr, lock=True):\n                cmds.setAttr(target + '.' + attr, value)\n        except:\n            pass\n            \n    def set_unlocked_ws_attr(target, attr, value_tuple):\n        ''' \n        Sets an attribute to the provided value in case it's not locked (Uses \"cmds.xform\" function with world space)\n        \n                Parameters:\n                    target (string): Name of the target object (object that will receive transforms)\n                    attr (string): Name of the attribute to apply (no need to add \".\", e.g. \"rx\" would be enough)\n                    value_tuple (tuple): A tuple with three (3) floats used to set attributes. e.g. (1.5, 2, 5)\n        \n        '''\n        try:\n            if attr == 'translate':\n                cmds.xform(target, ws=True, t=value_tuple)\n            if attr == 'rotate':\n                cmds.xform(target, ws=True, ro=value_tuple)\n            if attr == 'scale':\n                cmds.xform(target, ws=True, s=value_tuple)\n        except:\n            pass\n     \n     \n    # Find Available Controls\n    available_ctrls = []\n    for obj in gt_ab_ik_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_fk_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_general_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_center_ctrls:\n        if cmds.objExists(namespace + obj):\n            available_ctrls.append(obj)\n    \n    # Track Current State\n    import_version = 0.0\n    import_method = 'object-space'\n    \n    if not debugging:\n        file_name = cmds.fileDialog2(fileFilter=script_name + \" - POSE File (*.pose)\", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Proxy Pose for \"' + script_name + '\"') or []\n    else:\n        file_name = [debugging_path]\n    \n    if len(file_name) > 0:\n        pose_file = file_name[0]\n        file_exists = True\n    else:\n        file_exists = False\n    \n    if file_exists:\n        try: \n            with open(pose_file) as json_file:\n                data = json.load(json_file)\n                try:\n                    is_valid_file = True\n                    is_operation_valid = True\n\n                    if not data.get('gt_interface_version'):\n                        is_valid_file = False\n                        cmds.warning('Imported file doesn\\'t seem to be compatible or is missing data.')\n                    else:                       \n                        import_version = float(re.sub(\"[^0-9]\", \"\", str(data.get('gt_interface_version'))))\n                \n                    if data.get('gt_export_method'):\n                      import_method = data.get('gt_export_method')\n                \n                    if len(available_ctrls) == 0:\n                        cmds.warning('No controls were found. Please check if a namespace is necessary.')\n                        is_operation_valid = False\n                        \n                    if is_operation_valid:\n                        # Object-Space\n                        for ctrl in data:\n                            if ctrl != 'gt_interface_version' and ctrl != 'gt_export_method':\n                                curent_object = data.get(ctrl) # Name, T, R, S\n                                if cmds.objExists(namespace + curent_object[0]):\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'tx', curent_object[1][0])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'ty', curent_object[1][1])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'tz', curent_object[1][2])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'rx', curent_object[2][0])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'ry', curent_object[2][1])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'rz', curent_object[2][2])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'sx', curent_object[3][0])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'sy', curent_object[3][1])\n                                    set_unlocked_os_attr(namespace + curent_object[0], 'sz', curent_object[3][2])\n                        \n                        unique_message = '<' + str(random.random()) + '>'\n                        cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Pose imported from </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\">' + os.path.basename(pose_file) +'</span><span style=\\\"color:#FFFFFF;\\\">.</span>', pos='botLeft', fade=True, alpha=.9)\n                        sys.stdout.write('Pose imported from the file \"' + pose_file + '\".')\n                    \n                except Exception as e:\n                    print(e)\n                    cmds.warning('An error occured when importing the pose. Make sure you imported a valid POSE file.')\n        except:\n            file_exists = False\n            cmds.warning('Couldn\\'t read the file. Please make sure the selected file is accessible.')\n\n\n\ndef _pose_flip(namespace =''):\n    ''' \n    Flips the current pose (Essentially like a mirror in both sides at te same time)\n    Creates a Pose dictionary containing the translate, rotate and scale data from the rig controls (used to store a pose)\n    \n        Parameters:\n            namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    ''' \n    # Validate Operation and Write file\n    is_valid = True\n\n    # Find Available Controls\n    available_ctrls = []\n    for obj in gt_ab_ik_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_fk_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_general_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_center_ctrls:\n        if cmds.objExists(namespace + obj):\n            available_ctrls.append(obj)\n    \n    # No Controls were found\n    if len(available_ctrls) == 0:\n        is_valid=False\n        cmds.warning('No controls were found. Make sure you are using the correct namespace.')\n\n\n    if is_valid:\n        pose_dict = {}\n        for obj in available_ctrls:\n            # Get Pose\n            translate = cmds.getAttr(obj + '.translate')[0]\n            rotate = cmds.getAttr(obj + '.rotate')[0]\n            scale = cmds.getAttr(obj + '.scale')[0]\n            to_save = [obj, translate, rotate, scale]\n            pose_dict[obj] = to_save\n            \n            # Reset Current Pose ?\n            # _pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=namespace)\n        \n            \n            # TODO\n            # Set Pose\n            # for ctrl in pose_dict:\n            #     curent_object = pose_dict.get(ctrl) # Name, T, R, S\n            #     if cmds.objExists(namespace + curent_object[0]):\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'tx', curent_object[1][0])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'ty', curent_object[1][1])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'tz', curent_object[1][2])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'rx', curent_object[2][0])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'ry', curent_object[2][1])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'rz', curent_object[2][2])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'sx', curent_object[3][0])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'sy', curent_object[3][1])\n            #         set_unlocked_os_attr(namespace + curent_object[0], 'sz', curent_object[3][2])\n            \n\n\ndef _anim_reset(namespace=''):\n    '''\n    Deletes all keyframes and resets pose (Doesn't include Set Driven Keys)\n    \n            Parameters:\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.    \n    '''   \n    function_name = 'GT Reset Rig Animation'\n    cmds.undoInfo(openChunk=True, chunkName=function_name)\n    try:\n        keys_ta = cmds.ls(type='animCurveTA')\n        keys_tl = cmds.ls(type='animCurveTL')\n        keys_tt = cmds.ls(type='animCurveTT')\n        keys_tu = cmds.ls(type='animCurveTU')\n        deleted_counter = 0\n        all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu\n        for key in all_keyframes:\n            try:\n                key_target_namespace = cmds.listConnections(key, destination=True)[0].split(':')[0]\n                if key_target_namespace == namespace.replace(':', '') or len(cmds.listConnections(key, destination=True)[0].split(':')) == 1:\n                    cmds.delete(key)\n                    deleted_counter += 1\n            except:\n                pass   \n        message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  str(deleted_counter) + ' </span>'\n        is_plural = 'keyframe nodes were'\n        if deleted_counter == 1:\n            is_plural = 'keyframe node was'\n        message += is_plural + ' deleted.'\n        \n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        \n        # _pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace) # Add as an option?\n        \n    except Exception as e:\n        cmds.warning(str(e))\n    finally:\n        cmds.undoInfo(closeChunk=True, chunkName=function_name)\n        \n        \ndef _anim_mirror(gt_ab_ctrls, source_side, namespace=''):\n    '''\n    Mirrors the character animation from one side to the other\n\n        Parameters:\n                gt_ab_ctrls (dict) : A list of dictionaries of controls without their side prefix (e.g. \"_wrist_ctrl\")\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    '''\n    \n    def invert_float_list_values(float_list):\n        '''\n        Returns a list where all the float values are inverted. For example, if the value is 5, it will then become -5.\n\n            Parameters:\n                    float_list (list) : A list of floats.\n                    \n            Returns:\n                    inverted_float_list (list): A list of floats with their values inverted\n    \n        '''\n\n        inverted_values = []\n        for val in float_list:\n            inverted_values.append(val* -1)\n        return inverted_values\n\n    \n    # Merge Dictionaries\n    gt_ab_ctrls_dict = {}\n    for ctrl_dict in gt_ab_ctrls:\n        gt_ab_ctrls_dict.update(ctrl_dict)\n   \n    # Find available Ctrls\n    available_ctrls = []\n    for obj in gt_ab_ctrls_dict:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    # Start Mirroring\n    if len(available_ctrls) != 0:\n     \n        errors = []\n            \n        right_side_objects = []\n        left_side_objects = []\n\n        for obj in available_ctrls:  \n            if right_prefix in obj:\n                right_side_objects.append(obj)\n                \n        for obj in available_ctrls:  \n            if left_prefix in obj:\n                left_side_objects.append(obj)\n                \n        for left_obj in left_side_objects:\n            for right_obj in right_side_objects:\n                remove_side_tag_left = left_obj.replace(left_prefix,'')\n                remove_side_tag_right = right_obj.replace(right_prefix,'')\n                if remove_side_tag_left == remove_side_tag_right:\n                    # print(right_obj + ' was paired with ' + left_obj)\n                    \n                    key = gt_ab_ctrls_dict.get(remove_side_tag_right) # TR = [(ivnerted?,ivnerted?,ivnerted?),(ivnerted?,ivnerted?,ivnerted?)]\n                    transforms = []\n\n                    # Mirroring Transform?, Inverting it? (X,Y,Z), Transform name.\n                    transforms.append([True, key[0][0], 'tx']) \n                    transforms.append([True, key[0][1], 'ty'])\n                    transforms.append([True, key[0][2], 'tz'])\n                    transforms.append([True, key[1][0], 'rx'])\n                    transforms.append([True, key[1][1], 'ry'])\n                    transforms.append([True, key[1][2], 'rz'])\n                    \n                    if len(key) > 2: # Mirroring Scale?\n                        transforms.append([True, False, 'sx'])\n                        transforms.append([True, False, 'sy'])\n                        transforms.append([True, False, 'sz'])\n                    \n                    # Transfer Right to Left \n                    if source_side is 'right':\n                        for transform in transforms:\n                            if transform[0]: # Using Transform? Inverted? Name of the Attr\n                                try:\n                                    attr = transform[2]\n                                    \n                                    # Get Values\n                                    frames = cmds.keyframe(namespace + right_obj, q=1, at=attr)\n                                    values = cmds.keyframe(namespace + right_obj, q=1, at=attr, valueChange=True)\n                                    \n                                    in_angle_tangent = cmds.keyTangent(namespace + right_obj, at=attr, inAngle=True, query=True)\n                                    out_angle_tanget = cmds.keyTangent(namespace + right_obj, at=attr, outAngle=True, query=True)\n                                    is_locked = cmds.keyTangent(namespace + right_obj, at=attr, weightLock=True, query=True)\n                                    in_weight = cmds.keyTangent(namespace + right_obj, at=attr, inWeight=True, query=True)\n                                    out_weight = cmds.keyTangent(namespace + right_obj, at=attr, outWeight=True, query=True)\n                                    in_tangent_type = cmds.keyTangent(namespace + right_obj, at=attr, inTangentType=True, query=True)\n                                    out_tangent_type = cmds.keyTangent(namespace + right_obj, at=attr, outTangentType=True, query=True)\n                                    \n                                    if transform[1]: # Inverted?\n                                        values = invert_float_list_values(values)\n                                        in_angle_tangent = invert_float_list_values(in_angle_tangent)\n                                        out_angle_tanget = invert_float_list_values(out_angle_tanget)\n                                        in_weight = invert_float_list_values(in_weight)\n                                        out_weight = invert_float_list_values(out_weight)\n\n\n                                    # Set Keys/Values\n                                    for index in range(len(values)):\n                                        time = frames[index]\n                                        cmds.setKeyframe(namespace + left_obj, time=time, attribute=attr, value=values[index])\n                                        # Set Tangents\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), lock=is_locked[index], e=True)\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), inAngle=in_angle_tangent[index], e=True)\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), outAngle=out_angle_tanget[index], e=True)\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), inWeight=in_weight[index], e=True)\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), outWeight=out_weight[index], e=True)\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), inTangentType=in_tangent_type[index], e=True)\n                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), outTangentType=out_tangent_type[index], e=True)\n                                except:\n                                    pass # 0 keyframes\n\n                        # Other Attributes\n                        attributes = cmds.listAnimatable(namespace + right_obj)\n                        default_channels = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']\n                        for attr in attributes:\n                            try:\n                                short_attr = attr.split('.')[-1]\n                                if short_attr not in default_channels:\n                                     # Get Keys/Values\n                                    frames = cmds.keyframe(namespace + right_obj, q=1, at=short_attr)\n                                    values = cmds.keyframe(namespace + right_obj, q=1, at=short_attr, valueChange=True)\n\n                                    # Set Keys/Values\n                                    for index in range(len(values)):\n                                        cmds.setKeyframe(namespace + left_obj, time=frames[index], attribute=short_attr, value=values[index])\n                            except:\n                                pass # 0 keyframes\n                    \n                    # Transfer Left to Right\n                    if source_side is 'left':\n                        for transform in transforms:\n                            if transform[0]: # Using Transform? Inverted? Name of the Attr\n                                try:\n                                    attr = transform[2]\n                                    \n                                    # Get Values\n                                    frames = cmds.keyframe(namespace + left_obj, q=1, at=attr)\n                                    values = cmds.keyframe(namespace + left_obj, q=1, at=attr, valueChange=True)\n                                    \n                                    in_angle_tangent = cmds.keyTangent(namespace + left_obj, at=attr, inAngle=True, query=True)\n                                    out_angle_tanget = cmds.keyTangent(namespace + left_obj, at=attr, outAngle=True, query=True)\n                                    is_locked = cmds.keyTangent(namespace + left_obj, at=attr, weightLock=True, query=True)\n                                    in_weight = cmds.keyTangent(namespace + left_obj, at=attr, inWeight=True, query=True)\n                                    out_weight = cmds.keyTangent(namespace + left_obj, at=attr, outWeight=True, query=True)\n                                    in_tangent_type = cmds.keyTangent(namespace + left_obj, at=attr, inTangentType=True, query=True)\n                                    out_tangent_type = cmds.keyTangent(namespace + left_obj, at=attr, outTangentType=True, query=True)\n                                    \n                                    if transform[1]: # Inverted?\n                                        values = invert_float_list_values(values)\n                                        in_angle_tangent = invert_float_list_values(in_angle_tangent)\n                                        out_angle_tanget = invert_float_list_values(out_angle_tanget)\n                                        in_weight = invert_float_list_values(in_weight)\n                                        out_weight = invert_float_list_values(out_weight)\n\n\n                                    # Set Keys/Values\n                                    for index in range(len(values)):\n                                        time = frames[index]\n                                        cmds.setKeyframe(namespace + right_obj, time=time, attribute=attr, value=values[index])\n                                        # Set Tangents\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), lock=is_locked[index], e=True)\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), inAngle=in_angle_tangent[index], e=True)\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), outAngle=out_angle_tanget[index], e=True)\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), inWeight=in_weight[index], e=True)\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), outWeight=out_weight[index], e=True)\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), inTangentType=in_tangent_type[index], e=True)\n                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), outTangentType=out_tangent_type[index], e=True)\n                                except:\n                                    pass # 0 keyframes\n\n                        # Other Attributes\n                        attributes = cmds.listAnimatable(namespace + left_obj)\n                        default_channels = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']\n                        for attr in attributes:\n                            try:\n                                short_attr = attr.split('.')[-1]\n                                if short_attr not in default_channels:\n                                     # Get Keys/Values\n                                    frames = cmds.keyframe(namespace + left_obj, q=1, at=short_attr)\n                                    values = cmds.keyframe(namespace + left_obj, q=1, at=short_attr, valueChange=True)\n\n                                    # Set Keys/Values\n                                    for index in range(len(values)):\n                                        cmds.setKeyframe(namespace + right_obj, time=frames[index], attribute=short_attr, value=values[index])\n                            except:\n                                pass # 0 keyframes\n\n        # Print Feedback\n        unique_message = '<' + str(random.random()) + '>'\n        source_message = '(Left to Right)'\n        if source_side == 'right':\n            source_message = '(Right to Left)'\n        cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Animation </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\"> mirrored!</span> ' + source_message, pos='botLeft', fade=True, alpha=.9)\n                           \n        if len(errors) != 0:\n            unique_message = '<' + str(random.random()) + '>'\n            if len(errors) == 1:\n                is_plural = ' error '\n            else:\n                is_plural = ' errors '\n            for error in errors:\n                print(str(error))\n            sys.stdout.write(str(len(errors)) + is_plural + 'occurred. (Open Script Editor to see a list)\\n')\n    else:\n        cmds.warning('No controls were found. Please check if a namespace is necessary.')\n    cmds.setFocus(\"MayaWindow\")\n\n\n\ndef _anim_export(namespace =''):\n    ''' \n    Exports an ANIM (JSON) file containing the translate, rotate and scale keyframe (animation) data from the rig controls.\n\n        Parameters:\n            namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    \n    ''' \n    # Validate Operation and Write file\n    is_valid = True\n    successfully_created_file = False\n\n    # Find Available Controls\n    available_ctrls = []\n    for obj in gt_ab_ik_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_fk_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_general_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_center_ctrls:\n        if cmds.objExists(namespace + obj):\n            available_ctrls.append(obj)\n    \n    # No Controls were found\n    if len(available_ctrls) == 0:\n        is_valid=False\n        cmds.warning('No controls were found. Make sure you are using the correct namespace.')\n\n\n    if is_valid:\n        file_name = cmds.fileDialog2(fileFilter=script_name + \" - ANIM File (*.anim)\", dialogStyle=2, okCaption= 'Export', caption= 'Exporting Rig Animation for \"' + script_name + '\"') or []\n        if len(file_name) > 0:\n            pose_file = file_name[0]\n            successfully_created_file = True\n            \n\n    if successfully_created_file and is_valid:\n        export_dict = {'gt_interface_version' : script_version, 'gt_export_method' : 'object-space'}\n                \n        # Extract Keyframes:\n        for obj in available_ctrls:\n            attributes = cmds.listAnimatable(namespace + obj)\n            for attr in attributes:\n                try:\n                    short_attr = attr.split('.')[-1]\n                    frames = cmds.keyframe(namespace + obj, q=1, at=short_attr)\n                    values = cmds.keyframe(namespace + obj, q=1, at=short_attr, valueChange=True)\n                    in_angle_tangent = cmds.keyTangent(namespace + obj, at=short_attr, inAngle=True, query=True)\n                    out_angle_tanget = cmds.keyTangent(namespace + obj, at=short_attr, outAngle=True, query=True)\n                    is_locked = cmds.keyTangent(namespace + obj, at=short_attr, weightLock=True, query=True)\n                    in_weight = cmds.keyTangent(namespace + obj, at=short_attr, inWeight=True, query=True)\n                    out_weight = cmds.keyTangent(namespace + obj, at=short_attr, outWeight=True, query=True)\n                    in_tangent_type = cmds.keyTangent(namespace + obj, at=short_attr, inTangentType=True, query=True)\n                    out_tangent_type = cmds.keyTangent(namespace + obj, at=short_attr, outTangentType=True, query=True)\n                    export_dict['{}.{}'.format(obj, short_attr)] = zip(frames, values, in_angle_tangent, out_angle_tanget, is_locked, in_weight, out_weight, in_tangent_type, out_tangent_type)\n                except:\n                    pass # 0 keyframes\n\n\n        try: \n            with open(pose_file, 'w') as outfile:\n                json.dump(export_dict, outfile, indent=4)\n      \n            unique_message = '<' + str(random.random()) + '>'\n            cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Current Animation exported to </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\">' + os.path.basename(file_name[0]) +'</span><span style=\\\"color:#FFFFFF;\\\">.</span>', pos='botLeft', fade=True, alpha=.9)\n            sys.stdout.write('Animation exported to the file \"' + pose_file + '\".')\n        except Exception as e:\n            print (e)\n            successfully_created_file = False\n            cmds.warning('Couldn\\'t write to file. Please make sure the exporting directory is accessible.')\n\n\ndef _anim_import(debugging=False, debugging_path='', namespace=''):\n    ''' \n    Imports an ANIM (JSON) file containing the translate, rotate and scale keyframe data for the rig controls (exported using the \"_anim_export\" function)\n    Uses the imported data to set the translate, rotate and scale position of every control curve\n    \n            Parameters:\n                debugging (bool): If debugging, the function will attempt to auto load the file provided in the \"debugging_path\" parameter\n                debugging_path (string): Debugging path for the import function\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.    \n    ''' \n    # Find Available Controls\n    available_ctrls = []\n    for obj in gt_ab_ik_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_fk_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_general_ctrls:\n        if cmds.objExists(namespace + left_prefix + obj):\n            available_ctrls.append(left_prefix + obj)\n        if cmds.objExists(namespace + right_prefix + obj):\n            available_ctrls.append(right_prefix + obj)\n            \n    for obj in gt_ab_center_ctrls:\n        if cmds.objExists(namespace + obj):\n            available_ctrls.append(obj)\n    \n    # Track Current State\n    import_version = 0.0\n    import_method = 'object-space'\n    \n    if not debugging:\n        file_name = cmds.fileDialog2(fileFilter=script_name + \" - ANIM File (*.anim)\", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Proxy Pose for \"' + script_name + '\"') or []\n    else:\n        file_name = [debugging_path]\n    \n    if len(file_name) > 0:\n        anim_file = file_name[0]\n        file_exists = True\n    else:\n        file_exists = False\n    \n    if file_exists:\n        try: \n            with open(anim_file) as json_file:\n                data = json.load(json_file)\n                try:\n                    is_valid_file = True\n                    is_operation_valid = True\n\n                    if not data.get('gt_interface_version'):\n                        is_valid_file = False\n                        cmds.warning('Imported file doesn\\'t seem to be compatible or is missing data.')\n                    else:                       \n                        import_version = float(re.sub(\"[^0-9]\", \"\", str(data.get('gt_interface_version'))))\n                \n                    if data.get('gt_export_method'):\n                      import_method = data.get('gt_export_method')\n                \n                    if len(available_ctrls) == 0:\n                        cmds.warning('No controls were found. Please check if a namespace is necessary.')\n                        is_operation_valid = False\n                        \n                    if is_operation_valid:\n                        # Object-Space\n                        for key, dict_value in data.iteritems():\n                            if key != 'gt_interface_version' and key != 'gt_export_method':\n                                for key_data in dict_value:\n                                    # Unpack Data\n                                    time = key_data[0]\n                                    value = key_data[1]\n                                    in_angle_tangent = key_data[2]\n                                    out_angle_tanget = key_data[3] \n                                    is_locked = key_data[4]\n                                    in_weight = key_data[5]\n                                    out_weight = key_data[6] \n                                    in_tangent_type = key_data[7] \n                                    out_tangent_type = key_data[8] \n                                    \n                                    try:\n                                        obj, attr = key.split('.')\n                                        cmds.setKeyframe(namespace + obj, time=time, attribute=attr, value=value)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), lock=is_locked, e=True)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), inAngle=in_angle_tangent, e=True)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), outAngle=out_angle_tanget, e=True)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), inWeight=in_weight, e=True)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), outWeight=out_weight, e=True)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), inTangentType=in_tangent_type, e=True)\n                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), outTangentType=out_tangent_type, e=True)\n                                    except:\n                                        pass\n\n                        unique_message = '<' + str(random.random()) + '>'\n                        cmds.inViewMessage(amg=unique_message + '<span style=\\\"color:#FFFFFF;\\\">Animation imported from </span><span style=\\\"color:#FF0000;text-decoration:underline;\\\">' + os.path.basename(anim_file) +'</span><span style=\\\"color:#FFFFFF;\\\">.</span>', pos='botLeft', fade=True, alpha=.9)\n                        sys.stdout.write('Animation imported from the file \"' + anim_file + '\".')\n                            \n                except Exception as e:\n                    print(e)\n                    cmds.warning('An error occured when importing the pose. Make sure you imported a valid ANIM file.')\n        except:\n            file_exists = False\n            cmds.warning('Couldn\\'t read the file. Please make sure the selected file is accessible.')\n\n\n#Build UI\nif __name__ == '__main__':\n    build_gui_custom_rig_interface()",
        label='GTRig', tooltip='This button opens the Custom Rig Interface for GT Auto Biped Rigger.',
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
                ignore_rot (bool): Ignores the rotate channels and creates online lock translate attribute
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
                translate (bool): Whether or not to lock and hide translate
                rotate (bool): Whether or not to lock and hide rotate
                scale (bool): Whether or not to lock and hide scale
                visibility (bool): Whether or not to lock and hide visibility

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
            if condition_pair[1] in shape:
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
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sx', 0.8)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sy', 0.8)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sz', 0.8)

    # TX
    cmds.setAttr(left_upper_outer_lip_ctrl[1] + '.tx', 2)
    cmds.setAttr(left_lower_outer_lip_ctrl[1] + '.tx', 2)
    cmds.setAttr(left_upper_corner_lip_ctrl[1] + '.tx', 4)
    cmds.setAttr(left_lower_corner_lip_ctrl[1] + '.tx', 4)
    cmds.setAttr(right_upper_outer_lip_ctrl[1] + '.tx', -2)
    cmds.setAttr(right_lower_outer_lip_ctrl[1] + '.tx', -2)
    cmds.setAttr(right_upper_corner_lip_ctrl[1] + '.tx', -4)
    cmds.setAttr(right_lower_corner_lip_ctrl[1] + '.tx', -4)

    half_size_ctrls = [left_upper_outer_lip_ctrl, left_lower_outer_lip_ctrl, left_upper_corner_lip_ctrl,
                       left_lower_corner_lip_ctrl, right_upper_outer_lip_ctrl, right_lower_outer_lip_ctrl,
                       right_upper_corner_lip_ctrl, right_lower_corner_lip_ctrl, mid_upper_lip_ctrl, mid_lower_lip_ctrl]

    for ctrl in half_size_ctrls:
        cmds.setAttr(ctrl[1] + '.sx', 0.5)
        cmds.setAttr(ctrl[1] + '.sy', 0.5)
        cmds.setAttr(ctrl[1] + '.sz', 0.5)

    # 2D Controls
    left_corner_lip_ctrl = create_2d_slider_control('left_cornerLip_offset_ctrl')
    right_corner_lip_ctrl = create_2d_slider_control('right_cornerLip_offset_ctrl')
    jaw_ctrl = create_2d_slider_control('jaw_offset_ctrl')
    tongue_ctrl = create_2d_slider_control('tongue_offset_ctrl')

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

    left_inner_brow_ctrl = create_2d_slider_control('left_innerBrow_offset_ctrl',ignore_range='right')
    right_inner_brow_ctrl = create_2d_slider_control('right_innerBrow_offset_ctrl',ignore_range='left')
                    #
    cmds.setAttr(left_inner_brow_ctrl[1] + '.tx',7)
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
    left_upper_eyelid_ctrl = create_slider_control('left_upperEyelid_offset_ctrl', initial_position='top')
    left_lower_eyelid_ctrl = create_slider_control('left_lowerEyelid_offset_ctrl', initial_position='bottom')
    left_blink_eyelid_ctrl = create_slider_control('left_blinkEyelid_ctrl', initial_position='top')
    right_upper_eyelid_ctrl = create_slider_control('right_upperEyelid_offset_ctrl', initial_position='top')
    right_lower_eyelid_ctrl = create_slider_control('right_lowerEyelid_offset_ctrl', initial_position='bottom')
    right_blink_eyelid_ctrl = create_slider_control('right_blinkEyelid_ctrl', initial_position='top')

    # TY
    rescale(left_upper_eyelid_ctrl[1], 0.5, freeze=False)
    rescale(left_lower_eyelid_ctrl[1], 0.5, freeze=False)
    cmds.setAttr(left_upper_eyelid_ctrl[1] + '.tx', 15)
    cmds.setAttr(left_lower_eyelid_ctrl[1] + '.tx', 15)
    cmds.setAttr(left_upper_eyelid_ctrl[1] + '.ty', 3)
    cmds.setAttr(left_lower_eyelid_ctrl[1] + '.ty', -4)
    cmds.setAttr(left_blink_eyelid_ctrl[1] + '.tx', 5)

    rescale(right_upper_eyelid_ctrl[1], 0.5, freeze=False)
    rescale(right_lower_eyelid_ctrl[1], 0.5, freeze=False)
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

def create_facial_controls():
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

    offset_grp = cmds.group(name=obj_parent[0].replace(GRP_SUFFIX.capitalize(), offset_suffix + GRP_SUFFIX.capitalize()),
                            world=True, empty=True)
    cmds.delete(cmds.parentConstraint(obj, offset_grp))
    cmds.parent(offset_grp, obj_parent[0])
    cmds.parent(obj, offset_grp)
    return offset_grp


# Tests
if __name__ == '__main__':
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
    toggle_rigging_attr()
