"""Captures portable Kimodo definitions from evaluated Maya animation."""

import copy
import json
import os
import math
import re
import random
import secrets
import uuid
from functools import partial
from gt.utils import kimodo
from gt.ui import resource_library as resources
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor.tasks.task_kimodo_base import (
    TaskKimodoBase, ClipSnapshotFileLock, report_message, write_record, read_json, fingerprint, resolve_path,
)


class TaskKimodoDefinition(TaskKimodoBase):
    """Creates one or more self-contained definitions for each source scene."""

    task_type = constants.TaskType.KIMODO_DEFINITION
    default_display_name = "Kimodo Definition"
    icon = resources.Icon.batch_task_kimodo_definition
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_kimodo_definitions"
    extensions = (".ma", ".mb")

    def get_default_settings(self):
        """Returns capture, generation, and reproducible variation defaults.

        Returns:
            dict: Serializable task parameters.
        """
        settings = super().get_default_settings()
        settings.update(
            definition=kimodo.KimodoGenerationDefinition("A person moves naturally between the poses.").as_dict(),
            template_path="", pose_source="", range_mode="playback", start_frame=1, end_frame=120,
            capture_first=True, capture_last=True, pose_frames="", use_marker=False,
            marker_attribute="kimodo_pose:motion.isConstraintPose", marker_value=1, marker_mode="evaluated",
            sample_step=1, pose_type="fullbody", sequential_evaluation=True, bone_offset_tolerance=0.001,
            path_nodes="", path_frames="", path_samples=8, model_fps=30, duration_mode="source",
            retime_constraints=False, constraint_mode="replace", variations=1, seed_policy="per_file",
            base_seed=12345, variation_ranges="{}", prompt_choices="", output_extension=".json",
        )
        return settings

    def base_definition(self, project):
        """Loads the selected template or task-local generation settings.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            dict: Validated portable definition.
        """
        path = resolve_path(self.settings["template_path"], project, self)
        return kimodo.normalize_definition(read_json(path) if path else self.settings["definition"])

    def validate(self, project):
        """Validates capture settings before opening source files.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Collected diagnostics.
        """
        result = super().validate(project)
        try:
            definition = self.base_definition(project)
            kimodo.parse_scene_frames(self.settings["pose_frames"])
            kimodo.parse_scene_frames(self.settings["path_frames"])
            if not 1 <= int(self.settings["variations"]) <= 1000:
                raise ValueError("Choose 1 through 1000 definitions per source.")
            if float(self.settings["model_fps"]) <= 0:
                raise ValueError("Model FPS must be positive.")
            for key in ("model_fps", "sample_step", "bone_offset_tolerance"):
                kimodo._positive_number(float(self.settings[key]), key)
            if float(self.settings["bone_offset_tolerance"]) > 0.01:
                raise ValueError("Bone tolerance cannot exceed 0.01 meters.")
            if self.settings["use_marker"] and not self.settings["marker_attribute"].strip():
                raise ValueError("Provide a marker attribute when marker capture is enabled.")
            if self.settings["range_mode"] == "custom":
                select_frames(float(self.settings["start_frame"]), float(self.settings["end_frame"]))
            for key, allowed in (("range_mode", ("playback", "animation", "custom")),
                                 ("duration_mode", ("source", "definition")),
                                 ("constraint_mode", ("replace", "append")),
                                 ("marker_mode", ("evaluated", "keyed", "rising"))):
                if self.settings[key] not in allowed:
                    raise ValueError(f"Invalid {key}.")
            ranges = self.settings["variation_ranges"]
            ranges = json.loads(ranges) if isinstance(ranges, str) else ranges
            if "duration_seconds" in ranges and not self.settings["retime_constraints"]:
                raise ValueError("Duration variation requires Retime Constraints.")
            vary_definition(definition, self.settings, "validation", 1)
        except (ValueError, TypeError, KeyError, OSError) as error:
            result.add_error(str(error))
        return result

    def build_definitions(self, captured, definition, identity):
        """Applies timing, captured constraints, and deterministic variations.

        Args:
            captured (dict): Evaluated poses and source timing.
            definition (dict): Base generation request.
            identity (str): Stable source identity.

        Returns:
            list: Fully resolved definitions.
        """
        definitions = []
        fps = float(self.settings["model_fps"])
        ranges = self.settings["variation_ranges"]
        ranges = json.loads(ranges) if isinstance(ranges, str) else ranges
        for variation in range(1, int(self.settings["variations"]) + 1):
            resolved = vary_definition(definition, self.settings, identity, variation)
            original_count = sum(int(prompt["duration_seconds"] * fps) for prompt in definition["prompts"])
            requested = None
            if self.settings["duration_mode"] == "definition" or "duration_seconds" in ranges:
                requested = sum(int(prompt["duration_seconds"] * fps) for prompt in resolved["prompts"])
                if not self.settings["retime_constraints"]:
                    natural = kimodo.map_constraint_frames([], captured["start"], captured["end"],
                                              captured["source_fps"], fps)[1]
                    if requested != natural:
                        raise ValueError("Definition duration differs from source; enable Retime Constraints.")
            indices, count = kimodo.map_constraint_frames(captured["frames"], captured["start"], captured["end"],
                                             captured["source_fps"], fps, requested)
            kimodo.set_definition_frame_count(resolved, count, fps)
            constraints = [] if self.settings["constraint_mode"] == "replace" else resolved["constraints"]
            if constraints and original_count != count:
                if not self.settings["retime_constraints"]:
                    raise ValueError("Retained template constraints need Retime Constraints for the new duration.")
                for constraint in constraints:
                    constraint["frame_indices"], unused_count = kimodo.map_constraint_frames(
                        constraint["frame_indices"], 0, original_count - 1, fps, fps, count)
            if len(captured["poses"]) + len(constraints) + bool(captured["path"]) > 256:
                packed = {"type": self.settings["pose_type"], "frame_indices": indices}
                for key in captured["poses"][0]:
                    if key not in ("type", "frame_indices"):
                        packed[key] = [value for pose in captured["poses"] for value in pose[key]]
                constraints.append(packed)
            else:
                for pose, index in zip(captured["poses"], indices):
                    constraints.append(dict(copy.deepcopy(pose), frame_indices=[index]))
            if captured["path"]:
                path_indices, unused_count = kimodo.map_constraint_frames(
                    captured["path_frames"], captured["start"], captured["end"], captured["source_fps"], fps, requested)
                constraints.append(dict(copy.deepcopy(captured["path"]), frame_indices=path_indices))
            resolved["constraints"] = constraints
            kimodo.validate_constraints(constraints, count)
            definitions.append(kimodo.KimodoGenerationDefinition.from_dict(resolved).as_dict())
        return definitions

    def execute(self, work_item, project, step_output_dir, context=None):
        """Captures an input scene and returns its portable definition work items.

        Args:
            work_item (WorkItem): Source Maya file.
            project (BatchProcessorModel): Owning project.
            step_output_dir (str): Output root.
            context (dict, optional): Tracker context.

        Returns:
            list: Definition work items.
        """
        self.check_source(work_item)
        validation = self.validate(project)
        if validation.errors:
            raise ValueError("; ".join(validation.errors))
        report = partial(report_message, context)
        cache = self.recovery_directory(work_item, step_output_dir)
        record_path = os.path.join(cache, "capture.json")
        definition = self.base_definition(project)
        stat = os.stat(work_item.current_path)
        signature = fingerprint([self.settings, definition, stat.st_size, stat.st_mtime_ns])
        with ClipSnapshotFileLock(record_path, timeout_seconds=3600):
            record = read_json(record_path) if os.path.isfile(record_path) else {}
            if record.get("signature") != signature:
                cmds = batch_processor_maya.get_maya_cmds()
                cmds.file(work_item.current_path, open=True, force=True, executeScriptNodes=False, prompt=False)
                captured = capture_scene(self.settings, report)
                identity = base.get_work_item_relative_path(work_item) or work_item.current_path
                definitions = self.build_definitions(captured, definition, identity)
                record = {"signature": signature, "source": work_item.current_path, "definitions": definitions,
                          "source_frames": captured["frames"], "source_start": captured["start"],
                          "source_end": captured["end"], "source_fps": captured["source_fps"],
                          "model_fps": float(self.settings["model_fps"])}
                write_record(record_path, record)
            paths = [self.output_path(work_item, step_output_dir, variation=index,
                                      seed=value["parameters"]["seed"])
                     for index, value in enumerate(record["definitions"], 1)]
            if len({os.path.normcase(path) for path in paths}) != len(paths):
                raise ValueError("Definition output names collide.")
            self.reserve_outputs(work_item, paths, step_output_dir)
            items = []
            skipped = 0
            for path, resolved in zip(paths, record["definitions"]):
                if os.path.exists(path) and not self.settings["overwrite"]:
                    kimodo.normalize_definition(read_json(path))
                    report(f"Skipped existing definition: {path}")
                    skipped += 1
                else:
                    resolved["name"] = os.path.splitext(os.path.basename(path))[0]
                    write_record(path, resolved)
                    report(f"Saved definition: {path}")
                items.append(self.output_item(work_item, path, dict(
                    manifest=record_path, model_fps=record["model_fps"], source_frames=record["source_frames"])))
            if skipped == len(items):
                raise base.TaskSkip("All Kimodo definitions already exist.", work_item=items)
            return items


def select_frames(start, end, explicit=None, first=True, last=True, markers=None, mode="evaluated"):
    """Combines endpoints, explicit frames, and evaluated or keyed marker samples.

    Args:
        start (float): Inclusive source start.
        end (float): Inclusive source end.
        explicit (list, optional): Explicit frame values.
        first (bool): Include start.
        last (bool): Include end.
        markers (list, optional): Ordered (frame, active) samples, including inactive samples.
        mode (str): evaluated, keyed, or rising.

    Returns:
        list: Sorted deduplicated source frames.
    """
    if not math.isfinite(start) or not math.isfinite(end) or end <= start:
        raise ValueError("Capture range must contain at least two distinct times.")
    if mode not in ("evaluated", "keyed", "rising"):
        raise ValueError("Unknown marker mode.")
    frames = set(explicit or [])
    if any(frame < start or frame > end for frame in frames):
        raise ValueError("An explicit pose frame is outside the capture range.")
    if first:
        frames.add(start)
    if last:
        frames.add(end)
    previous = False
    for frame, active in sorted(markers or []):
        if start <= frame <= end:
            if active and (mode != "rising" or not previous):
                frames.add(frame)
            previous = bool(active)
    return sorted(frames)


def vary_definition(definition, settings, identity, variation):
    """Resolves seeds and opted-in parameter variations before capture.

    Args:
        definition (dict): Base definition.
        settings (dict): Task settings.
        identity (str): Stable source-relative identity.
        variation (int): One-based variation index.

    Returns:
        dict: Independent resolved definition.
    """
    data = copy.deepcopy(definition)
    policy = settings["seed_policy"]
    base_seed = int(settings["base_seed"])
    if float(settings["base_seed"]) != base_seed or not 0 <= base_seed < 2 ** 32:
        raise ValueError("Base seed must be an unsigned 32-bit integer.")
    derived = int(fingerprint([base_seed, identity, variation])[:8], 16)
    if policy not in ("fixed", "per_file", "random"):
        raise ValueError("Unknown seed policy.")
    seed = secrets.randbits(32) if policy == "random" else base_seed if policy == "fixed" else derived
    data["parameters"]["seed"] = seed
    rng = random.Random(seed if policy == "random" else derived)
    ranges = settings.get("variation_ranges") or {}
    if isinstance(ranges, str):
        ranges = json.loads(ranges)
    allowed = {"diffusion_steps", "heading", "guidance_text", "guidance_constraints", "duration_seconds"}
    if not isinstance(ranges, dict) or set(ranges) - allowed:
        raise ValueError(f"Variation ranges support only: {', '.join(sorted(allowed))}.")
    for key, bounds in ranges.items():
        if (not isinstance(bounds, list) or len(bounds) != 2
                or any(type(value) not in (int, float) or not math.isfinite(value) for value in bounds)
                or bounds[0] > bounds[1]):
            raise ValueError(f"Invalid min/max range for {key}.")
        value = rng.uniform(*bounds)
        if key == "diffusion_steps":
            data["parameters"][key] = rng.randint(math.ceil(bounds[0]), math.floor(bounds[1]))
        elif key.startswith("guidance_"):
            data["parameters"]["guidance"][0 if key == "guidance_text" else 1] = value
        elif key == "duration_seconds":
            total = sum(prompt["duration_seconds"] for prompt in data["prompts"])
            for prompt in data["prompts"]:
                prompt["duration_seconds"] *= value / total
        else:
            data["parameters"][key] = value
    choices = [line.strip() for line in settings.get("prompt_choices", "").splitlines() if line.strip()]
    if choices:
        data["prompts"][0]["text"] = rng.choice(choices)
    data["id"] = uuid.uuid4().hex
    return kimodo.KimodoGenerationDefinition.from_dict(data).as_dict()


def resolve_group(requested):
    """Resolves an explicit skeleton or a unique metadata-bearing placement group.

    Args:
        requested (str): Group or descendant name; empty enables unique detection.

    Returns:
        str: Full path of a Kimodo placement group.
    """
    import maya.cmds as cmds

    if requested:
        matches = cmds.ls(requested, long=True) or []
    else:
        matches = cmds.ls("*.kimodoSkeleton", objectsOnly=True, long=True, recursive=True) or []
    if len(matches) != 1:
        raise ValueError(f"Expected one Kimodo skeleton; found {len(matches)} for '{requested or 'auto-detect'}'.")
    return kimodo.find_pose_group(matches[0])


def scene_range(settings):
    """Resolves the selected source range, including saved ASCII playback settings.

    Args:
        settings (dict): Capture task settings.

    Returns:
        tuple: Inclusive start/end times.
    """
    import maya.cmds as cmds

    mode = settings["range_mode"]
    if mode == "custom":
        return float(settings["start_frame"]), float(settings["end_frame"])
    flags = ("minTime", "maxTime") if mode == "playback" else ("animationStartTime", "animationEndTime")
    # Maya saves playbackOptions in a configuration script node. Read only that
    # literal command; never execute scene scripts to recover timeline metadata.
    for node in cmds.ls(type="script") or []:
        body = cmds.getAttr(f"{node}.before") or ""
        if re.fullmatch(r"\s*playbackOptions\s+(?:-[a-zA-Z]+\s+[-+\d.eE]+\s*)+;?\s*", body):
            values = dict(re.findall(r"-([a-zA-Z]+)\s+([-+\d.eE]+)", body))
            keys = ("min", "max") if mode == "playback" else ("ast", "aet")
            if all(key in values for key in keys):
                return tuple(float(values[key]) for key in keys)
    return tuple(cmds.playbackOptions(query=True, **{flag: True}) for flag in flags)


def resolve_frames(settings):
    """Evaluates marker attributes on the timeline, restoring time and selection.

    Args:
        settings (dict): Range, frame expression, and marker options.

    Returns:
        dict: Resolved group, range, source FPS, and selected source frames.
    """
    import maya.cmds as cmds
    import maya.api.OpenMaya as om

    group = resolve_group(settings["pose_source"])
    start, end = scene_range(settings)
    select_frames(start, end)
    step = float(settings["sample_step"])
    if not math.isfinite(step) or step <= 0 or (end - start) / step > 100000:
        raise ValueError("Choose a positive sample step producing at most 100000 samples.")
    previous_time = cmds.currentTime(query=True)
    markers = []
    try:
        attribute = settings["marker_attribute"].strip()
        if settings["use_marker"]:
            if not cmds.objExists(attribute):
                raise ValueError(f"Pose marker attribute does not exist: {attribute}")
            if settings["marker_mode"] == "keyed":
                times = sorted(set(cmds.keyframe(attribute, query=True, timeChange=True) or []))
                times = [frame for frame in times if start <= frame <= end]
            else:
                times = [start + index * step for index in range(int((end - start) / step) + 1)]
                if times[-1] != end:
                    times.append(end)
            for frame in times:
                cmds.currentTime(frame, edit=True, update=True)
                value = cmds.getAttr(attribute)
                if not isinstance(value, (int, float, bool)):
                    raise ValueError("Pose marker must evaluate to a scalar numeric or boolean value.")
                markers.append((frame, abs(float(value) - float(settings["marker_value"])) <= 0.000001))
        frames = select_frames(start, end, kimodo.parse_scene_frames(settings["pose_frames"]),
                                    settings["capture_first"], settings["capture_last"], markers,
                                    settings["marker_mode"])
        return {"group": group, "start": start, "end": end, "frames": frames,
                "source_fps": om.MTime(1, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())}
    finally:
        cmds.currentTime(previous_time, edit=True, update=True)


def capture_scene(settings, report):
    """Samples live evaluated poses and a static curve/locator root trajectory.

    Args:
        settings (dict): Capture task settings.
        report (callable): Status reporter.

    Returns:
        dict: Capture metadata, poses, and optional root path with source times.
    """
    import maya.cmds as cmds

    resolved = resolve_frames(settings)
    report(f"Capture frames: {resolved['frames']} ({resolved['source_fps']:g} fps)")
    if len(resolved["frames"]) > 64:
        report("[WARNING] Dense pose capture may leave little freedom for inbetween generation.")
    current_time = cmds.currentTime(query=True)
    selection = cmds.ls(selection=True, long=True) or []
    poses = []
    try:
        previous = resolved["start"]
        for index, frame in enumerate(resolved["frames"]):
            if settings["sequential_evaluation"]:
                while previous < frame:
                    cmds.currentTime(previous, edit=True, update=True)
                    previous += 1
            cmds.currentTime(frame, edit=True, update=True)
            poses.append(kimodo.capture_pose(resolved["group"], index, settings["pose_type"],
                                              float(settings["bone_offset_tolerance"])))
            previous = frame
        path = None
        path_frames = []
        if settings["path_nodes"].strip():
            nodes = [value.strip() for value in settings["path_nodes"].split(",") if value.strip()]
            for node in nodes:
                if len(cmds.ls(node, long=True) or []) != 1:
                    raise ValueError(f"Root path node is missing or ambiguous: {node}")
            path_frames = kimodo.parse_scene_frames(settings["path_frames"])
            if not path_frames:
                count = int(settings["path_samples"])
                if not 2 <= count <= 7200:
                    raise ValueError("Root path sample count must be from 2 through 7200.")
                path_frames = [resolved["start"] + index * (resolved["end"] - resolved["start"]) / (count - 1)
                               for index in range(count)]
            if any(frame < resolved["start"] or frame > resolved["end"] for frame in path_frames):
                raise ValueError("Root path frames must be inside the capture range.")
            cmds.currentTime(resolved["start"], edit=True, update=True)
            path = kimodo.capture_root_path(nodes, list(range(len(path_frames))), resolved["group"])
        resolved.update(poses=poses, path=path, path_frames=path_frames)
        return resolved
    finally:
        cmds.currentTime(current_time, edit=True, update=True)
        cmds.select(selection, replace=True) if selection else cmds.select(clear=True)
