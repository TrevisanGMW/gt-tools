"""VLM preferences, local model discovery controls, and credential status."""

import os

from gt.utils import vault

from gt.tools.annotation_tracker import auto_annotation_model as model
from gt.ui.qt_import import QtCore, QtGui, QtWidgets


class ModelCombo(QtWidgets.QComboBox):
    """Model picker that asks for a model list when opened while empty."""

    popup_requested_empty = QtCore.Signal()

    def showPopup(self):
        """Requests a model list instead of showing an empty drop-down."""
        if self.count() == 0:
            self.popup_requested_empty.emit()
            return
        super().showPopup()


class VlmSettingsTab(QtWidgets.QWidget):
    """Edits VLM settings without handling scene access or credentials."""

    def __init__(self, settings, parent=None):
        """Builds the VLM tab.

        Args:
            settings (dict): Current Auto Annotate preferences.
            parent (QWidget, optional): Containing setup window.
        """
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.mode = QtWidgets.QComboBox()
        for label, value in (("Off", "off"), ("Review suggestions", "review"), ("Auto-accept", "auto")):
            self.mode.addItem(label, value)
        self.mode.setToolTip(
            "Off uses measured motion and any enabled calibration only.\n"
            "Review lets you choose suggestions in interactive Maya.\n"
            "Auto-accept applies eligible suggestions above the threshold and works in Batch Processor."
        )

        self.provider = QtWidgets.QComboBox()
        for label, value in (
            ("Local / Bionic (LM Studio)", "local"), ("OpenAI", "openai"), ("Anthropic / Claude", "anthropic"),
        ):
            self.provider.addItem(label, value)
        self.provider.setToolTip(
            "Choose the service that receives the sampled images.\nBionic can run entirely locally."
        )
        self.endpoint = QtWidgets.QLineEdit()
        self.endpoint.setToolTip(
            "Leave blank to use the provider's default URL.\n"
            "For Bionic, paste the base URL shown in the app or use Detect Server."
        )
        self.model_name = ModelCombo()
        self.model_name.setEditable(True)
        self.model_name.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.model_name.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.model_name.setMinimumContentsLength(24)
        self.model_name.setToolTip(
            "Use an exact model ID from your provider.\n"
            "For Bionic, Get Models lists installed vision models and loaded aliases.\n"
            "Opening the empty drop-down also fetches the list."
        )
        self.refresh_models = QtWidgets.QPushButton("Get Models")
        self.refresh_models.setToolTip(
            "Reads the connected Bionic server's installed vision models into the Model drop-down."
        )
        self.refresh_models.setMinimumWidth(self.refresh_models.fontMetrics().horizontalAdvance("Get Models") + 44)
        model_row = QtWidgets.QWidget()
        model_layout = QtWidgets.QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addWidget(self.model_name, 1)
        model_layout.addWidget(self.refresh_models)
        self.model_name.popup_requested_empty.connect(self._request_models)

        self.key_env = QtWidgets.QLineEdit()
        self.key_env.setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("[A-Za-z_][A-Za-z0-9_]*"), self.key_env
        ))
        self.key_env.setToolTip(
            "Enter the environment variable name, such as OPENAI_API_KEY, or leave blank for the provider default.\n"
            "Maya reads the key from its environment.\nOnly the variable name is saved in preferences."
        )
        self.api_key = QtWidgets.QLineEdit()
        self.api_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Paste an API key, then click Save Key")
        self.api_key.setToolTip(
            "The key is encrypted for your Windows user account and stored on this computer.\n"
            "It is never written to preferences or exported settings. An environment variable still takes priority."
        )
        self.save_key = QtWidgets.QPushButton("Save Key")
        self.clear_key = QtWidgets.QPushButton("Clear Key")
        for button in (self.save_key, self.clear_key):
            button.setMinimumWidth(button.fontMetrics().horizontalAdvance(button.text()) + 44)
        key_row = QtWidgets.QWidget()
        key_layout = QtWidgets.QHBoxLayout(key_row)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.addWidget(self.api_key, 1)
        key_layout.addWidget(self.save_key)
        key_layout.addWidget(self.clear_key)
        self.key_row = key_row
        self.key_label = QtWidgets.QLabel("API key")
        self.key_status = QtWidgets.QLabel()
        self.key_status.setMinimumWidth(110)
        self.key_status.setToolTip(
            "Shows whether this Maya process can read the configured variable.\n"
            "Provider authentication is checked when a request runs."
        )
        credential_row = QtWidgets.QWidget()
        credential_layout = QtWidgets.QHBoxLayout(credential_row)
        credential_layout.setContentsMargins(0, 0, 0, 0)
        credential_layout.addWidget(self.key_env, 1)
        credential_layout.addWidget(self.key_status)

        self.threshold = QtWidgets.QDoubleSpinBox()
        self.threshold.setRange(0, 1)
        self.threshold.setMinimumWidth(110)
        self.threshold.setSingleStep(0.05)
        self.fill_tip = (
            "Confidence the model must report (0 to 1) before Auto-accept fills an empty range field,\n"
            "such as stance or interaction type. Suggestions below it are deferred and listed in the log.\n"
            "Schema and measured-motion checks still apply, and locked ranges are never changed.\n"
            "Replacing a value that already exists uses the separate, higher replace threshold."
        )
        self.threshold.setToolTip(self.fill_tip)
        self.view_checks = {}
        views_row = QtWidgets.QWidget()
        views_layout = QtWidgets.QHBoxLayout(views_row)
        views_layout.setContentsMargins(0, 0, 0, 0)
        for key, text, tip in (
            ("vlm_view_side", "Side", "Side-view poses over time. Always the most useful row."),
            ("vlm_view_front", "Front", "Front-view poses. Helps with lateral steps, reaching and leaning."),
            ("vlm_view_travel", "Travel", "Poses at their real positions with fading history. Shown only when the character travels."),
            ("vlm_view_top", "Top", "Path from above with facing arrows. Shows turns and direction changes."),
        ):
            checkbox = QtWidgets.QCheckBox(text)
            checkbox.setToolTip(tip)
            self.view_checks[key] = checkbox
            views_layout.addWidget(checkbox)
        views_layout.addStretch()
        self.field_checks = {}
        fields_row = QtWidgets.QWidget()
        fields_layout = QtWidgets.QGridLayout(fields_row)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        for position, (field, text) in enumerate((
            ("style", "File style"), ("context", "File context"), ("stance", "Stance"),
            ("override_style", "Override style"), ("interaction_type", "Interaction type"),
            ("interaction_scope", "Interaction scope"), ("interaction_item", "Interaction item"),
        )):
            checkbox = QtWidgets.QCheckBox(text)
            checkbox.setToolTip(f"Allow the model to suggest '{field}'. Fields missing from the schema are ignored.")
            self.field_checks[field] = checkbox
            fields_layout.addWidget(checkbox, position // 3, position % 3)
        self.style_threshold = QtWidgets.QDoubleSpinBox()
        self.style_threshold.setRange(0, 1)
        self.style_threshold.setSingleStep(0.05)
        self.style_threshold.setMinimumWidth(110)
        self.file_tip = (
            "Confidence needed to fill the empty file-level context sentence, and the file Style when\n"
            "'Always pick a file style' is off. It is usually lower than the fill threshold, because these are one\n"
            "value per file and easy to correct. 0 accepts any suggestion.\n"
            "With 'Always pick a file style' on, the style ignores this threshold and any valid answer is used."
        )
        self.style_threshold.setToolTip(self.file_tip)
        self.style_forced = QtWidgets.QCheckBox("Always pick a file style")
        self.style_forced.setToolTip(
            "The model must choose one of the allowed styles. Local servers are forced to answer with one of them,\n"
            "and any valid answer is accepted whatever its confidence."
        )
        self.style_recheck = QtWidgets.QCheckBox("Re-check an uncertain style with more images")
        self.style_recheck.setToolTip(
            "When the style answer is missing or below the fill threshold, asks again with up to 6 pose sheets and\n"
            "the range timeline. The more confident answer is used."
        )
        self.replace_existing = QtWidgets.QCheckBox("Replace existing values")
        self.replace_existing.setToolTip(
            "On: Auto-accept also changes fields that already have a value, when confidence is high enough.\n"
            "Off: Auto-accept only fills empty fields. Locked ranges are never changed."
        )
        self.replace_threshold = QtWidgets.QDoubleSpinBox()
        self.replace_threshold.setRange(0, 1)
        self.replace_threshold.setSingleStep(0.05)
        self.replace_threshold.setMinimumWidth(110)
        self.replace_threshold.setToolTip(
            "Confidence needed to replace an existing value. Use more than the normal threshold, because\n"
            "overwriting is riskier than filling a blank."
        )
        self.replace_existing.toggled.connect(self.replace_threshold.setEnabled)
        self.guidance = QtWidgets.QPlainTextEdit()
        self.guidance.setMaximumHeight(96)
        self.guidance.setPlaceholderText("Rules for this dataset, for example when an interaction really counts.")
        self.guidance.setToolTip(
            "Added to every request. Use it to define how fields should be used in your dataset.\n"
            "The schema's field descriptions are also sent to the model."
        )
        self.max_tokens = QtWidgets.QSpinBox()
        self.max_tokens.setRange(0, 65536)
        self.max_tokens.setSingleStep(1024)
        self.max_tokens.setSpecialValueText("No limit")
        self.max_tokens.setMinimumWidth(110)
        self.max_tokens.setToolTip(
            "Token budget for each reply. Reasoning models also spend it on thinking, so raise it (for example\n"
            "32768) if you see 'ran out of tokens'. A request that hits the limit is retried once with double.\n"
            "No limit lets local and OpenAI servers decide, so a looping model can run until the timeout.\n"
            "Anthropic always needs a limit and uses 8192 here."
        )
        self.log_changes = QtWidgets.QCheckBox("Print every VLM suggestion in the log")
        self.log_changes.setToolTip(
            "Debug log: prints each suggestion with its before and after value, confidence, and whether it was\n"
            "applied, deferred, or ignored. Also lists ignored 'none' values."
        )
        self.image_width = QtWidgets.QSpinBox()
        self.image_width.setRange(512, 2048)
        self.image_width.setSingleStep(128)
        self.image_width.setSuffix(" px")
        self.image_width.setMinimumWidth(110)
        self.image_width.setToolTip(
            "Widest pose sheet sent to the model. Smaller images answer faster, but small text gets harder to read.\n"
            "Try 768 for heavy local models."
        )
        self.poses = QtWidgets.QSpinBox()
        self.poses.setRange(3, 12)
        self.poses.setMinimumWidth(110)
        self.poses.setToolTip(
            "Poses drawn in each image row. Poses are picked where the motion changes most.\n"
            "Small local models usually do better with 4 to 6 poses."
        )
        self.preview_request = QtWidgets.QPushButton("Preview Request")
        self.preview_request.setToolTip(
            "Builds the images and prompt exactly as a run would and saves them for review. Nothing is sent."
        )
        self.last_reply = QtWidgets.QPushButton("Last Reply")
        self.last_reply.setToolTip("Shows the most recent model reply or error, when one is stored.")
        self.purge_debug = QtWidgets.QPushButton("Purge Debug Files")
        self.purge_debug.setToolTip("Deletes saved previews, leftover images and the stored last reply.")
        self.open_debug = QtWidgets.QPushButton("Open Folder")
        self.open_debug.setToolTip("Opens the preview folder, creating it if needed.")
        for button in (self.preview_request, self.last_reply, self.purge_debug, self.open_debug):
            button.setMinimumWidth(button.fontMetrics().horizontalAdvance(button.text()) + 44)
        self.context_images = QtWidgets.QCheckBox("Use pose sheets for the file context")
        self.context_images.setToolTip(
            "Adds up to 3 evenly spaced pose sheets to the file context request, together with the range timeline.\n"
            "More precise for what the character does, but slower than a text-only request."
        )
        self.max_images = QtWidgets.QSpinBox()
        self.max_images.setRange(1, 200)
        self.max_images.setMinimumWidth(110)
        self.max_images.setToolTip(
            "Maximum pose-sheet images for the whole scene. Each range is sent as its own small request,\n"
            "so a long scene needs more images and takes longer, but no single request grows.\n"
            "Each range gets one image; long ranges use several."
        )
        self.timeout = QtWidgets.QSpinBox()
        self.timeout.setRange(1, 300)
        self.timeout.setMinimumWidth(110)
        self.timeout.setSuffix(" s")
        self.timeout.setToolTip(
            "Time allowed for a model request or Bionic command.\n"
            "A timeout leaves the measured annotations available."
        )
        self.allow_remote = QtWidgets.QCheckBox("Allow sending sampled images to a remote endpoint")
        self.allow_remote.setToolTip(
            "Enable this only for an endpoint you intend to send frames to.\n"
            "Required for cloud providers and non-loopback addresses."
        )
        def make_group(title):
            """Adds a titled box with a form to the tab.

            Args:
                title (str): Box title.

            Returns:
                QFormLayout: Layout for the box rows.
            """
            box = QtWidgets.QGroupBox(title)
            box_form = QtWidgets.QFormLayout(box)
            box_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            box.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
            layout.addWidget(box)
            return box_form

        service = make_group("Service")
        for label, control in (
            ("Mode", self.mode), ("Provider", self.provider), ("Endpoint", self.endpoint),
            ("Model", model_row), ("Credential variable", credential_row), (self.key_label, key_row),
        ):
            service.addRow(label, control)
        service.addRow(self.allow_remote)
        layout.addWidget(self._build_local_controls())
        accept = make_group("Auto-accept")
        for text, tip, control in (
            ("Fill threshold", self.fill_tip, self.threshold), ("File threshold", self.file_tip, self.style_threshold),
        ):
            label = QtWidgets.QLabel(text)
            label.setToolTip(tip)
            accept.addRow(label, control)
        accept.addRow(self.style_forced)
        accept.addRow(self.style_recheck)
        accept.addRow(self.replace_existing, self.replace_threshold)
        make_group("Fields the model may guess").addRow(fields_row)
        make_group("Model rules").addRow(self.guidance)
        images = make_group("Images sent to the model")
        images.addRow("Pose sheet views", views_row)
        images.addRow("Maximum images (scene)", self.max_images)
        images.addRow("Poses per image", self.poses)
        images.addRow("Image width", self.image_width)
        images.addRow(self.context_images)
        requests = make_group("Requests")
        requests.addRow("Request timeout", self.timeout)
        requests.addRow("Max reply tokens", self.max_tokens)
        debug = make_group("Debugging")
        debug.addRow(self.log_changes)
        debug_row = QtWidgets.QHBoxLayout()
        for button in (self.preview_request, self.last_reply, self.purge_debug, self.open_debug):
            debug_row.addWidget(button)
        debug_row.addStretch()
        debug.addRow(debug_row)
        layout.addStretch()

        self.mode.currentIndexChanged.connect(self._update_controls)
        self.provider.currentIndexChanged.connect(self._provider_changed)
        self.key_env.textChanged.connect(self._update_credential_status)
        self.apply_settings(settings)

    def _request_models(self):
        """Fetches Bionic models when the empty drop-down is opened."""
        if self.provider.currentData() == "local":
            self.refresh_models.click()

    def _build_local_controls(self):
        """Builds Bionic-only discovery and model memory controls.

        Returns:
            QGroupBox: Bionic controls.
        """
        self.local_group = QtWidgets.QGroupBox("Bionic")
        layout = QtWidgets.QVBoxLayout(self.local_group)
        actions = QtWidgets.QHBoxLayout()
        self.detect_server = QtWidgets.QPushButton("Detect Server")
        self.detect_server.setToolTip(
            "Finds Bionic's running local server and fills the Endpoint field.\n"
            "Use the auto-start option to let Auto Annotate start the server later."
        )
        actions.addWidget(self.detect_server)
        actions.addStretch()
        layout.addLayout(actions)
        self.auto_load = QtWidgets.QCheckBox("Start Bionic and load the selected model as needed")
        self.auto_load.setToolTip(
            "When annotation runs, the lms CLI can start a loopback server and load the selected installed model.\n"
            "Models must already be downloaded in Bionic."
        )
        self.eject_others = QtWidgets.QCheckBox("Unload other idle Bionic models before running")
        self.eject_others.setToolTip(
            "Frees memory by unloading other local language models that Bionic reports as idle.\n"
            "The selected model, active models, and embedding models are kept.\n"
            "This affects the shared local server and applies to interactive and batch runs."
        )
        layout.addWidget(self.auto_load)
        layout.addWidget(self.eject_others)
        return self.local_group

    def set_model_choices(self, choices):
        """Refreshes the picker without discarding a typed model ID.

        Args:
            choices (list): Model ID, display name, and loaded status tuples.
        """
        selected = self.model_name.currentText().strip()
        self.model_name.clear()
        for identifier, name, loaded in choices:
            row = self.model_name.count()
            self.model_name.addItem(identifier)
            status = "Loaded in Bionic" if loaded else "Installed in Bionic"
            self.model_name.setItemData(row, f"{name}\n{status}", QtCore.Qt.ItemDataRole.ToolTipRole)
        self.model_name.setCurrentIndex(self.model_name.findText(selected))
        self.model_name.setEditText(selected)

    def _provider_changed(self, *args):
        """Resets local choices and refreshes provider-specific controls."""
        self.set_model_choices([])
        self._update_controls()

    def _update_controls(self, *args):
        """Updates provider defaults and the controls used by the selected mode."""
        provider = self.provider.currentData()
        endpoint, name, key = model.VLM_PROVIDERS[provider]
        self.endpoint.setPlaceholderText(endpoint)
        self.model_name.lineEdit().setPlaceholderText(name or "Enter an image-capable model ID")
        self.key_env.setPlaceholderText(key or "Optional")
        self.local_group.setVisible(provider == "local")
        self.refresh_models.setVisible(provider == "local")
        self.threshold.setEnabled(self.mode.currentData() == "auto")
        self.style_threshold.setEnabled(self.mode.currentData() == "auto")
        self._update_credential_status()

    def _update_credential_status(self, *args):
        """Updates credential presence without displaying or storing the key."""
        default = model.VLM_PROVIDERS[self.provider.currentData()][2]
        name = self.key_env.text().strip() or default
        provider = self.provider.currentData()
        in_environment = bool(name and os.environ.get(name))
        saved = vault.has_secret(f"vlm_{provider}") if provider != "local" else False
        available = in_environment or saved
        text = "Environment" if in_environment else "Saved key" if saved else "Missing" if name else "Optional"
        self.key_status.setText(text)
        self.key_status.setStyleSheet("color: #DBB783;" if name and not available else "")
        self.key_row.setVisible(provider != "local")
        self.key_label.setVisible(provider != "local")
        self.clear_key.setEnabled(saved)
        self.save_key.setEnabled(vault.is_supported())

    def read_settings(self):
        """Gets current VLM preferences.

        Returns:
            dict: Provider, model, credential reference and runtime options.
        """
        return {
            "vlm_mode": self.mode.currentData(),
            "vlm_provider": self.provider.currentData(),
            "vlm_endpoint": self.endpoint.text().strip(),
            "vlm_model": self.model_name.currentText().strip(),
            "vlm_key_env": self.key_env.text().strip(),
            "vlm_threshold": self.threshold.value(),
            "vlm_max_images": self.max_images.value(),
            "vlm_timeout": self.timeout.value(),
            "vlm_local_auto_load": self.auto_load.isChecked(),
            "vlm_local_eject_other_models": self.eject_others.isChecked(),
            "allow_remote_vlm": self.allow_remote.isChecked(),
            "vlm_poses_per_image": self.poses.value(),
            "vlm_image_width": self.image_width.value(),
            "vlm_max_tokens": self.max_tokens.value(),
            "vlm_style_threshold": self.style_threshold.value(),
            "vlm_style_forced": self.style_forced.isChecked(),
            "vlm_style_recheck": self.style_recheck.isChecked(),
            "vlm_context_images": self.context_images.isChecked(),
            "vlm_replace_existing": self.replace_existing.isChecked(),
            "vlm_replace_threshold": self.replace_threshold.value(),
            "vlm_guidance": self.guidance.toPlainText().strip()[:2000],
            "vlm_log_changes": self.log_changes.isChecked(),
            "vlm_fields": [field for field, checkbox in self.field_checks.items() if checkbox.isChecked()],
            **{key: checkbox.isChecked() for key, checkbox in self.view_checks.items()},
        }

    def apply_settings(self, settings):
        """Updates VLM controls from stored values or defaults.

        Args:
            settings (dict): Auto Annotate preferences.
        """
        self.mode.setCurrentIndex(max(0, self.mode.findData(settings["vlm_mode"])))
        self.provider.setCurrentIndex(max(0, self.provider.findData(settings["vlm_provider"])))
        self.set_model_choices([])
        endpoint = settings["vlm_endpoint"]
        try:
            model.validate_vlm_credentials("", endpoint)
        except ValueError:
            endpoint = ""
        self.endpoint.setText(endpoint)
        self.model_name.setEditText(settings["vlm_model"])
        key_name = settings["vlm_key_env"]
        try:
            model.validate_vlm_credentials(key_name)
        except ValueError:
            key_name = ""
        self.key_env.setText(key_name)
        self.threshold.setValue(settings["vlm_threshold"])
        self.max_images.setValue(settings["vlm_max_images"])
        self.timeout.setValue(settings["vlm_timeout"])
        self.auto_load.setChecked(settings["vlm_local_auto_load"])
        self.eject_others.setChecked(settings["vlm_local_eject_other_models"])
        self.allow_remote.setChecked(settings["allow_remote_vlm"])
        self.poses.setValue(settings["vlm_poses_per_image"])
        self.image_width.setValue(settings["vlm_image_width"])
        self.max_tokens.setValue(settings["vlm_max_tokens"])
        self.style_threshold.setValue(settings["vlm_style_threshold"])
        self.style_forced.setChecked(settings["vlm_style_forced"])
        self.style_recheck.setChecked(settings["vlm_style_recheck"])
        self.context_images.setChecked(settings["vlm_context_images"])
        self.replace_existing.setChecked(settings["vlm_replace_existing"])
        self.replace_threshold.setValue(settings["vlm_replace_threshold"])
        self.replace_threshold.setEnabled(settings["vlm_replace_existing"])
        self.guidance.setPlainText(settings["vlm_guidance"])
        self.log_changes.setChecked(settings["vlm_log_changes"])
        for field, checkbox in self.field_checks.items():
            checkbox.setChecked(field in settings["vlm_fields"])
        for key, checkbox in self.view_checks.items():
            checkbox.setChecked(settings[key])
        self._update_controls()
