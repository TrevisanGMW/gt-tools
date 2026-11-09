"""
Batch Processor Validate Animation Task Widget

The Skeleton row decides what is checked: "None" runs the General checks on any
animated nodes, and picking a skeleton adds the Biped checks on its joints.
"""

from gt.tools.batch_processor.widgets.attr_widget_validation import (
    AttrWidgetValidationTaskBase,
    RUN_ONCE_AFTER_TOOLTIP,
    ROW_COLUMNS,
    LABEL_WIDTH,
)
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.tools.batch_processor.widgets.table_height_handle import TableHeightHandle
from gt.tools.batch_processor.tasks import task_validation_animation as task_module
from gt.tools.anim_evaluator.anim_evaluator_widgets import PresetEditorWidget, DISABLED_STYLESHEET
from gt.core.motion_eval import checks_base
from gt.core.motion_eval import presets
from gt.core.motion_eval import sampling
from gt.core.motion_eval import scene_io
from gt.core.motion_eval import templates
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import traceback
import json

SKELETON_LABELS = dict(
    [(task_module.SKELETON_NONE, "None - General checks only")]
    + [(key, templates.BUILTIN_TEMPLATES[key]["name"]) for key in templates.get_builtin_template_keys()]
    + [(task_module.SKELETON_CUSTOM, "Custom Skeleton")]
)
SKELETON_TOOLTIP = (
    "What is checked depends on the skeleton:\n"
    "None: only the General checks, on any animated nodes (noise, pops, speed, scale, ...).\n"
    "A skeleton: the General checks plus the Biped checks (feet, ground, knees, body),\n"
    "on the joints the skeleton maps. Use Custom Skeleton for rigs with other joint names\n"
    "(create the file in the Animation Evaluator's Skeleton tab)."
)
TARGET_LABELS = {
    scene_io.TARGET_DEDICATED_NODE: "Network Node",
    scene_io.TARGET_ROLE: "Skeleton Role",
    scene_io.TARGET_NAMED_NODE: "Named Node",
}
POLICY_LABELS = {
    scene_io.WRITE_POLICY_OVERWRITE: "Overwrite",
    scene_io.WRITE_POLICY_IF_MISSING: "Only If Missing",
    scene_io.WRITE_POLICY_NEVER: "Never",
}
JSON_FILE_FILTER = "JSON Files (*.json);;All Files (*);;"
FILTER_TOOLTIP = (
    "Optionally evaluate only some of the files, by name.\n"
    "Patterns are comma-separated and case-insensitive, and match the file name or its path.\n"
    "Text without wildcards matches names that contain it (blue_fox = *blue_fox*).\n"
    "Files skipped by the filters are not evaluated and are left out of the outputs."
)
OUTPUT_TOOLTIP = (
    "Folder that receives the outputs below (default: a folder named after this task in the task dir).\n"
    "Whole-batch files go directly in it. Per-file outputs go in <Output Folder>/<file name>/,\n"
    "or directly in the Output Folder when Per-File Folders is off.\n"
    "Path templates such as {project-dir} or {task-dir} are supported.\n"
    "Validation logs are separate (see Log & Fail)."
)


class AttrWidgetAnimationValidationTask(AttrWidgetValidationTaskBase):
    """Attribute widget for the Validate Animation task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskValidationAnimation, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.setStyleSheet(self.styleSheet() + DISABLED_STYLESHEET)
        self.skeleton_path_widget = None
        self.checks_summary_label = None
        self.preset_path_widget = None
        self.preset_editor = None
        self.preset_editor_widget = None
        self.custom_range_widgets = []
        self.scope_widgets = []
        self.node_list_widget = None
        self.score_option_widgets = []
        self.report_attribute_field = None
        self.graph_option_widgets = []
        self.filter_field_widgets = []
        self.add_common_task_settings()
        self.add_preferences_section()
        self.add_filters_section()
        self.add_checks_section()
        self.add_output_section()
        self.add_score_section()
        self.add_post_script_section()
        self.add_actions_section()
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=RUN_ONCE_AFTER_TOOLTIP.format("validation"),
        )
        self.sync_preset_mode()
        self.refresh_visibility()
        self.content_layout.addStretch()

    # ------------------------------------------------ Actions ------------------------------------------------
    def add_actions_section(self):
        """Adds the action buttons inside a collapsible section."""
        section = self.add_collapsible_section(
            label_text="Actions",
            collapsed=bool(self.task.settings.get("actions_collapsed", True)),
            state_setter=partial(self.set_task_setting, key="actions_collapsed"),
            tooltip="Try the task on the open scene, run it alone, or open the Animation Evaluator.",
        )
        self.add_actions_row(
            [
                (
                    "Run On Current Scene",
                    "Evaluate the scene currently open in Maya and show the results.\n"
                    "Nothing is loaded, written, saved, output, or logged.",
                    self.run_on_current_scene,
                    ui_res_lib.Icon.ui_play,
                ),
                (
                    "Run Validation Task",
                    "Run only this Validate Animation task against its configured source files.",
                    self.run_this_task_now,
                    ui_res_lib.Icon.batch_task_validate_animation,
                ),
                (
                    "Evaluator Tool",
                    "Open the Animation Evaluator to create Custom Skeletons and tune checks interactively.",
                    self.open_evaluator_tool,
                    ui_res_lib.Icon.tool_anim_evaluator,
                ),
            ],
            tooltip="Quick actions for this task.",
            parent_layout=section.get("content_layout"),
        )

    # ------------------------------------------------ Preferences ------------------------------------------------
    def add_preferences_section(self):
        """Adds scene, skeleton, range, node scope, and result options."""
        section = self.add_collapsible_section(
            label_text="Animation Validation Preferences",
            collapsed=bool(self.task.settings.get("preferences_collapsed", False)),
            state_setter=partial(self.set_task_setting, key="preferences_collapsed"),
            tooltip="Scene loading, skeleton (what is checked), frame range, nodes, logging, and failure options.",
        )
        layout = section.get("content_layout")
        self.add_scene_row(layout)
        self.add_skeleton_rows(layout)
        self.add_scope_rows(layout)
        self.add_range_row(layout)
        self.add_results_row(
            log_tooltip="Write JSON reports (score and every check) for every file, only files with issues, or never.",
            fail_key="fail_on_failed",
            fail_label="Fail Item on Failed Check",
            fail_tooltip="Mark the file as failed in the tracker when its result is failed:\n"
                         "the overall score is below Fail Below, or a check is below its own\n"
                         "Fail < threshold (unless that check has Allow Fail on).\n"
                         "When off, failed files are still logged and output, but the item succeeds.",
            parent_layout=layout,
        )
        self.add_checkbox_row(
            "Issue Rules",
            [
                ("Report Warnings", "report_warnings",
                 "Report items with a warning result to the tracker as warnings.", True),
                ("Fail On Error", "fail_on_error",
                 "Fail the item when it cannot be evaluated (for example the skeleton's joints are missing).\n"
                 "When off, the item is skipped instead.", True),
            ],
            tooltip="How evaluation results are reported.",
            parent_layout=layout,
        )

    def add_scene_row(self, parent_layout):
        """Adds scene loading options.

        Args:
            parent_layout (QLayout): Layout receiving the row.
        """
        layout = self.add_labeled_layout("Scene Load",
                                         tooltip="How each incoming file is loaded.\n"
                                                 "Maya scenes (.ma, .mb), FBX, and USD files are evaluated;\n"
                                                 "other files in the source folder are ignored.",
                                         parent_layout=parent_layout)
        self.add_option_checkbox(layout, "Load Scene", "load_scene",
                                 "Open or import each incoming file before evaluating.\n"
                                 "Turn off when a previous task already opened the scene.", True)
        self.add_row_combo_cell(layout, self.task.settings.get("source_load_mode") or "Open", ["Open", "Import"],
                                "source_load_mode",
                                tooltip="Open: open the file directly.\nImport: import it into a new empty scene.\n"
                                        "USD files are always imported into a new scene, at the file's frame rate.")
        self.add_option_checkbox(layout, "Load Plugins", "load_relevant_plugins",
                                 "Load known file-format plugins (FBX, USD, ...) before opening or importing.", True)
        self.add_option_checkbox(layout, "Align USD Up", "align_up_axis",
                                 "USD files (.usd, .usda, .usdc) only: rotate (and scale) each file into Maya's\n"
                                 "Y up and scene unit before evaluating, for example USD files exported Z up.\n"
                                 "Keep it on unless the files are already Y up.", True)

    # ------------------------------------------------ Filters ------------------------------------------------
    def add_filters_section(self):
        """Adds the optional Include/Exclude name filters inside a collapsible section."""
        section = self.add_collapsible_section(
            label_text="Filters",
            collapsed=bool(self.task.settings.get("filter_collapsed", True)),
            state_setter=partial(self.set_task_setting, key="filter_collapsed"),
            tooltip=FILTER_TOOLTIP,
        )
        layout = section.get("content_layout")
        row = self.add_labeled_layout("Name Filters", tooltip=FILTER_TOOLTIP, parent_layout=layout)
        checkbox = self.add_option_checkbox(row, "Enable Filters", "filter_enabled",
                                            "Evaluate only the files that pass the Include and Exclude patterns.\n"
                                            "Off: every animation file is evaluated.", False)
        checkbox.stateChanged.connect(lambda *args: self.refresh_visibility())
        self.fill_row_cells(row)
        self.filter_field_widgets = [
            self.add_text_field(
                "Include",
                str(self.task.settings.get("filter_include_patterns") or ""),
                partial(self.set_task_setting, key="filter_include_patterns"),
                placeholder="blue_fox_0*, *_take_01.usd   (empty: every file)",
                tooltip="Evaluate only files whose name matches one of these patterns.\n"
                        "Empty: every file is included (Exclude still applies).\n\n" + FILTER_TOOLTIP,
                label_width=LABEL_WIDTH,
                parent_layout=layout,
            ),
            self.add_text_field(
                "Exclude",
                str(self.task.settings.get("filter_exclude_patterns") or ""),
                partial(self.set_task_setting, key="filter_exclude_patterns"),
                placeholder="*_backup*, */old/*",
                tooltip="Skip files whose name matches one of these patterns (wins over Include).\n\n"
                        + FILTER_TOOLTIP,
                label_width=LABEL_WIDTH,
                parent_layout=layout,
            ),
        ]

    def add_skeleton_rows(self, parent_layout):
        """Adds the skeleton selector, the Custom Skeleton file, and the checks summary.

        Args:
            parent_layout (QLayout): Layout receiving the rows.
        """
        layout = self.add_labeled_layout("Skeleton", tooltip=SKELETON_TOOLTIP, parent_layout=parent_layout)
        cell = self.add_row_cell(layout, span=ROW_COLUMNS)
        combo = ui_qt.QtWidgets.QComboBox()
        for key, label in SKELETON_LABELS.items():
            combo.addItem(label, key)
        combo.setCurrentIndex(max(0, combo.findData(self.task.settings.get("skeleton_source"))))
        combo.setToolTip(SKELETON_TOOLTIP)
        combo.currentIndexChanged.connect(lambda index: self.on_skeleton_source_changed(combo.itemData(index)))
        cell.addWidget(combo, 1)
        self.skeleton_path_widget = ui_qt.QtWidgets.QWidget()
        path_layout = ui_qt.QtWidgets.QVBoxLayout(self.skeleton_path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        self.add_path_template_field(
            "Custom SKM File",
            self.task.settings.get("custom_skeleton_path"),
            partial(self.set_task_setting, key="custom_skeleton_path"),
            placeholder=task_module.DEFAULT_CUSTOM_SKELETON_PATH,
            tooltip="Custom Skeleton JSON file, saved from the Animation Evaluator's Skeleton tab.\n"
                    "Path templates such as {project-dir} are supported.",
            file_filter=JSON_FILE_FILTER,
            parent_layout=path_layout,
        )
        parent_layout.addWidget(self.skeleton_path_widget)
        summary_layout = self.add_labeled_layout(
            "Checks", tooltip="Checks that run with the selected skeleton.\nTune them in Checks and Thresholds.",
            parent_layout=parent_layout,
        )
        self.checks_summary_label = ui_qt.QtWidgets.QLabel()
        self.checks_summary_label.setStyleSheet("color: #9FC9FF;")
        summary_layout.addWidget(self.checks_summary_label, 1)

    def on_skeleton_source_changed(self, value):
        """Stores the skeleton choice and switches the checks between General and Biped.

        Args:
            value (str): "none", a built-in key, or "custom".
        """
        self.set_task_setting(value, key="skeleton_source")
        self.sync_preset_mode()
        self.refresh_visibility()

    def sync_preset_mode(self):
        """Makes the inline preset editor show the checks implied by the skeleton."""
        if self.preset_editor and self.preset_editor.get_mode() != self.task.get_mode():
            self.preset_editor.set_mode(self.task.get_mode(), notify=True)

    def add_range_row(self, parent_layout):
        """Adds the frame range options.

        Args:
            parent_layout (QLayout): Layout receiving the row.
        """
        tooltip = "\n".join(
            ["Frames evaluated in each scene:", ""]
            + [f"{mode}: {text}" for mode, text in sampling.RANGE_TOOLTIPS.items()]
        )
        layout = self.add_labeled_layout("Frame Range", tooltip=tooltip, parent_layout=parent_layout)
        combo = self.add_row_combo_cell(layout, self.task.settings.get("range_mode") or sampling.RANGE_PLAYBACK,
                                        sampling.RANGE_MODES, "range_mode", tooltip=tooltip, span=2)
        for index in range(combo.count()):
            combo.setItemData(index, sampling.RANGE_TOOLTIPS.get(combo.itemText(index), ""),
                              ui_qt.QtLib.ItemDataRole.ToolTipRole)
        combo.currentTextChanged.connect(lambda *args: self.refresh_visibility())
        self.custom_range_widgets = []
        for key, label in (("custom_start", "Start"), ("custom_end", "End")):
            cell = self.add_row_cell(layout)
            spin = ui_qt.QtWidgets.QSpinBox()
            spin.setRange(-1000000, 1000000)
            spin.setValue(int(self.task.settings.get(key) or 0))
            spin.setPrefix(f"{label}: ")
            spin.setToolTip(f"Custom {label.lower()} frame. Enabled when Frame Range is Custom.")
            spin.valueChanged.connect(partial(self.set_task_setting, key=key))
            cell.addWidget(spin, 1)
            self.custom_range_widgets.append(spin)

    def add_scope_rows(self, parent_layout):
        """Adds the node scope used without a skeleton.

        Args:
            parent_layout (QLayout): Layout receiving the rows.
        """
        tooltip = (
            "Nodes evaluated when Skeleton is None.\n"
            "With a skeleton, the joints it maps are evaluated, so this row is disabled."
        )
        layout = self.add_labeled_layout("Nodes", tooltip=tooltip, parent_layout=parent_layout)
        combo = self.add_row_combo_cell(layout, self.task.settings.get("general_scope") or sampling.SCOPE_ALL_JOINTS,
                                        task_module.BATCH_GENERAL_SCOPES, "general_scope", tooltip=tooltip,
                                        span=ROW_COLUMNS)
        for index in range(combo.count()):
            combo.setItemData(index, sampling.SCOPE_TOOLTIPS.get(combo.itemText(index), ""),
                              ui_qt.QtLib.ItemDataRole.ToolTipRole)
        combo.currentTextChanged.connect(lambda *args: self.refresh_visibility())
        self.scope_widgets = [layout.itemAt(0).widget(), combo]
        self.node_list_widget = ui_qt.QtWidgets.QWidget()
        node_layout = ui_qt.QtWidgets.QVBoxLayout(self.node_list_widget)
        node_layout.setContentsMargins(0, 0, 0, 0)
        self.add_text_field(
            "Node List",
            self.task.settings.get("node_list"),
            partial(self.set_task_setting, key="node_list"),
            placeholder="prop_ctrl, *:root",
            tooltip="Comma-separated node names or wildcards for the Node List scope.",
            label_width=100,
            parent_layout=node_layout,
        )
        parent_layout.addWidget(self.node_list_widget)

    # ------------------------------------------------ Checks ------------------------------------------------
    def add_checks_section(self):
        """Adds the preset source and the inline preset editor."""
        section = self.add_collapsible_section(
            label_text="Checks and Thresholds",
            collapsed=bool(self.task.settings.get("checks_collapsed", True)),
            state_setter=partial(self.set_task_setting, key="checks_collapsed"),
            tooltip="Enabled checks, weights, pass/warn/fail thresholds, and detection settings.\n"
                    "The checks listed follow the Skeleton choice (General, or General + Biped).",
        )
        layout = section.get("content_layout")
        tooltip = ("inline: edit the checks here (stored in this project).\n"
                   "file: load a preset JSON shared between projects (saved from this editor or the tool).\n"
                   "Either way, the Skeleton choice decides whether the Biped checks run.")
        row = self.add_labeled_layout("Preset", tooltip=tooltip, parent_layout=layout)
        combo = self.add_row_combo_cell(
            row,
            self.task.settings.get("preset_source") or task_module.PRESET_SOURCE_INLINE,
            task_module.PRESET_SOURCE_VALUES,
            "preset_source",
            tooltip=tooltip,
            span=ROW_COLUMNS,
        )
        combo.currentTextChanged.connect(lambda *args: self.refresh_visibility())
        self.preset_path_widget = ui_qt.QtWidgets.QWidget()
        path_layout = ui_qt.QtWidgets.QVBoxLayout(self.preset_path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        self.add_path_template_field(
            "Preset File",
            self.task.settings.get("preset_path"),
            partial(self.set_task_setting, key="preset_path"),
            placeholder=task_module.DEFAULT_PRESET_PATH,
            tooltip="Evaluation preset JSON (only values changed from the defaults).\n"
                    "Path templates such as {project-dir} are supported.",
            file_filter=JSON_FILE_FILTER,
            parent_layout=path_layout,
        )
        layout.addWidget(self.preset_path_widget)
        self.preset_editor_widget = ui_qt.QtWidgets.QWidget()
        editor_layout = ui_qt.QtWidgets.QVBoxLayout(self.preset_editor_widget)
        editor_layout.setContentsMargins(0, 4, 0, 4)
        self.preset_editor = PresetEditorWidget(
            parent=self.preset_editor_widget,
            preset=self.task.settings.get("preset"),
            changed_callback=partial(self.set_task_setting, key="preset"),
            show_mode=False,
        )
        self.checks_table_height_handle = TableHeightHandle(
            table=self.preset_editor.check_table,
            task=self.task,
            state_key="animation_checks_table_height",
            parent=self.preset_editor,
        )
        preset_layout = self.preset_editor.layout()
        table_index = preset_layout.indexOf(self.preset_editor.check_table)
        preset_layout.insertWidget(table_index + 1, self.checks_table_height_handle)
        self.preset_editor.setMinimumHeight(600)
        editor_layout.addWidget(self.preset_editor)
        layout.addWidget(self.preset_editor_widget)

    # ------------------------------------------------ Output ------------------------------------------------
    def add_output_section(self):
        """Adds the summary, JSON report, and graph outputs."""
        section = self.add_collapsible_section(
            label_text="Output",
            collapsed=bool(self.task.settings.get("output_collapsed", True)),
            state_setter=partial(self.set_task_setting, key="output_collapsed"),
            tooltip=OUTPUT_TOOLTIP,
        )
        layout = section.get("content_layout")
        self.add_path_template_field(
            "Output Folder",
            self.task.settings.get("output_path"),
            partial(self.set_task_setting, key="output_path"),
            placeholder=task_module.DEFAULT_OUTPUT_PATH,
            tooltip=OUTPUT_TOOLTIP,
            dir_only=True,
            parent_layout=layout,
        )
        self.add_checkbox_row(
            "Options",
            [
                ("Per-File Folders", "file_folders",
                 "On: each file's summary, report, and graphs go in <Output Folder>/<file name>/\n"
                 "(source sub-folders are kept).\n"
                 "Off: everything goes directly in the Output Folder. Names still start with the file name.",
                 True),
                ("Delete Temp Parts", "delete_parts",
                 "Whole-batch outputs are rebuilt from one small JSON part per file, kept in a temporary\n"
                 "folder inside this task's log folder while the batch runs.\n"
                 "On: delete that folder when the run finishes. Off: keep it (for debugging).",
                 True),
            ],
            tooltip="How the output files are organized.",
            parent_layout=layout,
        )
        rows = [
            ("Summary", "Readable text summary.", [
                ("Whole Batch", "summary_batch",
                 f"One {task_module.BATCH_SUMMARY_FILE_NAME} for the whole run: totals, the checks that\n"
                 "warned or failed most, then every file sorted by score (lowest first)."),
                ("Per File", "summary_per_file",
                 "<file>_summary.txt in each file's folder: score, every check, and its flagged frames."),
            ]),
            ("JSON Report", "Machine-readable JSON, for scripts or spreadsheets.", [
                ("Whole Batch", "report_batch",
                 f"One {task_module.BATCH_REPORT_FILE_NAME} for the whole run: totals plus each file's\n"
                 "score, status, and per-check results (scores, statuses, flagged frames), sorted by score."),
                ("Per File", "report_per_file",
                 "<file>_report.json in each file's folder: the full report, the same as\n"
                 "Export Report in the Animation Evaluator."),
            ]),
            ("Graphs", "PNG images.", [
                ("Whole Batch", "graphs_batch",
                 f"One {task_module.BATCH_GRAPH_FILE_NAME} for the whole run: a row per file (lowest score\n"
                 "first) with its score bar and a colored cell per check (green passed, yellow warning, red failed)."),
                ("Per File", "graphs_per_file",
                 "In each file's folder: <file>_00_summary.png plus one <file>_NN_<check>.png per check,\n"
                 "showing what was measured, the threshold, and the flagged frames."),
            ]),
        ]
        for label_text, row_tooltip, options in rows:
            row = self.add_labeled_layout(label_text, tooltip=row_tooltip, parent_layout=layout)
            for option_label, key, option_tooltip in options:
                checkbox = self.add_option_checkbox(row, option_label, key, option_tooltip,
                                                    bool(self.task.get_default_settings().get(key)))
                if key == "graphs_per_file":
                    checkbox.stateChanged.connect(lambda *args: self.refresh_visibility())
            if label_text == "Graphs":
                self.graph_option_widgets = [
                    self.add_option_checkbox(
                        row, "Only On Failure", "graphs_only_on_failure",
                        "Per-file graphs only for files whose result is failed.\n"
                        "Turn off to write them for every file. Enabled when Graphs Per File is on.", True,
                    )
                ]
            self.fill_row_cells(row)

    # ------------------------------------------------ Score ------------------------------------------------
    def add_score_section(self):
        """Adds the score attribute and save options."""
        section = self.add_collapsible_section(
            label_text="Score Attribute",
            collapsed=bool(self.task.settings.get("score_collapsed", True)),
            state_setter=partial(self.set_task_setting, key="score_collapsed"),
            tooltip="Store the 0-100 score (and a compact report) as Maya attributes, then optionally save.",
        )
        layout = section.get("content_layout")
        write_row = self.add_labeled_layout("Write", tooltip="Score attribute writing.", parent_layout=layout)
        write_checkbox = self.add_option_checkbox(write_row, "Write Score", "write_score",
                                                  "Store the score on a Maya attribute.", True)
        write_checkbox.stateChanged.connect(lambda *args: self.refresh_visibility())
        report_checkbox = self.add_option_checkbox(
            write_row, "Store Report", "write_report_attribute",
            "Also store a compact JSON report (scores and flagged frames per check) next to the score.", True,
        )
        report_checkbox.stateChanged.connect(lambda *args: self.refresh_visibility())
        self.score_option_widgets = [report_checkbox]
        self.score_option_widgets.append(
            self.add_value_combo_cell(write_row, POLICY_LABELS, "score_write_policy",
                                      "Overwrite: always write the new score.\n"
                                      "Only If Missing: keep a score that is already there.\n"
                                      "Never: do not write (useful to keep the setup but pause writing).", span=2)
        )
        target_row = self.add_labeled_layout("Target", tooltip="Node that stores the score.", parent_layout=layout)
        self.score_option_widgets.append(
            self.add_value_combo_cell(
                target_row, TARGET_LABELS, "score_target_mode",
                "Which node receives the score:\n"
                "Network Node: a dedicated node, created when missing (safe default).\n"
                "Skeleton Role: the joint mapped to a role, such as hips (needs a skeleton).\n"
                "Named Node: any existing node.",
                span=2,
            )
        )
        self.score_option_widgets.append(
            self.add_line_edit_cell(target_row, "score_node_name",
                                    "Network Node: the node name to create or reuse.\n"
                                    "Skeleton Role: a role key, for example hips.\n"
                                    "Named Node: the existing node name.",
                                    scene_io.DEFAULT_NODE_NAME, span=2)
        )
        attribute_row = self.add_labeled_layout("Attributes", tooltip="Attribute names.", parent_layout=layout)
        self.score_option_widgets.append(
            self.add_line_edit_cell(attribute_row, "score_attribute",
                                    "Integer attribute (0-100) for the score. Created when missing.",
                                    scene_io.DEFAULT_SCORE_ATTRIBUTE, span=2)
        )
        self.report_attribute_field = self.add_line_edit_cell(
            attribute_row, "report_attribute",
            "String attribute for the compact JSON report. Enabled when Store Report is on.",
            scene_io.DEFAULT_REPORT_ATTRIBUTE, span=2,
        )
        self.score_option_widgets.append(self.report_attribute_field)
        self.add_checkbox_row(
            "Save",
            [
                ("Save Scene", "save_scene",
                 "Save the scene in place after writing the score or running the post-script.\n"
                 "Use after a Save Maya File task so a copy is modified, not the original input.", False),
                ("Allow Source Overwrite", "allow_source_overwrite",
                 "Allow saving over the original input file.\nOff by default for data safety.", False),
            ],
            tooltip="Saving options. A later Save Maya File task reopens the file,\n"
                    "so save here to keep the score.",
            parent_layout=layout,
        )

    def add_value_combo_cell(self, layout, labels, key, tooltip, span=1):
        """Adds a combo cell that stores the item data instead of the label.

        Args:
            layout (QHBoxLayout): Row layout.
            labels (dict): Value to label mapping.
            key (str): Task setting key.
            tooltip (str): Tooltip.
            span (int): Grid columns.

        Returns:
            QComboBox: Created combo box.
        """
        cell = self.add_row_cell(layout, span=span)
        combo = ui_qt.QtWidgets.QComboBox()
        for value, label in labels.items():
            combo.addItem(label, value)
        combo.setCurrentIndex(max(0, combo.findData(self.task.settings.get(key))))
        combo.setToolTip(tooltip)
        combo.currentIndexChanged.connect(lambda index: self.set_task_setting(combo.itemData(index), key=key))
        cell.addWidget(combo, 1)
        return combo

    def add_line_edit_cell(self, layout, key, tooltip, placeholder, span=1):
        """Adds a line edit cell bound to a task setting.

        Args:
            layout (QHBoxLayout): Row layout.
            key (str): Task setting key.
            tooltip (str): Tooltip.
            placeholder (str): Placeholder text.
            span (int): Grid columns.

        Returns:
            QLineEdit: Created field.
        """
        cell = self.add_row_cell(layout, span=span)
        field = ui_qt.QtWidgets.QLineEdit(str(self.task.settings.get(key) or ""))
        field.setPlaceholderText(placeholder)
        field.setToolTip(tooltip)
        field.editingFinished.connect(lambda: self.set_task_setting(field.text().strip(), key=key))
        cell.addWidget(field, 1)
        return field

    # ------------------------------------------------ Post Script ------------------------------------------------
    def add_post_script_section(self):
        """Adds the collapsed optional post-script section."""
        section = self.add_collapsible_section(
            label_text="Post Script",
            collapsed=bool(self.task.settings.get("post_script_collapsed", True)),
            state_setter=partial(self.set_task_setting, key="post_script_collapsed"),
            tooltip="Optional Python script that runs after scoring (and after the score attribute is written).",
        )
        layout = section.get("content_layout")
        row = ui_qt.QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip, default in (
            ("Run", "run_post_script", "Run the post-script for every evaluated file.", False),
            ("Pass Task Args", "post_script_pass_standard_arguments",
             "Expose input, output, project, task, and related values as arguments and args.", True),
            ("Pass Env", "post_script_pass_environment_arguments",
             "Expose project environment variables as environment_variables and env.", True),
        ):
            self.add_checkbox(label_text, self.task.settings.get(key, default), partial(self.set_task_setting, key=key),
                              layout=row, tooltip=tooltip)
        row.addStretch()
        layout.addLayout(row)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=self.task.settings.get("post_script_text") or "",
            placeholder="Optional post-script. Use evaluation, score, and status, or choose an example.",
            tooltip=(
                "Inline Python executed after each evaluation, before the optional save.\n"
                "Globals: evaluation (full report), score, status, score_write, context, arguments/args,\n"
                "environment_variables/env, project, task, work_item, output_path/log_dir."
            ),
            text_changed_callback=partial(self.set_task_setting, key="post_script_text"),
            font_size=self.task.settings.get("post_script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="post_script_font_size"),
            sample_scripts_directory=self.task.post_script_samples_directory,
        )
        layout.addWidget(editor)

    # ------------------------------------------------ State ------------------------------------------------
    def refresh_visibility(self):
        """Shows or enables only the controls that affect the current settings."""
        settings = self.task.settings
        mode = self.task.get_mode()
        if self.skeleton_path_widget:
            self.skeleton_path_widget.setVisible(settings.get("skeleton_source") == task_module.SKELETON_CUSTOM)
        if self.checks_summary_label:
            if mode == checks_base.MODE_GENERAL:
                text = f"General: {presets.get_mode_check_summary(mode)} on the selected nodes"
            else:
                text = f"General + Biped: {presets.get_mode_check_summary(mode)} on the skeleton joints"
            self.checks_summary_label.setText(text)
        is_custom = settings.get("range_mode") == sampling.RANGE_CUSTOM
        for widget in self.custom_range_widgets:
            widget.setEnabled(is_custom)
        is_file_preset = settings.get("preset_source") == task_module.PRESET_SOURCE_FILE
        if self.preset_path_widget:
            self.preset_path_widget.setVisible(is_file_preset)
        if self.preset_editor_widget:
            self.preset_editor_widget.setVisible(not is_file_preset)
        is_general = mode == checks_base.MODE_GENERAL
        for widget in self.scope_widgets:
            widget.setEnabled(is_general)
        if self.node_list_widget:
            self.node_list_widget.setVisible(settings.get("general_scope") == sampling.SCOPE_NODE_LIST)
            self.node_list_widget.setEnabled(is_general)
        write_score = bool(settings.get("write_score", True))
        for widget in self.score_option_widgets:
            widget.setEnabled(write_score)
        if self.report_attribute_field:
            self.report_attribute_field.setEnabled(write_score and bool(settings.get("write_report_attribute", True)))
        filter_enabled = bool(settings.get("filter_enabled", False))
        for widget in self.filter_field_widgets:
            widget.setEnabled(filter_enabled)
        graphs_per_file = bool(settings.get("graphs_per_file", False))
        for widget in self.graph_option_widgets:
            widget.setEnabled(graphs_per_file)

    # ------------------------------------------------ Actions ------------------------------------------------
    def run_on_current_scene(self):
        """Evaluates the open scene and shows the results."""
        settings_result = self.task.validate(self.project)
        if settings_result.errors:
            self.emit_status_message(settings_result.errors[0], status="warning")
            return
        try:
            report = self.task.run_on_current_scene(self.project)
        except Exception as exception:
            traceback.print_exc()
            self.emit_status_message(f"Unable to evaluate the current scene: {exception}", status="warning")
            return
        from gt.core.motion_eval import evaluation

        self.task.print_report_summary("current scene", report)
        lines = [f"Task: {self.task.display_name}", ""] + evaluation.summarize_report(report)
        lines.extend(["", "Report:", json.dumps(report, indent=4, sort_keys=True)])
        self.show_results_window("Validate Animation Results", lines)
        status = "info" if report.get("status") == checks_base.STATUS_PASSED else "warning"
        self.emit_status_message(f"Validate Animation [{report.get('status')}]: score {report.get('score')}/100",
                                 status=status)

    def open_evaluator_tool(self):
        """Opens the Animation Evaluator tool."""
        try:
            import gt.tools.anim_evaluator as anim_evaluator

            anim_evaluator.launch_tool()
        except Exception as exception:
            traceback.print_exc()
            self.emit_status_message(f"Unable to open the Animation Evaluator: {exception}", status="warning")
