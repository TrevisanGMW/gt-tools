"""Annotation Setup controller for profiles, skeleton mapping, and preferences."""

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from gt.tools.annotation_tracker import annotation_tracker_scene, auto_annotation
from gt.tools.annotation_tracker import auto_annotation_capture as capture
from gt.tools.annotation_tracker import auto_annotation_local as local
from gt.tools.annotation_tracker import auto_annotation_model as model
from gt.tools.annotation_tracker import auto_annotation_motion as motion
from gt.tools.annotation_tracker import auto_annotation_scene as scene
from gt.tools.annotation_tracker import auto_annotation_vlm as vlm
from gt.tools.annotation_tracker.auto_annotation_progress import AnnotationProgress
from gt.utils import vault
from gt.tools.annotation_tracker.auto_annotation_setup_view import AnnotationSetupDialog
from gt.ui.qt_import import QtCore, QtWidgets


_active_dialog = None


class AnnotationSetupController:
    """Connects the settings and calibration view to Maya and profile storage."""

    def __init__(self, dialog, cmds, context):
        """Wires settings and calibration actions.

        Args:
            dialog (AnnotationSetupDialog): Setup view.
            cmds (module): Maya commands.
            context (dict): Optional Tracker automation context.
        """
        self.dialog = dialog
        self.cmds = cmds
        self.context = context
        self.export_schema = dialog.schema
        dialog.import_settings.clicked.connect(self.import_settings)
        dialog.export_settings.clicked.connect(self.export_settings)
        dialog.import_calibration.clicked.connect(self.import_calibration)
        dialog.export_calibration.clicked.connect(self.export_calibration)
        dialog.duplicate_calibration.clicked.connect(self.duplicate_calibration)
        dialog.clear_calibration.clicked.connect(self.clear_calibration)
        dialog.pick_root.clicked.connect(self.pick_root)
        dialog.pick_joint.clicked.connect(self.pick_joint)
        dialog.clear_mapping.clicked.connect(self.clear_mapping)
        dialog.detect_skeleton.clicked.connect(self.detect_skeleton)
        dialog.calibrate.clicked.connect(self.calibrate)
        dialog.calibrate_all.clicked.connect(self.calibrate_all)
        dialog.calibrate_playback.clicked.connect(self.calibrate_playback)
        dialog.refresh_ranges.clicked.connect(self.refresh_ranges)
        dialog.ranges_clicked.connect(self.refresh_ranges)
        dialog.tabs.currentChanged.connect(self._refresh_on_train_entry)
        dialog.calibration_tabs.currentChanged.connect(self._refresh_on_train_entry)
        dialog.buttons.accepted.connect(self.save)
        dialog.auto_save.toggled.connect(self._on_auto_save_toggled)
        self._last_snapshot = self._snapshot()
        self.autosave_timer = QtCore.QTimer(dialog)
        self.autosave_timer.setInterval(1000)
        self.autosave_timer.timeout.connect(self._autosave_tick)
        self.autosave_timer.start()
        dialog.reset_all.clicked.connect(self.reset_all)
        dialog.vlm.detect_server.clicked.connect(self.detect_local_server)
        dialog.vlm.refresh_models.clicked.connect(self.refresh_local_models)
        dialog.vlm.save_key.clicked.connect(self.save_api_key)
        dialog.vlm.clear_key.clicked.connect(self.clear_api_key)
        dialog.vlm.open_debug.clicked.connect(self.open_debug_folder)
        dialog.test_source.clicked.connect(self.test_source)
        dialog.vlm.preview_request.clicked.connect(self.preview_vlm_request)
        dialog.vlm.last_reply.clicked.connect(self.show_last_reply)
        dialog.vlm.purge_debug.clicked.connect(self.purge_debug_files)
        active_range = context.get("active_range")
        self.source_scene = None
        self.refresh_ranges(getattr(active_range, "id", None))

    def _snapshot(self):
        """Serializes the current Setup values to detect changes.

        Returns:
            str: Stable text form of the displayed settings.
        """
        return json.dumps(self.dialog.read_settings(), sort_keys=True, default=str)

    def _autosave_tick(self):
        """Saves pending edits when Auto-save is on."""
        if not self.dialog.auto_save.isChecked():
            return
        snapshot = self._snapshot()
        if snapshot == self._last_snapshot:
            return
        self._last_snapshot = snapshot
        if self.persist():
            self.dialog.status.show_message("Auto-saved changes.")

    def _on_auto_save_toggled(self, enabled):
        """Saves pending edits when switching on, or only the flag when switching off.

        Args:
            enabled (bool): New Auto-save state.
        """
        if enabled:
            self._last_snapshot = self._snapshot()
            if self.persist():
                self.dialog.status.show_message("Auto-save on. Changes are saved as you make them.")
            return
        try:
            model.save_settings(dict(model.load_settings(), auto_save=False))
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.status.show_message("Auto-save off. Click Save to keep further changes.")

    def save_api_key(self):
        """Encrypts the typed API key for the current Windows user."""
        provider = self.dialog.vlm.provider.currentData()
        key = self.dialog.vlm.api_key.text().strip()
        try:
            vault.store_secret(vlm.stored_secret_name(provider), key)
        except vault.VaultError as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.vlm.api_key.clear()
        self.dialog.vlm._update_credential_status()
        self.dialog.status.show_message(f"Saved the {provider} API key, encrypted for your Windows account.")

    def clear_api_key(self):
        """Deletes the saved API key of the selected provider after confirmation."""
        provider = self.dialog.vlm.provider.currentData()
        if not self._confirm("Clear API Key", f"Delete the saved {provider} API key from this computer?"):
            return
        vault.delete_secret(vlm.stored_secret_name(provider))
        self.dialog.vlm._update_credential_status()
        self.dialog.status.show_message(f"Deleted the saved {provider} API key.")

    def test_source(self):
        """Shows the Source the current folder-path settings would find."""
        settings = self.dialog.read_settings()
        path = self.dialog.source_test_path.text().strip() or self.cmds.file(query=True, sceneName=True) or ""
        if not path:
            self.dialog.status.show_message("Save the scene or paste a path to test.")
            return
        try:
            found = model.find_source_in_path(
                path, settings["file_source_pattern"], settings["file_source_depth"], settings["file_source_order"]
            )
        except Exception as error:
            self.dialog.status.show_message(f"The folder pattern is not valid. {error}")
            return
        self.dialog.status.show_message(
            f"Source would be '{found}'." if found else "No folder matched. Check the pattern and search depth."
        )

    def preview_vlm_request(self):
        """Saves the images and prompt of a VLM run for review without sending anything."""
        self.dialog.status.show_message("Building the VLM preview…")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            result = auto_annotation.preview_vlm_request(
                self.context, settings=self.dialog.read_settings(), schema=self.dialog.schema
            )
        except (OSError, ValueError, RuntimeError) as error:
            self.dialog.status.show_message(str(error))
            return
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        folder = result["vlm"].get("preview_folder")
        if not folder:
            self.dialog.status.show_message((result["warnings"] or ["Nothing to preview."])[0])
            return
        self.dialog.status.show_message(f"Saved {result['vlm']['preview_images']} image(s) and the prompt to {folder}.")
        try:
            os.startfile(str(folder))
        except (OSError, AttributeError):
            pass

    def show_last_reply(self):
        """Shows the most recent model reply or error."""
        reply = capture.read_last_reply()
        if reply is None:
            self.dialog.status.show_message("No model reply is stored yet. Run Auto Annotate with a VLM mode first.")
            return
        box = QtWidgets.QDialog(self.dialog)
        box.setWindowTitle("Last VLM Reply")
        box.resize(640, 460)
        layout = QtWidgets.QVBoxLayout(box)
        text = QtWidgets.QPlainTextEdit(json.dumps(reply, indent=2))
        text.setReadOnly(True)
        layout.addWidget(text)
        box.show()

    def purge_debug_files(self):
        """Deletes generated debug files after confirmation."""
        if not self._confirm("Purge Debug Files", "Delete saved previews, leftover images and the last reply?"):
            return
        count = capture.purge_debug_files()
        self.dialog.status.show_message(f"Deleted {count} debug file(s).")

    def open_debug_folder(self):
        """Opens the saved VLM request folder, creating it first."""
        folder = capture.get_debug_directory()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(str(folder))
        except (OSError, AttributeError) as error:
            self.dialog.status.show_message(f"Could not open {folder}. {error}")

    def detect_local_server(self):
        """Finds the running Bionic server and fills its base URL."""
        try:
            with AnnotationProgress(self.dialog) as progress:
                address = progress.wait_for_network("Checking Bionic server status…", local.get_running_local_endpoint)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.vlm.endpoint.setText(address)
        self.dialog.status.show_message(f"Found Bionic at {address}.")

    def refresh_local_models(self):
        """Populates the VLM model picker from the connected Bionic server."""
        try:
            settings = self.dialog.vlm.read_settings()
            provider, endpoint, _, key_name = vlm.get_provider_settings(settings)
            if not vlm._is_loopback(urlsplit(endpoint).hostname.lower()):
                raise ValueError("Use a loopback Bionic endpoint to discover local models.")
            key = vlm._api_secret(key_name, provider)
            with AnnotationProgress(self.dialog) as progress:
                choices = progress.wait_for_network(
                    "Reading installed Bionic vision models…",
                    local.discover_vision_models, endpoint, key, vlm._make_opener(endpoint),
                )
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.vlm.set_model_choices(choices)
        loaded = sum(item[2] for item in choices)
        self.dialog.status.show_message(
            f"Found {len(choices)} vision model ID(s), {loaded} loaded." if choices
            else "Bionic has no installed vision models."
        )

    def refresh_ranges(self, active_id=None):
        """Updates the calibration range list from the current Maya scene.

        Args:
            active_id (str, optional): Range ID to highlight.
        """
        current_scene = self.cmds.file(query=True, sceneName=True)
        selected_ids = {active_id} if active_id else set()
        if current_scene == self.source_scene:
            selected_ids.update(
                item.data(QtCore.Qt.ItemDataRole.UserRole)["id"] for item in self.dialog.ranges.selectedItems()
            )
        unchanged_scene = current_scene == self.source_scene
        self.source_scene = current_scene
        try:
            ranges = scene.read_payload(self.cmds, self.context)["range_data"]
        except (ValueError, RuntimeError) as error:
            ranges = []
            self.dialog.status.show_message(str(error))
        listed = [
            self.dialog.ranges.item(row).data(QtCore.Qt.ItemDataRole.UserRole)
            for row in range(self.dialog.ranges.count())
        ]
        if unchanged_scene and listed == ranges:
            return
        self.dialog.set_ranges(ranges, selected_ids)

    def _choose_export_path(self, title, filename):
        """Prompts for an export destination with a JSON filename.

        Args:
            title (str): File dialog title.
            filename (str): Suggested filename.

        Returns:
            Path or None: Chosen destination, or None when cancelled.
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self.dialog, title, filename, "JSON (*.json)")
        return Path(path) if path else None

    def _refresh_on_train_entry(self, *args):
        """Updates training ranges each time the Train page becomes visible."""
        if (
            self.dialog.tabs.currentWidget() is self.dialog.calibration_page
            and self.dialog.calibration_tabs.currentWidget() is self.dialog.training_page
        ):
            self.refresh_ranges()

    def import_settings(self):
        """Loads a settings file into Setup without changing saved preferences."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.dialog, "Import Auto Annotate Settings", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            settings = model.read_settings_file(path)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.export_schema = settings.get("schema", self.dialog.schema)
        self.dialog.apply_settings(settings)
        message = "Imported settings and calibration. Click Save to apply them in the Tracker."
        if self.export_schema != self.dialog.schema:
            message = (
                "Imported settings. This Tracker uses its active schema. "
                "An export retains the imported schema for dataset runs."
            )
        self.dialog.status.show_message(message)

    def export_settings(self):
        """Exports the current setup, calibration, and dataset schema."""
        path = self._choose_export_path("Export Auto Annotate Settings", "auto_annotation_settings.json")
        if path is None:
            return
        try:
            settings = dict(self.dialog.read_settings(), schema=self.export_schema)
            model.write_settings_file(path, settings)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.status.show_message(f"Exported settings to {path.name}.")

    def import_calibration(self):
        """Copies standalone calibration into the values currently being edited."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self.dialog, "Import Calibration", "", "JSON (*.json)")
        if not path:
            return
        try:
            profile = model.read_profile(path)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.select_label_source(profile.get("label_source", "stance"))
        self.dialog.set_calibration(profile, activate=True)
        self.dialog.status.show_message("Copied calibration into this setup. Save or export the settings to keep it.")

    def export_calibration(self):
        """Exports the selected calibration profile by itself."""
        profile = self.dialog.read_calibration() if self.dialog.showing_custom else model.copy_default_profile()
        path = self._choose_export_path("Export Calibration", "annotation_calibration.json")
        if path is None:
            return
        try:
            model.write_profile(path, profile)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.status.show_message(f"Exported calibration to {path.name}.")

    def duplicate_calibration(self):
        """Copies the built-in calibration into the editable custom slot."""
        if self.dialog.showing_custom:
            return
        if self.dialog.read_calibration() is not None and not self._confirm(
            "Duplicate Calibration",
            "Replace the current custom calibration profile with a copy of the built-in defaults?",
        ):
            return
        profile = model.copy_default_profile()
        self.dialog.select_label_source(profile["label_source"])
        self.dialog.set_calibration(profile, activate=True)
        self.dialog.status.show_message("Copied the built-in calibration to the custom profile. Save to keep it.")

    def pick_root(self):
        """Uses one selected Maya transform as the skeleton root."""
        selected = self.cmds.ls(selection=True, long=True, type=("transform", "joint")) or []
        if len(selected) != 1:
            self.dialog.status.show_message("Select one skeleton root transform or joint in Maya.")
            return
        self.dialog.skeleton_root.setText(selected[0])
        self.dialog.status.show_message("Skeleton root assigned.")

    def pick_joint(self):
        """Assigns one Maya joint to the highlighted manual role."""
        selected = self.cmds.ls(selection=True, long=True, type="joint") or []
        row = self.dialog.joints.currentRow()
        if len(selected) != 1 or row < 0:
            self.dialog.status.show_message("Select one Maya joint and highlight a skeleton role.")
            return
        self.dialog.set_joint(row, selected[0])
        self.dialog.status.show_message("Joint assigned.")

    def detect_skeleton(self):
        """Previews the current scene's detected joint roles."""
        try:
            mapping = scene.resolve_skeleton(
                self.cmds, skeleton_root=self.dialog.skeleton_root.text().strip(),
                short_name_fallback=self.dialog.short_name_fallback.isChecked(),
            )
        except (ValueError, RuntimeError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.set_joint_map(mapping)
        self.dialog.status.show_message(f"Detected {len(mapping)} joint roles.")

    def clear_mapping(self):
        """Clears only the saved skeleton binding after confirmation."""
        if not self._confirm("Clear Saved Mapping", "Remove the saved skeleton root and manual joint mapping?"):
            return
        try:
            settings = dict(model.load_settings(), skeleton_mode="auto", skeleton_root="", joint_map={})
            model.save_settings(settings)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.dialog.options["joint_map"] = {}
        self.dialog.skeleton_mode.setCurrentIndex(self.dialog.skeleton_mode.findData("auto"))
        self.dialog.skeleton_root.clear()
        self.dialog.set_joint_map({})
        self.dialog.status.show_message("Saved skeleton mapping cleared.")

    def clear_calibration(self):
        """Clears embedded calibration in the pending settings after confirmation."""
        if not self._confirm("Clear Calibration", "Clear calibration from this setup?"):
            return
        self.dialog.set_calibration(None, activate=False)
        self.dialog.status.show_message("Calibration cleared. Save to update the Tracker's saved settings.")

    def reset_all(self):
        """Resets saved preferences with an option to preserve calibration."""
        message = QtWidgets.QMessageBox(self.dialog)
        message.setWindowTitle("Reset Settings")
        message.setText("Restore the default Auto Annotate settings?")
        message.setInformativeText("Choose whether to keep the calibration currently shown in Setup.")
        reset = message.addButton("Reset Everything", QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
        keep = message.addButton("Keep Calibration", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        cancel = message.addButton(QtWidgets.QMessageBox.StandardButton.Cancel)
        message.setDefaultButton(cancel)
        message.setEscapeButton(cancel)
        message.exec()
        choice = message.clickedButton()
        if choice not in (reset, keep):
            return
        profile = self.dialog.read_calibration() if choice == keep else None
        try:
            pose_field = self.dialog.pose_field.currentData()
            defaults = model.reset_settings(
                profile, use_profile=self.dialog.showing_custom, pose_field=pose_field
            )
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return
        self.export_schema = self.dialog.schema
        self.dialog.apply_settings(defaults)
        self.dialog.status.show_message("Auto Annotate preferences restored to defaults.")

    def _confirm(self, title, message):
        """Confirms a requested reset or deletion.

        Args:
            title (str): Confirmation window title.
            message (str): Action that requires confirmation.

        Returns:
            bool: Whether the user chose Yes.
        """
        buttons = QtWidgets.QMessageBox.StandardButton
        return QtWidgets.QMessageBox.question(
            self.dialog, title, message, buttons.Yes | buttons.Cancel, buttons.Cancel
        ) == buttons.Yes

    def _labeled_examples(self, items, source, bounds):
        """Collects the stored pose and speed labels for ranges inside playback.

        Args:
            items (list): Live Tracker scene ranges.
            source (str): Range names or selected schema field.
            bounds (tuple): First and last playback frame.

        Returns:
            tuple: Inclusive frame pairs with pose labels and locomotion states.
        """
        field = self.dialog.range_fields.get(source)
        start, end = bounds
        examples = []
        states = []
        for item in items:
            pose, state = model.get_training_labels(item, source, field)
            first, last = max(start, item["start"]), min(end, item["end"])
            if first > last:
                continue
            if pose:
                learned_state = "activity" if model.is_activity_example(item) else ""
                examples.append((first, last, pose, learned_state))
            if state:
                states.append((first, last, state))
        return examples, states

    def calibrate(self):
        """Adds only selected Tracker ranges to the custom profile."""
        self._measure_examples("selected")

    def calibrate_all(self):
        """Adds all labeled ranges in the current scene in one sampling pass."""
        self._measure_examples("all")

    def calibrate_playback(self):
        """Prompts for a label for a clip that represents a single example."""
        source = self.dialog.pose_field.currentData()
        field = self.dialog.range_fields.get(source, {})
        if field.get("type") == "enum":
            choices = [value for value in field.get("options", []) if value and value != "none"]
            if not choices:
                self.dialog.status.show_message("The selected schema field has no usable values.")
                return
            label, accepted = QtWidgets.QInputDialog.getItem(
                self.dialog, "Learn from Playback", "Pose label", choices, 0, False
            )
        else:
            label, accepted = QtWidgets.QInputDialog.getText(self.dialog, "Learn from Playback", "Pose label")
        if accepted and label.strip():
            self._measure_examples("playback", label.strip())

    def _measure_examples(self, scope, label=""):
        """Samples the requested ranges once and embeds all measured examples.

        Args:
            scope (str): Selected ranges, all Tracker ranges, or full playback.
            label (str): Explicit label when training from full playback.
        """
        settings = self.dialog.read_settings()
        learn_speeds = self.dialog.speed_editor.learns_speeds()
        try:
            start, end = scene.playback_bounds(self.cmds)
            if scope == "playback":
                selected, states = [(start, end, label)], []
            else:
                live = scene.read_payload(self.cmds, self.context)["range_data"]
                if scope == "selected":
                    visible = [
                        item.data(QtCore.Qt.ItemDataRole.UserRole) for item in self.dialog.ranges.selectedItems()
                    ]
                    by_id = {item["id"]: item for item in live}
                    if self.source_scene != self.cmds.file(query=True, sceneName=True) or any(
                        by_id.get(item["id"]) != item for item in visible
                    ):
                        raise ValueError("Scene ranges changed. Refresh Ranges before adding selected cues.")
                    live = visible
                else:
                    self.refresh_ranges()
                selected, states = self._labeled_examples(live, settings["pose_field"], (start, end))
            skipped_speeds = bool(states) and not learn_speeds
            if not learn_speeds:
                states = []
            if not selected and not states:
                raise ValueError("No usable labels found. Name a range, set its State, or choose a populated field.")
            mapping = scene.resolve_skeleton(
                self.cmds, settings["skeleton_mode"], settings["skeleton_root"], settings["joint_map"],
                short_name_fallback=settings["short_name_fallback"],
            )
            samples = scene.sample_joints(self.cmds, mapping, start, end)
            analysis = motion.analyze_motion(samples)
            examples = motion.collect_examples(analysis, selected)
            locomotion = motion.collect_examples(analysis, states, ("speed",)) if states else {}
            profile = model.merge_profile_examples(settings["calibration"], examples, locomotion)
        except (OSError, ValueError, RuntimeError) as error:
            self.dialog.status.show_message(str(error))
            return
        count, focus = self._added_examples(settings["calibration"], profile)
        speed_note = " Speed ranges were ignored." if skipped_speeds else ""
        if locomotion and (settings["calibration"] or {}).get("locomotion") == profile.get("locomotion"):
            speed_note = (
                " Speed limits unchanged: they update only when two neighboring states "
                "(idle, walk, run, sprint) each have 8+ frames with distinct speeds."
            )
        self.dialog.show_training_result(profile, focus)
        self.export_schema = self.dialog.schema
        total = sum(
            len(items) for section in ("poses", "locomotion_examples") for items in profile.get(section, {}).values()
        )
        self.dialog.status.show_message(
            f"Added {count} new cue(s). Profile has {total} cues. Save or export to keep it.{speed_note}"
            if count else f"Profile still has {total} cues. Duplicate measurements were kept once.{speed_note}"
        )

    @staticmethod
    def _added_examples(before, after):
        """Counts appended examples and identifies one new example to inspect.

        Args:
            before (dict or None): Profile before collecting data.
            after (dict): Profile after collecting data.

        Returns:
            tuple: New example count and section, label and index to select.
        """
        count = 0
        focus = None
        for section in ("locomotion_examples", "poses"):
            previous = (before or {}).get(section, {})
            for label, items in after.get(section, {}).items():
                difference = len(items) - len(previous.get(label, []))
                if difference > 0:
                    count += difference
                    focus = (section, label, len(items) - 1)
        return count, focus

    def save(self):
        """Saves the displayed settings and closes Setup."""
        if self.persist():
            self.dialog.accept()

    def persist(self):
        """Validates and saves the displayed settings.

        Returns:
            bool: Whether the settings were saved.
        """
        settings = self.dialog.read_settings()
        try:
            if settings["skeleton_mode"] == "auto":
                settings["joint_map"] = self.dialog.options["joint_map"]
            elif not {"pelvis", "left_foot", "right_foot"}.issubset(settings["joint_map"]):
                raise ValueError("Manual mapping requires a pelvis and both feet.")
            if settings["file_style_source"] == "fixed" and not model.supports_value(
                self.dialog.file_fields.get("style"), settings["file_style"]
            ):
                raise ValueError("Choose a File Style value accepted by the active schema.")
            if settings["vlm_mode"] != "off":
                vlm.get_provider_settings(settings)
            model.save_settings(settings)
        except (OSError, ValueError) as error:
            self.dialog.status.show_message(str(error))
            return False
        self._last_snapshot = self._snapshot()
        return True


def open_setup(context=None):
    """Opens Annotation Setup inside interactive Maya.

    Args:
        context (dict, optional): Annotation Tracker automation context.

    Returns:
        QDialog or None: Active nonmodal setup window, when running interactively.
    """
    global _active_dialog
    context = context or {}
    cmds = annotation_tracker_scene._get_maya_cmds()
    if cmds.about(batch=True):
        return None
    if _active_dialog is not None:
        _active_dialog.raise_()
        _active_dialog.activateWindow()
        return _active_dialog
    parent = context.get("parent")
    if parent is None:
        from gt.ui.qt_utils import get_maya_main_window

        parent = get_maya_main_window()
    schema = auto_annotation.resolve_schema(context)
    dialog = AnnotationSetupDialog(model.load_settings(), schema, parent=parent)
    dialog.controller = AnnotationSetupController(dialog, cmds, context)
    dialog.destroyed.connect(_clear_dialog)
    _active_dialog = dialog
    dialog.show()
    print("[Auto Annotate] Setup window opened.")
    return dialog


def _clear_dialog(*args):
    """Clears the reference to a closed Setup window."""
    global _active_dialog
    _active_dialog = None
