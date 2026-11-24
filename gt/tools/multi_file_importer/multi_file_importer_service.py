"""
Multi-File Importer Service

Runs one import session inside Maya: prepares the scene, imports files one at a time (so the
controller can update progress and honour Cancel between files), places them, and finishes
with the timeline, review overrides and the optional post-import script.

Maya is imported inside methods so this module can be imported (and inspected) outside Maya.
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_controls as controls
from gt.tools.multi_file_importer import multi_file_importer_layout as layout
from gt.tools.multi_file_importer import multi_file_importer_scene as scene_settings
import gt.core.timeline as core_timeline
from gt.tools.multi_file_importer import multi_file_importer_formats as formats
import gt.core.str as core_str
import logging
import os
import time
import traceback

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PER_FILE_SCRIPT_NAME = "<multi_file_importer_per_file_script>"
POST_SCRIPT_NAME = "<multi_file_importer_post_script>"


def build_record(job):
    """Builds the result dictionary of one file. Scripts receive it as "record".

    Args:
        job (dict): Import job with "path", "index", "namespace" and "group_name".

    Returns:
        dict: Record with a pending status.
    """
    return {
        "index": job["index"],
        "path": job["path"],
        "name": os.path.splitext(os.path.basename(job["path"]))[0],
        "format": "",
        "status": constants.STATUS_PENDING,
        "message": "",
        "namespace": "",
        "reference_node": "",
        "nodes": [],
        "root_nodes": [],
        "group": "",
        "time_range": None,
        "stored_range": None,
        "anim_curve_ids": [],
        "explicit_range": None,
        "range_fps": 0.0,
        "file_info": {},
        "elapsed_seconds": 0.0,
    }


def run_script(code, context, script_name):
    """Runs user Python code with the given variables.

    Args:
        code (str): Python source.
        context (dict): Variables available to the script.
        script_name (str): Name shown in tracebacks.
    """
    import maya.cmds as cmds

    script_globals = {"__name__": "__main__", "cmds": cmds}
    script_globals.update(context)
    exec(compile(code, script_name, "exec"), script_globals)


class ImportSession:
    """Imports a list of files into the current scene."""

    def __init__(self, settings, format_settings, jobs):
        """Initializes the session.

        Args:
            settings (dict): Tool settings (see constants.DEFAULT_SETTINGS).
            format_settings (dict): Format key to format settings.
            jobs (list): Import jobs in order. Each job is a dict with "path", "index" (one-based),
                "namespace" (preferred, may be empty) and "group_name".
        """
        self.settings = dict(settings)
        self.format_settings = dict(format_settings or {})
        self.jobs = list(jobs)
        self.records = []
        self.messages = []
        self.top_group = ""
        self.used_namespaces = set()
        self.offsets = []
        self.deferred_placement = False
        self.original_state = {}
        self.scene_targets = {}
        self.control_node = ""

    # ------------------------------------------------------------------ start
    def start(self):
        """Prepares the scene before the first file is imported.

        No undo chunk is opened: Maya's file import flushes the undo queue, so the import
        could not be undone as one step anyway.

        Returns:
            list: Messages describing scene changes and warnings.
        """
        import maya.cmds as cmds
        import gt.core.namespace as core_nspace

        self.original_state = scene_settings.capture_scene_state()
        targets, warnings = scene_settings.resolve_scene_targets(self.settings, [job["path"] for job in self.jobs])
        self.scene_targets = targets
        self.messages.extend(warnings)
        changes = scene_settings.apply_scene_targets(targets)
        if changes:
            self.messages.append(f"Scene set to {', '.join(changes)}.")
        self.used_namespaces = core_nspace.get_all_namespaces()
        if self.settings["parent_all"]:
            group_name = core_str.sanitize_maya_name(self.settings["parent_all_name"], "imported_files_grp")
            self.top_group = (cmds.ls(cmds.group(empty=True, world=True, name=group_name), long=True) or [""])[0]
        self.deferred_placement = self.settings["create_layout_controls"] or (
            self.settings["offset_mode"] != constants.OFFSET_NONE and self.settings["auto_spacing"]
        )
        self.control_node = ""
        if not self.deferred_placement:
            self.offsets = layout.build_layout_offsets(len(self.jobs), self.settings)
        return list(self.messages)

    # ------------------------------------------------------------------ per file
    def import_job(self, job):
        """Imports one file, applies grouping and placement, then runs the per-file script.

        Args:
            job (dict): Import job (see __init__).

        Returns:
            dict: Record describing the result.

        Raises:
            RuntimeError: When the file fails and the failure policy is "Stop Import".
        """
        record = build_record(job)
        self.records.append(record)
        start_time = time.time()
        file_format = formats.get_format_for_path(job["path"])
        if not os.path.isfile(job["path"]):
            return self._finish_record(record, constants.STATUS_SKIPPED, "File not found.", start_time)
        if not file_format:
            return self._finish_record(record, constants.STATUS_SKIPPED, "Unsupported format.", start_time)
        record["format"] = file_format.key
        try:
            self._load_file(file_format, job, record)
            self._organize_record(job, record)
        except Exception as exception:
            logger.warning(f'Failed importing "{job["path"]}": {exception}')
            logger.debug(traceback.format_exc())
            self._finish_record(record, constants.STATUS_FAILED, str(exception), start_time)
            if self.settings["on_failure"] == constants.FAILURE_STOP:
                raise RuntimeError(f'Import stopped. "{record["name"]}" failed: {exception}')
            return record
        status, message = constants.STATUS_IMPORTED, ""
        script_error = self._run_per_file_script(record)
        if script_error:
            status, message = constants.STATUS_WARNING, f"Per-file script failed: {script_error}"
        return self._finish_record(record, status, message, start_time)

    def _load_file(self, file_format, job, record):
        """Loads a file with its format and fills the record.

        Args:
            file_format (FormatBase): Format of the file.
            job (dict): Import job.
            record (dict): Record updated in place.
        """
        import gt.core.scene as core_scene
        import gt.core.uuid as core_uuid

        reference = self.settings["load_mode"] == constants.LOAD_MODE_REFERENCE and file_format.supports_reference
        namespace = job.get("namespace") or ""
        if reference and not namespace:
            namespace = core_str.sanitize_maya_name(record["name"], "file")
        if namespace:
            namespace = core_str.build_unique_name(namespace, self.used_namespaces)
        file_format.load_plugins()
        result = file_format.load(
            job["path"],
            namespace=namespace,
            reference=reference,
            settings=self.format_settings.get(file_format.key),
        )
        record["namespace"] = namespace
        record["reference_node"] = result.reference_node
        record["nodes"] = list(result.nodes)
        record["file_info"] = formats.read_file_info(job["path"])
        anim_curves = core_timeline.get_time_anim_curves(result.nodes)
        record["anim_curve_ids"] = core_uuid.get_uuids(anim_curves)
        record["explicit_range"] = result.time_range
        record["range_fps"] = core_scene.get_frame_rate()
        record["time_range"] = result.time_range or core_timeline.get_key_range(anim_curves)
        record["stored_range"] = get_stored_range(record["file_info"], record["range_fps"])
        if self.settings["load_mode"] == constants.LOAD_MODE_REFERENCE and not file_format.supports_reference:
            self.messages.append(f'{file_format.label} files cannot be referenced; "{record["name"]}" was imported.')
        record["root_nodes"] = self._get_root_nodes(result)

    @staticmethod
    def _get_root_nodes(result):
        """Gets the top-level transforms created by an import.

        Args:
            result (ImportResult): Import result.

        Returns:
            list: Long names of top-level transforms.
        """
        import gt.core.hierarchy as core_hrchy

        root_nodes = list(result.root_nodes) or core_hrchy.get_root_transforms(result.nodes)
        return [node for node in root_nodes if "|" not in node.lstrip("|")]

    def _organize_record(self, job, record):
        """Groups and places one file's nodes.

        Args:
            job (dict): Import job.
            record (dict): Record updated in place.
        """
        import maya.cmds as cmds

        if not record["root_nodes"]:
            return
        if self.settings["group_per_file"]:
            group_kwargs = {"empty": True, "name": job["group_name"]}
            if self.top_group:
                group_kwargs["parent"] = self.top_group
            else:
                group_kwargs["world"] = True
            record["group"] = (cmds.ls(cmds.group(**group_kwargs), long=True) or [""])[0]
            record["root_nodes"] = cmds.ls(cmds.parent(record["root_nodes"], record["group"]), long=True) or []
        elif self.top_group:
            record["root_nodes"] = cmds.ls(cmds.parent(record["root_nodes"], self.top_group), long=True) or []
        if not self.deferred_placement and self.offsets:
            self.apply_offset(record, self.offsets[job["index"] - 1])

    def protect_skinned_geometry(self, record):
        """Keeps skinned geometry from being moved twice when its file is offset (when the setting is on).

        Args:
            record (dict): Import record.
        """
        if not self.settings["protect_skinned_meshes"] or record.get("protected_nodes") is not None:
            return
        self.messages.extend(controls.protect_skinned_geometry(record))
        if record["protected_nodes"]:
            logger.info(f'"{record["name"]}": kept {len(record["protected_nodes"])} skinned node(s) in place '
                        "(they follow their joints).")

    def apply_offset(self, record, offset):
        """Moves a file's content by an offset, keeping skinned geometry from moving twice.

        Args:
            record (dict): Import record.
            offset (list): Offset [x, y, z].
        """
        if not any(abs(value) > 0 for value in offset):
            return
        self.protect_skinned_geometry(record)
        self.messages.extend(controls.apply_static_offset(record, offset))

    def _run_per_file_script(self, record):
        """Runs the per-file script when enabled.

        Args:
            record (dict): Record of the file that was just imported.

        Returns:
            str: Error message, or an empty string when the script succeeded or is disabled.
        """
        code = self.settings["per_file_script"]
        if not self.settings["per_file_script_enabled"] or not code.strip():
            return ""
        context = {
            "file_path": record["path"],
            "file_index": record["index"],
            "total_files": len(self.jobs),
            "record": record,
            "nodes": list(record["nodes"]),
            "root_nodes": list(record["root_nodes"]),
            "group": record["group"],
            "namespace": record["namespace"],
            "reference_node": record["reference_node"],
            "records": list(self.records),
            "settings": dict(self.settings),
        }
        try:
            run_script(code, context, PER_FILE_SCRIPT_NAME)
        except Exception as exception:
            logger.warning(f'Per-file script failed on "{record["path"]}":\n{traceback.format_exc()}')
            return str(exception)
        return ""

    @staticmethod
    def _finish_record(record, status, message, start_time):
        """Stores the status and elapsed time of a record.

        Args:
            record (dict): Record updated in place.
            status (str): Final status.
            message (str): Detail message.
            start_time (float): time.time() when the file started.

        Returns:
            dict: The record.
        """
        record["status"] = status
        record["message"] = message
        record["elapsed_seconds"] = round(time.time() - start_time, 3)
        logger.info(f'[{record["index"]}] {status}: {record["path"]} ({record["elapsed_seconds"]}s)'
                    f'{f" - {message}" if message else ""}')
        return record

    # ------------------------------------------------------------------ finish
    def get_imported_records(self):
        """Gets the records of files that were imported.

        Returns:
            list: Imported (or imported with warnings) records.
        """
        return [
            record
            for record in self.records
            if record["status"] in (constants.STATUS_IMPORTED, constants.STATUS_WARNING)
        ]

    def finish(self, cancelled=False):
        """Finishes the session: deferred placement, timeline, review overrides and post script.

        Args:
            cancelled (bool, optional): Whether the user cancelled before every file was imported.

        Returns:
            dict: Summary with "time_range" and "messages".
        """
        imported_records = self.get_imported_records()
        if self.deferred_placement:
            self._apply_deferred_placement(imported_records)
        if self.settings["reapply_scene_settings"]:
            self._reapply_scene_settings()
        self._refresh_record_ranges(imported_records)
        time_range = scene_settings.resolve_timeline_range(self.settings, self.records)
        scene_settings.apply_timeline_range(time_range)
        if imported_records:
            frame_nodes = [self.top_group] if self.top_group else self._get_placed_nodes(imported_records)
            self.messages.extend(scene_settings.apply_review_overrides(self.settings, frame_nodes))
        self._run_post_script(time_range, cancelled)
        return {"time_range": time_range, "messages": list(self.messages)}

    def _reapply_scene_settings(self):
        """Applies the frame rate, unit and up axis again, undoing changes made by importers."""
        expected_state = scene_settings.build_final_targets(self.scene_targets, self.original_state)
        changed_labels = scene_settings.find_changed_values(expected_state, scene_settings.capture_scene_state())
        if not changed_labels:
            return
        scene_settings.apply_scene_targets(expected_state)
        self.messages.append(f"{', '.join(changed_labels)} changed while importing and was set back.")

    @staticmethod
    def _refresh_record_ranges(records):
        """Recomputes each file's ranges in the final scene frame rate.

        Changing the frame rate keeps keys at the same real-world time, so ranges measured during the
        import are refreshed from the file's animation curves (or converted when there are none).

        Args:
            records (list): Imported records, updated in place.
        """
        import gt.core.scene as core_scene
        import gt.core.uuid as core_uuid

        scene_fps = core_scene.get_frame_rate()
        for record in records:
            anim_curves = core_uuid.get_objects_from_uuids(record["anim_curve_ids"])
            key_range = core_timeline.get_key_range(anim_curves) if anim_curves else None
            explicit_range = scene_settings.scale_time_range(record["explicit_range"], record["range_fps"], scene_fps)
            record["time_range"] = explicit_range or key_range
            record["stored_range"] = get_stored_range(record["file_info"], scene_fps)

    @staticmethod
    def _get_placed_nodes(records):
        """Gets the nodes that represent each imported file in the scene.

        Args:
            records (list): Imported records.

        Returns:
            list: Groups, or root nodes for files without a group.
        """
        placed_nodes = []
        for record in records:
            placed_nodes.extend([record["group"]] if record["group"] else record["root_nodes"])
        return placed_nodes

    def _apply_deferred_placement(self, records):
        """Places files after every import: auto spacing from the largest bounding box, and layout controls.

        Args:
            records (list): Imported records.
        """
        max_size = None
        if self.settings["auto_spacing"]:
            bounding_boxes = [get_bounding_box(self._get_placed_nodes([record])) for record in records]
            max_size = layout.get_max_size(bounding_boxes)
        vector_a, vector_b = layout.build_layout_vectors(self.settings, max_size=max_size)
        coefficients = layout.build_layout_coefficients(len(records), self.settings)
        if not self.settings["create_layout_controls"]:
            for record, record_coefficients in zip(records, coefficients):
                self.apply_offset(record, layout.combine_offset(record_coefficients, vector_a, vector_b))
            return
        for record in records:
            self.protect_skinned_geometry(record)
        self.control_node, messages = controls.build_layout_controls(
            records, self.settings, vector_a, vector_b, coefficients, top_group=self.top_group
        )
        self.messages.extend(messages)
        self.messages.append(f'Layout controls created on "{self.control_node.split("|")[-1]}".')

    def _run_post_script(self, time_range, cancelled):
        """Runs the post-import script when enabled.

        Args:
            time_range (tuple): Applied timeline range, or None.
            cancelled (bool): Whether the import was cancelled.
        """
        code = self.settings["post_script"]
        if not self.settings["post_script_enabled"] or not code.strip():
            return
        context = {
            "records": list(self.records),
            "imported_records": self.get_imported_records(),
            "failed_records": [record for record in self.records if record["status"] == constants.STATUS_FAILED],
            "time_range": time_range,
            "cancelled": cancelled,
            "top_group": self.top_group,
            "control_node": self.control_node,
            "settings": dict(self.settings),
        }
        try:
            run_script(code, context, POST_SCRIPT_NAME)
        except Exception as exception:
            logger.warning(f"Post-import script failed:\n{traceback.format_exc()}")
            self.messages.append(f"Post-import script failed: {exception}")


def get_stored_range(file_info, scene_fps):
    """Gets the timeline saved in a file, converted to scene frames.

    Args:
        file_info (dict): File information (see formats.read_file_info).
        scene_fps (float): Current scene frame rate.

    Returns:
        tuple: (start, end) in scene frames, or None when the file stores no range.
    """
    stored_range = (file_info or {}).get(formats.FILE_INFO_TIME_RANGE)
    if not stored_range:
        return None
    return scene_settings.scale_time_range(stored_range, file_info.get(formats.FILE_INFO_FPS), scene_fps)


def get_bounding_box(nodes):
    """Gets the world bounding box of nodes, including joint-only hierarchies.

    Joints have no geometry, so Maya returns an empty box for them. In that case the box is built
    from the world positions of every transform in the hierarchy.

    Args:
        nodes (list): Root nodes.

    Returns:
        list: [min_x, min_y, min_z, max_x, max_y, max_z], or None when nothing can be measured.
    """
    import maya.cmds as cmds

    existing_nodes = [node for node in nodes or [] if cmds.objExists(node)]
    if not existing_nodes:
        return None
    bounding_box = cmds.exactWorldBoundingBox(existing_nodes)
    if layout.is_valid_bounding_box(bounding_box):
        return bounding_box
    transforms = list(existing_nodes)
    transforms += cmds.listRelatives(existing_nodes, allDescendents=True, type="transform", fullPath=True) or []
    positions = [cmds.xform(transform, query=True, worldSpace=True, translation=True) for transform in transforms]
    if not positions:
        return None
    return [min(position[axis] for position in positions) for axis in range(3)] + [
        max(position[axis] for position in positions) for axis in range(3)
    ]
