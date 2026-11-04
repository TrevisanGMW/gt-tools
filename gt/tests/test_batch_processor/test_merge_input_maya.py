"""Opt-in Maya integration checks for the Merge Input task.

Run with: set GT_TEST_MERGE_INPUT_MAYA=1 and mayapy -m unittest gt.tests.test_batch_processor.test_merge_input_maya
"""

import os
import tempfile
import unittest

from gt.tools.batch_processor import batch_processor_maya as maya_runtime
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_merge_input
from gt.tools.batch_processor.tasks import task_merge_input_utils as merge_utils
from gt.tools.batch_processor.tasks import task_utils


@unittest.skipUnless(os.environ.get("GT_TEST_MERGE_INPUT_MAYA") == "1", "Opt-in Maya integration test")
class TestMergeInputMaya(unittest.TestCase):
    """Merges real scenes in mayapy and checks the resulting scene."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone only when there is no active Maya session."""
        import maya.standalone

        cls.initialized = not maya_runtime.is_maya_session_available()
        if cls.initialized:
            maya.standalone.initialize(name="python")
        cls.cmds = maya_runtime.get_maya_cmds(initialize_standalone=False)

    @classmethod
    def tearDownClass(cls):
        """Uninitializes only the standalone session created by this test."""
        if cls.initialized:
            import maya.standalone

            maya.standalone.uninitialize()

    def setUp(self):
        """Writes two animated scenes that share node names."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.project.project_file_path = os.path.join(self.directory.name, "project.batch")
        self.output_dir = os.path.join(self.directory.name, "merged")
        self.walk_path = self.write_scene("walk.ma", key_range=(1, 10), playback_range=(1, 48))
        self.run_path = self.write_scene("run.ma", key_range=(5, 30), playback_range=(5, 30))
        self.work_items = [task_base.WorkItem(source_path=path) for path in (self.run_path, self.walk_path)]

    def write_scene(self, file_name, key_range, playback_range):
        """Writes a scene with an animated cube and a stray camera.

        Args:
            file_name (str): Scene file name.
            key_range (tuple): First and last key frame.
            playback_range (tuple): Saved playback range.

        Returns:
            str: Scene path.
        """
        cmds = self.cmds
        cmds.file(new=True, force=True)
        cube = cmds.polyCube(name="box")[0]
        cmds.setKeyframe(cube, attribute="translateY", time=key_range[0], value=0)
        cmds.setKeyframe(cube, attribute="translateY", time=key_range[1], value=10)
        camera_transform = cmds.camera()[0]
        cmds.rename(camera_transform, "unused_cam")
        cmds.playbackOptions(minTime=playback_range[0], maxTime=playback_range[1])
        scene_path = os.path.join(self.directory.name, file_name)
        cmds.file(rename=scene_path)
        cmds.file(save=True, force=True, type="mayaAscii")
        return scene_path

    def run_task(self, **settings):
        """Runs Merge Input on both fixture scenes.

        Args:
            **settings: Task setting overrides.

        Returns:
            tuple: (task, result work item).
        """
        task = self.project.add_task(task_merge_input.TaskMergeInput(settings=settings))
        result = task.execute(None, self.project, self.output_dir, context={"work_items": list(self.work_items)})
        return task, result

    def get_playback_range(self):
        """Gets the current playback range.

        Returns:
            tuple: (start, end).
        """
        return (
            self.cmds.playbackOptions(query=True, minTime=True),
            self.cmds.playbackOptions(query=True, maxTime=True),
        )

    def test_import_defaults_use_namespaces_and_keyframe_range(self):
        task, result = self.run_task()
        self.assertTrue(os.path.isfile(result.current_path))
        self.assertTrue(self.cmds.objExists("run:box"))
        self.assertTrue(self.cmds.objExists("walk:box"))
        self.assertTrue(self.cmds.objExists("walk:unused_cam"))
        expected = (1.0, 30.0)
        self.assertEqual(expected, self.get_playback_range())
        expected = 2
        self.assertEqual(expected, result.metadata["merged_inputs"])

    def test_remove_namespace_renames_clashes(self):
        self.run_task(remove_namespace=True)
        box_transforms = sorted(self.cmds.ls("box*", type="transform") or [])
        expected = ["box", "box1"]
        self.assertEqual(expected, box_transforms)
        self.assertFalse(self.cmds.namespace(exists=":run"))

    def test_organization_and_sequential_timing(self):
        self.run_task(
            group_each_input=True,
            group_all_inputs=True,
            display_layer_per_input=True,
            offset_inputs=True,
            input_offset=[100.0, 0.0, 0.0],
            timing_mode=merge_utils.TIMING_SEQUENTIAL,
            sequential_gap_frames=5,
            output_mode=task_base.OUTPUT_MODE_PASSTHROUGH,
        )
        expected = ["run_grp", "walk_grp"]
        self.assertEqual(expected, sorted(self.cmds.listRelatives("merged_inputs_grp", children=True)))
        expected = 100.0
        self.assertEqual(expected, self.cmds.getAttr("walk_grp.translateX"))
        self.assertTrue(self.cmds.objExists("walk_lyr"))
        # run (5-30) stays first; walk (1-10) is shifted to start at 30 + 5.
        expected = (5.0, 44.0)
        self.assertEqual(expected, self.get_playback_range())

    def test_reference_mode_with_groups(self):
        self.run_task(load_mode=merge_utils.LOAD_MODE_REFERENCE, group_each_input=True)
        references = [node for node in self.cmds.ls(type="reference") if "sharedReferenceNode" not in node]
        expected = 2
        self.assertEqual(expected, len(references))
        self.assertTrue(self.cmds.referenceQuery("run:box", isNodeReferenced=True))
        expected = ["|run_grp|run:box"]
        self.assertEqual(expected, self.cmds.ls("run:box", long=True))
        expected = (1.0, 30.0)
        self.assertEqual(expected, self.get_playback_range())

    def test_first_input_uses_saved_range(self):
        self.run_task(time_range_mode=merge_utils.TIME_RANGE_FIRST_INPUT, sort_inputs_by_name=True)
        expected = (5.0, 30.0)  # run.ma sorts first.
        self.assertEqual(expected, self.get_playback_range())

    def test_sample_scripts_run(self):
        samples = {sample["relative_path"]: sample["path"] for sample in task_utils.get_script_samples("merge_input")}
        delete_script = task_utils.load_script_file(samples[os.path.join("per_input", "delete_nodes_in_list.py")])
        post_script = "\n".join(
            task_utils.load_script_file(samples[os.path.join("post_merge", name)])
            for name in ("set_antialiasing.py", "frame_camera_on_node_type.py", "print_merge_context.py")
        )
        persp_before = self.cmds.getAttr("persp.translate")[0]
        self.run_task(
            run_input_script=True,
            input_script_text=delete_script,
            run_post_script=True,
            post_script_text=post_script,
            output_mode=task_base.OUTPUT_MODE_PASSTHROUGH,
        )
        expected = []
        self.assertEqual(expected, self.cmds.ls("*:unused_cam*"))
        self.assertTrue(self.cmds.objExists("walk:box"))
        expected = True
        self.assertEqual(expected, self.cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable"))
        self.assertNotEqual(persp_before, self.cmds.getAttr("persp.translate")[0])

    def test_unknown_plugin_nodes_do_not_block_saving(self):
        """Inputs with nodes from an unloaded plugin (e.g. mtoa in workers) still save in both formats."""
        unknown_path = os.path.join(self.directory.name, "arnold_like.ma")
        with open(unknown_path, "w", encoding="utf-8") as scene_file:
            scene_file.write(
                '//Maya ASCII 2025 scene\nrequires maya "2025";\nrequires "gtFakePlugin" "1.0";\n'
                'createNode gtFakeNode -n "fake_options";\ncreateNode transform -n "prop";\n'
            )
        self.work_items = [task_base.WorkItem(source_path=unknown_path), task_base.WorkItem(source_path=self.walk_path)]
        for extension in (".ma", ".mb"):
            with self.subTest(extension=extension):
                _task, result = self.run_task(output_extension=extension, output_name=f"merged_{extension[1:]}")
                self.assertTrue(os.path.isfile(result.current_path))
                self.assertTrue(self.cmds.ls(type="unknown"))

    def test_failing_input_is_skipped(self):
        broken_path = os.path.join(self.directory.name, "broken.ma")
        with open(broken_path, "w", encoding="utf-8") as broken_file:
            broken_file.write("this is not a maya file\n")
        self.work_items.append(task_base.WorkItem(source_path=broken_path))
        _task, result = self.run_task()
        expected = 1
        self.assertEqual(expected, result.metadata["failed_inputs"])
        self.assertTrue(os.path.isfile(result.current_path))


if __name__ == "__main__":
    unittest.main()
