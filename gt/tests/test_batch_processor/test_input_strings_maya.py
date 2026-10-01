"""Opt-in Maya integration checks: set GT_TEST_INPUT_STRINGS_MAYA=1 under mayapy."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker as worker
from gt.tools.batch_processor import batch_processor_maya as maya_runtime


@unittest.skipUnless(os.environ.get("GT_TEST_INPUT_STRINGS_MAYA") == "1", "Opt-in Maya integration test")
class TestInputStringsMaya(unittest.TestCase):
    """Checks actual empty-scene generation and saved results in both worker paths."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone only when no Maya session is already active."""
        import maya.standalone

        cls.initialized = not maya_runtime.is_maya_session_available()
        if cls.initialized:
            maya.standalone.initialize(name="python")
        cls.commands = maya_runtime.get_maya_cmds(initialize_standalone=False)

    @classmethod
    def tearDownClass(cls):
        """Uninitializes only the standalone session created by this test."""
        if cls.initialized:
            import maya.standalone

            maya.standalone.uninitialize()

    def setUp(self):
        """Creates an isolated string-to-Python project and a disposable initial scene."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.values = ["A person walks.", "A person runs — café.", "A person walks."]
        self.input_task = tasks.TaskInputStrings(settings={"strings": self.values})
        self.python_task = tasks.TaskPythonScript(settings={
            "source_mode": "incoming", "target_path": "{project-dir}/results",
            "script_text": (
                "import maya.cmds as cmds\n"
                "assert not cmds.objExists('row_result')\n"
                "assert not cmds.objExists('previous_scene_node')\n"
                "node = cmds.createNode('transform', name='row_result')\n"
                "cmds.addAttr(node, longName='inputText', dataType='string')\n"
                "cmds.setAttr(node + '.inputText', env['input-string'], type='string')\n"
            ),
        })
        self.project.tasks = [self.input_task, self.python_task]
        self.commands.file(new=True, force=True)
        self.commands.createNode("transform", name="previous_scene_node")

    def check_outputs(self):
        """Checks saved per-row values and absence of virtual source files."""
        for item, value in zip(self.input_task.prepare(self.project), self.values):
            path = os.path.join(self.directory.name, "results", os.path.basename(item.source_path))
            self.commands.file(path, open=True, force=True, executeScriptNodes=False)
            self.assertEqual(value, self.commands.getAttr("row_result.inputText"))
            self.assertFalse(os.path.exists(item.source_path))

    def test_single_runner(self):
        """Creates and saves one isolated scene per string through the real Python task."""
        tracker = worker.SingleInstanceBatchRunner().run(self.project)
        self.assertEqual(0, tracker.failed)
        self.assertEqual(3, tracker.succeeded)
        self.check_outputs()

    def test_tracker_worker_entry_point(self):
        """Reconstructs each scheduled virtual identity from the saved project snapshot."""
        from gt.tools.batch_processor.tracker import tracker_worker

        project_path = os.path.join(self.directory.name, "snapshot.batch")
        with open(project_path, "w", encoding="utf-8") as project_file:
            json.dump(self.project.to_dict(), project_file)
        for index, item in enumerate(self.input_task.prepare(self.project), 1):
            event_path = os.path.join(self.directory.name, f"events_{index}.jsonl")
            arguments = ["tracker_worker", "--project-file", project_path,
                         "--source-file", item.source_path, "--job-id", f"job-{index}",
                         "--event-file", event_path, "--task-id", self.python_task.id]
            with mock.patch.object(sys, "argv", arguments), self.assertRaises(SystemExit) as result:
                tracker_worker.main()
            self.assertEqual(0, result.exception.code)
        self.check_outputs()
