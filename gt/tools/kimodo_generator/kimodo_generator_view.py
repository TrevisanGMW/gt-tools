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
                         self.button("save_setup", "Save Setup"),
                         self.button("load_default_setup", "Reset to Default Setup"))
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
        """Creates an arrow-toggle section without a checkbox-style group title.

        Args:
            title (str): Visible group title.
            checked (bool): Whether the content starts expanded.
            tooltip (str): Optional group guidance.

        Returns:
            tuple: Section widget, content layout and content widget.
        """
        group = QtWidgets.QWidget()
        group_layout = QtWidgets.QVBoxLayout(group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        toggle = QtWidgets.QToolButton()
        toggle.setText(title)
        toggle.setCheckable(True)
        toggle.setChecked(checked)
        toggle.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toggle.setArrowType(QtCore.Qt.ArrowType.DownArrow if checked else QtCore.Qt.ArrowType.RightArrow)
        toggle.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        toggle.setStyleSheet("QToolButton { border: none; font-weight: bold; text-align: left; }")
        if tooltip:
            group.setToolTip(tooltip)
            toggle.setToolTip(tooltip)
        group_layout.addWidget(toggle)
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 2, 0, 0)
        group_layout.addWidget(content)
        content.setVisible(checked)

        def update_section(expanded):
            """Updates the disclosure arrow and section visibility.

            Args:
                expanded (bool): Whether the section is open.
            """
            toggle.setArrowType(QtCore.Qt.ArrowType.DownArrow if expanded else QtCore.Qt.ArrowType.RightArrow)
            content.setVisible(expanded)

        toggle.toggled.connect(update_section)
        group.toggle_button = toggle
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
        self.auto_connect = QtWidgets.QCheckBox("Auto-connect on launch")
        for label, widget in (("Connection", self.mode), ("Bridge URL", self.url),
                              ("Kimodo Python", self.row(self.python_path,
                                                         self.button("browse_python", "Browse Folder"))),
                              ("WSL distribution", self.row(self.distribution, self.button("query_wsl", "Query WSL"))),
                              ("Text encoder URL", self.encoder_url), ("Inference device", self.device),
                              ("Access token", self.token)):
            form.addRow(label, widget)
        self.launch_options = self.row(self.start_encoder, self.show_console, self.auto_connect)
        self.launch_options.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        form.addRow(self.launch_options)
        self.auto_connect_options = self.launch_options
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
        self.prompt_frames = QtWidgets.QCheckBox("Enter durations in frames")
        layout.addLayout(self.row(QtWidgets.QLabel("Prompt sequence — each row follows the previous segment."),
                                  self.prompt_frames))
        self.prompts = self.table(["Seconds", "Motion description"], "prompts")
        layout.addWidget(self.prompts)
        layout.addLayout(self.row(self.button("add_prompt", "Add Segment"), self.button("remove_prompt", "Remove"),
                                  self.button("prompt_up", "Move Up"), self.button("prompt_down", "Move Down")))
        settings = self.form()
        self.seed = QtWidgets.QLineEdit("12345")
        self.seed.setPlaceholderText("Blank = random")
        seed_controls = self.row(self.seed, self.button("randomize_seed", "Randomize"),
                                 QtWidgets.QLabel("Samples"))
        self.samples = QtWidgets.QSpinBox()
        self.samples.setRange(1, 8)
        self.steps = QtWidgets.QSpinBox()
        self.steps.setRange(1, 1000)
        self.steps.setValue(100)
        self.postprocess = QtWidgets.QCheckBox("Apply foot cleanup")
        self.postprocess.setChecked(True)
        seed_controls.addWidget(self.samples)
        seed_controls.addWidget(QtWidgets.QLabel("Steps"))
        seed_controls.addWidget(self.steps)
        settings.addRow("Seed", seed_controls)
        layout.addLayout(settings)
        self.advanced, advanced_layout, self.advanced_content = self.collapsible_group(
            "Advanced Settings", checked=False,
            tooltip="Optional generation controls. Expand to adjust foot cleanup, guidance, transition overlap, or "
                    "initial heading; collapsing this area keeps all current values.")
        advanced_form = self.form()
        advanced_layout.addLayout(advanced_form)
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
        advanced_form.addRow(self.postprocess)
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
        self.auto_humanik = QtWidgets.QCheckBox("Automatically add HumanIK")
        self.auto_humanik.setChecked(True)
        self.template_pose_previews = QtWidgets.QCheckBox("Template pose previews (unselectable)")
        self.template_pose_previews.setChecked(True)
        self.limit_body_joint_translations = QtWidgets.QCheckBox("Limit non-root joint translations")
        self.limit_body_joint_translations.setChecked(True)
        layout.addLayout(self.row(self.auto_humanik, self.template_pose_previews,
                                  self.limit_body_joint_translations))
        self.pose_kind = QtWidgets.QComboBox()
        for label, key in (("Full body", "fullbody"), ("Left hand", "left-hand"), ("Right hand", "right-hand"),
                           ("Left foot", "left-foot"), ("Right foot", "right-foot")):
            self.pose_kind.addItem(label, key)
        self.pose_frame = QtWidgets.QSpinBox()
        self.pose_frame.setRange(1, 7200)
        context_policy = getattr(QtCore.Qt, "CustomContextMenu", None)
        if context_policy is None:
            context_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        self.pose_frame.setContextMenuPolicy(context_policy)
        frame_field = QtWidgets.QWidget()
        frame_field_layout = QtWidgets.QHBoxLayout(frame_field)
        frame_field_layout.setContentsMargins(0, 0, 0, 0)
        frame_field_layout.setSpacing(4)
        self.pose_frame_label = QtWidgets.QLabel("Clip Frame: ")
        self.pose_frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        frame_field_layout.addWidget(self.pose_frame_label)
        frame_field_layout.addWidget(self.pose_frame)
        frame_field.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        layout.addLayout(self.row(self.pose_kind, frame_field, self.button("capture_pose", "Capture Pose")))
        self.constraints = self.table(["Use", "Clip frame(s)", "Type", "Name"], "constraints")
        layout.addWidget(self.constraints)
        layout.addLayout(self.row(self.button("preview_all_constraints", "Preview All Constraints"),
                                  self.button("remove_pose_previews", "Remove All Previews")))
        self.path_frames = QtWidgets.QLineEdit()
        self.path_frames.setPlaceholderText("Blank = auto spread over clip")
        self.path_frames.setToolTip(
            "Optional comma-separated destination clip frames, one per selected transform. Leave empty with two or "
            "more selected transforms to spread them from the first through last generated frame. With one selected "
            "NURBS curve and no explicit frames, the Curve samples setting controls how many points are distributed "
            "evenly across the full generated clip. Entering explicit frames disables that setting and uses one "
            "curve point per frame. Frames must fit inside the generated duration.")
        path_frames_form = self.form()
        path_frames_form.addRow("Root path frames", self.path_frames)
        layout.addLayout(path_frames_form)
        self.path_curve_samples = QtWidgets.QSpinBox()
        self.path_curve_samples.setRange(2, 7200)
        self.path_curve_samples.setValue(4)
        self.path_curve_samples.setToolTip(
            "Number of equally spaced points captured from one selected NURBS curve when Root path frames is blank. "
            "The point keys span the generated clip. Two or more selected transforms ignore this value. If explicit "
            "frames are entered, the count is determined by that list and this control is disabled. The default is "
            "four samples.")
        self.path_frames.textChanged.connect(lambda text: self.path_curve_samples.setEnabled(not text.strip()))
        samples_field = QtWidgets.QWidget()
        samples_layout = QtWidgets.QHBoxLayout(samples_field)
        samples_layout.setContentsMargins(0, 0, 0, 0)
        samples_layout.setSpacing(4)
        self.path_curve_samples_label = QtWidgets.QLabel("Curve samples")
        samples_layout.addWidget(self.path_curve_samples_label)
        samples_layout.addWidget(self.path_curve_samples)
        samples_field.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.path_heading = QtWidgets.QComboBox()
        for label, key in (("None", "none"), ("Direction of travel", "path"), ("Node +Z axis", "node"),
                           ("Fixed", "fixed")):
            self.path_heading.addItem(label, key)
        self.path_heading.setToolTip(
            "Facing direction captured with the root path. None leaves facing to the model. Direction of travel "
            "faces along the curve tangent or movement between samples, holding the last facing while stopped. "
            "Node +Z axis uses each selected transform's world +Z axis, or an animated transform's keyed rotation. "
            "Fixed uses only the offset as an absolute heading.")
        self.path_heading_offset = QtWidgets.QDoubleSpinBox()
        self.path_heading_offset.setRange(-360, 360)
        self.path_heading_offset.setDecimals(1)
        self.path_heading_offset.setSuffix(" deg")
        self.path_heading_offset.setToolTip(
            "Degrees added to the captured heading, or the absolute heading when Root heading is Fixed. 0 faces +Z. "
            "Use 180 for backward travel, or 90 / -90 to strafe.")
        heading_field = QtWidgets.QWidget()
        heading_layout = QtWidgets.QHBoxLayout(heading_field)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.setSpacing(4)
        self.path_heading_label = QtWidgets.QLabel("Root heading")
        heading_layout.addWidget(self.path_heading_label)
        heading_layout.addWidget(self.path_heading, 1)
        self.path_heading_offset_label = QtWidgets.QLabel("Offset")
        heading_layout.addWidget(self.path_heading_offset_label)
        heading_layout.addWidget(self.path_heading_offset)
        layout.addWidget(heading_field)
        layout.addLayout(self.row(samples_field, self.button("capture_path", "Capture Path from Transforms")))
        note = QtWidgets.QLabel(
            "Full-body keys guide joint positions, not exact rotation locks. Pose capture uses the skeleton's "
            "placement space. Move the placement group to position previews; rotate joints to pose them.")
        note.setWordWrap(True)
        layout.addWidget(note)

    def build_results(self):
        """Builds categorized automation, history, recovery, and result actions."""
        self.results_tab_index = self.tabs.count()
        layout, footer_layout = self.page_with_footer("Results")

        self.results_automation, automation_layout, self.results_automation_content = self.collapsible_group(
            "Automatic Processing", checked=False,
            tooltip="Configure the normal automatic flow: completed jobs download locally, then a separate Maya "
            "process creates retarget-ready scenes with HumanIK definitions.")
        self.results_automation_toggle = self.results_automation.toggle_button
        automation_note = QtWidgets.QLabel(
            "All options are enabled by default: completed jobs download, get a retarget-ready Maya + HumanIK file, "
            "then force-clear the current scene and import it. Uncheck Force-clear to preserve the open scene.")
        automation_note.setWordWrap(True)
        automation_layout.addWidget(automation_note)
        self.output = QtWidgets.QLineEdit()
        output_form = self.form()
        output_form.addRow("Download folder", self.row(self.output, self.button("browse_output", "Browse"),
                                                      self.button("use_cache", "Reset to Package Cache")))
        automation_layout.addLayout(output_form)
        options_layout = QtWidgets.QVBoxLayout()
        self.auto_download = QtWidgets.QCheckBox("Auto-download results")
        self.auto_download.setChecked(True)
        self.auto_download.setToolTip(
            "Download generated motion files as soon as the server reports the job succeeded. "
            "Downloaded files are stored under the selected output folder.")
        self.auto_maya_file = QtWidgets.QCheckBox("Auto-create Maya + HumanIK")
        self.auto_maya_file.setChecked(True)
        self.auto_maya_file.setToolTip(
            "Use a separate mayapy process to create a retarget-ready Maya file for each downloaded motion. "
            "This does not modify the currently open Maya scene.")
        self.auto_import_maya = QtWidgets.QCheckBox("Auto-import Maya file")
        self.auto_import_maya.setChecked(True)
        self.auto_import_maya.setToolTip(
            "After generated Maya file(s) are ready, import the result into the current scene. "
            "Import all samples chooses every generated alternative; otherwise the selected sample, or the first "
            "available sample when none is selected, is imported. Requires Auto-create Maya + HumanIK for newly "
            "generated results.")
        self.auto_import_all_samples = QtWidgets.QCheckBox("Import all samples into one scene")
        self.auto_import_all_samples.setChecked(True)
        self.auto_import_all_samples.setToolTip(
            "When Auto-import Maya file is enabled, import every generated sample scene into the same Maya scene "
            "instead of importing only the selected or first sample. Force-clear runs once before importing them. "
            "Each sample gets a distinct namespace. Requires Auto-create Maya + HumanIK.")
        self.auto_clear_scene = QtWidgets.QCheckBox("Force-clear scene before import")
        self.auto_clear_scene.setChecked(True)
        self.auto_clear_scene.setToolTip(
            "When Auto-import Maya file is enabled, run Maya's force-new-scene command immediately before import. "
            "This discards current scene contents without a save prompt. Leave off to import into the current scene.")
        self.auto_frame_rate = QtWidgets.QCheckBox("Match Maya frame-rate to motion")
        self.auto_frame_range = QtWidgets.QCheckBox("Match playback range to generated frames")
        self.auto_frame_rate.setChecked(True)
        self.auto_frame_range.setChecked(True)
        for widget in (self.auto_import_all_samples, self.auto_clear_scene,
                       self.auto_frame_rate, self.auto_frame_range):
            widget.setEnabled(self.auto_import_maya.isChecked())
        options_layout.addLayout(self.row(self.auto_download, self.auto_maya_file))
        options_layout.addLayout(self.row(self.auto_import_maya, self.auto_import_all_samples))
        options_layout.addLayout(self.row(self.auto_clear_scene, self.auto_frame_rate))
        options_layout.addLayout(self.row(self.auto_frame_range))
        automation_layout.addLayout(options_layout)
        import_heading = QtWidgets.QLabel("Maya import defaults")
        import_heading_font = ui_qt.QtGui.QFont(import_heading.font())
        import_heading_font.setBold(True)
        import_heading.setFont(import_heading_font)
        automation_layout.addWidget(import_heading)
        self.namespace = QtWidgets.QLineEdit("kimodo")
        self.start_frame = QtWidgets.QDoubleSpinBox()
        self.start_frame.setRange(-1000000, 1000000)
        self.start_frame.setValue(1)
        import_form = self.form()
        import_form.addRow("Import namespace", self.namespace)
        import_form.addRow("Start frame", self.start_frame)
        automation_layout.addLayout(import_form)

        self.results_jobs = QtWidgets.QGroupBox("Jobs")
        self.results_jobs.setToolTip(
            "Monitor server requests and their local download/Maya-file state. Select a row to inspect or act on it.")
        jobs_layout = QtWidgets.QVBoxLayout(self.results_jobs)
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
        layout.addWidget(self.results_automation)

        self.results_manual, manual_layout, self.results_manual_content = self.collapsible_group(
            "Recovery And Job Management", tooltip="Use these actions to recover a failed automatic step, work with "
            "the selected result, inspect its server location, or clean job history.")
        self.results_manual_toggle = self.results_manual.toggle_button
        manual_note = QtWidgets.QLabel(
            "Use these if automatic processing is disabled or needs repair. History cleanup and server diagnostics "
            "are grouped here as well.")
        manual_note.setWordWrap(True)
        manual_layout.addWidget(manual_note)
        manual_layout.addLayout(self.row(self.button("download_results", "Download / Repair Results"),
                                         self.button("create_maya_files", "Create / Repair Maya Files")))
        manual_layout.addLayout(self.row(self.button("import_maya_file", "Import Generated Maya File"),
                                         self.button("create_humanik", "Add HIK to Current Import")))
        manual_layout.addLayout(self.row(self.button("print_server_location", "Print Server Location"),
                                         self.button("delete_server_files", "Delete Server Files")))
        manual_layout.addLayout(self.row(self.button("clear_finished", "Clear Finished"),
                                         self.button("clear_history", "Clear All History")))
        layout.addWidget(self.results_manual)

        self.results_selected = QtWidgets.QGroupBox("Selected result")
        self.results_selected.setToolTip(
            "Open the downloaded job folder, or import its motion skeleton into the current Maya scene. "
            "The sample chooser appears only for jobs containing multiple alternatives. Expand Automatic Processing "
            "to choose automatic import of every generated sample into one scene, or edit the import namespace and "
            "start frame used by Import Sample.")
        selected_layout = QtWidgets.QVBoxLayout(self.results_selected)
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
            if key in self.buttons:
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
                            "Root path frames": "path_frames", "Curve samples": "path_curve_samples",
                            "Root heading": "path_heading", "Offset": "path_heading_offset",
                            "Import namespace": "namespace", "Start frame": "start_frame",
                            "Sample": "sample", "Model": "model"}
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
                                       QtWidgets.QToolButton, QtWidgets.QAbstractSpinBox, QtWidgets.QPushButton,
                                       QtWidgets.QCheckBox, QtWidgets.QTableWidget, QtWidgets.QGroupBox,
                                       QtWidgets.QTabBar)):
                    widget.setFont(self.font())
                if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QComboBox, QtWidgets.QToolButton,
                                       QtWidgets.QAbstractSpinBox, QtWidgets.QPushButton)):
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
        controller = getattr(self, "controller", None)
        if controller:
            controller.fit_jobs_table_width()
            controller.fit_constraints_table_width()

    def reflow_rows(self):
        """Stacks crowded rows vertically while preserving the active widgets."""
        for layout in self.responsive_rows:
            widths = [layout.itemAt(index).widget().sizeHint().width() for index in range(layout.count())
                      if layout.itemAt(index).widget()]
            required = sum(widths) + max(0, len(widths) - 1) * max(0, layout.spacing())
            available = min(layout.geometry().width() or max(1, self.width() - 50),
                            max(1, self.width() - 50))
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
        controller = getattr(self, "controller", None)
        if controller:
            controller.fit_jobs_table_width()
            controller.fit_constraints_table_width()

    def changeEvent(self, event):
        """Recomputes metrics after font or application-style changes.

        Args:
            event (QEvent): Qt property-change notification.
        """
        super().changeEvent(event)
        if hasattr(self, "status") and event.type() in (
                QtCore.QEvent.Type.FontChange, QtCore.QEvent.Type.ApplicationFontChange):
            self.refresh_layout_metrics()
