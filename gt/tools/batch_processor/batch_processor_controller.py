"""
Batch Processor Controller
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.widgets.attr_widget_base import get_icon_path
from gt.tools.batch_processor.widgets.attr_widget_project import AttrWidgetProject
from gt.tools.batch_processor.widgets.attr_widget_task import get_task_widget_class
from gt.tools.batch_processor import batch_processor_templates
from gt.tools.batch_processor import batch_processor_log_view
from gt.tools.batch_processor import batch_processor_tracker
from gt.tools.batch_processor import batch_processor_worker
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import gt.utils.request as utils_request
import gt.utils.system as utils_system
import gt.core.prefs as core_prefs
from functools import partial
import copy
import json
import logging
import os
import re
import shutil
import sys
import datetime

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BatchProcessorController:
    """Connects the batch processor model and view."""

    def __init__(self, model, view):
        """Initializes the batch processor controller.

        Args:
            model (BatchProcessorModel): Batch project model.
            view (BatchProcessorView): Batch processor view.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.log_view = batch_processor_log_view.BatchProcessorLoggingView(parent=self.view)
        self._active_log_file_path = None
        self._saved_project_state = None
        self._prefs = core_prefs.Prefs(constants.Project.PREFS_FILENAME)
        self._recent_projects = core_prefs.RecentProjects(
            prefs=self._prefs,
            key=constants.Project.PREFS_KEY_RECENT_PROJECTS,
            max_count=constants.Project.MAX_RECENT_PROJECTS,
        )
        self._convert_abs_paths_to_relative = self._prefs.get_bool(
            key=constants.Project.PREFS_KEY_CONVERT_ABS_PATHS_TO_RELATIVE,
            default=self._prefs.get_bool(key="on_set_path_abs_to_relative", default=True),
        )
        self._confirm_delete_task = self._prefs.get_bool(
            key=constants.Project.PREFS_KEY_CONFIRM_DELETE_TASK,
            default=True,
        )
        self._flag_skipped_tasks = self._prefs.get_bool(
            key=constants.Project.PREFS_KEY_FLAG_SKIPPED_TASKS,
            default=True,
        )
        self._ignore_disabled_tasks_for_task_index = self._prefs.get_bool(
            key=constants.Project.PREFS_KEY_IGNORE_DISABLED_TASKS_FOR_TASK_INDEX,
            default=False,
        )
        self._auto_segment_imported_projects = self._prefs.get_bool(
            key=constants.Project.PREFS_KEY_AUTO_SEGMENT_IMPORTED_PROJECTS,
            default=True,
        )
        self._show_package_templates = self._prefs.get_bool(
            key=constants.Project.PREFS_KEY_SHOW_PACKAGE_TEMPLATES,
            default=True,
        )
        self.apply_task_index_automation()
        self.add_menu_file()
        self.add_menu_tasks()
        self.add_menu_utils()
        self.add_menu_preferences()
        self.add_menu_logging()
        self.add_menu_help()
        self.connect_view()
        self.refresh_widgets()
        self.mark_project_clean()
        self.view.set_close_event_function(func=self.show_unsaved_changes_warning_dialog)
        self.view.show()
        self.view.install_host_close_event_filter()

    def connect_view(self):
        """Connects view signals to controller methods."""
        self.view.task_tree.itemSelectionChanged.connect(self.update_details)
        self.view.task_tree.set_drop_callback(self.sync_task_order_from_tree)
        self.view.task_tree.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        self.view.task_tree.customContextMenuRequested.connect(self.show_task_tree_context_menu)
        self.view.run_btn.clicked.connect(self.run_project)
        self.view.run_selected_btn.clicked.connect(self.run_selected_task)
        self.view.validate_btn.clicked.connect(self.validate_project)

    def add_menu_file(self):
        """Adds the File menu to the view."""
        menu_file = self.view.add_menu_parent("File")
        action_new = self.create_action("New Project", icon_path=ui_res_lib.Icon.ui_new)
        action_new.setToolTip("Create a new batch project.")
        action_new.triggered.connect(self.new_project)
        action_open = self.create_action("Open Project", icon_path=ui_res_lib.Icon.ui_open)
        action_open.setToolTip("Open an existing .batch project.")
        action_open.triggered.connect(self.open_project)
        action_save = self.create_action("Save Project", icon_path=ui_res_lib.Icon.ui_save)
        action_save.setToolTip("Save the current batch project.")
        action_save.triggered.connect(self.save_project)
        action_save_as = self.create_action("Save Project As", icon_path=ui_res_lib.Icon.ui_save)
        action_save_as.setToolTip("Save the current batch project to a new file.")
        action_save_as.triggered.connect(self.save_project_as)

        self.view.add_menu_action(parent_menu=menu_file, action=action_new)
        self.view.add_menu_action(parent_menu=menu_file, action=action_open)

        self._recent_projects_menu = self.view.add_menu_submenu(
            parent_menu=menu_file,
            submenu_name="Recent Projects",
            icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open),
        )
        self._recent_projects_menu.aboutToShow.connect(self.refresh_recent_projects_menu)
        self.refresh_recent_projects_menu()

        self.view.add_menu_action(parent_menu=menu_file, action=action_save)
        self.view.add_menu_action(parent_menu=menu_file, action=action_save_as)

        self._templates_menu = self.view.add_menu_submenu(
            parent_menu=menu_file,
            submenu_name="Templates",
            icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates),
        )
        self._template_menu_actions = []
        self._templates_menu.aboutToShow.connect(self.refresh_templates_menu)
        self.refresh_templates_menu()

        action_import_project = self.create_action("Import Project", icon_path=ui_res_lib.Icon.ui_open)
        action_import_project.setToolTip(
            "Import all tasks from an existing .batch project and append them to the current project. "
            "Only the tasks and their settings are imported; project settings are discarded."
        )
        action_import_project.triggered.connect(self.import_project)
        self.view.add_menu_action(parent_menu=menu_file, action=action_import_project)

    def refresh_templates_menu(self):
        """Rebuilds the template submenu from the current template directory."""
        if not ui_qt_utils.is_qt_object_valid(getattr(self, "_templates_menu", None)):
            return

        menu_templates = self._templates_menu
        self._template_menu_actions = []
        menu_templates.clear()
        template_registry = batch_processor_templates.BatchProcessorTemplates(
            include_package_templates=self._show_package_templates
        )

        package_templates = {}
        if self._show_package_templates:
            package_templates = template_registry.get_dict_templates(
                include_file_templates=False,
                include_package_templates=True,
            )
            if package_templates:
                ui_qt_utils.add_labeled_separator(menu=menu_templates, text="Package Templates")
            for name, template_func in package_templates.items():
                formatted_name = self.format_template_name(name)
                action_template = self.create_action(
                    formatted_name,
                    icon_path=get_icon_path(template_registry.icon_package_files),
                )
                action_template.triggered.connect(
                    partial(self.replace_project_from_template, template_func=template_func)
                )
                self._template_menu_actions.append(action_template)
                menu_templates.addAction(action_template)

        user_templates = template_registry.get_dict_templates(include_package_templates=False)
        ui_qt_utils.add_labeled_separator(menu=menu_templates, text="User Templates")
        if not user_templates:
            action_empty_templates = self.create_action("No Templates Found")
            action_empty_templates.setEnabled(False)
            self._template_menu_actions.append(action_empty_templates)
            menu_templates.addAction(action_empty_templates)
        else:
            for name, template_func in user_templates.items():
                formatted_name = self.format_template_name(name)
                action_template = self.create_action(
                    formatted_name,
                    icon_path=get_icon_path(template_registry.icon_files),
                )
                action_template.triggered.connect(
                    partial(self.replace_project_from_template, template_func=template_func)
                )
                self._template_menu_actions.append(action_template)
                menu_templates.addAction(action_template)

        ui_qt_utils.add_labeled_separator(menu=menu_templates, text="Template Folder")
        action_open_templates = self.create_action("Open Templates Folder", icon_path=ui_res_lib.Icon.util_open_dir)
        action_open_templates.triggered.connect(
            lambda *args: self.open_or_create_directory(batch_processor_templates.get_template_source_dir())
        )
        self._template_menu_actions.append(action_open_templates)
        menu_templates.addAction(action_open_templates)

        action_save_template = self.create_action("Save Current as Template", icon_path=ui_res_lib.Icon.ui_templates)
        action_save_template.setToolTip("Save a copy of the current project as a reusable template.")
        action_save_template.triggered.connect(self.save_current_project_as_template)
        self._template_menu_actions.append(action_save_template)
        menu_templates.addAction(action_save_template)

        action_show_package_templates = self.create_action("Show Package Templates")
        action_show_package_templates.setCheckable(True)
        action_show_package_templates.setChecked(self._show_package_templates)
        action_show_package_templates.triggered.connect(self.set_show_package_templates)
        self._template_menu_actions.append(action_show_package_templates)
        menu_templates.addAction(action_show_package_templates)

    def set_show_package_templates(self, is_checked):
        """Stores the package-template menu state and refreshes its contents.

        Args:
            is_checked (bool): Whether package templates should be displayed.
        """
        self._show_package_templates = bool(is_checked)
        self._prefs.set_bool(
            key=constants.Project.PREFS_KEY_SHOW_PACKAGE_TEMPLATES,
            value=self._show_package_templates,
        )
        self._prefs.save()
        ui_qt.QtCore.QTimer.singleShot(0, self.refresh_templates_menu)

    def refresh_recent_projects_menu(self):
        """Rebuilds the recent-project submenu from stored preferences."""
        self._recent_projects_menu.clear()
        recent_paths = self._recent_projects.get_paths()
        if not recent_paths:
            empty_action = self.create_action("No Recent Projects")
            empty_action.setEnabled(False)
            self._recent_projects_menu.addAction(empty_action)
            return
        for index, file_path in enumerate(recent_paths, start=1):
            action_recent = self.create_action(f"{index}. {file_path}", icon_path=ui_res_lib.Icon.ui_open)
            action_recent.setToolTip(file_path)
            action_recent.triggered.connect(partial(self.load_project_from_path, file_path))
            self._recent_projects_menu.addAction(action_recent)
        self._recent_projects_menu.addSeparator()
        action_clear = self.create_action("Clear Recent Projects", icon_path=ui_res_lib.Icon.ui_delete)
        action_clear.triggered.connect(self.clear_recent_projects)
        self._recent_projects_menu.addAction(action_clear)

    def clear_recent_projects(self):
        """Clears the stored recent-project list and refreshes its menu."""
        self._recent_projects.clear()
        self.refresh_recent_projects_menu()
        self.log_status("Cleared recent projects.")

    @staticmethod
    def open_or_create_directory(directory_path, *args):
        """Creates a directory when missing, then opens it in the system file browser.

        Args:
            directory_path (str): Directory path to open.
            *args: Optional Qt signal arguments.
        """
        if not directory_path:
            sys.stdout.write("Unable to open directory. Path was empty.\n")
            return
        directory_path = os.path.abspath(os.path.expanduser(str(directory_path)))
        if not os.path.isdir(directory_path):
            try:
                os.makedirs(directory_path, exist_ok=True)
                sys.stdout.write('Created directory: "{0}"\n'.format(directory_path))
            except OSError as exception:
                sys.stdout.write('Unable to create directory "{0}". Issue: {1}\n'.format(directory_path, exception))
                return
        if not os.path.isdir(directory_path):
            sys.stdout.write('Unable to open directory. Path does not exist: "{0}"\n'.format(directory_path))
            return
        utils_system.open_file_dir(directory_path)

    def add_menu_tasks(self):
        """Adds the categorized Tasks menu to the view."""
        menu_tasks = self.view.add_menu_parent("Tasks")
        category_icons = tasks.get_task_category_icons()
        for category_name, task_classes in tasks.get_task_categories().items():
            category_icon = category_icons.get(category_name) or ui_res_lib.Icon.batch_task_generic
            category_menu = self.view.add_menu_submenu(
                parent_menu=menu_tasks,
                submenu_name=category_name,
                icon=ui_qt.QtGui.QIcon(category_icon),
            )
            ui_qt_utils.add_labeled_separator(menu=category_menu, text=category_name)
            for task_class in task_classes:
                task_icon = task_class.icon
                action_task = self.create_action(task_class.default_display_name, icon_path=task_icon)
                action_task.setToolTip("Add a {0} task to the project.".format(task_class.default_display_name))
                action_task.triggered.connect(partial(self.add_task_by_type, task_type=task_class.task_type))
                self.view.add_menu_action(parent_menu=category_menu, action=action_task)

    def add_menu_utils(self):
        """Adds utilities actions to the view menu bar."""
        menu_utils = self.view.add_menu_parent("Utilities")
        ui_qt_utils.add_labeled_separator(menu=menu_utils, text="Project")

        action_open_project_folder = self.create_action(
            "Open Project Folder",
            icon_path=ui_res_lib.Icon.ui_open_external,
        )
        action_open_project_folder.setToolTip("Open the resolved project directory.")
        action_open_project_folder.triggered.connect(self.open_project_directory)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_open_project_folder)

        action_get_environment_vars = self.create_action(
            "Get Environment Variables", icon_path=ui_res_lib.Icon.ui_env_var
        )
        action_get_environment_vars.setToolTip("Show resolved batch environment variables.")
        action_get_environment_vars.triggered.connect(self.show_environment_variables)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_get_environment_vars)

        action_validate = self.create_action(
            "Validate Project", icon_path=ui_res_lib.Icon.batch_validator_pass
        )
        action_validate.setToolTip("Validate the active batch project.")
        action_validate.triggered.connect(self.validate_project)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_validate)

        ui_qt_utils.add_labeled_separator(menu=menu_utils, text="Task Execution")

        action_print_selected_index = self.create_action(
            "Print Selected Task Index",
            icon_path=ui_res_lib.Icon.batch_task_log_print,
        )
        action_print_selected_index.setToolTip(
            "Print the selected task's project index and task-variable index."
        )
        action_print_selected_index.triggered.connect(self.print_selected_task_index)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_print_selected_index)

        action_run_selected = self.create_action(
            "Run Selected Task", icon_path=ui_res_lib.Icon.batch_task_log_print
        )
        action_run_selected.setToolTip("Run only the selected task.")
        action_run_selected.triggered.connect(self.run_selected_task)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_run_selected)

        action_run_from_selected = self.create_action(
            "Run From Selected Task", icon_path=ui_res_lib.Icon.batch_task_log_print
        )
        action_run_from_selected.setToolTip("Run from the selected task through the end of the project.")
        action_run_from_selected.triggered.connect(self.run_from_selected)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_run_from_selected)

        ui_qt_utils.add_labeled_separator(menu=menu_utils, text="Cleanup")

        action_purge_task_files = self.create_action("Purge Task Directory Files", icon_path=ui_res_lib.Icon.ui_delete)
        action_purge_task_files.setToolTip("Delete all files under the configured task directory after confirmation.")
        action_purge_task_files.triggered.connect(self.purge_task_directory_files)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_purge_task_files)

        action_purge_output_files = self.create_action(
            "Purge Output Directory Files", icon_path=ui_res_lib.Icon.ui_delete
        )
        action_purge_output_files.setToolTip(
            "Delete all files under the configured output directory after confirmation."
        )
        action_purge_output_files.triggered.connect(self.purge_output_directory_files)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_purge_output_files)

    def add_menu_preferences(self):
        """Adds the Preferences menu with the toolkit automation toggles."""
        menu_preferences = self.view.add_menu_parent("Preferences")

        self.create_menu_checkbox_action(
            parent_menu=menu_preferences,
            text="Convert Absolute Paths to Relative",
            checked=self._convert_abs_paths_to_relative,
            tooltip=(
                "When browsing for paths inside {project-dir}, replace the absolute project folder with "
                "{project-dir}."
            ),
            callback=self.toggle_convert_abs_paths_to_relative,
        )

        self.create_menu_checkbox_action(
            parent_menu=menu_preferences,
            text="Flag Skipped Tasks in Single-Instance Log",
            checked=self._flag_skipped_tasks,
            tooltip="Print explicit log warnings when single-instance processing skips work.",
            callback=self.toggle_flag_skipped_tasks,
        )

        self.create_menu_checkbox_action(
            parent_menu=menu_preferences,
            text="Ignore Disabled Tasks for Index",
            checked=self._ignore_disabled_tasks_for_task_index,
            tooltip=(
                "Exclude disabled tasks when resolving index variables such as {task-idx}. "
                "When unchecked, disabled tasks keep their place in the task index."
            ),
            callback=self.toggle_ignore_disabled_tasks_for_task_index,
        )

        self.create_menu_checkbox_action(
            parent_menu=menu_preferences,
            text="Confirm Task Delete",
            checked=self._confirm_delete_task,
            tooltip="Ask for confirmation before deleting a task from the right-click menu or task panel.",
            callback=self.toggle_confirm_delete_task,
        )

        self.create_menu_checkbox_action(
            parent_menu=menu_preferences,
            text="Auto-Segment Imported Projects",
            checked=self._auto_segment_imported_projects,
            tooltip=(
                "When importing a project whose first task is an Input Files task, automatically start a "
                "new segment on it and name the segment after the imported project."
            ),
            callback=self.toggle_auto_segment_imported_projects,
        )

    def open_project_directory(self, *args):
        """Opens the resolved project directory in the system file browser.

        Args:
            *args: Optional Qt signal arguments.
        """
        configured_path = self.model.environment_variables.get("project-dir", "")
        if not str(configured_path or "").strip():
            self.log_status(
                "Warning: Unable to open directory because the path field is empty.",
                status="warning",
            )
            return
        resolved_path = self.model.resolve_template_path(configured_path)
        directory_path = resolved_path
        if os.path.isfile(directory_path):
            directory_path = os.path.dirname(directory_path)
        if not os.path.isdir(directory_path):
            message = f"Target folder does not exist:\n{directory_path or resolved_path or '<empty>'}"
            ui_qt.QtWidgets.QMessageBox.warning(
                self.view,
                "Target Folder Missing",
                message,
            )
            self.log_status(
                f"Warning: Unable to open directory because the path does not exist: {directory_path}",
                status="warning",
            )
            return
        try:
            utils_system.open_file_dir(directory_path)
            self.log_status(f"Opened directory: {directory_path}")
        except Exception as exception:
            self.log_status(f"Unable to open directory: {exception}")

    def add_menu_logging(self):
        """Adds logging actions to the view menu bar."""
        menu_logging = self.view.add_menu_parent("Logging")
        action_open_logs_win = self.create_action("Open Logs Window", icon_path=ui_res_lib.Icon.ui_templates)
        action_open_logs_win.setToolTip("Open the Batch Processor log window.")
        action_open_logs_win.triggered.connect(self.log_view.show_if_not_visible)
        self.view.add_menu_action(parent_menu=menu_logging, action=action_open_logs_win)

        action_clear_logs = self.create_action("Clear Logs", icon_path=ui_res_lib.Icon.ui_delete)
        action_clear_logs.setToolTip("Clear the Batch Processor log window.")
        action_clear_logs.triggered.connect(self.log_view.clear_log_widget)
        self.view.add_menu_action(parent_menu=menu_logging, action=action_clear_logs)

    def add_menu_help(self):
        """Adds help actions to the view menu bar."""
        menu_help = self.view.add_menu_parent("Help")
        package_docs_url = "https://github.com/TrevisanGMW/gt-tools/tree/release/docs"
        action_open_package_docs = self.create_action(
            "Open GT-Tools Documentation", icon_path=ui_res_lib.Icon.root_help
        )
        action_open_package_docs.triggered.connect(partial(utils_request.open_url_in_browser, package_docs_url))
        self.view.add_menu_action(parent_menu=menu_help, action=action_open_package_docs)

    def create_action(self, text, icon_path=None):
        """Creates a QAction compatible with PySide2 and PySide6.

        Args:
            text (str): Action label.
            icon_path (str, optional): Optional icon path.

        Returns:
            QAction: Created action.
        """
        if icon_path:
            return ui_qt.QtLib.QtGui.QAction(ui_qt.QtGui.QIcon(icon_path), text, self.view)
        return ui_qt.QtLib.QtGui.QAction(text, self.view)

    def create_menu_checkbox_action(self, parent_menu, text, checked, tooltip, callback):
        """Adds a checkbox row to a menu and connects it to a callback.

        Args:
            parent_menu (QMenu): Menu receiving the checkbox action.
            text (str): Checkbox label.
            checked (bool): Initial state.
            tooltip (str): Tooltip text.
            callback (callable): Function called with the checkbox state.

        Returns:
            QWidgetAction: Created widget action.
        """
        widget_action = ui_qt.QtWidgets.QWidgetAction(parent_menu)
        container = ui_qt.QtWidgets.QWidget(parent_menu)
        layout = ui_qt.QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 12, 4)
        layout.setSpacing(6)
        checkbox = ui_qt.QtWidgets.QCheckBox(text)
        checkbox.setMinimumHeight(24)
        checkbox.setChecked(bool(checked))
        checkbox.setToolTip(tooltip)
        container.setToolTip(tooltip)
        checkbox.toggled.connect(callback)
        layout.addWidget(checkbox)
        widget_action.setDefaultWidget(container)
        self.view.add_menu_action(parent_menu=parent_menu, action=widget_action)
        self.view.menu_items.append(container)
        self.view.menu_items.append(checkbox)
        return widget_action

    def toggle_convert_abs_paths_to_relative(self, checked):
        """Stores whether browsed absolute paths should become project-relative templates.

        Args:
            checked (bool): New preference state.
        """
        self._convert_abs_paths_to_relative = bool(checked)
        self._prefs.set_bool(
            key=constants.Project.PREFS_KEY_CONVERT_ABS_PATHS_TO_RELATIVE,
            value=self._convert_abs_paths_to_relative,
        )
        self._prefs.set_bool(key="on_set_path_abs_to_relative", value=self._convert_abs_paths_to_relative)
        self._prefs.save()
        state_name = "enabled" if self._convert_abs_paths_to_relative else "disabled"
        self.log_status("Convert Absolute Paths to Relative {0}.".format(state_name))

    def toggle_confirm_delete_task(self, checked):
        """Stores whether deleting a task should ask for confirmation.

        Args:
            checked (bool): New preference state.
        """
        self._confirm_delete_task = bool(checked)
        self._prefs.set_bool(
            key=constants.Project.PREFS_KEY_CONFIRM_DELETE_TASK,
            value=self._confirm_delete_task,
        )
        self._prefs.save()
        state_name = "enabled" if self._confirm_delete_task else "disabled"
        self.log_status("Task delete confirmation {0}.".format(state_name))

    def toggle_flag_skipped_tasks(self, checked):
        """Stores whether skipped tasks should emit explicit tracker warnings.

        Args:
            checked (bool): New preference state.
        """
        self._flag_skipped_tasks = bool(checked)
        self._prefs.set_bool(
            key=constants.Project.PREFS_KEY_FLAG_SKIPPED_TASKS,
            value=self._flag_skipped_tasks,
        )
        self._prefs.save()
        state_name = "enabled" if self._flag_skipped_tasks else "disabled"
        self.log_status("Skipped task tracker warnings {0}.".format(state_name))

    def toggle_ignore_disabled_tasks_for_task_index(self, checked):
        """Stores whether disabled tasks should be excluded from task indexes.

        Args:
            checked (bool): New preference state.
        """
        self._ignore_disabled_tasks_for_task_index = bool(checked)
        self._prefs.set_bool(
            key=constants.Project.PREFS_KEY_IGNORE_DISABLED_TASKS_FOR_TASK_INDEX,
            value=self._ignore_disabled_tasks_for_task_index,
        )
        self._prefs.save()
        self.apply_task_index_automation()
        self.refresh_widgets()
        state_name = "ignored" if self._ignore_disabled_tasks_for_task_index else "included"
        self.log_status(f"Disabled tasks are now {state_name} when resolving task indexes.")

    def toggle_auto_segment_imported_projects(self, checked):
        """Stores whether importing a project should start a new segment automatically.

        Args:
            checked (bool): New preference state.
        """
        self._auto_segment_imported_projects = bool(checked)
        self._prefs.set_bool(
            key=constants.Project.PREFS_KEY_AUTO_SEGMENT_IMPORTED_PROJECTS,
            value=self._auto_segment_imported_projects,
        )
        self._prefs.save()
        state_name = "enabled" if self._auto_segment_imported_projects else "disabled"
        self.log_status("Auto-segment imported projects {0}.".format(state_name))

    def apply_task_index_automation(self):
        """Applies the global disabled-task indexing preference to the active project."""
        self.model.run_settings["ignore_disabled_tasks_for_task_index"] = bool(
            self._ignore_disabled_tasks_for_task_index
        )

    def get_convert_abs_paths_to_relative(self):
        """Gets the global project-relative path conversion preference.

        Returns:
            bool: True when browsed paths should be converted to {project-dir} paths.
        """
        return bool(self._convert_abs_paths_to_relative)

    def get_confirm_delete_task(self):
        """Gets whether task delete actions should ask for confirmation.

        Returns:
            bool: True when deletes should be confirmed.
        """
        return bool(self._confirm_delete_task)

    def new_project(self):
        """Creates a new default project."""
        if self.show_unsaved_changes_warning_dialog(window=self.view, is_close_event=False):
            return
        self.model.reset_project()
        self.apply_task_index_automation()
        self.view.set_window_title(prefix=None)
        self.refresh_widgets()
        self.mark_project_clean()
        self.log_status("Created new project.")

    def replace_project_from_template(self, template_func):
        """Replaces the current project with a template project.

        Args:
            template_func (callable): Function returning a BatchProcessorModel.
        """
        if self.show_unsaved_changes_warning_dialog(window=self.view, is_close_event=False):
            return
        template_project = template_func()
        self.model = template_project
        self.apply_task_index_automation()
        self.refresh_widgets()
        self.view.set_window_title(prefix=None)
        self.mark_project_clean()
        self.log_status('Loaded template: "{0}".'.format(template_project.project_name))

    def open_project(self):
        """Opens an existing .batch project."""
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Open Batch Project",
            starting_directory=os.path.expanduser("~"),
            file_filter="Batch Projects (*.batch);;All Files (*);;",
            ok_caption="Open Project",
            cancel_caption="Cancel",
        )
        if file_path:
            return self.load_project_from_path(file_path)
        return False

    def import_project(self):
        """Imports all tasks from an existing project into the current project.

        Prompts for a .batch file and appends its tasks to the bottom of the
        current project. Only the tasks and their settings are imported; the
        source project's own settings are discarded.

        Returns:
            bool: True when tasks were imported.
        """
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Import Batch Project Tasks",
            starting_directory=os.path.expanduser("~"),
            file_filter="Batch Projects (*.batch);;All Files (*);;",
            ok_caption="Import Tasks",
            cancel_caption="Cancel",
        )
        if file_path:
            return self.import_tasks_from_path(file_path)
        return False

    def import_tasks_from_path(self, file_path, *args):
        """Appends every task from a project file to the current project.

        Args:
            file_path (str): Batch project file path to import tasks from.
            *args: Optional Qt signal arguments.

        Returns:
            bool: True when tasks were imported.
        """
        file_path = os.path.abspath(os.path.expanduser(str(file_path or "")))
        if not os.path.isfile(file_path):
            self.show_project_load_warning(
                title="Project Not Found",
                message=f"The project no longer exists:\n\n{file_path}",
            )
            return False
        try:
            imported_model = type(self.model).from_file(file_path)
        except Exception as exception:
            logger.exception('Unable to import batch project tasks: "%s"', file_path)
            self.show_project_load_warning(
                title="Unable to Import Project",
                message=(
                    "The project tasks could not be imported and the current project "
                    f"was preserved.\n\n{exception}"
                ),
            )
            return False
        imported_tasks = list(imported_model.tasks)
        if not imported_tasks:
            self.log_status(f"No tasks found to import from: {file_path}", status="warning")
            return False
        self.apply_auto_segment_on_import(imported_tasks=imported_tasks, imported_model=imported_model)
        for task in imported_tasks:
            self.model.add_task_from_dict(task.to_dict(), reinitialize_id=True)
        self.apply_task_index_automation()
        self.refresh_widgets()
        self.log_status(f"Imported {len(imported_tasks)} task(s) from: {file_path}")
        return True

    def apply_auto_segment_on_import(self, imported_tasks, imported_model):
        """Starts a new segment on an imported project's leading input task.

        When the auto-segment preference is enabled and the first imported task is
        an input task, it is flagged to start a new input list and named after the
        imported project, so the import reads as its own segment.

        Args:
            imported_tasks (list): Tasks being imported, in order.
            imported_model (BatchProcessorModel): Source project providing the name.
        """
        if not self._auto_segment_imported_projects or not imported_tasks:
            return
        first_task = imported_tasks[0]
        if not getattr(first_task, "is_input_task", False):
            return
        first_task.settings["start_new_input_list"] = True
        first_task.settings["force_segment_separator"] = True
        project_name = str(getattr(imported_model, "project_name", "") or "").strip()
        if project_name:
            first_task.settings["segment_name"] = project_name

    def load_project_from_path(self, file_path, *args):
        """Safely loads a project path after validating it and protecting changes.

        Args:
            file_path (str): Batch project file path to load.
            *args: Optional Qt signal arguments.

        Returns:
            bool: True when the project was loaded.
        """
        file_path = self._recent_projects.normalize_path(file_path)
        if not os.path.isfile(file_path):
            self._recent_projects.remove_path(file_path)
            self.refresh_recent_projects_menu()
            self.show_project_load_warning(
                title="Project Not Found",
                message=f'The project no longer exists:\n\n{file_path}',
            )
            return False
        if self.show_unsaved_changes_warning_dialog(window=self.view, is_close_event=False):
            return False
        try:
            loaded_model = type(self.model).from_file(file_path)
        except Exception as exception:
            logger.exception('Unable to load batch project: "%s"', file_path)
            self.show_project_load_warning(
                title="Unable to Open Project",
                message=f'The project could not be opened and the current project was preserved.\n\n{exception}',
            )
            return False
        self.model = loaded_model
        self.apply_task_index_automation()
        self.refresh_widgets()
        self.view.set_window_title(prefix=os.path.basename(file_path))
        self.mark_project_clean()
        self._recent_projects.add_path(file_path)
        self.refresh_recent_projects_menu()
        self.log_status(f"Loaded project: {file_path}")
        return True

    def show_project_load_warning(self, title, message):
        """Shows a blocking warning for an invalid recent project.

        Args:
            title (str): Warning dialog title.
            message (str): Warning dialog message.
        """
        message_box = ui_qt.QtWidgets.QMessageBox(self.view)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        try:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Warning)
        except AttributeError:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Icon.Warning)
        message_box.exec_()
        self.log_status(message.replace("\n", " "), status="warning")

    def save_project(self):
        """Saves the current project."""
        if not self.model.project_file_path:
            return self.save_project_as()
        self.model.save_to_file()
        self.view.set_window_title(prefix=os.path.basename(self.model.project_file_path))
        self.mark_project_clean()
        self._recent_projects.add_path(self.model.project_file_path)
        self.refresh_recent_projects_menu()
        self.log_status("Saved project: {0}".format(self.model.project_file_path))
        return True

    def save_project_as(self):
        """Prompts for a destination and saves the current project."""
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Save Batch Project",
            write_mode=True,
            starting_directory=os.path.expanduser("~"),
            file_filter="Batch Projects (*.batch);;All Files (*);;",
            ok_caption="Save Project",
            cancel_caption="Cancel",
        )
        if file_path:
            saved_path = self.model.save_to_file(file_path)
            self.view.set_window_title(prefix=os.path.basename(saved_path))
            self.mark_project_clean()
            self._recent_projects.add_path(saved_path)
            self.refresh_recent_projects_menu()
            self.log_status("Saved project: {0}".format(saved_path))
            return True
        return False

    def save_current_project_as_template(self, *args):
        """Saves the current project as a reusable template project file.

        Args:
            *args: Optional Qt signal arguments.

        Returns:
            bool: True when the template was created.
        """
        template_name = self.get_template_name_from_dialog(default_name=self.model.project_name)
        if not template_name:
            return False

        template_source_dir = batch_processor_templates.get_template_source_dir()
        template_path = os.path.join(template_source_dir, f"{template_name}{constants.Project.EXTENSION}")
        if os.path.isfile(template_path) and not self.show_template_overwrite_warning(template_path):
            return False

        try:
            saved_template_path = batch_processor_templates.save_project_template(
                project=self.model,
                template_path=template_path,
            )
        except (OSError, TypeError, ValueError) as exception:
            self.show_project_load_warning(
                title="Unable to Save Template",
                message=f"The template could not be saved:\n\n{exception}",
            )
            return False

        logger.info(f'Created batch project template "{saved_template_path}".')
        self.log_status(f"Saved template: {saved_template_path}")
        ui_qt.QtCore.QTimer.singleShot(0, self.refresh_templates_menu)
        return True

    def get_template_name_from_dialog(self, default_name):
        """Prompts the user for a safe name for a new project template.

        Args:
            default_name (str): Initial template name shown to the user.

        Returns:
            str: Sanitized template name without the project extension, or an
            empty string when cancelled or invalid.
        """
        template_name, accepted = ui_qt.QtWidgets.QInputDialog.getText(
            self.view,
            "Save Current as Template",
            "Template Name:",
            text=default_name or constants.Project.DEFAULT_NAME,
        )
        if not accepted:
            return ""

        template_name = tasks.sanitize_filename(template_name, fallback="")
        if template_name.lower().endswith(constants.Project.EXTENSION):
            template_name = template_name[: -len(constants.Project.EXTENSION)]
        if template_name:
            return template_name

        self.show_project_load_warning(
            title="Invalid Template Name",
            message="Enter a valid name for the template.",
        )
        return ""

    def show_template_overwrite_warning(self, template_path):
        """Asks the user before replacing an existing template project file.

        Args:
            template_path (str): Existing template file that would be replaced.

        Returns:
            bool: True when the existing template may be replaced.
        """
        result = ui_qt.QtWidgets.QMessageBox.question(
            self.view,
            "Replace Existing Template",
            f"A template already exists at:\n\n{template_path}\n\nReplace its project data?",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return result == ui_qt.QtLib.StandardButton.Yes

    def add_task_by_type(self, task_type):
        """Adds a new task to the project.

        Args:
            task_type (str): Task type key.
        """
        new_task = self.model.add_task_by_type(task_type)
        self.refresh_widgets()
        self.view.select_task_by_id(new_task.id)
        self.update_details()
        self.log_status('Added task: "{0}".'.format(new_task.display_name))

    def show_environment_variables(self):
        """Shows resolved project environment variables."""
        task_id = self.view.get_selected_task_id()
        task = self.model.get_task(task_id) if task_id else None
        task_index = self.model.get_task_environment_index(task) if task else None
        environment_variables = self.model.get_environment_variables(
            task=task,
            task_index=task_index,
            include_braces=True,
        )
        output_window = ui_python_output_view.PythonOutputView(parent=self.view, editable=False)
        output_window.setWindowTitle("Batch Project Environment Variables")
        output_window.set_python_output_text(json.dumps(environment_variables, indent=4, sort_keys=True))
        output_window.show()
        self.log_status("Opened environment variables window.")

    def validate_project(self):
        """Validates the current project and updates the view."""
        result = self.model.validate_project()
        input_count = len(self.model.discover_input_files())
        lines = []
        lines.append("Detected Input Files: {0}".format(input_count))
        lines.extend(["Error: {0}".format(error) for error in result.errors])
        lines.extend(["Warning: {0}".format(warning) for warning in result.warnings])
        if len(lines) == 1:
            lines.append("Project is valid.")
        self.append_log("\n".join(lines))
        self.log_status(
            "Validation finished: {0} input file(s), {1} error(s), {2} warning(s).".format(
                input_count, len(result.errors), len(result.warnings)
            )
        )

    def print_selected_task_index(self):
        """Prints the selected task's project and environment-variable indices."""
        task_id = self.view.get_selected_task_id()
        task = self.model.get_task(task_id) if task_id else None
        if not task:
            self.log_status("No task selected. Select a task to print its indices.", status="warning")
            return
        project_index = self.model.tasks.index(task) + 1
        task_index = self.model.get_task_environment_index(task)
        index_state = "Included" if task.includes_task_index() else "Excluded"
        message = "{0} Task: Project Index: {1}, Task Index: {2}, Index Count: {3}".format(
            task.display_name,
            project_index,
            task_index,
            index_state,
        )
        self.log_status(message)

    def show_unsaved_changes_warning_dialog(self, window, is_close_event=True, *args, **kwargs):
        """Shows a save warning dialog when the project has unsaved changes.

        Args:
            window (QDialog): Window receiving the dialog.
            is_close_event (bool or QCloseEvent, optional): Whether this was called by a close event. The
                native event is received here when the standalone view calls this function.
            *args: Optional close event arguments.
            **kwargs: Optional keyword arguments.

        Returns:
            bool: True if the pending operation was cancelled.
        """
        close_event = kwargs.get("close_event")
        if isinstance(is_close_event, ui_qt.QtGui.QCloseEvent):
            close_event = is_close_event
            is_close_event = True

        if not self.has_unsaved_changes():
            return False
        dialog_parent = window if ui_qt_utils.is_qt_object_valid(window) else None
        if window and not dialog_parent:
            logger.debug("Showing the Batch Processor unsaved-changes dialog without its stale Qt parent.")
        try:
            message_box = ui_qt.QtWidgets.QMessageBox(dialog_parent)
            message_box.setWindowTitle("Warning: Unsaved changes!")
            message_box.setText("You have unsaved changes. What do you want to do?")
            save_button = message_box.addButton("Save", ui_qt.QtWidgets.QMessageBox.AcceptRole)
            dont_save_button = message_box.addButton("Don't Save", ui_qt.QtWidgets.QMessageBox.DestructiveRole)
            cancel_button = message_box.addButton("Cancel", ui_qt.QtWidgets.QMessageBox.DestructiveRole)
            message_box.exec_()
            clicked_button = message_box.clickedButton()
        except RuntimeError as exception:
            if "Internal C++ object" not in str(exception) or "already deleted" not in str(exception):
                raise
            logger.debug(f"Skipped stale Batch Processor dialog parent. Issue: {exception}")
            return False
        if clicked_button == save_button:
            if not self.save_project():
                self.cancel_pending_close(
                    window=window,
                    is_close_event=is_close_event,
                    close_args=args,
                    close_event=close_event,
                )
                return True
            return False
        if clicked_button == dont_save_button:
            return False
        if clicked_button == cancel_button:
            self.cancel_pending_close(
                window=window,
                is_close_event=is_close_event,
                close_args=args,
                close_event=close_event,
            )
            return True
        return False

    def cancel_pending_close(self, window, is_close_event=True, close_args=None, close_event=None):
        """Cancels a pending close event when requested by the user.

        Args:
            window (QDialog): Window being closed.
            is_close_event (bool, optional): Whether a close event is active.
            close_args (tuple, optional): Close callback arguments.
            close_event (QCloseEvent, optional): Native close event when available.
        """
        if not is_close_event:
            return
        close_events = list(close_args or [])
        if close_event is not None:
            close_events.append(close_event)
        for pending_close_event in close_events:
            if isinstance(pending_close_event, ui_qt.QtGui.QCloseEvent):
                pending_close_event.ignore()
        if window and ui_qt_utils.is_qt_object_valid(window):
            ui_qt.QtCore.QTimer.singleShot(100, partial(window.setVisible, True))

    def mark_project_clean(self):
        """Stores an independent copy of the current project as the clean state."""
        self._saved_project_state = copy.deepcopy(self.model.to_dict())

    def has_unsaved_changes(self):
        """Checks whether the current project differs from the last clean state.

        Returns:
            bool: True if project data changed.
        """
        if self._saved_project_state is None:
            return False
        return self.model.to_dict() != self._saved_project_state

    def run_project(self):
        """Runs the current project from the first process task."""
        self._run_project()

    def run_from_selected(self):
        """Runs the current project from the selected process task."""
        self._run_project(run_from_task_id=self.view.get_selected_task_id())

    def run_selected_task(self):
        """Runs only the selected process task."""
        selected_task_id = self.view.get_selected_task_id()
        self._run_project(run_from_task_id=selected_task_id, run_to_task_id=selected_task_id)

    def purge_task_directory_files(self):
        """Deletes files under the configured task directory after confirmation."""
        self.purge_directory_files(
            directory_path=self.model.resolve_template_path("{project-dir}/{task-dir}"),
            label="Task",
            protected_paths=[
                self.model.get_project_dir(),
                self.model.resolve_template_path("{project-dir}/{input-dir}"),
                self.model.resolve_template_path("{project-dir}/{output-dir}"),
            ],
        )

    def purge_output_directory_files(self):
        """Deletes files under the configured output directory after confirmation."""
        self.purge_directory_files(
            directory_path=self.model.resolve_template_path("{project-dir}/{output-dir}"),
            label="Output",
            protected_paths=[
                self.model.get_project_dir(),
                self.model.resolve_template_path("{project-dir}/{input-dir}"),
                self.model.resolve_template_path("{project-dir}/{task-dir}"),
            ],
        )

    def purge_directory_files(self, directory_path, label, protected_paths=None):
        """Deletes files under a directory after confirmation.

        Args:
            directory_path (str): Directory to purge.
            label (str): User-facing directory label.
            protected_paths (list, optional): Directories that must not be purged.
        """
        if not os.path.isdir(directory_path):
            self.log_status("{0} directory does not exist: {1}".format(label, directory_path))
            return
        protected_paths = protected_paths or []
        normalized_directory = os.path.normcase(os.path.abspath(directory_path))
        for protected_path in protected_paths:
            if normalized_directory == os.path.normcase(os.path.abspath(protected_path)):
                self.log_status("Refusing to purge protected directory: {0}".format(directory_path))
                return
        file_paths = []
        for root, _, file_names in os.walk(directory_path):
            for file_name in file_names:
                file_paths.append(os.path.join(root, file_name))
        if not file_paths:
            self.log_status("{0} directory has no files to purge: {1}".format(label, directory_path))
            return
        message_box = ui_qt.QtWidgets.QMessageBox(self.view)
        message_box.setWindowTitle("Purge {0} Directory Files?".format(label))
        message_box.setText(
            "Delete {0} file(s) under the {1} directory?\n\n{2}".format(
                len(file_paths), label.lower(), directory_path
            )
        )
        message_box.setIconPixmap(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete).pixmap(64, 64))
        message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
        message_box.addButton(ui_qt.QtLib.StandardButton.No)
        exec_method = getattr(message_box, "exec_", None)
        if not exec_method:
            exec_method = getattr(message_box, "exec")
        result = exec_method()
        if result != ui_qt.QtLib.StandardButton.Yes:
            self.log_status("Purge {0} directory cancelled.".format(label.lower()))
            return
        deleted_count = 0
        for file_path in file_paths:
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted_count += 1
        for root, dir_names, _ in os.walk(directory_path, topdown=False):
            for dir_name in dir_names:
                dir_path = os.path.join(root, dir_name)
                try:
                    os.rmdir(dir_path)
                except OSError:
                    pass
        self.log_status(
            "Purged {0} file(s) from {1} directory: {2}".format(
                deleted_count, label.lower(), directory_path
            )
        )

    def refresh_widgets(self):
        """Refreshes tree and details widgets."""
        self.view.refresh_tree(self.model)
        self.update_details()

    def refresh_task_tree_item(self, task_id):
        """Refreshes one existing task tree item without rebuilding its details widget.

        Args:
            task_id (str): Identifier of the task to refresh.

        Returns:
            bool: True when the task and its tree item were found.
        """
        task = self.model.get_task(task_id)
        if not task:
            return False
        return self.view.update_task_tree_item(task)

    def update_details(self):
        """Updates the details panel for the current selection."""
        if self.view.is_segment_separator_selected():
            segment_name = self.view.get_selected_segment_name()
            self.view.set_task_widget(self.build_separator_details_widget(segment_name))
            return
        task_id = self.view.get_selected_task_id()
        if not task_id:
            widget_object = AttrWidgetProject(
                project=self.model,
                refresh_parent_func=self.refresh_widgets,
                controller=self,
            )
            self.view.set_task_widget(widget_object)
            return

        task = self.model.get_task(task_id)
        if not task:
            self.view.clear_task_widget()
            return
        widget_class = get_task_widget_class(task)
        widget_object = widget_class(
            task=task,
            project=self.model,
            refresh_parent_func=self.refresh_widgets,
            controller=self,
        )
        self.view.set_task_widget(widget_object)

    def build_separator_details_widget(self, segment_name):
        """Builds a centered, greyed-out details panel for a segment separator row.

        Args:
            segment_name (str): Name of the segment the separator labels.

        Returns:
            QWidget: Details widget.
        """
        container = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        grey_color = ui_res_lib.Color.Hex.gray_dim
        title_label = ui_qt.QtWidgets.QLabel("Segment Separator")
        title_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: {0}; font-size: 15pt;".format(grey_color))
        title_label.setWordWrap(True)
        name_label = ui_qt.QtWidgets.QLabel(segment_name or "New Segment")
        name_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(
            "color: {0}; font-size: 18pt; font-weight: bold;".format(ui_res_lib.Color.Hex.white)
        )
        name_label.setWordWrap(True)
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addWidget(name_label)
        layout.addStretch()
        return container

    def sync_task_order_from_tree(self):
        """Synchronizes model task order after a tree drag/drop operation."""
        project_item = self.view.project_item
        if not project_item:
            return
        task_by_id = {task.id: task for task in self.model.tasks}
        ordered_tasks = []
        for index in range(project_item.childCount()):
            task_id = project_item.child(index).data(0, self.view.DATA_ROLE)
            task = task_by_id.get(task_id)
            if not task:
                continue
            ordered_tasks.append(task)
        if len(ordered_tasks) == len(self.model.tasks):
            self.model.tasks = ordered_tasks
        self.refresh_widgets()

    def show_task_tree_context_menu(self, position):
        """Shows task actions for the task tree right-click menu.

        Args:
            position (QPoint): Tree viewport position for the context-menu request.
        """
        item = self.view.task_tree.itemAt(position)
        if item is None:
            return
        item_data = item.data(0, self.view.DATA_ROLE)
        source_task = None
        if item_data != "project":
            source_task = self.model.get_task(item_data)

        menu = ui_qt.QtWidgets.QMenu()

        action_duplicate = self.create_action("Duplicate", icon_path=ui_res_lib.Icon.rigger_action_duplicate)
        action_duplicate.triggered.connect(partial(self.context_menu_duplicate_task, source_task))
        self.view.add_menu_action(parent_menu=menu, action=action_duplicate)

        action_copy = self.create_action("Copy", icon_path=ui_res_lib.Icon.rigger_action_copy)
        action_copy.triggered.connect(partial(self.context_menu_copy_task, source_task))
        self.view.add_menu_action(parent_menu=menu, action=action_copy)

        action_paste = self.create_action("Paste", icon_path=ui_res_lib.Icon.rigger_action_paste)
        action_paste.triggered.connect(self.context_menu_paste_task)
        self.view.add_menu_action(parent_menu=menu, action=action_paste)

        action_export = self.create_action("Export", icon_path=ui_res_lib.Icon.rigger_action_export)
        action_export.triggered.connect(partial(self.context_menu_export_task, source_task))
        self.view.add_menu_action(parent_menu=menu, action=action_export)

        action_import = self.create_action("Import", icon_path=ui_res_lib.Icon.rigger_action_import)
        action_import.triggered.connect(self.context_menu_import_task)
        self.view.add_menu_action(parent_menu=menu, action=action_import)

        menu.addSeparator()

        action_delete = self.create_action("Delete", icon_path=ui_res_lib.Icon.ui_delete)
        action_delete.triggered.connect(partial(self.context_menu_delete_task, source_task))
        self.view.add_menu_action(parent_menu=menu, action=action_delete)

        if not source_task:
            action_duplicate.setEnabled(False)
            action_copy.setEnabled(False)
            action_export.setEnabled(False)
            action_delete.setEnabled(False)
        elif not getattr(source_task, "can_be_removed", True):
            action_delete.setEnabled(False)

        exec_method = getattr(menu, "exec_", None)
        if not exec_method:
            exec_method = getattr(menu, "exec")
        exec_method(self.view.task_tree.viewport().mapToGlobal(position))

    def context_menu_duplicate_task(self, source_task):
        """Duplicates a task from the task-tree context menu.

        Args:
            source_task (BatchTask): Source task to duplicate.
        """
        if not source_task:
            self.log_status("No task selected to duplicate.", status="warning")
            return
        duplicated_task = self.model.duplicate_task(source_task.id)
        if not duplicated_task:
            self.log_status('Unable to duplicate task "{0}".'.format(source_task.display_name), status="warning")
            return
        self.refresh_widgets()
        self.view.select_task_by_id(duplicated_task.id)
        self.log_status('Duplicated task: "{0}".'.format(source_task.display_name))

    def context_menu_copy_task(self, source_task):
        """Copies a task JSON payload to the clipboard.

        Args:
            source_task (BatchTask): Source task to copy.
        """
        if not source_task:
            self.log_status("No task selected to copy.", status="warning")
            return
        payload = json.dumps(source_task.to_dict(), indent=4, sort_keys=True)
        try:
            ui_qt.QtWidgets.QApplication.clipboard().setText(payload)
            self.log_status('Copied task to clipboard: "{0}".'.format(source_task.display_name))
        except Exception as exception:
            self.log_status("Unable to copy task to clipboard: {0}".format(exception), status="warning")

    def context_menu_paste_task(self):
        """Pastes a task JSON payload from the clipboard."""
        try:
            clipboard_content = ui_qt.QtWidgets.QApplication.clipboard().text()
            task_data = json.loads(clipboard_content)
            inserted_task = self.insert_task_from_data(task_data)
            self.refresh_widgets()
            self.view.select_task_by_id(inserted_task.id)
            self.log_status('Pasted task: "{0}".'.format(inserted_task.display_name))
        except Exception as exception:
            self.log_status("Unable to paste task from clipboard: {0}".format(exception), status="warning")

    def context_menu_export_task(self, source_task):
        """Exports a task JSON payload to disk.

        Args:
            source_task (BatchTask): Source task to export.
        """
        if not source_task:
            self.log_status("No task selected to export.", status="warning")
            return
        default_name = "{0}.json".format(tasks.sanitize_filename(source_task.display_name.lower().replace(" ", "_")))
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Export Batch Task",
            write_mode=True,
            starting_directory=default_name,
            file_filter="Batch Task (*.json);;All Files (*);;",
            ok_caption="Export Task",
            cancel_caption="Cancel",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        with open(file_path, "w", encoding="utf-8") as task_file:
            json.dump(source_task.to_dict(), task_file, indent=4, sort_keys=True)
        self.log_status('Exported task "{0}" to: {1}'.format(source_task.display_name, file_path))

    def context_menu_import_task(self):
        """Imports a task JSON payload from disk."""
        file_path = ui_file_dialog.file_dialog(
            parent=self.view,
            caption="Import Batch Task",
            write_mode=False,
            starting_directory=None,
            file_filter="Batch Task (*.json);;All Files (*);;",
            ok_caption="Import Task",
            cancel_caption="Cancel",
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as task_file:
                task_data = json.load(task_file)
            inserted_task = self.insert_task_from_data(task_data)
            self.refresh_widgets()
            self.view.select_task_by_id(inserted_task.id)
            self.log_status('Imported task "{0}" from: {1}'.format(inserted_task.display_name, file_path))
        except Exception as exception:
            self.log_status("Unable to import task: {0}".format(exception), status="warning")

    def context_menu_delete_task(self, source_task):
        """Deletes a task from the task-tree context menu after confirmation.

        Args:
            source_task (BatchTask): Task to delete.
        """
        if not source_task:
            self.log_status("No task selected to delete.", status="warning")
            return
        if self.get_confirm_delete_task():
            message_box = ui_qt.QtWidgets.QMessageBox(self.view)
            message_box.setWindowTitle('Delete Task "{0}"?'.format(source_task.display_name))
            message_box.setText('Are you sure you want to delete task "{0}"?'.format(source_task.display_name))
            message_box.setIconPixmap(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete).pixmap(64, 64))
            message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
            message_box.addButton(ui_qt.QtLib.StandardButton.No)
            exec_method = getattr(message_box, "exec_", None)
            if not exec_method:
                exec_method = getattr(message_box, "exec")
            result = exec_method()
            if result != ui_qt.QtLib.StandardButton.Yes:
                self.log_status("Delete task cancelled.")
                return
        self.model.remove_task(source_task.id)
        self.refresh_widgets()
        self.log_status('Deleted task: "{0}".'.format(source_task.display_name))

    def insert_task_from_data(self, task_data):
        """Inserts a task from serialized data after the selected task when possible.

        Args:
            task_data (dict): Serialized task data.

        Returns:
            BatchTask: Inserted task.
        """
        insert_index = self.get_selected_task_insert_index()
        return self.model.add_task_from_dict(data=task_data, index=insert_index, reinitialize_id=True)

    def get_selected_task_insert_index(self):
        """Gets the insertion index used by paste/import context-menu actions.

        Returns:
            int: Zero-based insertion index.
        """
        selected_task_id = self.view.get_selected_task_id()
        if not selected_task_id:
            return len(self.model.tasks)
        for index, task in enumerate(self.model.tasks):
            if task.id == selected_task_id:
                return index + 1
        return len(self.model.tasks)

    def _run_project(self, run_from_task_id=None, run_to_task_id=None, force_single_instance=False):
        """Runs the project and updates the progress panel.

        Args:
            run_from_task_id (str, optional): Task id to start from.
            run_to_task_id (str, optional): Task id to stop after.
            force_single_instance (bool, optional): Whether to bypass multi-instance execution for this run.
        """
        self._active_log_file_path = None
        creates_any_log = bool(
            self.model.run_settings.get("create_log", True)
            or self.model.run_settings.get("create_task_time_log", True)
        )
        if creates_any_log and self.model.run_settings.get("purge_logs_on_run", True):
            self.purge_logs_for_run()
        if self.model.run_settings.get("create_log", True):
            self._active_log_file_path = self.create_run_log_file()
        if self.model.run_settings.get("multi_instance") and not force_single_instance:
            runner = batch_processor_worker.MultiInstanceBatchRunner(project_log_path=self._active_log_file_path)
        else:
            if force_single_instance and self.model.run_settings.get("multi_instance"):
                self.append_log("[INFO] - (single-instance) - Running selected aggregate task in this process.")
            tracker = batch_processor_tracker.BatchProgressTracker(message_callback=self.append_log)
            runner = batch_processor_worker.SingleInstanceBatchRunner(
                tracker=tracker,
                flag_skipped_tasks=self._flag_skipped_tasks,
                task_time_log_path=self.create_task_time_log_file(),
            )
        try:
            tracker = runner.run(
                self.model,
                run_from_task_id=run_from_task_id,
                run_to_task_id=run_to_task_id,
            )
            self.append_log(self._format_tracker(tracker))
            if self.model.run_settings.get("multi_instance"):
                launch_message = "Run launched in standalone tracker."
                self.append_log(f"[OPERATION] - (Multi-instance) - {launch_message}")
                self.view.set_status(launch_message, status="success")
            else:
                self.log_status("Run finished: {0}".format(tracker.status))
        except Exception as exception:
            logger.warning("Batch run failed: %s", exception)
            self.log_status("Run failed: {0}".format(exception))
        finally:
            self._active_log_file_path = None

    def log_status(self, message, status="info"):
        """Updates the status bar and appends to the log window.

        Args:
            message (str): Message to show and log.
            status (str, optional): Status level used for the bottom status field.
        """
        self.view.set_status(message, status=status)
        self.append_log(message)

    def append_log(self, message):
        """Appends a message to the standalone log view.

        Args:
            message (str): Message to append.
        """
        formatted_message = self.format_log_message(message)
        self.log_view.append_log(formatted_message)
        if self._active_log_file_path:
            with open(self._active_log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(formatted_message + "\n")

    @staticmethod
    def format_log_message(message):
        """Formats a batch log message with an Auto Rigger-style timestamp.

        Args:
            message (str): Message to format.

        Returns:
            str: Timestamped log message.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        lines = str(message).splitlines() or [""]
        formatted_lines = []
        for line in lines:
            if not line:
                formatted_lines.append("")
                continue
            if line.startswith("["):
                formatted_lines.append("{0} - {1}".format(timestamp, line))
            else:
                formatted_lines.append("{0} - [INFO] - {1}".format(timestamp, line))
        return "\n".join(formatted_lines)

    def create_run_log_file(self):
        """Creates a timestamped run log file path under the project folder.

        Returns:
            str: Log file path.
        """
        logs_dir = self.model.get_logs_dir()
        if not logs_dir:
            self.append_log("[WARNING] - (logs) - Log directory is unresolved. File logging disabled for this run.")
            return None
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = os.path.join(logs_dir, "batch_processor_{0}.log".format(timestamp))
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("Batch Processor Log\n")
        return log_file_path

    def create_task_time_log_file(self):
        """Creates a timestamped task timing log when enabled for the project.

        Returns:
            str or None: Task timing log path, or None when disabled or unresolved.
        """
        if not self.model.run_settings.get("create_task_time_log", True):
            return None
        logs_dir = self.model.get_logs_dir()
        if not logs_dir:
            self.append_log("[WARNING] - (logs) - Log directory is unresolved. Task timing disabled for this run.")
            return None
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(logs_dir, "batch_processor_task_times_{0}.log".format(timestamp))

    def purge_logs_for_run(self):
        """Deletes existing files from the configured log folder before a run."""
        logs_dir = self.model.get_logs_dir()
        if not logs_dir or not os.path.isdir(logs_dir):
            return
        project_dir = os.path.abspath(self.model.get_project_dir())
        logs_dir_abs = os.path.abspath(logs_dir)
        drive, _ = os.path.splitdrive(logs_dir_abs)
        home_dir = os.path.abspath(os.path.expanduser("~"))
        if logs_dir_abs == project_dir or logs_dir_abs == drive + os.sep or logs_dir_abs == home_dir:
            self.append_log("[WARNING] - (logs) - Refused to purge unsafe log directory: {0}".format(logs_dir_abs))
            return
        deleted_count = 0
        for root, _, file_names in os.walk(logs_dir_abs):
            for file_name in file_names:
                file_path = os.path.join(root, file_name)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError as exception:
                    self.append_log(
                        "[WARNING] - (logs) - Unable to remove log file {0}: {1}".format(
                            file_path,
                            exception,
                        )
                    )
        for root, dir_names, _ in os.walk(logs_dir_abs, topdown=False):
            for dir_name in dir_names:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                except OSError as exception:
                    self.append_log(
                        "[WARNING] - (logs) - Unable to remove log folder {0}: {1}".format(
                            dir_path,
                            exception,
                        )
                    )
        self.append_log("[OPERATION] - (logs) - Purged {0} existing log file(s).".format(deleted_count))

    @staticmethod
    def _format_tracker(tracker):
        """Formats tracker state for the view.

        Args:
            tracker (BatchProgressTracker): Tracker to display.

        Returns:
            str: Human-readable tracker summary.
        """
        data = tracker.to_dict()
        return "\n".join(
            [
                "Project: {0}".format(data["project_name"]),
                "Task: {0}/{1} {2}".format(
                    data["current_step_index"], data["total_steps"], data["current_step_name"]
                ),
                "Files: {0}/{1}".format(data["processed_files"], data["total_files"]),
                "Succeeded: {0}".format(data["succeeded"]),
                "Failed: {0}".format(data["failed"]),
                "Skipped: {0}".format(data["skipped"]),
                "Warnings: {0}".format(data["warnings"]),
                "Mode: {0}".format(data["run_mode"]),
                "Messages:",
                "\n".join(data.get("messages") or []),
            ]
        )

    @staticmethod
    def format_template_name(name):
        """Formats a template file name for menu display.

        Args:
            name (str): Template key.

        Returns:
            str: User-facing template name.
        """
        normalized_name = str(name or "").replace("_", " ").replace("-", " ")
        normalized_name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", normalized_name)
        words = []
        for word in normalized_name.split():
            if word.isupper():
                words.append(word)
            else:
                words.append(word[:1].upper() + word[1:])
        return " ".join(words)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
