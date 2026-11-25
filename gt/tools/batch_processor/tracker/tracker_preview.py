"""Opens an empty Batch Processor tracker window for editing tracker preferences."""

import argparse
import os
import sys
import tempfile

PREVIEW_PROJECT_NAME = "Preferences Preview"


def open_preview_tracker():
    """Creates an idle tracker window that has no batch attached.

    The scheduler is never ticked, so nothing runs; the window only exists so
    the Preferences menu and view options can be edited without a project.

    Returns:
        TrackerController: Controller owning the window. The caller must keep a
            reference to it while the window is open.
    """
    from gt.tools.batch_processor.tracker import tracker_controller
    from gt.tools.batch_processor.tracker import tracker_model
    from gt.tools.batch_processor.tracker import tracker_scheduler
    from gt.tools.batch_processor.tracker import tracker_view

    session = tracker_model.TrackerSession(
        project_name=PREVIEW_PROJECT_NAME,
        project_path="",
        worker_count=1,
        jobs=[],
        session_dir=os.path.join(tempfile.gettempdir(), "gt_batch_tracker_preview"),
    )
    scheduler = tracker_scheduler.TrackerScheduler(session=session, options=argparse.Namespace())
    view = tracker_view.TrackerView(project_name=PREVIEW_PROJECT_NAME)
    controller = tracker_controller.TrackerController(
        session=session, scheduler=scheduler, view=view, preview_mode=True
    )
    return controller


def add_package_root_to_sys_path():
    """Adds the gt-tools package root so this file can run as a standalone script."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)


def run_preview_process():
    """Runs the preferences preview as its own application.

    A separate process follows each monitor's Windows scaling like a real tracker does,
    instead of inheriting the scaling behavior of the Maya session that opened it.

    Returns:
        int: Qt application exit code.
    """
    add_package_root_to_sys_path()
    import gt.ui.qt_import as ui_qt
    from gt.tools.batch_processor.tracker import tracker_process_utils
    from gt.tools.batch_processor.tracker import tracker_view

    tracker_process_utils.remove_qt_scaling_variables(os.environ)
    if ui_qt.IS_PYSIDE6:
        ui_qt.QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            ui_qt.QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    application = ui_qt.QtWidgets.QApplication(sys.argv)
    application.setApplicationName("Batch Processor Tracker")
    application.setStyle(tracker_view.MenuIconStyle(application.style()))
    application.controller = open_preview_tracker()
    return application.exec_()


if __name__ == "__main__":
    sys.exit(run_preview_process())
