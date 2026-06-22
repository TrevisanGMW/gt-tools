"""
Camera Utilities

Import Line:
    import gt.core.camera as core_cam
"""

from gt.core.feedback import FeedbackMessage
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def reset_camera_attributes(camera_name="persp", feedback=True):
    """
    Resets the transform and shape attributes of a specified camera to Maya's default values.

    Args:
        camera_name (str, optional): Name of the camera transform node. Defaults to 'persp'.
        feedback (bool, optional): If True, it will give in-view feedback in the current viewport.

    Raises:
        ValueError: If the camera shape is not found.
    """
    try:
        if cmds.objExists(camera_name):
            for scl in ["scaleX", "scaleY", "scaleZ"]:
                cmds.setAttr(f"{camera_name}.{scl}", 1)
    except Exception as e:
        logger.warning(str(e))

    try:
        camera_shape = cmds.listRelatives(camera_name, shapes=True, fullPath=True)
        if not camera_shape:
            raise ValueError(f"No shape found for camera '{camera_name}'.")
        camera_shape = camera_shape[0]

        reset_attr_values = {
            "focalLength": 35,
            "verticalFilmAperture": 0.945,
            "horizontalFilmAperture": 1.417,
            "lensSqueezeRatio": 1,
            "fStop": 5.6,
            "focusDistance": 5,
            "shutterAngle": 144,
            "locatorScale": 1,
            "nearClipPlane": 0.1,
            "farClipPlane": 10000.0,
            "cameraScale": 1,
            "preScale": 1,
            "postScale": 1,
            "depthOfField": 0,
            "centerOfInterest": 44.82186966202994,
            "depth": False,
            "depthType": 1,
            "displayCameraFarClip": False,
            "displayCameraFrustum": False,
            "displayCameraNearClip": False,
            "displayFieldChart": False,
            "displayFilmGate": False,
            "displayFilmOrigin": False,
            "displayFilmPivot": False,
            "displayGateMask": True,
            "displayResolution": False,
            "displaySafeAction": False,
            "displaySafeTitle": False,
            "filmFitOffset": 0.0,
            "filmRollOrder": 0,
            "filmRollValue": 0.0,
            "filmTranslateH": 0.0,
            "filmTranslateV": 0.0,
            "focusRegionScale": 1.0,
            "horizontalFilmOffset": 0.0,
            "horizontalPan": 0.0,
            "horizontalRollPivot": 0.0,
            "horizontalShake": 0.0,
            "image": True,
            "journalCommand": False,
            "mask": True,
            "orthographic": False,
            "orthographicWidth": 10.0,
            "overscan": 1.0,
            "panZoomEnabled": False,
            "renderPanZoom": False,
            "renderable": True,
            "shakeEnabled": False,
            "shakeOverscan": 1.0,
            "shakeOverscanEnabled": False,
            "threshold": 0.9,
            "transparencyBasedDepth": True,
            "tumblePivotX": 0.0,
            "tumblePivotY": 0.0,
            "tumblePivotZ": 0.0,
            "usePivotAsLocalSpace": False,
            "verticalFilmOffset": 0.0,
            "verticalPan": 0.0,
            "verticalRollPivot": 0.0,
            "verticalShake": 0.0,
            "zoom": 1.0,
        }

        if cmds.objExists(camera_shape):
            for key, value in reset_attr_values.items():
                try:
                    cmds.setAttr(f"{camera_shape}.{key}", value)
                except Exception as e:
                    logger.warning(f"Failed to reset {camera_shape}.{key}: {e}")

            cmds.viewFit(camera_name, allObjects=True)

            if feedback:
                feedback_message = f'"{camera_name}" camera attributes were reset back to default values.'
                FeedbackMessage(general_overwrite=feedback_message).print_inview_message()

    except Exception as e:
        logger.warning(str(e))


def get_camera_data(camera_name="persp"):
    """
    Retrieves basic transform and shape attributes from a camera.

    Args:
        camera_name (str): The name of the camera transform node. Defaults to "persp".

    Returns:
        dict: A dictionary with two keys:
            - 'transform': Translation, rotation, scale, visibility, rotateOrder.
            - 'shape': Common camera shape attributes (e.g., focal length, aperture).

    Raises:
        ValueError: If the camera or shape node does not exist.
    """
    if not cmds.objExists(camera_name):
        raise ValueError(f"Camera transform '{camera_name}' does not exist.")

    # Find the shape node under the camera transform
    shapes = cmds.listRelatives(camera_name, shapes=True, fullPath=True)
    if not shapes:
        raise ValueError(f"No camera shape found under transform '{camera_name}'.")
    cam_shape = shapes[0]

    transform_data = {
        "translate": cmds.getAttr(f"{camera_name}.translate")[0],
        "rotate": cmds.getAttr(f"{camera_name}.rotate")[0],
        "scale": cmds.getAttr(f"{camera_name}.scale")[0],
        "visibility": cmds.getAttr(f"{camera_name}.visibility"),
        "rotateOrder": cmds.getAttr(f"{camera_name}.rotateOrder"),
    }

    shape_attrs = [
        "focalLength",
        "horizontalFilmAperture",
        "verticalFilmAperture",
        "lensSqueezeRatio",
        "cameraScale",
        "orthographic",
        "orthographicWidth",
        "nearClipPlane",
        "farClipPlane",
        # Frustum Display Controls
        "displayCameraNearClip",
        "displayCameraFarClip",
        "displayCameraFrustum",
        "displayCameraFrustum",
        # Film Back
        "horizontalFilmAperture",
        "verticalFilmAperture",
        "lensSqueezeRatio",
        "filmFitOffset",
        "horizontalFilmOffset",
        "verticalFilmOffset",
        "shakeEnabled",
        "horizontalShake",
        "verticalShake",
        "shakeOverscanEnabled",
        "shakeOverscan",
        "preScale",
        "filmTranslateH",
        "filmTranslateV",
        "horizontalRollPivot",
        "verticalRollPivot",
        "filmRollValue",
        "filmRollOrder",
        "postScale",
        # Depth of Field
        "depthOfField",
        "fStop",
        "focusRegionScale",
        # Output Settings
        "renderable",
        "image",
        "depth",
        "mask",
        "depthType",
        "transparencyBasedDepth",
        "threshold",
        # Special Effects
        "shutterAngle",
        # Display Options
        "displayFilmGate",
        "displayResolution",
        "displayGateMask",
        "displayFilmGate",
        "displayFieldChart",
        "displaySafeAction",
        "displaySafeTitle",
        "displayFilmPivot",
        "displayFilmOrigin",
        "overscan",
        # 2D Pan/Zoom
        "panZoomEnabled",
        "horizontalPan",
        "verticalPan",
        "zoom",
        "renderPanZoom",
        # Movement Options
        "journalCommand",
        "centerOfInterest",
        "tumblePivotX",
        "tumblePivotY",
        "tumblePivotZ",
        "usePivotAsLocalSpace",
        # Orthographic Views
        "orthographic",
        "orthographicWidth",
    ]

    shape_data = {}
    for attr in shape_attrs:
        if cmds.attributeQuery(attr, node=cam_shape, exists=True):
            shape_data[attr] = cmds.getAttr(f"{cam_shape}.{attr}")

    return {
        "transform": transform_data,
        "shape": shape_data,
    }


def apply_camera_data(data=None, camera_name="persp"):
    """
    Applies transform and shape attributes to a specified camera.

    Args:
        data (dict, optional): The camera data dictionary to apply. Must match format from get_camera_data().
        camera_name (str, optional): The name of the target camera transform node. Defaults to "persp".

    Raises:
        ValueError: If the camera or shape node does not exist.
    """
    if not cmds.objExists(camera_name):
        raise ValueError(f"Camera transform '{camera_name}' does not exist.")
    if not data:
        raise ValueError("Camera data (data) must be provided.")

    shapes = cmds.listRelatives(camera_name, shapes=True, fullPath=True)
    if not shapes:
        raise ValueError(f"No camera shape found under transform '{camera_name}'.")
    cam_shape = shapes[0]

    transform_data = data.get("transform", {})
    if "translate" in transform_data:
        cmds.setAttr(f"{camera_name}.translate", *transform_data["translate"])
    if "rotate" in transform_data:
        cmds.setAttr(f"{camera_name}.rotate", *transform_data["rotate"])
    if "scale" in transform_data:
        cmds.setAttr(f"{camera_name}.scale", *transform_data["scale"])
    if "visibility" in transform_data:
        cmds.setAttr(f"{camera_name}.visibility", transform_data["visibility"])
    if "rotateOrder" in transform_data:
        cmds.setAttr(f"{camera_name}.rotateOrder", transform_data["rotateOrder"])

    shape_data = data.get("shape", {})
    for attr, val in shape_data.items():
        if cmds.attributeQuery(attr, node=cam_shape, exists=True):
            try:
                cmds.setAttr(f"{cam_shape}.{attr}", val)
            except Exception as e:
                print(f"Warning: Could not set attribute {cam_shape}.{attr} to {val}: {e}")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    # reset_camera_attributes()
    cam_data = get_camera_data()
    pprint(cam_data)
    apply_camera_data(cam_data)
