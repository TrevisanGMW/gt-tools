"""
Multi-File Importer Controller

Connects the view and the model, and runs the import loop. Files are imported one at a time on
Maya's main thread; Qt events are processed between files so the progress bar updates and the
Cancel button works (a cancel takes effect after the current file).

Edits to settings and the file list are written to preferences as they happen.
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_formats as formats
from gt.tools.multi_file_importer import multi_file_importer_model as model_module
from gt.tools.multi_file_importer import multi_file_importer_service as service
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import logging
import os
import time
import traceback

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

StatusLine = ui_qt_utils.StatusLine


class MultiFileImporterController:
    """Connects the Multi-File Importer view and model."""

    def __init__(self, model, view):
        """Initializes the controller and shows the view.

        Args:
            model (MultiFileImporterModel): Model instance.
            view (MultiFileImporterView): View instance.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.is_running = False
        self.cancel_requested = False
        self.context_handlers = {}
        self.populate_view()
        self.connect_view()
        self.view.show()
        self.view.fit_floating_window()

    # ------------------------------------------------------------------ setup
    def populate_view(self):
        """Fills the view from the model."""
        format_list = formats.get_formats()
        filter_items = [(constants.FILTER_ALL, constants.FILTER_ALL)]
        filter_items += [(file_format.label, file_format.key) for file_format in format_list]
        self.view.set_filter_items(filter_items)
        self.view.set_format_items([(file_format.label, file_format.key) for file_format in format_list])
        self.sync_view_from_model()
        if self.model.entries:
            self.view.set_status(f"Restored {len(self.model.entries)} file(s) from the last session.")

    def sync_view_from_model(self):
        """Shows the model settings, section states, format options and file list in the view."""
        self.view.set_settings(self.model.settings)
        for section_key, expanded in self.model.get_startup_section_states().items():
            section = self.view.sections.get(section_key)
            if section:
                section.set_expanded(expanded)
                self.model.set_section_state(section_key, expanded)
        format_index = self.view.format_combo.findData(self.model.selected_format)
        if format_index >= 0:
            blocked = self.view.format_combo.blockSignals(True)
            self.view.format_combo.setCurrentIndex(format_index)
            self.view.format_combo.blockSignals(blocked)
        self.show_format_options()
        self.refresh_entries()

    def connect_view(self):
        """Connects view signals."""
        self.view.connect_setting_changes(self.on_settings_changed)
        self.view.format_combo.currentIndexChanged.connect(lambda *args: self.on_format_selected())
        for section_key, section in self.view.sections.items():
            section.toggled.connect(lambda expanded, key=section_key: self.on_section_toggled(key, expanded))
        file_list = self.view.file_list
        file_list.paths_dropped.connect(self.add_paths)
        file_list.delete_requested.connect(self.remove_selected)
        file_list.copy_requested.connect(self.copy_paths)
        file_list.paste_requested.connect(self.paste_paths)
        file_list.toggle_requested.connect(self.toggle_selected)
        file_list.itemChanged.connect(self.on_item_changed)
        file_list.context_menu_requested.connect(self.show_context_menu)
        self.view.add_files_btn.clicked.connect(self.add_files_from_dialog)
        self.view.add_folder_btn.clicked.connect(self.add_folder_from_dialog)
        self.view.remove_btn.clicked.connect(self.remove_selected)
        self.view.clear_btn.clicked.connect(self.clear_entries)
        for sort_mode, action in self.view.sort_actions.items():
            action.triggered.connect(lambda *args, mode=sort_mode: self.sort_entries(mode))
        self.context_handlers = {
            "check_all": lambda: self.set_checks(None, True),
            "uncheck_all": lambda: self.set_checks(None, False),
            "check_selected": lambda: self.set_checks(self.view.get_selected_entry_ids(), True),
            "uncheck_selected": lambda: self.set_checks(self.view.get_selected_entry_ids(), False),
            "solo_selected": self.solo_selected,
            "invert_checks": self.invert_checks,
            "select_all": lambda: self.view.file_list.selectAll(),
            "select_checked": self.select_checked,
            "copy_paths": self.copy_paths,
            "paste_paths": self.paste_paths,
            "open_folder": self.open_selected_folder,
            "remove_selected": self.remove_selected,
            "remove_unchecked": self.remove_unchecked,
            "remove_missing": self.remove_missing,
            "reset_status": self.reset_statuses,
        }
        self.view.reset_btn.clicked.connect(self.reset_settings)
        self.view.export_settings_btn.clicked.connect(self.export_settings)
        self.view.import_settings_btn.clicked.connect(self.import_settings)
        self.view.per_file_load_btn.clicked.connect(lambda *args: self.load_script_file("per_file_script"))
        self.view.post_load_btn.clicked.connect(lambda *args: self.load_script_file("post_script"))
        self.view.import_btn.clicked.connect(self.run_import)
        self.view.cancel_btn.clicked.connect(self.request_cancel)
        self.view.set_close_callback(self.on_close)

    # ------------------------------------------------------------------ persistence
    def write_changes(self, **change_flags):
        """Writes the changed values to the tool preferences immediately.

        Args:
            **change_flags: Arguments for MultiFileImporterModel.write_changes.
        """
        if not self.model.write_changes(**change_flags):
            self.view.set_status("Unable to save preferences (see Script Editor).", StatusLine.WARNING)

    # ------------------------------------------------------------------ settings
    def on_settings_changed(self):
        """Stores edited settings in the model and refreshes dependent widgets."""
        changed_keys = self.model.update_settings(self.view.get_settings())
        self.view.refresh_enabled_states()
        if changed_keys:
            self.write_changes(setting_keys=changed_keys, files="keep_file_list" in changed_keys)

    def on_section_toggled(self, section_key, expanded):
        """Stores a section state.

        Args:
            section_key (str): Section key.
            expanded (bool): Expanded state.
        """
        self.model.set_section_state(section_key, expanded)

    def on_format_selected(self):
        """Shows the selected format and remembers it."""
        self.model.selected_format = self.view.get_selected_format_key()
        self.show_format_options()
        self.write_changes(selected_format=True)

    def show_format_options(self):
        """Shows the options of the format selected in the Format Options section."""
        format_key = self.view.get_selected_format_key()
        file_format = formats.get_format(format_key)
        if not file_format:
            self.view.set_format_options("", [], {}, self.on_format_option_changed)
            return
        description = file_format.description
        available, reason = file_format.is_available()
        if not available:
            description = f"{description}\nUnavailable: {reason}"
        self.view.set_format_options(
            description,
            file_format.get_options(),
            self.model.get_format_settings(format_key),
            self.on_format_option_changed,
        )

    def on_format_option_changed(self):
        """Stores the edited options of the selected format."""
        format_key = self.view.get_selected_format_key()
        self.model.set_format_settings(format_key, self.view.get_format_values())
        self.write_changes(format_keys=[format_key])

    def reset_settings(self):
        """Restores every setting to its default. The file list is kept."""
        saved = self.model.reset_preferences()
        self.sync_view_from_model()
        if not saved:
            self.view.set_status("Unable to save reset settings (see Script Editor).", StatusLine.WARNING)
            return
        self.view.set_status("Settings reset to defaults.")
        print(f"{constants.TOOL_NAME}: settings reset to defaults.")

    def export_settings(self):
        """Saves every setting and format option to a JSON file."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self.view, "Export Settings", os.path.join(self.get_start_directory(), "multi_file_importer.json"),
            constants.EXPORT_FILE_FILTER,
        )
        if not file_path:
            return
        try:
            self.model.export_settings(file_path)
        except (IOError, OSError, TypeError, ValueError) as exception:
            self.view.set_status(f"Unable to export settings: {exception}", StatusLine.ERROR)
            return
        self.model.last_directory = os.path.dirname(file_path)
        self.view.set_status(f"Settings exported: {os.path.basename(file_path)}", StatusLine.SUCCESS)
        self.write_changes(last_directory=True)

    def import_settings(self):
        """Loads settings and format options from a JSON file."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            self.view, "Import Settings", self.get_start_directory(), constants.EXPORT_FILE_FILTER
        )
        if not file_path:
            return
        try:
            added_count = self.model.import_settings(file_path)
        except (IOError, OSError, ValueError) as exception:
            self.view.set_status(f"Unable to import settings: {exception}", StatusLine.ERROR)
            return
        self.model.last_directory = os.path.dirname(file_path)
        self.sync_view_from_model()
        if not self.model.save_preferences():
            self.view.set_status("Settings imported, but could not be saved to preferences.", StatusLine.WARNING)
            return
        files_text = f" Added {added_count} file(s)." if added_count else ""
        self.view.set_status(f"Settings imported: {os.path.basename(file_path)}.{files_text}", StatusLine.SUCCESS)

    def load_script_file(self, code_key):
        """Loads a .py file into a script editor.

        Args:
            code_key (str): "per_file_script" or "post_script".
        """
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            self.view, "Load Script", self.get_start_directory(), "Python Files (*.py);;All Files (*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as script_file:
                script_text = script_file.read()
        except (IOError, OSError, UnicodeDecodeError) as exception:
            self.view.set_status(f"Unable to read script: {exception}", StatusLine.ERROR)
            return
        self.view.set_script_text(code_key, script_text)
        self.view.set_status(f"Loaded script: {os.path.basename(file_path)}")

    # ------------------------------------------------------------------ file list
    def refresh_entries(self):
        """Shows the model entries in the file list."""
        self.view.set_entries(self.model.entries)

    def save_file_list(self):
        """Writes changes to the file list when persistence is enabled."""
        if self.model.settings["keep_file_list"]:
            self.write_changes(files=True)

    def get_start_directory(self):
        """Gets the folder file dialogs open in.

        Returns:
            str: Last used folder when it still exists, otherwise the home folder.
        """
        if self.model.last_directory and os.path.isdir(self.model.last_directory):
            return self.model.last_directory
        return os.path.expanduser("~")

    def build_file_dialog_filter(self):
        """Builds the file dialog filter from the supported extensions.

        Returns:
            str: Qt file dialog filter.
        """
        patterns = " ".join(f"*{extension}" for extension in self.model.get_allowed_extensions())
        return f"Supported Files ({patterns});;All Files (*)"

    def add_files_from_dialog(self):
        """Adds files picked in a file dialog."""
        file_paths, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileNames(
            self.view, "Add Files", self.get_start_directory(), self.build_file_dialog_filter()
        )
        if file_paths:
            self.add_paths(file_paths, last_directory=os.path.dirname(file_paths[0]))

    def add_folder_from_dialog(self):
        """Adds every supported file of a folder picked in a dialog."""
        folder_path = ui_qt.QtWidgets.QFileDialog.getExistingDirectory(
            self.view, "Add Folder", self.get_start_directory()
        )
        if folder_path:
            self.add_paths([folder_path], last_directory=folder_path)

    def add_paths(self, paths, last_directory=None):
        """Adds files and folders to the list and reports the result.

        Args:
            paths (list): File and folder paths.
            last_directory (str, optional): Directory picked in a file or folder dialog.
        """
        if self.is_running:
            return
        if last_directory is not None:
            self.model.last_directory = last_directory
        result = self.model.add_paths(paths)
        self.refresh_entries()
        details = []
        if result["duplicates"]:
            details.append(f"{result['duplicates']} already listed")
        if result["unsupported"]:
            details.append(f"{result['unsupported']} unsupported or filtered out")
        detail_text = f" ({', '.join(details)})" if details else ""
        status = StatusLine.INFO if result["added"] else StatusLine.WARNING
        self.view.set_status(f"Added {result['added']} file(s){detail_text}.", status)
        save_files = bool(result["added"]) and self.model.settings["keep_file_list"]
        if save_files or last_directory is not None:
            self.write_changes(files=save_files, last_directory=last_directory is not None)

    def remove_selected(self):
        """Removes the selected files from the list."""
        if self.is_running:
            return
        removed_count = self.model.remove_entries(self.view.get_selected_entry_ids())
        self.refresh_entries()
        if removed_count:
            self.view.set_status(f"Removed {removed_count} file(s).")
            self.save_file_list()

    def remove_unchecked(self):
        """Removes every unchecked file from the list."""
        if self.is_running:
            return
        removed_count = self.model.remove_unchecked()
        self.refresh_entries()
        self.view.set_status(f"Removed {removed_count} unchecked file(s).")
        if removed_count:
            self.save_file_list()

    def remove_missing(self):
        """Removes files that no longer exist on disk."""
        if self.is_running:
            return
        removed_count = self.model.remove_missing()
        self.refresh_entries()
        self.view.set_status(f"Removed {removed_count} missing file(s).")
        if removed_count:
            self.save_file_list()

    def clear_entries(self):
        """Removes every file from the list."""
        if self.is_running:
            return
        self.model.clear_entries()
        self.refresh_entries()
        self.view.set_status("File list cleared.")
        self.save_file_list()

    def sort_entries(self, sort_mode):
        """Sorts the list.

        Args:
            sort_mode (str): One of constants.SORT_MODES.
        """
        self.model.sort_entries(sort_mode)
        self.refresh_entries()
        self.save_file_list()

    def set_checks(self, entry_ids, checked):
        """Checks or unchecks entries.

        Args:
            entry_ids (list): Entry IDs, or None for every entry.
            checked (bool): New state.
        """
        self.model.set_entries_enabled(entry_ids, checked)
        self.refresh_entries_keep_selection()
        self.save_file_list()

    def solo_selected(self):
        """Checks only the selected files."""
        self.model.solo_entries(self.view.get_selected_entry_ids())
        self.refresh_entries_keep_selection()
        self.save_file_list()

    def invert_checks(self):
        """Inverts every checkbox."""
        self.model.invert_checks()
        self.refresh_entries_keep_selection()
        self.save_file_list()

    def toggle_selected(self):
        """Toggles the checkboxes of the selected rows (Space key)."""
        selected_entries = self.model.get_entries(self.view.get_selected_entry_ids())
        new_state = not all(entry.enabled for entry in selected_entries)
        self.set_checks([entry.entry_id for entry in selected_entries], new_state)

    def select_checked(self):
        """Selects the rows of checked files."""
        self.view.select_entries([entry.entry_id for entry in self.model.get_enabled_entries()])

    def refresh_entries_keep_selection(self):
        """Refreshes the list without losing the row selection."""
        selected_ids = self.view.get_selected_entry_ids()
        self.refresh_entries()
        self.view.select_entries(selected_ids)

    def reset_statuses(self):
        """Marks every file as pending."""
        self.model.reset_statuses()
        self.refresh_entries_keep_selection()

    def copy_paths(self):
        """Copies the selected file paths (all paths when nothing is selected) to the clipboard."""
        selected_entries = self.model.get_entries(self.view.get_selected_entry_ids()) or self.model.entries
        if not selected_entries:
            return
        ui_qt.QtWidgets.QApplication.clipboard().setText("\n".join(entry.path for entry in selected_entries))
        self.view.set_status(f"Copied {len(selected_entries)} path(s).")

    def paste_paths(self):
        """Adds the files and folders found in the clipboard text (one path per line)."""
        paths = model_module.parse_pasted_paths(ui_qt.QtWidgets.QApplication.clipboard().text())
        if not paths:
            self.view.set_status("The clipboard has no paths to paste.", StatusLine.WARNING)
            return
        self.add_paths(paths)

    def open_selected_folder(self):
        """Opens the folder of the first selected file in the system file browser."""
        selected_entries = self.model.get_entries(self.view.get_selected_entry_ids())
        if not selected_entries:
            return
        folder_path = selected_entries[0].folder
        if not os.path.isdir(folder_path):
            self.view.set_status(f"Folder not found: {folder_path}", StatusLine.WARNING)
            return
        ui_qt.QtGui.QDesktopServices.openUrl(ui_qt.QtCore.QUrl.fromLocalFile(folder_path))

    def show_context_menu(self, position):
        """Shows the right-click menu with actions enabled for the current list and selection.

        Args:
            position (QPoint): Click position.
        """
        if self.is_running:
            return
        has_entries = bool(self.model.entries)
        has_selection = bool(self.view.get_selected_entry_ids())
        selection_actions = ["check_selected", "uncheck_selected", "solo_selected", "open_folder", "remove_selected"]
        list_actions = ["check_all", "uncheck_all", "invert_checks", "select_all", "select_checked", "copy_paths",
                        "remove_unchecked", "remove_missing", "reset_status"]
        enabled_states = {action_key: has_selection for action_key in selection_actions}
        enabled_states.update({action_key: has_entries for action_key in list_actions})
        self.view.show_context_menu(position, self.context_handlers, enabled_states)

    def on_item_changed(self, item, column):
        """Stores a checkbox change from the list.

        Args:
            item (QTreeWidgetItem): Changed item.
            column (int): Changed column.
        """
        self.model.set_entry_enabled(self.view.get_item_entry_id(item), self.view.is_item_checked(item))
        self.view.update_counts(self.model.entries)
        self.save_file_list()

    # ------------------------------------------------------------------ import
    def build_jobs(self, entries):
        """Builds service jobs for the enabled entries.

        Args:
            entries (list): Enabled FileEntry objects, in order.

        Returns:
            list: Job dictionaries.
        """
        jobs = []
        for index, entry in enumerate(entries, 1):
            jobs.append(
                {
                    "path": entry.path,
                    "index": index,
                    "namespace": self.model.build_namespace(entry.path, index),
                    "group_name": self.model.build_group_name(entry.path, index),
                }
            )
        return jobs

    def run_import(self):
        """Validates the settings and imports every checked file."""
        if self.is_running:
            return
        self.model.update_settings(self.view.get_settings())
        errors, warnings = self.model.validate()
        if errors:
            self.view.set_status(errors[0], StatusLine.ERROR)
            return
        if self.model.settings["new_scene_on_import"] and not self.start_new_scene():
            self.view.set_status("Import cancelled. The current scene was kept.", StatusLine.WARNING)
            return
        entries = self.model.get_enabled_entries()
        for entry in entries:
            entry.set_status(constants.STATUS_PENDING)
        self.refresh_entries()
        self.save_preferences()
        session = service.ImportSession(self.model.settings, self.model.get_all_format_settings(),
                                        self.build_jobs(entries))
        self.is_running = True
        self.cancel_requested = False
        self.view.set_running(True)
        start_time = time.time()
        try:
            session.start()
            stopped_message = self.import_entries(session, entries)
            summary = session.finish(cancelled=self.cancel_requested)
            summary["stopped_message"] = stopped_message
        except Exception as exception:
            logger.error(f"{constants.TOOL_NAME} failed:\n{traceback.format_exc()}")
            summary = {"error": str(exception)}
        finally:
            self.is_running = False
            if self.is_view_valid():
                self.view.set_running(False)
        if self.is_view_valid():
            self.report_summary(session, summary, warnings, time.time() - start_time)

    @staticmethod
    def start_new_scene():
        """Starts a new scene, offering to save unsaved changes first.

        Returns:
            bool: True when a new scene was created, False when the user cancelled.
        """
        import gt.core.scene as core_scene

        return core_scene.create_new_scene(prompt_save=True)

    def import_entries(self, session, entries):
        """Imports entries one by one, updating progress and honouring cancel requests.

        Args:
            session (ImportSession): Started import session.
            entries (list): Enabled FileEntry objects, in job order.

        Returns:
            str: Message when the "Stop Import" policy stopped the loop, otherwise an empty string.
        """
        total_count = len(entries)
        for entry_index, (entry, job) in enumerate(zip(entries, session.jobs)):
            self.process_events()
            if self.cancel_requested:
                self.mark_remaining(entries[entry_index:], constants.STATUS_CANCELLED, "Cancelled by the user.")
                return ""
            if self.is_view_valid():
                self.view.set_progress(entry_index, total_count, f"Importing {entry.name}")
            self.process_events()
            try:
                record = session.import_job(job)
            except RuntimeError as exception:
                failed_record = session.records[-1] if session.records else {}
                entry.set_status(constants.STATUS_FAILED, failed_record.get("message", str(exception)))
                self.update_entry_view(entry)
                self.mark_remaining(entries[entry_index + 1:], constants.STATUS_SKIPPED, "Import stopped.")
                return str(exception)
            entry.set_status(record["status"], record["message"])
            self.update_entry_view(entry)
            if self.is_view_valid():
                self.view.set_progress(entry_index + 1, total_count, entry.name)
        return ""

    def mark_remaining(self, entries, status, message):
        """Marks entries that were not imported.

        Args:
            entries (list): FileEntry objects.
            status (str): Status to set.
            message (str): Status detail.
        """
        for entry in entries:
            entry.set_status(status, message)
            self.update_entry_view(entry)

    def update_entry_view(self, entry):
        """Updates one entry row when the view is still open.

        Args:
            entry (FileEntry): Entry to show.
        """
        if self.is_view_valid():
            self.view.update_entry(entry)

    def report_summary(self, session, summary, validation_warnings, elapsed_seconds):
        """Shows the import result in the status line and logs the details.

        Args:
            session (ImportSession): Finished session.
            summary (dict): Result of ImportSession.finish, or {"error": message}.
            validation_warnings (list): Warnings found before importing.
            elapsed_seconds (float): Total duration.
        """
        if summary.get("error"):
            self.view.set_status(f"Import failed: {summary['error']} (see Script Editor).", StatusLine.ERROR)
            return
        records = session.records
        imported_count = len(session.get_imported_records())
        failed_count = len([record for record in records if record["status"] == constants.STATUS_FAILED])
        skipped_count = len([record for record in records if record["status"] == constants.STATUS_SKIPPED])
        warning_messages = list(validation_warnings) + list(summary.get("messages") or [])
        for message in warning_messages:
            logger.info(message)
        parts = [f"Imported {imported_count} of {len(session.jobs)} file(s) in {elapsed_seconds:.1f}s"]
        if failed_count:
            parts.append(f"{failed_count} failed")
        if skipped_count:
            parts.append(f"{skipped_count} skipped")
        if self.cancel_requested:
            parts.append("cancelled")
        if summary.get("time_range"):
            start_frame, end_frame = summary["time_range"]
            parts.append(f"timeline {start_frame:g}-{end_frame:g}")
        message = ", ".join(parts) + "."
        if summary.get("stopped_message"):
            message = f"{summary['stopped_message']} {message}"
        if warning_messages:
            message += f" {len(warning_messages)} note(s) in the Script Editor."
        if not imported_count:
            status = StatusLine.ERROR
        elif failed_count or skipped_count or self.cancel_requested or warning_messages:
            status = StatusLine.WARNING
        else:
            status = StatusLine.SUCCESS
        self.view.set_status(message, status)
        print(f"{constants.TOOL_NAME}: {message}")

    def request_cancel(self):
        """Asks the import loop to stop after the current file."""
        if not self.is_running:
            return
        self.cancel_requested = True
        if self.is_view_valid():
            self.view.set_cancel_requested()

    @staticmethod
    def process_events():
        """Lets Qt repaint and handle clicks (such as Cancel) between files."""
        ui_qt.QtWidgets.QApplication.processEvents()

    def is_view_valid(self):
        """Checks whether the view still exists.

        Returns:
            bool: True when the view can be updated.
        """
        return ui_qt_utils.is_qt_object_valid(self.view)

    def on_close(self):
        """Requests cancellation if the window closes during an import."""
        self.request_cancel()
