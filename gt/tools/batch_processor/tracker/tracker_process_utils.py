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

