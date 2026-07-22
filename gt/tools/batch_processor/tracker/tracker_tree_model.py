"""Qt presentation model and delegates for Batch Processor tracker rows."""

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker.tracker_events import elapsed_seconds, parse_timestamp


DISPLAY_ROLE = ui_qt.QtCore.Qt.ItemDataRole.DisplayRole if ui_qt.IS_PYSIDE6 else ui_qt.QtCore.Qt.DisplayRole
DECORATION_ROLE = ui_qt.QtCore.Qt.ItemDataRole.DecorationRole if ui_qt.IS_PYSIDE6 else ui_qt.QtCore.Qt.DecorationRole
TEXT_ALIGNMENT_ROLE = (
    ui_qt.QtCore.Qt.ItemDataRole.TextAlignmentRole if ui_qt.IS_PYSIDE6 else ui_qt.QtCore.Qt.TextAlignmentRole
)
USER_ROLE = ui_qt.QtCore.Qt.ItemDataRole.UserRole if ui_qt.IS_PYSIDE6 else ui_qt.QtCore.Qt.UserRole
SORT_ROLE = USER_ROLE + 1
STATUS_ROLE = USER_ROLE + 2
PROGRESS_ROLE = USER_ROLE + 3
OBJECT_ROLE = USER_ROLE + 4


class TrackerFilterProxyModel(ui_qt.QtCore.QSortFilterProxyModel):
    """Filters tracker rows by job name and useful result states."""

    def __init__(self, parent=None):
        """Initializes an unfiltered tracker proxy.

        Args:
            parent (QObject, optional): Qt parent.
        """
        super().__init__(parent)
        self.search_text = ""
        self.hide_completed = False
        self.failed_only = False
        self.warnings_only = False

    def set_tracker_filters(self, search_text="", hide_completed=False, failed_only=False, warnings_only=False):
        """Updates all tracker filter values.

        Args:
            search_text (str, optional): Case-insensitive job-name search.
            hide_completed (bool, optional): Whether successful rows are hidden.
            failed_only (bool, optional): Whether only failed rows are shown.
            warnings_only (bool, optional): Whether only warning rows are shown.
        """
        self.search_text = str(search_text or "").strip().lower()
        self.hide_completed = bool(hide_completed)
        self.failed_only = bool(failed_only)
        self.warnings_only = bool(warnings_only)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Checks whether a job or task should remain visible.

        Args:
            source_row (int): Source-model row.
            source_parent (QModelIndex): Source parent index.

        Returns:
            bool: True when the row matches every active filter.
        """
        source_model = self.sourceModel()
        source_index = source_model.index(source_row, 0, source_parent)
        item = source_index.data(OBJECT_ROLE)
        if not item:
            return False
        job = item.parent_job if isinstance(item, tracker_model.TrackerTask) else item
        if self.search_text and self.search_text not in job.name.lower():
            return False
        if self.failed_only:
            return item.status == tracker_constants.Status.FAILED or bool(item.errors)
        if self.warnings_only:
            return item.status == tracker_constants.Status.COMPLETED_WARNINGS or bool(item.warnings)
        if self.hide_completed and item.status == tracker_constants.Status.COMPLETED:
            return False
        return True


class TrackerTreeModel(ui_qt.QtCore.QAbstractItemModel):
    """Exposes tracker jobs and tasks as a hierarchical Qt model."""

    HEADERS = [
        "#",
        "Job / Task",
        "Progress",
        "Tasks",
        "Errors",
        "Status",
        "Worker",
        "Started",
        "Completed",
        "Elapsed",
    ]

    def __init__(self, session, parent=None):
        """Initializes the tracker tree model.

        Args:
            session (TrackerSession): Session state to expose.
            parent (QObject, optional): Qt parent.
        """
        super().__init__(parent)
        self.session = session

    def index(self, row, column, parent_index=ui_qt.QtCore.QModelIndex()):
        """Creates an index for a job or task row.

        Args:
            row (int): Child row.
            column (int): Column index.
            parent_index (QModelIndex, optional): Parent model index.

        Returns:
            QModelIndex: Requested model index.
        """
        if row < 0 or column < 0:
            return ui_qt.QtCore.QModelIndex()
        if not parent_index.isValid():
            if row < len(self.session.jobs):
                return self.createIndex(row, column, self.session.jobs[row])
            return ui_qt.QtCore.QModelIndex()
        parent_object = parent_index.internalPointer()
        if isinstance(parent_object, tracker_model.TrackerJob) and row < len(parent_object.tasks):
            return self.createIndex(row, column, parent_object.tasks[row])
        return ui_qt.QtCore.QModelIndex()

    def parent(self, child_index):
        """Gets the parent index for a task.

        Args:
            child_index (QModelIndex): Child index.

        Returns:
            QModelIndex: Parent job index or an invalid index.
        """
        if not child_index.isValid():
            return ui_qt.QtCore.QModelIndex()
        item = child_index.internalPointer()
        if isinstance(item, tracker_model.TrackerTask) and item.parent_job:
            try:
                row = self.session.jobs.index(item.parent_job)
            except ValueError:
                return ui_qt.QtCore.QModelIndex()
            return self.createIndex(row, 0, item.parent_job)
        return ui_qt.QtCore.QModelIndex()

    def rowCount(self, parent_index=ui_qt.QtCore.QModelIndex()):
        """Gets the number of child rows.

        Args:
            parent_index (QModelIndex, optional): Parent model index.

        Returns:
            int: Child count.
        """
        if not parent_index.isValid():
            return len(self.session.jobs)
        if parent_index.column() > 0:
            return 0
        item = parent_index.internalPointer()
        return len(item.tasks) if isinstance(item, tracker_model.TrackerJob) else 0

    def columnCount(self, parent_index=ui_qt.QtCore.QModelIndex()):
        """Gets the number of columns.

        Args:
            parent_index (QModelIndex, optional): Unused parent index.

        Returns:
            int: Column count.
        """
        return len(self.HEADERS)

    def data(self, index, role=DISPLAY_ROLE):
        """Gets display, sort, icon, and delegate data.

        Args:
            index (QModelIndex): Requested cell.
            role (int, optional): Qt data role.

        Returns:
            object: Role-specific value.
        """
        if not index.isValid():
            return None
        item = index.internalPointer()
        column = index.column()
        if role == OBJECT_ROLE:
            return item
        if role == STATUS_ROLE:
            return item.status
        if role == PROGRESS_ROLE:
            return item.progress
        if role == DECORATION_ROLE and column == 1:
            return self._get_icon(item)
        if role == SORT_ROLE:
            return self._get_sort_value(item, column)
        if role == TEXT_ALIGNMENT_ROLE and column in {0, 2, 3, 4, 6}:
            return int(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        if role != DISPLAY_ROLE:
            return None
        return self._get_display_value(item, column)

    def headerData(self, section, orientation, role=DISPLAY_ROLE):
        """Gets column header text.

        Args:
            section (int): Header section.
            orientation (Qt.Orientation): Header orientation.
            role (int, optional): Qt data role.

        Returns:
            str or None: Header text.
        """
        if role == DISPLAY_ROLE and orientation == ui_qt.QtLib.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def flags(self, index):
        """Gets read-only item flags.

        Args:
            index (QModelIndex): Cell index.

        Returns:
            Qt.ItemFlags: Enabled and selectable flags.
        """
        if not index.isValid():
            return ui_qt.QtCore.Qt.NoItemFlags
        if ui_qt.IS_PYSIDE6:
            return ui_qt.QtCore.Qt.ItemFlag.ItemIsEnabled | ui_qt.QtCore.Qt.ItemFlag.ItemIsSelectable
        return ui_qt.QtCore.Qt.ItemIsEnabled | ui_qt.QtCore.Qt.ItemIsSelectable

    def reset_rows(self):
        """Rebuilds the model structure after the job list changes.

        Used when a segmented multi-instance run materializes a new segment's
        jobs while running, so newly added rows appear in the view.
        """
        self.beginResetModel()
        self.endResetModel()

    def notify_all_changed(self):
        """Notifies views that all fixed-structure tracker values changed."""
        if not self.session.jobs:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self.session.jobs) - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)
        for job_row, job in enumerate(self.session.jobs):
            if not job.tasks:
                continue
            parent_index = self.index(job_row, 0)
            child_start = self.index(0, 0, parent_index)
            child_end = self.index(len(job.tasks) - 1, self.columnCount() - 1, parent_index)
            self.dataChanged.emit(child_start, child_end)

    @staticmethod
    def _get_display_value(item, column):
        """Gets formatted cell text.

        Args:
            item (TrackerJob or TrackerTask): Row object.
            column (int): Column number.

        Returns:
            object: Display value.
        """
        values = {
            0: item.number,
            1: item.name,
            2: f"{item.progress}%",
            3: item.get_count_text(),
            4: item.errors,
            5: item.status,
            6: item.worker or "-",
            7: format_timestamp(item.started_at),
            8: format_timestamp(item.completed_at),
            9: format_elapsed(item.started_at, item.completed_at),
        }
        return values.get(column, "")

    @staticmethod
    def _get_sort_value(item, column):
        """Gets an unformatted stable sort value.

        Args:
            item (TrackerJob or TrackerTask): Row object.
            column (int): Column number.

        Returns:
            object: Sort value.
        """
        values = {
            0: item.number,
            1: item.name.lower(),
            2: item.progress,
            3: len(item.tasks) if isinstance(item, tracker_model.TrackerJob) else item.total_items,
            4: item.errors,
            5: item.status,
            6: item.worker,
            7: item.started_at,
            8: item.completed_at,
            9: elapsed_seconds(item.started_at, item.completed_at),
        }
        return values.get(column, item.number)

    @staticmethod
    def _get_icon(item):
        """Gets the icon for a job or task.

        Args:
            item (TrackerJob or TrackerTask): Row object.

        Returns:
            QIcon: Row icon.
        """
        if isinstance(item, tracker_model.TrackerJob):
            path = ui_res_lib.Icon.rigger_project if item.is_finalization else ui_res_lib.Icon.ui_progress
        else:
            path = getattr(ui_res_lib.Icon, item.icon, ui_res_lib.Icon.ui_progress)
        return ui_qt.QtGui.QIcon(path)


class ProgressBarDelegate(ui_qt.QtWidgets.QStyledItemDelegate):
    """Paints compact status-colored progress bars."""

    def paint(self, painter, option, index):
        """Paints one progress cell.

        Args:
            painter (QPainter): Active painter.
            option (QStyleOptionViewItem): Cell style options.
            index (QModelIndex): Cell model index.
        """
        progress = int(index.data(PROGRESS_ROLE) or 0)
        status = index.data(STATUS_ROLE) or tracker_constants.Status.QUEUED
        color = ui_qt.QtGui.QColor(tracker_constants.STATUS_COLORS.get(status, "#72777d"))
        rectangle = option.rect.adjusted(5, 5, -5, -5)
        painter.save()
        painter.setRenderHint(ui_qt.QtGui.QPainter.Antialiasing, True)
        painter.setPen(ui_qt.QtGui.QPen(color.darker(125), 1))
        painter.setBrush(ui_qt.QtGui.QColor("#30343a"))
        painter.drawRoundedRect(rectangle, 3, 3)
        fill_width = int(rectangle.width() * max(0, min(100, progress)) / 100.0)
        if fill_width:
            fill_rectangle = ui_qt.QtCore.QRect(rectangle.left(), rectangle.top(), fill_width, rectangle.height())
            painter.setPen(ui_qt.QtCore.Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(fill_rectangle, 3, 3)
        painter.setPen(ui_qt.QtGui.QColor("#f2f2f2"))
        painter.drawText(rectangle, ui_qt.QtLib.AlignmentFlag.AlignCenter, f"{progress}%")
        painter.restore()

    def sizeHint(self, option, index):
        """Gets a readable progress-cell size.

        Args:
            option (QStyleOptionViewItem): Cell style options.
            index (QModelIndex): Cell model index.

        Returns:
            QSize: Preferred cell size.
        """
        return ui_qt.QtCore.QSize(140, 28)


def format_timestamp(value, include_year=True):
    """Formats an ISO timestamp in local time.

    Args:
        value (str): ISO timestamp.
        include_year (bool, optional): Whether to include the year. When False
            the year is omitted to save horizontal space.

    Returns:
        str: Local display timestamp.
    """
    timestamp = parse_timestamp(value)
    if not timestamp:
        return "-"
    time_format = "%Y-%m-%d %H:%M:%S" if include_year else "%m-%d %H:%M:%S"
    return timestamp.astimezone().strftime(time_format)


def format_duration(total_seconds):
    """Formats a duration in seconds as a compact HH:MM:SS string.

    Args:
        total_seconds (float): Duration in seconds.

    Returns:
        str: HH:MM:SS duration.
    """
    total_seconds = int(max(0, total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_elapsed(started_at, completed_at=""):
    """Formats elapsed duration compactly.

    Args:
        started_at (str): Start timestamp.
        completed_at (str, optional): End timestamp.

    Returns:
        str: HH:MM:SS duration.
    """
    if not started_at:
        return "-"
    return format_duration(elapsed_seconds(started_at, completed_at))
