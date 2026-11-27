"""Shared Auto Annotate entry point for Maya, Annotation Tracker, and Batch Processor."""

import json
import math
from pathlib import Path

from gt.tools.annotation_tracker import annotation_tracker_model, annotation_tracker_scene
from gt.tools.annotation_tracker import auto_annotation_model as model
from gt.tools.annotation_tracker import auto_annotation_motion as motion
from gt.tools.annotation_tracker import auto_annotation_rules as rules
from gt.tools.annotation_tracker import auto_annotation_scene as scene
from gt.tools.annotation_tracker.auto_annotation_model import read_settings_file as load_annotation_settings


def resolve_schema(context=None, schema=None, schema_path=None):
    """Selects the schema used by the interactive or unattended caller.

    Args:
        context (dict, optional): Tracker or Batch Processor context.
        schema (dict, optional): Explicit schema.
        schema_path (str, optional): Explicit schema JSON file.

    Returns:
        dict: Active schema.
    """
    context = context or {}
    if schema is None and schema_path:
        path = Path(schema_path).expanduser()
        if not path.is_absolute() and context.get("project_dir"):
            path = Path(context["project_dir"]) / path
        schema = annotation_tracker_model.read_schema(path)
    if schema is None:
        schema = context.get("schema")
    if schema is None:
        tracker = annotation_tracker_model.AnnotationTrackerModel()
        path = annotation_tracker_model.resolve_schema_path(
            tracker.get_preference("schema_path", ""), tracker.get_preference("use_custom_schema", False)
        )
        schema = annotation_tracker_model.read_schema(path)
    if not isinstance(schema, dict) or not schema:
        raise ValueError("Choose a valid Annotation Tracker schema.")
    return schema


def _effective_settings(context, overrides):
    """Combines preferences, project automation settings, and explicit inputs.

    Args:
        context (dict): Tracker or Batch Processor context.
        overrides (dict): Explicit per-run values.

    Returns:
        tuple: Effective settings and explicit configuration values.
    """
    settings_file = None
    settings_values = None
    environment = context.get("environment_variables") or {}
    project_options = environment.get("annotation-options") or (
        environment.get("gt-annotation-options") or environment.get("GT_ANNOTATION_OPTIONS") or {}
    )
    if isinstance(project_options, str):
        project_options = json.loads(project_options)
    context_options = context.get("annotation_options") or {}
    if not isinstance(project_options, dict) or not isinstance(context_options, dict):
        raise ValueError("Annotation options must be a JSON object or dictionary.")
    project_settings_path = (
        environment.get("annotation-settings")
        or environment.get("gt-annotation-settings") or environment.get("GT_ANNOTATION_SETTINGS")
        or context.get("settings_path")
    )
    explicit = {}
    for layer in (
        {"settings_path": project_settings_path} if project_settings_path else {},
        project_options, context_options, overrides,
    ):
        layer = dict(layer)
        if "settings_path" in layer or "settings" in layer:
            settings_file = layer.pop("settings_path", None)
            settings_values = layer.pop("settings", None)
            if settings_file and settings_values is not None:
                raise ValueError("Choose an exported settings path or an in-memory settings dictionary.")
        if {"profile_path", "profile", "calibration"} & layer.keys():
            for key in ("profile", "profile_path", "calibration"):
                if key not in layer:
                    explicit.pop(key, None)
        explicit.update(layer)
        if layer.get("profile_path") and "profile_location" not in layer:
            explicit["profile_location"] = "custom"
        if {"profile", "profile_path", "calibration"} & layer.keys() and "use_profile" not in layer:
            explicit["use_profile"] = True

    if settings_file:
        path = Path(settings_file).expanduser()
        if not path.is_absolute() and context.get("project_dir"):
            path = Path(context["project_dir"]) / path
        settings = load_annotation_settings(path)
    elif settings_values is not None:
        settings = model.normalize_settings(settings_values)
    else:
        settings = model.load_settings()
    if (settings_file or settings_values is not None) and "schema" not in settings and not context.get("schema"):
        settings["schema"] = annotation_tracker_model.read_schema(annotation_tracker_model.get_sample_schema_path())
    known = set(model.DEFAULT_SETTINGS) | {
        "profile", "profile_path", "profile_location", "schema", "schema_path", "frame_range",
        "floor_height", "file_data", "dry_run", "image_paths", "vlm_preview",
    }
    unknown = sorted(explicit.keys() - known)
    if unknown:
        raise ValueError(f"Unknown annotation options: {', '.join(unknown)}.")
    settings.update(explicit)
    for key in (
        "use_profile", "allow_remote_vlm", "vlm_local_auto_load", "dry_run",
        "vlm_local_eject_other_models",
        "auto_set_quality", "auto_set_clipped", "auto_set_annotated", "short_name_fallback",
    ):
        if key in settings and type(settings[key]) is not bool:
            raise ValueError(f"'{key}' must be true or false.")
    if settings["vlm_mode"] not in ("off", "review", "auto"):
        raise ValueError("VLM mode must be off, review, or auto.")
    if settings["fill_mode"] not in model.FILL_MODES:
        raise ValueError("Fill mode must be gaps or overwrite.")
    if settings["file_style_source"] not in ("keep", "fixed", "vlm"):
        raise ValueError("File style source must be keep, fixed, or vlm.")
    if settings["commercial_use"] is not None and type(settings["commercial_use"]) is not bool:
        raise ValueError("Commercial use must be true, false, or null.")
    if not isinstance(settings["quality_preset"], dict):
        raise ValueError("The quality preset must be a Motion Evaluator preset dictionary.")
    if not isinstance(settings["pose_field"], str) or settings["pose_field"] in ("", "state"):
        raise ValueError("Choose a separate schema field for calibrated pose labels.")
    return settings, explicit


def _get_profile(settings, explicit, context):
    """Gets embedded calibration or a deliberate legacy runtime override.

    Args:
        settings (dict): Resolved options.
        explicit (dict): Options deliberately supplied by the caller.
        context (dict): Runtime context.

    Returns:
        dict: Portable calibration to apply.
    """
    if not settings["use_profile"]:
        return {}
    if "profile" in explicit:
        return model.normalize_profile(explicit["profile"])
    if "profile_path" in explicit:
        try:
            path = model.get_profile_path(settings, project_dir=context.get("project_dir"))
            return model.read_profile(path)
        except (OSError, ValueError) as error:
            raise ValueError(f"Could not load annotation profile: {error}") from error
    calibration = settings.get("calibration")
    return model.normalize_profile(calibration) if calibration is not None else {}


def _measure(cmds, mapping, settings, start, end):
    """Samples the resolved skeleton for locomotion and pose analysis.

    Args:
        cmds (module): Maya commands module.
        mapping (dict): Resolved joint paths.
        settings (dict): Runtime options.
        start (int): First sampled frame.
        end (int): Last sampled frame.

    Returns:
        dict: Measured motion and pose.
    """
    floor = settings.get("floor_height")
    if floor is not None:
        floor = float(floor)
        if not math.isfinite(floor):
            raise ValueError("Floor height must be finite.")
    return motion.analyze_motion(scene.sample_joints(cmds, mapping, start, end), floor_height=floor)


def _resolve_source(cmds, settings):
    """Works out the Source value from a fixed text or the scene's folder path.

    Args:
        cmds (module): Maya commands module.
        settings (dict): Runtime options.

    Returns:
        str: Source text, or an empty string when none applies.
    """
    mode = settings["file_source_mode"]
    if mode == "fixed":
        return settings["file_source"].strip()
    if mode == "path":
        path = cmds.file(query=True, sceneName=True) or ""
        found = model.find_source_in_path(
            path, settings["file_source_pattern"], settings["file_source_depth"], settings["file_source_order"]
        )
        fallback = settings["file_source_fallback"]
        if found or fallback == "none":
            return found
        print(f"[Auto Annotate] No folder matched the Source pattern. Using the fallback: {fallback}.")
        return settings["file_source"].strip() if fallback == "text" else model.find_source_in_path(path)
    return ""


def _apply_file_data(cmds, data, settings, fields, warnings):
    """Fills opted-in file fields and preserves existing manual metadata.

    Args:
        cmds (module): Maya commands module.
        data (dict): Mutable file-level annotation data.
        settings (dict): Runtime options.
        fields (dict): Active schema's file-level definitions.
        warnings (list): Non-blocking diagnostics.
    """
    supplied = settings.get("file_data", {})
    if not isinstance(supplied, dict):
        raise ValueError("File metadata must be a dictionary.")
    values = {}
    if settings["commercial_use"] is not None and "commercial_use" in fields:
        values["commercial_use"] = settings["commercial_use"]
    if settings["file_style_source"] == "fixed" and "style" in fields:
        values["style"] = settings["file_style"]
    if "source" in fields and model.is_empty(data.get("source")):
        source = _resolve_source(cmds, settings)
        if source:
            values["source"] = source
            print(f"[Auto Annotate] Source set to '{source}'.")
        elif settings["file_source_mode"] != "keep":
            warnings.append("Could not determine the Source. Check the Source mode on the Metadata tab.")
    values.update(supplied)
    for name, value in values.items():
        if name in ("annotated", "clipped"):
            continue
        if name == "style" and isinstance(value, str) and value.strip().lower() in ("none", "---"):
            warnings.append("File Style cannot be 'none'. Choose a real style on the Metadata tab.")
        elif not model.supports_value(fields.get(name), value):
            warnings.append(f"File metadata '{name}' does not match the active schema.")
        elif model.is_empty(data.get(name)):
            data[name] = value
    if settings["auto_set_clipped"] and model.supports_value(fields.get("clipped"), True):
        try:
            if scene.has_valid_clips(cmds):
                data["clipped"] = True
            elif model.is_empty(data.get("clipped")):
                data["clipped"] = False
        except (RuntimeError, ValueError) as error:
            warnings.append(f"Could not check Clip Tracker data: {error}")


def _apply_quality(cmds, mapping, bounds, preset, field, file_data):
    """Evaluates playback and fills the active schema's quality field.

    Args:
        cmds (module): Maya commands module.
        mapping (dict): Resolved joint paths.
        bounds (tuple): Entire playback range.
        preset (dict): Motion Evaluator options.
        field (dict): File Quality schema definition.
        file_data (dict): Mutable annotation file metadata.

    Returns:
        dict: Motion Evaluator report.
    """
    from gt.tools.annotation_tracker.auto_annotation_quality import evaluate_quality

    report = evaluate_quality(cmds, mapping, bounds, preset)
    if field.get("type") == "integer":
        value = report["score"]
    else:
        status_labels = {"passed": "high", "warning": "medium", "failed": "low"}
        value = status_labels.get(report["status"])
    if model.supports_value(field, value):
        file_data["quality"] = value
    return report


def _analysis_bounds(playback, override):
    """Gets a requested integral analysis range within playback.

    Args:
        playback (tuple): Full playback bounds.
        override (tuple or list or None): Optional subrange.

    Returns:
        tuple: First and last analysis frame.
    """
    bounds = playback if override is None else override
    if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
        raise ValueError("Frame range must contain two integer frame numbers.")
    start, end = bounds
    if type(start) is not int or type(end) is not int or not playback[0] <= start <= end <= playback[1]:
        raise ValueError("Frame range must contain ordered integer bounds within playback.")
    return start, end


def preview_vlm_request(context=None, **overrides):
    """Builds the VLM images and prompt for the current scene and saves them for review. Nothing is sent or changed.

    Args:
        context (dict, optional): Annotation Tracker or Batch Processor context.
        **overrides: Same options as run_annotation, for example settings or schema.

    Returns:
        dict: Run result. ``vlm["preview_folder"]`` is the review folder, or None when nothing could be built.
    """
    return run_annotation(context, **dict(overrides, vlm_preview=True))


def run_annotation(context=None, **overrides):
    """Annotates the current scene through one shared Python entry point.

    Args:
        context (dict, optional): Annotation Tracker or Batch Processor context.
        **overrides: Pass settings_path or settings to use a dataset setup without reading or changing Prefs.
            Other options include embedded calibration, use_profile, skeleton_mode, skeleton_root,
            joint_map, short_name_fallback, pose_field, schema/schema_path,
            frame_range, floor_height, file_data, VLM settings, image_paths, or dry_run.
            Batch projects may use annotation-settings for the path and annotation-options for overrides.

    Returns:
        dict: Outcome, normalized payload, added ranges, validation, and diagnostics.
    """
    context = context or {}
    cmds = annotation_tracker_scene._get_maya_cmds()
    settings, explicit = _effective_settings(context, overrides)
    schema_path = settings.get("schema_path")
    schema = resolve_schema(context, None if schema_path else settings.get("schema"), schema_path)
    playback = scene.playback_bounds(cmds)
    start, end = _analysis_bounds(playback, settings.get("frame_range"))
    preview_vlm = bool(settings.get("vlm_preview"))
    dry_run = bool(settings.get("dry_run") or context.get("preview") or preview_vlm)
    needs_vlm = preview_vlm or (settings["vlm_mode"] != "off" and not dry_run)
    warnings = []
    original = scene.read_payload(cmds, context)
    profile = _get_profile(settings, explicit, context)
    profile_summary = model.describe_profile(profile, settings["use_profile"])
    if not settings["use_profile"] and model.has_calibration(settings.get("calibration")):
        warnings.append(
            "A custom calibration profile is saved but disabled. "
            "Choose Custom Profile in Annotation Setup > Calibration and click Save to use it."
        )
    pose_field = settings["pose_field"]
    if profile and "pose_field" not in explicit and ("profile" in explicit or "profile_path" in explicit):
        pose_field = profile.get("label_source", "stance")
    range_fields = model.get_schema_fields(schema, "frame_range")
    pose_definition = range_fields.get(pose_field)
    allow_activity = model.supports_value(range_fields.get("state"), "activity")
    trained_poses = profile.get("poses", {})
    if not allow_activity and any(
        example.get("state") == "activity" for examples in trained_poses.values() for example in examples
    ):
        warnings.append("Add 'activity' to the active schema's State options to use trained activity states.")
    unavailable = (
        [
            label for label, examples in trained_poses.items()
            if not model.supports_value(pose_definition, label)
            and not (allow_activity and any(example.get("state") == "activity" for example in examples))
        ]
        if pose_field != rules.RANGE_NAME_FIELD else []
    )
    if unavailable:
        labels = ", ".join(sorted(unavailable)[:5])
        warnings.append(f"Schema field '{pose_field}' does not accept these calibration labels: {labels}.")
    ranges = original["range_data"]
    overwritten = 0
    if settings["fill_mode"] == "overwrite":
        ranges, overwritten = model.clear_ranges(ranges, start, end)
    gaps = model.uncovered_spans(ranges, start, end)
    if not gaps and ranges and not preview_vlm:
        warnings.append(
            "Every frame in the analysis range already has an annotation range, so no new ranges were generated. "
            + (
                "The remaining ranges are locked."
                if settings["fill_mode"] == "overwrite" else
                "Fill mode is 'only fill gaps'. Choose 'overwrite' in Annotation Setup or delete the ranges to redo."
            )
        )
    file_fields = model.get_schema_fields(schema, "file_level")
    file_data = dict(original["file_data"])
    _apply_file_data(cmds, file_data, settings, file_fields, warnings)
    quality_field = file_fields.get("quality", {})
    needs_quality = (
        settings["auto_set_quality"] and quality_field.get("type") in ("integer", "enum", "string")
        and (start, end) == playback and (model.is_empty(file_data.get("quality")) or file_data.get("quality") == 0)
    )
    analysis = None
    mapping = None
    if gaps or needs_quality or needs_vlm:
        try:
            mapping = scene.resolve_skeleton(
                cmds, settings["skeleton_mode"], settings["skeleton_root"], settings["joint_map"],
                short_name_fallback=settings["short_name_fallback"],
            )
            if gaps or needs_vlm:
                analysis = _measure(cmds, mapping, settings, start, end)
        except ValueError as error:
            if gaps:
                return {
                    "outcome": "failed", "payload": original, "added_ranges": 0,
                    "changed": False, "validation_errors": [], "warnings": [*warnings, str(error)],
                    "quality": None, "vlm": {}, "profile": profile_summary, "overwritten_ranges": 0,
                }
            warnings.append(str(error))

    quality = None
    if mapping and needs_quality:
        try:
            quality = _apply_quality(cmds, mapping, playback, settings["quality_preset"], quality_field, file_data)
            warnings.extend(quality.get("warnings", []))
        except (RuntimeError, ValueError) as error:
            warnings.append(f"Motion Evaluator did not set Quality. {error}")

    generated = motion.generate_ranges(analysis, gaps, schema, profile, pose_field) if gaps else []
    payload = annotation_tracker_model.build_scene_payload(file_data, [*ranges, *generated])
    file_data = payload["file_data"]

    vlm_result = {}
    if preview_vlm:
        from gt.tools.annotation_tracker import auto_annotation_vlm

        preview = auto_annotation_vlm.preview_request(cmds, settings, schema, payload, start, end, analysis)
        warnings.extend(preview["warnings"])
        vlm_result = {"preview_folder": preview["folder"], "preview_images": preview["images"]}
    elif settings["vlm_mode"] != "off" and not dry_run:
        from gt.tools.annotation_tracker import auto_annotation_vlm

        vlm_result = auto_annotation_vlm.apply_vlm(cmds, context, settings, schema, payload, start, end, analysis)
        warnings.extend(vlm_result.get("warnings", []))
    elif settings["vlm_mode"] != "off":
        warnings.append("VLM requests are skipped in preview.")

    set_annotated = settings["auto_set_annotated"] and model.supports_value(file_fields.get("annotated"), True)
    if set_annotated:
        file_data["annotated"] = True
    errors = model.validate_annotation(schema, file_data, payload["range_data"], *playback)
    if errors and set_annotated:
        file_data["annotated"] = False
    changed = payload != original
    if not dry_run and changed:
        write_data = context.get("replace_annotation_data") or annotation_tracker_scene.set_scene_annotation_data
        if cmds.about(batch=True):
            payload = write_data(file_data, payload["range_data"])
        else:
            cmds.undoInfo(openChunk=True, chunkName="Auto Annotate")
            try:
                payload = write_data(file_data, payload["range_data"])
            finally:
                cmds.undoInfo(closeChunk=True)
    return {
        "outcome": "warning" if errors or warnings else "succeeded",
        "payload": payload,
        "changed": changed,
        "added_ranges": len(generated),
        "validation_errors": errors,
        "warnings": warnings,
        "quality": quality,
        "vlm": vlm_result,
        "profile": profile_summary,
        "overwritten_ranges": overwritten,
    }
