"""Controller for Offset Keyframes."""

import logging

import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)


class OffsetKeyframesController:
    """Connects Offset Keyframes view, model, and Maya service."""

    def __init__(self, model, view, service):
        """Initializes and displays the connected tool.

        Args:
            model (OffsetKeyframesModel): Persistent tool state.
            view (OffsetKeyframesView): Dockable Qt interface.
            service (OffsetKeyframesService): Maya runtime service.
        """
        self.model = model
        self.view = view
        self.service = service
        self.view.controller = self
        self.view.set_settings(self.model.get_settings())
        self._connect_view()
        self.view.show()
        ui_qt.QtCore.QTimer.singleShot(0, self.view.resize_to_contents)

    def _connect_view(self):
        """Connects all view signals."""
        self.view.offset_left_button.clicked.connect(lambda *args: self.offset(-1))
        self.view.offset_right_button.clicked.connect(lambda *args: self.offset(1))
        self.view.stagger_left_button.clicked.connect(lambda *args: self.stagger(-1))
        self.view.stagger_right_button.clicked.connect(lambda *args: self.stagger(1))
        for button in self.view.nudge_buttons:
            button.clicked.connect(
                lambda *args, widget=button: self.offset(widget.property("offset_amount"), absolute=True)
            )

    def _update_model(self):
        """Synchronizes and persists current widget settings."""
        self.model.set_settings(self.view.get_settings())
        self.model.save_preferences()

    def offset(self, direction, absolute=False):
        """Offsets selected keyframes.

        Args:
            direction (float): Signed direction or direct offset value.
            absolute (bool, optional): Whether direction already contains frames.
        """
        self._update_model()
        nodes = self.service.get_selection()
        if not nodes:
            self._warn("Nothing selected. Select animated objects and try again.")
            return
        offset = float(direction) if absolute else float(direction) * self.model.offset_amount
        try:
            result = self.service.offset(
                nodes=nodes,
                offset=offset,
                scope=self.model.scope,
                apply_euler_filter=self.model.apply_euler_filter,
            )
        except Exception as exception:
            logger.exception("Unable to offset keyframes.")
            self._warn(f"Offset failed: {exception}")
            return
        if not result.get("key_count"):
            self._warn("No matching time keys were found for the current scope.")
            return
        direction_name = "left" if offset < 0 else "right"
        message = (
            f"Moved {result['key_count']} key(s) on {len(result['curves'])} curve(s) "
            f"{abs(offset):g} frame(s) {direction_name}."
        )
        self.view.set_message(
            message,
            "success",
        )

    def stagger(self, direction):
        """Staggers selected keyframes in selection order.

        Args:
            direction (float): Signed stagger direction.
        """
        self._update_model()
        nodes = self.service.get_selection()
        if len(nodes) < 2:
            self._warn("Select at least two animated objects in the desired stagger order.")
            return
        step = float(direction) * self.model.stagger_step
        try:
            result = self.service.stagger(
                nodes=nodes,
                step=step,
                scope=self.model.scope,
                apply_euler_filter=self.model.apply_euler_filter,
            )
        except Exception as exception:
            logger.exception("Unable to stagger keyframes.")
            self._warn(f"Stagger failed: {exception}")
            return
        if not result.get("key_count"):
            self._warn("No matching time keys were found for the current scope.")
            return
        direction_name = "left" if step < 0 else "right"
        self.view.set_message(
            f"Staggered {result['key_count']} key(s) across {result['object_count']} object(s), "
            f"{abs(step):g} frame(s) per selection step {direction_name}.",
            "success",
        )

    def _warn(self, message):
        """Displays warning feedback in the view and Maya.

        Args:
            message (str): User-facing warning.
        """
        self.view.set_message(message, "warning")
        self.service.warn(message)
