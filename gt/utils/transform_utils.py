"""
Transform Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
from dataclasses import dataclass
import maya.cmds as cmds
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def __eq__(self, other):
        """
        Compare Vector3 objects, they are equal if their float values are all the same
        Args:
            other (Vector3): Object to compare
        """
        if isinstance(other, Vector3):
            return (
                    self.x == other.x and
                    self.y == other.y and
                    self.z == other.z
                   )
        return False


@dataclass
class Transform:
    position: Vector3
    rotation: Vector3
    scale: Vector3

    def __eq__(self, other):
        """
        Compare Transform objects, they are equal if all their Vector3 objects are the same
        Args:
            other (Transform): Object to compare
        """
        if isinstance(other, Transform):
            return (
                    self.position == other.position and
                    self.rotation == other.rotation and
                    self.scale == other.scale
                   )
        return False


def move_pivot_top():
    """ Moves pivot point to the top of the boundary box """
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)

    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    counter = 0
    errors = ''
    for obj in selection:
        try:
            bbox = cmds.exactWorldBoundingBox(obj)  # extracts bounding box
            top = [(bbox[0] + bbox[3]) / 2, bbox[4], (bbox[2] + bbox[5]) / 2]  # find top
            cmds.xform(obj, piv=top, ws=True)
            counter += 1
        except Exception as e:
            errors += str(e) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)

    pivot_pos = 'top'
    highlight_style = "color:#FF0000;text-decoration:underline;"
    feedback = FeedbackMessage(quantity=counter,
                               singular='pivot was',
                               plural='pivots were',
                               conclusion='moved to the',
                               suffix=pivot_pos,
                               style_suffix=highlight_style)
    if counter == 1:
        feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                   style_intro=highlight_style,
                                   conclusion='pivot was moved to the',
                                   suffix=pivot_pos,
                                   style_suffix=highlight_style)
    feedback.print_inview_message()


def move_pivot_base():
    """ Moves pivot point to the base of the boundary box """
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)

    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    counter = 0
    errors = ''
    for obj in selection:
        try:
            bbox = cmds.exactWorldBoundingBox(obj)  # extracts bounding box
            bottom = [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]  # find bottom
            cmds.xform(obj, piv=bottom, ws=True)  # sends pivot to bottom
            counter += 1
        except Exception as e:
            errors += str(e) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)
    pivot_pos = 'base'
    highlight_style = "color:#FF0000;text-decoration:underline;"
    feedback = FeedbackMessage(quantity=counter,
                               singular='pivot was',
                               plural='pivots were',
                               conclusion='moved to the',
                               suffix=pivot_pos,
                               style_suffix=highlight_style)
    if counter == 1:
        feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                   style_intro=highlight_style,
                                   conclusion='pivot was moved to the',
                                   suffix=pivot_pos,
                                   style_suffix=highlight_style)
    feedback.print_inview_message()


def move_to_origin():
    """ Moves selected objects back to origin """
    function_name = 'Move to Origin'
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True)
    selection_short = cmds.ls(selection=True)

    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    counter = 0
    errors = ''
    try:
        for obj in selection:
            try:
                cmds.move(0, 0, 0, obj, a=True, rpr=True)  # rpr flag moves it according to the pivot
                counter += 1
            except Exception as e:
                errors += str(e) + '\n'
        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('Some objects could not be moved to the origin. Open the script editor for a list of errors.')

        pivot_pos = 'origin'
        highlight_style = "color:#FF0000;text-decoration:underline;"
        feedback = FeedbackMessage(quantity=counter,
                                   singular='object was',
                                   plural='objects were',
                                   conclusion='moved to the',
                                   suffix=pivot_pos,
                                   style_suffix=highlight_style)
        if counter == 1:
            feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                       style_intro=highlight_style,
                                       conclusion='was moved to the',
                                       suffix=pivot_pos,
                                       style_suffix=highlight_style)
        feedback.print_inview_message()

    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def reset_transforms():
    """
    Reset transforms.
    It checks for incoming connections, then set the attribute to 0 if there are none
    It resets transforms, but ignores translate for joints.
    """
    function_name = 'Reset Transforms'
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    output_errors = ''
    output_counter = 0
    current_selection = cmds.ls(selection=True, long=True) or []
    current_selection_short = cmds.ls(selection=True) or []

    if not current_selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    def reset_trans(selection):
        errors = ''
        counter = 0
        for obj in selection:
            try:
                type_check = cmds.listRelatives(obj, children=True) or []

                if len(type_check) > 0 and cmds.objectType(type_check) != 'joint':
                    obj_connection_tx = cmds.listConnections(obj + '.tx', d=False, s=True) or []
                    if not len(obj_connection_tx) > 0:
                        if cmds.getAttr(obj + '.tx', lock=True) is False:
                            cmds.setAttr(obj + '.tx', 0)
                    obj_connection_ty = cmds.listConnections(obj + '.ty', d=False, s=True) or []
                    if not len(obj_connection_ty) > 0:
                        if cmds.getAttr(obj + '.ty', lock=True) is False:
                            cmds.setAttr(obj + '.ty', 0)
                    obj_connection_tz = cmds.listConnections(obj + '.tz', d=False, s=True) or []
                    if not len(obj_connection_tz) > 0:
                        if cmds.getAttr(obj + '.tz', lock=True) is False:
                            cmds.setAttr(obj + '.tz', 0)

                obj_connection_rx = cmds.listConnections(obj + '.rotateX', d=False, s=True) or []
                if not len(obj_connection_rx) > 0:
                    if cmds.getAttr(obj + '.rotateX', lock=True) is False:
                        cmds.setAttr(obj + '.rotateX', 0)
                obj_connection_ry = cmds.listConnections(obj + '.rotateY', d=False, s=True) or []
                if not len(obj_connection_ry) > 0:
                    if cmds.getAttr(obj + '.rotateY', lock=True) is False:
                        cmds.setAttr(obj + '.rotateY', 0)
                obj_connection_rz = cmds.listConnections(obj + '.rotateZ', d=False, s=True) or []
                if not len(obj_connection_rz) > 0:
                    if cmds.getAttr(obj + '.rotateZ', lock=True) is False:
                        cmds.setAttr(obj + '.rotateZ', 0)

                obj_connection_sx = cmds.listConnections(obj + '.scaleX', d=False, s=True) or []
                if not len(obj_connection_sx) > 0:
                    if cmds.getAttr(obj + '.scaleX', lock=True) is False:
                        cmds.setAttr(obj + '.scaleX', 1)
                obj_connection_sy = cmds.listConnections(obj + '.scaleY', d=False, s=True) or []
                if not len(obj_connection_sy) > 0:
                    if cmds.getAttr(obj + '.scaleY', lock=True) is False:
                        cmds.setAttr(obj + '.scaleY', 1)
                obj_connection_sz = cmds.listConnections(obj + '.scaleZ', d=False, s=True) or []
                if not len(obj_connection_sz) > 0:
                    if cmds.getAttr(obj + '.scaleZ', lock=True) is False:
                        cmds.setAttr(obj + '.scaleZ', 1)
                counter += 1
            except Exception as exception:
                logger.debug(str(exception))
                errors += str(exception) + '\n'
        return errors, counter

    try:
        output_errors, output_counter = reset_trans(current_selection)
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

    if output_counter > 0:
        feedback = FeedbackMessage(quantity=output_counter,
                                   conclusion='transforms were reset.')
        if output_counter == 1:
            feedback = FeedbackMessage(intro=f'"{current_selection_short[0]}"',
                                       style_intro="color:#FF0000;text-decoration:underline;",
                                       conclusion='transforms were reset.')
        feedback.print_inview_message()

    if output_errors != '':
        cmds.warning("Some objects couldn't be reset. Open the script editor for a list of errors.")


def convert_transforms_to_locators():
    """
    Converts transforms to locators without deleting them.
    Essentially places a locator where every transform is.
    """
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)
    errors = ''
    counter = 0
    if not selection:
        cmds.warning('Nothing selected. Please select at least one object and try again.')
        return

    locators_grp = 'transforms_as_locators_grp'
    if not cmds.objExists(locators_grp):
        locators_grp = cmds.group(name=locators_grp, world=True, empty=True)

    for obj in selection:
        try:
            loc = cmds.spaceLocator(name=obj + '_loc')[0]
            cmds.parent(loc, locators_grp)
            cmds.delete(cmds.parentConstraint(obj, loc))
            cmds.delete(cmds.scaleConstraint(obj, loc))
            counter += 1
        except Exception as exception:
            errors += str(exception) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)

    if counter > 0:
        cmds.select(selection)
        feedback = FeedbackMessage(quantity=counter,
                                   singular='locator was',
                                   plural='locators were',
                                   conclusion='created.')
        if counter == 1:
            feedback = FeedbackMessage(intro=f'"{selection_short[0]}"',
                                       style_intro="color:#FF0000;text-decoration:underline;",
                                       conclusion='locator was created.')
        feedback.print_inview_message(system_write=False)
        feedback.conclusion = f'created. Find generated elements in the group "{str(locators_grp)}".'
        sys.stdout.write(f'\n{feedback.get_string_message()}')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
