"""
Batch Processor Rename Task Attribute Widget
"""

from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetRenameTask(AttrWidgetTask):
    """Attribute widget for the rename task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the rename task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (RenameTask, optional): Rename task.
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
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Rename Preferences")
        self.add_text_field(
            "Name Template",
            self.task.settings.get("name_template") or self.task.settings.get("pattern"),
            partial(self.set_task_setting, key="name_template"),
            placeholder="{name}",
            tooltip="Base filename template. Supports rename tokens and batch environment variables.",
        )
        prefix_layout = ui_qt.QtWidgets.QHBoxLayout()
        prefix_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Prefix",
            self.task.settings.get("use_prefix"),
            partial(self.set_task_setting, key="use_prefix"),
            layout=prefix_layout,
            tooltip="Add a prefix to the rendered filename.",
        )
        prefix_field = self.create_text_field(
            text=self.task.settings.get("prefix"),
            placeholder="prefix_",
            tooltip="Prefix added when Prefix is enabled.",
        )
        prefix_field.textChanged.connect(partial(self.set_task_setting, key="prefix"))
        prefix_layout.addWidget(prefix_field)
        self.content_layout.addLayout(prefix_layout)
        suffix_layout = ui_qt.QtWidgets.QHBoxLayout()
        suffix_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Suffix",
            self.task.settings.get("use_suffix"),
            partial(self.set_task_setting, key="use_suffix"),
            layout=suffix_layout,
            tooltip="Add a suffix to the rendered filename.",
        )
        suffix_field = self.create_text_field(
            text=self.task.settings.get("suffix"),
            placeholder="_suffix",
            tooltip="Suffix added when Suffix is enabled.",
        )
        suffix_field.textChanged.connect(partial(self.set_task_setting, key="suffix"))
        suffix_layout.addWidget(suffix_field)
        self.content_layout.addLayout(suffix_layout)
        replace_layout = ui_qt.QtWidgets.QHBoxLayout()
        replace_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Search Replace",
            self.task.settings.get("use_search_replace"),
            partial(self.set_task_setting, key="use_search_replace"),
            layout=replace_layout,
            tooltip="Search and replace text in the rendered filename.",
        )
        search_field = self.create_text_field(
            text=self.task.settings.get("search_text"),
            placeholder="search",
            tooltip="Text to find when Search Replace is enabled.",
        )
        replace_field = self.create_text_field(
            text=self.task.settings.get("replace_text"),
            placeholder="replace",
            tooltip="Replacement text used when Search Replace is enabled.",
        )
        search_field.textChanged.connect(partial(self.set_task_setting, key="search_text"))
        replace_field.textChanged.connect(partial(self.set_task_setting, key="replace_text"))
        replace_layout.addWidget(search_field)
        replace_layout.addWidget(replace_field)
        self.content_layout.addLayout(replace_layout)
        index_layout = ui_qt.QtWidgets.QHBoxLayout()
        index_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Index",
            self.task.settings.get("use_index"),
            partial(self.set_task_setting, key="use_index"),
            layout=index_layout,
            tooltip="Append a padded index to the rendered filename.",
        )
        separator_label = ui_qt.QtWidgets.QLabel("Separator:")
        attr_widget_base.configure_label_for_scaled_displays(separator_label)
        separator_label.setToolTip("Separator inserted before the appended index.")
        index_layout.addWidget(separator_label)
        index_separator_field = self.create_text_field(
            text=self.task.settings.get("index_separator"),
            placeholder="_",
            tooltip="Separator inserted before the appended index.",
        )
        index_separator_field.textChanged.connect(partial(self.set_task_setting, key="index_separator"))
        index_layout.addWidget(index_separator_field)
        digits_label = ui_qt.QtWidgets.QLabel("Digits:")
        attr_widget_base.configure_label_for_scaled_displays(digits_label)
        digits_label.setToolTip("Number of digits used by the {index} token.")
        index_layout.addWidget(digits_label)
        index_padding_spin = ui_qt.QtWidgets.QSpinBox()
        index_padding_spin.setRange(0, 12)
        index_padding_spin.setValue(int(self.task.settings.get("padding") or 0))
        index_padding_spin.setMinimumHeight(35)
        index_padding_spin.setToolTip("Number of digits used by the {index} token.")
        index_padding_spin.valueChanged.connect(partial(self.set_task_setting, key="padding"))
        index_layout.addWidget(index_padding_spin)
        self.content_layout.addLayout(index_layout)
        toggle_layout = ui_qt.QtWidgets.QHBoxLayout()
        toggle_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Preserve Extension",
            self.task.settings.get("preserve_extension"),
            partial(self.set_task_setting, key="preserve_extension"),
            layout=toggle_layout,
            tooltip="Keep the original file extension unless the pattern explicitly includes one.",
        )
        self.content_layout.addLayout(toggle_layout)
        env_button = ui_qt.QtWidgets.QPushButton("Environment Variables")
        env_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        env_button.setToolTip("Show available batch environment variables.")
        env_button.clicked.connect(self.show_environment_variables)
        self.content_layout.addWidget(env_button)
        token_label = ui_qt.QtWidgets.QLabel(
            "Tokens: {name}=base filename, {ext}=extension, {index}=padded item number, "
            "{task-name}=task name, {date}=YYYYMMDD. The Index option appends the same padded value."
        )
        attr_widget_base.configure_label_for_scaled_displays(token_label, word_wrap=True)
        token_label.setWordWrap(True)
        token_label.setMinimumWidth(1)
        token_label.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        token_label.setStyleSheet("color: grey;")
        token_label.setToolTip("Supported rename pattern tokens.")
        self.content_layout.addWidget(token_label)
        self.content_layout.addStretch()

    def show_environment_variables(self):
        """Shows the currently available project environment variables."""
        import gt.ui.python_output_view as ui_python_output_view
        import json

        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle("Batch Project Environment Variables")
        output_window.set_python_output_text(
            json.dumps(
                self.project.get_environment_variables(task=self.task, include_braces=True),
                indent=4,
                sort_keys=True,
            )
        )
        output_window.show()
