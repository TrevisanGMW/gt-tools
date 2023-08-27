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


def create_shelf_button(command,
                        label='',
                        tooltip='',
                        image=None,  # Default Python Icon
                        label_color=(1, 0, 0),  # Default Red
                        label_bgc_color=(0, 0, 0, 1),  # Default Black
                        bgc_color=None
                        ):
    """
    Add a shelf button to the current shelf (according to the provided parameters)

    Args:
        command (str): A string containing the code or command you want the button to run when clicking on it.
                       e.g. "print("Hello World")"
        label (str): The label of the button. This is the text you see below it.
        tooltip (str): The help message you get when hovering the button.
        image (str): The image used for the button (defaults to Python icon if none)
        label_color (tuple): A tuple containing three floats,
                             these are RGB 0 to 1 values to determine the color of the label.
        label_bgc_color (tuple): A tuple containing four floats,
                                 these are RGBA 0 to 1 values to determine the background of the label.
        bgc_color (tuple): A tuple containing three floats,
                           these are RGB 0 to 1 values to determine the background of the icon

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
