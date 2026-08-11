"""Controller connecting Morphing Utilities model, view, and Maya service."""

import logging


logger = logging.getLogger(__name__)


class MorphingUtilitiesController:
    """Coordinates user actions and Maya scene operations."""

    def __init__(self, model, view, service):
        """Initializes and connects the tool components.

        Args:
            model (MorphingUtilitiesModel): Session state model.
            view (MorphingUtilitiesView): Qt interface.
            service (MorphingUtilitiesService): Maya runtime service.
        """
        self.model = model
        self.view = view
        self.service = service
        self.view.controller = self
        self._connect_view()
        self._sync_view()
        self.view.show()

    def _connect_view(self):
        """Connects view signals to controller actions."""
        self.view.flip_help_button.clicked.connect(
            lambda checked=False: self.view.show_help(topic="flip")
        )
        self.view.mirror_help_button.clicked.connect(
            lambda checked=False: self.view.show_help(topic="mirror")
        )
        self.view.load_source_button.clicked.connect(lambda checked=False: self.load_source())
        self.view.source_status_button.clicked.connect(
            lambda checked=False: self.select_loaded_source()
        )
        self.view.blend_node_list.currentTextChanged.connect(self.select_blend_node)
        self.view.delete_all_nodes_button.clicked.connect(
            lambda checked=False: self.delete_all_nodes()
        )
        self.view.delete_all_targets_button.clicked.connect(
            lambda checked=False: self.delete_all_targets()
        )
        self.view.rename_button.clicked.connect(lambda checked=False: self.rename_targets())
        self.view.flip_button.clicked.connect(
            lambda checked=False: self.duplicate_targets("flip")
        )
        self.view.mirror_button.clicked.connect(
            lambda checked=False: self.duplicate_targets("mirror")
        )
        self.view.set_values_button.clicked.connect(
            lambda checked=False: self.set_all_target_values()
        )
        self.view.extract_button.clicked.connect(
            lambda checked=False: self.extract_current_targets()
        )

    def _sync_view(self):
        """Synchronizes widgets with the initial model state."""
        settings = self.model.settings
        self.view.search_field.setText(settings["search_string"])
        self.view.replace_field.setText(settings["replace_string"])
        self.view.symmetry_axis_combo.setCurrentText(settings["symmetry_axis"])
        self.view.mirror_direction_combo.setCurrentText(settings["mirror_direction"])
        self.view.target_value_spinbox.setValue(settings["target_value"])
        self.view.set_source_status("Not loaded yet", "neutral")
        self.view.set_blend_nodes([])
        self.view.set_target_summary(0)
        self.view.set_status("Load a source mesh to begin.")
        self.view.set_target_operations_enabled(False)

    def load_source(self):
        """Loads one selected mesh and discovers its blend shape nodes."""
        selection = self.service.get_selection()
        if not selection:
            self._warn("Nothing selected. Select one source mesh and try again.")
            self._clear_source("Failed to load")
            return
        if len(selection) != 1:
            self._warn("Select only one source mesh and try again.")
            self._clear_source("Select one object")
            return

        source_object = selection[0]
        blend_nodes = self.service.get_blendshape_nodes(source_object)
        if not blend_nodes:
            self._warn(f'Unable to find blend shape nodes on "{source_object}".')
            self._clear_source("No blend shapes")
            return

        self.model.set_source_state(source_object, blend_nodes)
        self.view.set_source_status(source_object, "loaded")
        self.view.set_blend_nodes(blend_nodes)
        self.view.set_target_summary(0)
        self.view.set_target_operations_enabled(False)
        self.view.set_status(
            f"Loaded {source_object}. Select a blend shape node to continue.",
            "success",
        )

    def _clear_source(self, status_text):
        """Clears source-related state and updates the view.

        Args:
            status_text (str): Source status button text.
        """
        self.model.clear_scene_state()
        self.view.set_source_status(status_text, "failed")
        self.view.set_blend_nodes([])
        self.view.set_target_summary(0)
        self.view.set_target_operations_enabled(False)

    def select_loaded_source(self):
        """Selects the source object stored by the model."""
        if self.service.select_existing_object(self.model.morphing_object):
            self.view.set_status(f"Selected {self.model.morphing_object}.", "success")
            return
        self._warn("The loaded source object no longer exists. Load it again.")

    def select_blend_node(self, blend_node):
        """Stores the selected blend shape node and refreshes its target count.

        Args:
            blend_node (str): Blend shape node selected in the list.
        """
        blend_node = self.model.set_blend_node(blend_node)
        if not blend_node or not self.service.node_exists(blend_node):
            self.view.set_target_summary(0)
            self.view.set_target_operations_enabled(False)
            return
        target_count = len(self.service.get_target_names(blend_node))
        self.view.set_target_summary(target_count, blend_node)
        self.view.set_target_operations_enabled(True)
        self.view.set_status(f"Using {blend_node}.", "success")

    def delete_all_nodes(self):
        """Confirms and deletes all blendShape nodes in the scene."""
        if not self.view.confirm_action(
            "Delete Blend Shape Nodes",
            "Delete every blend shape node in the scene? This operation can be undone in Maya.",
        ):
            return
        try:
            with self.service.undo_chunk():
                deleted_count = self.service.delete_all_blendshape_nodes()
        except Exception as exception:
            logger.exception("Unable to delete blend shape nodes.")
            self._report_error(f"Delete failed: {exception}")
            return
        self._clear_source("No blend shapes")
        self.service.show_feedback(deleted_count, action="deleted")
        self.view.set_status(f"Deleted {deleted_count} blend shape node(s).", "success")

    def delete_all_targets(self):
        """Confirms and deletes all blendShape targets in the scene."""
        if not self.view.confirm_action(
            "Delete Blend Shape Targets",
            "Delete every blend shape target in the scene? This operation can be undone in Maya.",
        ):
            return
        try:
            with self.service.undo_chunk():
                deleted_count = self.service.delete_all_blendshape_targets()
        except Exception as exception:
            logger.exception("Unable to delete blend shape targets.")
            self._report_error(f"Delete failed: {exception}")
            return
        if self.model.blend_node:
            self.view.set_target_summary(0, self.model.blend_node)
        self.service.show_feedback(deleted_count, action="deleted")
        self.view.set_status(f"Deleted {deleted_count} blend shape target(s).", "success")

    def rename_targets(self):
        """Renames targets matching the current search and replacement fields."""
        self._update_model_from_view()
        if not self._validate_node_and_operation("rename"):
            return
        target_names = self.service.get_target_names(self.model.blend_node)
        rename_pairs = self.model.build_rename_pairs(target_names)
        try:
            with self.service.undo_chunk():
                result = self.service.rename_targets(self.model.blend_node, rename_pairs)
        except Exception as exception:
            logger.exception("Unable to rename blend shape targets.")
            self._report_error(f"Rename failed: {exception}")
            return
        self._report_operation(result, "renamed")

    def duplicate_targets(self, operation):
        """Duplicates filtered targets and flips or mirrors the new targets.

        Args:
            operation (str): Either ``flip`` or ``mirror``.
        """
        self._update_model_from_view()
        if not self._validate_node_and_operation(operation):
            return
        target_names = self.service.get_target_names(self.model.blend_node)
        duplicate_pairs = self.model.build_duplicate_pairs(target_names, operation)
        try:
            with self.service.undo_chunk():
                result = self.service.duplicate_targets(
                    blend_node=self.model.blend_node,
                    duplicate_pairs=duplicate_pairs,
                    operation=operation,
                    symmetry_axis=self.model.symmetry_axis,
                    mirror_direction=self.model.mirror_direction,
                )
        except Exception as exception:
            logger.exception("Unable to duplicate blend shape targets.")
            self._report_error(f"Duplicate failed: {exception}")
            return
        self._report_operation(result, f"duplicated {operation}")

    def set_all_target_values(self):
        """Sets every target weight on the selected blend shape node."""
        self._update_model_from_view()
        if not self._validate_node_and_operation("set values", requires_search=False):
            return
        try:
            with self.service.undo_chunk():
                result = self.service.set_all_target_values(
                    self.model.blend_node,
                    self.model.target_value,
                )
        except Exception as exception:
            logger.exception("Unable to set blend shape target values.")
            self._report_error(f"Set values failed: {exception}")
            return
        self._report_operation(result, "set")

    def extract_current_targets(self):
        """Extracts the selected blend shape targets as independent meshes."""
        if not self._validate_node_and_operation("extract", requires_search=False):
            return
        try:
            with self.service.undo_chunk():
                result = self.service.bake_current_state(self.model.blend_node)
        except Exception as exception:
            logger.exception("Unable to extract current blend shape targets.")
            self._report_error(f"Extract failed: {exception}")
            return
        count = result.get("created", 0)
        errors = result.get("errors", [])
        if errors:
            self._report_error(
                f"Extracted {count} target(s); {len(errors)} operation(s) failed."
            )
        else:
            self.service.show_feedback(count, action="extracted")
            self.view.set_status(f"Extracted {count} target mesh(es).", "success")

    def _update_model_from_view(self):
        """Copies editable widget values into the model."""
        self.model.set_search_replace(
            self.view.search_field.text(),
            self.view.replace_field.text(),
        )
        self.model.set_mirror_settings(
            self.view.symmetry_axis_combo.currentText(),
            self.view.mirror_direction_combo.currentText(),
        )
        self.model.set_target_value(self.view.target_value_spinbox.value())

    def _validate_node_and_operation(self, operation, requires_search=True):
        """Validates the selected node and requested operation.

        Args:
            operation (str): Operation label.
            requires_search (bool): Whether the model operation validation applies.

        Returns:
            bool: True when execution can continue.
        """
        if not self.model.blend_node or not self.service.node_exists(self.model.blend_node):
            self._warn("Select a valid blend shape node before running this operation.")
            return False
        if requires_search:
            is_valid, message = self.model.validate_operation(operation)
            if not is_valid:
                self._warn(message)
                return False
        return True

    def _report_operation(self, result, action):
        """Reports a service result in the view and Maya.

        Args:
            result (dict): Service result dictionary.
            action (str): Action description.
        """
        succeeded = result.get("succeeded", 0)
        errors = result.get("errors", [])
        self.service.show_feedback(succeeded, action=action)
        if errors:
            self._report_error(f"Completed {succeeded}; {len(errors)} item(s) failed.")
        else:
            self.view.set_status(f"{succeeded} target(s) {action}.", "success")
        self._refresh_target_summary()

    def _refresh_target_summary(self):
        """Refreshes the selected node target count after an operation."""
        if not self.model.blend_node:
            return
        count = len(self.service.get_target_names(self.model.blend_node))
        self.view.set_target_summary(count, self.model.blend_node)

    def _warn(self, message):
        """Shows a routine warning in both Maya and the tool status label.

        Args:
            message (str): Warning message.
        """
        self.service.warn(message)
        self.view.set_status(message, "warning")

    def _report_error(self, message):
        """Shows an operation error without hiding the detailed log.

        Args:
            message (str): Error message.
        """
        logger.error(message)
        self.view.set_status(message, "error")
        self.service.warn(message)


if __name__ == "__main__":
    print('Run Morphing Utilities from "__init__.py".')
