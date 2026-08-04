"""Standalone Qt view for Batch Processor tracking."""

import gt.core.session as core_session
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor.tracker import tracker_tree_model


MENU_ICON_SIZE = 16


class MenuIconStyle(ui_qt.QtWidgets.QProxyStyle):
    """Pins the small-icon size so menu icons match stylesheet check indicators.

    Menu action icons are drawn at the active style's small-icon metric, which
    scales differently from stylesheet-sized check indicators on remote or
    high-DPI displays (for example over Parsec), leaving icons large while the
    checkboxes stay small. Forcing the small-icon metric to the same value the
    indicators use keeps every menu icon and checkbox the same size regardless
    of the host resolution or scaling.

    This proxy wraps an existing base style and must be installed on the
    QApplication (not on individual widgets). Installing a custom style directly
    on a widget disables Qt Style Sheet rendering for it; at the application
    level the stylesheet style wraps this proxy, so both keep working.
    """

    def pixelMetric(self, metric, option=None, widget=None):
        """Returns a uniform size for the small-icon metric.

        Args:
            metric (QStyle.PixelMetric): Requested pixel metric.
            option (QStyleOption, optional): Style option.
            widget (QWidget, optional): Target widget.

        Returns:
            int: Overridden size for the small-icon metric, otherwise the base
                style value.
        """
        pixel_metric = (
            ui_qt.QtWidgets.QStyle.PixelMetric if ui_qt.IS_PYSIDE6 else ui_qt.QtWidgets.QStyle
        )
        if metric == pixel_metric.PM_SmallIconSize:
            return MENU_ICON_SIZE
        return super().pixelMetric(metric, option, widget)


class TrackerTreeView(ui_qt.QtWidgets.QTreeView):
    """Tree view with Maya Outliner-style branch indicators."""

    def __init__(self, parent=None):
        """Initializes responsive column tracking.

        Args:
            parent (QWidget, optional): Qt parent.
        """
        super().__init__(parent)
        self.last_viewport_width = 0
        self.resizing_columns = False

    def drawBranches(self, painter, rectangle, index):
        """Paints root and child branch icons for one row.

        Args:
            painter (QPainter): Active view painter.
            rectangle (QRect): Branch area.
            index (QModelIndex): Row model index.
        """
        if not index.isValid():
            return
        model = index.model()
        child_count = model.rowCount(index)
        if child_count:
            icon_path = (
                ui_res_lib.Icon.ui_branch_root_open
                if self.isExpanded(index)
                else ui_res_lib.Icon.ui_branch_root_closed
            )
            target_x = rectangle.right() - 19
            if self.isExpanded(index):
                self._draw_vertical_connector(
                    painter,
                    target_x + 10.5,
                    rectangle.center().y() + 5,
                    rectangle.bottom() + 1,
                )
            self._draw_branch_icon(painter, target_x, rectangle, icon_path)
            return

        parent_index = index.parent()
        sibling_count = model.rowCount(parent_index) if parent_index.isValid() else 0
        single_x = rectangle.right() - 19
        parent_x = rectangle.right() - 39
        if sibling_count <= 1:
            self._draw_vertical_connector(
                painter,
                parent_x + 10.5,
                rectangle.top() - 1,
                rectangle.center().y(),
            )
            self._draw_branch_icon(painter, parent_x, rectangle, ui_res_lib.Icon.ui_branch_end)
            self._draw_branch_icon(painter, single_x, rectangle, ui_res_lib.Icon.ui_branch_single)
            return
        parent_icon = (
            ui_res_lib.Icon.ui_branch_end
            if index.row() == sibling_count - 1
            else ui_res_lib.Icon.ui_branch_more
        )
        connector_end = (
            rectangle.center().y()
            if parent_icon == ui_res_lib.Icon.ui_branch_end
            else rectangle.bottom() + 1
        )
        self._draw_vertical_connector(painter, parent_x + 10.5, rectangle.top() - 1, connector_end)
        self._draw_branch_icon(painter, parent_x, rectangle, parent_icon)
        self._draw_branch_icon(painter, single_x, rectangle, ui_res_lib.Icon.ui_branch_single)

    @staticmethod
    def _draw_branch_icon(painter, target_x, rectangle, icon_path):
        """Paints one branch SVG at its authored size.

        Args:
            painter (QPainter): Active view painter.
            target_x (int): Left edge of the branch slot.
            rectangle (QRect): Full branch area.
            icon_path (str): Branch SVG path.
        """
        pixmap = ui_qt.QtGui.QPixmap(icon_path)
        target_y = rectangle.center().y() - int(pixmap.height() / 2)
        painter.drawPixmap(target_x, target_y, pixmap)

    @staticmethod
    def _draw_vertical_connector(painter, target_x, start_y, end_y):
        """Extends a branch stroke to row boundaries to remove visual gaps.

        Args:
            painter (QPainter): Active view painter.
            target_x (float): Horizontal stroke coordinate.
            start_y (float): Top stroke coordinate.
            end_y (float): Bottom stroke coordinate.
        """
        painter.save()
        painter.setPen(ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(147, 147, 147), 1))
        painter.drawLine(
            ui_qt.QtCore.QPointF(float(target_x), float(start_y)),
            ui_qt.QtCore.QPointF(float(target_x), float(end_y)),
        )
        painter.restore()

    def resizeEvent(self, event):
        """Scales current user-defined column proportions with the viewport.

        Args:
            event (QResizeEvent): Tree resize event.
        """
        super().resizeEvent(event)
        if self.resizing_columns or not self.model():
            return
        viewport_width = self.viewport().width()
        header = self.header()
        column_count = header.count()
        if viewport_width <= 0 or not column_count:
            return
        current_total = sum(header.sectionSize(column) for column in range(column_count))
        if current_total <= 0 or viewport_width == self.last_viewport_width:
            return
        scale = float(viewport_width) / float(current_total)
        self.resizing_columns = True
        try:
            remaining_width = viewport_width
            for column in range(column_count - 1):
                width = max(header.minimumSectionSize(), int(header.sectionSize(column) * scale))
                header.resizeSection(column, width)
                remaining_width -= width
            header.resizeSection(column_count - 1, max(header.minimumSectionSize(), remaining_width))
        finally:
            self.resizing_columns = False
            self.last_viewport_width = viewport_width


class TrackerView(ui_qt.QtWidgets.QMainWindow):
    """Displays jobs, tasks, logs, progress, and batch controls."""

    def __init__(self, project_name, parent=None):
        """Initializes the tracker window.

        Args:
            project_name (str): Project display name.
            parent (QWidget, optional): Qt parent.
        """
        super().__init__(parent)
        self.close_callback = None
        self.setWindowTitle(f"Batch Processor Tracker - {project_name}")
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.batch_tracker))
        self.resize(1320, 720)
        self.setMinimumSize(900, 480)
        self._create_widgets()
        self._create_layout()
        self._apply_stylesheet()

    def _create_widgets(self):
        """Creates tracker widgets."""
        self.tree = TrackerTreeView()
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionBehavior(ui_qt.QtWidgets.QAbstractItemView.SelectRows)
        self.tree.setSelectionMode(ui_qt.QtWidgets.QAbstractItemView.SingleSelection)
        self.tree.setIconSize(ui_qt.QtCore.QSize(20, 20))
        self.tree.setIndentation(20)
        self.tree.setItemDelegateForColumn(2, tracker_tree_model.ProgressBarDelegate(self.tree))
        self.tree.header().setSectionsMovable(True)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setHighlightSections(True)
        self.tree.header().setSortIndicatorShown(True)
        self.tree.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)

        self.toolbar_widget = ui_qt.QtWidgets.QWidget()
        self.toolbar_widget.setObjectName("trackerToolbar")
        self.actions_widget = ui_qt.QtWidgets.QWidget()
        self.filters_widget = ui_qt.QtWidgets.QWidget()
        self.tracker_menu_bar = ui_qt.QtWidgets.QMenuBar()
        self.file_menu = self.tracker_menu_bar.addMenu("File")
        self.open_batch_processor_action = self.file_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open),
            "Open Project",
        )
        self.open_batch_processor_action.setToolTip(
            "Open this project in an independent Batch Processor."
        )
        self.file_menu.addSeparator()
        self.exit_action = self.file_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.setup_close),
            "Exit",
        )
        self.view_menu = self.tracker_menu_bar.addMenu("View")
        self.expand_all_action = self.view_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_branch_open),
            "Expand All",
        )
        self.collapse_all_action = self.view_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_branch_closed),
            "Collapse All",
        )
        self.view_menu.addSeparator()
        self.flag_skips_as_warnings_action = self.view_menu.addAction("Flag Skips as Warnings")
        self.flag_skips_as_warnings_action.setCheckable(True)
        self.flag_skips_as_warnings_action.setChecked(True)
        self.actions_menu = self.tracker_menu_bar.addMenu("Actions")
        self.restart_failed_jobs_action = self.actions_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset),
            "Restart All Failed Jobs",
        )
        self.restart_failed_jobs_action.setToolTip("Queue every failed job to run again.")
        self.restart_canceled_jobs_action = self.actions_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset),
            "Restart All Canceled Jobs",
        )
        self.restart_canceled_jobs_action.setToolTip("Queue every canceled job to run again.")
        self.copy_menu = self.tracker_menu_bar.addMenu("Copy")
        copy_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_copy_text)
        self.copy_failed_jobs_action = self.copy_menu.addAction(copy_icon, "Copy Failed Job Names")
        self.copy_failed_jobs_action.setToolTip("Copy failed job file names, one per line.")
        self.copy_warning_jobs_action = self.copy_menu.addAction(copy_icon, "Copy Warning Job Names")
        self.copy_warning_jobs_action.setToolTip("Copy job file names with reported warnings, one per line.")
        self.copy_completed_jobs_action = self.copy_menu.addAction(copy_icon, "Copy Completed Job Names")
        self.copy_completed_jobs_action.setToolTip("Copy cleanly completed job file names, one per line.")
        self.copy_skipped_jobs_action = self.copy_menu.addAction(copy_icon, "Copy Skipped Job Names")
        self.copy_skipped_jobs_action.setToolTip("Copy job file names containing skipped work, one per line.")
        self.copy_menu.addSeparator()
        self.copy_all_jobs_action = self.copy_menu.addAction(copy_icon, "Copy All Job Names")
        self.copy_all_jobs_action.setToolTip("Copy every regular job file name, one per line.")
        self.copy_menu.addSeparator()
        self.copy_failed_paths_action = self.copy_menu.addAction(copy_icon, "Copy Failed Job Paths")
        self.copy_failed_paths_action.setToolTip("Copy failed job source file paths, one per line.")
        self.copy_warning_paths_action = self.copy_menu.addAction(copy_icon, "Copy Warning Job Paths")
        self.copy_warning_paths_action.setToolTip("Copy source file paths with reported warnings, one per line.")
        self.copy_completed_paths_action = self.copy_menu.addAction(copy_icon, "Copy Completed Job Paths")
        self.copy_completed_paths_action.setToolTip("Copy cleanly completed job source file paths, one per line.")
        self.copy_skipped_paths_action = self.copy_menu.addAction(copy_icon, "Copy Skipped Job Paths")
        self.copy_skipped_paths_action.setToolTip("Copy source file paths containing skipped work, one per line.")
        self.copy_menu.addSeparator()
        self.copy_all_paths_action = self.copy_menu.addAction(copy_icon, "Copy All Job Paths")
        self.copy_all_paths_action.setToolTip("Copy every regular job source file path, one per line.")
        self.filters_menu = self.tracker_menu_bar.addMenu("Filters")
        self.hide_completed_action = self.filters_menu.addAction("Hide Completed")
        self.hide_completed_action.setCheckable(True)
        self.hide_completed_action.setToolTip("Hide successfully completed jobs and tasks.")
        self.failed_only_action = self.filters_menu.addAction("Show Failed Only")
        self.failed_only_action.setCheckable(True)
        self.failed_only_action.setToolTip("Show only failed jobs and tasks.")
        self.warnings_only_action = self.filters_menu.addAction("Show Warnings Only")
        self.warnings_only_action.setCheckable(True)
        self.warnings_only_action.setToolTip("Show only jobs and tasks with warnings.")
        self.filters_menu.addSeparator()
        self.reset_filters_action = self.filters_menu.addAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset),
            "Reset Filters",
        )
        self.reset_filters_action.setToolTip("Clear all tracker filters.")
        self.search_field = ui_qt.QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Filter by job name...")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setMinimumWidth(180)
        self.search_field.setMaximumWidth(320)

        self.log_tabs = ui_qt.QtWidgets.QTabWidget()
        self.log_tabs.setDocumentMode(True)
        self.log_tabs.setTabsClosable(False)
        self.log_tabs.setMinimumHeight(150)

        self.splitter = ui_qt.QtWidgets.QSplitter(ui_qt.QtLib.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.log_tabs)
        self.splitter.setSizes([520, 180])

        self.information_widget = ui_qt.QtWidgets.QWidget()
        self.primary_summary_label = ui_qt.QtWidgets.QLabel()
        self.secondary_summary_label = ui_qt.QtWidgets.QLabel()
        self.status_icon_label = ui_qt.QtWidgets.QLabel()
        self.status_icon_label.setFixedSize(24, 24)
        self.status_icon_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_icon_label.setToolTip("Starting — preparing the worker queue.")
        self.status_icon_label.setAccessibleName("Tracker status: Starting")
        self.primary_summary_label.setTextFormat(ui_qt.QtCore.Qt.RichText)
        self.secondary_summary_label.setTextFormat(ui_qt.QtCore.Qt.RichText)
        self.project_logs_button = ui_qt.QtWidgets.QPushButton("Project Logs")
        self.project_logs_button.setCheckable(True)
        self.project_logs_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates))
        self.project_logs_button.setToolTip("Show the main Batch Processor project log.")
        self.project_folder_button = ui_qt.QtWidgets.QPushButton("Project Folder")
        self.project_folder_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        self.project_folder_button.setToolTip("Open the Batch Processor project folder.")
        self.show_logs_button = ui_qt.QtWidgets.QPushButton("Hide Logs")
        self.show_logs_button.setCheckable(True)
        self.show_logs_button.setChecked(True)
        self.show_logs_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates))
        self.abort_button = ui_qt.QtWidgets.QPushButton("Abort All")
        self.abort_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        self.abort_button.setToolTip("Stop scheduling and terminate all active worker process trees.")

    def _create_layout(self):
        """Creates the central layout and bottom information row."""
        central_widget = ui_qt.QtWidgets.QWidget()
        main_layout = ui_qt.QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 8)
        toolbar_layout = ui_qt.QtWidgets.QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(5, 3, 5, 3)
        toolbar_layout.setSpacing(4)
        actions_layout = ui_qt.QtWidgets.QHBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(3)
        actions_layout.addWidget(self.tracker_menu_bar)
        filters_layout = ui_qt.QtWidgets.QHBoxLayout(self.filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(3)
        filters_layout.addWidget(self.search_field)
        toolbar_layout.addWidget(self.actions_widget)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.filters_widget)
        main_layout.addWidget(self.toolbar_widget)
        main_layout.addWidget(self.splitter)
        information_layout = ui_qt.QtWidgets.QVBoxLayout(self.information_widget)
        information_layout.setContentsMargins(10, 6, 8, 6)
        information_layout.setSpacing(3)
        primary_layout = ui_qt.QtWidgets.QHBoxLayout()
        primary_layout.addWidget(self.primary_summary_label, 1)
        information_layout.addLayout(primary_layout)
        secondary_layout = ui_qt.QtWidgets.QHBoxLayout()
        secondary_layout.addWidget(self.secondary_summary_label, 1)
        secondary_layout.addWidget(self.status_icon_label)
        secondary_layout.addWidget(self.project_folder_button)
        secondary_layout.addWidget(self.project_logs_button)
        secondary_layout.addWidget(self.show_logs_button)
        secondary_layout.addWidget(self.abort_button)
        information_layout.addLayout(secondary_layout)
        main_layout.addWidget(self.information_widget)
        self.setCentralWidget(central_widget)

    def _apply_stylesheet(self):
        """Applies repository-compatible standalone styling."""
        checked_icon = ui_res_lib.Icon.ui_checkbox_checked.replace("\\", "/")
        unchecked_icon = ui_res_lib.Icon.ui_checkbox_unchecked.replace("\\", "/")
        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.tree_widget_base
        stylesheet += ui_res_lib.Stylesheet.table_widget_base
        stylesheet += ui_res_lib.Stylesheet.tab_widget_base
        if not core_session.is_script_in_interactive_maya():
            stylesheet += ui_res_lib.Stylesheet.menu_base
        self.setStyleSheet(stylesheet)
        self.tree.setStyleSheet(
            "QTreeView {"
            " background-color: #2d2d2d;"
            " alternate-background-color: #252525;"
            " color: #e6e6e6;"
            " border: 1px solid #484848;"
            " border-radius: 5px;"
            " selection-background-color: #4f7285;"
            " selection-color: #ffffff;"
            " outline: none;"
            "}"
            "QTreeView::item { color: #e6e6e6; padding: 2px; }"
            "QTreeView::item:hover { background-color: #3d464b; color: #ffffff; }"
            "QTreeView::item:selected { background-color: #4f7285; color: #ffffff; }"
            "QHeaderView::section {"
            " background-color: #383838;"
            " color: #dddddd;"
            " border: 1px solid #4b4b4b;"
            " border-radius: 3px;"
            " padding: 6px 7px;"
            " font-weight: bold;"
            "}"
            "QHeaderView::section:hover { background-color: #4a555b; color: #ffffff; }"
            "QHeaderView::section:pressed { background-color: #55788a; color: #ffffff; }"
        )
        self.toolbar_widget.setStyleSheet(
            "QWidget#trackerToolbar { background-color: #292929; border: 1px solid #424242;"
            " border-radius: 4px; }"
            "QWidget#trackerToolbar QWidget { background: transparent; border: none; }"
            "QToolButton { background-color: #363636; border: 1px solid #4a4a4a; border-radius: 3px; }"
            "QToolButton:hover { background-color: #465158; border-color: #65747c; }"
            "QToolButton:checked { background-color: #55788a; border-color: #7395a5; }"
            "QMenuBar { background: transparent; color: #dddddd; border: none; }"
            "QMenuBar::item { background: transparent; padding: 4px 8px; border-radius: 3px; }"
            "QMenuBar::item:selected { background-color: #465158; color: #ffffff; }"
            "QMenuBar::item:pressed { background-color: #55788a; color: #ffffff; }"
            "QMenu { background-color: #444444; color: #dddddd; border: 1px solid #5a5a5a;"
            " padding: 4px 0px; }"
            "QMenu::item { background-color: transparent; padding: 6px 28px 6px 36px; min-height: 20px; }"
            "QMenu::item:selected { background-color: #55788a; color: #ffffff; }"
            "QMenu::item:disabled { color: #808080; }"
            "QMenu::separator { height: 1px; background-color: #5f5f5f; margin: 4px 8px; }"
            "QMenu::icon { left: 9px; }"
            "QMenu::indicator { left: 9px; width: 16px; height: 16px; }"
            f"QMenu::indicator:checked {{ image: url({checked_icon}); }}"
            f"QMenu::indicator:unchecked {{ image: url({unchecked_icon}); }}"
            "QLineEdit { background-color: #202020; color: #e6e6e6; border: 1px solid #484848;"
            " border-radius: 3px; padding: 3px 7px; }"
            "QLineEdit:focus { border-color: #66899a; }"
        )
        self.log_tabs.setStyleSheet(
            "QTabWidget { background-color: #292929; color: #e6e6e6; border-radius: 5px; }"
            "QTabWidget::pane { background-color: #242424; border: 1px solid #484848; border-radius: 5px; }"
            "QTabBar::tab { background-color: #303030; color: #cfcfcf; padding: 6px 10px;"
            " border: 1px solid #444444; border-bottom: none;"
            " border-top-left-radius: 4px; border-top-right-radius: 4px; }"
            "QTabBar::tab:selected { background-color: #454f54; color: #ffffff; }"
            "QTabBar::tab:hover:!selected { background-color: #3d464b; color: #ffffff; }"
            "QPlainTextEdit { background-color: #202020; color: #e6e6e6;"
            " selection-background-color: #55788a; border: none; padding: 5px; }"
        )
        self.information_widget.setStyleSheet(
            "QWidget { background-color: #292929; border: 1px solid #424242; border-radius: 5px; }"
            "QLabel { background: transparent; border: none; }"
            "QPushButton { border-radius: 3px; padding: 4px 8px; }"
        )

    def set_status_icon(self, icon_path, tooltip, accessible_name):
        """Updates the overall tracker status indicator.

        Args:
            icon_path (str): Status icon resource path.
            tooltip (str): Detailed hover text.
            accessible_name (str): Screen-reader description.
        """
        pixmap = ui_qt.QtGui.QPixmap(icon_path)
        keep_aspect_ratio = (
            ui_qt.QtCore.Qt.AspectRatioMode.KeepAspectRatio
            if ui_qt.IS_PYSIDE6
            else ui_qt.QtCore.Qt.KeepAspectRatio
        )
        pixmap = pixmap.scaled(
            20,
            20,
            keep_aspect_ratio,
            ui_qt.QtLib.TransformationMode.SmoothTransformation,
        )
        self.status_icon_label.setPixmap(pixmap)
        self.status_icon_label.setToolTip(tooltip)
        self.status_icon_label.setAccessibleName(accessible_name)

    def set_logs_visible(self, visible):
        """Shows or hides the log panel.

        Args:
            visible (bool): Requested visibility.
        """
        self.log_tabs.setVisible(bool(visible))
        self.show_logs_button.setText("Hide Logs" if visible else "Show Logs")

    def set_abort_enabled(self, enabled):
        """Enables or disables abort controls.

        Args:
            enabled (bool): Requested state.
        """
        self.abort_button.setEnabled(bool(enabled))

    def confirm_abort(self):
        """Asks the user to confirm aborting every worker.

        Returns:
            bool: True when abort was confirmed.
        """
        answer = ui_qt.QtWidgets.QMessageBox.question(
            self,
            "Abort Batch",
            "Abort all queued and running jobs?\n\nGenerated files will be preserved.",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return answer == ui_qt.QtLib.StandardButton.Yes

    def confirm_restart_job(self, job_name, active=False):
        """Asks the user to confirm restarting one job.

        Args:
            job_name (str): File name shown for the selected job.
            active (bool, optional): Whether the job is still queued or running
                and will be canceled before it is restarted.

        Returns:
            bool: True when the restart was confirmed.
        """
        if active:
            message = (
                f"'{job_name}' is still active.\n\n"
                "It will be canceled and then restarted. Configured tasks will "
                "run again and may replace generated outputs."
            )
        else:
            message = f"Restart '{job_name}'?\n\nConfigured tasks will run again and may replace generated outputs."
        answer = ui_qt.QtWidgets.QMessageBox.question(
            self,
            "Restart Job",
            message,
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return answer == ui_qt.QtLib.StandardButton.Yes

    def confirm_restart_jobs(self, job_count, status_label):
        """Asks the user to confirm restarting every job in a status at once.

        Args:
            job_count (int): Number of jobs to be restarted.
            status_label (str): Lowercase word describing the job status.

        Returns:
            bool: True when the batch restart was confirmed.
        """
        job_label = "job" if job_count == 1 else "jobs"
        answer = ui_qt.QtWidgets.QMessageBox.question(
            self,
            f"Restart All {status_label.capitalize()} Jobs",
            f"Restart {job_count} {status_label} {job_label}?\n\n"
            "Configured tasks will run again and may replace generated outputs.",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return answer == ui_qt.QtLib.StandardButton.Yes

    def confirm_cancel_job(self, job_name):
        """Asks the user to confirm canceling one queued or running job.

        Args:
            job_name (str): File name shown for the selected job.

        Returns:
            bool: True when cancellation was confirmed.
        """
        answer = ui_qt.QtWidgets.QMessageBox.question(
            self,
            "Cancel Job",
            f"Cancel '{job_name}'?\n\nIf already running, its active task may leave a partial generated output.",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return answer == ui_qt.QtLib.StandardButton.Yes

    def confirm_close_active(self):
        """Asks whether an active batch should abort before closing.

        Returns:
            str: Either abort or keep_running.
        """
        message_box = ui_qt.QtWidgets.QMessageBox(self)
        message_box.setWindowTitle("Batch Still Running")
        message_box.setText("The tracker owns the worker queue and cannot close while the batch continues.")
        message_box.setInformativeText("Keep the tracker open, or abort all workers and close it.")
        keep_button = message_box.addButton("Keep Running", ui_qt.QtWidgets.QMessageBox.RejectRole)
        abort_button = message_box.addButton("Abort All and Close", ui_qt.QtWidgets.QMessageBox.DestructiveRole)
        message_box.setDefaultButton(keep_button)
        message_box.exec_()
        return "abort" if message_box.clickedButton() == abort_button else "keep_running"

    def closeEvent(self, event):
        """Delegates active-session close decisions to the controller.

        Args:
            event (QCloseEvent): Window close event.
        """
        if callable(self.close_callback) and not self.close_callback():
            event.ignore()
            return
        event.accept()
