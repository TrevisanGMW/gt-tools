"""
Unit tests for the Batch Processor Command task.

Covers the pure command helpers, the process runtime (using the current Python
interpreter as the child program), and the task's validation and execution.
"""

import logging
import os
import shutil
import socket
import sys
import tempfile
import threading
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Scripts
test_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker
from gt.tools.batch_processor.tasks import task_command
from gt.tools.batch_processor.tasks import task_command_process as command_process
from gt.tools.batch_processor.tasks import task_command_utils as command_utils


def build_python_arguments(code):
    """Builds Command task argument text that runs inline Python code.

    Args:
        code (str): Python code without double quotes.

    Returns:
        str: Argument text for the Command task.
    """
    return f'-c "{code}"'


class TestCommandUtils(unittest.TestCase):
    """Tests pure command helpers."""

    def test_split_arguments_keeps_backslashes_and_quoted_spaces(self):
        """Checks Windows paths and quoted groups survive argument parsing."""
        result = command_utils.split_arguments('run "C:\\My Folder\\file.txt" -v\n# comment\n\n--flag=1')
        expected = ["run", "C:\\My Folder\\file.txt", "-v", "--flag=1"]
        self.assertEqual(expected, result)

    def test_split_arguments_keeps_empty_quoted_argument(self):
        """Checks an empty quoted argument is passed as an empty string."""
        result = command_utils.split_arguments('--name ""')
        expected = ["--name", ""]
        self.assertEqual(expected, result)

    def test_parse_environment_overrides(self):
        """Checks KEY=VALUE parsing, comments, and invalid lines."""
        pairs, errors = command_utils.parse_environment_overrides("A=1\n# note\nB = two=2\nbad line\n1X=3\nEMPTY=")
        expected_pairs = [("A", "1"), ("B", "two=2"), ("EMPTY", "")]
        self.assertEqual(expected_pairs, pairs)
        self.assertEqual(2, len(errors))

    def test_build_process_environment_expands_references_in_order(self):
        """Checks overrides can extend inherited and earlier values."""
        environment = command_utils.build_process_environment(
            base_environment={"PATH": "base"},
            inherit_environment=True,
            batch_values={"BATCH_TASK": "Command"},
            override_pairs=[("TOOLS", "C:/tools"), ("PATH", "${TOOLS};%PATH%")],
        )
        self.assertEqual("C:/tools;base", command_utils.get_environment_value(environment, "PATH"))
        self.assertEqual("Command", environment["BATCH_TASK"])

    def test_build_process_environment_without_inherit_keeps_essentials(self):
        """Checks a clean environment still keeps PATH."""
        environment = command_utils.build_process_environment(
            base_environment={"PATH": "base", "SOMETHING_ELSE": "x"},
            inherit_environment=False,
            batch_values={},
            override_pairs=[],
        )
        self.assertEqual("base", command_utils.get_environment_value(environment, "PATH"))
        self.assertNotIn("SOMETHING_ELSE", environment)

    def test_parse_exit_codes(self):
        """Checks single values, ranges, wildcard, and errors."""
        self.assertEqual(({0}, []), command_utils.parse_exit_codes(""))
        self.assertEqual(({0, 3, 4, 5}, []), command_utils.parse_exit_codes("0, 3-5"))
        self.assertEqual((None, []), command_utils.parse_exit_codes("*"))
        _, errors = command_utils.parse_exit_codes("0, abc, 5-2")
        self.assertEqual(2, len(errors))

    def test_is_exit_code_accepted(self):
        """Checks accepted-code evaluation including the wildcard."""
        self.assertTrue(command_utils.is_exit_code_accepted(3, {0, 3}))
        self.assertFalse(command_utils.is_exit_code_accepted(1, {0}))
        self.assertTrue(command_utils.is_exit_code_accepted(99, None))

    def test_mask_secrets(self):
        """Checks secret-looking override values are hidden."""
        pairs = [("HF_TOKEN", "abcd1234"), ("MODE", "fast")]
        expected = "token=******** mode=fast"
        self.assertEqual(expected, command_utils.mask_secrets("token=abcd1234 mode=fast", pairs))
        expected_preview = ["HF_TOKEN=********", "MODE=fast"]
        self.assertEqual(expected_preview, command_utils.format_environment_preview(pairs))

    def test_parse_host_port(self):
        """Checks port-only, host:port, and invalid targets."""
        self.assertEqual(("127.0.0.1", 8000), command_utils.parse_host_port("8000"))
        self.assertEqual(("localhost", 22), command_utils.parse_host_port("localhost:22"))
        self.assertEqual((None, None), command_utils.parse_host_port("localhost"))

    def test_validate_ready_target(self):
        """Checks readiness target validation per check type."""
        self.assertEqual([], command_utils.validate_ready_target(command_utils.ReadyCheck.URL, "http://x/health"))
        self.assertEqual(1, len(command_utils.validate_ready_target(command_utils.ReadyCheck.URL, "x/health")))
        self.assertEqual(1, len(command_utils.validate_ready_target(command_utils.ReadyCheck.PORT, "99999")))
        self.assertEqual(1, len(command_utils.validate_ready_target(command_utils.ReadyCheck.FILE, "")))

    def test_build_shell_command_powershell_is_encoded(self):
        """Checks PowerShell text is passed through -EncodedCommand."""
        command, use_shell = command_utils.build_shell_command("Write-Output 'hi'", command_utils.ShellType.POWERSHELL)
        self.assertFalse(use_shell)
        self.assertIn("-EncodedCommand", command)

    def test_build_shell_command_system_joins_lines(self):
        """Checks the system shell receives one command string."""
        command, use_shell = command_utils.build_shell_command("echo a\n# skip\necho b", command_utils.ShellType.SYSTEM)
        self.assertTrue(use_shell)
        expected = "echo a && echo b" if os.name == "nt" else "echo a\necho b"
        self.assertEqual(expected, command)


class TestCommandProcess(unittest.TestCase):
    """Tests the process runtime with real child processes."""

    def setUp(self):
        """Creates a temporary folder."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Removes the temporary folder."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_and_wait_streams_output_and_exit_code(self):
        """Checks streamed output, UTF-8 decoding, and the exit code."""
        lines = []
        code = "import sys; sys.stdout.buffer.write('ok \\u2713\\n'.encode('utf-8')); sys.exit(3)"
        result = command_process.run_and_wait(
            [sys.executable, "-c", code], False, self.temp_dir, dict(os.environ), line_callback=lines.append
        )
        self.assertEqual(3, result.exit_code)
        self.assertFalse(result.timed_out)
        self.assertEqual(["ok \u2713"], lines)

    def test_run_and_wait_timeout_kills_process(self):
        """Checks a timeout stops a long-running process."""
        result = command_process.run_and_wait(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            False,
            self.temp_dir,
            dict(os.environ),
            timeout_seconds=1,
        )
        self.assertTrue(result.timed_out)
        self.assertIsNone(result.exit_code)
        self.assertLess(result.elapsed_seconds, 20)

    def test_run_until_ready_when_command_exits_then_file_appears(self):
        """Checks the ready wait continues after a quick command exit."""
        flag_path = os.path.join(self.temp_dir, "ready.flag")
        log_path = os.path.join(self.temp_dir, "out.log")
        code = f"open(r'{flag_path}', 'w').close(); print('started')"
        lines = []
        result = command_process.run_until_ready(
            [sys.executable, "-c", code],
            False,
            self.temp_dir,
            dict(os.environ),
            log_path=log_path,
            ready_probe=lambda: command_process.check_file(flag_path),
            ready_timeout_seconds=30,
            ready_interval_seconds=0.5,
            line_callback=lines.append,
        )
        self.assertTrue(result.ready)
        self.assertIn("started", lines)

    def test_run_until_ready_stops_on_rejected_exit_code(self):
        """Checks a failing command ends the ready wait early."""
        result = command_process.run_until_ready(
            [sys.executable, "-c", "import sys; sys.exit(2)"],
            False,
            self.temp_dir,
            dict(os.environ),
            log_path=os.path.join(self.temp_dir, "out.log"),
            ready_probe=lambda: False,
            ready_timeout_seconds=30,
            ready_interval_seconds=0.5,
            accepted_exit_check=lambda exit_code: exit_code == 0,
        )
        self.assertFalse(result.ready)
        self.assertEqual(2, result.exit_code)
        self.assertFalse(result.timed_out)

    def test_run_until_ready_times_out_and_kills_running_process(self):
        """Checks a never-ready process is stopped at the timeout."""
        result = command_process.run_until_ready(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            False,
            self.temp_dir,
            dict(os.environ),
            log_path=os.path.join(self.temp_dir, "out.log"),
            ready_probe=lambda: False,
            ready_timeout_seconds=1,
            ready_interval_seconds=0.5,
        )
        self.assertFalse(result.ready)
        self.assertTrue(result.timed_out)

    def test_check_port(self):
        """Checks the port probe against a listening socket."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        accept_thread = threading.Thread(target=lambda: server.accept()[0].close())
        accept_thread.daemon = True
        accept_thread.start()
        try:
            self.assertTrue(command_process.check_port("127.0.0.1", port))
        finally:
            server.close()

    def test_log_file_follower_reads_only_new_complete_lines(self):
        """Checks the follower returns appended complete lines once."""
        log_path = os.path.join(self.temp_dir, "follow.log")
        with open(log_path, "wb") as log_file:
            log_file.write(b"old\n")
        follower = command_process.LogFileFollower(log_path)
        with open(log_path, "ab") as log_file:
            log_file.write(b"new 1\nnew 2\npart")
        self.assertEqual(["new 1", "new 2"], follower.read_new_lines())
        self.assertEqual(["part"], follower.read_new_lines(flush=True))


class TestTaskCommand(unittest.TestCase):
    """Tests Command task validation and execution."""

    def setUp(self):
        """Creates a project with a project directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.project = batch_processor_model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.temp_dir
        self.messages = []
        self.warnings = []
        self.context = {"report_message": self.messages.append, "report_warning": self.warnings.append}

    def tearDown(self):
        """Removes the temporary folder."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_task(self, **settings):
        """Creates a Command task added to the project.

        Args:
            **settings: Task settings to override.

        Returns:
            TaskCommand: Configured task.
        """
        task = tasks.create_task(task_type=constants.TaskType.COMMAND)
        task.settings.update(settings)
        self.project.add_task(task)
        return task

    def test_task_is_registered_and_round_trips(self):
        """Checks the task type registers and serializes."""
        task = self.create_task(executable="python", arguments="-V")
        restored = tasks.create_task_from_dict(task.to_dict())
        self.assertIsInstance(restored, task_command.TaskCommand)
        self.assertEqual("-V", restored.settings["arguments"])

    def test_run_once_makes_task_aggregate(self):
        """Checks the run-once options switch the task to aggregate execution."""
        task = self.create_task()
        self.assertFalse(task.is_aggregate_task)
        task.settings["run_once_after_multi_instance"] = True
        self.assertTrue(task.is_aggregate_task)
        self.assertIn(constants.TaskType.COMMAND, batch_processor_worker.RUN_ONCE_PASSTHROUGH_TASK_TYPES)

    def test_validate_reports_missing_executable(self):
        """Checks an unknown program is a validation error."""
        task = self.create_task(executable="definitely_not_a_real_program_123")
        result = task.validate(self.project)
        self.assertEqual(1, len(result.errors))

    def test_validate_reports_bad_exit_codes_and_environment(self):
        """Checks invalid rule text is reported."""
        task = self.create_task(
            executable=sys.executable,
            accepted_exit_codes="zero",
            environment_overrides="no equals sign",
        )
        result = task.validate(self.project)
        self.assertEqual(2, len(result.errors))

    def test_validate_skips_executable_check_for_per_item_tokens(self):
        """Checks per-item executables are not resolved during validation."""
        task = self.create_task(executable="{input-file}.exe")
        result = task.validate(self.project)
        self.assertEqual([], result.errors)

    def test_execute_run_once_passes_items_and_environment(self):
        """Checks a run-once command sees overrides and BATCH_* values and returns items."""
        output_path = os.path.join(self.temp_dir, "env.txt")
        code = (
            "import os; open(os.environ['OUT'], 'w').write("
            "os.environ['GREETING'] + '|' + os.environ['BATCH_PROJECT_DIR'])"
        )
        task = self.create_task(
            executable=sys.executable,
            arguments=build_python_arguments(code),
            environment_overrides=f"OUT={output_path}\nGREETING=hello",
            run_once_before_multi_instance=True,
        )
        incoming_items = [tasks.WorkItem(source_path="a.ma")]
        context = dict(self.context, work_items=incoming_items)
        result = task.execute(None, self.project, self.temp_dir, context=context)
        self.assertEqual(incoming_items, result)
        with open(output_path) as output_file:
            self.assertEqual(f"hello|{self.temp_dir}", output_file.read())

    def test_execute_per_item_returns_item_and_streams_output(self):
        """Checks a per-item command returns the same item and logs output."""
        task = self.create_task(executable=sys.executable, arguments=build_python_arguments("print('line one')"))
        work_item = tasks.WorkItem(source_path=os.path.join(self.temp_dir, "a.ma"))
        result = task.execute(work_item, self.project, self.temp_dir, context=self.context)
        self.assertIs(work_item, result)
        self.assertIn("| line one", self.messages)

    def test_execute_failure_actions(self):
        """Checks Fail raises, Warning reports, and Ignore continues quietly."""
        arguments = build_python_arguments("import sys; sys.exit(4)")
        task = self.create_task(executable=sys.executable, arguments=arguments)
        work_item = tasks.WorkItem(source_path=os.path.join(self.temp_dir, "a.ma"))
        with self.assertRaises(RuntimeError):
            task.execute(work_item, self.project, self.temp_dir, context=self.context)
        task.settings["on_failure"] = command_utils.FailureAction.WARNING
        task.execute(work_item, self.project, self.temp_dir, context=self.context)
        self.assertEqual(1, len(self.warnings))
        task.settings["on_failure"] = command_utils.FailureAction.IGNORE
        task.execute(work_item, self.project, self.temp_dir, context=self.context)
        self.assertEqual(1, len(self.warnings))
        task.settings["accepted_exit_codes"] = "0-4"
        task.settings["on_failure"] = command_utils.FailureAction.FAIL
        task.execute(work_item, self.project, self.temp_dir, context=self.context)

    def test_execute_shell_mode_writes_log_file(self):
        """Checks shell mode runs and appends output to the log file."""
        log_path = os.path.join(self.temp_dir, "logs", "command.log")
        task = self.create_task(
            command_mode=command_utils.CommandMode.SHELL,
            command_text="echo shell_ok",
            write_output_log=True,
            output_log_path=log_path,
            run_once_after_multi_instance=True,
        )
        task.execute(None, self.project, self.temp_dir, context=dict(self.context, work_items=[]))
        with open(log_path, encoding="utf-8") as log_file:
            self.assertIn("shell_ok", log_file.read())

    def test_execute_wait_until_ready_with_file_check(self):
        """Checks the ready mode with a command that creates the ready file."""
        flag_path = os.path.join(self.temp_dir, "ready.flag")
        code = f"open(r'{flag_path}', 'w').close()"
        task = self.create_task(
            executable=sys.executable,
            arguments=build_python_arguments(code),
            wait_mode=command_utils.WaitMode.WAIT_UNTIL_READY,
            ready_check=command_utils.ReadyCheck.FILE,
            ready_target=flag_path,
            ready_timeout_seconds=30,
            ready_interval_seconds=1,
            run_once_before_multi_instance=True,
        )
        task.execute(None, self.project, self.temp_dir, context=dict(self.context, work_items=[]))
        self.assertTrue(any("Ready after" in message for message in self.messages))

    def test_preview_lines_mask_secrets(self):
        """Checks the preview shows the command and masks secrets."""
        task = self.create_task(executable=sys.executable, arguments="-V", environment_overrides="API_KEY=secret123")
        preview_text = "\n".join(task.build_preview_lines(self.project))
        self.assertIn("Command:", preview_text)
        self.assertIn("API_KEY=********", preview_text)
        self.assertNotIn("secret123", preview_text)


if __name__ == "__main__":
    unittest.main()
