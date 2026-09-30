"""HumanIK Utilities view/model binding and user action coordination."""

from functools import partial
import logging
import os

from gt.ui import qt_import as ui_qt
from gt.tools.anim_hik_utils import anim_hik_utils_model as tool_model
from gt.tools.anim_hik_utils.anim_hik_utils_service import AnimHikUtilsService

logger = logging.getLogger(__name__)


class AnimHikUtilsController:
    """Coordinates validated Maya actions, file dialogs, and user feedback."""

    def __init__(self, model, view, service=None):
        """Connects the MVC components and displays the window.

        Args:
            model (AnimHikUtilsModel): Pure tool state.
            view (AnimHikUtilsView): Constructed view.
            service (AnimHikUtilsService, optional): Injectable runtime service.
        """
        self.model = model
        self.view = view
        self.service = service or AnimHikUtilsService()
        self.view.controller = self
        self.view.set_settings(self.model.settings)
        self.actions = {
            "refresh": self.refresh,
            "reset": self.reset,
            "mirror_left": partial(self.pose, "left"),
            "mirror_right": partial(self.pose, "right"),
            "flip": partial(self.pose, "flip"),
            "animation_left": partial(self.animation, "left"),
            "animation_right": partial(self.animation, "right"),
            "animation_flip": partial(self.animation, "flip"),
            "playback_range": self.use_playback_range,
            "import_pose": partial(self.pose, "import"),
            "browse_xml": self.browse_xml,
            "preview_xml": self.preview_xml,
            "import_definition": self.import_definition,
            "detect_namespace": self.detect_namespace,
            "inspect": self.inspect,
            "cleanup": self.cleanup,
            "copy_properties": self.copy_properties,
            "paste_properties": self.paste_properties,
            "import_properties": self.import_properties,
            "bake_skeleton": partial(self.bake, "skeleton"),
            "bake_controls": partial(self.bake, "controls"),
        }
        for operation in ("create", "rename", "lock", "unlock", "source", "stance"):
            self.actions[operation] = partial(self.definition_action, operation)
        for kind in ("pose", "definition", "properties"):
            self.actions[f"export_{kind}"] = partial(self.export_file, kind)
        for kind in ("character", "skeleton", "controls", "property_node"):
            self.actions[f"select_{kind}"] = partial(self.select_nodes, kind)
        for key, button in view.buttons.items():
            button.clicked.connect(partial(self.execute, key))
        for widget in view.settings_widgets.values():
            if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
                widget.toggled.connect(self.save_settings)
            else:
                widget.editingFinished.connect(self.save_settings)
        self.view.character_combo.currentIndexChanged.connect(self.character_changed)
        self.execute("refresh")
        self.execute("playback_range")
        self.view.show()

    def execute(self, action, checked=False):
        """Handles an action and surfaces exceptions in the status area and log.

        Args:
            action (str): Registered action identifier.
            checked (bool): Qt clicked signal value.
        """
        try:
            self.save_settings()
            self.actions[action]()
        except Exception as exception:
            logger.exception("HumanIK action '%s' failed for '%s'.", action, self.model.character)
            self.view.set_status(str(exception))

    def save_settings(self, *unused_args):
        """Stores option changes without allowing a preference error to block work.

        Args:
            *unused_args: Optional Qt signal values.
        """
        self.model.update_settings(self.view.get_settings())
        try:
            self.model.save_preferences()
        except Exception:
            logger.warning("Could not save HumanIK Utilities preferences.", exc_info=True)

    def refresh(self):
        """Refreshes exact scene targets, preserving the selected character when valid."""
        characters = self.service.characters()
        combo = self.view.character_combo
        previous = self.model.character
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Choose a character", "")
        for character in characters:
            combo.addItem(character, character)
        combo.setCurrentIndex(max(0, combo.findData(previous)))
        combo.blockSignals(False)
        self.character_changed()
        self.view.set_status(f"Found {len(characters)} HumanIK character(s). Choose one to run utilities.")

    def character_changed(self, *unused_args):
        """Updates transient selection and available source choices.

        Args:
            *unused_args: Optional Qt signal values.
        """
        self.model.character = self.view.character_combo.currentData() or ""
        for button in self.view.target_buttons:
            button.setEnabled(bool(self.model.character))
        source = self.view.source_combo.currentData()
        self.view.source_combo.clear()
        self.view.source_combo.addItem("Choose a source character", "")
        combo = self.view.character_combo
        for index in range(1, combo.count()):
            character = combo.itemData(index)
            if character != self.model.character:
                self.view.source_combo.addItem(character, character)
        self.view.source_combo.setCurrentIndex(max(0, self.view.source_combo.findData(source)))
        self.view.character_summary.setText("Choose a HumanIK character or create a definition.")
        if self.model.character:
            try:
                details = self.service.inspect_character(self.model.character)
                state = "Locked" if details["locked"] else "Unlocked"
                namespace = details["namespace"] or "root"
                self.view.character_summary.setText(
                    f"{state} | Namespace: {namespace} | "
                    f"{len(details['skeleton'])} joints | {len(details['controls'])} controls\n"
                    f"Source: {details['source']}"
                )
            except Exception as exception:
                self.view.set_status(str(exception))

    def confirm(self, title, message):
        """Requests confirmation for a concrete destructive or replacing action.

        Args:
            title (str): Dialog title.
            message (str): Target-specific description.

        Returns:
            bool: Whether the user chose Yes.
        """
        buttons = ui_qt.QtWidgets.QMessageBox.StandardButton
        return ui_qt.QtWidgets.QMessageBox.question(
            self.view, title, message, buttons.Yes | buttons.No, buttons.No
        ) == buttons.Yes

    def file_dialog(self, kind, save=False):
        """Chooses a file and remembers its directory.

        Args:
            kind (str): pose, definition, or properties.
            save (bool): Show a save dialog with native overwrite confirmation.

        Returns:
            str: Selected path, or an empty string on cancellation.
        """
        extension = "xml" if kind == "definition" else "json"
        dialog = ui_qt.QtWidgets.QFileDialog
        chooser = dialog.getSaveFileName if save else dialog.getOpenFileName
        path, unused_filter = chooser(
            self.view, f"{'Export' if save else 'Import'} HumanIK {kind.title()}",
            self.model.settings["last_directory"], f"HumanIK {kind.title()} (*.{extension})",
        )
        if path:
            if save and not os.path.splitext(path)[1]:
                path = f"{path}.{extension}"
                if os.path.exists(path) and not self.confirm("Replace File", f"Replace this file?\n{path}"):
                    return ""
            self.model.settings["last_directory"] = os.path.dirname(path)
            self.save_settings()
        return path

    def reset(self):
        """Resets persisted options while keeping scene selection intact."""
        self.model.reset_to_defaults()
        self.view.set_settings(self.model.settings)
        self.view.set_status("HumanIK Utilities options reset.")

    def pose(self, operation):
        """Runs a current-frame pose action.

        Args:
            operation (str): left, right, flip, or import.
        """
        path = self.file_dialog("pose") if operation == "import" else None
        if operation == "import" and not path:
            return
        result = self.service.pose(self.model.character, operation, self.model.settings, path)
        self.view.set_status(f"Pose applied to {len(result)} controls. No keys added; key the result if needed.")

    def use_playback_range(self):
        """Refreshes the displayed animation range from Maya."""
        self.view.set_animation_range(*self.service.playback_range())

    def animation(self, operation):
        """Confirms the exact target and sampling range before replacing keys.

        Args:
            operation (str): left, right, or flip.
        """
        from gt.core.anim import get_frame_sample_times

        self.service.require_character(self.model.character)
        if self.view.animation_range_mode.currentIndex() == 0:
            self.use_playback_range()
        start, end = self.view.animation_start.value(), self.view.animation_end.value()
        step = self.view.animation_step.value()
        times = get_frame_sample_times(start, end, step)
        label = {"left": "Left to Right", "right": "Right to Left", "flip": "Flip"}[operation]
        if not self.confirm(
            "Mirror HumanIK Animation",
            f"{label}: {self.model.character}\nFrames {start:g} to {end:g}, {len(times)} samples.\n\n"
            "Replace animation keys on the affected controls within this range?\n"
            "Keys outside the range are kept. Continuous channels use sampled keys with linear tangents.\n"
            "Run on baked control-rig animation; animation layers and driven target channels are not supported.",
        ):
            return
        self.view.set_status(f"Sampling and mirroring {len(times)} frames...")
        result = self.service.animation(self.model.character, operation, self.model.settings, start, end, step)
        skipped = result["skipped_channels"]
        self.view.set_status(
            f"{label}: {len(result['controls'])} controls, {result['sample_count']} samples; "
            f"{len(skipped)} channels skipped. Undo restores the original animation."
        )
        if skipped:
            self.view.show_report("Skipped locked or non-keyable channels:\n" + "\n".join(skipped))

    def definition_action(self, operation):
        """Runs definition management or source assignment.

        Args:
            operation (str): Definition action identifier.
        """
        value = self.view.name_field.text()
        if operation == "source":
            value = self.view.source_combo.currentData()
            if not value:
                raise ValueError("Choose a source character, or use Clear Source / Stance.")
        elif operation == "stance":
            operation, value = "source", None
        result = self.service.definition_action(self.model.character, operation, value)
        if operation in ("create", "rename"):
            self.model.character = result
        self.refresh()
        self.view.set_status(f"HumanIK {operation} completed for {self.model.character}.")

    def browse_xml(self):
        """Chooses an XML match list for preview and import."""
        path = self.file_dialog("definition")
        if path:
            self.view.xml_path.setText(path)

    def preview_xml(self):
        """Reports resolved XML slots without modifying the character.

        Returns:
            list: Checked mapping rows.
        """
        rows = self.service.preview_definition(
            self.model.character, self.view.xml_path.text().strip(), self.model.settings
        )
        report = [f"XML mapping for {self.model.character}", ""]
        report.extend(f"[{status}] {slot}: {bone}" for slot, bone, status in rows)
        self.view.show_report("\n".join(report))
        ready = sum(status == "Ready" for unused_slot, unused_bone, status in rows)
        self.view.set_status(f"XML preview: {ready}/{len(rows)} mappings ready. No scene changes.")
        return rows

    def import_definition(self):
        """Previews and confirms mapped-slot replacement before importing."""
        rows = self.preview_xml()
        if any(status != "Ready" for unused_slot, unused_bone, status in rows):
            raise ValueError("Resolve the XML preview issues before importing. See Inspect.")
        if not self.confirm(
            "Import HumanIK Definition",
            f"Apply {len(rows)} bone mappings to {self.model.character}?\n"
            "Existing assignments in these slots will be replaced. The definition will be left unlocked.",
        ):
            return
        count = self.service.import_definition(
            self.model.character, self.view.xml_path.text().strip(), self.model.settings
        )
        self.character_changed()
        self.view.set_status(f"Imported {count} mappings. Review the definition and lock it when ready.")

    def detect_namespace(self):
        """Fills XML Prefix using the selected character's skeleton namespace."""
        namespace = self.service.inspect_character(self.model.character)["namespace"]
        self.model.settings["prefix"] = f"{namespace}:" if namespace else ""
        self.model.settings["search_namespace"] = ""
        self.model.settings["replace_namespace"] = ""
        self.view.set_settings(self.model.settings)
        self.save_settings()
        self.view.set_status(f"XML prefix set to {namespace or 'the root namespace'}.")

    def export_file(self, kind):
        """Exports the chosen data type after path and overwrite confirmation.

        Args:
            kind (str): pose, definition, or properties.
        """
        self.service.require_character(self.model.character)
        path = self.file_dialog(kind, save=True)
        if path:
            self.service.export_file(self.model.character, kind, path, self.model.settings)
            self.view.set_status(f"Exported {kind}: {path}")

    def copy_properties(self):
        """Copies character properties into the model's session clipboard."""
        self.model.copied_properties = self.service.properties(self.model.character)
        self.view.set_status(f"Copied {len(self.model.copied_properties)} properties from {self.model.character}.")

    def paste_properties(self):
        """Applies properties captured in this tool session."""
        if not self.model.copied_properties:
            raise ValueError("Copy properties from a character first.")
        self.apply_properties(self.model.copied_properties)

    def import_properties(self):
        """Loads and validates a portable HumanIK properties dictionary."""
        path = self.file_dialog("properties")
        if path:
            self.apply_properties(tool_model.read_properties(path))

    def apply_properties(self, properties):
        """Reports both applied and skipped properties.

        Args:
            properties (dict): Requested retarget settings.
        """
        applied = self.service.apply_properties(self.model.character, properties)
        skipped = sorted(set(properties) - set(applied))
        self.view.set_status(f"Applied {len(applied)}/{len(properties)} properties; {len(skipped)} skipped.")
        if skipped:
            self.view.show_report("Skipped properties (unsupported, locked, or connected):\n" + "\n".join(skipped))

    def bake(self, destination):
        """Confirms the character and playback range before baking.

        Args:
            destination (str): skeleton or controls.
        """
        self.service.require_character(self.model.character, writable=True)
        cmds, unused_hik = self.service.runtime()
        start = cmds.playbackOptions(query=True, minTime=True)
        end = cmds.playbackOptions(query=True, maxTime=True)
        if not self.confirm(
            "Bake HumanIK Animation",
            f"Bake {self.model.character} to {destination} over frames {start:g} to {end:g}?\n"
            "This can replace animation and incoming source connections on the target.",
        ):
            return
        self.view.set_status(f"Baking {self.model.character}...")
        self.service.bake(self.model.character, destination, self.model.settings["force_proxy"])
        self.character_changed()
        self.view.set_status(f"Baked {self.model.character} to {destination} over {start:g} to {end:g}.")

    def inspect(self):
        """Displays current scene information for the selected character."""
        details = self.service.inspect_character(self.model.character)
        lines = []
        for key, value in details.items():
            if isinstance(value, list):
                lines.append(f"\n{key.replace('_', ' ').title()} ({len(value)}):")
                lines.extend(f"  {node}" for node in value)
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value or '(none)'}")
        self.view.show_report("\n".join(lines))
        self.view.set_status(f"Inspected {self.model.character}.")

    def select_nodes(self, kind):
        """Selects the requested part of the chosen character.

        Args:
            kind (str): Character detail field.
        """
        count = self.service.select_nodes(self.model.character, kind)
        self.view.set_status(f"Selected {count} {kind.replace('_', ' ')} node(s).")

    def cleanup(self):
        """Previews and confirms deletion of exact empty local definitions."""
        candidates = self.service.empty_definitions()
        self.view.show_report("Empty local definitions eligible for deletion:\n\n" +
                              ("\n".join(candidates) or "None."))
        if not candidates:
            self.view.set_status("No empty, unprotected definitions to delete.")
            return
        if not self.confirm(
            "Delete Empty HumanIK Definitions",
            f"Delete these {len(candidates)} empty definitions?\n\n" + "\n".join(candidates),
        ):
            self.view.set_status("Cleanup preview only. Nothing deleted.")
            return
        count = self.service.delete_empty_definitions(candidates)
        self.refresh()
        self.view.set_status(f"Deleted {count} empty definitions. Maya Undo can restore them.")
