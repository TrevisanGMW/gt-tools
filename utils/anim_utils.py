"""
Animation Utilities
"""
import maya.cmds as cmds
import logging
import random


# Logging Setup
logging.basicConfig()
logger = logging.getLogger("anim_utils")
logger.setLevel(logging.INFO)


def delete_keyframes():
    """Deletes all keyframes. (Doesn't include Set Driven Keys)"""
    function_name = 'Delete All Keyframes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        keys_ta = cmds.ls(type='animCurveTA')
        keys_tl = cmds.ls(type='animCurveTL')
        keys_tt = cmds.ls(type='animCurveTT')
        keys_tu = cmds.ls(type='animCurveTU')
        # keys_ul = cmds.ls(type='animCurveUL') # Use optionVar to determine if driven keys should be deleted
        # keys_ua = cmds.ls(type='animCurveUA')
        # keys_ut = cmds.ls(type='animCurveUT')
        # keys_uu = cmds.ls(type='animCurveUU')
        deleted_counter = 0
        all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
        for obj in all_keyframes:
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))
        in_view_message = '<' + str(random.random()) + '>'
        if deleted_counter > 0:
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter)
            in_view_message += ' </span>'
            is_plural = 'keyframe nodes were'
            if deleted_counter == 1:
                is_plural = 'keyframe node was'
            in_view_message += is_plural + ' deleted.'
        else:
            in_view_message += 'No keyframes found in this scene.'

        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
