"""
Motion Evaluation Console - Hides console output from the host (Maya, Blender) while scenes load.

Pure Python, used by the runner and by the hosts' session() context managers.
"""

import contextlib
import os
import sys


def flush_stream(stream):
    """Flushes a console stream, ignoring streams that are missing or cannot be flushed.

    Args:
        stream (file): Stream such as sys.stdout. Can be None (for example under pythonw).
    """
    try:
        if stream:
            stream.flush()
    except (OSError, ValueError):
        pass


@contextlib.contextmanager
def quiet_output(enabled=True):
    """Hides everything printed to the console (including Maya's own messages) inside the block.

    Works at the operating-system level, so plugin and scene-loading messages printed by Maya
    are hidden too. Python's own sys.stdout and sys.stderr are swapped for a null stream as well:
    in a Windows console they write with console-only calls that fail on a redirected handle.
    Python exceptions still propagate normally.

    Args:
        enabled (bool): False runs the block without hiding anything.

    Yields:
        None
    """
    if not enabled:
        yield
        return
    saved_streams = (sys.stdout, sys.stderr)
    flush_stream(sys.stdout)
    flush_stream(sys.stderr)
    saved_handles = [os.dup(1), os.dup(2)]
    null_handle = os.open(os.devnull, os.O_WRONLY)
    null_stream = open(os.devnull, "w", encoding="utf-8")
    os.dup2(null_handle, 1)
    os.dup2(null_handle, 2)
    sys.stdout = sys.stderr = null_stream
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved_streams
        null_stream.close()
        os.dup2(saved_handles[0], 1)
        os.dup2(saved_handles[1], 2)
        for handle in saved_handles + [null_handle]:
            os.close(handle)
