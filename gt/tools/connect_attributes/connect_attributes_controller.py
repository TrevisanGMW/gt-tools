"""Controller for the Connect Attributes MVC tool."""

import logging


logger = logging.getLogger(__name__)


class ConnectAttributesController:
    """Coordinates the view, persistent model, and Maya scene service."""

    def __init__(self, model, view, service):
        """Initializes controller bindings.

        Args:
            model (ConnectAttributesModel): Persistent and transient tool state.
            view (ConnectAttributesView): Qt interface.
            service (ConnectAttributesService): Maya scene operations.
        """
        self.model = model
        self.view = view
        self.service = service
        self._syncing_view = False
        self._sync_view()
        self._connect_view()
        self.view.show()

    def _connect_view(self):
        """Connects all view signals to controller actions."""
        self.view.connect_radio.toggled.connect(self._operation_changed)
        self.view.use_selection_checkbox.toggled.connect(
            lambda value: self._store_setting("use_selection", value)
        )
        self.view.reverse_checkbox.toggled.connect(
            lambda value: self._store_setting("add_reverse_node", value)
        )
        self.view.force_checkbox.toggled.connect(
            lambda value: self._store_setting("force_connection", value)
        )
        self.view.utility_checkbox.toggled.connect(
            lambda value: self._store_setting("use_utility_node", value)
        )
        self.view.shared_input_checkbox.toggled.connect(
            lambda value: self._store_setting("use_shared_input", value)
        )
        self.view.utility_combo.currentTextChanged.connect(
            lambda value: self._store_setting("utility_node_type", value)
        )
        self.view.shared_input_combo.currentTextChanged.connect(
            lambda value: self._store_setting("shared_input_node_type", value)
        )
        self.view.source_attribute_field.editingFinished.connect(self._store_attribute_fields)
        self.view.target_attributes_field.editingFinished.connect(self._store_attribute_fields)
        self.view.source_attribute_field.returnPressed.connect(self.run)
        self.view.target_attributes_field.returnPressed.connect(self.run)
        self.view.load_source_button.clicked.connect(self.load_source)
        self.view.load_targets_button.clicked.connect(self.load_targets)
        self.view.source_status_label.clicked.connect(self.select_loaded_source)
        self.view.target_status_label.clicked.connect(self.select_loaded_targets)
        self.view.list_all_button.clicked.connect(lambda: self.browse_attributes(keyable=False))
        self.view.list_keyable_button.clicked.connect(lambda: self.browse_attributes(keyable=True))
        self.view.preview_button.clicked.connect(self.preview)
        self.view.run_button.clicked.connect(self.run)
        self.view.reset_action.triggered.connect(self.reset_settings)
        self.view.help_action.triggered.connect(self.view.show_help)

    def _sync_view(self):
        """Copies model settings and transient node state to the view."""
        self._syncing_view = True
        try:
            settings = self.model.settings
            is_connect = settings.get("operation") == "connect"
            self.view.connect_radio.setChecked(is_connect)
            self.view.disconnect_radio.setChecked(not is_connect)
            self.view.use_selection_checkbox.setChecked(settings.get("use_selection"))
            self.view.source_attribute_field.setText(settings.get("source_attribute"))
            self.view.target_attributes_field.setText(settings.get("target_attributes"))
            self.view.reverse_checkbox.setChecked(settings.get("add_reverse_node"))
            self.view.force_checkbox.setChecked(settings.get("force_connection"))
            self.view.utility_checkbox.setChecked(settings.get("use_utility_node"))
            self.view.utility_combo.setCurrentText(settings.get("utility_node_type"))
            self.view.shared_input_checkbox.setChecked(settings.get("use_shared_input"))
            self.view.shared_input_combo.setCurrentText(settings.get("shared_input_node_type"))
            self.view.set_loaded_nodes(self.model.source_object, self.model.target_objects)
            self._refresh_enabled_state()
        finally:
            self._syncing_view = False

    def _store_setting(self, key, value):
        """Stores one setting and refreshes dependent controls.

        Args:
            key (str): Model setting key.
            value (object): New setting value.
        """
        if self._syncing_view:
            return
        self.model.set_setting(key, value)
        self._refresh_enabled_state()

    def _store_attribute_fields(self):
        """Stores source and target attribute text together."""
        if self._syncing_view:
            return
        self.model.set_setting(
            "source_attribute", self.view.source_attribute_field.text(), save=False
        )
        self.model.set_setting(
            "target_attributes", self.view.target_attributes_field.text(), save=False
        )
        self.model.save_preferences()

    def _operation_changed(self, is_connect):
        """Stores the active operation radio state.

        Args:
            is_connect (bool): True when Connect is active.
        """
        if self._syncing_view:
            return
        self.model.set_setting("operation", "connect" if is_connect else "disconnect")
        self._refresh_enabled_state()

    def _refresh_enabled_state(self):
        """Updates controls affected by the current operation and options."""
        settings = self.model.settings
        is_connect = self.view.connect_radio.isChecked()
        self.view.update_enabled_state(
            use_selection=settings.get("use_selection"),
            is_connect=is_connect,
            use_utility=settings.get("use_utility_node"),
            use_shared_input=settings.get("use_shared_input"),
        )

    def load_source(self):
        """Loads exactly one selected node as the transient source."""
        selection = self.service.get_selection()
        if len(selection) != 1:
            self._report("Select exactly one object to load as the source.", level="warning")
            return
        self.model.set_source_object(selection[0])
        self.view.set_loaded_nodes(self.model.source_object, self.model.target_objects)
        self._report(f"Loaded source: {selection[0]}", level="success")

    def load_targets(self):
        """Loads all selected nodes as transient targets."""
        selection = self.service.get_selection()
        if not selection:
            self._report("Select at least one object to load as a target.", level="warning")
            return
        self.model.set_target_objects(selection)
        self.view.set_loaded_nodes(self.model.source_object, self.model.target_objects)
        self._report(f"Loaded {len(self.model.target_objects)} target(s).", level="success")

    def select_loaded_source(self, *args):
        """Selects the loaded source when it still exists.

        Args:
            *args: Ignored Qt signal arguments.
        """
        if self.model.source_object:
            self.service.select_nodes([self.model.source_object])

    def select_loaded_targets(self, *args):
        """Selects all loaded targets that still exist.

        Args:
            *args: Ignored Qt signal arguments.
        """
        self.service.select_nodes(self.model.target_objects)

    def _get_request(self):
        """Gets the latest normalized request and validation messages.

        Returns:
            tuple: Request dictionary and validation messages.
        """
        self._store_attribute_fields()
        selection = self.service.get_selection() if self.model.settings.get("use_selection") else None
        return self.model.build_request(selection=selection)

    def preview(self):
        """Validates and summarizes the pending operation without changing the scene."""
        request, issues = self._get_request()
        if issues:
            self._report(" ".join(issues), level="warning")
            return
        preview_lines = self.model.build_preview_lines(request)
        connection_count = len(preview_lines)
        operation = "connection" if request.get("operation") == "connect" else "disconnection"
        shared_input_type = None
        if (
            request.get("operation") == "connect"
            and request.get("use_utility_node")
            and request.get("use_shared_input")
        ):
            shared_input_type = request.get("shared_input_node_type")
        self.view.show_connection_preview(
            preview_lines=preview_lines,
            operation=request.get("operation"),
            shared_input_type=shared_input_type,
        )
        self._report(
            f"Ready for {connection_count} {operation}(s) across "
            f"{len(request.get('target_objects'))} target(s).",
            level="success",
        )

    def run(self):
        """Validates and executes the current operation request."""
        request, issues = self._get_request()
        if issues:
            self._report(" ".join(issues), level="warning")
            return
        result = self.service.execute(request)
        if result.get("errors"):
            logger.warning("Connect Attributes completed with errors:\n%s", "\n".join(result.get("errors")))
            message = (
                f"Completed {result.get('succeeded')} item(s); "
                f"{len(result.get('errors'))} failed. See the Script Editor for details."
            )
            self._report(message, level="warning")
            return
        skipped = result.get("skipped")
        suffix = f"; {skipped} already disconnected" if skipped else ""
        self._report(f"Completed {result.get('succeeded')} item(s){suffix}.", level="success")

    def browse_attributes(self, keyable=False):
        """Shows an attribute browser for the source or first selected node.

        Args:
            keyable (bool, optional): Whether to list only keyable attributes.
        """
        selection = self.service.get_selection()
        node = selection[0] if selection else self.model.source_object
        if not node:
            self._report("Select an object or load a source before browsing attributes.", level="warning")
            return
        attributes = self.service.list_attributes(node, keyable=keyable)
        if not attributes:
            self._report(f'No attributes found on "{node}".', level="warning")
            return
        self.view.show_attribute_browser(node, attributes, keyable=keyable)
        self._report(f"Showing {len(attributes)} attribute(s) from {node}.")

    def reset_settings(self, *args):
        """Restores default preferences without changing loaded scene nodes.

        Args:
            *args: Ignored Qt signal arguments.
        """
        self.model.reset_preferences()
        self._sync_view()
        self._report("Settings restored to defaults.", level="success")

    def _report(self, message, level="info"):
        """Reports feedback in the view and Maya warning stream when appropriate.

        Args:
            message (str): User-facing message.
            level (str, optional): Status severity.
        """
        self.view.set_status(message, level=level)
        if level in ("warning", "error"):
            try:
                self.service._get_cmds().warning(message)
            except Exception:
                logger.warning(message)
