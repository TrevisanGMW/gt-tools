"""Process helpers for the standalone Batch Processor tracker."""

import os
import signal
import subprocess
import sys


def terminate_process_tree(process, force=False):
    """Terminates a worker and its descendants.

    Args:
        process (subprocess.Popen): Root worker process.
        force (bool, optional): Whether to force termination.
    """
    if not process or process.poll() is not None:
        return
    if sys.platform == "win32":
        command = ["taskkill", "/PID", str(process.pid), "/T"]
        if force:
            command.append("/F")
        subprocess.run(command, capture_output=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        return
    try:
        process_group = os.getpgid(process.pid)
        os.killpg(process_group, signal.SIGKILL if force else signal.SIGTERM)
    except (OSError, ProcessLookupError):
        try:
            process.kill() if force else process.terminate()
        except OSError:
            pass



QT_SCALING_VARIABLES = (
    "QT_ENABLE_HIGHDPI_SCALING",
    "QT_AUTO_SCREEN_SCALE_FACTOR",
    "QT_SCALE_FACTOR",
    "QT_SCREEN_SCALE_FACTORS",
    "QT_USE_PHYSICAL_DPI",
    "QT_FONT_DPI",
    "QT_DEVICE_PIXEL_RATIO",
)


def remove_qt_scaling_variables(environment):
    """Drops inherited Qt scaling overrides so windows follow each monitor's Windows scaling.

    Maya or other hosts can export variables that turn high-DPI scaling off or force a
    fixed factor, which makes a window tiny on a 150% monitor.

    Args:
        environment (dict): Environment mapping to clean in place, such as ``os.environ``.

    Returns:
        list: Names of the variables that were removed.
    """
    removed = []
    for variable_name in QT_SCALING_VARIABLES:
        if variable_name in environment:
            environment.pop(variable_name, None)
            removed.append(variable_name)
    return removed
