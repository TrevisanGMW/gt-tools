"""Controller for the Render Calculator MVC tool."""

import logging


logger = logging.getLogger(__name__)


class RenderCalculatorController:
    """Connects the view to its model and Maya timeline."""

    def __init__(self, model, view, maya_cmds=None):
        """Initializes the controller and wires view signals.

        Args:
            model (RenderCalculatorModel): Calculator state and pure logic.
            view (RenderCalculatorView): Calculator Qt view.
            maya_cmds (module, optional): Injected ``maya.cmds`` module for tests.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self._maya_cmds = maya_cmds
        self._connect_view()
        self._sync_view_from_model()
        self._initialize_frame_count()
        self._refresh_result()
        self.view.show()

    def _connect_view(self):
        """Connects widget signals to model updates and controller actions."""
        self._connect_value_field(
            self.view.time_per_frame_spinbox,
            self.model.set_time_per_frame,
        )
        self._connect_value_field(
            self.view.num_frames_spinbox,
            self.model.set_num_frames,
        )
        self._connect_value_field(
            self.view.num_machines_spinbox,
            self.model.set_num_machines,
        )
        self.view.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        self.view.get_current_button.clicked.connect(
            lambda *args: self.get_current_frame_count()
        )
        self.view.reset_button.clicked.connect(
            lambda *args: self.reset_numbers()
        )

    def _connect_value_field(self, spinbox, update_model):
        """Connects a numeric input representing one model value.

        Args:
            spinbox (QSpinBox): Numeric input.
            update_model (callable): Model setter for the value.
        """
        spinbox.valueChanged.connect(update_model)
        spinbox.valueChanged.connect(self._refresh_result)

    def _on_unit_changed(self, unit_label):
        """Updates the model and result after a unit selection changes.

        Args:
            unit_label (str): Selected combo-box display label.
        """
        self.model.set_unit(unit_label)
        self._refresh_result()

    def _sync_view_from_model(self):
        """Copies the initial model state into the view."""
        self.view.set_input_values(
            time_per_frame=self.model.time_per_frame,
            num_frames=self.model.num_frames,
            num_machines=self.model.num_machines,
            unit=self.model.unit,
        )

    def _refresh_result(self, *args):
        """Rebuilds the output text from the current model state.

        Args:
            *args: Ignored Qt signal arguments.
        """
        self.view.set_result_text(self.model.get_render_summary())

    def _initialize_frame_count(self):
        """Uses Maya's current playback range for the initial frame count."""
        if self.model.has_persisted_frame_count:
            return
        try:
            frame_count = self._get_timeline_frame_count()
        except ImportError:
            logger.debug("Render Calculator is being initialized outside Maya.")
            return
        except Exception as exception:
            logger.warning("Unable to initialize the timeline frame count: %s", exception)
            return

        self.model.set_num_frames(frame_count)
        self.view.set_frame_count(self.model.num_frames)

    def reset_numbers(self):
        """Resets all numeric inputs, updates the view, and saves the values."""
        self.model.reset_numbers()
        self._sync_view_from_model()
        self._refresh_result()
        self.view.set_status("")

    def get_current_frame_count(self):
        """Loads the inclusive Maya playback range into the frame input."""
        try:
            frame_count = self._get_timeline_frame_count()
            self.model.set_num_frames(frame_count)
            self.view.set_frame_count(self.model.num_frames)
            self.view.set_status("")
            self._refresh_result()
        except Exception as exception:
            logger.exception("Unable to read the Maya playback range.")
            self.view.set_status(
                f"Unable to read the current timeline: {exception}",
                is_error=True,
            )
            self._warn_in_maya(str(exception))

    def _get_timeline_frame_count(self):
        """Gets the inclusive frame count from Maya playback options.

        Returns:
            int: Number of frames between Maya's minimum and maximum time.
        """
        maya_cmds = self._get_maya_cmds()
        start_frame = maya_cmds.playbackOptions(query=True, min=True)
        end_frame = maya_cmds.playbackOptions(query=True, max=True)
        return max(1, int(end_frame - start_frame + 1))

    def _get_maya_cmds(self):
        """Gets the Maya commands module lazily.

        Returns:
            module: Maya commands module.
        """
        if self._maya_cmds is None:
            from maya import cmds

            self._maya_cmds = cmds
        return self._maya_cmds

    def _warn_in_maya(self, message):
        """Writes a warning through Maya when the runtime is available.

        Args:
            message (str): Warning message to show.
        """
        try:
            self._get_maya_cmds().warning(message)
        except Exception:
            logger.debug("Unable to send Render Calculator warning to Maya.")
