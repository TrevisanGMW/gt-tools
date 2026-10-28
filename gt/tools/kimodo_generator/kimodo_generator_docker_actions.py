"""Qt controller actions for one explicitly selected local Docker deployment."""

import os
from gt.ui import qt_import as ui_qt
from gt.tools.kimodo_generator import kimodo_generator_docker as docker_runtime
from gt.tools.kimodo_generator import kimodo_generator_docker_inspection as inspection
from gt.utils import kimodo

QtWidgets = ui_qt.QtWidgets


class KimodoDockerActions:
    """Binds local deployment services to the owning MVC's background dispatcher."""

    def _docker_settings(self, allow_connected=False):
        """Captures settings and prevents overlapping lifecycle mutations.

        Args:
            allow_connected (bool): Allow read/control actions on the connected deployment.

        Returns:
            dict: Detached deployment folder and executable settings.
        """
        if any(key in self.pending for key in ("prepare_docker", "build_docker", "connect",
                                               "stop_bridge", "restart_bridge", "inspect_image_removal",
                                               "remove_docker_image")):
            raise ValueError("Wait for the current Docker/bridge operation to finish.")
        if not allow_connected and self.connection_state in ("connected", "connecting"):
            raise ValueError("Disconnect or stop the bridge before changing its deployment or building an image.")
        self.gather_connection()
        settings = dict(self.model.docker)
        docker_runtime.deployment_directory(settings["directory"])
        return settings

    def browse_docker(self):
        """Selects a dedicated folder without creating or starting services."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self.view, "Kimodo Docker Deployment Folder", self.view.docker_directory.text())
        if directory:
            self.view.docker_directory.setText(directory)
            self.save_docker_settings()

    def open_docker(self):
        """Creates a chosen deployment directory if needed and opens it without preparing services."""
        directory = docker_runtime.deployment_directory(self.view.docker_directory.text().strip())
        directory.mkdir(parents=True, exist_ok=True)
        if not directory.is_dir():
            raise ValueError("The deployment folder could not be created.")
        opened = ui_qt.QtGui.QDesktopServices.openUrl(ui_qt.QtCore.QUrl.fromLocalFile(str(directory)))
        self.message(f"Deployment folder: {directory}" if opened else f"Could not open deployment folder: {directory}")

    def save_docker_settings(self):
        """Persists an explicitly chosen deployment folder and optional CLI path."""
        if not self.loading:
            self.model.docker.update(directory=self.view.docker_directory.text().strip(),
                                     executable=self.view.docker_executable.text().strip(),
                                     image_name=self.view.docker_image_name.text().strip(),
                                     use_stable_revisions=self.view.docker_stable_revisions.isChecked())
            self.model.save_preferences()

    def find_docker(self):
        """Finds and saves the Docker CLI without preparing or starting a deployment."""
        executable = docker_runtime.find_docker()
        self.view.docker_executable.setText(executable)
        self.save_docker_settings()
        self.message(f"Docker executable found: {executable}")

    def prepare_docker(self):
        """Prepares configuration and copies an available local HF credential once."""
        settings = self._docker_settings()

        def ready(metadata):
            """Reports prepared deployment identity without exposing its credentials.

            Args:
                metadata (dict): Persistent project identity.
            """
            self.message(
                f"Prepared {metadata['project_name']}. Configure secrets/hf_token if needed, then Build Image.")
        self.run_network("prepare_docker", lambda: docker_runtime.prepare_deployment(
            settings["directory"], use_stable_revisions=settings["use_stable_revisions"],
            executable=settings["executable"], image_name=settings["image_name"]), ready)

    def build_docker(self):
        """Builds the selected source policy asynchronously, retaining detailed output."""
        settings = self._docker_settings()
        self._build_directory = settings["directory"]
        log_path = os.path.join(settings["directory"], "logs", "build.log")
        self._build_log_offset = os.path.getsize(log_path) if os.path.isfile(log_path) else 0
        self.message(f"Building Kimodo image. Progress: {os.path.join(settings['directory'], 'logs', 'build.log')}")

        def ready(path):
            """Reports build completion without interrupting a running service.

            Args:
                path (str): Persistent build log.
            """
            metadata = docker_runtime.read_deployment(settings["directory"])
            revision_source = metadata.get("revision_source", "selected").replace("_", " ")
            self.message(
                f"Docker image built using {revision_source} revisions. Connect / Start or Restart. Log: {path}")
        self.run_network("build_docker", lambda: docker_runtime.build_image(
            settings["directory"], settings["executable"], settings["use_stable_revisions"],
            settings["image_name"]), ready)

    def docker_logs(self):
        """Opens refreshing container logs without relying on unsupported Desktop routes."""
        self.gather_connection()
        settings = dict(self.model.docker)
        service = self.view.docker_log_service.currentData()
        directory = str(docker_runtime.deployment_directory(settings["directory"]))
        dialog = QtWidgets.QDialog(self.view)
        dialog.setWindowTitle(f"Kimodo Docker Logs - {service}")
        dialog.resize(880, 520)
        layout = QtWidgets.QVBoxLayout(dialog)
        note = QtWidgets.QLabel(
            "Live container output; refreshes every 3 seconds. Docker Desktop can also show these logs "
            "under Containers > your Kimodo deployment > the selected service.")
        note.setWordWrap(True)
        layout.addWidget(note)
        output = QtWidgets.QPlainTextEdit()
        output.setReadOnly(True)
        output.setMaximumBlockCount(1000)
        output.setPlainText("Reading container logs...")
        layout.addWidget(output)
        desktop = QtWidgets.QPushButton("Open Docker Desktop")
        desktop.setToolTip("Open Docker Desktop, then select the container's Logs tab.")
        desktop.clicked.connect(lambda: ui_qt.QtGui.QDesktopServices.openUrl(
            ui_qt.QtCore.QUrl("docker-desktop://dashboard/open")))
        layout.addWidget(desktop)
        timer = ui_qt.QtCore.QTimer(dialog)
        timer.setInterval(3000)
        state = {"open": True}

        def closed(unused_result):
            """Stops refresh after closing the window.

            Args:
                unused_result (int): Dialog result.
            """
            state["open"] = False
            timer.stop()

        def received(text):
            """Updates logs without pulling the scrollbar away from a reader.

            Args:
                text (str): Bounded container output.
            """
            if not state["open"]:
                return
            scrollbar = output.verticalScrollBar()
            following = scrollbar.value() == scrollbar.maximum()
            position = scrollbar.value()
            output.setPlainText(text or "No container output yet. Use Connect / Start if it is stopped.")
            scrollbar.setValue(scrollbar.maximum() if following else position)

        def read_logs():
            """Reads output or returns an actionable error to the log window.

            Returns:
                str: Container output or diagnostic message.
            """
            try:
                return docker_runtime._compose(
                    directory, ["logs", "--no-color", "--tail", "200", service], settings["executable"])
            except (RuntimeError, ValueError, OSError) as error:
                return f"Could not read {service} logs: {error}"

        def refresh():
            """Reads a bounded snapshot asynchronously while the dialog remains open."""
            if not state["open"] or self.closed or "docker_logs" in self.pending:
                return
            self.run_network("docker_logs", read_logs, received)

        dialog.finished.connect(closed)
        timer.timeout.connect(refresh)
        self.docker_logs_dialog = dialog
        dialog.show()
        timer.start()
        refresh()

    def remove_docker_image(self):
        """Previews stopped-container/image removal, then requests explicit confirmation."""
        settings = self._docker_settings()

        def preview_ready(preview):
            """Shows the precise image and stopped containers before requesting removal.

            Args:
                preview (dict): Revalidated, project-scoped removal plan.
            """
            containers = ", ".join(preview["containers"]) or "none"
            answer = QtWidgets.QMessageBox.question(
                self.view, "Remove Kimodo Deployment Image",
                f"Remove image {preview['image']}?\nStopped containers to remove: {containers}\n\n"
                "Models, jobs, credentials, sources, and logs stay in the deployment folder. "
                "No global cleanup is performed. You must build an image before starting again.",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No)
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return

            def removed(image):
                """Reports a completed image removal without deleting persistent data.

                Args:
                    image (str): Removed image reference.
                """
                self.set_connection_state("disconnected")
                self.message(
                    f"Removed {image}. Choose stable revisions if needed, then Build Image and Connect / Start.")
            self.run_network("remove_docker_image", lambda: inspection.remove_image(
                settings["directory"], preview["image_id"], settings["executable"]), removed)
        self.run_network("inspect_image_removal", lambda: inspection.image_removal_preview(
            settings["directory"], settings["executable"]), preview_ready)

    def stop_docker_bridge(self, connection):
        """Confirms stopping the idle local project, retaining jobs and model caches.

        Args:
            connection (KimodoConnection): Authenticated local deployment connection.
        """
        settings = self._docker_settings(allow_connected=True)
        answer = QtWidgets.QMessageBox.question(
            self.view, "Stop Kimodo Docker Deployment",
            f"Stop the bridge and text encoder in {settings['directory']}?\n\n"
            "The bridge refuses while jobs are active. "
            "Configuration, credentials, models, jobs, and logs are retained.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        def ready(result):
            """Reports the stopped project in the connection status field.

            Args:
                result (dict): Shutdown acknowledgement.
            """
            self.view.connection_info.setText(f"Docker deployment stopped: {settings['directory']}")
            self.encoder_ready = False
            self.set_connection_state("disconnected")
            self.message("Docker bridge and encoder stopped. All persistent data was retained.")
        self.run_network("stop_bridge", lambda: docker_runtime.stop(
            settings["directory"], connection, settings["executable"]), ready)

    def restart_docker_bridge(self, connection):
        """Recreates one idle local deployment using its latest built image.

        Args:
            connection (KimodoConnection): Authenticated local deployment connection.
        """
        settings = self._docker_settings(allow_connected=True)
        answer = QtWidgets.QMessageBox.question(
            self.view, "Restart Kimodo Docker Deployment",
            "Restart this deployment's bridge and encoder using its latest built image?\n\n"
            "Build Image first after updating bridge code. Active jobs prevent restart. Persistent data is retained.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        def operation():
            """Stops the verified deployment, then starts its configured image.

            Returns:
                tuple: Replacement bridge health, capabilities and skeleton.
            """
            docker_runtime.stop(settings["directory"], connection, settings["executable"])
            health = docker_runtime.start(settings["directory"], connection, settings["executable"])
            client = kimodo.KimodoClient(connection)
            return health, client.capabilities(), client.skeleton()

        def ready(payload):
            """Applies replacement metadata on Qt's main thread.

            Args:
                payload (tuple): Health, capabilities and rest motion.
            """
            health, self.model.capabilities, self.model.rest_motion = payload
            self.last_connection = connection
            self.tokens_by_url[connection.url] = connection.token
            self.populate_models()
            self.model.save_preferences()
            self.view.connection_info.setText(self._bridge_status_text(health, connection))
            self.set_connection_state("connected")
            self.message("Docker deployment restarted. Test Text Encoder to check model startup progress.")
        self.run_network("restart_bridge", operation, ready)
