"""
 GT Auto FK - Creates FK controls while mimicking joint hierarchy.
 github.com/TrevisanGMW/gt-tools - 2020-01-03
"""
from maya import OpenMayaUI as OpenMayaUI
from PySide2.QtWidgets import QWidget
from shiboken2 import wrapInstance
from PySide2.QtGui import QIcon
import maya.cmds as cmds
import logging
import copy

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_create_auto_fk")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Create FK Control"

# Version:
script_version = "?.?.?"  # Module version (init)

# Custom Curve Dictionary
gt_auto_fk_settings = {'using_custom_curve': False,
                       'custom_curve': "cmds.circle(name=joint_name + 'ctrl', normal=[1,0,0], radius=1.5, ch=False)",
                       'failed_to_build_curve': False,
                       'mimic_hierarchy': True,
                       'constraint_joint': True,
                       'auto_color_ctrls': True,
                       'select_hierarchy': True,
                       'string_ctrl_suffix': '_ctrl',
                       'string_ctrl_grp_suffix': '_ctrlGrp',
                       'string_joint_suffix': '_jnt',
                       'curve_radius': '1.0',
                       'undesired_strings': 'endJnt, eye',
                       }

# Store Default Values for Resetting
gt_auto_fk_settings_default_values = copy.deepcopy(gt_auto_fk_settings)


def get_persistent_settings_auto_fk():
    """
    Checks if persistent settings for auto FK script exists and transfer them to the settings variables.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    """
    stored_using_custom_curve_exists = cmds.optionVar(exists="gt_auto_fk_using_custom_curve")
    stored_custom_curve_exists = cmds.optionVar(exists="gt_auto_fk_custom_curve")
    stored_failed_to_build_curve_exists = cmds.optionVar(exists="gt_auto_fk_failed_to_build_curve")

    stored_mimic_hierarchy_exists = cmds.optionVar(exists="gt_auto_fk_mimic_hierarchy")
    stored_constraint_joint_exists = cmds.optionVar(exists="gt_auto_fk_constraint_joint")
    stored_auto_color_ctrls_exists = cmds.optionVar(exists="gt_auto_fk_auto_color_ctrls")
    stored_select_hierarchy_exists = cmds.optionVar(exists="gt_auto_fk_select_hierarchy")
    stored_curve_radius_exists = cmds.optionVar(exists="gt_auto_fk_curve_radius")

    stored_string_ctrl_suffix_exists = cmds.optionVar(exists="gt_auto_fk_string_ctrl_suffix")
    stored_string_ctrl_grp_suffix_exists = cmds.optionVar(exists="gt_auto_fk_string_ctrl_grp_suffix")
    stored_string_joint_suffix_exists = cmds.optionVar(exists="gt_auto_fk_string_joint_suffix")
    stored_undesired_strings_exists = cmds.optionVar(exists="gt_auto_fk_undesired_strings")

    # Custom Curve
    if stored_using_custom_curve_exists:
        gt_auto_fk_settings['using_custom_curve'] = cmds.optionVar(q="gt_auto_fk_using_custom_curve")

    if stored_custom_curve_exists:
        gt_auto_fk_settings['custom_curve'] = str(cmds.optionVar(q="gt_auto_fk_custom_curve"))

    if stored_failed_to_build_curve_exists:
        gt_auto_fk_settings['failed_to_build_curve'] = cmds.optionVar(q="gt_auto_fk_failed_to_build_curve")

    # General Settings
    if stored_mimic_hierarchy_exists:
        gt_auto_fk_settings['mimic_hierarchy'] = cmds.optionVar(q="gt_auto_fk_mimic_hierarchy")

    if stored_constraint_joint_exists:
        gt_auto_fk_settings['constraint_joint'] = cmds.optionVar(q="gt_auto_fk_constraint_joint")

    if stored_auto_color_ctrls_exists:
        gt_auto_fk_settings['auto_color_ctrls'] = cmds.optionVar(q="gt_auto_fk_auto_color_ctrls")

    if stored_select_hierarchy_exists:
        gt_auto_fk_settings['select_hierarchy'] = cmds.optionVar(q="gt_auto_fk_select_hierarchy")

    if stored_curve_radius_exists:
        gt_auto_fk_settings['curve_radius'] = str(cmds.optionVar(q="gt_auto_fk_curve_radius"))

    # Strings
    if stored_string_joint_suffix_exists:
        gt_auto_fk_settings['string_joint_suffix'] = str(cmds.optionVar(q="gt_auto_fk_string_joint_suffix"))

    if stored_string_ctrl_suffix_exists:
        gt_auto_fk_settings['string_ctrl_suffix'] = str(cmds.optionVar(q="gt_auto_fk_string_ctrl_suffix"))

    if stored_string_ctrl_grp_suffix_exists:
        gt_auto_fk_settings['string_ctrl_grp_suffix'] = str(cmds.optionVar(q="gt_auto_fk_string_ctrl_grp_suffix"))

    if stored_undesired_strings_exists:
        gt_auto_fk_settings['undesired_strings'] = str(cmds.optionVar(q="gt_auto_fk_undesired_strings"))


def set_persistent_settings_auto_fk(option_var_name, option_var):
    """
    Stores persistent settings for GT Auto FK.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    
    Args:
        option_var_name (string): name of the optionVar string. Must start with script name + name of the variable
        option_var (?): string to be stored under the option_var_name
                    
    """
    if isinstance(option_var, int) and option_var_name != '':
        cmds.optionVar(iv=(str(option_var_name), int(option_var)))
    elif option_var != '' and option_var_name != '':
        cmds.optionVar(sv=(str(option_var_name), str(option_var)))


def reset_persistent_settings_auto_fk():
    """ Resets persistent settings for GT Auto FK """
    cmds.optionVar(remove='gt_auto_fk_using_custom_curve')
    cmds.optionVar(remove='gt_auto_fk_custom_curve')
    cmds.optionVar(remove='gt_auto_fk_failed_to_build_curve')
    cmds.optionVar(remove='gt_auto_fk_mimic_hierarchy')
    cmds.optionVar(remove='gt_auto_fk_constraint_joint')
    cmds.optionVar(remove='gt_auto_fk_auto_color_ctrls')
    cmds.optionVar(remove='gt_auto_fk_select_hierarchy')
    cmds.optionVar(remove='gt_auto_fk_curve_radius')
    cmds.optionVar(remove='gt_auto_fk_string_ctrl_suffix')
    cmds.optionVar(remove='gt_auto_fk_string_ctrl_grp_suffix')
    cmds.optionVar(remove='gt_auto_fk_string_joint_suffix')
    cmds.optionVar(remove='gt_auto_fk_undesired_strings')

    for def_value in gt_auto_fk_settings_default_values:
        for value in gt_auto_fk_settings:
            if def_value == value:
                gt_auto_fk_settings[value] = gt_auto_fk_settings_default_values[def_value]

    get_persistent_settings_auto_fk()
    build_gui_auto_fk()
    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')


# Main Form ============================================================================
def build_gui_auto_fk():
    """
    Builds the UI for the script GT Auto FK
    """
    window_name = "build_gui_auto_fk"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    window_gui_auto_fk = cmds.window(window_name, title=script_name + "  (v" + script_version + ')',
                                     titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout()

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_auto_fk())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 13)], p=body_column)
    check_boxes_one = cmds.checkBoxGrp(columnWidth2=[120, 1], numberOfCheckBoxes=2,
                                       label1='Mimic Hierarchy', label2='Constraint Joint    ',
                                       v1=gt_auto_fk_settings.get('mimic_hierarchy'),
                                       v2=gt_auto_fk_settings.get('constraint_joint'),
                                       cc1=lambda x: set_persistent_settings_auto_fk('gt_auto_fk_mimic_hierarchy',
                                                                                     cmds.checkBoxGrp(check_boxes_one,
                                                                                                      q=True,
                                                                                                      value1=True)),
                                       cc2=lambda x: set_persistent_settings_auto_fk('gt_auto_fk_constraint_joint',
                                                                                     cmds.checkBoxGrp(check_boxes_one,
                                                                                                      q=True,
                                                                                                      value2=True)))

    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 13)], p=body_column)

    check_boxes_two = cmds.checkBoxGrp(columnWidth2=[120, 1], numberOfCheckBoxes=2,
                                       label1='Colorize Controls', label2="Select Hierarchy  ",
                                       v1=gt_auto_fk_settings.get("auto_color_ctrls"),
                                       v2=gt_auto_fk_settings.get("select_hierarchy"),
                                       cc1=lambda x: set_persistent_settings_auto_fk('gt_auto_fk_auto_color_ctrls',
                                                                                     cmds.checkBoxGrp(check_boxes_two,
                                                                                                      q=True,
                                                                                                      value1=True)),
                                       cc2=lambda x: set_persistent_settings_auto_fk('gt_auto_fk_select_hierarchy',
                                                                                     cmds.checkBoxGrp(check_boxes_two,
                                                                                                      q=True,
                                                                                                      value2=True)))

    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=10)
    cmds.separator(h=5, style='none')  # Empty Space

    # Customize Control
    cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1, 0)], p=body_column)
    ctrl_curve_radius_slider_grp = cmds.floatSliderGrp(cw=[(1, 100), (2, 50), (3, 10)], label='Curve Radius: ',
                                                       field=True, value=float(gt_auto_fk_settings.get('curve_radius')),
                                                       cc=lambda x: set_persistent_settings_auto_fk(
                                                           'gt_auto_fk_curve_radius',
                                                           str(cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, q=True,
                                                                                   value=True))),
                                                       en=not gt_auto_fk_settings.get('using_custom_curve'))
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1, 13)], p=body_column)
    cmds.button('gt_auto_fk_custom_curve_btn', l="(Advanced) Custom Curve", c=lambda x: define_custom_curve())
    if gt_auto_fk_settings.get('using_custom_curve') is True and gt_auto_fk_settings.get(
            'failed_to_build_curve') is False:
        cmds.button('gt_auto_fk_custom_curve_btn', e=True, l='ACTIVE - Custom Curve', bgc=[0, .1, 0])

    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.separator(h=10)

    # Text Fields   
    cmds.rowColumnLayout(nc=3, cw=[(1, 70), (2, 75), (3, 100)], cs=[(1, 5), (2, 0)], p=body_column)
    cmds.text("Joint Suffix:")
    cmds.text("Control Suffix:")
    cmds.text("Control Grp Suffix:")
    jnt_suffix_tf = cmds.textField(text=gt_auto_fk_settings.get('string_joint_suffix'),
                                   enterCommand=lambda x: generate_fk_controls(),
                                   cc=lambda x: set_persistent_settings_auto_fk('gt_auto_fk_string_joint_suffix',
                                                                                cmds.textField(jnt_suffix_tf, q=True,
                                                                                               text=True)))
    ctrl_suffix_tf = cmds.textField(text=gt_auto_fk_settings.get('string_ctrl_suffix'),
                                    enterCommand=lambda x: generate_fk_controls(),
                                    cc=lambda x: set_persistent_settings_auto_fk('gt_auto_fk_string_ctrl_suffix',
                                                                                 cmds.textField(ctrl_suffix_tf, q=True,
                                                                                                text=True)))
    ctrl_grp_suffix_tf = cmds.textField(text=gt_auto_fk_settings.get('string_ctrl_grp_suffix'),
                                        enterCommand=lambda x: generate_fk_controls(),
                                        cc=lambda
                                        x: set_persistent_settings_auto_fk('gt_auto_fk_string_ctrl_grp_suffix',
                                                                           cmds.textField(ctrl_grp_suffix_tf, q=True,
                                                                                          text=True)))

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)

    cmds.separator(h=10)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(label='Ignore Joints Containing These Strings:')
    cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=[(1, 5)], p=body_column)
    undesired_strings_text_field = cmds.textField(text=gt_auto_fk_settings.get('undesired_strings'),
                                                  enterCommand=lambda x: generate_fk_controls(),
                                                  cc=lambda x: set_persistent_settings_auto_fk(
                                                      'gt_auto_fk_undesired_strings',
                                                      cmds.textField(undesired_strings_text_field, q=True, text=True)))
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    cmds.text(label='(Use Commas to Separate Strings)')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.separator(h=10)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.button(l="Generate", bgc=(.6, .6, .6), c=lambda x: generate_fk_controls())
    cmds.separator(h=10, style='none')  # Empty Space

    # Generate FK Main Function Starts --------------------------------------------
    def generate_fk_controls():
        """
        Generate FK Controls.
        Creates a curves to be used as FK controls for the selected joint.
        """

        cmds.undoInfo(openChunk=True, chunkName='Auto Generate FK Ctrls')
        try:
            errors = ''
            ctrl_curve_radius = cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, q=True, value=True)
            selected_joints = cmds.ls(selection=True, type='joint', long=True)
            if cmds.checkBoxGrp(check_boxes_two, q=True, value2=True):
                cmds.select(hierarchy=True)
                selected_joints = cmds.ls(selection=True, type='joint', long=True)
            ctrl_suffix = parse_text_field(cmds.textField(ctrl_suffix_tf, q=True, text=True))[0]
            ctrl_grp_suffix = parse_text_field(cmds.textField(ctrl_grp_suffix_tf, q=True, text=True))[0]
            joint_suffix = parse_text_field(cmds.textField(jnt_suffix_tf, q=True, text=True))[0]
            undesired_jnt_strings = parse_text_field(cmds.textField(undesired_strings_text_field, q=True, text=True))
            undesired_joints = []

            # Find undesired joints and make a list of them
            for jnt in selected_joints:
                for string in undesired_jnt_strings:
                    if string in get_short_name(jnt):
                        undesired_joints.append(jnt)

            # Remove undesired joints from selection list
            for jnt in undesired_joints:
                if jnt in undesired_joints:
                    selected_joints.remove(jnt)

            for jnt in selected_joints:
                if len(joint_suffix) != 0:
                    joint_name = get_short_name(jnt).replace(joint_suffix, '')
                else:
                    joint_name = get_short_name(jnt)
                ctrl_name = joint_name + ctrl_suffix
                ctrl_grp_name = joint_name + ctrl_grp_suffix

                if gt_auto_fk_settings.get("using_custom_curve"):
                    ctrl = create_custom_curve(gt_auto_fk_settings.get("custom_curve"))

                    try:
                        ctrl = [cmds.rename(ctrl, ctrl_name)]
                    except Exception as e:
                        logging.debug(str(e))
                        ctrl = cmds.circle(name=ctrl_name, normal=[1, 0, 0], radius=ctrl_curve_radius,
                                           ch=False)  # Default Circle Curve

                    if gt_auto_fk_settings.get("failed_to_build_curve"):
                        ctrl = cmds.circle(name=ctrl_name, normal=[1, 0, 0], radius=ctrl_curve_radius,
                                           ch=False)  # Default Circle Curve

                else:
                    ctrl = cmds.circle(name=ctrl_name, normal=[1, 0, 0], radius=ctrl_curve_radius,
                                       ch=False)  # Default Circle Curve

                grp = cmds.group(name=ctrl_grp_name, empty=True)
                try:
                    cmds.parent(ctrl, grp)
                    constraint = cmds.parentConstraint(jnt, grp)
                    cmds.delete(constraint)
                except Exception as e:
                    errors = errors + str(e)

                # Colorize Control Start ------------------

                if cmds.checkBoxGrp(check_boxes_two, q=True, value1=True):
                    try:
                        cmds.setAttr(ctrl[0] + ".overrideEnabled", 1)
                        if ctrl[0].lower().startswith('right_') or ctrl[0].lower().startswith('r_'):
                            cmds.setAttr(ctrl[0] + ".overrideColor", 13)  # Red
                        elif ctrl[0].lower().startswith('left_') or ctrl[0].lower().startswith('l_'):
                            cmds.setAttr(ctrl[0] + ".overrideColor", 6)  # Blue
                        else:
                            cmds.setAttr(ctrl[0] + ".overrideColor", 17)  # Yellow
                    except Exception as e:
                        errors = errors + str(e)

                # Colorize Control End ---------------------

                # Constraint Joint
                if cmds.checkBoxGrp(check_boxes_one, q=True, value2=True):
                    try:
                        cmds.parentConstraint(ctrl_name, jnt)
                    except Exception as e:
                        errors = errors + str(e) + '\n'

                # Mimic Hierarchy
                if cmds.checkBoxGrp(check_boxes_one, q=True, value1=True):
                    try:
                        # Auto parents new controls
                        # "or []" Accounts for root joint that doesn't have a parent, it forces it to be a list
                        jnt_parent = cmds.listRelatives(jnt, allParents=True) or []
                        if len(jnt_parent) == 0:
                            pass
                        else:

                            if len(joint_suffix) != 0:
                                parent_ctrl = (jnt_parent[0].replace(joint_suffix, "") + ctrl_suffix)
                            else:
                                parent_ctrl = (jnt_parent[0] + ctrl_suffix)

                            if cmds.objExists(parent_ctrl):
                                cmds.parent(grp, parent_ctrl)
                    except Exception as e:
                        errors = errors + str(e) + '\n'

            # Print Errors if necessary            
            if errors != '':
                print('#' * 80)
                print(errors)
                print('#' * 80)
                error_message = 'Errors detected during creation. Open the script editor to see details.'
                cmds.warning(error_message)
        except Exception as e:
            logging.warning(str(e))
        finally:
            cmds.undoInfo(closeChunk=True, chunkName='Auto Generate FK Ctrls')

    # Generate FK Main Function Ends --------------------------------------------

    # Define Custom Curve
    def define_custom_curve():
        """Asks the user for input. Uses this input as a custom curve (by storing it in the settings dictionary)"""

        if gt_auto_fk_settings.get('custom_curve') == gt_auto_fk_settings_default_values.get('custom_curve'):
            textfield_data = ''
        else:
            textfield_data = str(gt_auto_fk_settings.get('custom_curve'))

        result = cmds.promptDialog(
            scrollableField=True,
            title='Py Curve',
            message='Paste Python Curve Below: \n(Use \"GT Generate Python Curve \" '
                    'to extract it from an existing curve)',
            button=['Use Python', 'Use Cube', 'Use Pin', 'Use Default'],
            defaultButton='OK',
            cancelButton='Use Default',
            dismissString='Use Default',
            text=textfield_data
        )

        if result == 'Use Python':
            if cmds.promptDialog(query=True, text=True) != '':
                gt_auto_fk_settings["custom_curve"] = cmds.promptDialog(query=True, text=True)
                gt_auto_fk_settings["using_custom_curve"] = True
                gt_auto_fk_settings["failed_to_build_curve"] = False
                cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, e=True, en=False)
                # Update Persistent Settings
                set_persistent_settings_auto_fk('gt_auto_fk_custom_curve',
                                                str(cmds.promptDialog(query=True, text=True)))
                set_persistent_settings_auto_fk('gt_auto_fk_using_custom_curve', True)
                set_persistent_settings_auto_fk('gt_auto_fk_failed_to_build_curve', False)
                cmds.button('gt_auto_fk_custom_curve_btn', e=True, l='ACTIVE - Custom Curve', bgc=[0, .1, 0])
        elif result == 'Use Cube':
            gt_auto_fk_settings["custom_curve"] = 'cmds.curve(p=[[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], ' \
                                                  '[0.5, 0.5, -0.5], [-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5], ' \
                                                  '[-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5],' \
                                                  ' [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5],' \
                                                  ' [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], ' \
                                                  '[-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5]], d=1)'
            gt_auto_fk_settings["using_custom_curve"] = True
            gt_auto_fk_settings["failed_to_build_curve"] = False
            cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, e=True, en=False)
            # Update Persistent Settings
            set_persistent_settings_auto_fk('gt_auto_fk_custom_curve',
                                            str(cmds.promptDialog(query=True, text=True)))
            set_persistent_settings_auto_fk('gt_auto_fk_using_custom_curve', True)
            set_persistent_settings_auto_fk('gt_auto_fk_failed_to_build_curve', False)
            cmds.button('gt_auto_fk_custom_curve_btn', e=True, l='ACTIVE - Custom Curve', bgc=[0, .1, 0])
        elif result == 'Use Pin':
            gt_auto_fk_settings["custom_curve"] = 'cmds.curve(p=[[0.0, 0.0, 0.0], [0.0, 4.007, 0.0], ' \
                                                  '[0.147, 4.024, 0.0], [0.286, 4.083, 0.0], [0.406, 4.176, 0.0],' \
                                                  ' [0.496, 4.292, 0.0], [0.554, 4.431, 0.0], [0.572, 4.578, 0.0],' \
                                                  ' [0.0, 4.578, 0.0], [0.0, 4.007, 0.0], [-0.147, 4.024, 0.0],' \
                                                  ' [-0.286, 4.083, 0.0], [-0.406, 4.176, 0.0], [-0.496, 4.292, 0.0],' \
                                                  ' [-0.554, 4.431, 0.0], [-0.572, 4.578, 0.0], [-0.554, 4.726, 0.0]' \
                                                  ', [-0.496, 4.864, 0.0], [-0.406, 4.985, 0.0],' \
                                                  ' [-0.286, 5.074, 0.0], [-0.147, 5.132, 0.0], [0.0, 5.15, 0.0],' \
                                                  ' [0.147, 5.132, 0.0], [0.286, 5.074, 0.0], [0.406, 4.985, 0.0],' \
                                                  ' [0.496, 4.864, 0.0], [0.554, 4.726, 0.0], [0.572, 4.578, 0.0],' \
                                                  ' [-0.572, 4.578, 0.0], [0.0, 4.578, 0.0], [0.0, 5.15, 0.0]], d=1)'
            gt_auto_fk_settings["using_custom_curve"] = True
            gt_auto_fk_settings["failed_to_build_curve"] = False
            cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, e=True, en=False)
            # Update Persistent Settings
            set_persistent_settings_auto_fk('gt_auto_fk_custom_curve',
                                            str(cmds.promptDialog(query=True, text=True)))
            set_persistent_settings_auto_fk('gt_auto_fk_using_custom_curve', True)
            set_persistent_settings_auto_fk('gt_auto_fk_failed_to_build_curve', False)
            cmds.button('gt_auto_fk_custom_curve_btn', e=True, l='ACTIVE - Custom Curve', bgc=[0, .1, 0])
        else:
            gt_auto_fk_settings["using_custom_curve"] = False
            cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, e=True, en=True)
            gt_auto_fk_settings['custom_curve'] = gt_auto_fk_settings_default_values.get('custom_curve')
            cmds.button('gt_auto_fk_custom_curve_btn', e=True, l="(Advanced) Custom Curve", nbg=False)
            # Update Persistent Settings
            set_persistent_settings_auto_fk('gt_auto_fk_using_custom_curve', False)

    # Show and Lock Window
    cmds.showWindow(window_gui_auto_fk)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/kinInsert.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_auto_fk():
    """Builds the help window. You can reset persistent settings in here."""
    window_name = "build_gui_help_auto_FK"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='This script generates FK controls for joints while storing', align="left")
    cmds.text(l='their transforms in groups.', align="left")
    cmds.text(l='Select desired joints and run script.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Colorize Controls:', align="left", fn="boldLabelFont")
    cmds.text(l='Automatically colorize controls according to their', align="left")
    cmds.text(l='names (prefix). It ignores uppercase/lowercase. ', align="left")
    cmds.text(l='No Prefix = Yellow', align="left")
    cmds.text(l='"l_" or "left_" = Blue', align="left")
    cmds.text(l='"r_" or "right_" = Red', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Select Hierarchy: ', align="left", fn="boldLabelFont")
    cmds.text(l='Automatically selects the rest of the hierarchy of the', align="left")
    cmds.text(l='selected object, thus allowing you to only select the', align="left")
    cmds.text(l='root joint before creating controls.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='(Advanced) Custom Curve:', align="left", fn="boldLabelFont")
    cmds.text(l='You can change the curve used for the creation of the', align="left")
    cmds.text(l='controls. Use the script "GT Generate Python Curve"', align="left")
    cmds.text(l='to generate the code you need to enter here.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Joint, Control, and Control Group Suffix:', align="left", fn="boldLabelFont")
    cmds.text(l='Used to determine the suffix of the elements.', align="left")
    cmds.text(l='Joint Suffix is removed from the joint name for the control.', align="left")
    cmds.text(l='Control Suffix is added to the generated control.', align="left")
    cmds.text(l='Control Group Suffix is added to the control group.', align="left")
    cmds.text(l='(This is the transform carrying the transforms of the joint).', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Ignore Joints Containing These Strings: ', align="left", fn="boldLabelFont")
    cmds.text(l='The script will ignore joints containing these strings.', align="left")
    cmds.text(l='To add multiple strings use commas - ",".', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='Reset Persistent Settings', h=30, c=lambda args: reset_persistent_settings_auto_fk())
    cmds.separator(h=5, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)

    def close_help_gui():
        """Function to close the help UI, created for the "OK" Button"""
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def parse_text_field(textfield_data):
    """
    Function to Parse textField data. It removes spaces and split elements using a comma. 
    
    Args:
        textfield_data (string) : String provided on the text field

    Returns:
        return_list (list) : A list containing strings from the textfield
    """
    text_field_data_no_spaces = textfield_data.replace(" ", "")
    if len(text_field_data_no_spaces) <= 0:
        return []
    else:
        return_list = text_field_data_no_spaces.split(",")
        empty_objects = []
        for obj in return_list:
            if '' == obj:
                empty_objects.append(obj)
        for obj in empty_objects:
            return_list.remove(obj)
        return return_list


def create_custom_curve(curve_py_code):
    """
    Attempts to create the custom curve provided by the user. It forces code to run even if nested - exec.
    
    Args:
        curve_py_code (string) : Code necessary to create a curve

    Returns:
        generated_object (string) : Name of the generated object
    """
    try:
        exec(curve_py_code)
        return cmds.ls(selection=True)
    except Exception as e:
        print('Failed to create custom curve: ', str(e))
        gt_auto_fk_settings["failed_to_build_curve"] = True
        set_persistent_settings_auto_fk('gt_auto_fk_failed_to_build_curve', True)
        set_persistent_settings_auto_fk('gt_auto_fk_using_custom_curve', False)
        cmds.button('gt_auto_fk_custom_curve_btn', e=True, l='ERROR - Custom Curve', bgc=[.3, 0, 0])
        cmds.error("Something is wrong with your custom curve! Please update it and try again.")


def get_short_name(obj):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

    Args:
            obj (string) - object to extract short name.

    Returns:
            short_name (string) - A string containing the short name of the object.
    """
    if obj == '':
        return ''
    split_path = obj.split('|')
    short_name = ''
    if len(split_path) >= 1:
        short_name = split_path[len(split_path) - 1]
    return short_name


# Get Persistent Settings and Build UI
get_persistent_settings_auto_fk()
if __name__ == '__main__':
    build_gui_auto_fk()
