"""
Camera Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def reset_persp_shape_attributes():
    """
    If persp shape exists (default camera), reset its attributes
    """
    cam_transform = 'persp'
    cam_shape = 'perspShape'
    try:
        if cmds.objExists(cam_transform):
            for scl in ["sx", "sy", "sz"]:
                cmds.setAttr(f"{cam_transform}.{scl}", 1)
    except Exception as e:
        logger.warning(str(e))

    try:
        reset_attr_values = {"focalLength": 35,
                             "verticalFilmAperture": 0.945,
                             "horizontalFilmAperture": 1.417,
                             "lensSqueezeRatio": 1,
                             "fStop": 5.6,
                             "focusDistance": 5,
                             "shutterAngle": 144,
                             "locatorScale": 1,
                             "nearClipPlane": 0.100,
                             "farClipPlane": 10000.000,
                             "cameraScale": 1,
                             "preScale": 1,
                             "postScale": 1,
                             "depthOfField": 0,
                             }
        if cmds.objExists(cam_shape):
            for key, value in reset_attr_values.items():
                cmds.setAttr(f"{cam_shape}.{key}", value)
            cmds.viewFit(allObjects=True)

            feedback_message = f'"{cam_transform}" camera attributes were reset back to default values.'
            feedback = FeedbackMessage(general_overwrite=feedback_message)
            feedback.print_inview_message()

    except Exception as e:
        logger.warning(str(e))


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
