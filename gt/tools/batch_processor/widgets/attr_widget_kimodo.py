"""Compact task panels for Kimodo capture and generation automation."""

import json
import math
import os
from functools import partial
from gt.ui import qt_import as qt
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks.task_kimodo_base import MOTION_TEXT_EXAMPLE


FIELD_HELP = {
    ("prompt_mode",): ("Choose the motion description source.\n"
                       "Table is the default.\n"
                       "Text replaces all prompt segments, including those from a setup,\n"
                       "while retaining the table for later use.", ""),
    ("prompt_text",): ("Enter one JSON list of [seconds, description] pairs.\n"
                       "Use {input-string} for a complete sequence,\n"
                       "or placeholders inside quoted descriptions.\n"
                       "Supports project variables, OS environment variables, {input-file},\n"
                       "{input-file-name}, {input-file-stem}, and {input-file-path}.\n"
                       "Custom query variables are resolved after the incoming scene opens.\n"
                       "Each duration must be positive and at most 30 seconds;\n"
                       "up to 16 segments / 120 seconds.",
                        MOTION_TEXT_EXAMPLE),
    ("use_input_string",): ("Replace the first prompt with the current Input Strings or Input Pairs text.\n"
                            "Inputs without scene files use prompt durations\n"
                            "and skip Maya pose/path capture.", ""),
    ("pose_source",): ("Kimodo placement group or descendant to capture.\n"
                       "Blank auto-detects one skeleton;\n"
                       "if none is found, pose constraints are skipped with a warning.\n"
                       "Multiple matches are an error.",
                       "Auto-detect, or kimodo_pose:motion"),
    ("range_mode",): ("Use the source's saved playback range, full animation range,\n"
                      "or the custom start/end below.\n"
                      "Source scene frames are converted to zero-based model indices.", "Playback range"),
    ("start_frame",): ("Inclusive source start frame, used only with Custom range.\n"
                       "Negative and fractional Maya frames are supported.", "296"),
    ("end_frame",): ("Inclusive source end frame, used only with Custom range.\n"
                     "Must be after Start.", "648"),
    ("capture_first",): ("Add the selected range's first frame to the pose constraints,\n"
                         "even without a marker.", ""),
    ("capture_last",): ("Add the selected range's last frame to the pose constraints,\n"
                        "even without a marker.", ""),
    ("pose_frames",): ("Additional source scene frames.\n"
                       "Accepts comma-separated values and inclusive start:end:step ranges.\n"
                       "Combined with endpoints and markers; duplicates are removed.",
                       "296, 423, 648 or 296:648:30"),
    ("pose_type",): ("Capture the full body, only the hips, or only the selected hand/foot.\n"
                     "Full-body constraints preserve root position and major joint rotations\n"
                     "at each captured frame; post-processing snaps the whole body to them.\n"
                     "Hips constrain only the pelvis position (including height), rotation and\n"
                     "facing, leaving the rest of the body free, so the pose is not snapped.",
                     "Full body"),
    ("use_marker",): ("Evaluate the specified attribute to select additional poses.\n"
                      "Disable when source scenes do not contain this attribute;\n"
                      "a missing requested attribute is an error.", ""),
    ("marker_attribute",): ("Full Maya node.attribute path that marks poses.\n"
                            "May be keyed, connected, or expression-driven\n"
                            "when using an evaluated marker mode.", "kimodo_pose:motion.isConstraintPose"),
    ("marker_value",): ("Capture when the scalar attribute equals this value\n"
                        "within a small numeric tolerance.\n"
                        "Use 1 for a boolean marker.", "1"),
    ("marker_mode",): ("Every active sample captures held values at each sample;\n"
                       "Active keyed frames reads keys directly on the attribute;\n"
                       "Start of active interval captures only the first active sample.",
                        ""),
    ("sample_step",): ("Source-frame spacing for evaluated marker scans.\n"
                       "Use 1 to inspect every frame.\n"
                       "Does not change explicitly entered pose frames or the model FPS.", "1"),
    ("path_nodes",): ("One NURBS curve, one animated transform,\n"
                      "or a comma-separated list of ordered locators.\n"
                      "An animated transform (for example a keyed or motion-path locator)\n"
                      "is sampled over time, so held keys become stops and key spacing sets speed.\n"
                      "With multiple locators, blank Path frames automatically spaces\n"
                      "one point per locator.\n"
                      "To choose among curves, enable Random curve per variation.",
                      "curve_path, trajectory_driver, or start, mid, end"),
    ("root_heading",): ("Facing direction sent with the root path.\n"
                        "None leaves facing to the model.\n"
                        "Direction of travel faces along the path (curve tangent or movement).\n"
                        "Node +Z axis uses each path transform's world +Z axis, ideal for an animated\n"
                        "driver whose rotation is keyed.\n"
                        "Fixed uses only the offset as an absolute heading.", ""),
    ("root_heading_offset",): ("Degrees added to the resolved heading;\n"
                               "the absolute heading when Root heading is Fixed.\n"
                               "0 faces +Z.\n"
                               "Use 180 for backward travel, or 90 / -90 to strafe.", "0"),
    ("path_frames",): ("Optional source frames for the root path.\n"
                       "Blank automatically spaces points across the capture range: one per locator,\n"
                       "or Path samples along a curve.\n"
                       "Explicit locator paths need one frame per locator.", "296, 423, 648"),
    ("path_samples",): ("Number of evenly spaced samples for a curve or animated transform\n"
                        "when Path frames is blank.\n"
                        "Locator lists automatically use one sample per locator.\n"
                        "Allowed range: 2–7200.", "8"),
    ("randomize_root_path",): ("Use only a list of two or more NURBS curve transforms.\n"
                               "One curve is selected per definition variation.\n"
                               "The curve list is shuffled from the first resolved seed\n"
                               "and cycles before repeating;\n"
                               "saved definitions retain their selected paths.", ""),
    ("template_path",): ("Optional Generator setup or portable definition JSON.\n"
                         "Replaces the local model, prompts, and generation settings below.\n"
                         "Project path variables are supported.",
                          "Optional: {project-dir}/kimodo/setup.json"),
    ("definition", "model"): ("Model ID reported by Bridge capabilities.\n"
                              "The task validates model availability before submission.", "kimodo-soma-rp-v1.1"),
    ("definition", "prompts"): ("Each table row is an ordered motion segment with a description and duration.\n"
                                "Use Add Segment, double-click cells to edit,\n"
                                "and move rows to set the action sequence.",
                                 "A person walks to a chair and sits down."),
    ("definition", "parameters", "num_samples"): ("Independent animations generated per definition, from 1 to 8.\n"
                                                  "Each receives its own output file.", "1"),
    ("definition", "parameters", "diffusion_steps"): ("Denoising iterations, from 1 to 1000.\n"
                                                      "The default is 100.\n"
                                                      "Very low counts are useful for smoke tests but may reduce "
                                                      "quality.", "100"),
    ("definition", "parameters", "postprocess"): ("Apply Kimodo's foot-contact cleanup.\n"
                                                  "This does not constrain the character\n"
                                                  "to the source trajectory or scene furniture.", ""),
    ("definition", "parameters", "heading"): ("Initial facing direction in radians.\n"
                                              "Zero uses the model's default heading;\n"
                                              "pose/path constraints may determine orientation.", "0"),
    ("definition", "parameters", "transition_frames"): ("Blend length between multiple prompt segments.\n"
                                                        "Each segment must be longer than this value.", "5"),
    ("definition", "parameters", "guidance"): ("Text controls prompt guidance; Pose controls constraint guidance.\n"
                                               "Both default to 2.\n"
                                               "Higher values change adherence and motion quality.",
                                                  "2"),
    ("model_fps",): ("Sample rate used to map source times into definition indices.\n"
                     "SOMA uses 30 fps.\n"
                     "Generation checks the rate against model metadata and output.", "30"),
    ("duration_mode",): ("Match source timing preserves elapsed time.\n"
                         "Use prompt durations changes total length and requires Retime constraints\n"
                         "when it differs from the source.", ""),
    ("retime_constraints",): ("Scale constraint times to the requested duration.\n"
                              "Required for duration variations or retained template constraints\n"
                              "whose clip length changes.", ""),
    ("constraint_mode",): ("Replace removes template constraints before capture.\n"
                           "Keep and append retains them and validates the combined constraints.", ""),
    ("variations",): ("Resolved definition files per source scene, from 1 to 1000.\n"
                      "This differs from Samples,\n"
                      "which generates multiple animations from a single definition.", "1"),
    ("seed_policy",): ("Fixed reuses Base seed;\n"
                       "Repeatable derives a stable seed from source identity and variation;\n"
                       "Random chooses a new seed for each definition.\n"
                       "Resolved seeds are saved in the JSON definition.\n"
                       "Add _seed_{seed} to Filename suffix to show a seed in output names.", ""),
    ("base_seed",): ("Unsigned integer from 0 to 4294967295\n"
                     "used for fixed or repeatable generation.\n"
                     "Changing it also invalidates the definition capture cache.", "12345"),
    ("prompt_choices",): ("Optional alternative texts for the first prompt, one per line.\n"
                          "A choice is resolved per definition variation and saved for reproducibility.",
                           "A person sits down slowly.\nA person sits down briskly."),
    ("variation_ranges",): ("Check a parameter and set its minimum and maximum.\n"
                            "A value is sampled once for each definition variation.\n"
                            "Duration variation requires retiming.", ""),
    ("sequential_evaluation",): ("Step through intervening source frames before pose capture to help evaluate\n"
                                 "live HumanIK and other time-dependent animation.", ""),
    ("bone_offset_tolerance",): ("Maximum accepted joint-translation drift in meters, up to 0.01.\n"
                                 "Default 0.001 allows small HumanIK deviations; source joints are unchanged.",
                                 "0.001"),
    ("name_pattern",): ("Output filename without extension.\n"
                        "Tokens: {source}, {variation:03d}, {seed}, {sample:03d}, {model}, {steps},\n"
                        "{guidance_text}, {guidance_constraints}, {duration}, and {prompt}.\n"
                        "Automatic variation suffixes can be turned off below;\n"
                        "sample suffixes remain when needed.",
                         "{source}"),
    ("filename_suffix",): ("Optional text appended to the output name.\n"
                           "It supports the same tokens as Output name.\n"
                           "For example, _seed_{seed}_steps_{steps}\n"
                           "records the resolved seed and step count.",
                            "Optional: _seed_{seed}"),
    ("include_version_suffix",): ("Keep version suffixes in output names.\n"
                                  "Definition adds _v001, _v002, etc. for multiple variations;\n"
                                  "Generate keeps a trailing _v### from the input definition filename.\n"
                                  "Turn this off when {seed} already identifies outputs.\n"
                                  "Multiple samples still receive their own _s### suffix.", ""),
    ("prompt_replacements",): ("Apply Search / Replace rules to every prompt segment in the numbered\n"
                               "variation, after Prompt choices.\n"
                               "Matching is case-sensitive and literal;\n"
                               "longer matches win and replacement text is not processed again.", ""),
    ("purge_cache_on_success",): ("Remove this input's .kimodo-cache recovery files after success,\n"
                                  "including temporary downloads.\n"
                                  "Failed jobs keep their cache for retry.\n"
                                  "Published scenes and requested artifacts are kept.", ""),
    ("purge_coordination_on_finish",): ("Remove .kimodo-coordination locks and output reservations when the batch\n"
                                        "finishes and no workers are using them.\n"
                                        "Enabled by default.\n"
                                        "Disable to retain output ownership records across runs.", ""),
    ("connection", "url"): ("HTTP address of the Kimodo Bridge,\n"
                            "accessible from the Maya worker on Windows.",
                              "http://127.0.0.1:7861"),
    ("connection", "mode"): ("Use an existing Bridge or start/reuse one\n"
                             "in WSL or a native Python environment.\n"
                             "Concurrent workers coordinate local startup.", ""),
    ("connection", "python_path"): ("Python executable with Kimodo installed, used only for local startup.\n"
                                    "For WSL enter its Linux path;\n"
                                    "for native mode enter an absolute Windows path.",
                                      "/home/user/kimodo_env/bin/python"),
    ("connection", "distribution"): ("WSL distribution used for local startup.\n"
                                     "Blank uses the default distribution.\n"
                                     "Ignored when connecting to an existing Bridge.", "Default WSL distribution"),
    ("connection", "device"): ("Compute device for a locally started Bridge.\n"
                               "Automatic selects an available GPU when supported.\n"
                               "Does not reconfigure an existing Bridge.", ""),
    ("connection", "text_encoder_url"): ("Text encoder service address used by a locally started Bridge.\n"
                                         "This address is resolved inside its Python/WSL environment.",
                                            "http://127.0.0.1:9550"),
    ("connection", "start_encoder"): ("Start the text encoder with a local Bridge.\n"
                                      "Disable when the encoder service is already managed separately.", ""),
    ("token_environment",): ("Optional environment variable containing the Bridge access token.\n"
                             "Enter its name, not the token itself.\n"
                             "It must be available to the Maya worker.",
                               "KIMODO_BRIDGE_TOKEN"),
    ("result_mode",): ("Save one Maya scene per sample, optionally retain every generated artifact,\n"
                       "or output only an artifact manifest.\n"
                       "Recovery downloads are stored in .kimodo-cache while a job runs;\n"
                       "Purge cache after success controls retention.", ""),
    ("output_extension",): ("Maya ASCII (.ma) or Maya Binary (.mb) output.\n"
                            "Ignored for artifacts-only output.", ""),
    ("import_incoming_scene",): ("Import the source Maya scene captured by Kimodo Definition into each\n"
                                 "generated scene, including curves and other scene nodes.\n"
                                 "String inputs have no scene to import.\n"
                                 "Ignored for artifacts-only output.", ""),
    ("include_definition_attribute",): ("Store the generation on the kimodo motion group as two string attributes:\n"
                                        "kimodoDefinition is the fully resolved definition JSON, ready to load in\n"
                                        "the Kimodo Generator; kimodoBatchDefinition keeps the unresolved Batch\n"
                                        "Processor task parameters and input values for later reference.\n"
                                        "Ignored for artifacts-only output.", ""),
    ("namespace",): ("Namespace for the generated skeleton in its new Maya scene.\n"
                     "Use letters, digits, and underscores; begin with a letter or underscore.", "kimodo"),
    ("import_start_frame",): ("Maya frame receiving the first generated sample.\n"
                              "Does not affect generation timing.", "1"),
    ("expected_model_fps",): ("Expected sample rate for external definitions without batch metadata.\n"
                              "SOMA uses 30 fps.\n"
                              "A mismatch stops publication instead of silently retiming motion.", "30"),
    ("add_humanik",): ("Characterize the imported Kimodo skeleton for later HumanIK retargeting.\n"
                       "This alone does not transfer animation onto another character.", ""),
    ("humanik", "character_name"): ("Name of the HumanIK character created for the imported skeleton.",
                                      "KimodoCharacter"),
    ("humanik", "definition_path"): ("Optional HumanIK definition XML.\n"
                                     "Blank uses the packaged Kimodo profile.\n"
                                     "Supports project path variables.",
                                       "Default Kimodo definition, or {project-dir}/hik.xml"),
    ("humanik", "tpose_path"): ("Optional T-pose file.\n"
                                "Blank uses the packaged Kimodo pose unless a reference frame is provided.\n"
                                "Choose a pose file or a reference frame, not both.",
                                 "Default Kimodo T-pose, or {project-dir}/tpose.json"),
    ("humanik", "reference_frame"): ("Optional frame in the imported animation\n"
                                     "to use as the characterization pose.\n"
                                     "Blank uses the rest/T-pose.\n"
                                     "Frame zero is valid.",
                                       "Optional frame; blank uses T-pose"),
    ("humanik", "lock_definition"): ("Lock the created HumanIK character definition after characterization.", ""),
    ("startup_timeout",): ("Seconds to wait for a locally started Bridge to become healthy.", "180"),
    ("queue_timeout",): ("Maximum seconds waiting for queue capacity and a queued job to start.", "7200"),
    ("generation_timeout",): ("Maximum seconds waiting after the job starts.\n"
                              "Separate from queue time.\n"
                              "Cancel on timeout controls whether the remote job is also canceled.", "1200"),
    ("poll_interval",): ("Seconds between job-status requests.\n"
                         "Smaller values update the tracker more often.", "1"),
    ("connection", "timeout"): ("Timeout in seconds for an individual Bridge HTTP request,\n"
                                "including downloads.\n"
                                "Separate from the total generation timeout.", "10"),
    ("network_retries",): ("Retry count for transient connection failures, from 0 to 100.\n"
                           "Submission retries reuse the saved job ID to avoid duplicate generation.", "5"),
    ("cancel_on_timeout",): ("Cancel the remote job when the task wait expires.\n"
                             "When disabled, the job can continue on the Bridge\n"
                             "and be recovered on a later run.", ""),
    ("retry_failed",): ("Start a new job for a previously recorded failed or canceled job.\n"
                        "Successful generation is reused for download/import retries.", ""),
}


class KimodoComboBox(qt.QtWidgets.QComboBox):
    """Prevents wheel scrolling from changing an option while scrolling the panel."""

    def wheelEvent(self, event):
        """Ignores wheel changes so the containing settings panel can scroll instead.

        Args:
            event (QWheelEvent): Mouse wheel event.
        """
        event.ignore()


def _get_numeric_range_default(value, fallback, integer=False):
    """Converts a definition value to a safe spin-box default.

    Args:
        value (object): Requested value.
        fallback (int or float): Value used when conversion fails.
        integer (bool, optional): Whether to return a whole number.

    Returns:
        int or float: Finite default value.
    """
    try:
        if isinstance(value, bool):
            raise ValueError("Boolean values are not numeric range defaults.")
        numeric_value = int(value) if integer else float(value)
        if not math.isfinite(numeric_value):
            raise ValueError("Numeric range defaults must be finite.")
        return numeric_value
    except (TypeError, ValueError, OverflowError):
        return fallback


class AttrWidgetKimodo(AttrWidgetTask):
    """Shared form binding for nested Kimodo task settings."""

    def __init__(self, *args, **kwargs):
        """Builds common I/O settings and non-modal validation feedback.

        Args:
            *args: Standard task-widget positional arguments.
            **kwargs: Standard task-widget keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.invalid_fields = set()
        self.sections = {}
        self.add_common_task_settings(collapsible=False)
        self.modify_checkbox.setEnabled(False)
        self.modify_checkbox.setToolTip("Kimodo outputs always use a separate target folder.")
        self.status = qt.QtWidgets.QLabel()
        self.status.setWordWrap(True)
        self.controls = {}
        self.control_extras = {}
        self.building = True

    def section(self, title, collapsed=True):
        """Creates a compact optional section.

        Args:
            title (str): Section title.
            collapsed (bool): Initial collapsed state.

        Returns:
            QLayout: Section content layout.
        """
        section_data = self.add_collapsible_section(title, collapsed=collapsed)
        self.sections[title] = section_data
        return section_data["content_layout"]

    def add_labeled_layout(self, label_text, label_width=110, tooltip=None, parent_layout=None):
        """Keeps labels compact while giving the remaining row width to its editor.

        Args:
            label_text (str): Field label.
            label_width (int): Minimum label width in logical pixels.
            tooltip (str, optional): Field help text.
            parent_layout (QLayout, optional): Destination section.

        Returns:
            QHBoxLayout: Row with a font-scaled, fixed-width label.
        """
        row = super().add_labeled_layout(label_text, label_width, tooltip, parent_layout)
        label = row.itemAt(0).widget()
        width = label.fontMetrics().horizontalAdvance("Generation timeout (s):") + 8
        label.setFixedWidth(max(label_width, width))
        label.setSizePolicy(qt.QtLib.SizePolicy.Fixed, qt.QtLib.SizePolicy.Preferred)
        return row

    def value(self, path):
        """Retrieves a nested setting.

        Args:
            path (tuple): Setting keys.

        Returns:
            object: Current setting.
        """
        value = self.task.settings
        for key in path:
            value = value[key]
        return value

    def store(self, path, value):
        """Stores a nested setting without rebuilding the active widget.

        Args:
            path (tuple): Setting keys.
            value (object): New value.
        """
        target = self.task.settings
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        if not self.building:
            self.update_enabled_state()

    def field(self, layout, label, key, kind="text", choices=None, tooltip="", inline_row=None):
        """Adds a bound setting control with a readable label and tooltip.

        Args:
            layout (QLayout): Destination layout.
            label (str): User-facing name.
            key (str or tuple): Setting key or nested key path.
            kind (str): text, path, integer, number, boolean, json, area, or choice.
            choices (list, optional): Value/label pairs for a combo box.
            tooltip (str): Setting guidance.
            inline_row (QHBoxLayout, optional): Existing row for related controls.

        Returns:
            QWidget: Created control.
        """
        path = key if isinstance(key, tuple) else (key,)
        help_text, placeholder = FIELD_HELP[path[:-1] if isinstance(path[-1], int) else path]
        tooltip = help_text
        value = self.value(path)
        setter = partial(self.store, path)
        row = inline_row
        if row is not None and kind != "boolean" and label:
            inline_label = qt.QtWidgets.QLabel(label)
            inline_label.setToolTip(tooltip)
            row.addWidget(inline_label)
            self.control_extras[path] = [inline_label]
        if kind == "path":
            widgets = self.add_path_template_field(label, value, setter, placeholder=placeholder,
                                                   tooltip=tooltip, parent_layout=layout, return_widgets=True)
            control = widgets["field"]
            self.control_extras[path] = [widgets[name] for name in ("info_button", "open_button", "browse_button")]
        elif kind == "boolean":
            if row is None:
                row = qt.QtWidgets.QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                layout.addLayout(row)
            control = qt.QtWidgets.QCheckBox(label)
            control.setChecked(bool(value))
            control.toggled.connect(setter)
            control.setSizePolicy(qt.QtLib.SizePolicy.Fixed, qt.QtLib.SizePolicy.Preferred)
            row.addWidget(control)
        elif kind in ("integer", "number"):
            if row is None:
                row = self.add_labeled_layout(label, parent_layout=layout, tooltip=tooltip)
            control = qt.QtWidgets.QDoubleSpinBox() if kind == "number" else qt.QtWidgets.QSpinBox()
            if kind == "number":
                control.setDecimals(0 if path == ("base_seed",) else 6 if path == ("bone_offset_tolerance",) else 3)
                control.setRange(-1000000, 4294967295)
            else:
                control.setRange(-1000000, 1000000)
            control.setValue(float(value) if kind == "number" else int(value))
            if path[:3] == ("definition", "parameters", "guidance"):
                control.setRange(0, 20)
                control.setSingleStep(0.25)
            control.valueChanged.connect(setter)
            if path == ("definition", "parameters", "num_samples"):
                control.setRange(1, 8)
            control.setMinimumHeight(35)
            control.setMinimumWidth(control.fontMetrics().horizontalAdvance("0000.000") + 24)
            ignored_policy = getattr(qt.QtWidgets.QSizePolicy, "Policy", qt.QtWidgets.QSizePolicy).Ignored
            control.setSizePolicy(ignored_policy, qt.QtLib.SizePolicy.Fixed)
            control.lineEdit().setPlaceholderText(placeholder)
            row.addWidget(control, 1)
        elif kind == "choice":
            if row is None:
                row = self.add_labeled_layout(label, parent_layout=layout, tooltip=tooltip)
            control = KimodoComboBox()
            for option, text in choices:
                control.addItem(text, option)
            control.setCurrentIndex(max(0, control.findData(value)))
            control.currentIndexChanged.connect(partial(self.store_choice, path, control))
            control.setMinimumHeight(35)
            control.setMinimumWidth(65)
            ignored_policy = getattr(qt.QtWidgets.QSizePolicy, "Policy", qt.QtWidgets.QSizePolicy).Ignored
            control.setSizePolicy(ignored_policy, qt.QtLib.SizePolicy.Fixed)
            row.addWidget(control, 1)
        elif kind in ("json", "area"):
            text = json.dumps(value, indent=2) if kind == "json" and not isinstance(value, str) else value
            control = self.add_text_area(label, text, partial(self.store_json, path) if kind == "json" else setter,
                                         tooltip=tooltip, parent_layout=layout)
            control.setPlaceholderText(placeholder)
        else:
            if row is not None:
                control = self.create_text_field(text=str(value) if value is not None else "",
                                                 placeholder=placeholder, tooltip=tooltip)
                control.textChanged.connect(setter)
                row.addWidget(control, 1)
            else:
                control = self.add_text_field(label, str(value) if value is not None else "", setter,
                                              placeholder=placeholder, tooltip=tooltip, parent_layout=layout)
        if control:
            control.setToolTip(tooltip or label)
        self.controls[path] = control
        return control

    def set_field_enabled(self, key, enabled):
        """Toggles a control and its related labels/path buttons without changing its value.

        Args:
            key (str or tuple): Setting key or path.
            enabled (bool): Whether the setting applies in the current mode.
        """
        path = key if isinstance(key, tuple) else (key,)
        for widget in [self.controls[path]] + self.control_extras.get(path, []):
            widget.setEnabled(enabled)

    def update_enabled_state(self):
        """Updates dependencies in the concrete task panel after a setting changes."""

    def store_choice(self, path, control, index):
        """Stores a combo box's stable option value.

        Args:
            path (tuple): Setting keys.
            control (QComboBox): Source control.
            index (int): Selected index.
        """
        self.store(path, control.itemData(index))

    def store_json(self, path, text):
        """Keeps incomplete JSON visible and prevents silently using stale values.

        Args:
            path (tuple): Setting keys.
            text (str): Editable JSON text.
        """
        try:
            value = json.loads(text)
            self.invalid_fields.discard(path)
        except ValueError:
            value = text
            self.invalid_fields.add(path)
        self.store(path, value)
        self.status.setText("Complete invalid JSON before running."
                            if self.invalid_fields else "Settings updated.")

    def finish(self):
        """Adds naming, validation, and persistent status feedback."""
        section = self.section(self.task.output_section_name)
        self.field(section, "Output name", "name_pattern")
        self.field(section, "Filename suffix", "filename_suffix")
        options_row = qt.QtWidgets.QHBoxLayout()
        options_row.setContentsMargins(0, 0, 0, 0)
        section.addLayout(options_row)
        self.field(section, "Include version suffix", "include_version_suffix", "boolean", inline_row=options_row)
        if "import_incoming_scene" in self.task.settings:
            self.field(section, "Import incoming scene", "import_incoming_scene", "boolean",
                       inline_row=options_row)
        if "include_definition_attribute" in self.task.settings:
            self.field(section, "Include definition attribute", "include_definition_attribute", "boolean",
                       inline_row=options_row)
        options_row.addStretch(1)
        button = qt.QtWidgets.QPushButton("Validate Settings")
        button.setToolTip("Check task settings and profile paths without opening scenes or submitting\n"
                          "generation.")
        button.clicked.connect(self.validate_settings)
        self.content_layout.addWidget(button)
        self.content_layout.addWidget(self.status)
        self.content_layout.addStretch()
        self.building = False
        self.update_enabled_state()

    def validate_settings(self):
        """Displays diagnostics and expands each area with an error."""
        result = self.task.validate(self.project)
        for error in result.errors:
            if not error.startswith("[") or "]" not in error:
                continue
            section_name = error[1:error.find("]")]
            section_data = self.sections.get(section_name)
            if section_data and not section_data["button"].isChecked():
                section_data["button"].click()
        self.status.setText("\n".join(result.errors + result.warnings) or "Settings are valid.")


class AttrWidgetKimodoDefinition(AttrWidgetKimodo):
    """Capture rules, generation parameters, and variations for definition creation."""

    def __init__(self, *args, **kwargs):
        """Builds the definition task panel.

        Args:
            *args: Standard task-widget positional arguments.
            **kwargs: Standard task-widget keyword arguments.
        """
        super().__init__(*args, **kwargs)
        section = self.section("Pose Capture")
        self.field(section, "Skeleton", "pose_source",
                   tooltip="Group or descendant.\n"
                           "Blank requires one Kimodo skeleton.")
        self.field(section, "Range", "range_mode", "choice", [
            ("playback", "Playback range"), ("animation", "Animation range"), ("custom", "Custom range")])
        row = self.add_labeled_layout("Custom range", parent_layout=section)
        self.field(section, "Start", "start_frame", "number", inline_row=row)
        self.field(section, "End", "end_frame", "number", inline_row=row)
        row = self.add_labeled_layout("Capture", parent_layout=section)
        self.field(section, "First frame", "capture_first", "boolean", inline_row=row)
        self.field(section, "Last frame", "capture_last", "boolean", inline_row=row)
        row.addStretch(1)
        self.field(section, "Pose frames", "pose_frames", tooltip="Scene frames: 296, 423, 648 or 296:648:30.")
        self.field(section, "Pose type", "pose_type", "choice", [
            ("fullbody", "Full body"), ("hips", "Hips"), ("left-hand", "Left hand"), ("right-hand", "Right hand"),
            ("left-foot", "Left foot"), ("right-foot", "Right foot")])
        row = self.add_labeled_layout("Marker attribute", parent_layout=section)
        self.field(section, "Use", "use_marker", "boolean", inline_row=row)
        self.field(section, "Attribute", "marker_attribute", inline_row=row)
        self.field(section, "Marker mode", "marker_mode", "choice", [
            ("evaluated", "Every active sample"), ("keyed", "Active keyed frames"),
            ("rising", "Start of active interval")])
        row = self.add_labeled_layout("Marker sampling", parent_layout=section)
        self.field(section, "Active value", "marker_value", "number", inline_row=row)
        self.field(section, "Step", "sample_step", "number", inline_row=row)
        button = qt.QtWidgets.QPushButton("Preview Frames in Current Scene")
        button.setToolTip("Evaluate capture rules in the open scene and list source frames and model\n"
                          "indices.\n"
                          "Restores the current time; does not save or generate animation.")
        button.clicked.connect(self.preview_frames)
        section.addWidget(button)
        section = self.section("Root Path")
        self.field(section, "Curve / locator list", "path_nodes")
        self.field(section, "Random curve per variation", "randomize_root_path", "boolean")
        self.field(section, "Path frames", "path_frames")
        self.field(section, "Path samples", "path_samples", "integer")
        row = self.add_labeled_layout("Root heading", parent_layout=section)
        self.field(section, "", "root_heading", "choice", [
            ("none", "None"), ("path", "Direction of travel"), ("node", "Node +Z axis"), ("fixed", "Fixed")],
            inline_row=row)
        self.field(section, "Offset", "root_heading_offset", "number", inline_row=row)
        section = self.section("Generation")
        self.field(section, "Use input string as prompt", "use_input_string", "boolean",
                   tooltip="Replace the first prompt with the current Input Strings or Input Pairs text.\n"
                           "Inputs without scene files use prompt durations\n"
                           "and skip Maya pose/path capture.")
        self.field(section, "Setup / definition", "template_path", "path",
                   tooltip="Optional template replaces the local generation settings below.")
        self.field(section, "Model", ("definition", "model"))
        self.field(section, "Motion source", "prompt_mode", "choice", [("table", "Table"), ("text", "Text")])
        self.field(section, "Motion text", "prompt_text")
        self.motion_source_status = qt.QtWidgets.QLabel()
        self.motion_source_status.setWordWrap(True)
        section.addWidget(self.motion_source_status)
        self.motion_text_help = qt.QtWidgets.QLabel(
            f"Format: {MOTION_TEXT_EXAMPLE}\n"
            "Use {input-string} for a complete sequence, or [[2, \"{input-file}\"]] for an input name description.")
        self.motion_text_help.setWordWrap(True)
        section.addWidget(self.motion_text_help)
        from gt.tools.batch_processor.widgets.kimodo_prompt_editor import KimodoPromptEditor

        self.prompt_editor = KimodoPromptEditor(
            self.value(("definition", "prompts")), partial(self.store, ("definition", "prompts")))
        self.prompt_editor.setToolTip(FIELD_HELP[("definition", "prompts")][0])
        self.controls[("definition", "prompts")] = self.prompt_editor
        section.addWidget(self.prompt_editor)
        section.addSpacing(12)
        row = self.add_labeled_layout("Sampling", parent_layout=section)
        self.field(section, "Samples", ("definition", "parameters", "num_samples"), "integer", inline_row=row)
        self.field(section, "Steps", ("definition", "parameters", "diffusion_steps"), "integer", inline_row=row)
        row = self.add_labeled_layout("Guidance", parent_layout=section)
        self.field(section, "Text", ("definition", "parameters", "guidance", 0), "number", inline_row=row)
        self.field(section, "Pose", ("definition", "parameters", "guidance", 1), "number", inline_row=row)
        row = self.add_labeled_layout("Motion", parent_layout=section)
        self.field(section, "Heading (rad)", ("definition", "parameters", "heading"), "number", inline_row=row)
        self.field(section, "Postprocess", ("definition", "parameters", "postprocess"), "boolean", inline_row=row)
        self.field(section, "Transition frames", ("definition", "parameters", "transition_frames"), "integer")
        self.field(section, "Model FPS", "model_fps", "number",
                   tooltip="SOMA uses 30 fps.\n"
                           "Generation verifies this against bridge metadata/results.")
        self.field(section, "Duration", "duration_mode", "choice", [
            ("source", "Match source timing"), ("definition", "Use prompt durations")])
        self.field(section, "Retime constraints", "retime_constraints", "boolean")
        self.field(section, "Template constraints", "constraint_mode", "choice", [
            ("replace", "Replace with captured constraints"), ("append", "Keep and append captures")])
        section = self.section("Variations")
        section.parentWidget().setSizePolicy(qt.QtLib.SizePolicy.Preferred, qt.QtLib.SizePolicy.Minimum)
        self.field(section, "Definitions per file", "variations", "integer")
        self.field(section, "Seed policy", "seed_policy", "choice", [
            ("fixed", "Fixed seed"), ("per_file", "Repeatable per file / variation"), ("random", "Random")])
        self.field(section, "Base seed", "base_seed", "number")
        seed_hint = qt.QtWidgets.QLabel(
            "Random seeds are stored in each definition. To include one in its filename, "
            "set Filename suffix to _seed_{seed} under Output Naming."
        )
        seed_hint.setWordWrap(True)
        section.addWidget(seed_hint)
        self.field(section, "Prompt choices", "prompt_choices", "area",
                   tooltip="Optional alternatives for the first prompt, one per line.")
        from gt.tools.batch_processor.widgets.kimodo_replacement_editor import KimodoReplacementEditor

        self.replacement_editor = KimodoReplacementEditor(
            self.value(("prompt_replacements",)), partial(self.store, ("prompt_replacements",)))
        self.replacement_editor.setToolTip(FIELD_HELP[("prompt_replacements",)][0])
        self.controls[("prompt_replacements",)] = self.replacement_editor
        section.addWidget(self.replacement_editor)
        from gt.tools.batch_processor.widgets.kimodo_variation_editor import KimodoVariationRangeEditor

        self.variation_editor = KimodoVariationRangeEditor(
            self.value(("variation_ranges",)), partial(self.store, ("variation_ranges",)),
            defaults=self.get_variation_range_defaults())
        self.variation_editor.setToolTip(FIELD_HELP[("variation_ranges",)][0])
        self.controls[("variation_ranges",)] = self.variation_editor
        section.addWidget(self.variation_editor)
        section = self.section("Evaluation")
        self.field(section, "Sequential stepping", "sequential_evaluation", "boolean")
        self.field(section, "Bone tolerance (m)", "bone_offset_tolerance", "number",
                   tooltip="Allowed HumanIK translation drift.\n"
                           "Default 0.001 m; offsets normalize to model bones.")
        section = self.section("Recovery")
        self.field(section, "Purge cache after success", "purge_cache_on_success", "boolean")
        self.field(section, "Purge coordination folders after run", "purge_coordination_on_finish", "boolean")
        self.finish()

    def get_variation_range_defaults(self):
        """Gets neutral min/max defaults from the task's local definition.

        Returns:
            dict: Default bounds for each supported range, used only while unchecked.
        """
        definition = self.value(("definition",))
        parameters = definition.get("parameters", {}) if isinstance(definition, dict) else {}
        prompts = definition.get("prompts", []) if isinstance(definition, dict) else []
        guidance = parameters.get("guidance", [2, 2])
        if not isinstance(guidance, (list, tuple)) or len(guidance) < 2:
            guidance = [2, 2]
        try:
            duration = sum(float(prompt.get("duration_seconds", 0))
                           for prompt in prompts if isinstance(prompt, dict))
            if not math.isfinite(duration):
                duration = 1
        except (TypeError, ValueError, OverflowError):
            duration = 1
        values = {
            "diffusion_steps": _get_numeric_range_default(parameters.get("diffusion_steps"), 100, integer=True),
            "heading": _get_numeric_range_default(parameters.get("heading"), 0),
            "guidance_text": _get_numeric_range_default(guidance[0], 2),
            "guidance_constraints": _get_numeric_range_default(guidance[1], 2),
            "duration_seconds": duration if duration > 0 else 1,
        }
        return {key: [value, value] for key, value in values.items()}

    def update_enabled_state(self):
        """Clarifies active capture inputs and template overrides without clearing local settings."""
        settings = self.task.settings
        for key in ("start_frame", "end_frame"):
            self.set_field_enabled(key, settings["range_mode"] == "custom")
        for key in ("marker_attribute", "marker_mode", "marker_value"):
            self.set_field_enabled(key, settings["use_marker"])
        self.set_field_enabled("sample_step", settings["use_marker"] and settings["marker_mode"] != "keyed")
        path_enabled = bool(settings["path_nodes"].strip())
        path_nodes = [value.strip() for value in settings["path_nodes"].split(",") if value.strip()]
        self.set_field_enabled("path_frames", path_enabled)
        self.set_field_enabled("randomize_root_path", path_enabled)
        self.set_field_enabled("root_heading", path_enabled)
        self.set_field_enabled("root_heading_offset", path_enabled and settings.get("root_heading", "none") != "none")
        curve_sampling = settings.get("randomize_root_path", False) or len(path_nodes) == 1
        self.set_field_enabled("path_samples", path_enabled and not settings["path_frames"].strip()
                               and curve_sampling)
        local_definition = not settings["template_path"].strip()
        for path in self.controls:
            if path[0] == "definition":
                self.set_field_enabled(path, local_definition)
        text_mode = settings.get("prompt_mode", "table") == "text"
        self.set_field_enabled("prompt_text", text_mode)
        self.motion_text_help.setVisible(text_mode)
        self.set_field_enabled(("definition", "prompts"), local_definition and not text_mode)
        self.set_field_enabled("use_input_string", not text_mode)
        if text_mode:
            source_status = "Motion descriptions come from Text. The table is inactive; its rows are retained."
        elif not local_definition:
            source_status = "Motion descriptions come from the setup / definition file. The local table is inactive."
        elif settings.get("use_input_string"):
            source_status = "Motion descriptions come from the table; the first description uses the input string."
        else:
            source_status = "Motion descriptions come from the table."
        self.motion_source_status.setText(source_status)
        self.set_field_enabled(("definition", "parameters", "transition_frames"),
                               local_definition and (text_mode or self.prompt_editor.table.rowCount() > 1))
        self.prompt_editor.set_timing_mode(settings["duration_mode"] == "source")

    def preview_frames(self):
        """Shows capture timing without writing files or replacing the current scene."""
        from gt.tools.batch_processor.tasks import task_kimodo_definition
        from gt.utils import kimodo

        try:
            result = task_kimodo_definition.resolve_frames(self.task.settings)
            indices, count = kimodo.map_constraint_frames(result["frames"], result["start"], result["end"],
                                                    result["source_fps"], self.task.settings["model_fps"])
            prefix = "Dense capture: " if len(indices) > 64 else ""
            warning = result.get("group_warning")
            warning_text = f"WARNING: {warning}\n" if warning else ""
            self.status.setText(f"{warning_text}{prefix}{len(indices)} poses / {count} model frames.\n"
                                f"Scene frames: {result['frames']}\nModel indices: {indices}")
        except Exception as error:
            self.status.setText(str(error))


class AttrWidgetKimodoGenerate(AttrWidgetKimodo):
    """Bridge, output, recovery, and HumanIK controls for generation."""

    def __init__(self, *args, **kwargs):
        """Builds the generation task panel.

        Args:
            *args: Standard task-widget positional arguments.
            **kwargs: Standard task-widget keyword arguments.
        """
        super().__init__(*args, **kwargs)
        section = self.section("Connection", False)
        self.field(section, "Bridge URL", ("connection", "url"))
        row = self.add_labeled_layout("Connection", parent_layout=section)
        self.field(section, "Mode", ("connection", "mode"), "choice", [
            ("existing", "Existing bridge"), ("wsl", "Start / reuse WSL bridge"),
            ("native", "Start / reuse native bridge")], inline_row=row)
        self.field(section, "Device", ("connection", "device"), "choice", [
            ("auto", "Automatic"), ("cuda", "CUDA"), ("cpu", "CPU")], inline_row=row)
        self.field(section, "Python executable", ("connection", "python_path"),
                   tooltip="Absolute Linux path for WSL, or absolute Windows path for native startup.")
        self.field(section, "WSL distribution", ("connection", "distribution"))
        row = self.add_labeled_layout("Text encoder", parent_layout=section)
        self.field(section, "Auto-start", ("connection", "start_encoder"), "boolean", inline_row=row)
        self.field(section, "URL", ("connection", "text_encoder_url"), inline_row=row)
        self.field(section, "Token environment", "token_environment",
                   tooltip="Optional environment variable name.\n"
                           "Token values are never stored in batch files.")
        button = qt.QtWidgets.QPushButton("Test Connection")
        button.setToolTip("Check the configured Bridge and list available models without starting a\n"
                          "job.")
        button.clicked.connect(self.test_connection)
        section.addWidget(button)
        section = self.section("Results")
        self.field(section, "Output", "result_mode", "choice", [
            ("maya", "Maya scenes only"), ("maya_and_artifacts", "Maya scenes + all artifacts"),
            ("artifacts", "All artifacts only")])
        row = self.add_labeled_layout("Maya output", parent_layout=section)
        self.field(section, "Format", "output_extension", "choice",
                   [(".ma", "Maya ASCII"), (".mb", "Maya Binary")], inline_row=row)
        self.field(section, "Start frame", "import_start_frame", "number", inline_row=row)
        self.field(section, "Namespace", "namespace")
        self.field(section, "Expected model FPS", "expected_model_fps", "number")
        section = self.section("HumanIK")
        row = self.add_labeled_layout("Characterize", parent_layout=section)
        self.field(section, "Add HumanIK", "add_humanik", "boolean", inline_row=row)
        self.field(section, "Lock definition", ("humanik", "lock_definition"), "boolean", inline_row=row)
        row.addStretch(1)
        self.field(section, "Character name", ("humanik", "character_name"))
        for label, key in (("Definition XML", "definition_path"), ("T-pose file", "tpose_path")):
            self.field(section, label, ("humanik", key), "path", tooltip="Blank uses the default Kimodo profile.")
        frame = self.field(section, "Reference frame", ("humanik", "reference_frame"),
                           tooltip="Blank uses the rest pose.\n"
                                   "Choose either a frame or a T-pose file.")
        frame.textChanged.disconnect()
        frame.textChanged.connect(self.set_reference_frame)
        section = self.section("Recovery and Timeouts")
        for label, fields in (
                ("Connection limits (s)", (("Startup", "startup_timeout"), ("Request", ("connection", "timeout")))),
                ("Job limits (s)", (("Queue", "queue_timeout"), ("Generation", "generation_timeout")))):
            row = self.add_labeled_layout(label, parent_layout=section)
            for field_label, key in fields:
                self.field(section, field_label, key, "number", inline_row=row)
        self.field(section, "Poll interval (s)", "poll_interval", "number")
        self.field(section, "Network retries", "network_retries", "integer")
        row = self.add_labeled_layout("Recovery", parent_layout=section)
        self.field(section, "Cancel on timeout", "cancel_on_timeout", "boolean", inline_row=row)
        self.field(section, "Retry failed jobs", "retry_failed", "boolean", inline_row=row)
        row.addStretch(1)
        self.field(section, "Purge cache after success", "purge_cache_on_success", "boolean")
        self.field(section, "Purge coordination folders after run", "purge_coordination_on_finish", "boolean")
        self.finish()

    def update_enabled_state(self):
        """Enables only connection, scene, and HumanIK settings that apply to the selected modes."""
        settings = self.task.settings
        local_bridge = settings["connection"]["mode"] != "existing"
        for key in ("python_path", "device", "text_encoder_url", "start_encoder"):
            self.set_field_enabled(("connection", key), local_bridge)
        self.set_field_enabled(("connection", "distribution"), settings["connection"]["mode"] == "wsl")
        self.set_field_enabled("startup_timeout", local_bridge)
        maya_output = settings["result_mode"] != "artifacts"
        for key in ("output_extension", "namespace", "import_start_frame", "add_humanik", "import_incoming_scene",
                    "include_definition_attribute"):
            self.set_field_enabled(key, maya_output)
        hik_enabled = maya_output and settings["add_humanik"]
        for key in settings["humanik"]:
            if ("humanik", key) in self.controls:
                self.set_field_enabled(("humanik", key), hik_enabled)
        pose_path = bool(settings["humanik"]["tpose_path"].strip())
        reference_frame = settings["humanik"]["reference_frame"] is not None
        self.set_field_enabled(("humanik", "tpose_path"), hik_enabled and (not reference_frame or pose_path))
        self.set_field_enabled(("humanik", "reference_frame"), hik_enabled and (not pose_path or reference_frame))

    def set_reference_frame(self, text):
        """Stores an optional reference frame, retaining invalid text for validation.

        Args:
            text (str): Frame text or empty value.
        """
        try:
            value = float(text) if text.strip() else None
        except ValueError:
            value = text
        self.store(("humanik", "reference_frame"), value)

    def test_connection(self):
        """Checks server health and models without starting or submitting anything."""
        from gt.utils import kimodo

        try:
            token_name = self.task.settings["token_environment"]
            client = kimodo.KimodoClient(kimodo.KimodoConnection(
                token=os.environ.get(token_name) if token_name else None, **self.task.settings["connection"]))
            health = client.health()
            self.status.setText(f"Bridge ready; {health.get('queue_size', 0)} queued jobs.\n"
                                + ", ".join(model["id"] for model in client.capabilities()["models"]))
        except Exception as error:
            self.status.setText(str(error))
