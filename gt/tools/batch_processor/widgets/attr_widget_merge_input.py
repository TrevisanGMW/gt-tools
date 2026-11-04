"""
Batch Processor Merge Input Task Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_maya_import import MayaSceneOptionControlsMixin
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.tools.batch_processor.tasks import task_merge_input_utils as merge_utils
import gt.ui.qt_import as ui_qt
from functools import partial


NAME_TOKEN_TOOLTIP = (
    f"Supports {merge_utils.INPUT_NAME_TOKEN}, {merge_utils.INPUT_INDEX_TOKEN}, "
    f"{merge_utils.INPUT_INDEX_PADDED_TOKEN}, and project variables."
)


class AttrWidgetMergeInputTask(MayaSceneOptionControlsMixin, AttrWidgetTask):
    """Attribute widget for the Merge Input task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Merge Input task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskMergeInput, optional): Merge Input task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.reference_deferred_checkbox = None
        self.remove_namespace_checkbox = None
        self.manual_range_widgets = []
        self.sequential_gap_spin_box = None
        self.offset_spin_boxes = []
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings(collapsible=False, passthrough_label="Keep Open")
        self.add_merge_controls()
        self.add_scene_option_controls(include_clear_scene=False, apply_moment="before merging inputs")
        self.add_organization_controls()
        self.add_time_controls()
        self.add_script_section(
            prefix="input_script",
            label_text="Per-Input Script",
            tooltip="Optional Python script that runs after each input is merged.",
            editor_tooltip=(
                "Runs after each input is merged.\nUse context, args, env, input_path, input_index, total_inputs, "
                "namespace, load_mode, reference_node, merged_nodes, root_nodes, input_group, merge_group, "
                "input_record, and merged_records."
            ),
            samples_directory=self.task.input_script_samples_directory,
        )
        self.add_script_section(
            prefix="post_script",
            label_text="Post-Merge Script",
            tooltip="Optional Python script that runs once after every input is merged, before saving.",
            editor_tooltip=(
                "Runs once after every input is merged and the time range is set, before saving.\nUse context, "
                "args, env, output_path, merged_records, merged_inputs, failed_inputs, merge_group, and time_range."
            ),
            samples_directory=self.task.post_script_samples_directory,
        )
        self.segmentation_section = self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, merge once after all worker jobs finish.\nKeep this on so every input "
                "lands in one scene. Place this task last and point Source Path at the files to merge."
            ),
            include_input_directory_validation=True,
        )
        self.refresh_dependent_controls()
        self.content_layout.addStretch()

    # ------------------------------------------------------------------ merge
    def add_merge_controls(self):
        """Adds output, load mode, namespace, ordering, and failure controls."""
        self.add_widget_separator_line(label_text="Merge Preferences")
        self.add_text_field(
            "Output Name",
            self.task.settings.get("output_name"),
            partial(self.set_task_setting, key="output_name"),
            placeholder="{project-sanitized-name}_merged",
            tooltip="Merged scene file name without extension. Supports project variables.",
            label_width=110,
        )
        self.add_combo_box(
            "Output Ext",
            self.task.settings.get("output_extension"),
            [".ma", ".mb"],
            partial(self.set_task_setting, key="output_extension"),
            tooltip="Maya file type used for the merged scene.",
        )
        load_layout = self.add_labeled_layout(
            "Load Mode",
            tooltip="Import copies every node into the merged scene.\nReference links each input file instead.",
        )
        load_combo = self.create_row_combo_box(
            value=self.task.settings.get("load_mode"),
            values=merge_utils.LOAD_MODES,
            tooltip="Import copies every node into the merged scene.\nReference links each input file instead.",
        )
        load_combo.currentTextChanged.connect(partial(self.set_setting_and_refresh, key="load_mode"))
        load_layout.addWidget(load_combo)
        self.reference_deferred_checkbox = self.add_checkbox(
            "Unloaded",
            self.task.settings.get("reference_deferred"),
            partial(self.set_task_setting, key="reference_deferred"),
            layout=load_layout,
            tooltip=(
                "Create references unloaded (deferred). Faster to save, but nothing is visible until loaded.\n"
                "References point to the incoming file path, so avoid temporary task folders that get deleted."
            ),
        )
        load_layout.addStretch()
        namespace_layout = self.add_labeled_layout(
            "Namespace", tooltip=f"Namespace for each input. {NAME_TOKEN_TOOLTIP}"
        )
        namespace_field = self.create_text_field(
            text=self.task.settings.get("namespace"),
            placeholder="Leave empty to merge into the root namespace (import only).",
            tooltip=(
                f"Namespace for each input. {NAME_TOKEN_TOOLTIP}\nDuplicate namespaces get a number suffix. "
                "References always need a namespace."
            ),
        )
        namespace_field.textChanged.connect(partial(self.set_task_setting, key="namespace"))
        namespace_layout.addWidget(namespace_field)
        self.remove_namespace_checkbox = self.add_checkbox(
            "Remove",
            self.task.settings.get("remove_namespace"),
            partial(self.set_setting_and_refresh, key="remove_namespace"),
            layout=namespace_layout,
            tooltip=(
                "Merge each input's namespace into the root after loading.\nMaya renames clashing nodes. "
                "Ignored in Reference mode."
            ),
        )
        options_layout = self.add_labeled_layout("Inputs", tooltip="Input ordering and error handling.")
        self.add_checkbox(
            "Sort By Path",
            self.task.settings.get("sort_inputs_by_name", False),
            partial(self.set_task_setting, key="sort_inputs_by_name"),
            layout=options_layout,
            tooltip="Merge inputs in path order. Off keeps the incoming order.",
        )
        self.add_row_label(options_layout, "On Error", tooltip="What to do when one input fails to load.")
        failure_combo = self.create_row_combo_box(
            value=self.task.settings.get("on_input_failure"),
            values=merge_utils.FAILURE_POLICIES,
            tooltip="Skip Input logs the error and keeps merging. Fail Merge stops the task.",
        )
        failure_combo.currentTextChanged.connect(partial(self.set_task_setting, key="on_input_failure"))
        options_layout.addWidget(failure_combo)
        self.add_row_label(options_layout, "Warn Above", tooltip="Warn when merging more inputs than this. 0 disables.")
        warning_spin_box = ui_qt.QtWidgets.QSpinBox()
        warning_spin_box.setRange(0, 100000)
        warning_spin_box.setValue(self.task.get_input_count_warning())
        warning_spin_box.setMinimumHeight(35)
        warning_spin_box.setToolTip("Warn when merging more inputs than this. 0 disables.")
        warning_spin_box.valueChanged.connect(partial(self.set_task_setting, key="input_count_warning"))
        options_layout.addWidget(warning_spin_box)
        options_layout.addStretch()
        self.add_path_template_field(
            "Base Scene",
            self.task.settings.get("base_scene_path"),
            partial(self.set_task_setting, key="base_scene_path"),
            placeholder="Leave empty to start from a new empty scene.",
            tooltip="Optional Maya scene opened before merging, e.g. lights, ground, or a review camera.",
            file_filter="Maya Scenes (*.ma *.mb);;All Files (*);;",
        )

    # ------------------------------------------------------------------ organization
    def add_organization_controls(self):
        """Adds grouping, display layer, and spatial offset controls."""
        self.add_widget_separator_line(label_text="Organization")
        self.add_named_toggle_row(
            label_text="Group Each",
            toggle_key="group_each_input",
            name_key="input_group_name",
            tooltip=f"Group each input's top-level nodes. {NAME_TOKEN_TOOLTIP}",
        )
        self.add_named_toggle_row(
            label_text="Group All",
            toggle_key="group_all_inputs",
            name_key="merge_group_name",
            tooltip="Parent everything merged (or each input group) under one group.",
        )
        self.add_named_toggle_row(
            label_text="Display Layer",
            toggle_key="display_layer_per_input",
            name_key="display_layer_name",
            tooltip=f"Create one display layer per input. {NAME_TOKEN_TOOLTIP}",
        )
        offset_tooltip = (
            "Move each input by this step so inputs do not overlap (input 1 stays in place, input 2 moves one "
            "step, and so on).\nEach input gets its own group when this is on."
        )
        offset_layout = self.add_labeled_layout("Offset Each", tooltip=offset_tooltip)
        self.add_checkbox(
            "Use",
            self.task.settings.get("offset_inputs"),
            partial(self.set_setting_and_refresh, key="offset_inputs"),
            layout=offset_layout,
            tooltip=offset_tooltip,
        )
        offset_values = self.task.get_input_offset()
        for axis_index, axis_name in enumerate(["X", "Y", "Z"]):
            self.add_row_label(offset_layout, axis_name, tooltip=f"{axis_name} offset step.")
            spin_box = self.create_double_spin_box(offset_values[axis_index], f"{axis_name} offset step.")
            spin_box.valueChanged.connect(partial(self.set_input_offset_axis, axis_index=axis_index))
            offset_layout.addWidget(spin_box)
            self.offset_spin_boxes.append(spin_box)
        offset_layout.addStretch()

    def add_named_toggle_row(self, label_text, toggle_key, name_key, tooltip):
        """Adds a row with an enable checkbox followed by a name field.

        Args:
            label_text (str): Row label.
            toggle_key (str): Setting toggled by the checkbox.
            name_key (str): Setting edited by the name field.
            tooltip (str): Row tooltip.

        Returns:
            QLineEdit: Name field.
        """
        layout = self.add_labeled_layout(label_text, tooltip=tooltip)
        self.add_checkbox(
            "Use",
            self.task.settings.get(toggle_key),
            partial(self.set_task_setting, key=toggle_key),
            layout=layout,
            tooltip=tooltip,
        )
        name_field = self.create_text_field(
            text=self.task.settings.get(name_key),
            placeholder=self.task.get_default_settings().get(name_key, ""),
            tooltip=tooltip,
        )
        name_field.textChanged.connect(partial(self.set_task_setting, key=name_key))
        layout.addWidget(name_field)
        return name_field

    # ------------------------------------------------------------------ time
    def add_time_controls(self):
        """Adds time range and clip timing controls."""
        self.add_widget_separator_line(label_text="Time")
        range_tooltip = (
            "Keyframes: covers every key in the merged scene, measured once after merging.\n"
            "First Input: uses the range saved in the first input (or its keys when it has none saved).\n"
            "Manual: uses the start and end below.\nKeep Scene Range: leaves the range unchanged."
        )
        range_layout = self.add_labeled_layout("Time Range", tooltip=range_tooltip)
        range_combo = self.create_row_combo_box(
            value=self.task.settings.get("time_range_mode"),
            values=merge_utils.TIME_RANGE_MODES,
            tooltip=range_tooltip,
        )
        range_combo.currentTextChanged.connect(partial(self.set_setting_and_refresh, key="time_range_mode"))
        range_layout.addWidget(range_combo)
        for label_text, setting_key in [("Start", "manual_start_frame"), ("End", "manual_end_frame")]:
            label = self.add_row_label(range_layout, label_text, tooltip=f"Manual {label_text.lower()} frame.")
            spin_box = self.create_double_spin_box(
                self.task.settings.get(setting_key), f"Manual {label_text.lower()} frame."
            )
            spin_box.valueChanged.connect(partial(self.set_task_setting, key=setting_key))
            range_layout.addWidget(spin_box)
            self.manual_range_widgets.extend([widget for widget in [label, spin_box] if widget])
        range_layout.addStretch()
        timing_tooltip = (
            "Original Time keeps every input at its own frames.\n"
            "Sequential shifts each imported input to start after the previous one (Import mode only)."
        )
        timing_layout = self.add_labeled_layout("Timing", tooltip=timing_tooltip)
        timing_combo = self.create_row_combo_box(
            value=self.task.settings.get("timing_mode"),
            values=merge_utils.TIMING_MODES,
            tooltip=timing_tooltip,
        )
        timing_combo.currentTextChanged.connect(partial(self.set_setting_and_refresh, key="timing_mode"))
        timing_layout.addWidget(timing_combo)
        self.add_row_label(timing_layout, "Gap", tooltip="Frames between sequential inputs.")
        self.sequential_gap_spin_box = self.create_double_spin_box(
            self.task.settings.get("sequential_gap_frames"), "Frames between sequential inputs.", minimum=0
        )
        self.sequential_gap_spin_box.valueChanged.connect(partial(self.set_task_setting, key="sequential_gap_frames"))
        timing_layout.addWidget(self.sequential_gap_spin_box)
        timing_layout.addStretch()

    # ------------------------------------------------------------------ scripts
    def add_script_section(self, prefix, label_text, tooltip, editor_tooltip, samples_directory):
        """Adds a collapsible inline script section.

        Args:
            prefix (str): Setting prefix, e.g. "input_script" or "post_script".
            label_text (str): Section label.
            tooltip (str): Section tooltip.
            editor_tooltip (str): Editor tooltip listing the available script values.
            samples_directory (str): Sample script folder relative to the task scripts folder.
        """
        section = self.add_collapsible_section(
            label_text=label_text,
            collapsed=bool(self.task.settings.get(f"{prefix}_collapsed", True)),
            state_setter=partial(self.set_task_setting, key=f"{prefix}_collapsed"),
            tooltip=tooltip,
        )
        layout = section.get("content_layout")
        options_layout = ui_qt.QtWidgets.QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 5)
        option_rows = [
            ("Run", f"run_{prefix}", False, tooltip),
            (
                "Pass Task Args",
                f"{prefix}_pass_standard_arguments",
                True,
                "Expose input, output, project, task, and related values as arguments and args.",
            ),
            (
                "Pass Env",
                f"{prefix}_pass_environment_arguments",
                True,
                "Expose project environment variables as environment_variables and env.",
            ),
        ]
        for option_label, setting_key, default_value, option_tooltip in option_rows:
            self.add_checkbox(
                option_label,
                self.task.settings.get(setting_key, default_value),
                partial(self.set_task_setting, key=setting_key),
                layout=options_layout,
                tooltip=option_tooltip,
            )
        options_layout.addStretch()
        layout.addLayout(options_layout)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=self.task.settings.get(f"{prefix}_text") or "",
            placeholder="Write an optional Python script here, or choose an example.",
            tooltip=editor_tooltip,
            text_changed_callback=partial(self.set_task_setting, key=f"{prefix}_text"),
            font_size=self.task.settings.get(f"{prefix}_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key=f"{prefix}_font_size"),
            sample_scripts_directory=samples_directory,
        )
        layout.addWidget(editor)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def create_double_spin_box(value, tooltip, minimum=-1000000.0, maximum=1000000.0):
        """Creates a compact floating-point spin box.

        Args:
            value (float): Initial value.
            tooltip (str): Tooltip text.
            minimum (float, optional): Minimum value.
            maximum (float, optional): Maximum value.

        Returns:
            QDoubleSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QDoubleSpinBox()
        spin_box.setRange(float(minimum), float(maximum))
        spin_box.setDecimals(2)
        try:
            spin_box.setValue(float(value or 0))
        except (TypeError, ValueError):
            spin_box.setValue(0.0)
        spin_box.setMinimumHeight(35)
        spin_box.setMinimumWidth(80)
        spin_box.setToolTip(tooltip)
        return spin_box

    def set_input_offset_axis(self, value, axis_index):
        """Stores one axis of the per-input offset step.

        Args:
            value (float): New axis value.
            axis_index (int): Axis index (0 = X, 1 = Y, 2 = Z).
        """
        offset_values = self.task.get_input_offset()
        offset_values[axis_index] = float(value)
        self.set_task_setting(offset_values, key="input_offset")

    def set_setting_and_refresh(self, value, key):
        """Stores a setting and refreshes controls that depend on it.

        Args:
            value (object): New setting value.
            key (str): Setting key.
        """
        self.set_task_setting(value, key=key)
        self.refresh_dependent_controls()

    def refresh_dependent_controls(self):
        """Enables or disables controls based on the current settings."""
        is_reference = self.task.uses_reference_mode()
        if self.reference_deferred_checkbox:
            self.reference_deferred_checkbox.setEnabled(is_reference)
        if self.remove_namespace_checkbox:
            self.remove_namespace_checkbox.setEnabled(not is_reference)
        is_manual = self.task.settings.get("time_range_mode") == merge_utils.TIME_RANGE_MANUAL
        for widget in self.manual_range_widgets:
            widget.setEnabled(is_manual)
        if self.sequential_gap_spin_box:
            is_sequential = self.task.settings.get("timing_mode") == merge_utils.TIMING_SEQUENTIAL
            self.sequential_gap_spin_box.setEnabled(is_sequential and not is_reference)
        for spin_box in self.offset_spin_boxes:
            spin_box.setEnabled(bool(self.task.settings.get("offset_inputs")))
        if is_reference and self.task.settings.get("remove_namespace"):
            self.emit_status_message("Remove Namespace is ignored in Reference mode.", status="warning")
