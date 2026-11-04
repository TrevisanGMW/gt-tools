"""Opens the Batch Processor editor outside of Maya, in its own application.

Run with mayapy, optionally with a project to open or a hand-off from a Maya session::

    mayapy standalone_main.py [--project-file my_project.batch]
"""

import argparse
import os
import sys


def add_package_root_to_sys_path():
    """Adds the gt-tools package root so this file can run as a standalone script."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)


def parse_args():
    """Parses launch arguments.

    Returns:
        argparse.Namespace: Parsed options.
    """
    parser = argparse.ArgumentParser(description="Batch Processor (standalone)")
    parser.add_argument("--project-file", default="", help="Saved .batch project to open.")
    parser.add_argument("--recovery-file", default="", help="Hand-off file written by a Maya session.")
    parser.add_argument("--ready-file", default="", help="File written once the project has loaded.")
    parser.add_argument("--hide-console", action="store_true", help="Hide this process's console window.")
    return parser.parse_args()


def hide_console_window():
    """Hides the console window that mayapy opens when started from a shortcut or bat file."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            ctypes.windll.user32.ShowWindow(console_window, 0)
    except Exception:
        return


def create_application():
    """Creates the Qt application so it follows each monitor's Windows scaling.

    Returns:
        QApplication: Application instance.
    """
    import gt.ui.qt_import as ui_qt
    from gt.tools.batch_processor.tracker import tracker_process_utils

    tracker_process_utils.remove_qt_scaling_variables(os.environ)
    if ui_qt.IS_PYSIDE6:
        ui_qt.QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            ui_qt.QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication(sys.argv)
    application.setApplicationName("Batch Processor")
    return application


def run(args):
    """Builds the editor, loads the requested project, and runs the application.

    Args:
        args (argparse.Namespace): Launch options.

    Returns:
        int: Application exit code.
    """
    from gt.tools.batch_processor import __version__
    from gt.tools.batch_processor import batch_processor_controller
    from gt.tools.batch_processor import batch_processor_handoff
    from gt.tools.batch_processor import batch_processor_model
    from gt.tools.batch_processor import batch_processor_view

    application = create_application()
    view = batch_processor_view.BatchProcessorView(parent=None, version=__version__)
    model = batch_processor_model.BatchProcessorModel()
    controller = batch_processor_controller.BatchProcessorController(model=model, view=view)
    application.controller = controller
    try:
        if args.recovery_file:
            recovery_data = batch_processor_handoff.read_json_file(args.recovery_file)
            if not recovery_data.get("project"):
                raise ValueError(f"Hand-off file is missing or empty: {args.recovery_file}")
            controller.restore_from_recovery(recovery_data)
            try:
                os.remove(args.recovery_file)
            except OSError:
                pass
        elif args.project_file:
            controller.load_project_from_path(args.project_file)
    except Exception as error:
        batch_processor_handoff.write_ready_file(args.ready_file, status="failed", error=str(error))
        raise
    batch_processor_handoff.write_ready_file(args.ready_file)
    try:
        return application.exec_()
    finally:
        try:
            from gt.tools.batch_processor import batch_processor_maya

            batch_processor_maya.shutdown_standalone()
        except Exception:
            pass


def main():
    """Entry point."""
    add_package_root_to_sys_path()
    args = parse_args()
    if args.hide_console:
        hide_console_window()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
