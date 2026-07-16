"""Controller for World Space Baker."""

import logging

import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)


class WorldSpaceBakerController:
    """Connects the World Space Baker model, view, and Maya service."""

    def __init__(self, model, view, service):
        """Initializes and displays the connected tool.

        Args:
            model (WorldSpaceBakerModel): Session-state model.
            view (WorldSpaceBakerView): Qt interface.
            service (WorldSpaceBakerService): Maya runtime service.
        """
        self.model = model
        self.view = view
        self.service = service
        self.view.controller = self
        self._connect_view()
        self.view.set_frame_range(self.model.start_frame, self.model.end_frame)
        self.view.show()
        ui_qt.QtCore.QTimer.singleShot(0, self.view.resize_to_contents)

    def _connect_view(self):
        """Connects all view signals to controller actions."""
        self.view.load_selection_button.clicked.connect(self.load_selection)
        self.view.target_status_button.clicked.connect(self.select_loaded_targets)
        self.view.get_start_button.clicked.connect(lambda *args: self.set_current_frame("start"))
        self.view.get_end_button.clicked.connect(lambda *args: self.set_current_frame("end"))
        self.view.start_frame_spinbox.valueChanged.connect(self.update_frame_range)
        self.view.end_frame_spinbox.valueChanged.connect(self.update_frame_range)
        self.view.extract_button.clicked.connect(self.extract_world_space)
        self.view.bake_button.clicked.connect(self.bake_world_space)
        self.view.help_button.clicked.connect(self.view.show_help)

    def load_selection(self):
        """Loads the current Maya selection as extraction targets."""
        targets = self.service.get_selection()
        if not targets:
            self.model.set_targets([])
            self.view.set_target_state("Failed to Load", "error")
            self.view.stored_status_label.setText("No Data")
            self.view.set_workflow_enabled(False)
            self.view.set_message("Nothing selected. Select at least one object and try again.", "warning")
            self.service.warn("Nothing selected. Please select at least one object.")
            return
        self.model.set_targets(targets)
        self.view.set_target_state(self.model.get_target_label(), "loaded")
        self.view.stored_status_label.setText("No Data")
        self.view.set_workflow_enabled(True)
        self.view.set_message(f"Loaded {len(targets)} target(s).", "success")

    def select_loaded_targets(self):
        """Selects all loaded targets that still exist."""
        if not self.model.targets:
            self.view.set_message("No targets are loaded.", "warning")
            return
        existing, missing = self.service.select_existing(self.model.targets)
        if missing:
            self.view.set_message(f"Selected {len(existing)} target(s); {len(missing)} are missing.", "warning")
            return
        self.view.set_message(f"Selected {len(existing)} loaded target(s).", "success")

    def set_current_frame(self, target_field):
        """Copies the current timeline frame into a range field.

        Args:
            target_field (str): Start or end field key.
        """
        current_frame = self.service.get_current_frame()
        if target_field == "start":
            self.view.start_frame_spinbox.setValue(current_frame)
        else:
            self.view.end_frame_spinbox.setValue(current_frame)
        self.update_frame_range()

    def update_frame_range(self):
        """Synchronizes frame inputs into the session model."""
        start_frame, end_frame = self.view.get_frame_range()
        self.model.set_frame_range(start_frame, end_frame)

    def extract_world_space(self):
        """Validates and extracts world-space data for loaded targets."""
        self.update_frame_range()
        is_valid, message = self.model.validate_frame_range()
        if not is_valid:
            self.view.set_message(message, "warning")
            self.service.warn(message)
            return
        try:
            animation_data = self.service.extract(
                targets=self.model.targets,
                start_frame=self.model.start_frame,
                end_frame=self.model.end_frame,
            )
        except Exception as exception:
            logger.exception("Unable to extract world-space animation.")
            message = f"Extraction failed: {exception}"
            self.view.set_message(message, "error")
            self.service.warn(message)
            return
        self.model.set_animation_data(animation_data)
        if not animation_data:
            self.view.stored_status_label.setText("No Data")
            self.view.set_workflow_enabled(bool(self.model.targets), has_data=False)
            message = "No animatable translate or rotate data was found on the loaded targets."
            self.view.set_message(message, "warning")
            self.service.warn(message)
            return
        self.view.stored_status_label.setText(self.model.get_stored_summary())
        self.view.set_workflow_enabled(True, has_data=True)
        self.view.set_message("World-space animation extracted successfully.", "success")

    def bake_world_space(self):
        """Bakes the currently stored samples onto their source objects."""
        if not self.model.animation_data:
            message = "No extracted world-space data is available."
            self.view.set_message(message, "warning")
            self.service.warn(message)
            return
        try:
            result = self.service.bake(self.model.animation_data)
        except Exception as exception:
            logger.exception("Unable to bake world-space animation.")
            message = f"Bake failed: {exception}"
            self.view.set_message(message, "error")
            self.service.warn(message)
            return
        baked_count = result.get("baked", 0)
        missing_count = result.get("missing", 0)
        if not baked_count:
            message = "No stored targets could be baked. They may no longer exist."
            self.view.set_message(message, "warning")
            self.service.warn(message)
            return
        message = f"Baked world-space animation onto {baked_count} target(s)."
        level = "success"
        if missing_count:
            message += f" Skipped {missing_count} missing target(s)."
            level = "warning"
        self.view.set_message(message, level)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
