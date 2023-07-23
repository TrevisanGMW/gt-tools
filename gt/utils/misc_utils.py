"""
Misc Utilities - Any utilities that might not clearly fit in an existing category.
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
import maya.cmds as cmds
import maya.mel as mel
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def open_resource_browser():
    """ Opens Maya's Resource Browser """
    try:
        import maya.app.general.resourceBrowser as resourceBrowser
        resourceBrowser.resourceBrowser().run()
    except Exception as e:
        logger.debug(str(e))


def material_copy():
    """ Copies selected material to clipboard """
    selection = cmds.ls(selection=True)
    try:
        mel.eval('ConvertSelectionToFaces;')
        cmds.polyClipboard(copy=True, shader=True)
        feedback = FeedbackMessage(prefix='Material',
                                   intro='copied',
                                   style_intro="color:#FF0000;text-decoration:underline;",
                                   conclusion='to the clipboard.')
        feedback.print_inview_message(system_write=False)
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Couldn't copy material. Make sure you selected an object or component before copying.")
    cmds.select(selection)


def material_paste():
    """ Pastes selected material to clipboard """
    try:
        cmds.polyClipboard(paste=True, shader=True)
        feedback = FeedbackMessage(prefix='Material',
                                   intro='pasted',
                                   style_intro="color:#FF0000;text-decoration:underline;",
                                   conclusion='from the clipboard.')
        feedback.print_inview_message(system_write=False)
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Couldn't paste material. Make sure you copied a material first, "
                     "then selected the target objects or components.")


def output_string_to_notepad(string, file_name='tmp'):
    """
    Creates a txt file and writes a list of objects to it (with necessary code used to select it, in Mel and Python)

    Args:
        string (string): A list of string to be exported to a txt file
        file_name (string): Name of the generated file

    """
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir + file_name + '.txt'

    f = open(txt_file, 'w')
    f.write(string)
    f.close()

    notepad_command = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepad_command)
