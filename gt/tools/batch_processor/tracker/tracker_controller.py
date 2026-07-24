"""Controller for the standalone Batch Processor tracker."""

from functools import partial
import html
import os
import subprocess
import sys

import gt.core.prefs as core_prefs
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib
import gt.utils.system as utils_system

from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_system_stats
from gt.tools.batch_processor.tracker import tracker_tree_model


class TrackerController:
    """Binds tracker session state, scheduling, and the Qt view."""

    MAX_LOG_CHARACTERS = 200000

    def __init__(self, session, scheduler, view):
        """Initializes the tracker controller.

        Args:
            session (TrackerSession): Active tracker state.
            scheduler (TrackerScheduler): Worker scheduler.
            view (TrackerView): Standalone tracker view.
        """
        self.session = session
        self.scheduler = scheduler
        self.view = view
        self.source_model = tracker_tree_model.TrackerTreeModel(session=session, parent=view.tree)
        self._displayed_job_count = len(session.jobs)
        self.proxy_model = tracker_tree_model.TrackerFilterProxyModel(view.tree)
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setSortRole(tracker_tree_model.SORT_ROLE)
        self.proxy_model.setDynamicSortFilter(True)
        self.view.tree.setModel(self.proxy_model)
        self.view.tree.sortByColumn(0, ui_qt.QtCore.Qt.AscendingOrder)
        self.system_stats = tracker_system_stats.SystemStats()
        self.log_widgets = {}
        self.log_offsets = {}
        self.selected_object = None
        self.close_after_abort = False
        self.cpu_text = "-"
        self.memory_text = "-"
        self.cpu_percent = None
        self.memory_percent = None
        self.showing_project_log = False
        self.prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        flag_skips_as_warnings = self.prefs.get_bool(
            tracker_constants.PREFS_KEY_FLAG_SKIPS_AS_WARNINGS,
            default=True,
        )
        self.session.set_flag_skips_as_warnings(flag_skips_as_warnings)
        self.view.flag_skips_as_warnings_action.setChecked(flag_skips_as_warnings)
        self.scheduler.update_callback = self.refresh
        self.scheduler.finish_callback = self.on_finished
        self._connect_signals()
        self._configure_columns()
        self._create_timers()
        self._update_open_project_action()
        self.refresh()
        self.view.project_logs_button.setChecked(True)
        self.view.show()

    def _connect_signals(self):
        """Connects view signals."""
        self.view.abort_button.clicked.connect(self.request_abort)
        self.view.project_folder_button.clicked.connect(self.open_project_folder)
        self.view.project_logs_button.toggled.connect(self.toggle_project_log)
        self.view.show_logs_button.toggled.connect(self.toggle_logs_visible)
        self.view.tree.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.view.tree.header().sectionClicked.connect(self.on_header_clicked)
        self.view.tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.view.open_batch_processor_action.triggered.connect(self.open_batch_processor)
        self.view.exit_action.triggered.connect(self.view.close)
        self.view.expand_all_action.triggered.connect(self.view.tree.expandAll)
        self.view.collapse_all_action.triggered.connect(self.view.tree.collapseAll)
        self.view.flag_skips_as_warnings_action.toggled.connect(self.toggle_skip_warnings)
        self.view.restart_failed_jobs_action.triggered.connect(self.restart_all_failed_jobs)
        self.view.restart_canceled_jobs_action.triggered.connect(self.restart_all_canceled_jobs)
        self.view.copy_failed_jobs_action.triggered.connect(
            partial(self.copy_job_names, "failed")
        )
        self.view.copy_warning_jobs_action.triggered.connect(
            partial(self.copy_job_names, "warning")
        )
        self.view.copy_completed_jobs_action.triggered.connect(
            partial(self.copy_job_names, "completed")
        )
        self.view.copy_skipped_jobs_action.triggered.connect(
            partial(self.copy_job_names, "skipped")
        )
        self.view.copy_all_jobs_action.triggered.connect(
            partial(self.copy_job_names, "all")
        )
        self.view.hide_completed_action.toggled.connect(self.apply_filters)
        self.view.failed_only_action.toggled.connect(self.toggle_failed_filter)
        self.view.warnings_only_action.toggled.connect(self.toggle_warnings_filter)
        self.view.reset_filters_action.triggered.connect(self.reset_filters)
        self.view.search_field.textChanged.connect(self.apply_filters)
        self.view.close_callback = self.request_close

    def _configure_columns(self):
        """Configures balanced columns that remain manually resizable."""
        header = self.view.tree.header()
        for column in range(self.source_model.columnCount()):
            header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.Interactive)
        header.setMinimumSectionSize(48)
        initial_widths = [52, 250, 140, 85, 62, 135, 72, 145, 145, 82]
        for column, width in enumerate(initial_widths):
            header.resizeSection(column, width)

    def _create_timers(self):
        """Creates non-blocking scheduler, display, and metrics timers."""
        self.scheduler_timer = ui_qt.QtCore.QTimer(self.view)
        self.scheduler_timer.setInterval(250)
        self.scheduler_timer.timeout.connect(self.scheduler.tick)
        self.scheduler_timer.start()
        self.display_timer = ui_qt.QtCore.QTimer(self.view)
        self.display_timer.setInterval(1000)
        self.display_timer.timeout.connect(self.refresh_time_values)
        self.display_timer.start()
        self.stats_timer = ui_qt.QtCore.QTimer(self.view)
        self.stats_timer.setInterval(2000)
        self.stats_timer.timeout.connect(self.refresh_system_stats)
        self.stats_timer.start()
        self.log_timer = ui_qt.QtCore.QTimer(self.view)
        self.log_timer.setInterval(750)
        self.log_timer.timeout.connect(self.refresh_logs)
        self.log_timer.start()

    def refresh(self):
        """Refreshes tracker rows and aggregate summary text."""
        if len(self.session.jobs) != self._displayed_job_count:
            self.source_model.reset_rows()
            self._displayed_job_count = len(self.session.jobs)
        self.source_model.notify_all_changed()
        self._update_copy_actions()
        self._update_summary()
        self.refresh_logs()

    def _update_copy_actions(self):
        """Enables global copy actions only when matching jobs exist."""
        action_categories = {
            self.view.copy_failed_jobs_action: "failed",
            self.view.copy_warning_jobs_action: "warning",
            self.view.copy_completed_jobs_action: "completed",
            self.view.copy_skipped_jobs_action: "skipped",
            self.view.copy_all_jobs_action: "all",
        }
        for action, category in action_categories.items():
            action.setEnabled(bool(self.session.get_job_names(category)))

    def copy_job_names(self, result_category, *args):
        """Copies matching regular job names to the system clipboard.

        Args:
            result_category (str): Result category requested by the copy action.
            *args: Optional Qt signal values.
        """
        job_names = self.session.get_job_names(result_category)
        if not job_names:
            return
        ui_qt.QtWidgets.QApplication.clipboard().setText("\n".join(job_names))

    def _format_estimate(self):
        """Formats the estimated remaining time for the summary row.

        Returns:
            str: HH:MM:SS estimate, "Done" once finished, or "-" while no
                regular job has completed yet.
        """
        if self.session.finished:
            return "Done"
        seconds = self.session.estimate_remaining_seconds()
        if seconds is None:
            return "-"
        return tracker_tree_model.format_duration(seconds)

    def _update_summary(self):
        """Updates project, progress, worker, issue, and timing summaries."""
        regular_jobs = self.session.regular_jobs
        completed = len([job for job in regular_jobs if job.status in tracker_constants.TERMINAL_STATUSES])
        failed = len([job for job in regular_jobs if job.status == tracker_constants.Status.FAILED])
        warning_jobs = len(
            [job for job in regular_jobs if job.status == tracker_constants.Status.COMPLETED_WARNINGS]
        )
        active_statuses = {tracker_constants.Status.WAITING, tracker_constants.Status.RUNNING}
        active = len([job for job in self.session.jobs if job.status in active_statuses])
        errors = sum(job.errors for job in regular_jobs)
        warnings = sum(job.warnings for job in regular_jobs)
        elapsed = tracker_tree_model.format_elapsed(self.session.started_at, self.session.completed_at)
        estimate = self._format_estimate()
        primary_values = [
            ("Project", self.session.project_name, "value"),
            ("Jobs / Files", f"{completed}/{len(regular_jobs)}", "value"),
            ("Overall", f"{self.session.progress}%", "value"),
            ("Failed", failed, "error" if failed else "value"),
            ("Errors", errors, "error" if errors else "value"),
            ("Warnings", warnings, "warning" if warnings else "value"),
        ]
        secondary_values = [
            ("Started", tracker_tree_model.format_timestamp(self.session.started_at, include_year=False), "value"),
            ("Elapsed", elapsed, "value"),
            ("Est. Left", estimate, "value"),
            ("Workers", f"{active}/{self.session.worker_count}", "value"),
            ("CPU", self.cpu_text, self._usage_color_role(self.cpu_percent)),
            ("RAM", self.memory_text, self._usage_color_role(self.memory_percent)),
        ]
        self.view.primary_summary_label.setText(self._build_summary_html(primary_values))
        self.view.secondary_summary_label.setText(self._build_summary_html(secondary_values))
        self._update_status_icon(
            errors=errors,
            warnings=warnings,
            failed=failed,
            warning_jobs=warning_jobs,
        )

    def _update_status_icon(self, errors, warnings, failed, warning_jobs):
        """Updates the overall batch-health icon and its explanatory tooltip.

        Args:
            errors (int): Total worker error count.
            warnings (int): Total worker warning count.
            failed (int): Number of failed regular jobs.
            warning_jobs (int): Number of jobs completed with warnings.
        """
        state = self.session.health_state
        warning_status = (
            (
                ui_res_lib.Icon.validator_warning,
                f"Completed with warnings — {warning_jobs} job(s), {warnings} reported warning(s).",
                "Tracker status: Completed with warnings",
            )
            if self.session.finished
            else (
                ui_res_lib.Icon.ui_yellow_circle,
                f"Running with warnings — {warnings} reported warning(s).",
                "Tracker status: Running with warnings",
            )
        )
        error_status = (
            (
                ui_res_lib.Icon.validator_fail_hard,
                f"Failed — {failed} failed job(s), {errors} error(s).",
                "Tracker status: Failed",
            )
            if self.session.finished
            else (
                ui_res_lib.Icon.ui_red_circle,
                f"Running with errors — {failed} failed job(s), {errors} error(s).",
                "Tracker status: Running with errors",
            )
        )
        aborted_status = (
            (
                ui_res_lib.Icon.validator_fail_soft,
                "Aborted by the user.",
                "Tracker status: Aborted",
            )
            if self.session.finished
            else (
                ui_res_lib.Icon.ui_red_circle,
                "Aborting — worker processes are being stopped.",
                "Tracker status: Aborting",
            )
        )
        status_data = {
            tracker_constants.HealthState.STARTING: (
                ui_res_lib.Icon.ui_grey_circle,
                "Starting — preparing the worker queue.",
                "Tracker status: Starting",
            ),
            tracker_constants.HealthState.RUNNING: (
                ui_res_lib.Icon.ui_green_circle,
                "Running — batch processing is active.",
                "Tracker status: Running",
            ),
            tracker_constants.HealthState.COMPLETED: (
                ui_res_lib.Icon.validator_pass,
                "Completed successfully.",
                "Tracker status: Completed successfully",
            ),
            tracker_constants.HealthState.WARNING: warning_status,
            tracker_constants.HealthState.ERROR: error_status,
            tracker_constants.HealthState.ABORTED: aborted_status,
        }
        icon_path, tooltip, accessible_name = status_data[state]
        self.view.set_status_icon(icon_path, tooltip, accessible_name)

    @staticmethod
    def _build_summary_html(items):
        """Builds a Clip Tracker-style two-tone summary string.

        Args:
            items (list): Label, value, and color-role tuples.

        Returns:
            str: Rich-text summary.
        """
        colors = {"value": "#e0e0e0", "error": "#e78787", "warning": "#e4bf67"}
        fragments = []
        for label, value, color_role in items:
            value_text = html.escape(str(value))
            value_color = colors.get(color_role, colors["value"])
            fragments.append(
                f'<span style="color:#999999;">{html.escape(str(label))}:</span> '
                f'<span style="color:{value_color}; font-weight:600;">{value_text}</span>'
            )
        return '&nbsp;&nbsp;<span style="color:#666666;">|</span>&nbsp;&nbsp;'.join(fragments)

    def refresh_time_values(self):
        """Refreshes elapsed time cells while work is active."""
        if not self.session.finished:
            self.source_model.notify_all_changed()
            self._update_summary()

    def refresh_system_stats(self):
        """Refreshes CPU and memory information."""
        values = self.system_stats.sample()
        cpu_value = values.get("cpu_percent")
        used_memory = values.get("memory_used")
        total_memory = values.get("memory_total")
        cpu_text = "-" if cpu_value is None else f"{cpu_value:.0f}%"
        memory_text = "-"
        if used_memory is not None and total_memory:
            gigabyte = 1024.0 ** 3
            memory_text = f"{used_memory / gigabyte:.1f}/{total_memory / gigabyte:.1f} GB"
        self.cpu_text = cpu_text
        self.memory_text = memory_text
        self.cpu_percent = cpu_value
        self.memory_percent = (
            used_memory / total_memory * 100.0
            if used_memory is not None and total_memory
            else None
        )
        self._update_summary()

    @staticmethod
    def _usage_color_role(percentage):
        """Maps resource utilization to a summary color role.

        Args:
            percentage (float or None): Resource usage percentage.

        Returns:
            str: Summary color role.
        """
        if percentage is not None and percentage > 90:
            return "error"
        if percentage is not None and percentage > 80:
            return "warning"
        return "value"

    def toggle_project_log(self, checked):
        """Shows or hides the main project log.

        Args:
            checked (bool): Whether the project log should be visible.
        """
        if checked:
            self.show_project_log()
            return
        if self.showing_project_log:
            self.showing_project_log = False
            self.view.show_logs_button.setChecked(False)

    def toggle_logs_visible(self, visible):
        """Synchronizes general log visibility with the project-log toggle.

        Args:
            visible (bool): Requested log-panel visibility.
        """
        self.view.set_logs_visible(visible)
        if visible or not self.showing_project_log:
            return
        self.showing_project_log = False
        self.view.project_logs_button.blockSignals(True)
        self.view.project_logs_button.setChecked(False)
        self.view.project_logs_button.blockSignals(False)

    def show_project_log(self):
        """Populates and shows the main project log tab."""
        self.showing_project_log = True
        self.view.show_logs_button.setChecked(True)
        self.view.set_logs_visible(True)
        self.selected_object = None
        self.view.log_tabs.clear()
        self.log_widgets = {}
        self.log_offsets = {}
        project_log_path = self.session.project_log_path
        if not project_log_path:
            text_edit = self._create_log_widget()
            text_edit.setPlainText("The current session does not have a main project log.")
            self.view.log_tabs.addTab(text_edit, "Project Log")
            return
        text_edit = self._create_log_widget()
        text_edit.setToolTip(project_log_path)
        self.log_widgets[project_log_path] = text_edit
        self.view.log_tabs.addTab(text_edit, "Project Log")
        self.refresh_logs()

    def open_project_folder(self):
        """Opens the resolved project folder in the system file browser."""
        project_path = os.path.normpath(self.session.project_path or "")
        if project_path and os.path.isdir(project_path):
            utils_system.open_file_dir(project_path)
            return
        ui_qt.QtWidgets.QMessageBox.warning(
            self.view,
            "Project Folder Unavailable",
            f"The project folder could not be found:\n{project_path or 'No project folder is configured.'}",
        )

    def _update_open_project_action(self):
        """Updates availability of the standalone Batch Processor action."""
        project_file = os.path.normpath(self.session.source_project_file or "")
        available = bool(project_file and os.path.isfile(project_file))
        self.view.open_batch_processor_action.setEnabled(available)
        if available:
            self.view.open_batch_processor_action.setToolTip(
                f"Open this project in an independent Batch Processor.\n{project_file}"
            )
        else:
            self.view.open_batch_processor_action.setToolTip(
                "The original saved Batch Processor project is unavailable."
            )

    def open_batch_processor(self):
        """Opens the original project in an independent Batch Processor process."""
        project_file = os.path.abspath(self.session.source_project_file or "")
        if not project_file or not os.path.isfile(project_file):
            self._update_open_project_action()
            return
        mayapy_path = getattr(self.scheduler.options, "mayapy", "")
        launcher_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker_batch_processor_launcher.py")
        command = [mayapy_path, launcher_path, "--project-file", project_file]
        environment = dict(os.environ)
        environment["PYTHONIOENCODING"] = "utf-8"
        creation_flags = 0
        popen_kwargs = {}
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        else:
            popen_kwargs["start_new_session"] = True
        try:
            subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                env=environment,
                creationflags=creation_flags,
                **popen_kwargs,
            )
        except (OSError, ValueError) as exception:
            ui_qt.QtWidgets.QMessageBox.warning(
                self.view,
                "Unable to Open Batch Processor",
                f"The standalone Batch Processor could not be launched:\n\n{exception}",
            )

    def apply_filters(self, *args):
        """Applies toolbar filters to the tracker proxy.

        Args:
            *args: Optional Qt signal values.
        """
        self.proxy_model.set_tracker_filters(
            search_text=self.view.search_field.text(),
            hide_completed=self.view.hide_completed_action.isChecked(),
            failed_only=self.view.failed_only_action.isChecked(),
            warnings_only=self.view.warnings_only_action.isChecked(),
        )

    def toggle_failed_filter(self, checked):
        """Activates the failed-only filter and clears warning-only.

        Args:
            checked (bool): Requested failed-only state.
        """
        if checked:
            self.view.warnings_only_action.blockSignals(True)
            self.view.warnings_only_action.setChecked(False)
            self.view.warnings_only_action.blockSignals(False)
        self.apply_filters()

    def toggle_warnings_filter(self, checked):
        """Activates the warning-only filter and clears failed-only.

        Args:
            checked (bool): Requested warning-only state.
        """
        if checked:
            self.view.failed_only_action.blockSignals(True)
            self.view.failed_only_action.setChecked(False)
            self.view.failed_only_action.blockSignals(False)
        self.apply_filters()

    def reset_filters(self):
        """Clears search and status filtering in one update."""
        widgets = [
            self.view.search_field,
            self.view.hide_completed_action,
            self.view.failed_only_action,
            self.view.warnings_only_action,
        ]
        for widget in widgets:
            widget.blockSignals(True)
        self.view.search_field.clear()
        self.view.hide_completed_action.setChecked(False)
        self.view.failed_only_action.setChecked(False)
        self.view.warnings_only_action.setChecked(False)
        for widget in widgets:
            widget.blockSignals(False)
        self.apply_filters()

    def toggle_skip_warnings(self, enabled):
        """Updates whether skipped work produces warning results.

        Args:
            enabled (bool): Whether skips should be represented as warnings.
        """
        self.session.set_flag_skips_as_warnings(enabled)
        self.prefs.set_bool(
            tracker_constants.PREFS_KEY_FLAG_SKIPS_AS_WARNINGS,
            bool(enabled),
        )
        self.prefs.save()
        self.refresh()

    def show_tree_context_menu(self, position):
        """Shows file actions for the job under the cursor.

        Args:
            position (QPoint): Viewport-local context-menu position.
        """
        proxy_index = self.view.tree.indexAt(position)
        if not proxy_index.isValid():
            return
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = source_index.data(tracker_tree_model.OBJECT_ROLE)
        job = item.parent_job if isinstance(item, tracker_model.TrackerTask) else item
        if not isinstance(job, tracker_model.TrackerJob) or job.is_finalization:
            return
        menu = ui_qt.QtWidgets.QMenu(self.view.tree)
        copy_name_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_copy),
            "Copy File Name",
        )
        copy_path_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_copy),
            "Copy Full Path",
        )
        open_source_folder_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir),
            "Open Source Folder",
        )
        source_directory = os.path.dirname(os.path.normpath(job.source_file or ""))
        open_source_folder_action.setEnabled(bool(source_directory and os.path.isdir(source_directory)))
        menu.addSeparator()
        open_log_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates),
            "Open Job Log",
        )
        open_log_action.setEnabled(bool(job.log_path and os.path.isfile(job.log_path)))
        open_log_folder_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir),
            "Open Log Folder",
        )
        log_directory = self.scheduler.get_logs_dir()
        open_log_folder_action.setEnabled(os.path.isdir(log_directory))
        menu.addSeparator()
        restart_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset),
            "Restart Job",
        )
        restart_action.setEnabled(self.scheduler.can_restart_job(job))
        cancel_action = menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete),
            "Cancel Job",
        )
        cancel_action.setEnabled(self.scheduler.can_cancel_job(job))
        self.tree_context_menu = menu
        selected_action = menu.exec_(self.view.tree.viewport().mapToGlobal(position))
        if selected_action == copy_name_action:
            ui_qt.QtWidgets.QApplication.clipboard().setText(job.name)
        elif selected_action == copy_path_action:
            ui_qt.QtWidgets.QApplication.clipboard().setText(os.path.normpath(job.source_file))
        elif selected_action == open_source_folder_action:
            utils_system.open_file_dir(source_directory)
        elif selected_action == open_log_action:
            log_url = ui_qt.QtCore.QUrl.fromLocalFile(os.path.normpath(job.log_path))
            ui_qt.QtGui.QDesktopServices.openUrl(log_url)
        elif selected_action == open_log_folder_action:
            utils_system.open_file_dir(log_directory)
        elif selected_action == restart_action:
            self.restart_job(job)
        elif selected_action == cancel_action:
            self.cancel_job(job)

    def restart_job(self, job):
        """Confirms and queues one terminal job for another execution.

        Args:
            job (TrackerJob): Regular tracker job to restart.
        """
        if not self.scheduler.can_restart_job(job):
            return
        if not self.view.confirm_restart_job(job.name):
            return
        if not self.scheduler.restart_job(job):
            return
        self.close_after_abort = False
        self.view.set_abort_enabled(True)
        self.scheduler_timer.start()
        self.log_timer.start()
        self.refresh()
        self.rebuild_log_tabs()

    def restart_all_failed_jobs(self):
        """Confirms and queues every failed regular job for another execution."""
        self._restart_all_jobs_with_status(tracker_constants.Status.FAILED, "failed")

    def restart_all_canceled_jobs(self):
        """Confirms and queues every canceled regular job for another execution."""
        self._restart_all_jobs_with_status(tracker_constants.Status.CANCELED, "canceled")

    def _restart_all_jobs_with_status(self, status, status_label):
        """Confirms and queues every regular job in a status for another run.

        Mirrors selecting "Restart Job" for each matching job, but asks for a
        single confirmation and starts the scheduler once for the whole batch.

        Args:
            status (str): Terminal status value used to select jobs to restart.
            status_label (str): Lowercase word shown to the user for the status.
        """
        matching_jobs = [
            job
            for job in self.session.regular_jobs
            if job.status == status and self.scheduler.can_restart_job(job)
        ]
        if not matching_jobs:
            self.view.statusBar().showMessage(f"No {status_label} jobs available to restart.", 5000)
            return
        if not self.view.confirm_restart_jobs(len(matching_jobs), status_label):
            return
        restarted = 0
        for job in matching_jobs:
            if self.scheduler.restart_job(job):
                restarted += 1
        if not restarted:
            return
        self.close_after_abort = False
        self.view.set_abort_enabled(True)
        self.scheduler_timer.start()
        self.log_timer.start()
        self.refresh()
        self.rebuild_log_tabs()

    def cancel_job(self, job):
        """Confirms and cancels one queued or running regular job.

        Args:
            job (TrackerJob): Regular tracker job to cancel.
        """
        if not self.scheduler.can_cancel_job(job):
            return
        if not self.view.confirm_cancel_job(job.name):
            return
        if not self.scheduler.cancel_job(job):
            return
        self.refresh()
        self.rebuild_log_tabs()

    def on_header_clicked(self, section):
        """Restores original order when the number header is clicked.

        Args:
            section (int): Clicked header section.
        """
        if section == 0:
            self.view.tree.sortByColumn(0, ui_qt.QtCore.Qt.AscendingOrder)

    def on_selection_changed(self, selected, deselected):
        """Updates log tabs for the selected job or task.

        Args:
            selected (QItemSelection): Selected indexes.
            deselected (QItemSelection): Deselected indexes.
        """
        indexes = self.view.tree.selectionModel().selectedRows(0)
        if self.showing_project_log:
            self.showing_project_log = False
            self.view.project_logs_button.blockSignals(True)
            self.view.project_logs_button.setChecked(False)
            self.view.project_logs_button.blockSignals(False)
        self.selected_object = None
        if indexes:
            source_index = self.proxy_model.mapToSource(indexes[0])
            self.selected_object = source_index.data(tracker_tree_model.OBJECT_ROLE)
        self.rebuild_log_tabs()

    def rebuild_log_tabs(self):
        """Rebuilds log tabs for the current selection."""
        self.view.log_tabs.clear()
        self.log_widgets = {}
        self.log_offsets = {}
        paths = []
        messages = []
        item = self.selected_object
        if isinstance(item, tracker_model.TrackerJob):
            paths.extend([item.log_path, item.timing_log_path])
            for task in item.tasks:
                paths.extend(task.log_paths)
                messages.extend([(task.name, level, message) for level, message in task.messages])
        elif isinstance(item, tracker_model.TrackerTask):
            paths.extend([item.parent_job.log_path, item.parent_job.timing_log_path])
            paths.extend(item.log_paths)
            messages.extend([(item.name, level, message) for level, message in item.messages])
        paths = list(dict.fromkeys([path for path in paths if path]))
        if messages:
            summary_widget = self._create_log_widget()
            summary_widget.setPlainText(
                "\n".join([f"[{level}] ({task_name}) {message}" for task_name, level, message in messages])
            )
            self.view.log_tabs.addTab(summary_widget, "Issues")
        if not paths and not messages:
            text_edit = self._create_log_widget()
            text_edit.setPlainText("No log files are available for the current selection.")
            self.view.log_tabs.addTab(text_edit, "Logs")
            return
        for path in paths:
            text_edit = self._create_log_widget()
            text_edit.setToolTip(path)
            self.log_widgets[path] = text_edit
            self.view.log_tabs.addTab(text_edit, os.path.basename(path))
        self.refresh_logs()

    def refresh_logs(self):
        """Appends new log output without disturbing selection or scrolling."""
        if not self.view.log_tabs.isVisible():
            return
        for path, text_edit in self.log_widgets.items():
            if not os.path.isfile(path):
                if path not in self.log_offsets:
                    text_edit.setPlainText(f"Waiting for log file:\n{path}")
                    self.log_offsets[path] = None
                continue
            try:
                file_size = os.path.getsize(path)
            except OSError:
                continue
            offset = self.log_offsets.get(path)
            if offset is None or file_size < offset:
                text_edit.setPlainText(self._read_log_tail(path))
                self.log_offsets[path] = file_size
                text_edit.verticalScrollBar().setValue(text_edit.verticalScrollBar().maximum())
                continue
            if file_size == offset:
                continue
            try:
                with open(path, "rb") as log_file:
                    log_file.seek(offset)
                    new_text = log_file.read().decode("utf-8", errors="replace")
            except OSError:
                continue
            self.log_offsets[path] = file_size
            if not new_text:
                continue
            scroll_bar = text_edit.verticalScrollBar()
            was_at_bottom = scroll_bar.value() >= scroll_bar.maximum() - 4
            scroll_value = scroll_bar.value()
            selection_cursor = text_edit.textCursor()
            cursor_anchor = selection_cursor.anchor()
            cursor_position = selection_cursor.position()
            cursor = ui_qt.QtGui.QTextCursor(text_edit.document())
            cursor.movePosition(self._text_cursor_end())
            cursor.insertText(new_text)
            restored_cursor = ui_qt.QtGui.QTextCursor(text_edit.document())
            restored_cursor.setPosition(cursor_anchor)
            restored_cursor.setPosition(cursor_position, self._text_cursor_keep_anchor())
            text_edit.setTextCursor(restored_cursor)
            if was_at_bottom:
                scroll_bar.setValue(scroll_bar.maximum())
            else:
                scroll_bar.setValue(scroll_value)

    def request_abort(self):
        """Confirms and requests termination of the active batch."""
        if self.session.finished or not self.view.confirm_abort():
            return
        self.view.set_abort_enabled(False)
        self.scheduler.abort()

    def request_close(self):
        """Handles attempts to close the active tracker.

        Returns:
            bool: True when the window may close.
        """
        if self.session.finished:
            return True
        decision = self.view.confirm_close_active()
        if decision != "abort":
            return False
        self.close_after_abort = True
        self.scheduler.abort()
        return False

    def on_finished(self):
        """Stops scheduling timers and leaves the completed tracker open."""
        self.scheduler_timer.stop()
        self.view.set_abort_enabled(False)
        self.refresh()
        self.log_timer.stop()
        if self.close_after_abort:
            self.view.close()

    @staticmethod
    def _create_log_widget():
        """Creates a read-only monospaced log viewer.

        Returns:
            QPlainTextEdit: Log viewer.
        """
        text_edit = ui_qt.QtWidgets.QPlainTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(ui_qt.QtWidgets.QPlainTextEdit.NoWrap)
        text_edit.setMaximumBlockCount(10000)
        font = ui_qt.QtGui.QFontDatabase.systemFont(ui_qt.QtGui.QFontDatabase.FixedFont)
        text_edit.setFont(font)
        return text_edit

    @staticmethod
    def _text_cursor_end():
        """Gets the binding-compatible QTextCursor end operation.

        Returns:
            QTextCursor.MoveOperation: Cursor operation for the document end.
        """
        if ui_qt.IS_PYSIDE6:
            return ui_qt.QtGui.QTextCursor.MoveOperation.End
        return ui_qt.QtGui.QTextCursor.End

    @staticmethod
    def _text_cursor_keep_anchor():
        """Gets the binding-compatible QTextCursor keep-anchor mode.

        Returns:
            QTextCursor.MoveMode: Cursor mode that preserves the selection anchor.
        """
        if ui_qt.IS_PYSIDE6:
            return ui_qt.QtGui.QTextCursor.MoveMode.KeepAnchor
        return ui_qt.QtGui.QTextCursor.KeepAnchor

    @classmethod
    def _read_log_tail(cls, path):
        """Reads a bounded UTF-8 tail from a log file.

        Args:
            path (str): Log path.

        Returns:
            str: Log text or a helpful placeholder.
        """
        if not path or not os.path.isfile(path):
            return f"Waiting for log file:\n{path}"
        try:
            with open(path, "rb") as log_file:
                log_file.seek(0, os.SEEK_END)
                file_size = log_file.tell()
                log_file.seek(max(0, file_size - cls.MAX_LOG_CHARACTERS))
                data = log_file.read()
            prefix = "... earlier log content omitted ...\n" if file_size > cls.MAX_LOG_CHARACTERS else ""
            return prefix + data.decode("utf-8", errors="replace")
        except OSError as exception:
            return f"Unable to read log file:\n{path}\n\n{exception}"
