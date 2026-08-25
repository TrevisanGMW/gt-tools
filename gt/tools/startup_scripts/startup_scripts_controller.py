"""Controller for the GT Tools Startup Scripts tool."""

from gt.tools.startup_scripts import startup_scripts_model as model_constants
from gt.tools.startup_scripts import startup_scripts_runtime as runtime
import os


class StartupScriptsController:
    """Connects Startup Scripts preferences, UI editing, and Maya runtime setup."""

    def __init__(self, model, view):
        """Initializes the controller and connects the view to the model.

        Args:
            model (StartupScriptsModel): Persistent Startup Scripts model.
            view (StartupScriptsView): Startup Scripts Qt view.
        """
        self.model = model
        self.view = view
        self.selected_script_id = ""
        self.view.controller = self
        self.view.set_run_modes(
            model_constants.RUN_MODE_VALUES,
            run_mode_tooltips=model_constants.RUN_MODE_TOOLTIPS,
        )
        self.view.set_run_interval_units(model_constants.RUN_INTERVAL_UNITS)
        self.view.set_sample_scripts(model_constants.get_sample_scripts())
        self.view.sample_load_callback = self.load_sample_script
        self._connect_view()
        self.refresh_view()
        self.view.show()

    def _connect_view(self):
        """Connects all editable controls and persistent actions."""
        self.view.script_list.currentItemChanged.connect(self.on_script_selection_changed)
        self.view.add_script_button.clicked.connect(self.add_script)
        self.view.duplicate_script_button.clicked.connect(self.duplicate_script)
        self.view.move_up_button.clicked.connect(lambda: self.move_selected_script(-1))
        self.view.move_down_button.clicked.connect(lambda: self.move_selected_script(1))
        self.view.remove_script_button.clicked.connect(self.remove_selected_script)
        self.view.import_backup_button.clicked.connect(self.import_backup)
        self.view.export_backup_button.clicked.connect(self.export_backup)
        self.view.name_field.textChanged.connect(lambda value: self.update_selected_script({"name": value}, True))
        self.view.enabled_checkbox.toggled.connect(
            lambda value: self.update_selected_script({"enabled": bool(value)}, True)
        )
        self.view.run_mode_combo.currentTextChanged.connect(
            lambda value: self.update_selected_script({"run_mode": value})
        )
        self.view.run_interval_enabled_checkbox.toggled.connect(
            lambda value: self.update_selected_script({"run_interval_enabled": bool(value)})
        )
        self.view.run_interval_value_spinbox.valueChanged.connect(
            lambda value: self.update_selected_script({"run_interval_value": int(value)})
        )
        self.view.run_interval_unit_combo.currentTextChanged.connect(
            lambda value: self.update_selected_script({"run_interval_unit": value})
        )
        self.view.print_message_checkbox.toggled.connect(
            lambda value: self.update_selected_script({"print_execution_message": bool(value)})
        )
        self.view.inline_editor.python_edit.textChanged.connect(
            lambda: self.update_selected_script({"script_text": self.view.inline_editor.get_text()})
        )
        self.view.inline_editor.font_size_slider.valueChanged.connect(
            lambda value: self.update_selected_script({"font_size": int(value)})
        )
        self.view.add_external_file_button.clicked.connect(self.add_external_files)
        self.view.remove_external_file_button.clicked.connect(self.remove_external_file)
        self.view.add_directory_button.clicked.connect(self.add_script_directory)
        self.view.remove_directory_button.clicked.connect(self.remove_script_directory)
        self.view.external_files_list.itemChanged.connect(
            lambda item: self.update_source_entries(self.view.external_files_list, "external_files")
        )
        self.view.script_directories_list.itemChanged.connect(
            lambda item: self.update_source_entries(self.view.script_directories_list, "script_directories")
        )
        self.view.examples_button.clicked.connect(self.view.show_samples_menu)
        self.view.run_selected_button.clicked.connect(self.run_selected_script)

    def refresh_view(self, selected_script_id=""):
        """Synchronizes the view with persisted model data.

        Args:
            selected_script_id (str, optional): Script identifier to select.
        """
        scripts = self.model.get_scripts()
        available_ids = [script.get("id") for script in scripts]
        candidate_id = selected_script_id or self.selected_script_id
        if candidate_id not in available_ids:
            candidate_id = available_ids[0] if available_ids else ""
        self.selected_script_id = candidate_id
        self.view.set_scripts(scripts, selected_script_id=candidate_id)
        self.view.set_script_details(self.model.get_script(candidate_id))

    def on_script_selection_changed(self, current_item, previous_item):
        """Loads a selected configuration into the detail editor.

        Args:
            current_item (QListWidgetItem): Newly selected item.
            previous_item (QListWidgetItem): Previously selected item.
        """
        if self.view.is_loading:
            return
        self.selected_script_id = self.view.get_current_script_id()
        self.view.set_script_details(self.model.get_script(self.selected_script_id))

    def add_script(self):
        """Adds and selects a new persistent startup-script configuration."""
        script = self.model.add_script()
        self.refresh_runtime_callback()
        self.refresh_view(script.get("id"))
        self.view.emit_status_message("Added and saved a new startup script.")

    def duplicate_script(self):
        """Duplicates the selected startup-script configuration."""
        script = self.model.duplicate_script(self.selected_script_id)
        if not script:
            return
        self.refresh_runtime_callback()
        self.refresh_view(script.get("id"))
        self.view.emit_status_message("Duplicated and saved the startup script.")

    def remove_selected_script(self):
        """Removes the selected persistent startup-script configuration."""
        script = self.model.get_script(self.selected_script_id)
        if not script:
            return
        if not self.view.confirm_remove_script(script.get("name") or "Startup Script"):
            return
        self.model.remove_script(self.selected_script_id)
        self.selected_script_id = ""
        self.refresh_runtime_callback()
        self.refresh_view()
        self.view.emit_status_message("Removed the startup script.")

    def import_backup(self):
        """Imports a complete startup-script setup after confirmation.

        The selected backup replaces every current startup-script configuration.
        """
        file_path = self.view.choose_backup_import_path()
        if not file_path or not self.view.confirm_backup_import():
            return
        try:
            imported_scripts = self.model.import_backup(file_path)
        except Exception as exception:
            self.view.emit_status_message(f"Unable to import backup: {exception}", status="error")
            return
        self.selected_script_id = ""
        self.refresh_runtime_callback()
        self.refresh_view()
        self.view.emit_status_message(f"Imported {len(imported_scripts)} startup script(s) from backup.")

    def export_backup(self):
        """Exports the complete startup-script setup to a JSON backup."""
        file_path = self.view.choose_backup_export_path()
        if not file_path:
            return
        try:
            written_path = self.model.export_backup(file_path)
        except Exception as exception:
            self.view.emit_status_message(f"Unable to export backup: {exception}", status="error")
            return
        self.view.emit_status_message(f"Exported Startup Scripts backup: {written_path}")

    def move_selected_script(self, offset):
        """Moves the selected script within the persisted execution order.

        Args:
            offset (int): Signed positional offset.
        """
        if not self.model.move_script(self.selected_script_id, offset):
            return
        self.refresh_view(self.selected_script_id)
        self.view.emit_status_message("Saved the startup script order.")

    def update_selected_script(self, updates, refresh_list=False):
        """Persists one or more edited selected-script fields.

        Args:
            updates (dict): Field values to save.
            refresh_list (bool, optional): Whether the configuration list label should refresh.
        """
        if self.view.is_loading or not self.selected_script_id:
            return
        updated_script = self.model.update_script(self.selected_script_id, updates)
        if not updated_script:
            return
        self.refresh_runtime_callback()
        if refresh_list:
            self.view.set_scripts(self.model.get_scripts(), self.selected_script_id)

    def update_source_entries(self, source_list, source_key):
        """Persists the enabled state and order of one source list.

        Args:
            source_list (QListWidget): Edited file or directory list.
            source_key (str): Configuration key that owns the source list.
        """
        if self.view.is_loading:
            return
        entries = self.view.get_source_entries(source_list)
        self.update_selected_script({source_key: entries})

    def add_external_files(self):
        """Adds selected Python files to the current script configuration."""
        file_paths = self.view.choose_external_files()
        if not file_paths or not self.selected_script_id:
            return
        script = self.model.get_script(self.selected_script_id)
        entries = list(script.get("external_files", []))
        entries.extend({"path": path, "enabled": True} for path in file_paths)
        self.model.update_script(self.selected_script_id, {"external_files": entries})
        self.refresh_runtime_callback()
        self.refresh_view(self.selected_script_id)
        self.view.emit_status_message(f"Added {len(file_paths)} external Python file(s).")

    def remove_external_file(self):
        """Removes the selected external Python file from the configuration."""
        self.remove_selected_source(self.view.external_files_list, "external_files")

    def add_script_directory(self):
        """Adds one recursively scanned Python directory to the configuration."""
        directory_path = self.view.choose_script_directory()
        if not directory_path or not self.selected_script_id:
            return
        script = self.model.get_script(self.selected_script_id)
        entries = list(script.get("script_directories", []))
        entries.append({"path": directory_path, "enabled": True})
        self.model.update_script(self.selected_script_id, {"script_directories": entries})
        self.refresh_runtime_callback()
        self.refresh_view(self.selected_script_id)
        self.view.emit_status_message(f"Added script directory: {directory_path}")

    def remove_script_directory(self):
        """Removes the selected script directory from the configuration."""
        self.remove_selected_source(self.view.script_directories_list, "script_directories")

    def remove_selected_source(self, source_list, source_key):
        """Removes the current row from an external source list.

        Args:
            source_list (QListWidget): File or directory list with a selected row.
            source_key (str): Configuration key that owns the source list.
        """
        source_row = source_list.currentRow()
        if source_row < 0 or not self.selected_script_id:
            return
        script = self.model.get_script(self.selected_script_id)
        entries = list(script.get(source_key, []))
        if source_row >= len(entries):
            return
        removed_entry = entries.pop(source_row)
        self.model.update_script(self.selected_script_id, {source_key: entries})
        self.refresh_runtime_callback()
        self.refresh_view(self.selected_script_id)
        self.view.emit_status_message(f"Removed source: {removed_entry.get('path')}")

    def load_sample_script(self, sample_path):
        """Loads a packaged sample into the selected script's inline editor.

        Args:
            sample_path (str): Absolute packaged sample path.
        """
        try:
            source_text = model_constants.load_script_file(sample_path)
        except (IOError, OSError) as exception:
            self.view.emit_status_message(f"Unable to load example: {exception}", status="warning")
            return
        self.model.update_script(self.selected_script_id, {"script_text": source_text})
        self.refresh_runtime_callback()
        self.view.set_script_details(self.model.get_script(self.selected_script_id))
        self.view.emit_status_message(f"Loaded example: {os.path.basename(sample_path)}")

    def run_selected_script(self):
        """Runs the selected script configuration immediately for interactive validation."""
        script = self.model.get_script(self.selected_script_id)
        if not script:
            return
        if runtime.run_script_configuration(
            script,
            event_name=runtime.EVENT_MANUAL,
            ignore_run_mode=True,
            ignore_run_interval=True,
        ):
            self.view.emit_status_message(f"Ran '{script.get('name') or 'Startup Script'}'.")
        else:
            self.view.emit_status_message(
                "No enabled runnable source was available for the selected script.",
                status="warning",
            )

    @staticmethod
    def refresh_runtime_callback():
        """Refreshes the Maya file-open callback after preferences change."""
        runtime.refresh_file_open_callback()
