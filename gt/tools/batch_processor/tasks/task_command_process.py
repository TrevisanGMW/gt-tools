"""
Batch Processor Command Task Process Runtime

Starts command processes, streams their output, enforces timeouts, kills
process trees, and runs readiness checks. Uses only the standard library and
never imports Maya, so it works in Maya, mayapy, and plain Python.
"""

import os
import queue
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request

CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008
CREATE_BREAKAWAY_FROM_JOB = 0x01000000

_IS_WINDOWS = os.name == "nt"
_STREAM_POLL_SECONDS = 0.2


class CommandResult:
    """Outcome of a finished or launched command process."""

    def __init__(self, exit_code=None, timed_out=False, still_running=False, ready=None, elapsed_seconds=0.0, pid=None):
        """Initializes a command result.

        Args:
            exit_code (int, optional): Process exit code, or None when it did not exit.
            timed_out (bool, optional): Whether the process or readiness wait timed out.
            still_running (bool, optional): Whether the process was left running on purpose.
            ready (bool, optional): Readiness outcome, or None when no check ran.
            elapsed_seconds (float, optional): Time spent in the task.
            pid (int, optional): Process identifier.
        """
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.still_running = still_running
        self.ready = ready
        self.elapsed_seconds = elapsed_seconds
        self.pid = pid


def decode_output_line(raw_line):
    """Decodes one output line without ever raising on bad bytes.

    Args:
        raw_line (bytes or str): Raw process output.

    Returns:
        str: Decoded line without the trailing newline.
    """
    if isinstance(raw_line, bytes):
        text = raw_line.decode("utf-8", errors="replace")
    else:
        text = str(raw_line)
    return text.rstrip("\r\n")


def get_attached_creation_flags():
    """Gets Windows flags for a process the task waits on.

    Returns:
        int: Creation flags; zero outside Windows.
    """
    if not _IS_WINDOWS:
        return 0
    return CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP


def get_detached_creation_flags(hide_window=True):
    """Gets Windows flags for a process that may outlive the task.

    Args:
        hide_window (bool, optional): Hide console windows instead of detaching the console.

    Returns:
        int: Creation flags; zero outside Windows.
    """
    if not _IS_WINDOWS:
        return 0
    console_flag = CREATE_NO_WINDOW if hide_window else DETACHED_PROCESS
    return console_flag | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB


def start_process(command, use_shell, working_directory, environment, stdout, creation_flags):
    """Starts a process, retrying without job breakaway when Windows refuses it.

    Args:
        command (list or str): Command to run.
        use_shell (bool): Whether to run through the system shell.
        working_directory (str): Working directory, or None.
        environment (dict): Process environment.
        stdout (int or file): Standard output target.
        creation_flags (int): Windows creation flags.

    Returns:
        subprocess.Popen: Started process.
    """
    popen_kwargs = {
        "shell": use_shell,
        "cwd": working_directory or None,
        "env": environment,
        "stdin": subprocess.DEVNULL,
        "stdout": stdout,
        "stderr": subprocess.STDOUT if stdout not in (None, subprocess.DEVNULL) else subprocess.DEVNULL,
    }
    if not _IS_WINDOWS:
        popen_kwargs["start_new_session"] = True
        return subprocess.Popen(command, **popen_kwargs)
    try:
        return subprocess.Popen(command, creationflags=creation_flags, **popen_kwargs)
    except OSError:
        if not creation_flags & CREATE_BREAKAWAY_FROM_JOB:
            raise
    return subprocess.Popen(command, creationflags=creation_flags & ~CREATE_BREAKAWAY_FROM_JOB, **popen_kwargs)


def kill_process_tree(process):
    """Kills a process and every child it started.

    Args:
        process (subprocess.Popen): Process to stop.
    """
    if process is None or process.poll() is not None:
        return
    try:
        if _IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
                check=False,
            )
        else:
            import signal

            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def _read_stream_lines(stream, line_queue):
    """Reads process output lines into a queue until the stream closes.

    Args:
        stream (file): Process stdout pipe.
        line_queue (queue.Queue): Queue receiving decoded lines, then None.
    """
    try:
        for raw_line in iter(stream.readline, b""):
            line_queue.put(decode_output_line(raw_line))
    except (OSError, ValueError):
        pass
    finally:
        line_queue.put(None)


def emit_line(line, line_callback, log_handle):
    """Sends one output line to the callback and the optional log file.

    Args:
        line (str): Output line.
        line_callback (callable): Receives each line, or None.
        log_handle (file): Open text log file, or None.
    """
    if callable(line_callback):
        line_callback(line)
    if log_handle:
        log_handle.write(line + "\n")
        log_handle.flush()


def run_and_wait(command, use_shell, working_directory, environment, timeout_seconds=0, line_callback=None,
                 log_handle=None):
    """Runs a command, streams its output, and waits for it to exit.

    Args:
        command (list or str): Command to run.
        use_shell (bool): Whether to run through the system shell.
        working_directory (str): Working directory.
        environment (dict): Process environment.
        timeout_seconds (float, optional): Kill the process tree after this many seconds. Zero waits forever.
        line_callback (callable, optional): Receives each decoded output line.
        log_handle (file, optional): Open text file that also receives every line.

    Returns:
        CommandResult: Exit code and timeout state.
    """
    started_at = time.time()
    process = start_process(
        command, use_shell, working_directory, environment, subprocess.PIPE, get_attached_creation_flags()
    )
    line_queue = queue.Queue()
    reader = threading.Thread(target=_read_stream_lines, args=(process.stdout, line_queue))
    reader.daemon = True
    reader.start()
    timed_out = False
    stream_closed = False
    try:
        while not stream_closed:
            if timeout_seconds and time.time() - started_at > timeout_seconds:
                timed_out = True
                kill_process_tree(process)
                break
            try:
                line = line_queue.get(timeout=_STREAM_POLL_SECONDS)
            except queue.Empty:
                continue
            if line is None:
                stream_closed = True
                continue
            emit_line(line, line_callback, log_handle)
        if not timed_out:
            remaining_seconds = None
            if timeout_seconds:
                remaining_seconds = max(1.0, timeout_seconds - (time.time() - started_at))
            try:
                process.wait(timeout=remaining_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                kill_process_tree(process)
    except BaseException:
        kill_process_tree(process)
        raise
    finally:
        reader.join(timeout=2)
        while True:
            try:
                line = line_queue.get_nowait()
            except queue.Empty:
                break
            if line is not None:
                emit_line(line, line_callback, log_handle)
        if process.stdout:
            process.stdout.close()
    return CommandResult(
        exit_code=None if timed_out else process.returncode,
        timed_out=timed_out,
        elapsed_seconds=time.time() - started_at,
        pid=process.pid,
    )


def launch_detached(command, use_shell, working_directory, environment, log_path=None):
    """Starts a command that keeps running after the task finishes.

    Args:
        command (list or str): Command to run.
        use_shell (bool): Whether to run through the system shell.
        working_directory (str): Working directory.
        environment (dict): Process environment.
        log_path (str, optional): File receiving the process output. Output is discarded when empty.

    Returns:
        subprocess.Popen: Started process.
    """
    if not log_path:
        return start_process(
            command, use_shell, working_directory, environment, subprocess.DEVNULL,
            get_detached_creation_flags(hide_window=False),
        )
    with open(log_path, "ab") as log_file:
        return start_process(
            command, use_shell, working_directory, environment, log_file,
            get_detached_creation_flags(hide_window=True),
        )


class LogFileFollower:
    """Reads lines appended to a log file since the last read."""

    def __init__(self, log_path):
        """Initializes the follower at the current end of the file.

        Args:
            log_path (str): Log file to follow.
        """
        self.log_path = log_path
        self.position = os.path.getsize(log_path) if os.path.isfile(log_path) else 0
        self.pending_bytes = b""

    def read_new_lines(self, flush=False):
        """Reads complete lines appended since the last call.

        Args:
            flush (bool, optional): Also return a trailing partial line.

        Returns:
            list: Decoded lines.
        """
        if not os.path.isfile(self.log_path):
            return []
        try:
            with open(self.log_path, "rb") as log_file:
                log_file.seek(self.position)
                new_bytes = log_file.read()
                self.position = log_file.tell()
        except OSError:
            return []
        data = self.pending_bytes + new_bytes
        raw_lines = data.split(b"\n")
        self.pending_bytes = raw_lines.pop()
        if flush and self.pending_bytes:
            raw_lines.append(self.pending_bytes)
            self.pending_bytes = b""
        return [decode_output_line(raw_line) for raw_line in raw_lines]


def run_until_ready(command, use_shell, working_directory, environment, log_path, ready_probe, ready_timeout_seconds,
                    ready_interval_seconds, line_callback=None, accepted_exit_check=None):
    """Starts a command and waits until a readiness check passes.

    The command may exit (for example ``docker compose up -d``) or keep running
    (for example a local server). A process still running when the check passes
    is left running. If the check never passes, the process tree is killed.

    Args:
        command (list or str): Command to run.
        use_shell (bool): Whether to run through the system shell.
        working_directory (str): Working directory.
        environment (dict): Process environment.
        log_path (str): File receiving the process output while it runs.
        ready_probe (callable): Returns True when the target is ready.
        ready_timeout_seconds (float): Maximum seconds to wait for readiness.
        ready_interval_seconds (float): Seconds between readiness checks.
        line_callback (callable, optional): Receives each decoded output line.
        accepted_exit_check (callable, optional): Receives an exit code and returns
            True when it counts as success. A rejected code stops the wait early.

    Returns:
        CommandResult: Exit code (when the process exited), readiness, and timeout state.
    """
    started_at = time.time()
    follower = LogFileFollower(log_path)
    process = launch_detached(command, use_shell, working_directory, environment, log_path=log_path)
    interval_seconds = max(0.5, float(ready_interval_seconds or 1))
    next_check_at = started_at
    exit_code = None
    try:
        while True:
            for line in follower.read_new_lines():
                if callable(line_callback):
                    line_callback(line)
            if exit_code is None:
                exit_code = process.poll()
                if exit_code is not None:
                    for line in follower.read_new_lines(flush=True):
                        if callable(line_callback):
                            line_callback(line)
                    if callable(accepted_exit_check) and not accepted_exit_check(exit_code):
                        return CommandResult(exit_code=exit_code, ready=False,
                                             elapsed_seconds=time.time() - started_at, pid=process.pid)
            now = time.time()
            if now >= next_check_at:
                if ready_probe():
                    return CommandResult(
                        exit_code=exit_code,
                        ready=True,
                        still_running=exit_code is None,
                        elapsed_seconds=time.time() - started_at,
                        pid=process.pid,
                    )
                next_check_at = now + interval_seconds
            if ready_timeout_seconds and now - started_at > ready_timeout_seconds:
                kill_process_tree(process)
                return CommandResult(exit_code=exit_code, ready=False, timed_out=True,
                                     elapsed_seconds=time.time() - started_at, pid=process.pid)
            time.sleep(_STREAM_POLL_SECONDS)
    except BaseException:
        kill_process_tree(process)
        raise


def check_url(url, timeout_seconds=5.0):
    """Checks whether a URL answers with a 2xx or 3xx status.

    Args:
        url (str): URL to request.
        timeout_seconds (float, optional): Request timeout.

    Returns:
        bool: True when the URL responds successfully.
    """
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "gt-tools-batch-processor"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=timeout_seconds) as response:
            return 200 <= response.getcode() < 400
    except urllib.error.HTTPError as error:
        return 200 <= error.code < 400
    except (urllib.error.URLError, OSError, ValueError):
        return False


def check_port(host, port, timeout_seconds=3.0):
    """Checks whether a TCP port accepts connections.

    Args:
        host (str): Host name or address.
        port (int): TCP port.
        timeout_seconds (float, optional): Connection timeout.

    Returns:
        bool: True when a connection succeeds.
    """
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_seconds):
            return True
    except (OSError, ValueError):
        return False


def check_file(path):
    """Checks whether a file or folder exists.

    Args:
        path (str): Path to check.

    Returns:
        bool: True when the path exists.
    """
    return bool(path) and os.path.exists(path)


def check_command(command, use_shell, working_directory, environment, timeout_seconds=30.0):
    """Checks whether a command exits with code zero.

    Args:
        command (list or str): Command to run.
        use_shell (bool): Whether to run through the system shell.
        working_directory (str): Working directory.
        environment (dict): Process environment.
        timeout_seconds (float, optional): Maximum seconds for one check.

    Returns:
        bool: True when the command exits with code zero.
    """
    try:
        result = run_and_wait(command, use_shell, working_directory, environment, timeout_seconds=timeout_seconds)
    except OSError:
        return False
    return result.exit_code == 0
