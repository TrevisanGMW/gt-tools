"""
 GT Render Calculator - Script for calculating the time a render will take
 github.com/TrevisanGMW - 2022-07-18
"""
from maya import OpenMayaUI as OpenMayaUI
from functools import partial
import maya.cmds as cmds
import logging
import datetime


try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget


# Script Name
script_name = "GT - Render Calculator"

# Version
script_version = "1.0.1"


# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_render_calculator")
logger.setLevel(logging.INFO)


def calculate_render_time(input_time, num_frames=1, num_machines=1, unit='seconds'):
    """
    Generates the text describing how long it will take to render an animation
    Args:
        input_time: Integer value describing time, for example 600 seconds = 10 minutes
        num_frames (optional, int): Total number of frames (multiplies the input_time parameter)
        num_machines (optional, int): Total number of computers (divides the input_time parameter)
        unit (optional, string): Unit used to calculate time, "seconds", "minutes" or "hours" (default: seconds)

    Returns:
        output_time (string): A string describing the duration according to the provided input
    """
    processed_time = input_time * num_frames
    processed_time = int(processed_time/num_machines)

    if unit == 'minutes':
        timedelta_sec = datetime.timedelta(minutes=processed_time)
    elif unit == 'seconds':
        timedelta_sec = datetime.timedelta(seconds=processed_time)
    elif unit == 'hours':
        timedelta_sec = datetime.timedelta(hours=processed_time)
    else:
        logger.warning('Unable to determine unit. Using seconds.')
        timedelta_sec = datetime.timedelta(seconds=processed_time)

    # timedelta_sec = datetime.timedelta(seconds=time_per_frame_seconds)
    time = datetime.datetime(1, 1, 1) + timedelta_sec

    years = time.year - 1
    months = time.month - 1
    days = time.day - 1
    hours = time.hour
    minutes = time.minute
    seconds = time.second

    logger.debug('########### Detailed Output:')
    logger.debug('years: ' + str(years))
    logger.debug('months: ' + str(months))
    logger.debug('days: ' + str(days))
    logger.debug('hours: ' + str(hours))
    logger.debug('minutes: ' + str(minutes))
    logger.debug('seconds: ' + str(seconds))

    output_time = ''
    if years > 0:
        output_time += ' ' + str(years) + ' year' + ('' if years == 1 else 's') + '\n'
    if months > 0:
        output_time += ' ' + str(months) + ' month' + ('' if months == 1 else 's') + '\n'
    if days > 0:
        output_time += ' ' + str(days) + ' day' + ('' if days == 1 else 's') + '\n'
    if hours > 0:
        output_time += ' ' + str(hours) + ' hour' + ('' if hours == 1 else 's') + '\n'
    if minutes > 0:
        output_time += ' ' + str(minutes) + ' minute' + ('' if minutes == 1 else 's') + '\n'
    if seconds > 0:
        output_time += ' ' + str(seconds) + ' second' + ('' if seconds == 1 else 's') + '\n'

    return output_time


def build_gui_render_calculator():
    """ Builds the main window/GUI"""
    def _recalculate_time(*args):
        """
        Recalculates everything using the data found in the GUI. Created to be used with changeCommand
        """
        logger.debug(str(args))
        time_per_frame_out = cmds.intSliderGrp(time_per_frame, q=True, value=True)
        num_of_frames_out = cmds.intSliderGrp(num_of_frames, q=True, value=True)
        num_of_machines_out = cmds.intSliderGrp(num_of_machines, q=True, value=True)
        unit_out_string = cmds.optionMenu(unit_option, q=True, value=True)
        unit_out = (unit_out_string.replace('(s)', '') + 's').lower()
        result = 'Time per frame ' + str(time_per_frame_out) + ' ' + unit_out_string.lower() + '\n'
        result += 'Frame Count ' + str(num_of_frames_out) + ' frames(s)\n'
        result += 'Total render time:\n'
        result += calculate_render_time(time_per_frame_out, num_of_frames_out, num_of_machines_out, unit=unit_out)
        if num_of_machines_out != 1:
            result += 'Per computer (Number of computers: ' + str(num_of_machines_out) + ')'
        cmds.scrollField(output_python, e=True, ip=1, it='')  # Bring Back to the Top
        cmds.scrollField(output_python, edit=True, wordWrap=True, text='', sl=True)
        cmds.scrollField(output_python, edit=True, wordWrap=True, text=result, sl=True)

    def get_timeline_range_num():
        """ Returns the timeline range """
        start = cmds.playbackOptions(q=True, min=True)
        end = cmds.playbackOptions(q=True, max=True)
        return end - start + 1

    def _btn_get_current_timeline(*args):
        """ Populates num_of_frames text field with timeline range """
        current_timeline_num = get_timeline_range_num()
        cmds.intSliderGrp(num_of_frames, e=True, value=current_timeline_num)
        logger.debug(str(args))
        logger.debug(str(current_timeline_num))
        _recalculate_time()

    window_name = "build_gui_render_calculator"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Main GUI Start Here =================================================================================
    window_gui_render_calculator = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                               titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 325), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: _open_gt_tools_documentation())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p=content_main)
    cmds.rowColumnLayout(nc=2, cw=[(1, 190), (2, 90)], cs=[(1, 45)])

    time_per_frame = cmds.intSliderGrp(field=True, label='Average Time Per Frame: ', cw=[(1, 130), (2, 50), (3, 0)],
                                       minValue=1, maxValue=999999,
                                       fieldMinValue=1, fieldMaxValue=999999,
                                       value=1, cc=partial(_recalculate_time))
    unit_option = cmds.optionMenu(label='', cc=partial(_recalculate_time))
    cmds.menuItem(label='Second(s)')
    cmds.menuItem(label='Minute(s)')
    cmds.menuItem(label='Hour(s)')

    cmds.rowColumnLayout(nc=2, cw=[(1, 190), (2, 90)], cs=[(1, 55)], p=content_main)
    num_of_frames = cmds.intSliderGrp(field=True, label='Total Number of Frames: ', cw=[(1, 130), (2, 50), (3, 15)],
                                      minValue=1, fieldMinValue=1, maxValue=999999,
                                      fieldMaxValue=999999, value=get_timeline_range_num(),
                                      cc=partial(_recalculate_time))
    cmds.button('Get Current', height=10, c=_btn_get_current_timeline)
    cmds.rowColumnLayout(nc=2, cw=[(1, 190), (2, 90)], cs=[(1, 55)], p=content_main)
    num_of_machines = cmds.intSliderGrp(field=True, label='Total Number of Machines: ', cw=[(1, 130), (2, 50), (3, 15)],
                                        minValue=1, fieldMinValue=1, maxValue=999999,
                                        fieldMaxValue=999999, value=1,
                                        cc=partial(_recalculate_time))
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space
    cmds.separator(h=10, p=content_main)

    cmds.rowColumnLayout(nc=1, cw=[(1, 390)], cs=[(1, 10)], p=content_main)
    cmds.text(label='Render Time:')
    output_python = cmds.scrollField(editable=True, wordWrap=True)
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_render_calculator)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/render.png')
    widget.setWindowIcon(icon)

    _recalculate_time()

    # Main GUI Ends Here =================================================================================


def _open_gt_tools_documentation():
    """ Opens a web browser with GT Tools docs  """
    cmds.showHelp('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-render-calculator-', absolute=True)


# Build UI
if __name__ == "__main__":
    build_gui_render_calculator()
