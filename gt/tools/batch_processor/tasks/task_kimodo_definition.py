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
from gt.tools.batch_processor.batch_processor_item_context import is_string_scene
from gt.tools.batch_processor.tasks.task_kimodo_base import (
    TaskKimodoBase, ClipSnapshotFileLock, report_message, write_record, read_json, fingerprint, resolve_path,
    resolve_motion_text, uses_runtime_variables, parse_motion_text,
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
            path_nodes="", path_frames="", path_samples=8, randomize_root_path=False,
            root_heading="none", root_heading_offset=0.0,
            model_fps=30, duration_mode="source",
            retime_constraints=False, constraint_mode="replace", variations=1, seed_policy="per_file",
            base_seed=12345, variation_ranges="{}", prompt_choices="", prompt_replacements=[],
            output_extension=".json", use_input_string=False, prompt_mode="table", prompt_text="",
        )
        return settings

    def base_definition(self, project, work_item=None, evaluate_queries=True):
        """Loads the selected template or task-local generation settings.

        Args:
            project (BatchProcessorModel): Owning project.
            work_item (WorkItem, optional): Current input used to resolve motion text.
            evaluate_queries (bool, optional): Whether scene queries can run in the current context.

        Returns:
            dict: Validated portable definition.
        """
        path = resolve_path(self.settings["template_path"], project, self)
        data = copy.deepcopy(read_json(path) if path else self.settings["definition"])
        mode = self.settings.get("prompt_mode", "table")
        if mode not in ("table", "text"):
            raise ValueError("Choose Table or Text for the motion description source.")
        if mode == "text":
            text = self.settings.get("prompt_text", "")
            if not isinstance(text, str):
                raise ValueError("Motion text must be a string of JSON pairs.")
            resolver = partial(resolve_motion_text, project=project,
                               task=self, work_item=work_item,
                               evaluate_queries=evaluate_queries and work_item is not None)
            expanded = resolver(text)
            definition = data.get("definition", data)
            if ((work_item is None or not evaluate_queries)
                    and uses_runtime_variables(expanded, project)):
                definition["prompts"] = [{"text": "Motion text is resolved per input.", "duration_seconds": 4}]
            else:
                definition["prompts"] = parse_motion_text(text, resolver)
        return kimodo.normalize_definition(data)

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Validates each resolved motion sequence before any scene is opened.

        Args:
            work_items (list): Incoming scene or string items.
            project (BatchProcessorModel): Owning project.
            step_output_dir (str): Resolved output directory.
            context (dict, optional): Tracker context.

        Returns:
            ValidationResult: Input, output, and motion-sequence diagnostics.
        """
        result = super().validate_work_items(work_items, project, step_output_dir, context)
        if self.settings.get("prompt_mode", "table") == "text":
            for item in work_items:
                try:
                    definition = self.base_definition(project, item, evaluate_queries=False)
                    vary_definition(definition, self.settings, item.current_path, 1)
                except (ValueError, TypeError, KeyError, OSError) as error:
                    self.add_area_error(result, "Generation", f"{item.current_path}: {error}")
        return result

    def validate(self, project):
        """Validates capture settings before opening source files.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Collected diagnostics.
        """
        result = super().validate(project)
        area = "Generation"
        try:
            definition = self.base_definition(project)
            if self.settings.get("prompt_mode", "table") == "text":
                expanded = resolve_motion_text(self.settings["prompt_text"], project, self, evaluate_queries=False)
                if uses_runtime_variables(expanded, project):
                    result.add_warning("[Generation] Motion text variables are checked after each input is prepared.")

            if float(self.settings["model_fps"]) <= 0:
                raise ValueError("Model FPS must be positive.")
            kimodo._positive_number(float(self.settings["model_fps"]), "model_fps")
            for key, allowed in (("duration_mode", ("source", "definition")),
                                 ("constraint_mode", ("replace", "append"))):
                if self.settings[key] not in allowed:
                    raise ValueError(f"Invalid {key}.")

            area = "Pose Capture"
            kimodo.parse_scene_frames(self.settings["pose_frames"])
            if self.settings["use_marker"] and not self.settings["marker_attribute"].strip():
                raise ValueError("Provide a marker attribute when marker capture is enabled.")
            if self.settings["range_mode"] == "custom":
                select_frames(float(self.settings["start_frame"]), float(self.settings["end_frame"]))
            for key, allowed in (("range_mode", ("playback", "animation", "custom")),
                                 ("marker_mode", ("evaluated", "keyed", "rising"))):
                if self.settings[key] not in allowed:
                    raise ValueError(f"Invalid {key}.")

            area = "Root Path"
            path_frames = kimodo.parse_scene_frames(self.settings["path_frames"])
            path_nodes = [value.strip() for value in self.settings["path_nodes"].split(",") if value.strip()]
            if path_nodes and path_frames and len(path_frames) < 2:
                raise ValueError("A root path needs at least two destination frames.")
            if not isinstance(self.settings.get("randomize_root_path", False), bool):
                raise ValueError("Random curve selection must be enabled or disabled.")
            if self.settings["randomize_root_path"] and len(path_nodes) < 2:
                raise ValueError("Random curve selection requires at least two curve transforms.")
            kimodo.validate_root_heading_mode(self.settings.get("root_heading", "none"),
                                              self.settings.get("root_heading_offset", 0.0))
            if path_nodes and (self.settings["randomize_root_path"] or len(path_nodes) == 1):
                path_samples = int(self.settings["path_samples"])
                if not 2 <= path_samples <= 7200:
                    raise ValueError("Curve path samples must be from 2 through 7200.")
            elif len(path_nodes) > 1 and path_frames and len(path_frames) != len(path_nodes):
                raise ValueError("Enter one Path frame per locator, or leave Path frames blank to space them evenly.")

            area = "Pose Capture"
            kimodo._positive_number(float(self.settings["sample_step"]), "sample_step")

            area = "Evaluation"
            kimodo._positive_number(float(self.settings["bone_offset_tolerance"]), "bone_offset_tolerance")
            if float(self.settings["bone_offset_tolerance"]) > 0.01:
                raise ValueError("Bone tolerance cannot exceed 0.01 meters.")

            area = "Variations"
            if not 1 <= int(self.settings["variations"]) <= 1000:
                raise ValueError("Choose 1 through 1000 definitions per source.")
            ranges = self.settings["variation_ranges"]
            ranges = json.loads(ranges) if isinstance(ranges, str) else ranges
            if "duration_seconds" in ranges and not self.settings["retime_constraints"]:
                raise ValueError("Duration variation requires Retime Constraints.")
            vary_definition(definition, self.settings, "validation", 1)
        except (ValueError, TypeError, KeyError, OSError) as error:
            self.add_area_error(result, area, error)
        if not isinstance(self.settings.get("purge_cache_on_success", True), bool):
            self.add_area_error(result, "Recovery", "Purge cache after success must be enabled or disabled.")
        return result

    def build_definitions(self, captured, definition, identity, report=None):
        """Applies timing, captured constraints, and deterministic variations.

        Args:
            captured (dict): Evaluated poses and source timing.
            definition (dict): Base generation request.
            identity (str): Stable source identity.
            report (callable, optional): Status reporter for selected curve paths.

        Returns:
            list: Fully resolved definitions.
        """
        definitions = []
        fps = float(self.settings["model_fps"])
        ranges = self.settings["variation_ranges"]
        ranges = json.loads(ranges) if isinstance(ranges, str) else ranges
        variations = [vary_definition(definition, self.settings, identity, variation)
                      for variation in range(1, int(self.settings["variations"]) + 1)]
        path_options = captured.get("path_options") or []
        if path_options:
            path_options = list(path_options)
            first_seed = variations[0]["parameters"]["seed"]
            path_rng_seed = int(fingerprint([
                first_seed, [option["name"] for option in path_options], "root-path-cycle",
            ])[:8], 16)
            random.Random(path_rng_seed).shuffle(path_options)
        for variation, resolved in enumerate(variations, 1):
            path = captured["path"]
            if path_options:
                selected_path = path_options[(variation - 1) % len(path_options)]
                path = selected_path["constraint"]
                if report:
                    report(f"Variation {variation} (seed {resolved['parameters']['seed']}) uses root path: "
                           f"{selected_path['name']}")
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
            if len(captured["poses"]) + len(constraints) + bool(path) > 256:
                packed = {"type": self.settings["pose_type"], "frame_indices": indices}
                for key in captured["poses"][0]:
                    if key not in ("type", "frame_indices"):
                        packed[key] = [value for pose in captured["poses"] for value in pose[key]]
                constraints.append(packed)
            else:
                for pose, index in zip(captured["poses"], indices):
                    constraints.append(dict(copy.deepcopy(pose), frame_indices=[index]))
            if path:
                path_indices, unused_count = kimodo.map_constraint_frames(
                    captured["path_frames"], captured["start"], captured["end"],
                    captured["source_fps"], fps, requested)
                constraints.append(dict(copy.deepcopy(path), frame_indices=path_indices))
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
        string_scene = is_string_scene(work_item)
        if not string_scene:
            cmds = batch_processor_maya.get_maya_cmds()
            cmds.file(work_item.current_path, open=True, force=True,
                      executeScriptNodes=False, prompt=False)
        definition = self.base_definition(project, work_item)
        if self.settings.get("use_input_string") and self.settings.get("prompt_mode", "table") == "table":
            value = work_item.metadata.get("input_string")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Use input string as prompt requires nonblank text from Input Strings or Input Pairs.")
            definition["prompts"][0]["text"] = value
        if string_scene:
            signature = fingerprint([self.settings, definition, work_item.metadata["input_string"]])
        else:
            stat = os.stat(work_item.current_path)
            signature = fingerprint([self.settings, definition, stat.st_size, stat.st_mtime_ns])
        with self.recovery_lock(work_item, step_output_dir, timeout_seconds=3600, context=context):
            try:
                with ClipSnapshotFileLock(record_path, timeout_seconds=3600):
                    record = read_json(record_path) if os.path.isfile(record_path) else {}
                    if record.get("signature") != signature:
                        identity = base.get_work_item_relative_path(work_item) or work_item.current_path
                        if string_scene:
                            definitions = [vary_definition(definition, self.settings, identity, variation)
                                           for variation in range(1, int(self.settings["variations"]) + 1)]
                            fps = float(self.settings["model_fps"])
                            count = sum(int(prompt["duration_seconds"] * fps) for prompt in definition["prompts"])
                            captured = {"frames": [], "start": 0, "end": count - 1, "source_fps": fps}
                            report("Building definitions from input text using prompt durations; no scene capture.")
                        else:
                            captured = capture_scene(self.settings, report)
                            definitions = self.build_definitions(captured, definition, identity, report=report)
                        record = {"signature": signature, "source": work_item.current_path, "definitions": definitions,
                                  "source_frames": captured["frames"], "source_start": captured["start"],
                                  "source_end": captured["end"], "source_fps": captured["source_fps"],
                                  "model_fps": float(self.settings["model_fps"]),
                                  "group_warning": captured.get("group_warning")}
                        write_record(record_path, record)
                    if record.get("group_warning"):
                        report(f"[WARNING] {record['group_warning']}")
                    paths = [self.output_path(work_item, step_output_dir, variation=index,
                                              seed=value["parameters"]["seed"], definition=value)
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
                        metadata = {"model_fps": record["model_fps"], "source_frames": record["source_frames"]}
                        if not string_scene:
                            metadata["source_scene"] = work_item.current_path
                        if not self.settings.get("purge_cache_on_success", True):
                            metadata["manifest"] = record_path
                        items.append(self.output_item(work_item, path, metadata))
                    if skipped == len(items):
                        raise base.TaskSkip("All Kimodo definitions already exist.", work_item=items)
            except base.TaskSkip:
                self.cleanup_recovery_cache(work_item, step_output_dir, cache, context)
                raise
            self.cleanup_recovery_cache(work_item, step_output_dir, cache, context)
            return items

    def check_source(self, item):
        """Accepts virtual scenes while preserving file checks for ordinary inputs.

        Args:
            item (WorkItem): Incoming scene or string work item.
        """
        if is_string_scene(item):
            if not self.writes_to_target_path():
                raise ValueError("Kimodo definitions require a separate target folder.")
            return
        super().check_source(item)


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
    apply_prompt_replacements(data["prompts"], settings, variation)
    data["id"] = uuid.uuid4().hex
    return kimodo.KimodoGenerationDefinition.from_dict(data).as_dict()


def apply_prompt_replacements(prompts, settings, variation):
    """Validates all replacement rows and applies the selected variation in one pass.

    Args:
        prompts (list): Detached prompt dictionaries to update.
        settings (dict): Task settings with numbered replacement rules.
        variation (int): One-based variation to apply.

    Raises:
        ValueError: If a row is invalid or repeats a search within one variation.
    """
    rules = settings.get("prompt_replacements", [])
    if not isinstance(rules, list):
        raise ValueError("Prompt replacements must be a list of Variation / Search / Replace rows.")
    replacements = {}
    seen = set()
    for index, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            raise ValueError(f"Prompt replacement row {index} must contain Variation, Search, and Replace.")
        number = rule.get("variation")
        search = rule.get("search")
        replacement = rule.get("replace")
        if type(number) is not int or not 1 <= number <= int(settings.get("variations", 1)):
            raise ValueError(f"Prompt replacement row {index}: Variation must be within Definitions per file.")
        if not isinstance(search, str) or not search.strip() or not isinstance(replacement, str):
            raise ValueError(f"Prompt replacement row {index}: enter Search text and a text replacement.")
        if (number, search) in seen:
            raise ValueError(f"Prompt replacement row {index}: duplicate Search text for variation {number}.")
        seen.add((number, search))
        if number == variation:
            replacements[search] = replacement
    if replacements:
        pattern = re.compile("|".join(re.escape(search) for search in sorted(replacements, key=len, reverse=True)))

        def replace_match(match):
            """Returns literal replacement text without applying subsequent rules.

            Args:
                match (re.Match): Matched source text.

            Returns:
                str: Replacement for this match.
            """
            return replacements[match.group(0)]

        for prompt in prompts:
            prompt["text"] = pattern.sub(replace_match, prompt["text"])


def resolve_group(requested):
    """Resolves an explicit skeleton or a unique metadata-bearing placement group.

    Args:
        requested (str): Group or descendant name; empty enables unique detection.

    Returns:
        str or None: Full path of a Kimodo placement group, or None when auto-detect finds none.
    """
    import maya.cmds as cmds

    if requested:
        matches = cmds.ls(requested, long=True) or []
    else:
        matches = cmds.ls("*.kimodoSkeleton", objectsOnly=True, long=True, recursive=True) or []
    if not matches and not requested:
        return None
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

    pose_source = settings.get("pose_source") or ""
    group = resolve_group(pose_source)
    group_warning = None
    if group is None:
        group_warning = ("No Kimodo skeleton was found for auto-detect. Pose constraints will not be "
                         "captured or used.")
    start, end = scene_range(settings)
    select_frames(start, end)
    step = float(settings["sample_step"])
    if not math.isfinite(step) or step <= 0 or (end - start) / step > 100000:
        raise ValueError("Choose a positive sample step producing at most 100000 samples.")
    previous_time = cmds.currentTime(query=True)
    markers = []
    try:
        attribute = settings["marker_attribute"].strip()
        if group and settings["use_marker"]:
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
                               settings["marker_mode"]) if group else []
        return {"group": group, "start": start, "end": end, "frames": frames,
                "source_fps": om.MTime(1, om.MTime.kSeconds).asUnits(om.MTime.uiUnit()),
                "group_warning": group_warning}
    finally:
        cmds.currentTime(previous_time, edit=True, update=True)


def capture_scene(settings, report):
    """Samples live evaluated poses and a curve, locator, or animated transform root trajectory.

    Args:
        settings (dict): Capture task settings.
        report (callable): Status reporter.

    Returns:
        dict: Capture metadata, poses, and optional root path choices with source times.
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
        path_options = []
        path_frames = []
        if settings["path_nodes"].strip():
            nodes = [value.strip() for value in settings["path_nodes"].split(",") if value.strip()]
            resolved_nodes = []
            curve_flags = []
            for requested_node in nodes:
                matches = cmds.ls(requested_node, long=True) or []
                if len(matches) != 1:
                    raise ValueError(f"Root path node is missing or ambiguous: {requested_node}")
                node = matches[0]
                resolved_nodes.append(node)
                shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
                curve_flags.append(any(cmds.nodeType(shape) == "nurbsCurve" for shape in shapes))
            randomize_path = settings.get("randomize_root_path", False)
            if randomize_path and (len(resolved_nodes) < 2 or not all(curve_flags)):
                raise ValueError("Random curve selection requires two or more NURBS curve transforms only.")
            if not randomize_path and len(resolved_nodes) > 1 and any(curve_flags):
                raise ValueError("Use one curve, or enable Random curve per variation for a curve list.")
            # One non-curve transform is an animated trajectory driver sampled over time.
            animated_node = not randomize_path and len(resolved_nodes) == 1 and not curve_flags[0]
            sample_curves = randomize_path or len(resolved_nodes) == 1
            path_frames = kimodo.parse_scene_frames(settings["path_frames"])
            if not path_frames:
                count = int(settings["path_samples"]) if sample_curves else len(resolved_nodes)
                if not 2 <= count <= 7200:
                    raise ValueError("Root path sample count must be from 2 through 7200.")
                path_frames = [resolved["start"] + index * (resolved["end"] - resolved["start"]) / (count - 1)
                               for index in range(count)]
            elif not sample_curves and len(path_frames) != len(resolved_nodes):
                raise ValueError("Enter one Path frame per locator, or leave Path frames blank to space them evenly.")
            if any(frame < resolved["start"] or frame > resolved["end"] for frame in path_frames):
                raise ValueError("Root path frames must be inside the capture range.")
            if len(path_frames) < 2:
                raise ValueError("A root path needs at least two destination frames.")
            cmds.currentTime(resolved["start"], edit=True, update=True)
            capture_path = partial(kimodo.capture_root_path, frame_indices=list(range(len(path_frames))),
                                   group=resolved["group"], heading_mode=settings.get("root_heading", "none"),
                                   heading_offset=float(settings.get("root_heading_offset", 0.0)))
            if randomize_path:
                for node in resolved_nodes:
                    path_options.append({"name": node, "constraint": capture_path([node])})
            elif animated_node:
                path = capture_path(resolved_nodes, sample_times=path_frames)
                report(f"Sampled animated root path from {resolved_nodes[0]} at {len(path_frames)} times.")
            else:
                path = capture_path(resolved_nodes)
        resolved.update(poses=poses, path=path, path_options=path_options, path_frames=path_frames)
        return resolved
    finally:
        cmds.currentTime(current_time, edit=True, update=True)
        cmds.select(selection, replace=True) if selection else cmds.select(clear=True)
