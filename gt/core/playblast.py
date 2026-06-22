"""
Playblast Utilities

Import Line:
    import gt.core.playblast as core_playblast
"""

import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ViewportImageFormats:
    """
    Supported image formats for Maya's `playblast` and render outputs.
    Format names are strings, IDs are stored internally.
    """

    IFF = "iff"  # Maya IFF
    TIF = "tif"  # TIFF
    TIFF = "tiff"  # TIFF alias
    GIF = "gif"  # GIF
    JPG = "jpg"  # JPEG
    JPEG = "jpeg"  # JPEG alias
    EPS = "eps"  # Encapsulated PostScript
    RGB = "rgb"  # SGI RGB
    SGI = "sgi"  # SGI alias
    TGA = "tga"  # Targa
    BMP = "bmp"  # Windows Bitmap
    CIN = "cin"  # Cineon
    YUV = "yuv"  # YUV
    DDS = "dds"  # DirectDraw Surface
    PNG = "png"  # PNG
    EXR = "exr"  # OpenEXR
    HEIF = "heif"  # High Efficiency Image Format
    HEIC = "heic"  # HEIC (container for HEIF)

    # Internal map: format string -> Maya imageFormat ID
    _format_ids = {
        "iff": 0,
        "tif": 1,
        "tiff": 3,
        "gif": 2,
        "jpg": 8,
        "jpeg": 8,
        "eps": 4,
        "rgb": 5,
        "sgi": 6,
        "tga": 7,
        "bmp": 20,
        "cin": 9,
        "yuv": 10,
        "dds": 19,
        "png": 32,
        "exr": 51,
        "heif": 52,
        "heic": 52,
    }

    @classmethod
    def get_all_formats(cls):
        """Returns a list of all supported format strings."""
        return [value for name, value in vars(cls).items() if not name.startswith("_") and isinstance(value, str)]

    @classmethod
    def is_valid(cls, format_name):
        """
        Checks if the given format name is supported.

        Args:
            format_name (str): Format string (e.g., "png")

        Returns:
            bool: True if supported, False otherwise.
        """
        return format_name.lower() in cls._format_ids

    @classmethod
    def get_format_id(cls, format_name):
        """
        Returns the imageFormat ID for the given format name.

        Args:
            format_name (str): Format string (e.g., "png")

        Returns:
            int or None: imageFormat ID or None if unsupported.
        """
        return cls._format_ids.get(format_name.lower())


class ViewportPlayblastFormats:
    """
    Container for all supported video formats for the render_viewport_playblast function.
    """

    QT = "qt"  # QuickTime (.mov), commonly used with H.264 compression
    AVI = "avi"  # AVI format (depends on codec support)
    IMAGE = "image"  # Sequence of images, not an actual video
    MOVIE = "movie"  # Generic movie format (alias in some configurations)

    @classmethod
    def get_all_formats(cls):
        """
        Returns a list of all available video formats (class attributes that are strings and not private or methods).

        Returns:
            list[str]: List of supported format strings.
        """
        return [value for name, value in vars(cls).items() if not name.startswith("_") and isinstance(value, str)]

    @classmethod
    def is_valid(cls, format_name):
        """
        Checks if a given format is supported.

        Args:
            format_name (str): Format name to validate.

        Returns:
            bool: True if format is supported, False otherwise.
        """
        return format_name in cls.get_all_formats()


def render_viewport_snapshot(
    file_name, target_dir, image_format=ViewportImageFormats.JPG, width=512, height=512, frame=None
):
    """
    Renders a snapshot of the current viewport.

    Args:
        file_name (str): Name of the file (without extension).
        target_dir (str): Path to a directory where the image will be stored.
        image_format (str, optional): Format of the output file.
                                      Should match one of ViewportImageFormats values (e.g., "jpg").
        width (int, optional): Width of the snapshot.
        height (int, optional): Height of the snapshot.
        frame (int or float, optional): Frame number to render. If None, uses current frame.

    Returns:
        str or None: Path to generated image. None if it failed.
    """
    if not cmds.objExists("hardwareRenderingGlobals"):
        logger.warning('Unable to find "hardwareRenderingGlobals"')
        return None

    current_line_aa_enable = cmds.getAttr("hardwareRenderingGlobals.lineAAEnable")
    current_multi_sample = cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable")
    current_multi_count = cmds.getAttr("hardwareRenderingGlobals.multiSampleCount")
    current_image_format = cmds.getAttr("defaultRenderGlobals.imageFormat")
    current_frame = cmds.currentTime(query=True)

    # Normalize input format
    fmt = image_format.lower()
    fmt_id = ViewportImageFormats.get_format_id(fmt)

    if fmt_id is None:
        logger.error(f"Unsupported image format: {image_format}")
        return None

    try:
        # Set frame if specified
        if frame is not None:
            cmds.currentTime(frame, edit=True)

        cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", 1)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", 16)
        cmds.setAttr("defaultRenderGlobals.imageFormat", fmt_id)
        cmds.refresh()

        image_file = os.path.join(target_dir, f"{file_name}.{fmt}")

        cmds.playblast(
            completeFilename=image_file,
            startTime=cmds.currentTime(query=True),
            endTime=cmds.currentTime(query=True),
            forceOverwrite=True,
            showOrnaments=False,
            viewer=0,
            format="image",
            qlt=100,
            p=100,
            framePadding=0,
            width=width,
            height=height,
        )
    except Exception as e:
        logger.exception(f"Viewport snapshot failed: {e}")
        return None
    finally:
        # Restore original settings
        cmds.setAttr("defaultRenderGlobals.imageFormat", current_image_format)
        cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", current_line_aa_enable)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", current_multi_sample)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", current_multi_count)

        # Restore original frame if it was changed
        if frame is not None:
            cmds.currentTime(current_frame, edit=True)

    return image_file if os.path.exists(image_file) else None


def render_viewport_playblast(
    file_name,
    target_dir,
    start_frame=1,
    end_frame=24,
    width=512,
    height=512,
    video_format="qt",
    show_ornaments=False,
    frame_padding=4,
):
    """
    Renders a video of the current viewport using playblast.

    Args:
        file_name (str): Name of the video file (without extension).
        target_dir (str): Directory to save the video.
        start_frame (int, optional): Start frame of the video. Default is 1.
        end_frame (int, optional): End frame of the video. Default is 24.
        width (int, optional): Width of the video. Default is 512.
        height (int, optional): Height of the video. Default is 512.
        video_format (str, optional): Video format (usually 'qt' or 'avi'). Default is 'qt'.
        show_ornaments (bool, optional): Whether to include HUD, grid, etc. Default is False.
        frame_padding (int, optional): Frame padding for image sequences. Default is 4.

    Returns:
        str or None: Path to the generated file or None if it failed.
    """
    if not cmds.objExists("hardwareRenderingGlobals"):
        logger.warning('Unable to find "hardwareRenderingGlobals"')
        return None

    # Map file extensions
    ext_map = {
        "qt": "mov",
        "avi": "avi",
        "image": "jpg",
    }
    file_ext = ext_map.get(video_format, "mov")
    video_file = os.path.join(target_dir, f"{file_name}.{file_ext}")

    # Save current render settings to restore later
    current_line_aa_enable = cmds.getAttr("hardwareRenderingGlobals.lineAAEnable")
    current_multi_sample = cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable")
    current_multi_count = cmds.getAttr("hardwareRenderingGlobals.multiSampleCount")

    # Set anti-aliasing for quality
    cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", 1)
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
    cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", 16)

    try:
        cmds.refresh()

        playblast_args = {
            "startTime": start_frame,
            "endTime": end_frame,
            "format": video_format,
            "filename": video_file,
            "forceOverwrite": True,
            "clearCache": True,
            "showOrnaments": show_ornaments,
            "viewer": False,
            "offScreen": True,
            "percent": 100,
            "widthHeight": (width, height),
            "framePadding": frame_padding,
        }

        if video_format == "qt":
            try:  # Try H.264 first
                logger.debug("Trying playblast with H.264 compression...")
                cmds.playblast(**playblast_args, compression="H.264")
            except RuntimeError as e:
                if "codec" in str(e).lower() or "compression" in str(e).lower():
                    logger.debug("H.264 compression failed. Retrying without compression...")
                    cmds.playblast(**playblast_args)  # No compression
                else:
                    raise
        else:
            cmds.playblast(**playblast_args)  # No compression for other formats

    except Exception as e:
        logger.error(f"Failed to render viewport video: {e}")
        return None
    finally:
        # Restore render settings
        cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", current_line_aa_enable)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", current_multi_sample)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", current_multi_count)

    return video_file if os.path.exists(video_file) else None


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    out = None
    from gt.utils.system import get_desktop_path, get_formatted_time

    # out = render_viewport_snapshot(get_formatted_time(format_str="Snapshot %Y-%m-%d %H%M%S"), get_desktop_path())
    out = render_viewport_playblast(
        file_name=get_formatted_time(format_str="Playblast %Y-%m-%d %H%M%S"),
        target_dir=get_desktop_path(),
        start_frame=1,
        end_frame=24,
        width=512,
        height=512,
        video_format="qt",
        show_ornaments=True,
    )
    pprint(out)
