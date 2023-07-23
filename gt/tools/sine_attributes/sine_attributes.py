"""
 Create Sine output attributes without using third-party plugins or expressions.
 github.com/TrevisanGMW/gt-tools - 2021-01-25
"""
try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

from maya import OpenMayaUI
import maya.cmds as cmds
import re

# Script Name
script_name = "GT - Add Sine Attributes"

# Version:
script_version = "?.?.?"  # Module version (init)


# Main Form ============================================================================
def build_gui_add_sine_attr():
    window_name = "build_gui_add_sine_attr"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    # Build UI
    window_add_sine_attr = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                       titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_add_sine_attr())
    cmds.separator(h=5, style='none')  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.text(l='Select attribute holder first, then run script.', align="center")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text('Sine Attributes Prefix:')
    stretchy_system_prefix = cmds.textField(text='', pht='Sine Attributes Prefix (Optional)')

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 115), (2, 150)], cs=[(1, 10)], p=content_main)

    add_abs_output_checkbox = cmds.checkBox(label='Add Abs Output')
    add_prefix_nn_checkbox = cmds.checkBox(label='Add Prefix to Nice Name', value=True)

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.separator(h=5, style='none')  # Empty Space

    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.button(l="Add Sine Attributes", bgc=(.6, .6, .6), c=lambda x: validate_operation())
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_add_sine_attr)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)

    icon = QIcon(':/sineCurveProfile.png')
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)

    # Main GUI Ends Here =================================================================================

    def validate_operation():
        """ Checks elements one last time before running the script """

        add_abs_output_value = cmds.checkBox(add_abs_output_checkbox, q=True, value=True)
        add_prefix_nn_value = cmds.checkBox(add_prefix_nn_checkbox, q=True, value=True)

        stretchy_prefix = cmds.textField(stretchy_system_prefix, q=True, text=True).replace(' ', '')

        selection = cmds.ls(selection=True) or []
        if len(selection) > 0:
            target = selection[0]
            is_valid = True
        else:
            cmds.warning('Please select a target object to be the attribute holder.')
            is_valid = False
            target = ''

        # Name
        if stretchy_prefix != '':
            stretchy_name = stretchy_prefix
        else:
            stretchy_name = 'sine'

        if is_valid:
            current_attributes = cmds.listAttr(target, r=True, s=True, userDefined=True) or []

            possible_conflicts = [stretchy_name + 'Time',
                                  stretchy_name + 'Amplitude',
                                  stretchy_name + 'Frequency',
                                  stretchy_name + 'Offset',
                                  stretchy_name + 'Output',
                                  stretchy_name + 'Tick',
                                  stretchy_name + 'AbsOutput',
                                  ]

            for conflict in possible_conflicts:
                for attr in current_attributes:
                    if attr == conflict:
                        is_valid = False

            if not is_valid:
                cmds.warning('The object selected has conflicting attributes. '
                             'Please change the prefix or select another object.')

        # Run Script
        if is_valid:
            if stretchy_name:
                add_sine_attributes(target, sine_prefix=stretchy_name, tick_source_attr='time1.outTime',
                                    hide_unkeyable=False, add_absolute_output=add_abs_output_value,
                                    nice_name_prefix=add_prefix_nn_value)
                cmds.select(target, r=True)
            else:
                add_sine_attributes(target, sine_prefix=stretchy_name, tick_source_attr='time1.outTime',
                                    hide_unkeyable=False, add_absolute_output=add_abs_output_value,
                                    nice_name_prefix=add_prefix_nn_value)
                cmds.select(target, r=True)


# Creates Help GUI
def build_gui_help_add_sine_attr():
    """ Creates GUI for Make Stretchy IK """
    window_name = "build_gui_help_add_sine_attr"
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
    cmds.text(l='Create Sine attributes without using\nthird-party plugins or expressions.', align="center")
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='Select and object, then click on "Add Sine Attributes"', align="center")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Sine Attributes:', align='center', font='boldLabelFont')
    cmds.text(l='Time: Multiplier for the time input (tick)', align="center")
    cmds.text(l='Amplitude: Wave amplitude (how high it gets)', align="center")
    cmds.text(l='Frequency: Wave frequency (how often it happens)', align="center")
    cmds.text(l='Offset: Value added after calculation, offset.', align="center")
    cmds.text(l='Tick: Time as seen by the sine system.', align="center")
    cmds.text(l='Output: Result of the sine operation.', align="center")
    cmds.text(l='Abs Output: Absolute output. (no negative values)', align="center")
    cmds.separator(h=10, style='none')  # Empty Space

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
        """ Closes Help Window """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def add_sine_attributes(obj, sine_prefix='sine', tick_source_attr='time1.outTime', hide_unkeyable=True,
                        add_absolute_output=False, nice_name_prefix=True):
    """
    Create Sine functions without using third-party plugins or expressions
    
    Args:
        obj (string): Name of the object
        sine_prefix (string): Prefix given to the name of the attributes (default is "sine")
        tick_source_attr (string): Name of the attribute used as the source for time. It uses the default "time1"
                                   node if nothing else is specified
        hide_unkeyable (bool): Hides the tick and output attributes
        add_absolute_output (bool): Also creates an output version that gives only positive numbers much like the abs()
                                   expression
        nice_name_prefix (bool): Add prefix or not

    Returns:
        sine_output_attrs (list): A string with the name of the object and the name of the sine output attribute.
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

    cmds.setAttr(obj + '.' + influence_attr, 1)
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


# Build UI
if __name__ == '__main__':
    build_gui_add_sine_attr()
