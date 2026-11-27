"""Builds the pose-sheet images and review files for the VLM pass, using the shared skeleton renderer."""

import base64
import datetime
import json
import math
import shutil
import tempfile
import time
from pathlib import Path

from gt.core import render
from gt.tools.annotation_tracker import auto_annotation_model as model

DEBUG_RUNS_KEPT = 10
STALE_CAPTURE_SECONDS = 24 * 3600
SECONDS_PER_POSE = 0.5
MAX_CHUNKS_PER_RANGE = 8
IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
EXTENSIONS = {media_type: extension.lstrip(".") for extension, media_type in reversed(list(IMAGE_TYPES.items()))}
VIEW_SETTINGS = (
    ("vlm_view_side", render.VIEW_SIDE), ("vlm_view_front", render.VIEW_FRONT),
    ("vlm_view_travel", render.VIEW_TRAVEL), ("vlm_view_top", render.VIEW_TOP),
)
SHEET_NOTE = (
    "Each image is a pose sheet for one annotation range: skeleton poses in time order from left to right, with "
    "frame numbers and seconds under each pose. Blue is the character's left side, red is the right side, grey is "
    "the spine and head. The SIDE view always shows the character facing right. FRONT shows the character from the "
    "front. TRAVEL places poses at their real positions with older poses fainter. TOP is a map from above: the "
    "dashed line is the pelvis path, numbers give pose order and the dot on each line marks facing. The skeleton "
    "does not show props or furniture, so infer interactions only from body motion. Each image caption names the "
    "target it belongs to."
)


def get_cache_directory():
    """Resolves the GT-Tools cache folder used for VLM files.

    Returns:
        Path: Cache folder for this feature. It is not created here.
    """
    return model._prefs_directory().parent / "cache" / "annotation_vlm"


def get_debug_directory():
    """Resolves the folder that holds generated request previews.

    Returns:
        Path: Preview root folder. It is not created here.
    """
    return get_cache_directory() / "debug"


def get_last_reply_path():
    """Resolves the file that stores the last model reply.

    Returns:
        Path: JSON file path. It may not exist.
    """
    return get_cache_directory() / "last_reply.json"


def purge_debug_files():
    """Deletes generated previews, leftover captures and the stored last reply.

    Returns:
        int: Number of files removed.
    """
    removed = 0
    for folder in (get_debug_directory(), get_cache_directory() / "capture"):
        if folder.is_dir():
            removed += sum(1 for item in folder.rglob("*") if item.is_file())
            shutil.rmtree(folder, ignore_errors=True)
    reply = get_last_reply_path()
    if reply.is_file():
        reply.unlink()
        removed += 1
    return removed


def save_last_reply(provider_settings, requests):
    """Stores the latest model replies, or failures, so they can be inspected later.

    Args:
        provider_settings (tuple): Provider, endpoint, model and credential variable. The key is never saved.
        requests (list): One dict per request with ``target``, ``images``, ``status`` and ``suggestions`` or ``error``.

    Returns:
        Path: Stored file.
    """
    provider, endpoint, name, _ = provider_settings
    document = {
        "time": datetime.datetime.now().isoformat(timespec="seconds"), "provider": provider, "endpoint": endpoint,
        "model": name, "requests": requests,
    }
    path = get_last_reply_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return path


def read_last_reply():
    """Reads the latest stored model reply.

    Returns:
        dict or None: Stored reply document, or None when nothing is stored.
    """
    path = get_last_reply_path()
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def get_views(settings):
    """Lists the views enabled in the settings.

    Args:
        settings (dict): Effective Auto Annotate settings.

    Returns:
        list: View names. Falls back to the side view when none is enabled.
    """
    views = [view for key, view in VIEW_SETTINGS if settings.get(key, True)]
    return views or [render.VIEW_SIDE]


def plan_images(spans, max_images, poses_per_image, fps):
    """Decides which frame spans get an image and splits long ones into parts.

    Args:
        spans (list): ``(range_index, first_frame, last_frame)`` for each eligible range.
        max_images (int): Maximum images for the whole request.
        poses_per_image (int): Poses drawn in each image.
        fps (float): Frames per second.

    Returns:
        list: Dictionaries with ``range_index``, ``first``, ``last``, ``part`` and ``parts``.
    """
    if not spans or max_images < 1:
        return []
    if len(spans) > max_images:
        if max_images == 1:
            spans = [spans[len(spans) // 2]]
        else:
            spans = [spans[round(step * (len(spans) - 1) / (max_images - 1))] for step in range(max_images)]
    parts = {span[0]: 1 for span in spans}
    wanted = {
        index: min(MAX_CHUNKS_PER_RANGE, math.ceil(math.ceil((last - first) / fps / SECONDS_PER_POSE) / poses_per_image))
        for index, first, last in spans
    }
    for _ in range(max_images - len(spans)):
        growing = [span for span in spans if parts[span[0]] < wanted[span[0]]]
        if not growing:
            break
        best = max(growing, key=lambda span: (span[2] - span[1]) / parts[span[0]])
        parts[best[0]] += 1
    plan = []
    for index, first, last in spans:
        total = last - first + 1
        count = max(1, min(parts[index], total // 2 or 1))
        for part in range(count):
            part_first = first + total * part // count
            part_last = first + total * (part + 1) // count - 1
            plan.append({"range_index": index, "first": part_first, "last": part_last, "part": part + 1, "parts": count})
    return plan


def make_caption(item):
    """Names an image after its target range and frame span.

    Args:
        item (dict): Entry from plan_images.

    Returns:
        str: Caption such as ``range_3 frames 40-120 part 1 of 2``.
    """
    text = f"range_{item['range_index'] + 1} frames {item['first']}-{item['last']}"
    return f"{text} part {item['part']} of {item['parts']}" if item["parts"] > 1 else text


def get_span_cues(analysis, first, last):
    """Measures duration, travel and height for a frame span.

    Args:
        analysis (dict): Motion analysis with sampled positions.
        first (int): First frame.
        last (int): Last frame.

    Returns:
        dict: Measured facts, or an empty dict when positions are unavailable.
    """
    positions = (analysis or {}).get("positions")
    if not positions:
        return {}
    begin = max(first - analysis["start"], 0)
    end = min(last - analysis["start"] + 1, len(positions))
    if end <= begin:
        return {}
    return render.describe_span(
        positions[begin:end], analysis["fps"], analysis["leg_length"], analysis["floor"]
    )


def _encode(path):
    """Reads an image file as base64.

    Args:
        path (Path): Image file.

    Returns:
        tuple: Media type and base64 text, or None for unsupported or oversized files.
    """
    media_type = IMAGE_TYPES.get(path.suffix.lower())
    if not media_type or path.stat().st_size > 5_000_000:
        return None
    return media_type, base64.b64encode(path.read_bytes()).decode("ascii")


def _get_capture_root():
    """Creates the folder for in-flight renders and removes leftovers from crashed runs.

    Returns:
        Path: Folder that holds one temporary folder per run.
    """
    root = get_cache_directory() / "capture"
    root.mkdir(parents=True, exist_ok=True)
    for folder in root.iterdir():
        try:
            if folder.is_dir() and time.time() - folder.stat().st_mtime > STALE_CAPTURE_SECONDS:
                shutil.rmtree(folder, ignore_errors=True)
        except OSError:
            continue
    return root


def render_images(analysis, plan, views, poses_per_image, progress=None, image_width=1024):
    """Renders one pose sheet per planned span and encodes it. Temporary files are deleted afterwards.

    Args:
        analysis (dict): Motion analysis with sampled positions.
        plan (list): Entries from plan_images.
        views (list): Views to draw.
        poses_per_image (int): Poses per row.
        progress (AnnotationProgress, optional): Interactive progress display.
        image_width (int): Widest allowed image in pixels. Wider sheets are scaled down, which speeds up inference.

    Returns:
        list: ``(middle_frame, media_type, base64_text, caption)`` per image.
    """
    from gt.ui.qt_import import QtCore

    positions = analysis.get("positions")
    if not positions:
        raise ValueError("No skeleton motion data is available to draw pose sheets.")
    images = []
    with tempfile.TemporaryDirectory(prefix="sheets_", dir=str(_get_capture_root())) as temporary:
        for number, item in enumerate(plan, start=1):
            if progress:
                progress.update_stage(f"Drawing pose sheet {number} of {len(plan)}…", number - 1, len(plan))
            begin = item["first"] - analysis["start"]
            frames = list(range(item["first"], item["last"] + 1))
            sheet = render.render_pose_sheet(
                positions[begin:begin + len(frames)], frames, views, analysis["fps"], poses_per_image,
                leg_length=analysis["leg_length"], floor=analysis["floor"],
            )
            if sheet.width() > image_width:
                sheet = sheet.scaledToWidth(image_width, QtCore.Qt.TransformationMode.SmoothTransformation)
            path = Path(temporary) / f"sheet_{number:02d}.png"
            render.save_image(sheet, path)
            media_type, data = _encode(path)
            images.append(((item["first"] + item["last"]) // 2, media_type, data, make_caption(item)))
    return images


def load_provided_images(paths, start, end):
    """Encodes pre-rendered images supplied by the caller.

    Args:
        paths (dict): Frame numbers mapped to absolute image paths.
        start (int): First frame under analysis.
        end (int): Last frame under analysis.

    Returns:
        list: ``(frame, media_type, base64_text)`` per usable image.
    """
    if not isinstance(paths, dict):
        raise ValueError("Image paths must map frame numbers to absolute PNG, JPG, or WebP paths.")
    selected = {int(frame): Path(path) for frame, path in paths.items() if start <= int(frame) <= end}
    if any(not path.is_absolute() for path in selected.values()):
        raise ValueError("Supply absolute image paths for unattended VLM requests.")
    images = []
    for frame, path in sorted(selected.items()):
        encoded = _encode(path)
        if encoded:
            images.append((frame, *encoded))
    return images


def _image_caption(item):
    """Gets the caption of an image tuple.

    Args:
        item (tuple): ``(frame, media_type, data)`` with an optional caption.

    Returns:
        str: Caption text.
    """
    return item[3] if len(item) > 3 else f"Frame {item[0]}"


def write_preview(groups, images, provider_settings):
    """Writes the exact images and prompts of a run into a new review folder without sending anything.

    Args:
        groups (list): Request groups with ``target_names``, ``images`` and ``prompt``.
        images (list): All image tuples as returned by render_images.
        provider_settings (tuple or None): Provider, endpoint, model and credential variable. The key is never saved.

    Returns:
        Path: Review folder.
    """
    root = get_debug_directory()
    folder = root / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)
    for number, item in enumerate(images, start=1):
        media_type, data = item[1], item[2]
        caption = _image_caption(item)
        name = "_".join(caption.split()).replace("/", "-")
        (folder / f"image_{number:02d}_{name}.{EXTENSIONS.get(media_type, 'img')}").write_bytes(base64.b64decode(data))
    requests = []
    for number, group in enumerate(groups, start=1):
        label = "_".join(group["target_names"])[:60]
        (folder / f"prompt_{number:02d}_{label}.txt").write_text(group["prompt"], encoding="utf-8")
        requests.append({
            "prompt_file": f"prompt_{number:02d}_{label}.txt", "targets": group["target_names"],
            "images": [_image_caption(item) for item in group["images"]],
        })
    provider, endpoint, name, _ = provider_settings or ("", "", "", "")
    summary = {
        "provider": provider, "endpoint": endpoint, "model": name, "request_count": len(requests),
        "requests": requests, "note": "Preview only. Nothing was sent.",
    }
    (folder / "request.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for old_folder in sorted(path for path in root.iterdir() if path.is_dir())[:-DEBUG_RUNS_KEPT]:
        shutil.rmtree(old_folder, ignore_errors=True)
    return folder
