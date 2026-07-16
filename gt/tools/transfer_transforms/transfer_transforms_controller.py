"""Controller for the Transfer Transforms MVC tool."""

import logging
import os

import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)


class TransferTransformsController:
    """Coordinates persistent state, the Qt view, and Maya scene operations."""

    def __init__(self, model, view, service, version):
        """Initializes controller bindings.

        Args:
            model (TransferTransformsModel): Persistent and session state.
            view (TransferTransformsView): Qt interface.
            service (TransferTransformsService): Maya runtime operations.
            version (str): Tool version used by exported files.
        """
        self.model = model
        self.view = view
        self.service = service
        self.version = version
        self.view.controller = self
        self._syncing_view = False
        self._sync_view()
        self._connect_view()
        self.view.show()

    def _connect_view(self):
        """Connects view signals to controller actions."""
        for attribute, widgets in self.view.attribute_widgets.items():
            widgets.get("enabled").toggled.connect(
                lambda value, key=f"{attribute}_enabled": self._store_setting(key, value)
            )
            widgets.get("inverted").toggled.connect(
                lambda value, key=f"{attribute}_inverted": self._store_setting(key, value)
            )
        self.view.left_tag_field.editingFinished.connect(self._store_side_tags)
        self.view.right_tag_field.editingFinished.connect(self._store_side_tags)
        for attribute, field in self.view.clipboard_fields.items():
            field.editingFinished.connect(
                lambda attribute=attribute, field=field: self._store_clipboard_value(attribute, field)
            )
        self.view.transfer_button.clicked.connect(self.transfer_selection)
        self.view.right_to_left_button.clicked.connect(lambda: self.transfer_sides("right"))
        self.view.left_to_right_button.clicked.connect(lambda: self.transfer_sides("left"))
        self.view.get_button.clicked.connect(self.get_transforms)
        self.view.set_button.clicked.connect(self.set_transforms)
        self.view.export_button.clicked.connect(self.export_transforms)
        self.view.import_button.clicked.connect(self.import_transforms)
        self.view.reset_button.clicked.connect(self.reset_settings)
        self.view.help_button.clicked.connect(self.view.show_help)

    def _sync_view(self):
        """Copies model state into the view without saving it again."""
        self._syncing_view = True
        try:
            for attribute, widgets in self.view.attribute_widgets.items():
                widgets.get("enabled").setChecked(self.model.settings.get(f"{attribute}_enabled"))
                widgets.get("inverted").setChecked(self.model.settings.get(f"{attribute}_inverted"))
            self.view.left_tag_field.setText(self.model.settings.get("left_tag"))
            self.view.right_tag_field.setText(self.model.settings.get("right_tag"))
            self._sync_clipboard_fields()
        finally:
            self._syncing_view = False

    def _sync_clipboard_fields(self):
        """Copies persistent clipboard values into their fields."""
        for attribute, field in self.view.clipboard_fields.items():
            field.setText(f"{self.model.clipboard.get(attribute):.3f}")

    def _store_setting(self, key, value):
        """Stores one persistent setting.

        Args:
            key (str): Model setting key.
            value (object): New value.
        """
        if not self._syncing_view:
            self.model.set_setting(key, value)

    def _store_side_tags(self):
        """Stores both side tags in one preferences write."""
        if self._syncing_view:
            return
        self.model.set_setting("left_tag", self.view.left_tag_field.text(), save=False)
        self.model.set_setting("right_tag", self.view.right_tag_field.text(), save=False)
        self.model.save_preferences()

    def _store_clipboard_value(self, attribute, field, save=True):
        """Validates and stores one editable clipboard value.

        Args:
            attribute (str): Transform channel.
            field (QLineEdit): Edited field.
            save (bool, optional): Whether to save preferences immediately.
        """
        if self.model.set_clipboard_value(attribute, field.text(), save=save):
            return
        field.setText(f"{self.model.clipboard.get(attribute):.3f}")
        self._report(f"Enter a valid number for {attribute}.", level="warning")

    def transfer_selection(self):
        """Transfers enabled channels from the first selected node to the rest."""
        selection = self.service.get_selection()
        if len(selection) < 2:
            self._report("Select a source first, followed by at least one target.", level="warning")
            return
        result = self.service.transfer(
            source=selection[0],
            targets=selection[1:],
            transform_options=self.model.get_transform_options(),
        )
        self._report_result(result, "Transferred")

    def transfer_sides(self, source_side):
        """Transfers enabled channels between name-paired selected nodes.

        Args:
            source_side (str): ``left`` or ``right``.
        """
        self._store_side_tags()
        left_tag = self.model.settings.get("left_tag")
        right_tag = self.model.settings.get("right_tag")
        if not left_tag or not right_tag or left_tag == right_tag:
            self._report("Left and right tags must be different, non-empty values.", level="warning")
            return
        selection = self.service.get_selection()
        pairs = self.model.build_side_pairs(selection, left_tag, right_tag)
        if not pairs:
            self._report("No selected left/right object pairs matched the current tags.", level="warning")
            return
        result = self.service.transfer_pairs(
            pairs=pairs,
            source_side=source_side,
            transform_options=self.model.get_transform_options(),
        )
        self._report_result(result, f"Transferred {len(pairs)} pair(s);")

    def get_transforms(self):
        """Copies enabled channels from the first selected node into session state."""
        selection = self.service.get_selection()
        if not selection:
            self._report("Select an object to get its transforms.", level="warning")
            return
        values, errors = self.service.get_values(selection[0], self.model.get_transform_options())
        self.model.set_clipboard(values)
        self._sync_clipboard_fields()
        result = {"succeeded": len(values), "errors": errors}
        self._report_result(result, "Copied")

    def set_transforms(self):
        """Applies the editable persistent values to every selected node."""
        for attribute, field in self.view.clipboard_fields.items():
            self._store_clipboard_value(attribute, field, save=False)
        self.model.save_preferences()
        selection = self.service.get_selection()
        if not selection:
            self._report("Select at least one object to set its transforms.", level="warning")
            return
        result = self.service.set_values(
            targets=selection,
            values=self.model.clipboard,
            transform_options=self.model.get_transform_options(),
        )
        self._report_result(result, "Set")

    def export_transforms(self):
        """Exports complete TRS data for the current selection."""
        selection = self.service.get_selection()
        if not selection:
            self._report("Select at least one object to export.", level="warning")
            return
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self.view,
            "Export Transforms",
            os.path.expanduser("~"),
            "JSON Files (*.json)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        try:
            records = self.service.collect_records(selection)
            self.model.write_transform_file(file_path, records, self.version)
        except Exception as exception:
            logger.exception("Unable to export transforms.")
            self._report(f"Export failed: {exception}", level="error")
            return
        self._report(f"Exported {len(records)} object(s) to {file_path}.", level="success")

    def import_transforms(self):
        """Imports complete TRS data from a selected JSON file."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            self.view,
            "Import Transforms",
            os.path.expanduser("~"),
            "JSON Files (*.json)",
        )
        if not file_path:
            return
        try:
            records = self.model.read_transform_file(file_path)
            result = self.service.apply_records(records)
        except Exception as exception:
            logger.exception("Unable to import transforms.")
            self._report(f"Import failed: {exception}", level="error")
            return
        missing_count = len(result.get("missing", []))
        if missing_count:
            logger.warning("Missing imported objects: %s", ", ".join(result.get("missing")))
        self._report_result(result, "Imported", extra_count=missing_count)

    def reset_settings(self):
        """Restores default options and clipboard values, then refreshes the view."""
        self.model.reset_preferences()
        self._sync_view()
        self._report("Settings restored to defaults.", level="success")

    def _report_result(self, result, verb, extra_count=0):
        """Reports a standard scene-operation result.

        Args:
            result (dict): Service result dictionary.
            verb (str): Past-tense operation label.
            extra_count (int, optional): Additional skipped item count.
        """
        succeeded = result.get("succeeded", 0)
        errors = result.get("errors", [])
        if errors:
            logger.warning("Transfer Transforms issues:\n%s", "\n".join(errors))
        if errors or extra_count:
            details = []
            if errors:
                details.append(f"{len(errors)} channel(s) skipped")
            if extra_count:
                details.append(f"{extra_count} object(s) missing")
            self._report(
                f"{verb} {succeeded} channel value(s); {', '.join(details)}. See Script Editor.",
                level="warning",
            )
            return
        self._report(f"{verb} {succeeded} channel value(s).", level="success")

    def _report(self, message, level="info"):
        """Reports feedback in the view and Maya warning stream.

        Args:
            message (str): User-facing message.
            level (str, optional): Feedback severity.
        """
        self.view.set_status(message, level=level)
        if level in ("warning", "error"):
            try:
                self.service._get_cmds().warning(message)
            except Exception:
                logger.warning(message)
