"""Controller connecting Script Library persistence and its dockable view."""

from gt.tools.script_library.script_library_constants import ScriptLibraryConstants
from gt.ui import file_dialog as ui_file_dialog
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib
import logging
import os
import subprocess
import sys
import traceback


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScriptLibraryController:
    """Coordinates Script Library editing, execution, archives, icons, and shelf actions."""

    def __init__(self, model, view):
        """Initializes controller state and view bindings.

        Args:
            model (ScriptLibraryModel): Persistent Script Library model.
            view (ScriptLibraryView): Dockable Script Library view.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.current_script_id = ""
        self.editor_dirty = False
        self.loading_editor = False
        self.auto_save_pending = False
        self.script_context_menu = None
        self.connect_view()
        self.view.set_library_preferences(
            self.model.get_show_details_in_use_mode(), self.model.get_auto_save()
        )
        self.view.set_edit_mode(
            self.model.get_edit_mode(), self.model.get_show_details_in_use_mode()
        )
        splitter_sizes = self.model.get_splitter_sizes()
        if splitter_sizes:
            self.view.splitter.setSizes(splitter_sizes)
        self.populate_script_list(preferred_id=self.model.get_selected_script_id())
        self.view.show()

    def connect_view(self):
        """Connects view signals to controller actions."""
        self.view.edit_mode_button.toggled.connect(self.on_edit_mode_toggled)
        self.view.search_bar.textChanged.connect(self.filter_script_list)
        self.view.item_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.view.item_list.customContextMenuRequested.connect(
            self.show_script_context_menu
        )
        self.view.run_button.clicked.connect(self.run_selected_script)
        self.view.list_run_button.clicked.connect(self.run_selected_script)
        self.view.add_button.clicked.connect(self.add_script)
        self.view.delete_button.clicked.connect(self.delete_selected_script)
        self.view.duplicate_button.clicked.connect(self.duplicate_selected_script)
        self.view.open_scripts_folder_button.clicked.connect(self.open_scripts_folder)
        self.view.save_button.clicked.connect(self.save_current_script)
        self.view.import_script_button.clicked.connect(self.import_scripts)
        self.view.export_selected_button.clicked.connect(self.export_selected_script)
        self.view.import_all_button.clicked.connect(self.import_library_backup)
        self.view.export_all_button.clicked.connect(self.export_library_backup)
        self.view.upload_icon_button.clicked.connect(self.upload_icon)
        self.view.snapshot_button.clicked.connect(self.capture_viewport_snapshot)
        self.view.open_resource_library_button.clicked.connect(self.open_resource_library)
        self.view.add_to_shelf_button.clicked.connect(self.add_selected_to_shelf)
        self.view.edit_script_name_button.clicked.connect(self.rename_selected_script)
        self.view.icon_mode_combo.currentIndexChanged.connect(self.on_icon_mode_changed)
        self.view.show_details_in_use_check_box.toggled.connect(
            self.on_show_details_in_use_toggled
        )
        self.view.auto_save_check_box.toggled.connect(self.on_auto_save_toggled)

        self.view.name_field.textChanged.connect(self.mark_editor_dirty)
        self.view.package_icon_field.textChanged.connect(self.mark_editor_dirty)
        self.view.script_editor.textChanged.connect(self.mark_editor_dirty)
        self.view.description_field.textChanged.connect(self.mark_editor_dirty)
        self.view.visible_check_box.stateChanged.connect(self.mark_editor_dirty)

    def mark_editor_dirty(self, *args):
        """Marks edit fields as containing unsaved changes.

        Args:
            *args: Signal arguments that are intentionally ignored.
        """
        if not self.loading_editor and self.current_script_id:
            self.editor_dirty = True
            if self.model.get_auto_save():
                self.queue_auto_save()
            else:
                self.view.show_status("Unsaved script changes")

    def queue_auto_save(self):
        """Defers one automatic save until the current Qt signal completes."""
        if self.auto_save_pending:
            return
        self.auto_save_pending = True
        ui_qt.QtCore.QTimer.singleShot(0, self.auto_save_current_script)

    def auto_save_current_script(self):
        """Saves pending editor changes when automatic saving remains enabled."""
        self.auto_save_pending = False
        if (
            self.editor_dirty
            and self.current_script_id
            and self.model.get_auto_save()
        ):
            self.save_current_script(silent=True)

    def on_icon_mode_changed(self, *args):
        """Updates icon controls and marks the editor dirty.

        Args:
            *args: Signal arguments that are intentionally ignored.
        """
        icon_mode = self.view.icon_mode_combo.currentData()
        self.view.update_icon_controls(icon_mode)
        self.mark_editor_dirty()

    def on_edit_mode_toggled(self, is_edit_mode):
        """Switches between editing and streamlined use mode.

        Args:
            is_edit_mode (bool): New edit-mode state.
        """
        if not is_edit_mode and self.editor_dirty:
            self.save_current_script(silent=True)
        self.model.set_edit_mode(is_edit_mode)
        self.view.set_edit_mode(
            is_edit_mode, self.model.get_show_details_in_use_mode()
        )
        self.populate_script_list(preferred_id=self.current_script_id)

    def on_show_details_in_use_toggled(self, should_show):
        """Stores the use-mode details preference and refreshes its visibility.

        Args:
            should_show (bool): Whether the use-mode details panel is shown.
        """
        self.model.set_show_details_in_use_mode(should_show)
        self.view.set_edit_mode(self.model.get_edit_mode(), should_show)

    def on_auto_save_toggled(self, should_auto_save):
        """Stores automatic-saving preference and saves current pending edits.

        Args:
            should_auto_save (bool): Whether automatic saving is enabled.
        """
        self.model.set_auto_save(should_auto_save)
        self.view.set_library_preferences(
            self.model.get_show_details_in_use_mode(), should_auto_save
        )
        if should_auto_save and self.editor_dirty:
            self.queue_auto_save()

    def filter_script_list(self, *args):
        """Applies the current search text to the script list.

        Args:
            *args: Signal arguments that are intentionally ignored.
        """
        if self.editor_dirty:
            self.save_current_script(silent=True)
        self.populate_script_list(preferred_id=self.current_script_id)

    def populate_script_list(self, preferred_id=""):
        """Rebuilds the script list for the active mode and search text.

        Args:
            preferred_id (str, optional): Stable script ID to restore after rebuilding.
        """
        include_hidden = self.model.get_edit_mode()
        search_text = self.view.search_bar.text()
        scripts = self.model.search_scripts(
            search_text=search_text,
            include_hidden=include_hidden,
        )
        signals_blocked = self.view.item_list.blockSignals(True)
        try:
            self.view.clear_script_list()
            for item in scripts:
                icon_path = self.model.get_script_icon_path(item)
                icon = ui_qt.QtGui.QIcon(icon_path)
                self.view.add_script_item(
                    item_name=item.nice_name,
                    icon=icon,
                    metadata={"script_id": item.script_id},
                    is_hidden=not item.visible,
                )
            selected = False
            if preferred_id:
                selected = self.view.select_script_id(preferred_id)
            if not selected and self.view.item_list.count():
                self.view.item_list.setCurrentRow(0)
        finally:
            self.view.item_list.blockSignals(signals_blocked)
        self.on_selection_changed()

    def on_selection_changed(self):
        """Saves pending edits and loads the newly selected script."""
        selected_id = self.view.get_selected_script_id()
        if (
            self.editor_dirty
            and self.current_script_id
            and self.current_script_id != selected_id
        ):
            self.save_current_script(silent=True)
        self.current_script_id = selected_id
        if not selected_id:
            self.editor_dirty = False
            self.view.clear_details()
            self.model.set_selected_script_id("")
            return
        item = self.model.get_script(selected_id)
        if not item:
            self.view.clear_details()
            return
        self.loading_editor = True
        try:
            self.view.set_editor_enabled(True)
            self.view.set_editor_data(item, self.model.read_script_content(item))
            self.view.update_use_display(
                nice_name=item.nice_name,
                description=item.description,
                image_path=self.model.get_script_icon_path(item),
            )
        finally:
            self.loading_editor = False
        self.editor_dirty = False
        self.model.set_selected_script_id(selected_id)

    def save_current_script(self, *args, silent=False):
        """Writes the current editor fields and script content through Prefs.

        Args:
            *args: Signal arguments that are intentionally ignored.
            silent (bool, optional): Whether routine success feedback is suppressed.

        Returns:
            bool: True when the selected script was saved.
        """
        if not self.current_script_id:
            if not silent:
                self.view.show_status("Select a script before saving.", warning=True)
            return False
        editor_data = self.view.get_editor_data()
        try:
            item = self.model.update_script(
                script_id=self.current_script_id,
                nice_name=editor_data.get("nice_name"),
                script_content=editor_data.get("script_content"),
                description=editor_data.get("description"),
                visible=editor_data.get("visible"),
                icon_mode=editor_data.get("icon_mode"),
                icon_value=editor_data.get("icon_value"),
            )
        except (KeyError, ValueError, IOError, OSError) as exception:
            self.view.show_status(f"Unable to save script: {exception}", warning=True)
            return False
        self.editor_dirty = False
        self._refresh_selected_list_item(item)
        self.view.update_use_display(
            nice_name=item.nice_name,
            description=item.description,
            image_path=self.model.get_script_icon_path(item),
        )
        if not silent:
            icon_path = self.model.get_script_icon_path(item)
            from gt.ui import resource_library

            if (
                item.icon_mode == ScriptLibraryConstants.ICON_MODE_PACKAGE
                and icon_path == resource_library.Icon.script_library_missing_icon
            ):
                self.view.show_status(
                    "Script saved, but the package icon name could not be resolved.",
                    warning=True,
                )
            else:
                self.view.show_status(f'Saved "{item.nice_name}"')
        return True

    def _refresh_selected_list_item(self, item):
        """Refreshes the selected row after metadata or icon changes.

        Args:
            item (ScriptLibraryItem): Updated script item.
        """
        list_item = None
        for index in range(self.view.item_list.count()):
            candidate = self.view.item_list.item(index)
            metadata = candidate.data(ui_qt.QtLib.ItemDataRole.UserRole) or {}
            if metadata.get("script_id") == item.script_id:
                list_item = candidate
                break
        if not list_item:
            return
        list_item.setText(item.nice_name)
        list_item.setIcon(ui_qt.QtGui.QIcon(self.model.get_script_icon_path(item)))
        if item.visible:
            from gt.ui import resource_library

            list_item.setForeground(
                ui_qt.QtGui.QColor(resource_library.Color.Hex.white)
            )
            list_item.setToolTip("")
        else:
            from gt.ui import resource_library

            list_item.setForeground(
                ui_qt.QtGui.QColor(resource_library.Color.Hex.gray_lighter)
            )
            list_item.setToolTip("Hidden in Use Mode")

    def add_script(self):
        """Creates a new script and opens it in edit mode."""
        if self.editor_dirty:
            self.save_current_script(silent=True)
        requested_name, accepted = ui_qt.QtWidgets.QInputDialog.getText(
            self.view,
            "Add Script",
            "Script Name:",
            text=ScriptLibraryConstants.DEFAULT_SCRIPT_NAME,
        )
        if not accepted:
            return
        requested_name = str(requested_name or "").strip()
        if not requested_name:
            self.view.show_status("Script name cannot be empty.", warning=True)
            return
        if self.model.has_script_name_conflict(requested_name):
            self.view.show_status(
                f'A script named "{requested_name}" already exists.', warning=True
            )
            return
        try:
            item = self.model.create_script(
                nice_name=requested_name,
                script_content=ScriptLibraryConstants.DEFAULT_SCRIPT_CONTENT,
            )
        except (ValueError, IOError, OSError) as exception:
            self.view.show_status(f"Unable to create script: {exception}", warning=True)
            return
        if not self.model.get_edit_mode():
            self.model.set_edit_mode(True)
            self.view.set_edit_mode(
                True, self.model.get_show_details_in_use_mode()
            )
        self.populate_script_list(preferred_id=item.script_id)
        self.view.name_field.setFocus()
        self.view.name_field.selectAll()
        self.view.show_status("New script created.")

    def rename_selected_script(self):
        """Prompts for and applies a managed script-file rename.

        Nice Name remains a separate display-only value and is not changed.
        """
        item = self.model.get_script(self.current_script_id)
        if not item:
            self.view.show_status("Select a script before renaming.", warning=True)
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        current_file_stem = os.path.splitext(item.file_name)[0]
        requested_name = self.get_script_file_name_from_user(current_file_stem)
        if requested_name is None:
            return
        try:
            renamed_item = self.model.rename_script(item.script_id, requested_name)
        except (KeyError, ValueError, IOError, OSError) as exception:
            self.view.show_status(f"Unable to rename script: {exception}", warning=True)
            return
        self.populate_script_list(preferred_id=renamed_item.script_id)
        self.view.show_status(f'Renamed script file to "{renamed_item.file_name}"')

    def get_script_file_name_from_user(self, current_file_stem):
        """Prompts for a script file name without allowing the extension to change.

        Args:
            current_file_stem (str): Current script file name without ``.py``.

        Returns:
            str or None: Requested file stem, or None when the dialog is cancelled.
        """
        dialog = ui_qt.QtWidgets.QDialog(self.view)
        dialog.setWindowTitle("Edit Script File Name")
        dialog.setWindowIcon(self.view.windowIcon())
        dialog.setModal(True)
        dialog_layout = ui_qt.QtWidgets.QVBoxLayout(dialog)
        explanation_label = ui_qt.QtWidgets.QLabel(
            "Change the saved script file name. This does not change Nice Name."
        )
        explanation_label.setWordWrap(True)
        dialog_layout.addWidget(explanation_label)
        file_name_layout = ui_qt.QtWidgets.QHBoxLayout()
        file_name_label = ui_qt.QtWidgets.QLabel("Script File Name:")
        file_name_field = ui_qt.QtWidgets.QLineEdit(str(current_file_stem or ""))
        file_name_field.setToolTip("Name of the managed Python file without its extension.")
        extension_label = ui_qt.QtWidgets.QLabel(".py")
        extension_label.setToolTip("Python script extension. This extension cannot be changed here.")
        file_name_layout.addWidget(file_name_label)
        file_name_layout.addWidget(file_name_field, 1)
        file_name_layout.addWidget(extension_label)
        dialog_layout.addLayout(file_name_layout)
        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        cancel_button = ui_qt.QtWidgets.QPushButton("Cancel")
        confirm_button = ui_qt.QtWidgets.QPushButton("Rename File")
        cancel_button.setToolTip("Cancel without changing the script file name.")
        confirm_button.setToolTip("Rename the managed .py file and any managed image.")
        cancel_button.clicked.connect(dialog.reject)
        confirm_button.clicked.connect(dialog.accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(confirm_button)
        dialog_layout.addLayout(button_layout)
        file_name_field.selectAll()
        file_name_field.setFocus()
        if hasattr(dialog, "exec"):
            accepted = dialog.exec()
        else:
            accepted = dialog.exec_()
        if not accepted:
            return None
        requested_name = str(file_name_field.text() or "").strip()
        if requested_name.lower().endswith(ScriptLibraryConstants.SCRIPT_EXTENSION):
            requested_name = requested_name[: -len(ScriptLibraryConstants.SCRIPT_EXTENSION)]
        return requested_name

    def delete_selected_script(self):
        """Confirms and deletes the selected script and managed assets."""
        item = self.model.get_script(self.current_script_id)
        if not item:
            self.view.show_status("Select a script before deleting.", warning=True)
            return
        user_choice = ui_qt.QtWidgets.QMessageBox.question(
            self.view,
            "Delete Script?",
            f'Delete "{item.nice_name}" and its managed custom icon or viewport snapshot, if present?\n\n'
            "This action cannot be undone.",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        if user_choice != ui_qt.QtLib.StandardButton.Yes:
            return
        deleted_name = item.nice_name
        try:
            self.model.delete_script(item.script_id)
        except OSError as exception:
            self.view.show_status(f"Unable to delete script: {exception}", warning=True)
            return
        self.current_script_id = ""
        self.editor_dirty = False
        self.populate_script_list()
        self.view.show_status(f'Deleted "{deleted_name}"')

    def duplicate_selected_script(self):
        """Duplicates the selected script and its managed icon."""
        if not self.current_script_id:
            self.view.show_status("Select a script before duplicating.", warning=True)
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        try:
            duplicate = self.model.duplicate_script(self.current_script_id)
        except (KeyError, IOError, OSError, ValueError) as exception:
            self.view.show_status(f"Unable to duplicate script: {exception}", warning=True)
            return
        self.populate_script_list(preferred_id=duplicate.script_id)
        self.view.show_status(f'Created "{duplicate.nice_name}"')

    def open_scripts_folder(self):
        """Opens the Prefs-managed scripts folder in the system file browser."""
        scripts_dir = os.path.abspath(self.model.get_scripts_dir())
        try:
            if not os.path.isdir(scripts_dir):
                raise IOError("The scripts folder could not be created.")
            if os.name == "nt":
                windows_directory = os.environ.get("WINDIR", r"C:\\Windows")
                explorer_path = os.path.join(windows_directory, "explorer.exe")
                subprocess.Popen([explorer_path, scripts_dir])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", scripts_dir])
            else:
                subprocess.Popen(["xdg-open", scripts_dir])
        except Exception as exception:
            self.view.show_status(f"Unable to open scripts folder: {exception}", warning=True)
            return
        self.view.show_status(f'Opened scripts folder: "{scripts_dir}"')

    def open_selected_script(self):
        """Opens the selected managed Python script in the operating system."""
        item = self.model.get_script(self.current_script_id)
        if not item:
            self.view.show_status("Select a script before opening it.", warning=True)
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        script_path = self.model.get_script_path(item)
        if not script_path or not os.path.isfile(script_path):
            self.view.show_status("The selected script file is missing.", warning=True)
            return
        try:
            if os.name == "nt":
                os.startfile(script_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", script_path])
            else:
                subprocess.Popen(["xdg-open", script_path])
        except Exception as exception:
            self.view.show_status(f"Unable to open script: {exception}", warning=True)
            return
        self.view.show_status(f'Opened "{item.nice_name}"')

    def show_script_context_menu(self, position):
        """Shows selected-script actions from a list-item right-click.

        Args:
            position (QPoint): Point in the script-list viewport coordinate space.
        """
        list_item = self.view.item_list.itemAt(position)
        if not list_item:
            return
        self.view.item_list.setCurrentItem(list_item)
        self.script_context_menu = ui_qt.QtWidgets.QMenu(self.view)
        run_action = self.script_context_menu.addAction("Run Script")
        run_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        run_action.setToolTip("Run the selected script.")
        open_action = self.script_context_menu.addAction("Open Script")
        open_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        open_action.setToolTip("Open the selected Python script in its default editor.")
        shelf_action = self.script_context_menu.addAction("Add to Shelf")
        shelf_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_shelf))
        shelf_action.setToolTip("Add a shortcut for the selected script to the Maya shelf.")
        run_action.triggered.connect(self.run_selected_script)
        open_action.triggered.connect(self.open_selected_script)
        shelf_action.triggered.connect(self.add_selected_to_shelf)
        if self.model.get_edit_mode():
            self.script_context_menu.addSeparator()
            duplicate_action = self.script_context_menu.addAction("Duplicate")
            duplicate_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_duplicate))
            duplicate_action.setToolTip("Duplicate the selected script and managed image.")
            delete_action = self.script_context_menu.addAction("Delete")
            delete_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_remove))
            delete_action.setToolTip("Delete the selected script and managed image.")
            duplicate_action.triggered.connect(self.duplicate_selected_script)
            delete_action.triggered.connect(self.delete_selected_script)
        global_position = self.view.item_list.viewport().mapToGlobal(position)
        if hasattr(self.script_context_menu, "exec"):
            self.script_context_menu.exec(global_position)
        else:
            self.script_context_menu.exec_(global_position)

    def run_selected_script(self):
        """Executes the selected script and reports errors without closing the tool."""
        if not self.current_script_id:
            self.view.show_status("Select a script before running.", warning=True)
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        item = self.model.get_script(self.current_script_id)
        try:
            self.model.execute_script(self.current_script_id)
        except Exception as exception:
            logger.error(traceback.format_exc())
            self.view.show_status(
                f'Failed to run "{item.nice_name if item else "script"}": {exception}',
                warning=True,
            )
            return
        self.view.show_status(f'Executed "{item.nice_name}"')

    def upload_icon(self):
        """Copies an icon file beside the selected script."""
        if not self.current_script_id:
            return
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Choose Script Icon",
            starting_directory=self.model.get_last_directory(),
            file_filter="Images (*.svg *.png *.jpg *.jpeg *.bmp *.ico)",
        )
        if not file_path:
            return
        self.model.set_last_directory(os.path.dirname(file_path))
        try:
            icon_path = self.model.attach_custom_icon(self.current_script_id, file_path)
        except (KeyError, ValueError, IOError, OSError) as exception:
            self.view.show_status(f"Unable to upload icon: {exception}", warning=True)
            return
        self.loading_editor = True
        try:
            self.view.set_editor_icon(
                ScriptLibraryConstants.ICON_MODE_CUSTOM,
                os.path.basename(icon_path),
            )
        finally:
            self.loading_editor = False
        self.editor_dirty = False
        self._refresh_current_item_from_model()
        self.view.show_status(f'Icon copied to "{icon_path}"')

    def capture_viewport_snapshot(self):
        """Captures the Maya viewport as the selected script icon."""
        item = self.model.get_script(self.current_script_id)
        if not item:
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        script_stem = os.path.splitext(item.file_name)[0]
        try:
            from gt.core.playblast import render_viewport_snapshot

            snapshot_path = render_viewport_snapshot(
                file_name=f"{script_stem}_snapshot",
                target_dir=self.model.get_scripts_dir(),
            )
            if not snapshot_path:
                raise IOError("Maya did not generate a viewport image.")
            managed_path = self.model.attach_snapshot(item.script_id, snapshot_path)
        except Exception as exception:
            logger.error(traceback.format_exc())
            self.view.show_status(f"Unable to capture snapshot: {exception}", warning=True)
            return
        self.loading_editor = True
        try:
            self.view.set_editor_icon(
                ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
                os.path.basename(managed_path),
            )
        finally:
            self.loading_editor = False
        self.editor_dirty = False
        self._refresh_current_item_from_model()
        self.view.show_status(f'Snapshot saved to "{managed_path}"')

    def _refresh_current_item_from_model(self):
        """Refreshes list and preview data for the current model item."""
        item = self.model.get_script(self.current_script_id)
        if not item:
            return
        self._refresh_selected_list_item(item)
        self.view.update_use_display(
            nice_name=item.nice_name,
            description=item.description,
            image_path=self.model.get_script_icon_path(item),
        )

    def open_resource_library(self):
        """Opens Resource Library so users can inspect package icon names."""
        try:
            from gt.utils.system import initialize_tool

            initialize_tool("resource_library")
        except Exception as exception:
            self.view.show_status(
                f"Unable to open Resource Library: {exception}", warning=True
            )
            return
        self.view.show_status(
            "Resource Library opened. Type or copy an Icon attribute name into Package Icon."
        )

    def add_selected_to_shelf(self):
        """Adds a shelf shortcut that resolves the latest stored script by ID."""
        item = self.model.get_script(self.current_script_id)
        if not item:
            self.view.show_status("Select a script before adding it to the shelf.", warning=True)
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        command = (
            "from gt.tools.script_library.script_library_model import run_script_by_id\n"
            f"run_script_by_id({item.script_id!r})"
        )
        try:
            from gt.core.misc import create_shelf_button

            shelf_button = create_shelf_button(
                command=command,
                label=item.nice_name[:8],
                tooltip=item.description or f'Run Script Library item "{item.nice_name}".',
                image=self.model.get_script_icon_path(item),
            )
        except Exception as exception:
            logger.error(traceback.format_exc())
            self.view.show_status(
                f"Unable to add shelf button: {exception}", warning=True
            )
            return
        if not shelf_button:
            self.view.show_status("Maya did not create the shelf button.", warning=True)
            return
        self.view.show_status(f'Added "{item.nice_name}" to the current shelf')

    def export_selected_script(self):
        """Exports the selected script to a self-contained compressed archive."""
        item = self.model.get_script(self.current_script_id)
        if not item:
            self.view.show_status("Select a script before exporting.", warning=True)
            return
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        file_stem = self.model.sanitize_file_stem(item.nice_name)
        starting_path = os.path.join(self.model.get_last_directory(), file_stem)
        target_path = ui_file_dialog.file_dialog(
            parent=self.view,
            write_mode=True,
            caption="Export Script",
            starting_directory=starting_path,
            file_filter="GT Script (*.gtscript)",
        )
        if not target_path:
            return
        try:
            archive_path = self.model.export_script(item.script_id, target_path)
        except (KeyError, IOError, OSError, ValueError) as exception:
            self.view.show_status(f"Unable to export script: {exception}", warning=True)
            return
        self.model.set_last_directory(os.path.dirname(archive_path))
        self.view.show_status(f'Exported script to "{archive_path}"')

    def export_library_backup(self):
        """Exports every script and managed icon as one compressed backup."""
        if self.editor_dirty and not self.save_current_script(silent=True):
            return
        starting_path = os.path.join(
            self.model.get_last_directory(), "script_library_backup"
        )
        target_path = ui_file_dialog.file_dialog(
            parent=self.view,
            write_mode=True,
            caption="Export Script Library Backup",
            starting_directory=starting_path,
            file_filter="GT Script Library (*.gtscriptlib)",
        )
        if not target_path:
            return
        try:
            archive_path = self.model.export_all(target_path)
        except (IOError, OSError, ValueError) as exception:
            self.view.show_status(f"Unable to export backup: {exception}", warning=True)
            return
        self.model.set_last_directory(os.path.dirname(archive_path))
        self.view.show_status(f'Exported {len(self.model.scripts)} scripts to "{archive_path}"')

    def import_scripts(self):
        """Imports one or more raw Python files or per-script archives."""
        file_paths = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Import Scripts",
            starting_directory=self.model.get_last_directory(),
            file_filter="Scripts (*.py *.gtscript)",
            multiple_files=True,
        )
        if not file_paths:
            return
        imported_ids = []
        skipped_count = 0
        for file_path in file_paths:
            try:
                if file_path.lower().endswith(ScriptLibraryConstants.SCRIPT_EXTENSION):
                    item = self.model.import_python_file(file_path)
                    imported_ids.append(item.script_id)
                else:
                    result = self.model.import_archive(file_path, conflict_policy="copy")
                    imported_ids.extend(result.get("imported", []))
                    imported_ids.extend(result.get("replaced", []))
                    skipped_count += len(result.get("skipped", []))
            except (IOError, OSError, ValueError) as exception:
                logger.warning(f'Unable to import "{file_path}": {exception}')
                skipped_count += 1
        self.model.set_last_directory(os.path.dirname(file_paths[0]))
        preferred_id = imported_ids[-1] if imported_ids else self.current_script_id
        self.populate_script_list(preferred_id=preferred_id)
        self.view.show_status(
            f"Imported {len(imported_ids)} script(s); skipped {skipped_count}."
        )

    def import_library_backup(self):
        """Imports a full backup, replacing matching stable IDs after confirmation."""
        archive_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Import Script Library Backup",
            starting_directory=self.model.get_last_directory(),
            file_filter="GT Script Library (*.gtscriptlib)",
        )
        if not archive_path:
            return
        try:
            summary = self.model.get_archive_summary(archive_path)
        except (IOError, OSError, ValueError) as exception:
            self.view.show_status(f"Unable to read backup: {exception}", warning=True)
            return
        conflicts = summary.get("conflicts", [])
        if conflicts:
            user_choice = ui_qt.QtWidgets.QMessageBox.question(
                self.view,
                "Replace Matching Scripts?",
                f"This backup contains {len(conflicts)} script(s) with matching stable IDs.\n\n"
                "Replace those scripts with the backup versions? Other scripts are preserved.",
                ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
                ui_qt.QtLib.StandardButton.No,
            )
            if user_choice != ui_qt.QtLib.StandardButton.Yes:
                return
        try:
            result = self.model.import_archive(archive_path, conflict_policy="replace")
        except (IOError, OSError, ValueError) as exception:
            self.view.show_status(f"Unable to import backup: {exception}", warning=True)
            return
        self.model.set_last_directory(os.path.dirname(archive_path))
        imported_ids = result.get("imported", []) + result.get("replaced", [])
        preferred_id = imported_ids[-1] if imported_ids else self.current_script_id
        self.populate_script_list(preferred_id=preferred_id)
        self.view.show_status(
            f"Backup import complete: {len(result.get('imported', []))} added, "
            f"{len(result.get('replaced', []))} replaced, "
            f"{len(result.get('skipped', []))} skipped."
        )

    def on_view_close(self):
        """Persists pending editor and splitter state when the view closes."""
        if self.editor_dirty:
            self.save_current_script(silent=True)
        if self.view.splitter:
            self.model.set_splitter_sizes(self.view.splitter.sizes())
        sys.stdout.write("Script Library state saved.\n")


if __name__ == "__main__":
    print('Run Script Library from its package "launch_tool" entry point.')
