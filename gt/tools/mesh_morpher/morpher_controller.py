"""
Mesh Morpher Controller
"""

import gt.tools.mesh_morpher.morpher_constants as tools_morpher_const
import gt.tools.mesh_morpher.morpher_addons as tools_morpher_addons
import gt.tools.mesh_morpher.morpher_addon_widget as tools_morpher_widget
import gt.tools.mesh_morpher.morpher_model as tools_morpher_model
import gt.ui.file_dialog as ui_file_dialog
import gt.core.feedback as core_fback
import gt.ui.qt_import as ui_qt
import gt.core.io as core_io
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_addon_tab_widget(addon):
    """
    Gets the associated attribute widget used to populate the post-processing portion in the main UI.
    Args:
        addon (MorpherAddon): The addon instance to determine the corresponding UI widget for.
    Returns:
        TabWidget: Tab Widget used to populate the post-processing tab.
    """
    if type(addon) is tools_morpher_addons.Addons.DeltaMush:
        return tools_morpher_widget.TabWidgetDeltaMush
    if type(addon) is tools_morpher_addons.Addons.Masking:
        return tools_morpher_widget.TabWidgetMasking
    if type(addon) is tools_morpher_addons.Addons.Anchor:
        return tools_morpher_widget.TabWidgetAnchor
    if type(addon) is tools_morpher_addons.Addons.Renaming:
        return tools_morpher_widget.TabWidgetRenaming


class MorpherController:
    def __init__(self, model, view):
        """
        Initialize the MorpherController object.

        Args:
            model (MorpherModel): The MorpherModel object used for data manipulation.
            view (MorpherView): The view object to interact with the user interface.
        """
        self.model_list = [model]  # list of models related to the selected meshes
        self.view = view
        self.view.controller = self
        self.progress_win = None

        # Default parameters
        self.rbf_cache_folder = tools_morpher_const.MeshMorpherConstants.DEFAULT_RBF_CACHE_FOLDER
        self._subject_previous_name = ""

        # Connections
        self.view.subject_get_button.clicked.connect(self.add_selected_meshes_to_list)
        self.view.subject_delete_button.clicked.connect(self.delete_subject_from_list)
        self.view.generate_button.clicked.connect(self.generate_reshaped_meshes)
        self.view.import_button.clicked.connect(self.import_definition_from_file)
        self.view.export_button.clicked.connect(self.export_definition_to_file)
        self.view.new_rbf_cache_btn.clicked.connect(self.create_new_rbf_cache)
        self.view.subject_mesh_list.itemSelectionChanged.connect(self.refresh_fields)
        self.view.subject_mesh_list.itemDoubleClicked.connect(self.rename_subject_previous_name)
        self.view.subject_mesh_list.itemChanged.connect(self.rename_subject_new_name)

        # Initial Refresh
        self.refresh_fields()

        # Show
        self.view.show()

    def refresh_fields(self):
        """Refreshes the interface fields."""
        self.populate_rbf_list()
        self.populate_post_process_tabs()

    # --------------------------------------------- RBF Group ---------------------------------------------
    def create_new_rbf_cache(self):
        """Allows the user to create new RBF cache files"""
        model = self.get_current_model()
        model.get_definition().export_rbf_data_file()
        self.populate_rbf_list()

    def clear_rbf_list(self):
        """Clears RBF list."""
        # Clear the list
        for i in reversed(range(self.view.rbf_container_layout.count())):
            widget = self.view.rbf_container_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def populate_rbf_list(self):
        """Populates the RBF list with the available files from the cache directory."""
        self.clear_rbf_list()

        if not os.path.exists(self.rbf_cache_folder):
            return

        model = self.get_current_model()
        existing_rbf_paths = set(model.get_definition().rbf_data_paths)  # Get existing paths

        _ext = tools_morpher_const.MeshMorpherConstants.DATA_EXTENSION
        for file in os.listdir(self.rbf_cache_folder):
            if file.endswith(f".{_ext}"):
                file_path = os.path.join(self.rbf_cache_folder, file)
                file_name = os.path.splitext(file)[0]  # Remove .json extension
                checkbox = ui_qt.QtWidgets.QCheckBox(file_name)
                checkbox.setProperty("path", file_path)  # Store full path
                checkbox.stateChanged.connect(self.update_rbf_paths)

                # Check the box if the file path is already in the model's RBF paths
                if file_path in existing_rbf_paths:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(True)
                    checkbox.blockSignals(False)

                self.view.rbf_container_layout.addWidget(checkbox)

    def update_rbf_paths(self):
        """
        Updates definition RBF paths list with selected RBF caches.
        """
        model = self.get_current_model()
        model.get_definition().clear_rbf_data_paths()
        for i in range(self.view.rbf_container_layout.count()):
            checkbox = self.view.rbf_container_layout.itemAt(i).widget()
            if checkbox and checkbox.isChecked():
                model.get_definition().rbf_data_paths.append(checkbox.property("path"))

    def import_definition_from_file(self):
        """
        Shows an open file dialog offering to load a new definition from a file. (JSON formatted)
        """
        file_path = ui_file_dialog.file_dialog(
            caption="Open Morpher Definitions",
            write_mode=False,
            starting_directory=None,
            file_filter=tools_morpher_const.MeshMorpherConstants.DATA_FILTER,
            ok_caption="Open Definition",
            cancel_caption="Cancel",
        )
        if file_path:
            _definitions_data = core_io.read_json_dict(file_path)
            # backward compatibility - only one dictionary in the file
            if isinstance(_definitions_data, dict):
                _definitions_data = [_definitions_data]

            self.view.subject_mesh_list.clear()
            self.model_list = []
            for _imported_definition_data in _definitions_data:
                # populate models
                _subject_model = tools_morpher_model.MorpherModel()
                _subject_model.get_definition().read_data_from_dict(_imported_definition_data)
                self.model_list.append(_subject_model)
                # populate list widget
                self.view.add_item_subject_list(_subject_model.get_definition().get_subject_mesh())

            self.view.select_last_item_subject_list()
            self.refresh_fields()
            logger.info(f"Subject definitions loaded from file: {file_path}")

    def export_definition_to_file(self):
        """
        Shows a save file dialog offering to save the current definition to a file. (JSON formatted)
        """
        _save_path = None

        # File Dialog
        if not _save_path:
            _save_path = ui_file_dialog.file_dialog(
                caption="Save Morpher Definitions",
                write_mode=True,
                file_filter=tools_morpher_const.MeshMorpherConstants.DATA_FILTER,
                ok_caption="Save Definitions",
                cancel_caption="Cancel",
            )
        # Save Project
        if _save_path:
            # If already present, make it modifiable
            if _save_path and os.path.exists(_save_path):
                core_io.set_file_permission_modifiable(_save_path)

            _definitions_data = []
            for _model in self.model_list:
                _model_data = _model.definition.get_definition_as_dict()
                _definitions_data.append(_model_data)
            core_io.write_json(path=_save_path, data=_definitions_data)
            logger.info(f'Definitions saved to "{_save_path}".')

    # --------------------------------------------- Subject Field ---------------------------------------------
    def get_current_model(self):
        """Gets the selected model from the list of meshes to use.
        Returns:
            current_model (MorpherModel class): the current model to use.
        """
        subjects_selected = self.view.subject_mesh_list.selectedItems()
        if subjects_selected:
            subject_item_name = subjects_selected[0].text()
            for _model in self.model_list:
                _model_subject = _model.get_definition().get_subject_mesh()
                if subject_item_name == _model_subject:
                    return _model

        return self.model_list[0]

    def get_model_by_subject(self, subject_name):
        """Gets the model that has the supplied subject name.
        Args:
            subject_name (str): name of the subject used to find the related model.
        Returns:
            model (MorpherModel class) or None: the subject related model.
        """
        for _model in self.model_list:
            _model_subject = _model.get_definition().get_subject_mesh()
            if subject_name == _model_subject:
                return _model

    def create_definition(self, subject_name):
        """
        Create a model based on a mesh and store the relation into the model_map.

        Args:
            subject_name (str): mesh name, object existing in the scene
        """
        for _model in self.model_list:
            _model_subject = _model.get_definition().get_subject_mesh()
            if subject_name == _model_subject:
                return

        # check empty model
        empty_model = None
        for _model in self.model_list:
            _model_subject = _model.get_definition().get_subject_mesh()
            if _model_subject == "":
                empty_model = _model

        if empty_model:
            empty_model.get_definition().set_subject_mesh(subject_name)
        else:
            # Create a new model - new mesh
            subject_model = tools_morpher_model.MorpherModel()
            subject_model.get_definition().set_subject_mesh(subject_name)
            self.model_list.append(subject_model)

    def add_selected_meshes_to_list(self):
        """
        Gets the items in the user's selection to be added as subject meshes to the list.
        This function also update/make the definition related to each mesh.
        """
        selection = cmds.ls(selection=True)
        if not selection:
            logger.warning(f"Nothing selected.")
            return

        # only meshes
        selected_meshes = []
        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True)
            if shapes:
                if cmds.nodeType(shapes[0]) == "mesh":
                    selected_meshes.append(obj)
        if not selected_meshes:
            logger.warning(f"No meshes selected.")
            return

        # check history - meshes shouldn't have history, the RBF doesn't work well otherwise.
        meshes_with_history = []
        for _mesh in selected_meshes:
            _history = cmds.listHistory(_mesh)
            [_history.remove(_node) for _node in reversed(_history) if cmds.nodeType(_node) == "mesh"]
            if _history:
                meshes_with_history.append(_mesh)
        if meshes_with_history:
            _history_string = "\n - ".join(meshes_with_history)
            _warning_msg = (
                f"The following meshes have history: \n - {_history_string}\n"
                "Please delete the history before using the tool."
            )
            logger.warning(_warning_msg)
            feedback = core_fback.FeedbackMessage(style_intro="color:#FFFF00;", intro=_warning_msg)
            feedback.print_inview_message(system_write=False)

        for subject_name in selected_meshes:
            self.create_definition(subject_name)
            self.view.add_item_subject_list(subject_name)

        self.view.select_last_item_subject_list()
        self.populate_post_process_tabs()
        logger.info(f"Subject meshes added to list: {(';'.join(selected_meshes))}")

    def delete_subject_from_list(self):
        """Deletes the selected subject."""
        deleted_subject_name = self.view.delete_item_subject_list()
        # clean the model list
        if deleted_subject_name:
            for i, _model in enumerate(self.model_list):
                _model_subject = _model.get_definition().get_subject_mesh()
                if deleted_subject_name == _model_subject:
                    self.model_list.pop(i)

            if len(self.model_list) == 0:
                empty_model = tools_morpher_model.MorpherModel()
                self.model_list.append(empty_model)

            self.view.select_last_item_subject_list()
            self.populate_post_process_tabs()
            logger.info(f"Subject mesh deleted: {deleted_subject_name}")

    def rename_subject_previous_name(self):
        """Stores the name of the subject when the text field is clicked."""
        if not self.view.subject_mesh_list.currentItem():
            return
        self._subject_previous_name = self.view.subject_mesh_list.currentItem().text()

    def rename_subject_new_name(self):
        """Edits the subject text fields when a new string is prompted by the user."""
        if not self._subject_previous_name:
            return
        if not self.view.subject_mesh_list.currentItem():
            return

        subject_name = self.view.subject_mesh_list.currentItem().text()
        if subject_name == self._subject_previous_name:
            return
        if not subject_name:
            self.view.subject_mesh_list.currentItem().setText(self._subject_previous_name)
            return
        if not cmds.objExists(subject_name):
            self.view.subject_mesh_list.currentItem().setText(self._subject_previous_name)
            logger.warning("Rename skipped. The new name does not correspond to any existing objects in the scene.")
            return

        for _model in self.model_list:
            _model_subject = _model.get_definition().get_subject_mesh()
            if subject_name == _model_subject:
                self.view.subject_mesh_list.blockSignals(True)
                self.view.subject_mesh_list.currentItem().setText(self._subject_previous_name)
                self.view.subject_mesh_list.blockSignals(False)
                logger.warning("Rename skipped. Another subject in the list has the new chosen name.")
                return

        model_to_rename = None
        for _model in self.model_list:
            _model_subject = _model.get_definition().get_subject_mesh()
            if self._subject_previous_name == _model_subject:
                model_to_rename = _model
        if model_to_rename:
            model_to_rename.get_definition().set_subject_mesh(subject_name)
            logger.info(f"Renamed subject '{self._subject_previous_name}' to '{subject_name}'.")
        else:
            error_message = (
                f"No model found for the checked subject '{self._subject_previous_name}'. Corrupted list.\n"
                "Please delete and re-add the items."
            )
            logger.error(error_message)

    # --------------------------------------------- Post Processing ---------------------------------------------
    def populate_post_process_tabs(self):
        """
        Populates the post-process tab widget with tabs for each available addon.
        """
        # Clear tabs
        self.view.post_tab_widget.clear()
        model = self.get_current_model()
        _definition = model.get_definition()

        if hasattr(_definition, "addons") and _definition.addons:
            for addon in _definition.addons:
                tab_widget = get_addon_tab_widget(addon=addon)
                if not tab_widget:
                    _name = addon.get_class_name()
                    logger.warning(f'Addon "{_name}" does not have a QT widget defined. Tab construction was skipped.')
                    continue
                initialized_widget = tab_widget(addon=addon, definition=model.get_definition())
                self.view.post_tab_widget.addTab(initialized_widget, addon.get_class_name())

    # --------------------------------------------- Generate Button ---------------------------------------------
    def generate_reshaped_meshes(self):
        """Runs the reshaping process"""
        subject_names = self.view.get_checked_meshes_subject_list()
        if not subject_names:
            logger.warning("No meshes checked. Please check at least one item in the list.")
            return

        for subject_name in subject_names:
            _model = self.get_model_by_subject(subject_name)
            if _model:
                _model.get_definition().morpher_generate_reshaped_subject_meshes()
            else:
                error_message = (
                    f"No model found for the checked subject '{subject_name}'. Corrupted list.\n"
                    "Please delete and re-add the items."
                )
                logger.error(error_message)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
