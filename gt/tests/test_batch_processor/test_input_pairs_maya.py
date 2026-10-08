"""Opt-in Maya integration checks for custom names and pair metadata in both runners."""

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
from gt.tools.batch_processor.tasks.task_input_pairs import create_pair


@unittest.skipUnless(os.environ.get("GT_TEST_INPUT_PAIRS_MAYA") == "1", "Opt-in Maya integration test")
class TestInputPairsMaya(unittest.TestCase):
    """Checks actual scene creation, naming, and pair values without physical input scenes."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone only when there is no active Maya session."""
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
        """Creates a named-pair project whose Python task writes both runtime values."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.rows = [create_pair("Custom Walk", "A person walks"), create_pair("Custom Run", "A person runs")]
        self.input_task = tasks.TaskInputPairs(settings={"input_mode": "manual", "manual_pairs": self.rows})
        self.python_task = tasks.TaskPythonScript(settings={
            "source_mode": "incoming", "target_path": "{project-dir}/results/{input-file}",
            "script_text": (
                "import maya.cmds as cmds\n"
                "assert not cmds.objExists('row_result')\n"
                "assert not cmds.objExists('previous_scene_node')\n"
                "node = cmds.createNode('transform', name='row_result')\n"
                "cmds.addAttr(node, longName='inputFile', dataType='string')\n"
                "cmds.addAttr(node, longName='inputText', dataType='string')\n"
                "cmds.setAttr(node + '.inputFile', env['input-file'], type='string')\n"
                "cmds.setAttr(node + '.inputText', env['input-string'], type='string')\n"
            ),
        })
        self.project.tasks = [self.input_task, self.python_task]
        self.commands.file(new=True, force=True)
        self.commands.createNode("transform", name="previous_scene_node")

    def check_outputs(self):
        """Checks the custom names, resolved paths, and scene attributes for both rows."""
        for item in self.input_task.prepare(self.project):
            filename = item.metadata["input_file"]
            path = os.path.join(self.directory.name, "results", filename, f"{filename}.ma")
            self.assertTrue(os.path.isfile(path), path)
            self.commands.file(path, open=True, force=True, executeScriptNodes=False)
            self.assertEqual(filename, self.commands.getAttr("row_result.inputFile"))
            self.assertEqual(item.metadata["input_string"], self.commands.getAttr("row_result.inputText"))
            self.assertFalse(os.path.exists(item.source_path))
        self.assertFalse(os.path.exists(self.input_task.get_input_dir(self.project)))

    def test_single_instance_runner(self):
        """Runs each manual pair in a fresh scene and saves it under its custom name."""
        tracker = worker.SingleInstanceBatchRunner().run(self.project)
        self.assertEqual(0, tracker.failed)
        self.assertEqual(2, tracker.succeeded)
        self.check_outputs()

    def test_tracker_worker_entry_point(self):
        """Reconstructs pair metadata and custom filenames from a saved worker snapshot."""
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
