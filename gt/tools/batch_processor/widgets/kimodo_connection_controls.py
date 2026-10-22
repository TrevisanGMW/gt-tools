"""Connection discovery actions for Kimodo task panels; HTTP work stays off the UI thread."""

import copy
from functools import partial

from gt.ui import qt_import as qt
from gt.utils import kimodo
from gt.tools.batch_processor.tasks import task_kimodo_connection as connections


class QuerySignals(qt.QtCore.QObject):
    """Delivers plain HTTP query results to the main Qt thread."""

    finished = qt.QtCore.Signal(object, object)


class BridgeQuery(qt.QtCore.QRunnable):
    """Queries metadata without starting services, importing Maya, or submitting jobs."""

    def __init__(self, connection, settings):
        """Captures validated transport settings.

        Args:
            connection (KimodoConnection): HTTP endpoint and runtime credentials.
            settings (dict): Resolved credential references and expected deployment.
        """
        super().__init__()
        self.connection = connection
        self.settings = settings
        self.signals = QuerySignals()

    def run(self):
        """Emits health and current model metadata, or a readable error."""
        try:
            client = kimodo.KimodoClient(self.connection)
            result = {"health": connections.check_health(client, self.settings),
                      "models": client.capabilities()["models"]}
        except Exception as error:
            self.signals.finished.emit(None, connections.connection_error(error))
        else:
            self.signals.finished.emit(result, None)


class KimodoConnectionControls:
    """Adds connection copying and read-only model discovery to task widgets."""

    def use_generator_connection(self):
        """Copies saved connection references while leaving generator credentials private."""
        try:
            settings = connections.generator_settings()
            # Update bound fields rather than rebuilding a widget inside its callback.
            for path, control in self.controls.items():
                if path[0] not in ("connection", "docker"):
                    continue
                value = settings[path[0]].get(path[1])
                if value is None:
                    continue
                if isinstance(control, qt.QtWidgets.QComboBox):
                    control.setCurrentIndex(control.findData(value))
                elif isinstance(control, qt.QtWidgets.QCheckBox):
                    control.setChecked(value)
                elif isinstance(control, qt.QtWidgets.QLineEdit):
                    control.setText(str(value))
                else:
                    control.setValue(value)
            try:
                connections.docker.validate_local_url(settings["connection"]["url"])
            except ValueError:
                policy = "environment"
            else:
                policy = "auto"
            self.controls[("token_environment",)].setText("")
            self.controls[("authentication",)].setCurrentIndex(
                self.controls[("authentication",)].findData(policy))
            self.status.setText("Copied connection references. Local credentials are automatic; "
                                "remote credentials need a token variable name.")
        except Exception as error:
            self.status.setText(str(error))

    def update_authentication_controls(self):
        """Shows credential provenance and enables only the active credential fields."""
        settings = self.task.settings
        mode = settings["connection"]["mode"]
        policy = settings.get("authentication", "auto")
        control = self.controls[("authentication",)]
        blocked = control.blockSignals(True)
        control.setCurrentIndex(control.findData("auto" if mode == "docker" else policy))
        control.blockSignals(blocked)
        self.set_field_enabled("authentication", mode != "docker")
        self.set_field_enabled("token_environment", mode != "docker" and policy == "environment")
        self.set_field_enabled(("docker", "directory"), mode == "docker" or (mode == "existing" and policy == "auto"))
        self.set_field_enabled(("docker", "executable"), mode == "docker")
        if mode == "docker":
            note = ("Reads secrets/bridge_token from the selected local deployment automatically. "
                    "Choose a prepared deployment or Use Saved Generator Connection. No environment setup is needed.")
        elif policy == "auto":
            note = ("Automatic: reads the selected local deployment's token. If blank, uses the saved Generator "
                    "deployment for a matching localhost URL. No environment setup is needed for local Docker. "
                    "Remote bridge: choose Environment variable.")
        elif policy == "environment":
            note = ("Enter a variable NAME below, not the token value. Set that variable to the remote bridge's "
                    "token before launching Maya; workers inherit Maya's environment. Tokens are never saved here.")
        else:
            note = ("Sends no token. Use only for a bridge configured without authentication, "
                    "such as a legacy local WSL bridge. Docker deployments still require their generated token.")
        self.authentication_note.setText(note)

    def discovery_settings(self):
        """Chooses the generating task's endpoint, falling back to saved generator settings.

        Returns:
            dict: Detached settings with resolved deployment references.
        """
        task = self.task
        if task.task_type != "kimodo_generate":
            tasks = list(getattr(self.project, "tasks", []))
            index = next((index for index, item in enumerate(tasks) if item.id == task.id), -1)
            task = next((item for item in tasks[index + 1:]
                         if item.task_type == "kimodo_generate" and item.enabled), None)
        settings = copy.deepcopy(task.settings) if task else connections.generator_settings()
        return connections.resolve_settings(settings, self.project, task)

    def query_bridge(self, choose_models=False):
        """Starts one asynchronous read-only metadata query.

        Args:
            choose_models (bool): Whether to offer a model selection menu on success.
        """
        if getattr(self, "_query_pending", False):
            return
        try:
            settings = self.discovery_settings()
            connection = connections.make_connection(settings)
        except Exception as error:
            self.status.setText(str(error))
            return
        self._query_pending = True
        self._choose_models = choose_models
        self.status.setText(f"Querying available models at {connection.url}...")
        self._query_worker = BridgeQuery(connection, settings)
        self._query_worker.signals.finished.connect(self.receive_bridge_query)
        button = getattr(self, "get_models_button", getattr(self, "test_connection_button", None))
        if button:
            button.setEnabled(False)
        qt.QtCore.QThreadPool.globalInstance().start(self._query_worker)

    def receive_bridge_query(self, result, error):
        """Displays metadata and an optional model menu on the main thread.

        Args:
            result (dict or None): Bridge health and current models.
            error (str or None): Query failure.
        """
        self._query_pending = False
        self.update_enabled_state()
        button = getattr(self, "get_models_button", getattr(self, "test_connection_button", None))
        if button and not self._choose_models:
            button.setEnabled(True)
        if error:
            self.status.setText(f"Could not query bridge: {error}. Connect / Start it in Kimodo Generator first.")
            return
        models = result.get("models", [])
        self.status.setText("Available models: " + (", ".join(model["id"] for model in models) or "none"))
        if not self._choose_models or not models:
            return
        self.models_menu = qt.QtWidgets.QMenu(self)
        for model in models:
            label = model["id"]
            if model.get("fps"):
                label += f" ({model['fps']} fps)"
            action = self.models_menu.addAction(label)
            action.triggered.connect(partial(self.select_discovered_model, model))
        self.models_menu.popup(button.mapToGlobal(qt.QtCore.QPoint(0, button.height())))

    def select_discovered_model(self, model, unused_checked=False):
        """Stores a selected model and its advertised sample rate.

        Args:
            model (dict): Current server model metadata.
            unused_checked (bool): Qt action check state.
        """
        if self.task.settings.get("template_path", "").strip():
            self.status.setText("The setup / definition file controls the model. Clear it to edit the local model.")
            return
        self.controls[("definition", "model")].setText(model["id"])
        if model.get("fps"):
            self.controls[("model_fps",)].setValue(float(model["fps"]))

    def get_models(self):
        """Queries the downstream generating bridge and offers current models."""
        self.query_bridge(choose_models=True)

    def test_connection(self):
        """Queries the configured bridge without starting containers or submitting jobs."""
        self.query_bridge()
