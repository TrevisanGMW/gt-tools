"""
Batch Processor Input Task Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetInputTask(AttrWidgetTask):
    """Attribute widget for input tasks."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the input task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (InputTask, optional): Input task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
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
        self.input_count_label = None
        self.add_widget_separator_line(label_text="Input Preferences")
        self.add_path_template_field(
            "Source Path",
            self.task.get_source_path_template(),
            partial(self.set_task_setting, key="source_path"),
            placeholder="{project-dir}/{input-dir}",
            tooltip="Directory template used to discover input files.",
            dir_only=True,
        )
        discovery_layout = self.add_labeled_layout(
            "Discovery",
            label_width=110,
            tooltip="Input discovery options.",
        )
        discovery_layout.setSpacing(8)
        discovery_layout.addSpacing(4)
        self.add_checkbox(
            "Include Subdirectories",
            self.task.settings.get("include_subdirectories"),
            partial(self.set_task_setting, key="include_subdirectories"),
            layout=discovery_layout,
            tooltip="Search nested folders under the input path.",
        )
        self.add_row_label(
            layout=discovery_layout,
            label_text="Extensions:",
            tooltip="Comma-separated file extensions accepted by this input task.",
        )
        extensions_field = self.create_text_field(
            text=", ".join(self.task.settings.get("extensions") or []),
            placeholder=".ma, .mb, .fbx",
            tooltip="Comma-separated file extensions accepted by this input task.",
        )
        extensions_field.textChanged.connect(partial(self.set_task_setting_list_from_text, key="extensions"))
        discovery_layout.addWidget(extensions_field)
        self.add_task_index_checkbox(discovery_layout)
        discovery_layout.addStretch()
        self.add_text_field(
            "Exclude Patterns",
            ", ".join(self.task.settings.get("exclude_patterns") or []),
            partial(self.set_task_setting_list_from_text, key="exclude_patterns"),
            placeholder="*_tmp.ma, */cache/*",
            tooltip="Comma-separated filename or path patterns to exclude.",
        )
        explicit_files_text = "\n".join(self.task.settings.get("explicit_files") or [])
        self.add_text_area(
            "Explicit Files",
            explicit_files_text,
            partial(self.set_task_setting_list_from_text, key="explicit_files"),
            placeholder="One file, name, or pattern per line. Examples: hero.fbx, *.ma, rigs/*_anim.fbx",
            tooltip=(
                "Optional explicit files, names, or wildcard patterns. Entries are resolved against "
                "templates, the project, and the input folder."
            ),
        )
        count_layout = ui_qt.QtWidgets.QVBoxLayout()
        count_layout.setSpacing(6)
        count_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignVCenter)
        self.input_count_label = ui_qt.QtWidgets.QLabel()
        self.input_count_label.setWordWrap(True)
        self.input_count_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.input_count_label.setToolTip("Input source statistics.")
        count_buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        count_buttons_layout.setContentsMargins(0, 0, 0, 0)
        count_buttons_layout.setSpacing(4)
        refresh_button = ui_qt.QtWidgets.QPushButton()
        refresh_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        refresh_button.setToolTip("Refresh file count.")
        refresh_button.clicked.connect(lambda *args: self.refresh_input_count(update_status=True))
        preview_button = ui_qt.QtWidgets.QPushButton()
        preview_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        preview_button.setToolTip("Show all resolved input file paths.")
        preview_button.clicked.connect(lambda *args: self.show_resolved_input_files())
        count_buttons_layout.addStretch()
        count_buttons_layout.addWidget(refresh_button)
        count_buttons_layout.addWidget(preview_button)
        count_buttons_layout.addStretch()
        count_layout.addWidget(self.input_count_label)
        count_layout.addLayout(count_buttons_layout)
        self.content_layout.addLayout(count_layout)
        self.refresh_input_count(update_status=False)
        self.build_segmentation_section()
        self.content_layout.addStretch()

    def build_segmentation_section(self):
        """Builds the segmentation controls shown at the bottom of the widget."""
        self.add_widget_separator_line(label_text="Segmentation")
        starts_new_input_list = bool(self.task.settings.get("start_new_input_list"))
        checkbox_row = ui_qt.QtWidgets.QHBoxLayout()
        checkbox_row.setSpacing(6)
        self.content_layout.addLayout(checkbox_row)
        checkbox_row.addStretch()
        self.add_checkbox(
            "Start New Segment",
            starts_new_input_list,
            self.set_start_new_input_list,
            layout=checkbox_row,
            tooltip=(
                "Start a new input segment at this task. Files discovered here replace the "
                "accumulated incoming files instead of merging with them, so the tasks that "
                "follow process a fresh list. This lets one project handle different file "
                "sets in sequence (for example FBX retargeting, then MA-to-FBX export, then "
                "USD processing). Leave this off to merge these files with earlier input tasks."
            ),
        )
        checkbox_row.addStretch()
        add_separator_tooltip = (
            "Show a labeled divider above this task in the task list without starting a "
            "new segment. Useful for naming the first segment or visually grouping "
            'tasks. Enabling this activates the segment name and color below, just like '
            '"Start New Segment" does.'
        )
        add_separator_checkbox = self.add_checkbox(
            "Add Separator",
            self.task.settings.get("force_segment_separator"),
            self.set_force_segment_separator,
            layout=checkbox_row,
            tooltip=add_separator_tooltip,
        )
        checkbox_row.addStretch()
        if starts_new_input_list:
            # A separator is always shown while a new segment is started, so the
            # explicit toggle is redundant and disabled.
            add_separator_checkbox.setEnabled(False)
            add_separator_checkbox.setToolTip(
                'A separator is always shown while "Start New Segment" is enabled.'
            )
        segmentation_enabled = bool(
            starts_new_input_list or self.task.settings.get("force_segment_separator")
        )
        segment_name_tooltip = (
            "Optional name for this segment divider. It labels the divider shown in the task "
            'list. Only applies when "Start New Segment" or "Add Separator" is enabled. '
            'Leave empty to use "New Input Segment".'
        )
        segment_name_layout = self.add_labeled_layout(
            "Segment Name",
            label_width=140,
            tooltip=segment_name_tooltip,
        )
        segment_name_field = self.create_text_field(
            text=self.task.settings.get("segment_name") or "",
            placeholder="New Input Segment",
            tooltip=segment_name_tooltip,
        )
        segment_name_field.textChanged.connect(partial(self.set_task_setting, key="segment_name"))
        segment_name_field.editingFinished.connect(self.call_parent_refresh)
        segment_name_field.setEnabled(segmentation_enabled)
        segment_name_layout.addWidget(segment_name_field)

        color_tooltip = (
            "Color used for this segment's divider in the task list. Pick any color from the "
            "toolkit UI colors to highlight a segment. Defaults to a soft blue."
        )
        color_layout = self.add_labeled_layout("Segment Color", label_width=140, tooltip=color_tooltip)
        color_combo = ui_qt.QtWidgets.QComboBox()
        color_combo.setMinimumHeight(35)
        color_combo.setMinimumWidth(1)
        color_combo.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        color_combo.setToolTip(color_tooltip)
        for name, color_hex in self._get_ui_color_choices():
            color_combo.addItem(self._make_color_icon(color_hex), name)
        current_color_name = self.task.get_segment_color_name()
        current_index = color_combo.findText(current_color_name)
        if current_index < 0:
            color_combo.addItem(current_color_name)
            current_index = color_combo.findText(current_color_name)
        color_combo.setCurrentIndex(max(0, current_index))
        color_combo.setEnabled(segmentation_enabled)
        # "activated" only fires on real user selection, never programmatically or on
        # teardown, which avoids a rebuild-triggered refresh loop.
        color_combo.activated.connect(
            lambda index, combo=color_combo: self.set_segment_color(combo.itemText(index))
        )
        color_layout.addWidget(color_combo)

    @staticmethod
    def _get_ui_color_choices():
        """Gets the selectable UI color names and their hex values.

        Returns:
            list: Sorted (name, hex) tuples from the toolkit UI color library.
        """
        choices = []
        for name in dir(ui_res_lib.Color.Hex):
            if name.startswith("_"):
                continue
            value = getattr(ui_res_lib.Color.Hex, name)
            if isinstance(value, str) and value.startswith("#"):
                choices.append((name, value))
        return sorted(choices)

    @staticmethod
    def _make_color_icon(color_hex):
        """Builds a small swatch icon for a color.

        Args:
            color_hex (str): Hex color value.

        Returns:
            QIcon: Swatch icon filled with the color.
        """
        pixmap = ui_qt.QtGui.QPixmap(16, 16)
        pixmap.fill(ui_qt.QtGui.QColor(color_hex))
        return ui_qt.QtGui.QIcon(pixmap)

    def set_start_new_input_list(self, value):
        """Sets the segment-start flag and refreshes the task tree separator.

        Args:
            value (bool): Whether this input task starts a new input segment.
        """
        self.set_task_setting(value=value, key="start_new_input_list")
        self.call_parent_refresh()

    def set_force_segment_separator(self, value):
        """Sets the forced-separator flag and refreshes the task tree separator.

        Args:
            value (bool): Whether a divider is shown without starting a new input list.
        """
        self.set_task_setting(value=value, key="force_segment_separator")
        self.call_parent_refresh()

    def set_segment_color(self, value):
        """Sets the segment divider color and refreshes the task tree separator.

        Args:
            value (str): UI color name selected for the divider.
        """
        self.set_task_setting(value=value, key="segment_color")
        self.call_parent_refresh()

    def show_resolved_input_files(self):
        """Shows all file paths resolved by this input task."""
        file_paths = self.task.discover_files(self.project) if self.project else []
        self.show_path_list(title="Resolved Input Files", file_paths=file_paths)
        self.emit_status_message("Resolved input preview found {0} file(s).".format(len(file_paths)))

    def refresh_input_count(self, update_status=True):
        """Refreshes the resolved input file count.

        Args:
            update_status (bool, optional): Whether to update the status/log message.
        """
        stats = self.task.get_file_statistics(self.project)
        input_count = stats.get("resolved_count", 0)
        total_count = stats.get("total_count", 0)
        file_type_count = stats.get("file_type_count", 0)
        extension_counts = stats.get("extension_counts") or {}
        resolved_extension_counts = stats.get("resolved_extension_counts") or {}
        found_types = self.format_extension_list(extension_counts)
        input_types = self.format_extension_list(resolved_extension_counts)
        self.input_count_label.setText(
            '<span style="color:#888888;">Input Files:</span> '
            '<span style="color:#FFFFFF;">{0}</span><br>'
            '<span style="color:#888888;">Total Files:</span> '
            '<span style="color:#FFFFFF;">{1}</span><br>'
            '<span style="color:#888888;">File Types:</span> '
            '<span style="color:#FFFFFF;">{2}</span><br>'
            '<span style="color:#888888;">Found Types:</span> '
            '<span style="color:#FFFFFF;">{3}</span><br>'
            '<span style="color:#888888;">Input Types:</span> '
            '<span style="color:#FFFFFF;">{4}</span>'.format(
                input_count,
                total_count,
                file_type_count,
                found_types,
                input_types,
            )
        )
        extension_lines = [
            "{0}: {1}".format(extension, extension_counts.get(extension))
            for extension in sorted(extension_counts)
        ]
        input_lines = [
            "{0}: {1}".format(extension, resolved_extension_counts.get(extension))
            for extension in sorted(resolved_extension_counts)
        ]
        self.input_count_label.setToolTip(
            "Found Types:\n{0}\n\nInput Types:\n{1}".format(
                "\n".join(extension_lines) or "No files found.",
                "\n".join(input_lines) or "No input files matched.",
            )
        )
        if update_status:
            self.emit_status_message(
                (
                    'Input task "{0}" found {1} resolved file(s), {2} total folder file(s), '
                    "and {3} file type(s)."
                ).format(
                    self.task.display_name,
                    input_count,
                    total_count,
                    file_type_count,
                )
            )

    @staticmethod
    def format_extension_list(extension_counts):
        """Formats extension counts as a compact readable list.

        Args:
            extension_counts (dict): Mapping of extensions to counts.

        Returns:
            str: Comma-separated extension list.
        """
        extensions = []
        for extension in sorted(extension_counts or {}):
            if extension == "<no extension>":
                extensions.append(extension)
            else:
                extensions.append(str(extension).lstrip("."))
        return ", ".join(extensions) or "None"
