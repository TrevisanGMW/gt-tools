"""Compact Qt interface for connections, motion prompts, poses, and results."""

from gt.ui import qt_import as ui_qt
from gt.ui import qt_utils
from gt.ui import resource_library as resources
from gt.tools.kimodo_generator.kimodo_generator_help import ACTION_TOOLTIPS, CONTROL_TOOLTIPS, TAB_TOOLTIPS
import html

QtWidgets = ui_qt.QtWidgets
QtCore = ui_qt.QtCore
PRIMARY_BUTTON_STYLE = (
    "QPushButton { background-color: #b0b0b0; color: #202020; font-weight: bold; }"
    "QPushButton:hover { background-color: #c4c4c4; }"
    "QPushButton:pressed { background-color: #888888; }"
    "QPushButton:disabled { background-color: #686868; color: #a0a0a0; }"
)


class KimodoGeneratorView(metaclass=qt_utils.MayaWindowMeta):
    """Constructs widgets without requiring a connection, model, or Maya scene."""

    def __init__(self, parent=None, version=None):
        """Builds a resizable tool window.

        Args:
            parent (QWidget, optional): Application parent.
            version (str, optional): Display version.
        """
        super().__init__(parent=parent)
        self.controller = None
        self.buttons = {}
        self.responsive_rows = []
        self.tables = []
        self.table_registry = {}
        self._observed_screen = None
        self._screen_handle = None
        self._sized_once = False
        self._updating_metrics = False
        self.setWindowTitle(f"Kimodo Generator — {version or '1.0'}")
        self.setWindowIcon(ui_qt.QtGui.QIcon(resources.Icon.tool_kimodo_generator))
        self.setMinimumSize(460, 380)
        self.setStyleSheet(resources.Stylesheet.maya_dialog_base + """
            QGroupBox { margin-top: 12px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; }
            QPushButton { padding: 5px 10px; }
            QTableWidget { gridline-color: #454545; color: #e0e0e0; selection-color: white; }
            QTableWidget::item { padding: 2px 6px; }
            QHeaderView::section { background-color: #383b3e; color: #dedede; padding: 4px; }
            QCheckBox { color: #dedede; }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        heading = QtWidgets.QLabel("Kimodo Generator")
        self.heading_label = heading
        heading_font = ui_qt.QtGui.QFont(self.font())
        heading_font.setPointSizeF(max(9, heading_font.pointSizeF()) * 1.3)
        heading_font.setBold(True)
        heading.setFont(heading_font)
        title = self.row(heading, self.button("load_setup", "Load Setup"),
                         self.button("save_setup", "Save Setup"))
        title.setStretch(0, 1)
        layout.addLayout(title)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.currentChanged.connect(self.schedule_metrics_refresh)
        layout.addWidget(self.tabs)
        self.build_connection()
        self.build_generation()
        self.build_constraints()
        self.build_humanik()
        self.build_summary()
        self.build_results()
        self.status = QtWidgets.QLabel("Connect to a Kimodo bridge to begin.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.apply_tooltips()
        self.refresh_layout_metrics()
        qt_utils.center_window(self)

    def button(self, key, text, tooltip=None):
        """Creates and registers an action button.

        Args:
            key (str): Controller action key.
            text (str): Button label.
            tooltip (str, optional): Additional guidance.

        Returns:
            QPushButton: New button.
        """
        button = QtWidgets.QPushButton(text)
        button.setToolTip(tooltip or text)
        self.buttons[key] = button
        return button

    @staticmethod
    def make_primary(button):
        """Styles a primary action like the bright-grey actions in other GT tools.

        Args:
            button (QPushButton): Button to emphasize.

        Returns:
            QPushButton: Same styled button for inline use.
        """
        button.setStyleSheet(PRIMARY_BUTTON_STYLE)
        return button

    def page(self, title):
        """Adds a scrollable tab to accommodate scaled displays.

        Args:
            title (str): Tab title.

        Returns:
            QVBoxLayout: Content layout.
        """
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setSpacing(10)
        scroll.setWidget(content)
        self.tabs.addTab(scroll, title)
        return layout

    def page_with_footer(self, title):
        """Adds a scrollable tab with a fixed action area at its bottom.

        Args:
            title (str): Tab title.

        Returns:
            tuple: Scroll-content layout and fixed footer layout.
        """
        page = QtWidgets.QWidget()
        page_layout = QtWidgets.QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(8)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setSpacing(10)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)
        footer_layout = QtWidgets.QVBoxLayout()
        page_layout.addLayout(footer_layout)
        self.tabs.addTab(page, title)
        return content_layout, footer_layout

    def row(self, *widgets):
        """Builds a horizontal widget row.

        Args:
            *widgets: Widgets to place in order.

        Returns:
            QHBoxLayout: Row layout.
        """
        layout = QtWidgets.QHBoxLayout()
        for widget in widgets:
            layout.addWidget(widget)
        self.responsive_rows.append(layout)
        return layout

    def form(self):
        """Creates a form whose labels wrap above fields on narrow displays.

        Returns:
            QFormLayout: Adaptive form layout.
        """
        layout = QtWidgets.QFormLayout()
        layout.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        return layout

    def table(self, labels, name):
        """Creates a row-selecting table with adaptive, user-resizable columns.

        Args:
            labels (list): Column labels.
            name (str): Stable preference key for user column widths.

        Returns:
            QTableWidget: Empty table.
        """
        table = QtWidgets.QTableWidget(0, len(labels))
        table.setHorizontalHeaderLabels(labels)
        header = table.horizontalHeader()
        for column in range(len(labels)):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(len(labels) - 1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        context_policy = getattr(QtCore.Qt, "CustomContextMenu", None)
        if context_policy is None:
            context_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        table.setContextMenuPolicy(context_policy)
        table.setWordWrap(False)
        table.setProperty("gt_table_name", name)
        self.tables.append(table)
        self.table_registry[name] = table
        return table

    def fit_table_columns(self, table, force=False):
        """Fits fixed columns to visible content and leaves the final column flexible.

        Widths are established once after data is first populated. A forced pass is
        used after font/DPI changes, while normal refreshes preserve manual resizing.

        Args:
            table (QTableWidget): Table whose columns should be initialized.
            force (bool): Recalculate even when this table was already fitted.
        """
        if table.property("gt_user_widths"):
            return
        if table.property("gt_columns_fitted") and not force:
            return
        header = table.horizontalHeader()
        last_column = table.columnCount() - 1
        table.setProperty("gt_adjusting_columns", True)
        try:
            for column in range(table.columnCount()):
                header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.Interactive)
            table.resizeColumnsToContents()
            metrics = table.fontMetrics()
            padding = max(12, metrics.height())
            viewport_width = max(table.viewport().width(), table.width() - table.verticalHeader().width())
            column_cap = max(metrics.horizontalAdvance("00000000"), int(viewport_width * 0.38))
            for column in range(last_column):
                title = table.horizontalHeaderItem(column).text()
                title_width = metrics.horizontalAdvance(title) + padding * 2
                content_width = table.columnWidth(column) + padding
                table.setColumnWidth(column, min(max(title_width, content_width), column_cap))
            title = table.horizontalHeaderItem(last_column).text()
            minimum = metrics.horizontalAdvance(title) + padding * 2
            remaining = viewport_width - sum(table.columnWidth(column) for column in range(last_column))
            table.setColumnWidth(last_column, max(minimum, remaining))
            if table.rowCount():
                table.setProperty("gt_columns_fitted", True)
        finally:
            table.setProperty("gt_adjusting_columns", False)

    def collapsible_group(self, title, checked=False, tooltip=None):
        """Creates a compact checkable group whose contents hide when collapsed.

        Args:
            title (str): Visible group title.
            checked (bool): Whether the content starts expanded.
            tooltip (str): Optional group guidance.

        Returns:
            tuple: Group box, content layout and content widget.
        """
        group = QtWidgets.QGroupBox(title)
        group.setCheckable(True)
        group.setChecked(checked)
        if tooltip:
            group.setToolTip(tooltip)
        group_layout = QtWidgets.QVBoxLayout(group)
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 2, 0, 0)
        group_layout.addWidget(content)
        content.setVisible(checked)
        group.toggled.connect(content.setVisible)
        return group, content_layout, content

    def build_connection(self):
        """Builds connection, launch settings, and model discovery controls."""
        layout = self.page("Connection")
        form = self.form()
        self.mode = QtWidgets.QComboBox()
        for label, key in (("Connect to existing bridge", "existing"), ("Start in WSL", "wsl"),
                           ("Start on Windows", "native")):
            self.mode.addItem(label, key)
        self.url = QtWidgets.QLineEdit()
        self.url.setPlaceholderText("http://127.0.0.1:7861")
        self.url.setToolTip("Kimodo bridge URL. The Kimodo browser demo at port 7860 is a separate service.")
        self.python_path = QtWidgets.QLineEdit()
        self.python_path.setPlaceholderText("Environment folder or its Python executable")
        self.distribution = QtWidgets.QComboBox()
        self.distribution.setEditable(True)
        self.distribution.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.distribution.lineEdit().setPlaceholderText("Query installed distributions or enter a name")
        self.encoder_url = QtWidgets.QLineEdit()
        self.token = QtWidgets.QLineEdit()
        self.token.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.token.setPlaceholderText("Optional bearer token; kept in memory only")
        self.device = QtWidgets.QComboBox()
        self.device.addItems(["auto", "cuda", "cpu"])
        self.start_encoder = QtWidgets.QCheckBox("Auto-start text encoder")
        self.show_console = QtWidgets.QCheckBox("Open bridge console")
        for label, widget in (("Connection", self.mode), ("Bridge URL", self.url),
                              ("Kimodo Python", self.row(self.python_path,
                                                         self.button("browse_python", "Browse Folder"))),
                              ("WSL distribution", self.row(self.distribution, self.button("query_wsl", "Query WSL"))),
                              ("Text encoder URL", self.encoder_url), ("Inference device", self.device),
                              ("Access token", self.token)):
            form.addRow(label, widget)
        self.launch_options = self.row(self.start_encoder, self.show_console)
        self.launch_options.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        form.addRow(self.launch_options)
        layout.addLayout(form)

        self.bridge_control = QtWidgets.QGroupBox("Bridge control")
        self.bridge_control.setToolTip(
            "The bridge is a separate Python server. Local modes run it inside the selected WSL distribution or "
            "Windows environment; Existing mode connects to a server managed elsewhere.")
        control_layout = QtWidgets.QVBoxLayout(self.bridge_control)
        control_note = QtWidgets.QLabel(
            "Connect / Start launches a missing local bridge. Tests do not start services. Restart redeploys the "
            "current GT Tools bridge code and preserves the separate text encoder.")
        control_note.setWordWrap(True)
        control_layout.addWidget(control_note)
        control_layout.addLayout(self.row(self.button("connect", "Connect / Start"),
                                          self.button("test_bridge", "Test Bridge"),
                                          self.button("test_encoder", "Test Text Encoder")))
        control_layout.addLayout(self.row(self.button("restart_bridge", "Restart Bridge"),
                                          self.button("stop_bridge", "Stop Bridge"),
                                          self.button("refresh_models", "Refresh Models")))
        self.connection_info = QtWidgets.QLabel(
            "Bridge status: not tested. Local startup uses your existing Kimodo environment; nothing is installed.")
        self.connection_info.setWordWrap(True)
        self.connection_info.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        control_layout.addWidget(self.connection_info)
        layout.addWidget(self.bridge_control)
        layout.addLayout(self.row(self.button("reset", "Reset Settings")))
        layout.addStretch()

    def build_generation(self):
        """Builds ordered prompt segments, sampling settings, and import options."""
        layout = self.page("Generate")
        self.model = QtWidgets.QComboBox()
        self.model.setMinimumContentsLength(12)
        self.model.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        layout.addLayout(self.row(QtWidgets.QLabel("Model"), self.model,
                                  self.button("download_model", "Download Model")))
        layout.addWidget(QtWidgets.QLabel("Prompt sequence — each row follows the previous segment."))
        self.prompts = self.table(["Seconds", "Motion description"], "prompts")
        layout.addWidget(self.prompts)
        layout.addLayout(self.row(self.button("add_prompt", "Add Segment"), self.button("remove_prompt", "Remove"),
                                  self.button("prompt_up", "Move Up"), self.button("prompt_down", "Move Down")))
        settings = self.form()
        self.seed = QtWidgets.QLineEdit("12345")
        self.seed.setPlaceholderText("Blank = random")
        self.samples = QtWidgets.QSpinBox()
        self.samples.setRange(1, 8)
        self.steps = QtWidgets.QSpinBox()
        self.steps.setRange(1, 1000)
        self.steps.setValue(100)
        self.postprocess = QtWidgets.QCheckBox("Apply foot cleanup")
        self.postprocess.setChecked(True)
        settings.addRow("Seed", self.row(self.seed, QtWidgets.QLabel("Samples"), self.samples,
                                         QtWidgets.QLabel("Steps"), self.steps))
        settings.addRow(self.postprocess)
        layout.addLayout(settings)
        self.advanced = QtWidgets.QGroupBox("Advanced settings")
        self.advanced.setCheckable(True)
        self.advanced.setChecked(False)
        advanced_layout = QtWidgets.QVBoxLayout(self.advanced)
        self.advanced_content = QtWidgets.QWidget()
        advanced_form = self.form()
        self.advanced_content.setLayout(advanced_form)
        self.text_guidance = QtWidgets.QDoubleSpinBox()
        self.constraint_guidance = QtWidgets.QDoubleSpinBox()
        for spin in (self.text_guidance, self.constraint_guidance):
            spin.setRange(0, 20)
            spin.setSingleStep(0.25)
            spin.setValue(2)
        self.transition = QtWidgets.QSpinBox()
        self.transition.setRange(1, 60)
        self.transition.setValue(5)
        self.heading = QtWidgets.QDoubleSpinBox()
        self.heading.setRange(-360, 360)
        advanced_form.addRow("Text / constraint guidance", self.row(self.text_guidance, self.constraint_guidance))
        advanced_form.addRow("Transition frames", self.transition)
        advanced_form.addRow("Initial heading (degrees)", self.heading)
        advanced_layout.addWidget(self.advanced_content)
        self.advanced_content.hide()
        self.advanced.toggled.connect(self.advanced_content.setVisible)
        layout.addWidget(self.advanced)
        layout.addLayout(self.row(self.button("validate", "Validate Request"),
                                  self.button("generate", "Generate Motion")))
        self.make_primary(self.buttons["generate"])

    def build_constraints(self):
        """Builds pose capture, timing, root-path, and native JSON controls."""
        layout = self.page("Constraints")
        instructions = QtWidgets.QLabel(
            "1. Create a pose skeleton or select an imported Kimodo skeleton.\n"
            "2. Pose its joints in Maya, choose a clip frame, then Capture Pose.\n"
            "3. Repeat for more poses. Clip frames start at 1, independent of Maya's current frame.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.pose_source = QtWidgets.QLabel("Pose source: select a Kimodo skeleton")
        self.pose_source.setWordWrap(True)
        layout.addWidget(self.pose_source)
        layout.addLayout(self.row(self.button("create_skeleton", "Create Pose Skeleton"),
                                  self.button("use_selection", "Use Selected Skeleton")))
        self.auto_humanik = QtWidgets.QCheckBox("Automatically add HumanIK to new pose skeletons")
        self.auto_humanik.setChecked(True)
        layout.addWidget(self.auto_humanik)
        self.pose_kind = QtWidgets.QComboBox()
        for label, key in (("Full body", "fullbody"), ("Left hand", "left-hand"), ("Right hand", "right-hand"),
                           ("Left foot", "left-foot"), ("Right foot", "right-foot")):
            self.pose_kind.addItem(label, key)
        self.pose_frame = QtWidgets.QSpinBox()
        self.pose_frame.setRange(1, 7200)
        layout.addLayout(self.row(self.pose_kind, QtWidgets.QLabel("Clip frame"), self.pose_frame,
                                  self.button("capture_pose", "Capture Pose")))
        self.constraints = self.table(["Use", "Clip frame(s)", "Type", "Name"], "constraints")
        layout.addWidget(self.constraints)
        layout.addLayout(self.row(self.button("preview_pose", "Preview Pose"),
                                  self.button("duplicate_constraint", "Duplicate"),
                                  self.button("remove_constraint", "Remove")))
        self.path_frames = QtWidgets.QLineEdit("1, 30, 60, 90")
        self.path_frames.setToolTip("Clip frames for ordered selected locators, or evenly spaced curve samples.")
        layout.addLayout(self.row(QtWidgets.QLabel("Root path frames"), self.path_frames,
                                  self.button("capture_path", "Capture Selected Path")))
        layout.addLayout(self.row(self.button("import_constraints", "Load Constraints JSON"),
                                  self.button("export_constraints", "Save Constraints JSON")))
        note = QtWidgets.QLabel(
            "Full-body keys guide joint positions, not exact rotation locks. Pose capture uses the skeleton's "
            "placement space. Move the placement group to position previews; rotate joints to pose them.")
        note.setWordWrap(True)
        layout.addWidget(note)

    def build_results(self):
        """Builds categorized automation, history, recovery, and result actions."""
        self.results_tab_index = self.tabs.count()
        layout, footer_layout = self.page_with_footer("Results")

        self.results_automation = QtWidgets.QGroupBox("Automatic processing")
        self.results_automation.setToolTip(
            "Configure the normal automatic flow: completed jobs download locally, then a separate Maya process "
            "creates retarget-ready scenes with HumanIK definitions.")
        automation_layout = QtWidgets.QVBoxLayout(self.results_automation)
        automation_note = QtWidgets.QLabel(
            "Normal flow: generate motion â†’ download results â†’ create Maya + HumanIK files. "
            "Both automatic steps are enabled by default.")
        automation_note.setWordWrap(True)
        automation_layout.addWidget(automation_note)
        self.output = QtWidgets.QLineEdit()
        output_form = self.form()
        output_form.addRow("Download folder", self.row(self.output, self.button("browse_output", "Browse"),
                                                      self.button("use_cache", "Package Cache")))
        automation_layout.addLayout(output_form)
        self.auto_download = QtWidgets.QCheckBox("Auto-download finished results")
        automation_layout.addWidget(self.auto_download)
        self.auto_maya_file = QtWidgets.QCheckBox("Auto-create Maya + HumanIK files")
        automation_layout.addWidget(self.auto_maya_file)
        layout.addWidget(self.results_automation)

        self.results_jobs = QtWidgets.QGroupBox("Jobs")
        self.results_jobs.setToolTip(
            "Monitor server requests and their local download/Maya-file state. Select a row to inspect or act on it.")
        jobs_layout = QtWidgets.QVBoxLayout(self.results_jobs)
        description = QtWidgets.QLabel(
            "Each row is one server request (generation or model download). Ready to download means the server "
            "has finished; Downloaded means its tracked local files exist.")
        description.setWordWrap(True)
        jobs_layout.addWidget(description)
        self.jobs = self.table(["Job", "Created", "Status", "Stage / Model"], "jobs")
        self.jobs.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        jobs_layout.addWidget(self.jobs)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        jobs_layout.addWidget(self.progress)
        self.result_info = QtWidgets.QLabel("Select a job to inspect results.")
        self.result_info.setWordWrap(True)
        self.result_info.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        jobs_layout.addWidget(self.result_info)
        jobs_layout.addLayout(self.row(self.button("refresh_job", "Refresh Selected Job"),
                                       self.button("cancel_job", "Cancel Job")))
        layout.addWidget(self.results_jobs)

        self.results_manual, manual_layout, self.results_manual_content = self.collapsible_group(
            "Manual / recovery actions", tooltip="These actions are normally handled by automatic processing. "
            "Expand this section to repair a download, rebuild Maya files, or characterize a current-scene import.")
        manual_note = QtWidgets.QLabel(
            "Normally unnecessary: use these actions to retry a failed automatic step or work with a clip "
            "imported into the current scene.")
        manual_note.setWordWrap(True)
        manual_layout.addWidget(manual_note)
        manual_layout.addLayout(self.row(self.button("download_results", "Download / Repair Results"),
                                         self.button("create_maya_files", "Create / Repair Maya Files"),
                                         self.button("create_humanik", "Add HIK to Current Import")))
        layout.addWidget(self.results_manual)

        self.results_history, history_layout, self.results_history_content = self.collapsible_group(
            "History / diagnostics", tooltip="Inspect the selected job's server directory or clean tracked history "
            "and server files after confirmation.")
        history_layout.addLayout(self.row(self.button("print_server_location", "Print Server Location"),
                                          self.button("clear_finished", "Clear Finished"),
                                          self.button("clear_history", "Clear All History")))
        layout.addWidget(self.results_history)

        self.results_selected = QtWidgets.QGroupBox("Selected result")
        self.results_selected.setToolTip(
            "Open the downloaded job folder, or import its motion skeleton into the current Maya scene. "
            "The sample chooser appears only for jobs containing multiple alternatives.")
        selected_layout = QtWidgets.QVBoxLayout(self.results_selected)
        self.namespace = QtWidgets.QLineEdit("kimodo")
        self.start_frame = QtWidgets.QDoubleSpinBox()
        self.start_frame.setRange(-1000000, 1000000)
        self.start_frame.setValue(1)
        import_form = self.form()
        import_form.addRow("Import namespace / start frame", self.row(self.namespace, self.start_frame))
        selected_layout.addLayout(import_form)
        self.sample_selector = QtWidgets.QWidget()
        sample_layout = QtWidgets.QHBoxLayout(self.sample_selector)
        sample_layout.setContentsMargins(0, 0, 0, 0)
        sample_layout.setSpacing(6)
        self.sample_label = QtWidgets.QLabel("Sample")
        self.sample = QtWidgets.QComboBox()
        sample_layout.addWidget(self.sample_label)
        sample_layout.addWidget(self.sample)
        sample_layout.addStretch()
        self.sample_selector.hide()
        selected_layout.addWidget(self.sample_selector)
        selected_layout.addLayout(self.row(self.button("open_folder", "Open Results Folder"),
                                           self.button("import_sample", "Import Sample to Current Scene")))
        self.make_primary(self.buttons["open_folder"])
        footer_layout.addWidget(self.results_selected)
        layout.addStretch()

    def build_summary(self):
        """Builds a read-only project overview with a primary generation action."""
        layout, footer_layout = self.page_with_footer("Summary")
        introduction = QtWidgets.QLabel(
            "Review the active connection, generation request, constraints, output automation, HumanIK settings, "
            "and job history before submitting.")
        introduction.setWordWrap(True)
        layout.addWidget(introduction)
        self.project_summary = QtWidgets.QLabel("Project settings are loadingâ€¦")
        self.project_summary.setWordWrap(True)
        self.project_summary.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.project_summary.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.project_summary.setStyleSheet(
            "QLabel { background-color: #303030; border: 1px solid #505050; padding: 10px; }")
        layout.addWidget(self.project_summary)
        layout.addStretch()
        summary_generate = self.make_primary(self.button("summary_generate", "Generate Motion"))
        footer_layout.addLayout(self.row(summary_generate))

    def build_humanik(self):
        """Builds optional local characterization overrides, empty by default."""
        layout = self.page("HumanIK")
        note = QtWidgets.QLabel(
            "Select an imported Kimodo group or joint, then click Add HumanIK Definition in Results. "
            "With nothing selected, the current pose source or latest imported sample is used. "
            "Leave overrides blank to automatically use the default Kimodo definition and rest T-pose. "
            "Existing animation is restored after characterization; Retargeter remains a separate tool.")
        note.setWordWrap(True)
        layout.addWidget(note)
        form = self.form()
        self.hik_name = QtWidgets.QLineEdit()
        self.hik_name.setPlaceholderText("Blank = kimodo (automatic default)")
        self.hik_xml = QtWidgets.QLineEdit()
        self.hik_xml.setPlaceholderText("Blank = default Kimodo definition (automatic)")
        self.hik_pose = QtWidgets.QLineEdit()
        self.hik_pose.setPlaceholderText("Blank = default Kimodo T-pose (automatic)")
        self.hik_frame = QtWidgets.QLineEdit()
        self.hik_frame.setPlaceholderText("Blank = default Kimodo T-pose, unless a pose file is set")
        self.hik_lock = QtWidgets.QCheckBox("Lock definition after mapping")
        self.hik_lock.setChecked(True)
        form.addRow("Character name", self.hik_name)
        form.addRow("Definition XML", self.row(self.hik_xml, self.button("browse_hik_xml", "Browse XML")))
        form.addRow("T-pose file", self.row(self.hik_pose, self.button("browse_hik_pose", "Browse Pose")))
        form.addRow("Reference frame", self.hik_frame)
        form.addRow(self.hik_lock)
        layout.addLayout(form)
        for title, actions, icon in (
            ("Actions", (("hik_export_pose", "Export Pose"), ("hik_export_source", "Export Source HIK")),
             resources.Icon.rigger_action_export_grayscale),
            ("Testing", (("hik_apply_pose", "Apply Pose To Source"), ("hik_import_source", "Import Source HIK")),
             resources.Icon.rigger_action_import_grayscale)):
            layout.addWidget(QtWidgets.QLabel(title))
            buttons = []
            for key, label in actions:
                button = self.button(key, label)
                button.setIcon(ui_qt.QtGui.QIcon(icon))
                buttons.append(button)
            layout.addLayout(self.row(*buttons))
        layout.addStretch()

    def closeEvent(self, event):
        """Stops UI polling without terminating server jobs.

        Args:
            event (QCloseEvent): Qt close event.
        """
        if self.controller:
            self.controller.close()
        self.observe_screen(None)
        super().closeEvent(event)

    def apply_tooltips(self):
        """Attaches detailed, wrapping help to controls, actions, tabs, and table headers."""
        for key, text in ACTION_TOOLTIPS.items():
            self.buttons[key].setToolTip(f"<qt>{html.escape(text)}</qt>")
        for name, text in CONTROL_TOOLTIPS.items():
            getattr(self, name).setToolTip(f"<qt>{html.escape(text)}</qt>")
        for index, text in enumerate(TAB_TOOLTIPS):
            self.tabs.setTabToolTip(index, text)
        for table in self.tables:
            for column in range(table.columnCount()):
                table.horizontalHeaderItem(column).setToolTip(table.toolTip())
        for form in self.findChildren(QtWidgets.QFormLayout):
            for row in range(form.rowCount()):
                label = form.itemAt(row, QtWidgets.QFormLayout.ItemRole.LabelRole)
                field = form.itemAt(row, QtWidgets.QFormLayout.ItemRole.FieldRole)
                if not label or not label.widget() or not field:
                    continue
                if field.widget():
                    label.widget().setToolTip(field.widget().toolTip())
                elif field.layout():
                    texts = [field.layout().itemAt(index).widget().toolTip()
                             for index in range(field.layout().count()) if field.layout().itemAt(index).widget()]
                    label.widget().setToolTip("<br>".join(texts))
        caption_controls = {"Samples": "samples", "Steps": "steps", "Clip frame": "pose_frame",
                            "Root path frames": "path_frames", "Sample": "sample", "Model": "model"}
        for label in self.findChildren(QtWidgets.QLabel):
            label.setWordWrap(True)
            if not label.toolTip():
                control = caption_controls.get(label.text())
                label.setToolTip(getattr(self, control).toolTip() if control else label.text())

    def refresh_layout_metrics(self, *unused):
        """Fits controls to current font metrics and the active screen's logical geometry.

        Args:
            *unused: Optional Qt signal arguments.
        """
        if self._updating_metrics:
            return
        self._updating_metrics = True
        try:
            metrics = self.fontMetrics()
            line_height = metrics.height()
            padding = max(8, round(line_height * 0.5))
            for widget in self.findChildren(QtWidgets.QWidget):
                if isinstance(widget, (QtWidgets.QLabel, QtWidgets.QLineEdit, QtWidgets.QComboBox,
                                       QtWidgets.QAbstractSpinBox, QtWidgets.QPushButton, QtWidgets.QCheckBox,
                                       QtWidgets.QTableWidget, QtWidgets.QGroupBox, QtWidgets.QTabBar)):
                    widget.setFont(self.font())
                if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QComboBox, QtWidgets.QAbstractSpinBox,
                                       QtWidgets.QPushButton)):
                    widget.setMinimumHeight(max(widget.minimumSizeHint().height(), line_height + padding))
                if isinstance(widget, QtWidgets.QComboBox):
                    widget.setSizeAdjustPolicy(
                        QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                    widget.setMinimumContentsLength(12)
            title_font = ui_qt.QtGui.QFont(self.font())
            title_font.setPointSizeF(max(9, title_font.pointSizeF()) * 1.3)
            title_font.setBold(True)
            self.heading_label.setFont(title_font)
            for spin in self.findChildren(QtWidgets.QAbstractSpinBox):
                spin.setMinimumWidth(metrics.horizontalAdvance("0000") + padding * 3)
            for table in self.tables:
                table.verticalHeader().setDefaultSectionSize(line_height + padding)
                table.setMinimumHeight(line_height * 7)
                self.fit_table_columns(table, force=True)
            self.status.setMinimumHeight(line_height * 2 + padding)
            screen = self._observed_screen or self.screen() or QtWidgets.QApplication.primaryScreen()
            if screen:
                available = screen.availableGeometry()
                max_width = max(200, available.width() - padding * 4)
                max_height = max(200, available.height() - padding * 6)
                self.setMinimumSize(min(460, max_width), min(380, max_height))
                width = self.width() if self._sized_once else max(800, metrics.averageCharWidth() * 95)
                height = self.height() if self._sized_once else max(730, line_height * 46)
                self.resize(min(max_width, width), min(max_height, height))
                self._sized_once = True
            self.reflow_rows()
        finally:
            self._updating_metrics = False

    def reflow_rows(self):
        """Stacks crowded rows vertically while preserving the active widgets."""
        for layout in self.responsive_rows:
            widths = [layout.itemAt(index).widget().sizeHint().width() for index in range(layout.count())
                      if layout.itemAt(index).widget()]
            required = sum(widths) + max(0, len(widths) - 1) * max(0, layout.spacing())
            available = layout.geometry().width() or max(1, self.width() - 50)
            direction = (QtWidgets.QBoxLayout.Direction.TopToBottom if required > available
                         else QtWidgets.QBoxLayout.Direction.LeftToRight)
            if layout.direction() != direction:
                layout.setDirection(direction)

    def schedule_metrics_refresh(self, *unused):
        """Defers measurement until a newly displayed tab has its final geometry.

        Args:
            *unused: Qt tab-change signal arguments.
        """
        if hasattr(self, "status"):
            QtCore.QTimer.singleShot(0, self.refresh_layout_metrics)

    def observe_screen(self, screen):
        """Reconnects Qt screen signals when a floating window changes monitors.

        Args:
            screen (QScreen or None): Newly active monitor or None during close.
        """
        if self._observed_screen:
            try:
                self._observed_screen.logicalDotsPerInchChanged.disconnect(self.refresh_layout_metrics)
                self._observed_screen.availableGeometryChanged.disconnect(self.refresh_layout_metrics)
            except (RuntimeError, TypeError):
                pass
        self._observed_screen = screen
        if screen:
            screen.logicalDotsPerInchChanged.connect(self.refresh_layout_metrics)
            screen.availableGeometryChanged.connect(self.refresh_layout_metrics)
            self.refresh_layout_metrics()

    def showEvent(self, event):
        """Tracks the displayed screen without changing Maya's global DPI settings.

        Args:
            event (QShowEvent): Qt show notification.
        """
        super().showEvent(event)
        handle = self.windowHandle()
        if handle and handle is not self._screen_handle:
            self._screen_handle = handle
            handle.screenChanged.connect(self.observe_screen)
        self.observe_screen(handle.screen() if handle else self.screen())

    def resizeEvent(self, event):
        """Reflows action rows when resized or docked into a narrower area.

        Args:
            event (QResizeEvent): Qt size notification.
        """
        super().resizeEvent(event)
        if hasattr(self, "responsive_rows"):
            self.reflow_rows()

    def changeEvent(self, event):
        """Recomputes metrics after font or application-style changes.

        Args:
            event (QEvent): Qt property-change notification.
        """
        super().changeEvent(event)
        if hasattr(self, "status") and event.type() in (
                QtCore.QEvent.Type.FontChange, QtCore.QEvent.Type.ApplicationFontChange):
            self.refresh_layout_metrics()
