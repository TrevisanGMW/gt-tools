"""Pure export helpers and actual isolated mayapy scene creation regression tests."""

import os
import subprocess
import sys
import tempfile
import unittest
from gt.core.io import read_json_dict, write_json
from gt.tools.kimodo_generator import kimodo_generator_export as scene_export
from gt.tools.kimodo_generator import kimodo_generator_results as results


class TestExportHelpers(unittest.TestCase):
    """Checks import isolation, sample filtering, and missing-scene status."""

    def test_import_is_pure(self):
        """Requires neither Maya nor Qt to import the export launcher."""
        code = ("import sys; from gt.tools.kimodo_generator import kimodo_generator_export; "
                "assert not any(name in sys.modules for name in ('maya', 'PySide6', 'torch', 'numpy'))")
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)

    def test_samples_and_missing_files(self):
        """Selects every motion sample without treating manifests as animations."""
        paths = dict.fromkeys(("motion.json", "sample_1.json", "result.json", "motion.npz"), __file__)
        self.assertEqual({"motion.json": __file__, "sample_1.json": __file__}, scene_export.motion_paths(paths))
        with self.assertRaises(ValueError):
            scene_export.motion_paths({"motion.json": "relative.json"})
        with self.assertRaises(ValueError):
            scene_export.motion_paths({"result.json": __file__})
        self.assertEqual("ready", results.maya_status({"maya_files": {"motion.json": __file__}}))
        self.assertEqual("Maya files missing", results.maya_status({"maya_files": {"motion.json": "missing.ma"}}))
        self.assertEqual("Maya export failed", results.maya_status({"maya_export_error": "failure"}))


class TestIsolatedMayaExport(unittest.TestCase):
    """Runs the real worker and inspects saved scene data with mayapy."""

    @classmethod
    def setUpClass(cls):
        """Initializes a disposable parent Maya session only when Maya is available."""
        try:
            import maya.standalone
            import maya.cmds as cmds
        except ImportError:
            raise unittest.SkipTest("Requires mayapy.")
        cls.owns_maya = not hasattr(cmds, "file")
        if cls.owns_maya:
            maya.standalone.initialize(name="python")
        cls.cmds = cmds

    @classmethod
    def tearDownClass(cls):
        """Closes the standalone session owned by this test class."""
        if cls.owns_maya:
            import maya.standalone
            maya.standalone.uninitialize()

    def test_export_reuse_scene_isolation_and_no_overwrite(self):
        """Produces locked HIK scenes for all samples, preserving the parent scene and edited files."""
        cmds = self.cmds
        cmds.file(new=True, force=True)
        marker = cmds.createNode("transform", name="unsaved_scene_marker")
        cmds.currentUnit(time="film")
        cmds.select(marker)
        fixture = read_json_dict(os.path.join(os.path.dirname(__file__), "data", "soma_skeleton.json"))
        motion = {"schema_version": 1, "fps": 30, "frame_count": 2, "skeleton": fixture,
                  "coordinates": {"units": "meters", "up": "y", "forward": "+z",
                                  "rotations": "column_local_matrix"},
                  "root_positions": [[0, 1, 0], [0.1, 1.1, 0.2]],
                  "local_rotations": [[[[1, 0, 0], [0, 1, 0], [0, 0, 1]] for unused in range(77)]
                                      for unused in range(2)]}
        with tempfile.TemporaryDirectory() as directory:
            paths = {name: os.path.join(directory, name) for name in ("motion.json", "sample_1.json")}
            for path in paths.values():
                write_json(path, motion)
            source_digest = scene_export.file_digest(paths["motion.json"])
            files = scene_export.export_maya_files(paths, mayapy_path=sys.executable)
            self.assertEqual(set(paths), set(files))
            self.assertEqual([marker], cmds.ls(selection=True))
            self.assertEqual("film", cmds.currentUnit(query=True, time=True))
            self.assertEqual([], cmds.ls(type="HIKCharacterNode"))
            self.assertEqual("", cmds.file(query=True, sceneName=True))
            self.assertEqual(source_digest, scene_export.file_digest(paths["motion.json"]))
            modified_time = os.path.getmtime(files["motion.json"])
            self.assertEqual(files, scene_export.export_maya_files(paths, mayapy_path=sys.executable))
            self.assertEqual(modified_time, os.path.getmtime(files["motion.json"]))
            for path in files.values():
                cmds.file(path, open=True, force=True)
                self.assertEqual(["kimodo"], cmds.ls(type="HIKCharacterNode"))
                self.assertEqual(True, bool(cmds.getAttr("kimodo.InputCharacterizationLock")))
                self.assertEqual("ntsc", cmds.currentUnit(query=True, time=True))
                self.assertEqual([1.0, 2.0], cmds.keyframe("kimodo_animation:Hips", attribute="translateX",
                                                        query=True, timeChange=True))
                self.assertEqual([0.0, 10.0], cmds.keyframe("kimodo_animation:Hips", attribute="translateX",
                                                         query=True, valueChange=True))
            cmds.file(new=True, force=True)
            with open(files["motion.json"], "a", encoding="utf-8") as stream:
                stream.write("\n// User edit\n")
            edited_digest = scene_export.file_digest(files["motion.json"])
            with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                scene_export.export_maya_files(paths, mayapy_path=sys.executable)
            self.assertEqual(edited_digest, scene_export.file_digest(files["motion.json"]))


if __name__ == "__main__":
    unittest.main()
