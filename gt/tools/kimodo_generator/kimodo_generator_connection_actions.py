"""Main-thread connection state, deployment step locking, and bounded progress polling."""

import time

from gt.ui import qt_import as ui_qt
from gt.utils import kimodo
from gt.tools.kimodo_generator import kimodo_generator_docker_inspection as inspection

LIFECYCLE_OPERATIONS = ("prepare_docker", "build_docker", "connect", "stop_bridge", "restart_bridge",
                        "inspect_image_removal", "remove_docker_image")


class KimodoConnectionActions:
    """Keeps connection state separate from persistent authoring/settings data."""

    def initialize_connection_state(self):
        """Initializes a connection indicator and a guarded, lightweight UI timer."""
        self.connection_state = "disconnected"
        self.encoder_ready = False
        self._encoder_ready_since = None
        self._last_health_check = time.monotonic()
        self._build_directory = None
        self._build_log_offset = 0
        self.connection_timer = ui_qt.QtCore.QTimer(self.view)
        self.connection_timer.setInterval(1000)
        self.connection_timer.timeout.connect(self.refresh_connection_status)
        self.connection_timer.start()

    def update_mode_settings(self, mode):
        """Shows applicable launch controls and preserves separate Python environments.

        Args:
            mode (str): Selected launch mode.
        """
        previous = getattr(self, "_settings_mode", None)
        if not self.loading and previous != mode:
            profiles = self.model.launch_settings
            fields = {"python_path": self.view.python_path.text(),
                      "distribution": self.view.distribution.currentText(),
                      "text_encoder_url": self.view.encoder_url.text(), "device": self.view.device.currentText(),
                      "start_encoder": self.view.start_encoder.isChecked(),
                      "show_console": self.view.show_console.isChecked()}
            if previous in ("wsl", "native"):
                profiles[previous] = fields
            if mode in ("wsl", "native"):
                settings = profiles.get(mode, {"python_path": "", "distribution": "",
                                               "text_encoder_url": "http://127.0.0.1:9550", "device": "auto",
                                               "start_encoder": True, "show_console": True})
                self.view.python_path.setText(settings["python_path"])
                self.view.distribution.setCurrentText(settings["distribution"])
                self.view.encoder_url.setText(settings["text_encoder_url"])
                self.view.device.setCurrentText(settings["device"])
                self.view.start_encoder.setChecked(settings["start_encoder"])
                self.view.show_console.setChecked(settings["show_console"])
                self.model.connection.update(settings)
            self.model.connection["mode"] = mode
            self.model.save_preferences()
        self._settings_mode = mode
        self.view.python_group.setVisible(mode in ("wsl", "native"))
        title = "WSL Launch Settings" if mode == "wsl" else "Windows Launch Settings"
        self.view.python_group.toggle_button.setText(title)
        if mode in self.model.launch_expanded:
            button = self.view.python_group.toggle_button
            blocked = button.blockSignals(True)
            button.setChecked(self.model.launch_expanded[mode])
            button.blockSignals(blocked)
            self.view.python_content.setVisible(button.isChecked())
            button.setArrowType(ui_qt.QtCore.Qt.ArrowType.DownArrow if button.isChecked()
                                else ui_qt.QtCore.Qt.ArrowType.RightArrow)
        self.view.distribution_row.setVisible(mode == "wsl")
        self.view.distribution_label.setVisible(mode == "wsl")
        self.view.existing_group.setVisible(mode == "existing")
        self.view.token.setVisible(mode != "docker")
        self.view.token_label.setVisible(mode != "docker")

    def set_connection_state(self, state):
        """Updates the persistent status indicator and connection/setup controls.

        Args:
            state (str): disconnected, connecting, connected, or failed.
        """
        self.connection_state = state
        if state != "connected":
            self.encoder_ready = False
            self._encoder_ready_since = None
            self.view.docker_encoder_group.hide()
        self._last_health_check = time.monotonic()
        self.view.set_connection_status(
            "loading" if state == "connected" and self.model.connection["mode"] == "docker"
            and not self.encoder_ready else state,
            "Encoder Loading" if state == "connected" and self.model.connection["mode"] == "docker"
            and not self.encoder_ready else None)
        self.update_launch_fields()

    def update_connection_controls(self):
        """Locks setup mutations during a connection or lifecycle operation."""
        busy = any(key in self.pending for key in LIFECYCLE_OPERATIONS)
        locked = busy or self.connection_state in ("connected", "connecting")
        for widget in (self.view.mode, self.view.url, self.view.auto_connect, self.view.docker_directory,
                       self.view.docker_executable, self.view.docker_image_name, self.view.docker_stable_revisions):
            widget.setEnabled(not locked)
        for key in ("browse_docker", "find_docker", "prepare_docker", "build_docker", "remove_docker_image"):
            self.view.buttons[key].setEnabled(not locked)
        self.view.buttons["connect"].setEnabled(not locked and "test_bridge" not in self.pending)
        self.view.buttons["disconnect_bridge"].setEnabled(self.connection_state == "connected" and not busy)
        self.view.buttons["restart_bridge"].setEnabled(
            self.view.mode.currentData() != "existing" and not locked)
        self.view.buttons["stop_bridge"].setEnabled(self.connection_state == "connected" and not busy)
        self.view.buttons["reset_connection_settings"].setEnabled(not locked)
        for key in self.pending:
            if key in self.view.buttons:
                self.view.buttons[key].setEnabled(False)

    def disconnect_bridge(self):
        """Releases the UI connection while leaving the server and accepted jobs running."""
        self.last_connection = None
        self.encoder_ready = False
        self.view.docker_encoder_group.hide()
        self.set_connection_state("disconnected")
        self.message("Disconnected from the bridge. Its server and accepted jobs continue running.")

    def refresh_connection_status(self):
        """Refreshes local progress and schedules infrequent HTTP-only health checks."""
        if self.closed or not self._view_is_valid():
            return
        building = "build_docker" in self.pending
        self.view.docker_build_group.setVisible(building)
        if building and self._build_directory:
            self.view.docker_build_label.setText(inspection.build_progress(
                self._build_directory, self._build_log_offset))
        connected = self.connection_state == "connected"
        docker_mode = self.model.connection["mode"] == "docker"
        if self.encoder_ready:
            if self._encoder_ready_since is None:
                self._encoder_ready_since = time.monotonic()
        else:
            self._encoder_ready_since = None
        show_progress = not self.encoder_ready or time.monotonic() - self._encoder_ready_since < 2
        self.view.docker_encoder_group.setVisible(connected and docker_mode and show_progress)
        if connected and docker_mode:
            self.view.set_connection_status("connected" if self.encoder_ready else "loading",
                                            None if self.encoder_ready else "Encoder Loading")
        if connected and docker_mode:
            progress = inspection.encoder_progress(self.model.docker["directory"])
            if self.encoder_ready:
                progress = {"stage": "ready", "detail": "Text encoder ready.", "percent": 100}
            elif progress["stage"] == "ready":
                progress = {"stage": "loading", "detail": "Confirming encoder readiness..."}
            self.view.docker_encoder_label.setText(progress["detail"])
            self.view.docker_encoder_label.setStyleSheet(
                "color: #e28686;" if progress["stage"] == "failed" else "")
            self.view.docker_encoder_progress.setVisible(progress["stage"] != "unknown")
            measured = progress.get("percent")
            if progress["stage"] == "failed":
                self.view.docker_encoder_progress.setRange(0, 100)
                self.view.docker_encoder_progress.setValue(0)
            elif measured is not None or progress["stage"] == "ready":
                self.view.docker_encoder_progress.setRange(0, 100)
                self.view.docker_encoder_progress.setValue(measured if measured is not None else 100)
            else:
                self.view.docker_encoder_progress.setRange(0, 0)
        if not connected or not self.last_connection or "connection_health" in self.pending:
            return
        if time.monotonic() - self._last_health_check < 10:
            return
        self._last_health_check = time.monotonic()
        connection = kimodo.KimodoConnection(url=self.last_connection.url, token=self.last_connection.token, timeout=3)
        check_encoder = docker_mode

        def operation():
            """Checks HTTP health without querying Docker or touching Maya scene data.

            Returns:
                tuple: Bridge health and optional encoder readiness.
            """
            client = kimodo.KimodoClient(connection)
            health = client.health()
            ready = None
            if check_encoder:
                try:
                    ready = client.test_text_encoder().get("status") == "ready"
                except (kimodo.KimodoEncoderUnavailable, ValueError):
                    ready = False
            return health, ready

        def ready(payload):
            """Applies readiness information from the background probe.

            Args:
                payload (tuple): Bridge health and optional encoder readiness.
            """
            if payload[1] is not None:
                self.encoder_ready = payload[1]
        self.run_network("connection_health", operation, ready)
