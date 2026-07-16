"""
Animation Retargeter Controller
"""

import gt.tools.retargeter.retargeter_constants as tools_retargeter_const
import gt.tools.retargeter.retargeter_framework as tools_retargeter_frm
import gt.tools.retargeter.retargeter_widget as tools_retargeter_widget
import gt.tools.retargeter.retargeter_model as tools_retargeter_model
import gt.tools.retargeter.retargeter_utils as tools_retargeter_utils
import gt.ui.progress_bar as ui_progress_bar
import gt.ui.resource_library as ui_res_lib
import gt.core.naming as core_naming
import gt.utils.system as utils_sys
import gt.core.anim as core_anim
import gt.core.io as core_io
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RetargeterController:
    def __init__(self, model, view):
        """
        Initialize the RetargeterController object.

        Args:
            model (RetargeterModel): The RetargeterModel object used for data manipulation.
            view (RetargeterView): The view object to interact with the user interface.
        """
        self.model = model  # the model is used for the Definition Setup
        self.view = view
        self.view.attach_model(model)
        self.view.controller = self
        self.progress_win = None

        # Default parameters
        self.project_definition_folder = tools_retargeter_const.RetargeterConstants.DEFAULT_DEFINITION_FOLDER

        # Connections
        self.view.definition_dir_widget.text_field.textChanged.connect(self.update_definition_fields)
        self.view.retarget_btn.clicked.connect(self.retarget)
        self.view.definition_widget.combobox.currentIndexChanged.connect(self.update_view_from_definition)
        self.view.new_definition_btn.clicked.connect(self.create_new_definition)
        self.view.edit_definition_widget.combobox.currentIndexChanged.connect(self.update_view_from_model)
        self.view.edit_mode_btn.clicked.connect(self.edit_mode)
        self.view.edit_save_definition_btn.clicked.connect(self.save_definition)
        self.view.save_source_skel_pose_btn.clicked.connect(self.save_source_skeleton_pose)
        self.view.clear_source_skel_pose_btn.clicked.connect(self.clear_source_skeleton_pose)
        self.view.mapping_table_widget.itemSelectionChanged.connect(self.select_scene_targets)
        self.view.add_controls_btn.clicked.connect(self.add_controls_from_selection)
        self.view.delete_targets_btn.clicked.connect(self.delete_targets_from_table)
        self.view.autofix_mapping_names_btn.clicked.connect(self.autofix_mapping_names)
        self.view.reset_definition_btn.clicked.connect(self.reset_definition_folder)

        # Init Retarget Tab - update fields from definition
        self.update_view_from_definition()

        # Init Definition Setup Tab - data from model
        self.update_view_from_model()

        # Show
        self.view.show()

    # Getters ------------------------------
    def get_source_list(self):
        """Gets the list of files to retarget, independently of the mode selected by the user.

        Returns:
            list: source files to retarget
        """

        if self.view.batch_status:
            return self.view.get_batch_list_selected_paths()
        else:
            if not self.get_source_animation_path():
                return []
            return [self.get_source_animation_path()]

    def get_source_animation_path(self):
        """Gets the source file picked by the user when not in batch mode.

        Returns:
            str: source file path
        """
        if not self.view.source_animation_path:
            logger.warning("Source animation file not selected.")
            return
        if not os.path.isfile(self.view.source_animation_path):
            logger.warning("Source animation file cannot be found. Please select a valid path.")
            return

        return os.path.normpath(self.view.source_animation_path)

    def get_target_rig_path(self):
        """Gets the target file selected by the user.

        Returns:
            str: target rig path
        """
        if not self.view.target_rig_path:
            logger.warning("Target rig file not selected.")
            return
        if not os.path.isfile(self.view.target_rig_path):
            logger.warning("Target rig file cannot be found. Please select a valid path.")
            return

        return os.path.normpath(self.view.target_rig_path)

    def get_definition_path(self):
        """Gets the definition file selected by the user.

        Returns:
            str: definition path
        """
        if not self.view.definition_folder:
            logger.warning("Definition folder not set.")
            return
        if not self.view.definition_filename:
            return

        _definition_path = os.path.normpath(os.path.join(self.view.definition_folder, self.view.definition_filename))
        if not os.path.isfile(_definition_path):
            logger.warning(f"Following definition file cannot be found: {_definition_path}")
            return

        return _definition_path

    def get_edit_definition_path(self):
        """Gets the edit definition file selected by the user in the Definition Setup tab.

        Returns:
            str: edit definition path
        """
        if not self.view.definition_folder:
            logger.warning("Definition folder not set.")
            return
        if not self.view.definition_setup_filename:
            return

        _definition_path = os.path.normpath(
            os.path.join(self.view.definition_folder, self.view.definition_setup_filename)
        )
        if not os.path.isfile(_definition_path):
            logger.warning(f"Following definition file cannot be found: {_definition_path}")
            return

        return _definition_path

    def get_batch_target_folder(self):
        """Gets the batch target folder selected by the user.

        Returns:
            str: batch target folder path
        """
        if not self.view.batch_target_folder:
            logger.warning("Batch target folder not selected.")
            return
        if not os.path.isdir(self.view.batch_target_folder):
            logger.warning("Batch target folder cannot be found. Please select a valid path.")
            return

        return os.path.normpath(self.view.batch_target_folder)

    def get_source_namespace(self):
        """Gets the source namespace from user ui settings.

        Returns:
            str: source namespace
        """
        if not self.view.source_namespace:
            logger.debug("Source namespace empty. Please insert a namespace.")
            return

        return self.view.source_namespace

    def get_target_namespace(self):
        """Gets the target namespace from user ui settings.

        Returns:
            str: target namespace
        """
        if not self.view.target_namespace:
            logger.debug("Target namespace empty. Please insert a namespace.")
            return

        return self.view.target_namespace

    def get_source_path(self):
        """Gets the source path inside the definition setup tab selected by the user.

        Returns:
            str: edit source path
        """
        if not self.view.source_path:
            logger.debug("Source file not selected.")
            return
        if not os.path.isfile(self.view.source_path):
            logger.debug("Source file cannot be found. Please select a valid path.")
            return

        return os.path.normpath(self.view.source_path)

    def get_target_path(self):
        """Gets the target path inside the definition setup tab selected by the user.

        Returns:
            str: edit target path
        """
        if not self.view.target_path:
            logger.debug("Target file not selected.")
            return
        if not os.path.isfile(self.view.target_path):
            logger.debug("Target file cannot be found. Please select a valid path.")
            return

        return os.path.normpath(self.view.target_path)

    def get_joints_from_loaded_source(self):
        """Gets the skeleton joints from the loaded source.

        Returns:
            list: source joints
        """
        import gt.core.hierarchy as core_hrchy

        _source_joints = []

        # Get selected source namespace and top level nodes that are matching it
        _source_namespace = self.get_source_namespace()
        if not _source_namespace:
            _source_namespace = ""
            _top_level_nodes = cmds.ls(assemblies=True)
        else:
            _top_level_nodes = cmds.ls(f"{_source_namespace}:*", assemblies=True)

        if not _top_level_nodes:
            return _source_joints

        for top_node in _top_level_nodes:
            item_list = core_hrchy.get_hierarchy(root=top_node, full_path=True)
            if item_list:
                _source_joints.extend(item_list)
        _source_joints = cmds.ls(_source_joints, type="joint", long=True, absoluteName=True)

        return _source_joints

    def update_view_from_definition(self):
        """
        Updates the retarget tab fields when the user changes the definition.
        """
        _definition_file_model = tools_retargeter_model.RetargeterModel()
        _definition_path = self.get_definition_path()
        if _definition_path:

            _definition_file_model.load_project_from_file(_definition_path)
            _model_target_rig_path = _definition_file_model.get_target_path()
            # Update Target Rig field
            self.view.set_target_rig_path(_model_target_rig_path)
        else:
            self.view.set_target_rig_path(None)

    def update_view_from_model(self):
        """Loads the project in the model and updates the Definition Setup fields
        when a definition is selected by the user."""

        _source_path = None
        _target_path = None
        _source_namespace = None
        _target_namespace = None
        _edit_definition_path = self.get_edit_definition_path()
        if _edit_definition_path:
            self.model.load_project_from_file(_edit_definition_path)
            _source_path = self.model.get_source_path()
            _target_path = self.model.get_target_path()
            _source_namespace = self.model.get_source_namespace()
            _target_namespace = self.model.get_target_namespace()

        # Update fields
        self.view.set_source_path(_source_path)
        self.view.set_target_path(_target_path)
        self.view.set_source_namespace(_source_namespace)
        self.view.set_target_namespace(_target_namespace)
        self.view.option_boxes_widget.update_values()
        self.view.addon_scene_options_widget.update_values()
        self.view.addon_source_setup_widget.update_values()
        self.view.addon_post_bake_widget.update_values()
        self.view.addon_patches_widget.update_values()
        self.view.addon_python_script_widget.update_values()
        self.update_definition_model()
        self.update_mapping_table()

    def update_mapping_table(self):
        """Updates the mapping table - definition links."""
        _source_joints = []

        try:
            _source_joints = self.get_joints_from_loaded_source()
        except Exception as e:  # Otherwise running the code without maya.cmds in PyCharm will fail
            logger.warning(f"Unable to collect source joints for the mapping table. Issue: {e}")

        missing_definition_files = []
        if self.view.source_path and not os.path.isfile(self.view.source_path):
            missing_definition_files.append("source")
        if self.view.target_path and not os.path.isfile(self.view.target_path):
            missing_definition_files.append("target")

        if missing_definition_files:
            _missing_files = " and ".join(missing_definition_files)
            _file_label = "file was"
            if len(missing_definition_files) > 1:
                _file_label = "files were"
            _msg_text = (
                f"Definition {_missing_files} {_file_label} not found. "
                "Mapping links were still loaded from the definition."
            )
            logger.warning(_msg_text)
            if self.view.timed_message_label:
                self.view.timed_message_label.show_message(_msg_text, seconds=6, msg_type="warning")

        self.model.update_links()
        try:
            _health_score_dict = self.model.get_links_health_score(verbose=False)
        except Exception as e:
            logger.warning(f"Unable to score mapping links. Loading links with warning status. Issue: {e}")
            _health_score_dict = {link: 0 for link in self.model.project.get_links()}

        self.view.update_mapping_table(
            health_score_dict=_health_score_dict,
            source_joints=_source_joints,
            source_namespace=self.model.get_source_namespace(),
            target_namespace=self.model.get_target_namespace(),
        )

    def update_definition_model(self):
        """
        Updates model with user settings from ui.
        """

        view_source_path = self.get_source_path()
        view_target_path = self.get_target_path()
        
        if not view_source_path or not view_target_path:
            return

        if self.model.get_source_path() != view_source_path:
            self.model.set_source_path(view_source_path)
        if self.model.get_target_path() != view_target_path:
            self.model.set_target_path(view_target_path)

        view_source_namespace = self.get_source_namespace()
        view_target_namespace = self.get_target_namespace()

        if not view_source_namespace and not view_target_namespace:
            return

        self.model.set_source_namespace(view_source_namespace)
        self.model.set_target_namespace(view_target_namespace)
        self.model.update_links()

        # Update Definition general options
        self.view.option_boxes_widget.update_definition()

        # Update Definition Addon Scene Options
        self.view.addon_scene_options_widget.update_definition()

        # Update Definition Addon Source Setup
        self.view.addon_source_setup_widget.update_definition()

        # Update Definition Addon Post Bake
        self.view.addon_post_bake_widget.update_definition()

        # Update Definition Addon Patches
        self.view.addon_patches_widget.update_definition()

        # Update Definition Addon Python Script
        self.view.addon_python_script_widget.update_definition()

    # Retarget ------------------------------
    def retarget(self):
        """Runs the retarget process."""

        # Check animation unsaved changes ----------------------------------------------------
        unsaved_anim_changes = core_anim.check_unsaved_animation_changes()
        if unsaved_anim_changes:
            _msg_title = "Retarget Animation"
            _msg_text = (
                "Detected unsaved animation changes."
                "\nThe retarget process will create a new scene, those changes will be lost."
                "\n\nDo you want to proceed anyway?"
            )
            _proceed = tools_retargeter_widget.show_message_box(
                self.view,
                title=_msg_title,
                message=_msg_text,
                icon_type="warning",
                ask_user=True,
            )

            if not _proceed:
                return

        # Get Source List --------------------------------------------------------------------
        _feedback_title = "Retargeting..."
        source_list = self.get_source_list()
        if not source_list:
            _msg_text = "No Source Animation selected. Please select an animation or a list of files to batch."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_feedback_title, message=_msg_text, icon_type="warning"
            )
            return

        # Get Target Path --------------------------------------------------------------------
        target_rig_path = self.get_target_rig_path()
        if not target_rig_path:
            _msg_text = "No Target Rig selected. Please select a rig file."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_feedback_title, message=_msg_text, icon_type="warning"
            )
            return

        # Get Target Folder (batch mode) -----------------------------------------------------
        target_folder = None
        if self.view.batch_status:
            target_folder = self.get_batch_target_folder()
            if not target_folder:
                _msg_text = (
                    "Target folder not defined.\n"
                    "Please select a location where the retargeted animations can be saved."
                )
                logger.warning(_msg_text)
                tools_retargeter_widget.show_message_box(
                    self.view, title=_feedback_title, message=_msg_text, icon_type="warning"
                )
                return

        # -------------------------------- Multi-processing Batch Mode (Start) --------------------------------
        is_single_file = not self.view.batch_status
        if self.view.multi_process_batch and not is_single_file:
            import gt.tools.retargeter.multi_batch_launcher as tools_retargeter_multi_launcher

            retarget_model = tools_retargeter_model.RetargeterModel()
            retarget_model.load_project_from_file(self.get_definition_path())
            retarget_model.set_target_path(target_rig_path)

            # Apply overrides from the interface
            if self.view.override_delete_source:
                retarget_model.project.set_delete_source_status(True)
            if self.view.delete_static_channels:
                retarget_model.project.set_delete_static_channels_status(True)
            if self.view.override_target_namespace_status:
                if self.view.override_target_namespace:
                    retarget_model.project.set_target_namespace(self.view.override_target_namespace)
            # -- post bake override
            _addon_pb = retarget_model.project.get_addon_post_bake()
            _addon_pb.active = not self.view.disable_post_processing

            definition_project = retarget_model.get_project()
            definition_as_dict = definition_project.get_definition_as_dict()

            tools_retargeter_multi_launcher.run_retarget_batch(
                definition_json_path=definition_as_dict,
                source_files_list=source_list,
                output_dir=target_folder,
                max_workers=self.view.multi_process_max_instances,
                disable_logging=not self.view.multi_write_log_file,
                skip_existing_files=self.view.skip_existing_files,
            )
            return
        # --------------------------------- Multi-processing Batch Mode (End) ---------------------------------

        # Create Progress Bar Window ---------------------------------------------------------
        self.progress_win = ui_progress_bar.ProgressBarWindow(parent=self.view, on_top=False)
        self.progress_win.show()
        self.progress_win.set_progress_bar_name(_feedback_title)
        # Create connections
        self.progress_win.first_button.clicked.connect(self.progress_win.close_window)
        self.progress_win.set_progress_bar_max_value(len(source_list) * 4)  # Num of operations per retarget
        self.progress_win.increase_progress_bar_value()
        # Progress Bar Text Colors
        _rgb_feedback_neutral = ui_res_lib.Color.Hex.white
        _rgb_feedback_passed = ui_res_lib.Color.Hex.green_pale
        _rgb_feedback_failed = ui_res_lib.Color.Hex.red_melon
        _rgb_feedback_warning = ui_res_lib.Color.Hex.yellow_khaki

        # Retarget Steps ---------------------------------------------------------------------
        retargeted_file_list = []
        for index, source_path in enumerate(source_list):
            # Feedback Window Message Index
            _msg = ""
            if len(source_list) > 1:
                _msg += f"{index + 1}. "

            # Define target path for skipping existing (if needed) ---------------------------
            retarget_const = tools_retargeter_const.RetargeterConstants
            _source_name = os.path.basename(source_path).split(".")[0]
            if is_single_file:  # Running Batch Mode
                target_folder = ""
            _target_path = os.path.normpath(
                os.path.join(target_folder, f"{_source_name}.{retarget_const.RIG_MA_EXTENSION}")
            )
            _target_path = _target_path.replace("\\", "/")
            if os.path.exists(_target_path) and self.view.skip_existing_files:
                _msg += f'Skipped existing file: "{_target_path}".\n'
                self.progress_win.add_text_to_output_box(input_string=_msg, color=_rgb_feedback_warning)
                continue

            # Start Retarget Process ---------------------------------------------------------
            cmds.file(new=True, force=True)

            # Log Current Source
            _msg += f'Retargeting "{utils_sys.get_filename(source_path)}".'
            self.progress_win.add_text_to_output_box(input_string=_msg, color=_rgb_feedback_neutral)

            # Init a separate model for to retarget the animations
            _msg = "Initializing definition."
            self.progress_win.add_text_to_output_box(input_string=_msg, color=_rgb_feedback_neutral)
            retarget_model = tools_retargeter_model.RetargeterModel()
            retarget_model.load_project_from_file(self.get_definition_path())

            # Set paths from ui
            retarget_model.set_source_path(source_path)
            retarget_model.set_target_path(target_rig_path)

            # Apply overrides from the interface
            if self.view.override_delete_source:
                retarget_model.project.set_delete_source_status(True)
            if self.view.delete_static_channels:
                retarget_model.project.set_delete_static_channels_status(True)
            if self.view.override_target_namespace_status:
                if self.view.override_target_namespace:
                    retarget_model.project.set_target_namespace(self.view.override_target_namespace)
            # -- post bake override
            _addon_pb = retarget_model.project.get_addon_post_bake()
            _addon_pb.active = not self.view.disable_post_processing

            # Retarget
            try:
                callbacks = [self.progress_win.add_text_to_output_box, self.progress_win.increase_progress_bar_value]
                retarget_model.project.retarget(callbacks=callbacks)

                if is_single_file:
                    _msg = f"Retargeting process complete."
                    self.progress_win.add_text_to_output_box(input_string=_msg, color=_rgb_feedback_neutral)
                    self.progress_win.change_last_line_color(_rgb_feedback_passed)
            except Exception as e:
                # If there are errors, show it in the progress textfield.
                self.progress_win.add_text_to_output_box(input_string=str(e), color=_rgb_feedback_failed)

            # Save - Batch mode --------------------------------------------------------------
            if is_single_file:
                continue

            self.save_retargeted_animation(_target_path)  # @@@
            retargeted_file_list.append(_target_path)
            _msg = f'Retargeted file save to "{_target_path}".\n'
            self.progress_win.add_text_to_output_box(input_string=_msg, color=_rgb_feedback_passed)
            self.progress_win.change_last_line_color(_rgb_feedback_passed)

        # Batch complete message
        if self.view.batch_status:
            _msg = "Batch retargeting process complete."
            self.progress_win.add_text_to_output_box(input_string=_msg, color=_rgb_feedback_neutral)

    @staticmethod
    def save_retargeted_animation(animation_path):
        """Saves retargeted animation.

        Args:
            animation_path (str): path of the animation file to save.
        """
        if animation_path and os.path.exists(animation_path):
            core_io.set_file_permission_modifiable(animation_path)

        unknown_nodes = cmds.ls(type="unknown")
        if unknown_nodes:
            cmds.delete(unknown_nodes)

        cmds.file(rename=animation_path)
        cmds.file(save=True, force=True, type="mayaAscii")

    def edit_mode(self):
        """Activates the project edit mode."""

        _source_path = self.get_source_path()
        _target_path = self.get_target_path()
        _msg_title = "Import Retarget Definition Files"

        if not _source_path or not _target_path:
            _msg_text = "Source or target paths are missing. Please make sure to select them first."
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return
        if not os.path.isfile(_source_path):
            _msg_text = "Source file is missing. Cannot import/reload."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return
        if not os.path.isfile(_target_path):
            _msg_text = "Target file is missing. Cannot import/reload."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        self.update_definition_model()
        # Enable edit mode
        _linked_mode = self.view.linked_status
        self.model.retarget_edit_mode(linked_mode=_linked_mode)
        # Update mapping table
        self.update_mapping_table()
        # Update Source Setup Tab
        self.view.addon_source_setup_widget.update_values()

        # Info
        _linked_string = "[Linked]" if _linked_mode else "[Not Linked]"
        _msg_text = f"Correctly loaded the retarget files. Turned On Edit Mode {_linked_string}."
        self.view.timed_message_label.show_message(_msg_text, seconds=6)

    def add_controls_from_selection(self):
        """Adds selected controls to the mapping table."""
        import gt.core.namespace as core_nspace

        # Get selected objects
        selection = cmds.ls(sl=True, type="transform")
        if not selection:
            logger.warning("No transform nodes are selected.")
            return

        # Check Target Namespace
        target_namespace = self.get_target_namespace()
        sel_nspace_matching = [node for node in selection if core_nspace.get_namespace(node) == target_namespace]
        if not sel_nspace_matching:
            logger.warning("No selected nodes matching the target namespace.")
            return

        targets_to_add = cmds.ls(sel_nspace_matching, long=True, absoluteName=True)
        _targets_to_highlight = []
        for new_target in targets_to_add:
            if not self.check_unique_target(new_target):
                logger.warning(f"The Mapping Table already has the following control: {new_target}")
                continue

            # Add control to the TargetingLinks
            new_link = tools_retargeter_frm.TargetingLink(
                source="",
                target=new_target,
                method=tools_retargeter_frm.TargetingMethods.rotation,
            )
            _targets_to_highlight.append(new_target)
            self.model.project.add_link(link=new_link)
            logger.info(f"The following control has been added to the mapping table: {new_target}")

        # Update Mapping Table
        self.update_mapping_table()

        # Select New Items
        self.view.mapping_table_widget.select_target_items(target_names=_targets_to_highlight)
        self.view.mapping_table_widget.scrollToBottom()

    def check_unique_target(self, target_to_add):
        """Checks if the target to add is already in the TargetingLink list.

        Args:
            target_to_add (str): target name to add to the mapping.
        Returns:
            bool: check result.
        """
        result = True
        current_links = self.model.project.links
        for link in current_links:
            link_target = link.get_target()
            link_target = link_target.replace("|:", "|")
            if target_to_add == link_target:
                result = False
                break
        return result

    def delete_targets_from_table(self):
        """Deletes selected target rows from the table."""

        # TODO: Add message boxes (tools_retargeter_widget.show_message_box)

        selected_table_items = self.view.mapping_table_widget.selectedItems()
        if not selected_table_items:
            logger.warning("No Targets selected.")

        for table_item in selected_table_items:
            target_data = table_item.data(self.view._user_role)

            # Delete target from model
            active_link = self.model.project.get_links_from_target(target_data)
            if not active_link:
                logger.warning(f"Cannot find the following TargetLink in the project: {active_link}")
                continue
            active_link = active_link[0]
            removed = self.model.project.remove_link(active_link)
            if removed:
                logger.info(f"Successfully removed the following TargetLink from the mapping: {active_link}")
            else:
                logger.warning(f"Cannot remove the following TargetLink from the mapping: {active_link}")

        # Update Mapping Table
        self.update_mapping_table()

    def autofix_mapping_names(self):
        """Auto-fix Link short names to long-absolute."""
        # Verify scene
        _msg_title = "Autofix Mapping Names"
        try:
            self.model.project.read_addons_and_links_scene_data()
        except Exception:
            _msg_text = "Cannot find required objects in the scene. Please Import/Reload the definition files."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return
        # Convert short names to long
        self.model.convert_links_short_to_long()
        # Update Mapping Table
        self.update_mapping_table()
        # Info
        _msg_text = f"Converted the mapping targets and sources names with their current long-absolute ones."
        tools_retargeter_widget.show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="info")

    def save_definition(self):
        """Saves the current selected definition with the ui values picked by the user."""
        _msg_title = "Save Definition"

        # Get Definition path
        _definition_path = self.get_edit_definition_path()
        if not _definition_path:
            _msg_text = "Definition not selected. Cannot retrieve the file and save."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        # Update the model with the data from the UI
        self.update_definition_model()
        _user_defined_attr = self.view.option_boxes_widget.get_user_defined_attr()

        # Read the values that the Addons required from the scene
        try:
            self.model.project.read_addons_and_links_scene_data(
                get_user_defined=_user_defined_attr,
                exclude_addon="Source Setup",
            )
            _source_setup = self.model.project.get_addon_source_setup()
            retargeted_status = _source_setup.get_retargeted_status()
        except Exception:
            _msg_text = "Cannot read Addons scene data. Please Import/Reload the definition files."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        # Retargeted scene check
        if retargeted_status:
            _msg_text = (
                f"Detected a retargeted animation in the scene, if you save you could break the stored pose."
                "\n\nDo you want to proceed anyway?"
            )
            _proceed = tools_retargeter_widget.show_message_box(
                self.view,
                title=_msg_title,
                message=_msg_text,
                icon_type="info",
                ask_user=True,
            )

            if not _proceed:
                return

        # Get the project dict
        _definition_dict = self.model.project.get_definition_as_dict()

        # Save Definition json file
        # -- If already present, make it modifiable
        if _definition_path and os.path.exists(_definition_path):
            core_io.set_file_permission_modifiable(_definition_path)
        _file_path = core_io.write_json(path=_definition_path, data=_definition_dict)
        if os.path.isfile(_file_path):
            _msg_text = f"Successfully saved the current retarget definition.\n\nJson file:{_definition_path}"
            tools_retargeter_widget.show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="info")

    def clear_source_skeleton_pose(self):
        """Clears the source skeleton pose and saves the definition."""
        self.save_source_skeleton_pose(clear_source_skeleton=True)

    def save_source_skeleton_pose(self, clear_source_skeleton=False):
        """
        Gets and saves the current source skeleton pose, or clears the pose and saves.
        Args:
            clear_source_skeleton (bool): if True, instead of getting the values from the scene, it will clear
                                          the data and then save.
        """
        _msg_title = "Save Source Skeleton Pose"

        # Get Definition path
        _definition_path = self.get_edit_definition_path()
        if not _definition_path:
            _msg_text = "Definition not selected. Cannot retrieve the file and save."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        # Read the values that the Addons required from the scene
        try:
            _source_setup = self.model.project.get_addon_source_setup()
            if clear_source_skeleton:
                _source_setup.clear_scene_data()
            else:
                _source_setup.read_scene_data()  # Read the values and update the data
            retargeted_status = _source_setup.get_retargeted_status()
        except Exception:
            _msg_text = "Cannot read Addons scene data. Please Import/Reload the definition files."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        # Retargeted scene check
        if retargeted_status:
            _msg_text = (
                f"Detected a retargeted animation in the scene, if you save you could break the stored pose."
                "\n\nDo you want to proceed anyway?"
            )
            _proceed = tools_retargeter_widget.show_message_box(
                self.view,
                title=_msg_title,
                message=_msg_text,
                icon_type="info",
                ask_user=True,
            )

            if not _proceed:
                return

        # Get the project dict
        _definition_dict = self.model.project.get_definition_as_dict()

        # Save Definition json file
        # -- If already present, make it modifiable
        if _definition_path and os.path.exists(_definition_path):
            core_io.set_file_permission_modifiable(_definition_path)
        _file_path = core_io.write_json(path=_definition_path, data=_definition_dict)
        if os.path.isfile(_file_path):
            if clear_source_skeleton:
                _msg_text = f"Successfully cleared the source skeleton pose.\n\nJson file:{_definition_path}"
            else:
                _msg_text = f"Successfully saved the current source skeleton pose.\n\nJson file:{_definition_path}"
            tools_retargeter_widget.show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="info")

    def create_new_definition(self):
        """Creates and loads a new definition."""
        _new_definition_name = None
        _new_definition_profile = None

        _msg_title = "New Definition"
        _new_definition_dialog = tools_retargeter_widget.NewDefinitionDialog(self.view)
        if _new_definition_dialog.exec_():
            _new_definition_name = _new_definition_dialog.definition_name
            _new_definition_profile = _new_definition_dialog.definition_profile

        # check new definition path
        if not self.view.definition_folder:
            _msg_text = "Definition folder not set."
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        if not os.path.isdir(self.view.definition_folder):
            _msg_text = f"Following definition folder does not exist: {self.view.definition_folder}"
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        if not _new_definition_name or not _new_definition_profile:
            logger.info("Create new definition aborted.")
            return

        retarget_const = tools_retargeter_const.RetargeterConstants
        _new_definition_filename = f"{_new_definition_name}.{retarget_const.DATA_EXTENSION}"
        _new_definition_path = os.path.normpath(
            os.path.join(self.view.definition_folder, _new_definition_filename)
        )
        _new_definition_path = _new_definition_path.replace("\\", "/")

        if os.path.isfile(_new_definition_path):
            _msg_text = (
                "Cannot overwrite the existing file. Please choose a different name."
                f"\n\n{_new_definition_path}"
            )
            logger.warning(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )
            return

        # Create the new definition
        # TODO: currently hardcoded. Once we have a profile logic we can change this.
        new_definition = None
        if _new_definition_profile == "biped":
            import gt.tools.retargeter.template_biped as tools_retargeter_biped

            retargeter_dir = os.path.dirname(__file__)
            tools_dir = os.path.dirname(retargeter_dir)
            package_dir = os.path.dirname(tools_dir)
            test_data_dir = os.path.join(package_dir, "tests", "test_retargeter", "data")
            rig_file = os.path.join(test_data_dir, "male_rig.ma")

            new_definition = tools_retargeter_biped.rom_create_biped_definition_with_long_skin_tester(
                target_path=rig_file,
                add_fingers=True,
            )

        else:
            # create a new empty definition
            new_definition = tools_retargeter_frm.RetargeterDefinition()

        # Write Definition json file
        new_definition_as_dict = new_definition.get_definition_as_dict()
        # -- If already present, make it modifiable - it shouldn't be needed but just in case
        if _new_definition_path and os.path.exists(_new_definition_path):
            core_io.set_file_permission_modifiable(_new_definition_path)
        _new_path = core_io.write_json(path=_new_definition_path, data=new_definition_as_dict)
        if _new_path:
            # Update UI definition fields
            self.view.definition_setup_filename = _new_definition_filename
            self.view.update_definition_combobox()
            self.update_view_from_model()

            # Info message
            _msg_text = f"A new definition has been created and loaded:\n\n{_new_path}"
            logger.info(_msg_text)
            tools_retargeter_widget.show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="info")
        else:
            # Info message
            _msg_text = f"The creation of the new definition failed.\nPlease check the log."
            logger.info(_msg_text)
            tools_retargeter_widget.show_message_box(
                self.view, title=_msg_title, message=_msg_text, icon_type="warning"
            )

    def reset_definition_folder(self):
        """Resets the definition folder to the default one."""
        _default_definition_folder = self.get_default_definition_folder()
        if _default_definition_folder:
            self.view.definition_dir_widget.text_field.setText(_default_definition_folder)
            self.update_definition_fields()

    def update_definition_fields(self):
        """Updates definition view fields."""
        self.view.update_definition_combobox()
        self.update_view_from_model()

    def get_default_definition_folder(self):
        """Gets the default definition folder.

        Returns:
            str: default definition folder
        """
        if not os.path.isdir(self.project_definition_folder):
            _msg_title = "Get Definition Folder"
            _msg_text = f"Missing default folder: {self.project_definition_folder}"
            logger.debug(_msg_text)
            tools_retargeter_widget.show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="error")
            return
        else:
            return self.project_definition_folder

    def select_scene_targets(self):
        """Selects the scene target objects when the mapping table selection changes."""
        # Enabled by the checkbox "Select Scene Targets"
        available_targets = []
        if self.view.select_scene_targets:
            table_selection = self.view.mapping_table_widget.selectedItems()
            for target in table_selection:
                target_scene_path = target.data(self.view._user_role)

                if cmds.objExists(target_scene_path):
                    # Target path stored in the item
                    available_targets.append(target_scene_path)
                else:
                    # Attempt forcing namespace in case it's missing
                    target_short = core_naming.get_short_name(target_scene_path, remove_namespace=True)
                    target_with_namespace = f"{self.get_target_namespace()}:{target_short}"
                    if cmds.objExists(target_with_namespace):
                        available_targets.append(target_with_namespace)

        # Select
        if available_targets:
            cmds.select(available_targets)

    def select_scene_sources(self, widget):
        """
        Selects the scene source objects when clicking on a source in the mapping table.
        Args:
            widget (QtWidgets.QComboBox): The combo box widget from the table cell that contains the source item.
        """
        # Enabled by the checkbox "Select Scene Sources"
        source_object = None
        if self.view.select_scene_sources:
            _index = widget.currentIndex()
            source_scene_path = widget.itemData(_index)

            if cmds.objExists(source_scene_path):
                # Source path stored in the item
                source_object = source_scene_path
            else:
                # Attempt forcing namespace in case it's missing
                source_short = core_naming.get_short_name(source_scene_path, remove_namespace=True)
                source_with_namespace = f"{self.get_source_namespace()}:{source_short}"
                if cmds.objExists(source_with_namespace):
                    source_object = source_with_namespace

        # Select
        if source_object:
            cmds.select(source_object)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
