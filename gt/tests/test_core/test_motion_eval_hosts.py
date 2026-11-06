"""Motion evaluation hosts: host routing, motion sample files, and the host-agnostic rules for checks."""

import tempfile
import unittest
import ast
import math
import os
from unittest import mock

from gt.core.motion_eval import checks_base
from gt.core.motion_eval import evaluation
from gt.core.motion_eval import hosts
from gt.core.motion_eval import math_utils
from gt.core.motion_eval import presets
from gt.core.motion_eval import runner
from gt.core.motion_eval import sample_io
from gt.core.motion_eval import sampling
from gt.core.motion_eval import scene_io
from gt.core.motion_eval import templates
from gt.core.motion_eval.hosts import blender_host
from gt.core.motion_eval.hosts import host_base
from gt.tests.test_core import test_motion_eval as fixtures

PACKAGE_DIR = os.path.dirname(os.path.abspath(evaluation.__file__))
# The only modules allowed to import a DCC: everything else must work in Maya, Blender, and plain Python.
HOST_MODULES = {os.path.join("hosts", "maya_host.py"), os.path.join("hosts", "blender_host.py"), "usd_scene.py"}
DCC_MODULES = ("maya", "bpy", "mathutils", "pymel")


def build_template():
    """Builds a skeleton template matching the synthetic test biped.

    Returns:
        dict: Skeleton template.
    """
    roles = {role: [f"{role}_jnt"] for role in fixtures.REST_POSE}
    return templates.create_template(name="Test Biped", roles=roles)


def build_file_sample():
    """Builds a motion sample (as saved to file) of the synthetic idle.

    Returns:
        dict: Sample made with sample_io.create_sample.
    """
    sample = fixtures.build_sample(fixtures.build_idle_positions())
    return sample_io.create_sample(fps=sample["fps"], start_frame=sample["start_frame"], nodes=sample["nodes"],
                                   up_axis="y", meters_per_unit=0.01)


def list_imported_modules(file_path):
    """Lists the top-level modules a Python file imports.

    Args:
        file_path (str): Python file.

    Returns:
        set: Top-level module names.
    """
    with open(file_path, "r", encoding="utf-8") as source_file:
        tree = ast.parse(source_file.read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


class FakeBlenderMatrix:
    """Mimics mathutils.Matrix indexing: matrix[row][column], translation in the last column."""

    def __init__(self, rows):
        """Stores the rows.

        Args:
            rows (list): Four rows of four values.
        """
        self.rows = rows

    def __getitem__(self, row_index):
        """Gets one row.

        Args:
            row_index (int): Row.

        Returns:
            list: Row values.
        """
        return self.rows[row_index]


class TestMotionEvalHostRules(unittest.TestCase):
    def test_only_host_modules_import_a_dcc(self):
        offenders = []
        for folder, _sub_folders, file_names in os.walk(PACKAGE_DIR):
            for file_name in file_names:
                if not file_name.endswith(".py"):
                    continue
                file_path = os.path.join(folder, file_name)
                relative = os.path.relpath(file_path, PACKAGE_DIR)
                if relative in HOST_MODULES:
                    continue
                imported = list_imported_modules(file_path)
                offenders.extend(f"{relative}: {name}" for name in DCC_MODULES if name in imported)
        self.assertEqual([], offenders)

    def test_every_host_implements_the_required_methods(self):
        required = [name for name, value in vars(host_base.SceneHost).items()
                    if callable(value) and "Required" in (value.__doc__ or "")]
        self.assertIn("sample_world_matrices", required)
        for name in hosts.HOST_NAMES:
            host = hosts.create_host(name)
            missing = [method for method in required
                       if getattr(type(host), method) is getattr(host_base.SceneHost, method)
                       and not (method == "save_scene_copy" and not host.copy_extension)]
            self.assertEqual([], missing, name)

    def test_unknown_host_is_rejected(self):
        with self.assertRaises(ValueError):
            hosts.create_host("houdini")


class TestMotionEvalHostRegistry(unittest.TestCase):
    def test_get_host_returns_shared_instances(self):
        self.assertIs(hosts.get_host("blender"), hosts.get_host("blender"))
        self.assertEqual("maya", hosts.get_host("maya").name)

    def test_use_host_restores_previous_host(self):
        before = hosts.get_host()
        with hosts.use_host("sample") as active:
            self.assertEqual("sample", active.name)
            self.assertEqual("sample", sampling.get_host().name)
        self.assertIs(before, hosts.get_host())

    def test_blender_is_not_detected_outside_blender(self):
        self.assertFalse(hosts.get_host("blender").is_available())
        self.assertNotEqual("blender", hosts.detect_host_name())

    def test_scene_extensions_per_host(self):
        self.assertIn(".mb", hosts.get_scene_extensions("maya"))
        self.assertNotIn(".mb", hosts.get_scene_extensions("blender"))
        self.assertIn(".blend", hosts.get_scene_extensions("blender"))

    def test_blender_pip_command_targets_a_folder(self):
        host = hosts.get_host("blender")
        with mock.patch.object(host, "get_dependency_target", return_value="C:/blender/modules"), \
                mock.patch.object(host, "get_python_executable", return_value="python.exe"):
            command = host.build_pip_install_command(["PySide6-Essentials"])
        self.assertEqual(["python.exe", "-m", "pip", "install", "--disable-pip-version-check", "--target",
                          "C:/blender/modules", "PySide6-Essentials"], command)


class TestMotionEvalBlenderHelpers(unittest.TestCase):
    def test_flatten_matrix_transposes_into_maya_layout(self):
        matrix = FakeBlenderMatrix([[1.0, 0.0, 0.0, 5.0], [0.0, 0.0, -1.0, 6.0], [0.0, 1.0, 0.0, 7.0],
                                    [0.0, 0.0, 0.0, 1.0]])
        flat = blender_host.flatten_matrix(matrix)
        self.assertEqual((5.0, 6.0, 7.0), math_utils.matrix_position(flat))
        self.assertEqual([(1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0)], math_utils.matrix_axes(flat))

    def test_bone_name_from_data_path(self):
        data_path = 'pose.bones["mixamorig:Hips"].location'
        self.assertEqual("mixamorig:Hips", blender_host.get_bone_name_from_data_path(data_path))
        self.assertIsNone(blender_host.get_bone_name_from_data_path("location"))


class TestMotionEvalComposeMatrix(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(fixtures.build_matrix((1.0, 2.0, 3.0)), math_utils.compose_matrix((1.0, 2.0, 3.0)))

    def test_rotation_and_scale(self):
        half = math.sqrt(0.5)
        matrix = math_utils.compose_matrix((0.0, 0.0, 0.0), (0.0, 0.0, half, half), (2.0, 1.0, 1.0))
        axes = math_utils.matrix_axes(matrix)
        self.assertAlmostEqual(2.0, axes[0][1])
        self.assertAlmostEqual(-1.0, axes[1][0])
        self.assertAlmostEqual(90.0, math_utils.rotation_angle_between(matrix, fixtures.build_matrix((0, 0, 0))))


class TestMotionEvalSampleIO(unittest.TestCase):
    def test_round_trip(self):
        sample = build_file_sample()
        with tempfile.TemporaryDirectory() as directory:
            path = sample_io.save_sample(sample, os.path.join(directory, "idle"))
            self.assertTrue(path.endswith(sample_io.SAMPLE_EXTENSION))
            loaded = sample_io.load_sample(path)
        self.assertEqual(sample["nodes"], loaded["nodes"])
        self.assertEqual(fixtures.FRAME_COUNT, loaded["frame_count"])

    def test_create_sample_rejects_mismatched_frames(self):
        with self.assertRaises(ValueError):
            sample_io.create_sample(fps=30, start_frame=1, nodes={
                "|a": {"parent": None, "matrices": [fixtures.build_matrix((0, 0, 0))] * 3},
                "|b": {"parent": "|a", "matrices": [fixtures.build_matrix((0, 0, 0))] * 2},
            })

    def test_load_rejects_other_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "other.motion.json")
            with open(path, "w", encoding="utf-8") as other_file:
                other_file.write("{}")
            with self.assertRaises(ValueError):
                sample_io.load_sample(path)


class TestMotionEvalSampleHost(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.sample_path = sample_io.save_sample(build_file_sample(), os.path.join(self.directory.name, "idle"))

    def tearDown(self):
        self.directory.cleanup()

    def test_sample_scene_through_the_host_matches_evaluate_sample(self):
        template = build_template()
        preset = presets.create_preset(mode="biped")
        with hosts.use_host("sample") as host:
            host.load_scene(self.sample_path)
            report = evaluation.evaluate_scene(preset=preset, template=template)
        expected = evaluation.evaluate_sample(fixtures.build_sample(fixtures.build_idle_positions()), preset)
        self.assertEqual(expected["score"], report["score"])
        self.assertEqual([entry["score"] for entry in expected["checks"]],
                         [entry["score"] for entry in report["checks"]])
        self.assertEqual("idle.motion", report["scene"])

    def test_frame_ranges_use_the_sample(self):
        with hosts.use_host("sample") as host:
            host.load_scene(self.sample_path)
            self.assertEqual((1, fixtures.FRAME_COUNT), sampling.resolve_frame_range(sampling.RANGE_ANIMATION))
            self.assertEqual((5, 20), sampling.resolve_frame_range(sampling.RANGE_CUSTOM, 5, 20))
            with self.assertRaises(ValueError):
                host.sample_world_matrices(["|hips_jnt"], 0, 10)

    def test_score_write_is_refused(self):
        with hosts.use_host("sample"):
            with self.assertRaises(ValueError):
                scene_io.write_score({"score": 50, "roles": {}})

    def test_describe_scene(self):
        with hosts.use_host("sample") as host:
            host.load_scene(self.sample_path)
            description = sampling.describe_scene()
        self.assertEqual("sample", description["host"])
        self.assertEqual(len(fixtures.REST_POSE), description["joint_count"])


class TestMotionEvalRunnerHosts(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.directory.name, "input")
        sample_io.save_sample(build_file_sample(), os.path.join(self.input_dir, "idle"))

    def tearDown(self):
        self.directory.cleanup()

    def test_run_motion_samples_in_plain_python(self):
        job = runner.create_job(input_dir=self.input_dir, output_dir=os.path.join(self.directory.name, "output"),
                                skeleton=build_template(), outputs={"summary_per_file": True})
        result = runner.run(job, show_progress=False)
        self.assertEqual({}, result["errors"])
        self.assertEqual(100, result["results"][0]["score"])
        self.assertTrue(os.path.isfile(os.path.join(self.directory.name, "output", "batch_summary.txt")))

    def test_job_extensions_follow_the_host(self):
        blender_extensions = runner.get_job_extensions(runner.create_job(host="blender"))
        self.assertIn(".blend", blender_extensions)
        self.assertNotIn(".ma", blender_extensions)
        self.assertIn(sample_io.SAMPLE_EXTENSION, blender_extensions)
        custom = runner.get_job_extensions(runner.create_job(host="blender", extensions=[".fbx"]))
        self.assertEqual([".fbx", sample_io.SAMPLE_EXTENSION], custom)

    def test_invalid_host_fails_validation(self):
        errors = runner.validate_job(runner.create_job(host="houdini"))
        self.assertEqual(1, len([error for error in errors if "houdini" in error]))

    def test_graphs_are_skipped_with_a_warning_without_qt(self):
        from gt.core.motion_eval import report_graphs

        job = runner.create_job(output_dir=os.path.join(self.directory.name, "output"), skeleton=build_template(),
                                outputs={"graphs_batch": True, "graphs_per_file": True,
                                         "graphs_only_on_failure": False})
        sample_path = os.path.join(self.input_dir, "idle.motion.json")
        with mock.patch.object(report_graphs, "is_qt_available", return_value=False):
            result = runner.run_job([sample_path], job)
        self.assertEqual(1, len([warning for warning in result["warnings"] if "pip" in warning]))
        self.assertFalse([path for path in result["batch_outputs"] if path.endswith(".png")])
        self.assertFalse([path for path in result["results"][0]["outputs"] if path.endswith(".png")])

    def test_no_graph_warning_when_graphs_are_off(self):
        job = runner.create_job(outputs={"graphs_batch": False, "graphs_per_file": False})
        self.assertEqual("", runner.get_graph_warning(job))

    def test_blender_command_line_arguments(self):
        with mock.patch("sys.argv", ["blender", "-b", "--python", "cli.py", "--", "job.json", "a.fbx"]):
            self.assertEqual(["job.json", "a.fbx"], runner.get_command_line_arguments())



class TestMotionEvalRequiredData(unittest.TestCase):
    def setUp(self):
        def check_floor(data, parameters):
            """Flags frames whose stored floor height is above zero.

            Args:
                data (MotionData): Sampled motion.
                parameters (dict): Unused.

            Returns:
                CheckResult: Findings.
            """
            result = checks_base.CheckResult()
            result.flag_many(index for index, height in enumerate(data.get_extra("floor_heights")) if height > 0)
            return result

        self.check = checks_base.CheckDefinition(key="test_floor", label="Test Floor", mode=checks_base.MODE_GENERAL,
                                                 description="Test check.", function=check_floor,
                                                 required_data=["floor_heights"])
        self.data = checks_base.MotionData(fixtures.build_sample(fixtures.build_idle_positions()))
        self.values = {"enabled": True, "parameters": {}}

    def test_check_skips_when_the_host_lacks_the_data(self):
        result = evaluation.run_check(self.check, self.data, self.values)
        self.assertIn("floor_heights", result.skip_reason)

    def test_check_runs_with_the_data(self):
        self.data.extra["floor_heights"] = [0.0] * (fixtures.FRAME_COUNT - 1) + [1.0]
        result = evaluation.run_check(self.check, self.data, self.values)
        self.assertEqual("", result.skip_reason)
        self.assertEqual({fixtures.FRAME_COUNT - 1}, result.flagged)

    def test_required_data_is_collected_from_the_host(self):
        sample = build_file_sample()
        sample["extra"] = {"floor_heights": [0.0] * fixtures.FRAME_COUNT}
        with hosts.use_host("sample") as host:
            host.sample = sample
            collected = sampling.collect_extra_data(["floor_heights", "unknown"], [], 1, fixtures.FRAME_COUNT)
        self.assertEqual(["floor_heights"], list(collected))


if __name__ == "__main__":
    unittest.main()
