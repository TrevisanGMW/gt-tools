import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rigger_path_utils as tools_rig_path_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.utils.system as utils_sys
import gt.core.material as core_mat
import gt.ui.qt_import as ui_qt
import gt.core.str as core_str
import gt.core.io as core_io
import maya.cmds as cmds
import subprocess
import textwrap
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ProjectContextPathWidget(ui_qt.QtWidgets.QWidget):
    """
    A custom QWidget that combines a label, a line edit for path input, and
    buttons for a file dialog and environment variable feedback.
    """

    text_changed = ui_qt.QtCore.Signal(str)

    def __init__(
        self,
        nice_name,
        default_text,
        project,
        dir_only=False,
        ok_caption="Set Path",
        file_filter="All Files (*)",
        parent=None,
    ):
        """
        Initializes the ProjectContextPathWidget.

        Args:
            nice_name (str): The display label for the widget.
            default_text (str): The initial text to populate in the line edit (e.g., "{project-dir}/...").
            project (obj): The project instance used to resolve environment variables.
            dir_only (bool, optional): If True, the file dialog will restrict selection to directories.
                                       Defaults to False.
            ok_caption (str, optional): The caption text for the file dialog's confirmation button.
                                        Defaults to "Set Path".
            file_filter (str, optional): The file filter string for the dialog. Defaults to "All Files (*)".
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super(ProjectContextPathWidget, self).__init__(parent)

        self._project = project
        self.dir_only = dir_only
        self.ok_caption = ok_caption
        self.file_filter = file_filter

        self.tooltip = self._generate_tooltip()

        self.setLayout(ui_qt.QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Widgets
        self.label = ui_qt.QtWidgets.QLabel(f"{nice_name}:")
        self.text_field = ui_qt_utils.ConfirmableQLineEdit()
        self.path_btn = ui_qt.QtWidgets.QPushButton()
        self.env_var_btn = ui_qt.QtWidgets.QPushButton()

        self.text_field.setText(default_text)
        self.text_field.setFixedHeight(35)
        self.text_field.setPlaceholderText(default_text)

        self.path_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        self.path_btn.setToolTip("Use file dialog to set path")
        self.path_btn.setFixedWidth(30)

        self.env_var_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        self.env_var_btn.setToolTip("Get more information about the current path.")
        self.env_var_btn.setFixedWidth(30)

        # Set Tooltips
        self.label.setToolTip(self.tooltip)
        self.text_field.setToolTip(self.tooltip)

        # Add to Layout
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.text_field)
        self.layout().addWidget(self.env_var_btn)
        self.layout().addWidget(self.path_btn)

        # Connections
        self.text_field.textChanged.connect(self.text_changed.emit)
        self.path_btn.clicked.connect(self._open_file_dialog)
        self.env_var_btn.clicked.connect(self._open_env_var_feedback_dialog)

    def text(self):
        """
        Retrieves the current text from the path input field.

        Returns:
            str: The raw string currently in the line edit.
        """
        return self.text_field.text()

    def set_text(self, new_text):
        """
        Sets the text of the path input field.

        Args:
            new_text (str): The string to set in the line edit.
        """
        self.text_field.setText(new_text)

    @staticmethod
    def _generate_tooltip():
        """
        Generates the rich tooltip string listing supported environment variables.

        Returns:
            str: A formatted string describing available environment variables.
        """
        return textwrap.dedent(
            """\
            Environment Variables:
            "{project-dir}": The path set in the auto rigger project.
            "{project-name}": The name of the project.
            "{scene-dir}": The directory of the current scene (if saved).
            ... and many others (check auto rigger docs)
            """
        )

    def parse_path(self, path):
        """
        Resolves environment variables in the provided path using the RigProject context.

        Args:
            path (str): The path string containing environment variables (e.g., "{project-dir}/geo").

        Returns:
            str: The absolute, normalized system path with variables resolved.
        """
        environment_vars_dict = tools_rig_frm.get_environment_variables(rig_project=self._project)
        path = core_str.replace_keys_with_values(path, environment_vars_dict)
        return os.path.normpath(path).replace("\\", "/")

    def _open_file_dialog(self):
        """
        Opens a Maya file dialog (directory or file) and updates the QLineEdit with the selected path.
        """
        file_mode = 3 if self.dir_only else 1
        start_path = self.parse_path(self.text()) or os.path.expanduser("~")

        try:
            paths = cmds.fileDialog2(
                fileFilter=self.file_filter,
                dialogStyle=2,
                fm=file_mode,
                caption=self.ok_caption,
                startingDirectory=os.path.dirname(start_path),
            )
            if paths:
                self.set_text(paths[0].replace("\\", "/"))
        except Exception as e:
            logger.error(f"File dialog failed: {e}")

    def _open_env_var_feedback_dialog(self):
        """Opens a detailed window with information about the resolved path."""
        configured_path = self.text_field.text()
        parsed_path = self.parse_path(path=configured_path)
        tools_rig_path_utils.show_path_information(
            parent=self,
            configured_path=configured_path,
            parsed_path=parsed_path,
            title="Path Information",
        )


class GeometryPreprocessor(ui_qt.QtWidgets.QDialog):
    """
    Main UI dialog for managing geometry and texture migration within a rigging project.
    """

    def __init__(self, project=None, parent=None):
        """
        Initializes the GeometryPreprocessor.

        Args:
            project (obj, optional): The rigging project instance associated with this session. Defaults to None.
            parent (QWidget, optional): The parent widget for this dialog. Defaults to None.
        """
        super().__init__(parent)
        self._project = project

        self.setWindowTitle("Geometry Preprocessor")
        self.setMinimumWidth(590)

        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_geo_preprocessor))

        # Internal state variables
        self.texture_data = {}
        self.current_outside_count = 0
        self.current_missing_count = 0
        self.current_total_files = 0

        self._create_widgets()
        self._create_layout()
        self._create_connections()

        self._refresh_compression_status(log_feedback=False)
        self._refresh_texture_status()

    # --- Path Resolution & Context ---
    def get_resolved_path(self, path_string):
        """
        Resolves the path string using the dedicated ProjectContextPathWidget's parser.

        Args:
            path_string (str): The raw path string containing environment variables.

        Returns:
            str: The resolved absolute path.
        """
        return self.texture_target_path_widget.parse_path(path_string)

    # --- UI Creation ---
    def _create_widgets(self):
        """
        Initializes all widgets for the dialog.
        """

        # --- 1. Texture Migration Section Widgets ---
        default_tex_path = f"{project-dir}/textures"
        self.texture_target_path_widget = ProjectContextPathWidget(
            nice_name="Texture Target",
            default_text=default_tex_path,
            project=self._project,
            dir_only=True,
            ok_caption="Select Texture Folder",
        )

        # Status Labels
        status_names = ["found", "outside", "missing", "in_target"]
        self.status_labels = {name: ui_qt.QtWidgets.QLabel("...") for name in status_names}

        # Migration/Status Buttons
        self.refresh_tex_btn = ui_qt.QtWidgets.QPushButton("Refresh Status")
        self.remove_missing_btn = ui_qt.QtWidgets.QPushButton("Remove Missing Paths")  # Added button
        self.migrate_btn = ui_qt.QtWidgets.QPushButton("Migrate Textures")

        # --- 2. Target Texture Dir Analysis Section Widgets ---
        self.refresh_compress_btn = ui_qt.QtWidgets.QPushButton("Refresh Size Analysis")
        self.open_target_dir_btn = ui_qt.QtWidgets.QPushButton("Open Target Dir")
        self.open_target_dir_btn.setToolTip("Open target texture directory.")

        # Compression Status Labels
        compress_names = ["total_files", "total_size_mb"]
        self.compress_labels = {name: ui_qt.QtWidgets.QLabel("...") for name in compress_names}

        self.compress_action_btn = None

        # --- 3. Clean-up Section Widgets ---
        self.delete_namespaces_btn = ui_qt.QtWidgets.QPushButton("Delete Namespaces")
        self.delete_display_layers_btn = ui_qt.QtWidgets.QPushButton("Delete Display Layers")
        self.delete_unused_nodes_btn = ui_qt.QtWidgets.QPushButton("Delete Unused Nodes")
        self.delete_keyframes_btn = ui_qt.QtWidgets.QPushButton("Delete Keyframes")
        self.reset_persp_cam_btn = ui_qt.QtWidgets.QPushButton('Reset "persp" Camera')

        # --- 4. Save Geometry Section Widgets ---
        default_geo_path = f"{project-dir}/geo/{project-name}.ma"
        self.geo_target_path_widget = ProjectContextPathWidget(
            nice_name=core_str.snake_to_title("Maya_File_Target"),
            default_text=default_geo_path,
            project=self._project,
            dir_only=False,
            ok_caption="Save Geometry As",
            file_filter="Maya ASCII (*.ma);;Maya Binary (*.mb)",
        )

        self.bypass_checkbox = ui_qt.QtWidgets.QCheckBox("Bypass Migration Check")  # Renamed
        self.bypass_checkbox.setChecked(False)

        self.open_geo_dir_btn = ui_qt.QtWidgets.QPushButton("Open Geo Dir")
        self.open_geo_dir_btn.setToolTip("Open project geometry directory.")

        self.save_scene_btn = ui_qt.QtWidgets.QPushButton("Save Geometry Scene")
        self.save_scene_btn.setStyleSheet("font: bold; padding: 10px;")
        self.save_scene_btn.setEnabled(False)

    def _create_layout(self):
        """
        Arranges widgets into the main layout using QGroupBoxes.
        """
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)

        # --- 1. Texture Migration Group ---
        texture_group = ui_qt.QtWidgets.QGroupBox("Texture Location")
        texture_layout = ui_qt.QtWidgets.QVBoxLayout(texture_group)

        texture_layout.addWidget(self.texture_target_path_widget)

        # Status Grid
        status_grid = ui_qt.QtWidgets.QGridLayout()
        status_grid.addWidget(ui_qt.QtWidgets.QLabel("Textures Found:"), 0, 0)
        status_grid.addWidget(self.status_labels["found"], 0, 1)
        status_grid.addWidget(ui_qt.QtWidgets.QLabel("Already in Target:"), 0, 2)
        status_grid.addWidget(self.status_labels["in_target"], 0, 3)

        status_grid.addWidget(ui_qt.QtWidgets.QLabel("Outside Target:"), 1, 0)
        status_grid.addWidget(self.status_labels["outside"], 1, 1)
        status_grid.addWidget(ui_qt.QtWidgets.QLabel("Missing Files:"), 1, 2)
        status_grid.addWidget(self.status_labels["missing"], 1, 3)
        texture_layout.addLayout(status_grid)

        # --- Migration Actions (Reordered) ---

        # Row 1: Refresh Status (1st)
        texture_layout.addWidget(self.refresh_tex_btn)

        # Row 2: Remove Missing Paths (2nd)
        texture_layout.addWidget(self.remove_missing_btn)

        # Row 3: Migrate Textures (3rd)
        texture_layout.addWidget(self.migrate_btn)

        main_layout.addWidget(texture_group)

        # --- 2. Target Texture Dir Analysis Group ---
        compression_group = ui_qt.QtWidgets.QGroupBox("Target Texture Dir Analysis")
        compression_layout = ui_qt.QtWidgets.QVBoxLayout(compression_group)

        compress_grid = ui_qt.QtWidgets.QGridLayout()
        compress_grid.addWidget(ui_qt.QtWidgets.QLabel("Total Image Files:"), 0, 0)
        compress_grid.addWidget(self.compress_labels["total_files"], 0, 1)
        compress_grid.addWidget(ui_qt.QtWidgets.QLabel("Total Size (MB):"), 1, 0)
        compress_grid.addWidget(self.compress_labels["total_size_mb"], 1, 1)
        compression_layout.addLayout(compress_grid)

        # Analysis Action Row (Refresh + Open Dir)
        analysis_action_layout = ui_qt.QtWidgets.QHBoxLayout()
        analysis_action_layout.addWidget(self.refresh_compress_btn)
        analysis_action_layout.addWidget(self.open_target_dir_btn)  # Added

        compression_layout.addLayout(analysis_action_layout)

        main_layout.addWidget(compression_group)

        # --- 3. Clean-up Groupbox ---
        cleanup_group = ui_qt.QtWidgets.QGroupBox("Clean-up")
        cleanup_layout = ui_qt.QtWidgets.QVBoxLayout(cleanup_group)

        cleanup_btn_layout = ui_qt.QtWidgets.QGridLayout()
        cleanup_btn_layout.addWidget(self.delete_namespaces_btn, 0, 0)
        cleanup_btn_layout.addWidget(self.delete_display_layers_btn, 0, 1)
        cleanup_btn_layout.addWidget(self.delete_unused_nodes_btn, 1, 0)
        cleanup_btn_layout.addWidget(self.delete_keyframes_btn, 1, 1)
        cleanup_btn_layout.addWidget(self.reset_persp_cam_btn, 2, 0, 1, 2)

        cleanup_layout.addLayout(cleanup_btn_layout)
        main_layout.addWidget(cleanup_group)

        # --- 4. Save Geometry Group ---
        save_group = ui_qt.QtWidgets.QGroupBox("Save Geometry File")
        save_layout = ui_qt.QtWidgets.QVBoxLayout(save_group)

        save_layout.addWidget(self.geo_target_path_widget)

        bypass_layout = ui_qt.QtWidgets.QHBoxLayout()
        bypass_layout.addWidget(self.bypass_checkbox)
        bypass_layout.addWidget(self.open_geo_dir_btn)

        save_layout.addLayout(bypass_layout)
        save_layout.addWidget(self.save_scene_btn)

        main_layout.addWidget(save_group)

    def _create_connections(self):
        """
        Connects signals to slots for all UI elements.
        """
        self.refresh_tex_btn.clicked.connect(self._refresh_texture_status)
        self.migrate_btn.clicked.connect(self._execute_texture_migration)
        self.remove_missing_btn.clicked.connect(self._execute_remove_missing_paths)
        self.refresh_compress_btn.clicked.connect(lambda: self._refresh_compression_status(log_feedback=True))
        self.save_scene_btn.clicked.connect(self._save_geometry_scene)

        self.bypass_checkbox.stateChanged.connect(
            lambda: self._update_save_button_state(self.current_outside_count, self.current_missing_count)
        )
        self.texture_target_path_widget.text_changed.connect(self._refresh_texture_status)

        # Directory Openers
        self.open_target_dir_btn.clicked.connect(self._open_target_texture_directory)
        self.open_geo_dir_btn.clicked.connect(self._open_project_geometry_directory)

        # Connect Clean-up buttons to dedicated methods
        self.delete_namespaces_btn.clicked.connect(self._delete_namespaces)
        self.delete_display_layers_btn.clicked.connect(self._delete_display_layers)
        self.delete_unused_nodes_btn.clicked.connect(self._delete_unused_nodes)
        self.delete_keyframes_btn.clicked.connect(self._delete_keyframes)
        self.reset_persp_cam_btn.clicked.connect(self._reset_persp_camera)

    # --- CLEANUP IMPLEMENTATION ---
    @staticmethod
    def _delete_namespaces():
        """
        Deletes all namespaces in the scene except reserved ones (UI, shared).
        """
        import gt.core.namespace as core_nspace

        core_nspace.delete_namespaces()
        # cmds.inViewMessage(m="Cleanup: Deleting Namespaces...", pos="topCenter", fadeTime=1000)

    @staticmethod
    def _delete_display_layers():
        """
        Deletes all display layers in the scene, moving objects to the default layer.
        """
        import gt.core.display as core_display

        core_display.delete_display_layers()
        # cmds.inViewMessage(m="Cleanup: Deleting Display Layers...", pos="topCenter", fadeTime=1000)

    @staticmethod
    def _delete_unused_nodes():
        """
        Deletes unused dependency nodes to optimize scene size and remove errors.
        """
        import gt.core.cleanup as core_cleanup

        core_cleanup.delete_unused_nodes()
        # cmds.inViewMessage(m="Cleanup: Deleting Unused Nodes...", pos="topCenter", fadeTime=1000)

    @staticmethod
    def _delete_keyframes():
        """
        Deletes all keyframes and animation data in the scene.
        """
        import gt.core.anim as core_anim

        core_anim.delete_time_keyframes()
        cmds.inViewMessage(m="Cleanup: Deleting Keyframes...", pos="topCenter", fadeTime=1000)
        # Real implementation: cmds.cutKey(clear=True, animation='keys')

    @staticmethod
    def _reset_persp_camera():
        """
        Resets the 'persp' camera's position, rotation, and field of view to default values.
        """
        import gt.core.camera as core_cam

        core_cam.reset_camera_attributes()

    # --- DIRECTORY OPENERS ---
    def _open_target_texture_directory(self):
        """
        Opens the resolved target texture directory in the OS file explorer.
        """
        path_string = self.texture_target_path_widget.text()
        resolved_path = self.get_resolved_path(path_string)

        if os.path.exists(resolved_path) and os.path.isdir(resolved_path):
            os.startfile(resolved_path) if os.name == "nt" else subprocess.call(["open", resolved_path])
            logger.info(f"Opened texture directory: {resolved_path}")
        else:
            cmds.warning(f"Directory does not exist: {resolved_path}")

    def _open_project_geometry_directory(self):
        """
        Opens the directory containing the resolved geometry file path in the OS file explorer.
        """
        path_string = self.geo_target_path_widget.text()
        resolved_path = self.get_resolved_path(path_string)
        target_dir = os.path.dirname(resolved_path)

        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            os.startfile(target_dir) if os.name == "nt" else subprocess.call(["open", target_dir])
            logger.info(f"Opened geometry directory: {target_dir}")
        else:
            cmds.warning(f"Directory does not exist: {target_dir}")

    # --- MIGRATION FLOW ---
    def _execute_remove_missing_paths(self):
        """
        Executes the texture cleanup, deleting file nodes that have
        missing or empty paths, without performing any file copying (migration).
        """
        target_dir_str = self.texture_target_path_widget.text()
        target_dir = self.get_resolved_path(target_dir_str)

        if self.current_missing_count == 0:
            cmds.warning("No missing or empty paths detected for removal.")
            return

        # 1. Filter the current data to ONLY include missing/empty nodes
        nodes_for_deletion = {}
        for node_name, path_list in self.texture_data.items():
            # Check for explicitly missing/empty status
            is_empty_path = not path_list or (len(path_list) == 1 and not path_list[0])
            is_broken_path = not is_empty_path and not os.path.exists(path_list[0])

            if is_empty_path or is_broken_path:
                # Include the node and its (empty/broken) path list
                nodes_for_deletion[node_name] = path_list

        # 2. Call the core function, forcing deletion (remove_missing_nodes=True)
        migration_report = core_mat.migrate_textures_to_directory(
            nodes_for_deletion, target_dir, remove_missing_nodes=True
        )

        removed_count = len(migration_report.get("removed_nodes", []))

        if removed_count > 0:
            logger.info(f"Successfully DELETED {removed_count} file nodes with missing/empty paths.")
        else:
            cmds.warning("Failed to delete any missing nodes.")

        # 3. Refresh status to update UI
        self._refresh_texture_status()

    def _execute_texture_migration(self):
        """
        Executes the texture migration, copying outside textures to the target directory
        and updating the file nodes in the scene. Refreshes status upon completion.
        """
        target_dir_str = self.texture_target_path_widget.text()
        target_dir = self.get_resolved_path(target_dir_str)

        if self.current_outside_count == 0:
            cmds.warning("Migration skipped: No textures need copying to the target folder.")
            return

        migration_report = core_mat.migrate_textures_to_directory(
            self.texture_data, target_dir, remove_missing_nodes=False
        )

        if migration_report.get("failed_copies"):
            cmds.warning(f"Migration failed for {len(migration_report['failed_copies'])} files. Check script editor.")

        if migration_report.get("copied_count", 0) > 0 or migration_report.get("updated_count", 0) > 0:
            logger.info(
                f"Migration successful. Copied: {migration_report.get('copied_count', 0)}, "
                f"Updated: {migration_report.get('updated_count', 0)}."
            )

        self._refresh_texture_status()
        self._refresh_compression_status(log_feedback=False)

    def _refresh_texture_status(self):
        """
        Scans the Maya scene for 'file' texture nodes, determines their status
        (outside target, missing, or in target), updates the UI labels, and
        logs detailed information to the script editor.
        """
        logger.info("Refreshing texture status...")

        target_dir_str = self.texture_target_path_widget.text()
        target_dir = self.get_resolved_path(target_dir_str)

        all_texture_nodes = cmds.ls(type="file", long=True) or []
        self.texture_data = core_mat.get_file_texture_paths(file_nodes=all_texture_nodes, resolve_udims=True)

        total_nodes = len(self.texture_data)
        count_outside = 0
        count_missing = 0
        count_in_target = 0

        outside_paths = []
        missing_nodes = []

        normalized_target_dir = os.path.normpath(target_dir).replace("\\", "/")
        if not normalized_target_dir.endswith("/"):
            normalized_target_dir += "/"

        for node_name, path_list in self.texture_data.items():

            is_empty_path = not path_list or (len(path_list) == 1 and not path_list[0])

            if is_empty_path:
                count_missing += 1
                missing_nodes.append(f"{node_name} (Empty Path)")
                self.texture_data[node_name] = [""]
                continue

            is_any_file_found_on_disk = False
            first_broken_path = None

            for path in path_list:
                if os.path.exists(path):
                    is_any_file_found_on_disk = True

                    if not path.startswith(normalized_target_dir):
                        count_outside += 1
                        outside_paths.append(path)
                    else:
                        count_in_target += 1

                    break

                elif first_broken_path is None:
                    first_broken_path = path

            if not is_any_file_found_on_disk:
                count_missing += 1
                missing_nodes.append(f"{node_name} (Broken Path: {first_broken_path})")

        self.current_outside_count = count_outside
        self.current_missing_count = count_missing

        # --- Conditional Coloring ---
        outside_text = f"<b>{count_outside}</b>"
        missing_text = f"<b>{count_missing}</b>"

        if count_outside > 0:
            outside_text = f'<font color="#FFA500">{outside_text}</font>'

        if count_missing > 0:
            missing_text = f'<font color="#FF0000">{missing_text}</font>'

        self.status_labels["found"].setText(str(total_nodes))
        self.status_labels["outside"].setText(outside_text)
        self.status_labels["missing"].setText(missing_text)
        self.status_labels["in_target"].setText(str(count_in_target))
        # ---------------------------

        # --- Detailed Logging to Script Editor ---
        if outside_paths:
            unique_outside_paths = sorted(list(set(outside_paths)))
            logger.info("--- Paths Outside Target Folder ---")
            for path in unique_outside_paths:
                logger.info(f"OUTSIDE: {path}")

        if missing_nodes:
            logger.info("--- Missing File Nodes ---")
            for entry in missing_nodes:
                logger.warning(f"MISSING: {entry}")

        if outside_paths or missing_nodes:
            logger.info("Detailed migration status log is available in the Script Editor for review.")

        textures_word = "texture" if total_nodes == 1 else "textures"
        logger.info(f"Summary: {total_nodes} {textures_word}, {count_outside} outside, {count_missing} missing.")

        self._update_save_button_state(count_outside, count_missing)

    def _refresh_compression_status(self, log_feedback):
        """
        Scans the target texture directory for image files and calculates their total count and size.

        Args:
            log_feedback (bool): If True, logs the process and result to the script editor.
        """
        target_dir_str = self.texture_target_path_widget.text()
        target_dir = self.get_resolved_path(target_dir_str)

        if log_feedback:
            logger.info("Refreshing compression analysis...")
            logger.info(f"Scanning directory: {target_dir}")

        total_files = 0
        total_bytes = 0

        # Define allowed image extensions
        _allowed_extensions = (
            ".png",
            ".jpg",
            ".jpeg",
            ".tiff",
            ".tif",
            ".tga",
            ".exr",
            ".iff",
        )

        if os.path.isdir(target_dir):
            for root, _, files in os.walk(target_dir):
                for file_name in files:
                    if file_name.lower().endswith(_allowed_extensions):
                        full_path = os.path.join(root, file_name)
                        try:
                            # Use os.path.getsize(full_path) for actual size
                            total_bytes += os.path.getsize(full_path)
                            total_files += 1
                        except OSError as e:
                            if log_feedback:
                                logger.warning(f"Could not get size for {file_name}: {e}")

        total_mb = round(total_bytes / (1024 * 1024), 2)
        self.current_total_files = total_files

        self.compress_labels["total_files"].setText(str(total_files))
        self.compress_labels["total_size_mb"].setText(f"{total_mb:.2f} MB")

        if log_feedback:
            logger.info(f"Size analysis updated: {total_files} files, {total_mb:.2f} MB.")

    def _update_save_button_state(self, outside_count, missing_count):
        """
        Enables or disables the Save Geometry button based on migration status and bypass checkbox.

        Args:
            outside_count (int): Number of textures residing outside the target project folder.
            missing_count (int): Number of texture files missing from disk.
        """
        is_bypass_active = self.bypass_checkbox.isChecked()
        is_migration_complete = outside_count == 0 and missing_count == 0

        if is_migration_complete or is_bypass_active:
            self.save_scene_btn.setEnabled(True)
            self.save_scene_btn.setToolTip("Ready to save.")
        else:
            self.save_scene_btn.setEnabled(False)
            self.save_scene_btn.setToolTip(
                "Cannot save: Textures are missing or outside the target folder. Check the bypass option."
            )

    def _save_geometry_scene(self):
        """
        Saves the current Maya scene to the parsed path without performing migration.
        """
        geo_path_str = self.geo_target_path_widget.text()
        geo_path = self.get_resolved_path(geo_path_str)

        # 1. Check Pre-Save Condition
        if not self.save_scene_btn.isEnabled():
            cmds.warning("Save aborted: Save button is disabled due to missing/outside textures.")
            return

        # 2. Save Maya Scene (Only parsing and saving)
        try:
            save_dir = os.path.dirname(geo_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            if geo_path and os.path.exists(geo_path):
                core_io.set_file_permission_modifiable(geo_path)

            cmds.file(geo_path, rename=geo_path)
            cmds.file(save=True, type="mayaAscii")
            logger.info(f"Scene saved successfully to: {geo_path}")
            cmds.inViewMessage(
                m=f"Geometry scene saved successfully to: {os.path.basename(geo_path)}", pos="topCenter", fadeTime=2000
            )

        except Exception as e:
            cmds.error(f"Failed to save scene: {e}")
            logger.error(f"Scene save error: {e}")


if __name__ == "__main__":
    with ui_qt_utils.QtApplicationContext():
        a_sample_project = tools_rig_frm.RigProject()
        a_sample_project.set_project_dir_path(utils_sys.get_desktop_path())

        tool = GeometryPreprocessor(parent=ui_qt_utils.get_maya_main_window(), project=a_sample_project)
        tool.show()
