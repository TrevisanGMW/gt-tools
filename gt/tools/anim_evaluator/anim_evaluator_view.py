"""
Animation Evaluator View - Widgets only. Builds without Maya scene data or controller state.
"""

from gt.tools.anim_evaluator.anim_evaluator_widgets import PresetEditorWidget, DISABLED_STYLESHEET
from gt.tools.anim_evaluator.anim_evaluator_widgets import HEADER_STYLESHEET, fit_combo_to_items
from gt.tools.anim_evaluator.anim_evaluator_widgets import install_empty_click_deselect, get_text_width
from gt.core.motion_eval import checks_base
from gt.core.motion_eval import presets
from gt.core.motion_eval import sampling
from gt.core.motion_eval import scene_io
from gt.core.motion_eval import templates
from gt.ui import resource_library as ui_res_lib
from gt.ui import qt_import as ui_qt
from gt.ui import qt_utils

STATUS_COLORS = {
    checks_base.STATUS_PASSED: "#94FF9D",
    checks_base.STATUS_WARNING: "#FFD166",
    checks_base.STATUS_FAILED: "#FF8A8A",
    checks_base.STATUS_SKIPPED: "#888888",
    checks_base.STATUS_DISABLED: "#666666",
}
CUSTOM_TEMPLATE_LABEL = "Custom Skeleton (File / Edited)"
TARGET_MODE_LABELS = {
    scene_io.TARGET_DEDICATED_NODE: "Network Node",
    scene_io.TARGET_ROLE: "Skeleton Role",
    scene_io.TARGET_NAMED_NODE: "Named Node",
}
LABEL_WIDTH = 64
RESULT_COLUMNS = ["Check", "Score", "Status", "Frames", "Events"]
ROLE_COLUMNS = ["Role", "Joint Names (comma separated)", "Resolved In Scene"]


class AnimEvaluatorView(metaclass=qt_utils.MayaWindowMeta):
    """Main Animation Evaluator window."""

    def __init__(self, parent=None, version=None):
        """Builds the window.

        Args:
            parent (QWidget, optional): Maya parent window.
            version (str, optional): Version shown in the title.
        """
        super().__init__(parent=parent)
        self.controller = None
        self.buttons = {}
        self.setWindowTitle("Animation Evaluator" + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_anim_evaluator))
        self.setStyleSheet("\n".join((
            ui_res_lib.Stylesheet.maya_dialog_base,
            ui_res_lib.Stylesheet.checkbox_base,
            ui_res_lib.Stylesheet.tab_widget_base,
            ui_res_lib.Stylesheet.scroll_bar_base,
            "QWidget { color: #DDDDDD; } QGroupBox { margin-top: 12px; padding-top: 8px; } "
            "QTreeWidget, QTableWidget { background-color: #2B2B2B; alternate-background-color: #303030; }",
            DISABLED_STYLESHEET,
            HEADER_STYLESHEET,
        )))
        self.setMinimumWidth(520)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addLayout(self.build_header())
        layout.addWidget(self.build_setup_group())
        self.tabs = ui_qt.QtWidgets.QTabWidget()
        self.tabs.addTab(self.build_results_tab(), "Results")
        self.preset_editor = PresetEditorWidget(parent=self, show_mode=False)
        self.tabs.addTab(self.wrap_in_scroll(self.preset_editor), "Checks")
        self.tabs.addTab(self.build_skeleton_tab(), "Skeleton")
        self.tabs.addTab(self.wrap_in_scroll(self.build_preferences_tab()), "Preferences")
        layout.addWidget(self.tabs, 1)
        self.status_label = ui_qt.QtWidgets.QLabel("Ready. Pick a mode (and a skeleton for Biped), then Evaluate.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(32)
        layout.addWidget(self.status_label)
        self.resize(640, 820)
        qt_utils.center_window(self)

    # ------------------------------------------------ Helpers ------------------------------------------------
    def button(self, key, label, tooltip, icon=None):
        """Creates and registers a button.

        Args:
            key (str): Controller action key.
            label (str): Button text.
            tooltip (str): Tooltip.
            icon (str, optional): Icon path.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setToolTip(tooltip)
        if icon:
            button.setIcon(ui_qt.QtGui.QIcon(icon))
        self.buttons[key] = button
        return button

    @staticmethod
    def wrap_in_scroll(widget):
        """Wraps a widget in a scroll area for small screens.

        Args:
            widget (QWidget): Content widget.

        Returns:
            QScrollArea: Scroll area.
        """
        scroll = ui_qt.QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = ui_qt.QtWidgets.QWidget()
        container_layout = ui_qt.QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.addWidget(widget)
        scroll.setWidget(container)
        return scroll

    @staticmethod
    def labeled_row(label_text, tooltip=""):
        """Creates a row layout with a fixed-width label.

        Args:
            label_text (str): Label text.
            tooltip (str): Label tooltip.

        Returns:
            QHBoxLayout: Row layout.
        """
        row = ui_qt.QtWidgets.QHBoxLayout()
        label = ui_qt.QtWidgets.QLabel(label_text)
        label.setFixedWidth(LABEL_WIDTH)
        label.setToolTip(tooltip)
        row.addWidget(label)
        return row

    @staticmethod
    def set_item_tooltips(combo, tooltips):
        """Sets a tooltip on each combo item.

        Args:
            combo (QComboBox): Combo box.
            tooltips (dict): Item text to tooltip.
        """
        for index in range(combo.count()):
            tooltip = tooltips.get(combo.itemText(index))
            if tooltip:
                combo.setItemData(index, tooltip, ui_qt.QtLib.ItemDataRole.ToolTipRole)

    # ------------------------------------------------ Build ------------------------------------------------
    def build_header(self):
        """Builds the title row.

        Returns:
            QHBoxLayout: Header layout.
        """
        header = ui_qt.QtWidgets.QHBoxLayout()
        title = ui_qt.QtWidgets.QLabel("Animation Evaluator")
        title.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))
        header.addWidget(title, 1)
        header.addWidget(self.button("reset", "Reset Options",
                                     "Restore every tool setting, the skeleton, and the checks to their defaults."))
        return header

    def build_setup_group(self):
        """Builds the always-visible setup controls.

        Returns:
            QGroupBox: Setup group.
        """
        group = ui_qt.QtWidgets.QGroupBox("Setup")
        layout = ui_qt.QtWidgets.QVBoxLayout(group)
        layout.setSpacing(5)
        mode_tooltip = (
            "What to check:\n"
            "General: checks that work on any animated nodes (noise, pops, speed, scale, ...).\n"
            "Biped: the General checks plus feet, ground, knee, and body checks.\n"
            "Biped needs a skeleton so the tool knows which joints are the hips, legs, and feet."
        )
        mode_row = self.labeled_row("Mode", mode_tooltip)
        self.mode_combo = ui_qt.QtWidgets.QComboBox()
        for mode in checks_base.MODE_VALUES:
            self.mode_combo.addItem(presets.get_mode_display_label(mode), mode)
        self.mode_combo.setToolTip(mode_tooltip)
        fit_combo_to_items(self.mode_combo)
        mode_row.addWidget(self.mode_combo)
        scope_tooltip = (
            "Nodes evaluated in General mode.\n"
            "Biped mode always uses the joints mapped by the skeleton, so this is disabled there."
        )
        self.scope_label = ui_qt.QtWidgets.QLabel("Nodes")
        self.scope_label.setToolTip(scope_tooltip)
        mode_row.addWidget(self.scope_label)
        self.scope_combo = ui_qt.QtWidgets.QComboBox()
        self.scope_combo.addItems(sampling.GENERAL_SCOPES)
        self.scope_combo.setToolTip(scope_tooltip)
        self.set_item_tooltips(self.scope_combo, sampling.SCOPE_TOOLTIPS)
        mode_row.addWidget(self.scope_combo)
        self.node_list_field = ui_qt.QtWidgets.QLineEdit()
        self.node_list_field.setPlaceholderText("prop_ctrl, *:root")
        self.node_list_field.setToolTip(
            "Nodes for the Node List scope, comma separated. Wildcards such as *:root are allowed.\n"
            "Enabled when Nodes is set to Node List."
        )
        mode_row.addWidget(self.node_list_field, 1)
        layout.addLayout(mode_row)
        skeleton_tooltip = (
            "Skeleton that tells the evaluator which joints are the hips, spine, legs, feet, and arms.\n"
            "Used in Biped mode and by the Template Joints node scope. Edit or create one in the Skeleton tab."
        )
        skeleton_row = self.labeled_row("Skeleton", skeleton_tooltip)
        self.skeleton_label = skeleton_row.itemAt(0).widget()
        self.template_combo = ui_qt.QtWidgets.QComboBox()
        for template_key in templates.get_builtin_template_keys():
            self.template_combo.addItem(templates.BUILTIN_TEMPLATES[template_key]["name"], template_key)
        self.template_combo.addItem(CUSTOM_TEMPLATE_LABEL, "")
        self.template_combo.setToolTip(
            "Built-in skeletons, or a Custom Skeleton loaded from a file or edited in the Skeleton tab.\n"
            "Disabled in General mode unless Nodes is Template Joints."
        )
        skeleton_row.addWidget(self.template_combo, 1)
        skeleton_row.addWidget(self.button("load_template", "Load",
                                           "Load a Custom Skeleton JSON file\n(saved from the Skeleton tab)."))
        skeleton_row.addWidget(self.button(
            "detect_template", "Detect",
            "Find the built-in skeleton whose joint names match the open scene\nand check every role."
        ))
        layout.addLayout(skeleton_row)
        range_tooltip = "Frames to evaluate. Hover each option for details."
        range_row = self.labeled_row("Range", range_tooltip)
        self.range_combo = ui_qt.QtWidgets.QComboBox()
        self.range_combo.addItems(sampling.RANGE_MODES)
        self.range_combo.setToolTip(
            "\n".join([range_tooltip, ""] + [f"{mode}: {text}" for mode, text in sampling.RANGE_TOOLTIPS.items()])
        )
        self.set_item_tooltips(self.range_combo, sampling.RANGE_TOOLTIPS)
        range_row.addWidget(self.range_combo, 1)
        self.start_spin = ui_qt.QtWidgets.QSpinBox()
        self.end_spin = ui_qt.QtWidgets.QSpinBox()
        for spin, label_text in ((self.start_spin, "Start"), (self.end_spin, "End")):
            spin.setRange(-1000000, 1000000)
            spin.setPrefix(f"{label_text}: ")
            spin.setMinimumWidth(110)
            spin.setToolTip(f"Custom {label_text.lower()} frame. Enabled when Range is Custom.")
            range_row.addWidget(spin)
        layout.addLayout(range_row)
        run_row = ui_qt.QtWidgets.QHBoxLayout()
        evaluate_button = self.button(
            "evaluate", "Evaluate Scene",
            "Sample the open scene over the chosen range and run every enabled check.\n"
            "The scene is not modified.",
            ui_res_lib.Icon.ui_play,
        )
        evaluate_button.setMinimumHeight(32)
        run_row.addWidget(evaluate_button, 1)
        self.score_label = ui_qt.QtWidgets.QLabel("Score: -")
        self.score_label.setMinimumWidth(170)
        self.score_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        run_row.addWidget(self.score_label)
        layout.addLayout(run_row)
        return group

    def build_results_tab(self):
        """Builds the results tab.

        Returns:
            QWidget: Results tab.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        self.results_tree = ui_qt.QtWidgets.QTreeWidget()
        self.results_tree.setColumnCount(len(RESULT_COLUMNS))
        self.results_tree.setHeaderLabels(RESULT_COLUMNS)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setToolTip(
            "Expand a check to see where it found issues.\n"
            "Double-click a frame span to jump to it, or an offender to select it in Maya."
        )
        header = self.results_tree.header()
        header.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.Stretch)
        for column in range(1, len(RESULT_COLUMNS)):
            header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        install_empty_click_deselect(self.results_tree)
        layout.addWidget(self.results_tree, 1)
        actions = ui_qt.QtWidgets.QHBoxLayout()
        actions.addWidget(self.button("write_score", "Write Score",
                                      "Store the last score as an attribute in the scene, so it is saved\n"
                                      "with the file and can be read by other tools or batch scripts.\n"
                                      "Where it goes is set in the Preferences tab (default: motionEval.motionScore).\n"
                                      "The scene is modified (undoable) but not saved."))
        actions.addWidget(self.button("copy_summary", "Copy Summary", "Copy a text summary to the clipboard."))
        actions.addWidget(self.button("export_report", "Export Report...",
                                      "Save the full report (every check, span, and setting) as JSON."))
        actions.addWidget(self.button("export_graphs", "Export Graphs...",
                                      "Save PNG graphs of what each check measured into a folder you choose:\n"
                                      "a summary image plus one graph per check, with thresholds and flagged frames."))
        layout.addLayout(actions)
        return widget

    def build_preferences_tab(self):
        """Builds the preferences tab (options that rarely change).

        Returns:
            QWidget: Preferences tab content.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.build_score_group())
        layout.addStretch(1)
        return widget

    def build_score_group(self):
        """Builds the score attribute options used by Write Score.

        Returns:
            QGroupBox: Score attribute group.
        """
        group = ui_qt.QtWidgets.QGroupBox("Write Score")
        group.setToolTip("Where the Write Score button (Results tab) stores the score in the scene.")
        grid = ui_qt.QtWidgets.QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        description = ui_qt.QtWidgets.QLabel(
            "Write Score (Results tab) saves the score as an attribute in the scene, so it travels\n"
            "with the file and other tools or batch post-scripts can read it."
        )
        description.setStyleSheet("color: #A0A0A0;")
        description.setWordWrap(True)
        grid.addWidget(description, 0, 0, 1, 2)
        self.target_mode_combo = ui_qt.QtWidgets.QComboBox()
        for target_mode in scene_io.TARGET_MODES:
            self.target_mode_combo.addItem(TARGET_MODE_LABELS[target_mode], target_mode)
        target_tooltip = (
            "Which node receives the attributes:\n"
            "Network Node: a dedicated network node, created when missing.\n"
            "    Safe default, it does not touch the rig or skeleton.\n"
            "Skeleton Role: the joint mapped to a skeleton role, such as hips.\n"
            "    Useful when only the skeleton is exported.\n"
            "Named Node: any existing node, typed below."
        )
        self.target_mode_combo.setToolTip(target_tooltip)
        fit_combo_to_items(self.target_mode_combo)
        self.target_mode_combo.view().setMinimumWidth(self.target_mode_combo.minimumWidth())
        self.target_name_field = ui_qt.QtWidgets.QLineEdit()
        target_name_tooltip = (
            "Depends on Target:\n"
            "Network Node: name of the node to create or reuse (default: motionEval).\n"
            "Skeleton Role: a role key from the Skeleton tab, for example hips.\n"
            "Named Node: the existing node name."
        )
        self.target_name_field.setToolTip(target_name_tooltip)
        self.score_attribute_field = ui_qt.QtWidgets.QLineEdit()
        score_tooltip = (
            "Integer attribute (0-100) that receives the overall score.\n"
            "Created on the target node when missing, and overwritten on every Write Score."
        )
        self.score_attribute_field.setToolTip(score_tooltip)
        report_tooltip = (
            "Store Report: also write a short JSON summary next to the score, on the same node.\n"
            "It holds the overall score, mode, skeleton, and frame range, plus each enabled check's\n"
            "score, status, and flagged frame spans. Use it to see why a file got its score\n"
            "without evaluating again. Turn it off to store only the number.\n"
            "The full report (offenders and settings included) is saved with Export Report... instead."
        )
        self.write_report_checkbox = ui_qt.QtWidgets.QCheckBox()
        self.write_report_checkbox.setToolTip(report_tooltip)
        self.report_attribute_field = ui_qt.QtWidgets.QLineEdit()
        self.report_attribute_field.setToolTip(
            "String attribute that receives the JSON summary (default: motionReport).\n"
            "Created when missing. Enabled when Store Report is on."
        )
        rows = [
            ("Target", self.target_mode_combo, target_tooltip),
            ("Node / Role", self.target_name_field, target_name_tooltip),
            ("Score Attr", self.score_attribute_field, score_tooltip),
            ("Store Report", self.write_report_checkbox, report_tooltip),
            ("Report Attr", self.report_attribute_field, self.report_attribute_field.toolTip()),
        ]
        for row_index, (label_text, field, tooltip) in enumerate(rows, start=1):
            label = ui_qt.QtWidgets.QLabel(label_text)
            label.setToolTip(tooltip)
            label.setMinimumWidth(get_text_width(label, label_text) + 8)
            grid.addWidget(label, row_index, 0)
            grid.addWidget(field, row_index, 1)
        grid.setColumnStretch(1, 1)
        return group

    def build_skeleton_tab(self):
        """Builds the skeleton template editor tab.

        Returns:
            QWidget: Skeleton tab.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        info_row = ui_qt.QtWidgets.QHBoxLayout()
        info_row.addWidget(ui_qt.QtWidgets.QLabel("Name"))
        self.template_name_field = ui_qt.QtWidgets.QLineEdit()
        self.template_name_field.setToolTip("Skeleton display name, shown in reports.")
        info_row.addWidget(self.template_name_field, 1)
        info_row.addWidget(ui_qt.QtWidgets.QLabel("Up Axis"))
        self.up_axis_combo = ui_qt.QtWidgets.QComboBox()
        self.up_axis_combo.addItems(templates.UP_AXIS_VALUES)
        self.up_axis_combo.setToolTip(
            "Up axis of the animation.\n"
            "scene: use the Maya preference. Pick y or z when the data was authored with a different up axis."
        )
        info_row.addWidget(self.up_axis_combo)
        layout.addLayout(info_row)
        self.template_source_label = ui_qt.QtWidgets.QLabel()
        self.template_source_label.setWordWrap(True)
        layout.addWidget(self.template_source_label)
        self.role_table = ui_qt.QtWidgets.QTableWidget(len(templates.ROLE_KEYS), len(ROLE_COLUMNS))
        self.role_table.setHorizontalHeaderLabels(ROLE_COLUMNS)
        self.role_table.verticalHeader().setVisible(False)
        install_empty_click_deselect(self.role_table)
        self.role_table.setSelectionBehavior(ui_qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.role_table.setToolTip(
            "Double-click a Joint Names cell to edit. Several names can be listed; the first match wins.\n"
            "Prefixed names such as 'Character1_Hips' and namespaces are matched automatically."
        )
        header = self.role_table.horizontalHeader()
        header.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Stretch)
        header.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Stretch)
        for row, role_key in enumerate(templates.ROLE_KEYS):
            required = role_key in templates.REQUIRED_BIPED_ROLES
            role_item = ui_qt.QtWidgets.QTableWidgetItem(
                templates.ROLE_LABELS[role_key] + (" *" if required else "")
            )
            role_item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled | ui_qt.QtLib.ItemFlag.ItemIsSelectable)
            required_text = " Required for Biped mode." if required else ""
            role_item.setToolTip(templates.ROLE_DESCRIPTIONS[role_key] + required_text)
            self.role_table.setItem(row, 0, role_item)
            self.role_table.setItem(row, 1, ui_qt.QtWidgets.QTableWidgetItem(""))
            resolved_item = ui_qt.QtWidgets.QTableWidgetItem("")
            resolved_item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled | ui_qt.QtLib.ItemFlag.ItemIsSelectable)
            self.role_table.setItem(row, 2, resolved_item)
        layout.addWidget(self.role_table, 1)
        buttons = ui_qt.QtWidgets.QHBoxLayout()
        buttons.addWidget(self.button("assign_selected", "Assign Selected",
                                      "Select a role row above and a joint in Maya,\n"
                                      "then click to use that joint's name for the role."))
        buttons.addWidget(self.button("check_scene", "Check Scene",
                                      "Find every role's joint in the open scene.\n"
                                      "Missing required roles (*) are shown in red."))
        buttons.addWidget(self.button("save_template", "Save As...",
                                      "Save this skeleton as a Custom Skeleton JSON file\n"
                                      "(load it here or in the Validate Animation batch task)."))
        layout.addLayout(buttons)
        return widget

    # ------------------------------------------------ Updates ------------------------------------------------
    def set_status(self, text, level="info"):
        """Shows a status message.

        Args:
            text (str): Message.
            level (str): info, success, warning, or error.
        """
        colors = {"info": "#DDDDDD", "success": "#94FF9D", "warning": "#FFD166", "error": "#FF8A8A"}
        self.status_label.setStyleSheet(f"color: {colors.get(level, '#DDDDDD')};")
        self.status_label.setText(text)

    def set_score(self, score, status):
        """Shows the overall score.

        Args:
            score (int or None): Overall score.
            status (str): Overall status.
        """
        if score is None:
            self.score_label.setText("Score: -")
            self.score_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            return
        color = STATUS_COLORS.get(status, "#DDDDDD")
        self.score_label.setText(f"Score: {score} ({status})")
        self.score_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")

    def set_report(self, report):
        """Fills the results tree.

        Args:
            report (dict or None): Evaluation report.
        """
        self.results_tree.clear()
        if not report:
            self.set_score(None, "")
            return
        self.set_score(report.get("score"), report.get("status"))
        user_role = ui_qt.QtLib.ItemDataRole.UserRole
        for warning in report.get("warnings") or []:
            item = ui_qt.QtWidgets.QTreeWidgetItem([f"Warning: {warning}", "", "", "", ""])
            item.setForeground(0, ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor(STATUS_COLORS["warning"])))
            self.results_tree.addTopLevelItem(item)
        for entry in report.get("checks") or []:
            status = entry.get("status", "")
            score = "" if entry.get("score") is None else str(entry["score"])
            item = ui_qt.QtWidgets.QTreeWidgetItem(
                [
                    entry.get("label", ""),
                    score,
                    status,
                    str(entry.get("flagged_frames", "")),
                    str(entry.get("events", "")),
                ]
            )
            color = ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor(STATUS_COLORS.get(status, "#DDDDDD")))
            item.setForeground(2, color)
            item.setToolTip(0, entry.get("skip_reason") or "")
            for start, end in entry.get("spans") or []:
                span_item = ui_qt.QtWidgets.QTreeWidgetItem([f"Frames {start}-{end}", "", "", str(end - start + 1), ""])
                span_item.setData(0, user_role, {"frame": start})
                item.addChild(span_item)
            for offender in entry.get("offenders") or []:
                offender_item = ui_qt.QtWidgets.QTreeWidgetItem([f"Offender: {offender['name']}", "", "",
                                                                 str(offender["frames"]), ""])
                offender_item.setData(0, user_role, {"offender": offender["name"]})
                item.addChild(offender_item)
            for detail in entry.get("details") or []:
                item.addChild(ui_qt.QtWidgets.QTreeWidgetItem([detail, "", "", "", ""]))
            if entry.get("skip_reason") and status == checks_base.STATUS_SKIPPED:
                item.addChild(ui_qt.QtWidgets.QTreeWidgetItem([entry["skip_reason"], "", "", "", ""]))
            self.results_tree.addTopLevelItem(item)

    def set_template(self, template, source_label, combo_key):
        """Shows a template in the skeleton tab and the template combo.

        Args:
            template (dict): Template data.
            source_label (str): Readable template source.
            combo_key (str): Built-in key, or "" for the custom entry.
        """
        self.template_combo.blockSignals(True)
        self.template_combo.setCurrentIndex(max(0, self.template_combo.findData(combo_key)))
        self.template_combo.blockSignals(False)
        self.template_name_field.blockSignals(True)
        self.template_name_field.setText(template.get("name", ""))
        self.template_name_field.blockSignals(False)
        self.up_axis_combo.blockSignals(True)
        self.up_axis_combo.setCurrentText(template.get("up_axis", "scene"))
        self.up_axis_combo.blockSignals(False)
        self.template_source_label.setText(f"Source: {source_label}")
        self.role_table.blockSignals(True)
        for row, role_key in enumerate(templates.ROLE_KEYS):
            self.role_table.item(row, 1).setText(", ".join(template.get("roles", {}).get(role_key, [])))
        self.role_table.blockSignals(False)

    def set_resolution(self, resolution):
        """Shows resolved scene nodes per role.

        Args:
            resolution (dict or None): Resolution from the service, or None to clear.
        """
        roles = (resolution or {}).get("roles", {})
        missing_required = set((resolution or {}).get("missing_required", []))
        for row, role_key in enumerate(templates.ROLE_KEYS):
            item = self.role_table.item(row, 2)
            if resolution is None:
                item.setText("")
                continue
            path = roles.get(role_key, "")
            missing_text = "missing (required)" if role_key in missing_required else "-"
            item.setText(path.split("|")[-1] if path else missing_text)
            item.setToolTip(path)
            color = "#94FF9D" if path else ("#FF8A8A" if role_key in missing_required else "#888888")
            item.setForeground(ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor(color)))

    def get_template_from_table(self):
        """Builds a template from the skeleton tab.

        Returns:
            dict: Normalized template.
        """
        roles = {}
        for row, role_key in enumerate(templates.ROLE_KEYS):
            roles[role_key] = self.role_table.item(row, 1).text()
        return templates.create_template(
            name=self.template_name_field.text().strip() or "Custom Skeleton",
            roles=roles,
            up_axis=self.up_axis_combo.currentText(),
        )

    def get_selected_role_row(self):
        """Gets the selected role table row.

        Returns:
            int or None: Row index.
        """
        rows = sorted(set(index.row() for index in self.role_table.selectedIndexes()))
        return rows[0] if rows else None

    def set_role_names(self, row, names):
        """Sets the names of a role row (emits itemChanged).

        Args:
            row (int): Role row.
            names (list): Joint names.
        """
        self.role_table.item(row, 1).setText(", ".join(names))

    def refresh_mode_controls(self, mode, range_mode, uses_skeleton, write_report):
        """Enables only the controls that affect the current settings.

        Args:
            mode (str): Evaluation mode.
            range_mode (str): Frame range mode.
            uses_skeleton (bool): Whether the skeleton is used (Biped mode or Template Joints scope).
            write_report (bool): Whether the report attribute is written.
        """
        is_general = mode == checks_base.MODE_GENERAL
        for widget in (self.scope_label, self.scope_combo):
            widget.setEnabled(is_general)
        self.node_list_field.setEnabled(is_general and self.scope_combo.currentText() == sampling.SCOPE_NODE_LIST)
        for widget in (self.skeleton_label, self.template_combo, self.buttons["load_template"],
                       self.buttons["detect_template"]):
            widget.setEnabled(uses_skeleton)
        is_custom = range_mode == sampling.RANGE_CUSTOM
        self.start_spin.setEnabled(is_custom)
        self.end_spin.setEnabled(is_custom)
        self.report_attribute_field.setEnabled(write_report)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = AnimEvaluatorView()
        window.show()
