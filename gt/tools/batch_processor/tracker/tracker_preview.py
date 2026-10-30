"""Opens an empty Batch Processor tracker window for editing tracker preferences."""

import argparse
import os
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
