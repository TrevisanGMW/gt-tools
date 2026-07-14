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
        self.add_text_field(
            "Explicit Ignores",
            ", ".join(self.task.settings.get("explicit_ignore_patterns") or []),
            partial(self.set_task_setting_list_from_text, key="explicit_ignore_patterns"),
            placeholder="hero_preview.ma, nested/*_old.fbx",
            tooltip=(
                "Comma-separated file name or path patterns removed from input results. "
                "Applies to both folder discovery and Explicit Files."
            ),
        )
        count_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.input_count_label = ui_qt.QtWidgets.QLabel()
        self.input_count_label.setWordWrap(True)
        self.input_count_label.setToolTip("Input source statistics.")
        count_buttons_layout = ui_qt.QtWidgets.QVBoxLayout()
        count_buttons_layout.setContentsMargins(0, 0, 0, 0)
        count_buttons_layout.setSpacing(4)
        refresh_button = ui_qt.QtWidgets.QPushButton()
        refresh_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        refresh_button.setToolTip("Refresh file count.")
        refresh_button.clicked.connect(lambda *args: self.refresh_input_count(update_status=True))
        preview_button = ui_qt.QtWidgets.QPushButton()
        preview_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        preview_button.setToolTip("Show all resolved input file paths.")
        preview_button.clicked.connect(self.show_resolved_input_files)
        count_buttons_layout.addWidget(refresh_button)
        count_buttons_layout.addWidget(preview_button)
        count_buttons_layout.addStretch()
        count_layout.addWidget(self.input_count_label)
        count_layout.addLayout(count_buttons_layout)
        self.content_layout.addLayout(count_layout)
        self.refresh_input_count(update_status=False)
        self.content_layout.addStretch()

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
