"""
Playblast Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_viewport_snapshot(file_name, target_dir, image_format="jpg"):
    """
    Generate curve thumbnail
    Args:
        file_name (str): Name of the file (without extension)
        target_dir (str): Path to a directory where the curve thumbnails will be stored.
        image_format (str, optional): Format of the output file. Can be "jpg" or "png". Default: "jpg"

    Returns:
        str or None: Path to generated image. None if it failed.
    """

    current_line_aa_enable = cmds.getAttr(f'hardwareRenderingGlobals.lineAAEnable')
    current_multi_sample = cmds.getAttr(f'hardwareRenderingGlobals.multiSampleEnable')
    current_multi_count = cmds.getAttr(f'hardwareRenderingGlobals.multiSampleCount')
    current_image_format = cmds.getAttr("defaultRenderGlobals.imageFormat")

    # Setup Viewport and Render Image
    cmds.setAttr(f'hardwareRenderingGlobals.lineAAEnable', 1)
    cmds.setAttr(f'hardwareRenderingGlobals.multiSampleEnable', 1)
    cmds.setAttr(f'hardwareRenderingGlobals.multiSampleCount', 16)
    cmds.refresh()
    image_file = os.path.join(target_dir, f'{file_name}.{image_format}')
    if image_format == "jpg" or image_format == "jpeg":
        cmds.setAttr("defaultRenderGlobals.imageFormat", 8)  # JPEG
    elif image_format == "png":
        cmds.setAttr("defaultRenderGlobals.imageFormat", 32)  # PNG
    cmds.playblast(completeFilename=image_file, startTime=True, endTime=True, forceOverwrite=True, showOrnaments=False,
                   viewer=0, format="image", qlt=100, p=100, framePadding=0, w=512, h=512)
    cmds.setAttr("defaultRenderGlobals.imageFormat", current_image_format)
    cmds.setAttr(f'hardwareRenderingGlobals.lineAAEnable', current_line_aa_enable)
    cmds.setAttr(f'hardwareRenderingGlobals.multiSampleEnable', current_multi_sample)
    cmds.setAttr(f'hardwareRenderingGlobals.multiSampleCount', current_multi_count)
    if os.path.exists(image_file):
        return image_file


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    from gt.utils.system_utils import get_desktop_path
    out = create_viewport_snapshot("temp", get_desktop_path())
    pprint(out)
