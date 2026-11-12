"""Unit tests for motion evaluation repairs (pure math, manifests, and fixes on a fake keyable host)."""

import contextlib
import json
import math
import os
import tempfile
import unittest

from gt.core.motion_eval import math_utils
from gt.core.motion_eval import templates
from gt.core.motion_eval.hosts import host_base
from gt.core.motion_eval.repairs import apply
from gt.core.motion_eval.repairs import fixes
from gt.core.motion_eval.repairs import manifest
from gt.core.motion_eval.repairs import registry
from gt.core.motion_eval.repairs import solvers
from gt.core.motion_eval.repairs import transform_math
from gt.core.motion_eval.repairs.scene import RepairScene
from gt.core.motion_eval.repairs.scene import clean_node_label

FRAME_COUNT = 30
HIPS = "|hips_jnt"
LEFT_THIGH = "|hips_jnt|left_up_leg_jnt"
LEFT_KNEE = "|hips_jnt|left_up_leg_jnt|left_leg_jnt"
LEFT_FOOT = "|hips_jnt|left_up_leg_jnt|left_leg_jnt|left_foot_jnt"


def translation_matrix(position):
    """Builds a translation-only matrix.

    Args:
        position (tuple): Translation.

    Returns:
        list: Sixteen values.
    """
    return math_utils.compose_matrix(position)


class FakeKeyHost(host_base.SceneHost):
    """Plain-Python host with a local-matrix hierarchy that records keys."""

    name = "fake"
    label = "Fake"
    supports_keying = True

    def __init__(self, parents, local_frames, frame_range=(0, FRAME_COUNT - 1)):
        """Initializes the host.

        Args:
            parents (dict): Node path to parent path (None for top nodes), parents listed first.
            local_frames (dict): Node path to a list of local matrices (one per frame from 0).
            frame_range (tuple): Playback range.
        """
        self.parents = dict(parents)
        self.local_frames = dict((path, [list(matrix) for matrix in frames]) for path, frames in local_frames.items())
        self.frame_range = frame_range
        self.key_calls = []

    def list_joints(self):
        """Lists the nodes.

        Returns:
            list: Node paths.
        """
        return list(self.parents)

    def list_transforms(self):
        """Lists non-joint transforms.

        Returns:
            list: Empty list.
        """
        return []

    def get_parents(self, node_paths):
        """Gets parents.

        Args:
            node_paths (list): Node paths.

        Returns:
            dict: Path to parent.
        """
        return dict((path, self.parents.get(path)) for path in node_paths)

    def get_up_axis(self):
        """Gets the up axis.

        Returns:
            str: "y".
        """
        return "y"

    def get_time_range(self, kind):
        """Gets the playback range.

        Args:
            kind (str): Ignored.

        Returns:
            tuple: (start, end).
        """
        return self.frame_range

    def get_local(self, node_path, frame):
        """Gets a local matrix, holding the first/last frame outside the range.

        Args:
            node_path (str): Node path.
            frame (int): Frame.

        Returns:
            list: Local matrix.
        """
        frames = self.local_frames[node_path]
        return frames[min(len(frames) - 1, max(0, int(frame)))]

    def get_world(self, node_path, frame):
        """Computes a world matrix.

        Args:
            node_path (str): Node path.
            frame (int): Frame.

        Returns:
            list: World matrix.
        """
        parent = self.parents.get(node_path)
        local = self.get_local(node_path, frame)
        return local if parent is None else transform_math.multiply_matrices(local, self.get_world(parent, frame))

    def sample_world_matrices(self, node_paths, start_frame, end_frame):
        """Samples world matrices.

        Args:
            node_paths (list): Node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame.

        Returns:
            dict: Path to matrices.
        """
        return dict((path, [self.get_world(path, frame) for frame in range(int(start_frame), int(end_frame) + 1)])
                    for path in node_paths)

    def edit_block(self, label="motion_eval_repair"):
        """Returns a no-op context.

        Args:
            label (str): Ignored.

        Returns:
            contextlib.AbstractContextManager: Null context.
        """
        return contextlib.nullcontext()

    def key_local_transforms(self, node_path, frames, local_matrices, channels=("rotate",)):
        """Stores keys by replacing the chosen channels of the local matrices.

        Args:
            node_path (str): Node path.
            frames (list): Frames.
            local_matrices (list): Local matrices.
            channels (tuple): Channels.

        Returns:
            dict: Key count and warnings.
        """
        self.key_calls.append((node_path, list(frames), tuple(channels)))
        for frame, matrix in zip(frames, local_matrices):
            if not 0 <= frame < len(self.local_frames[node_path]):
                continue
            current = self.local_frames[node_path][frame]
            if "rotate" in channels:
                current = transform_math.replace_rotation(current, transform_math.matrix_to_quaternion(matrix))
            if "translate" in channels:
                current = transform_math.replace_position(current, math_utils.matrix_position(matrix))
            self.local_frames[node_path][frame] = current
        return {"keys": len(frames) * 3 * len(channels), "warnings": []}


def build_leg_host(hips_step=0.25):
    """Builds a hips + left leg chain whose hips slide forward, so the planted foot slides too.

    Args:
        hips_step (float): Forward hips motion per frame.

    Returns:
        FakeKeyHost: Host.
    """
    parents = {HIPS: None, LEFT_THIGH: HIPS, LEFT_KNEE: LEFT_THIGH, LEFT_FOOT: LEFT_KNEE}
    local_frames = {
        HIPS: [translation_matrix((0.0, 95.0, frame * hips_step)) for frame in range(FRAME_COUNT)],
        LEFT_THIGH: [translation_matrix((10.0, -5.0, 0.0))] * FRAME_COUNT,
        LEFT_KNEE: [translation_matrix((0.0, -40.0, 8.0))] * FRAME_COUNT,
        LEFT_FOOT: [translation_matrix((0.0, -40.0, -8.0))] * FRAME_COUNT,
    }
    return FakeKeyHost(parents, local_frames)


def build_template():
    """Builds a template for the fake leg.

    Returns:
        dict: Template.
    """
    roles = {"hips": ["hips_jnt"], "left_up_leg": ["left_up_leg_jnt"], "left_leg": ["left_leg_jnt"],
             "left_foot": ["left_foot_jnt"]}
    return templates.create_template(name="Fake Leg", roles=roles)


class TestRepairTransformMath(unittest.TestCase):
    def test_quaternion_rows_round_trip(self):
        quaternion = transform_math.normalize_quaternion((0.2, -0.4, 0.1, 0.85))
        result = transform_math.rows_to_quaternion(transform_math.quaternion_to_rows(quaternion))
        expected = quaternion
        for expected_value, value in zip(expected, transform_math.align_quaternion(result, expected)):
            self.assertAlmostEqual(expected_value, value, places=6)

    def test_invert_matrix(self):
        matrix = math_utils.compose_matrix((3.0, -2.0, 5.0), (0.1, 0.7, -0.2, 0.6))
        product = transform_math.multiply_matrices(matrix, transform_math.invert_matrix(matrix))
        expected = math_utils.compose_matrix((0.0, 0.0, 0.0))
        for expected_value, value in zip(expected, product):
            self.assertAlmostEqual(expected_value, value, places=6)

    def test_local_world_round_trip(self):
        parent = math_utils.compose_matrix((1.0, 2.0, 3.0), (0.0, 0.3, 0.0, 0.95))
        world = math_utils.compose_matrix((4.0, 1.0, -2.0), (0.2, 0.0, 0.1, 0.97))
        result = transform_math.world_from_local(transform_math.local_from_world(world, parent), parent)
        for expected_value, value in zip(world, result):
            self.assertAlmostEqual(expected_value, value, places=6)

    def test_quaternion_from_to_rotates_row_vector(self):
        rows = transform_math.quaternion_to_rows(transform_math.quaternion_from_to((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
        result = transform_math.rotate_row_vector((1.0, 0.0, 0.0), rows)
        expected = (0.0, 1.0, 0.0)
        for expected_value, value in zip(expected, result):
            self.assertAlmostEqual(expected_value, value, places=6)


class TestRepairSolvers(unittest.TestCase):
    def test_blend_weights(self):
        result = solvers.build_blend_weights(10, 4, 5, 2)
        self.assertEqual(0.0, result[0])
        self.assertEqual(1.0, result[4])
        self.assertEqual(1.0, result[5])
        self.assertTrue(0.0 < result[3] < 1.0)
        self.assertTrue(0.0 < result[7] < 1.0)
        self.assertEqual(0.0, result[9])

    def test_bridge_vectors_removes_spike(self):
        vectors = [(float(index), 0.0, 0.0) for index in range(10)]
        vectors[5] = (5.0, 30.0, 0.0)
        result = solvers.bridge_vectors(vectors, 5, 5)
        self.assertAlmostEqual(5.0, result[5][0], places=6)
        self.assertAlmostEqual(0.0, result[5][1], places=6)
        self.assertEqual(vectors[4], result[4])

    def test_two_bone_keeps_lengths(self):
        hip, knee, ankle = (0.0, 90.0, 0.0), (0.0, 50.0, 8.0), (0.0, 10.0, 0.0)
        new_knee, reached, _bend = solvers.solve_two_bone(hip, knee, ankle, (0.0, 12.0, 6.0))
        self.assertAlmostEqual(math_utils.distance(hip, knee), math_utils.distance(hip, new_knee), places=6)
        self.assertAlmostEqual(math_utils.distance(knee, ankle), math_utils.distance(new_knee, reached), places=6)
        self.assertAlmostEqual(0.0, math_utils.distance(reached, (0.0, 12.0, 6.0)), places=6)
        self.assertGreater(new_knee[2], 0.0)

    def test_ground_offsets_modes(self):
        heights = [-2.0, 0.0, 3.0]
        self.assertEqual([2.0, 0.0, 0.0], solvers.build_ground_offsets(heights, 0.0, "raise", 0))
        self.assertEqual([0.0, 0.0, -3.0], solvers.build_ground_offsets(heights, 0.0, "lower", 0))


class TestRepairManifest(unittest.TestCase):
    def test_validate_reports_bad_steps(self):
        data = manifest.create_manifest()
        data["takes"]["walk"] = {"steps": [{"fix": "foot_lock", "frames": [5, 2]}, {"fix": "nope", "frames": [1, 2]},
                                           {"fix": "span_bridge", "frames": [1, 2], "params": {"bad": 1}}]}
        errors = manifest.validate_manifest(data, tempfile.gettempdir())
        self.assertEqual(3, len(errors))

    def test_find_take_is_case_insensitive(self):
        data = manifest.create_manifest()
        manifest.set_take(data, "Walk_V003", {"steps": []})
        name, entry = manifest.find_take(data, ["missing", "walk_v003"])
        self.assertEqual("Walk_V003", name)
        self.assertEqual({"steps": []}, entry)
        self.assertTrue(manifest.remove_take(data, "WALK_V003"))
        self.assertEqual({}, data["takes"])

    def test_fingerprint(self):
        entry = {"seed": 4711, "frame_range": [0, 29]}
        self.assertEqual((True, ""), manifest.check_fingerprint(entry, seed=4711, frame_range=(0, 29)))
        self.assertEqual((True, ""), manifest.check_fingerprint(entry, seed=None, frame_range=None))
        self.assertFalse(manifest.check_fingerprint(entry, seed=12, frame_range=(0, 29))[0])
        self.assertFalse(manifest.check_fingerprint(entry, seed=4711, frame_range=(0, 40))[0])

    def test_registry_suggestions(self):
        self.assertEqual(["foot_lock", "hips_follow"], registry.suggest_fixes("foot_slide"))
        self.assertEqual([], registry.suggest_fixes("excessive_speed"))
        self.assertIn("foot_lock", registry.describe_fixes())

    def test_clean_node_label(self):
        self.assertEqual("foot_l", clean_node_label("foot_l (left_foot)"))
        self.assertEqual("|a|b", clean_node_label("|a|b"))


class TestRepairFixes(unittest.TestCase):
    def test_foot_lock_pins_foot(self):
        host = build_leg_host()
        scene = RepairScene(host=host, template=build_template())
        before = host.sample_world_matrices([LEFT_FOOT], 10, 20)[LEFT_FOOT]
        result = registry.get_fix("foot_lock").function(scene, (10, 20), [], {"side": "left", "blend": 3})
        after = host.sample_world_matrices([LEFT_FOOT, LEFT_KNEE, LEFT_THIGH], 0, FRAME_COUNT - 1)
        pinned = [math_utils.matrix_position(matrix) for matrix in after[LEFT_FOOT][10:21]]
        before_positions = [math_utils.matrix_position(matrix) for matrix in before]
        travel_before = math_utils.distance(before_positions[0], before_positions[-1])
        travel_after = math_utils.distance(pinned[0], pinned[-1])
        self.assertGreater(travel_before, 2.0)
        self.assertLess(travel_after, 0.01)
        for frame in range(FRAME_COUNT):
            knee = math_utils.matrix_position(after[LEFT_KNEE][frame])
            foot = math_utils.matrix_position(after[LEFT_FOOT][frame])
            self.assertAlmostEqual(math.sqrt(40.0 ** 2 + 8.0 ** 2), math_utils.distance(knee, foot), places=4)
        self.assertEqual([LEFT_THIGH, LEFT_KNEE, LEFT_FOOT], result["nodes"])
        self.assertEqual(list(range(7, 24)), host.key_calls[0][1])

    def test_foot_lock_auto_picks_planted_leg(self):
        host = build_leg_host()
        right_thigh = "|hips_jnt|right_up_leg_jnt"
        right_knee = f"{right_thigh}|right_leg_jnt"
        right_foot = f"{right_knee}|right_foot_jnt"
        host.parents.update({right_thigh: HIPS, right_knee: right_thigh, right_foot: right_knee})
        host.local_frames[right_thigh] = [translation_matrix((-10.0, -5.0, 0.0))] * FRAME_COUNT
        host.local_frames[right_knee] = [translation_matrix((0.0, -30.0 if 10 <= frame <= 20 else -40.0, 8.0))
                                         for frame in range(FRAME_COUNT)]
        host.local_frames[right_foot] = [translation_matrix((0.0, -40.0, -8.0))] * FRAME_COUNT
        scene = RepairScene(host=host, template=build_template())
        legs = [[LEFT_THIGH, LEFT_KNEE, LEFT_FOOT], [right_thigh, right_knee, right_foot]]
        picked = fixes.pick_planted_legs(scene, legs, (10, 20), "y")
        self.assertEqual([[LEFT_THIGH, LEFT_KNEE, LEFT_FOOT]], picked)

    def test_resolve_report_side_label(self):
        scene = RepairScene(host=build_leg_host(), template=build_template())
        self.assertEqual(LEFT_FOOT, scene.resolve_node("left foot"))
        self.assertEqual(LEFT_FOOT, scene.resolve_node("left_foot_jnt (left_foot)"))

    def test_foot_lock_keeps_foot_rotation(self):
        host = build_leg_host()
        scene = RepairScene(host=host, template=build_template())
        before = host.sample_world_matrices([LEFT_FOOT], 15, 15)[LEFT_FOOT][0]
        registry.get_fix("foot_lock").function(scene, (10, 20), [], {"side": "left", "blend": 3})
        after = host.sample_world_matrices([LEFT_FOOT], 15, 15)[LEFT_FOOT][0]
        self.assertAlmostEqual(0.0, math_utils.rotation_angle_between(before, after), places=4)

    def test_ground_snap_raises_hips(self):
        host = build_leg_host(hips_step=0.0)
        for frame in range(13, 15):
            host.local_frames[HIPS][frame] = translation_matrix((0.0, 90.0, 0.0))
        scene = RepairScene(host=host, template=build_template())
        result = registry.get_fix("ground_snap").function(scene, (13, 14), [], {"mode": "raise", "smooth": 0,
                                                                                 "blend": 2, "contacts": ["left_foot"]})
        hips = math_utils.matrix_position(host.sample_world_matrices([HIPS], 13, 13)[HIPS][0])
        self.assertAlmostEqual(95.0, hips[1], places=4)
        self.assertAlmostEqual(10.0, result["floor"], places=4)

    def test_span_bridge_removes_rotation_pop(self):
        host = build_leg_host(hips_step=0.0)
        popped = math_utils.compose_matrix((10.0, -5.0, 0.0), (0.5, 0.0, 0.0, 0.866))
        host.local_frames[LEFT_THIGH][14] = popped
        scene = RepairScene(host=host, template=build_template())
        registry.get_fix("span_bridge").function(scene, (14, 14), ["left_up_leg"], {"channels": "rotate",
                                                                                      "strength": 1.0})
        result = host.local_frames[LEFT_THIGH][14]
        expected = translation_matrix((10.0, -5.0, 0.0))
        self.assertAlmostEqual(0.0, math_utils.rotation_angle_between(expected, result), places=4)


class TestRepairApply(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.temp_dir, "patches.json")
        script_path = os.path.join(self.temp_dir, "custom", "mark.py")
        os.makedirs(os.path.dirname(script_path))
        with open(script_path, "w", encoding="utf-8") as stream:
            stream.write("def run(context):\n    return {'keys': 1, 'note': context['params']['note']}\n")

    def write_manifest(self, take_entry, on_error="warn"):
        """Writes a manifest with one take.

        Args:
            take_entry (dict): Take entry.
            on_error (str): Error policy.
        """
        data = manifest.create_manifest(template="", on_error=on_error)
        data["takes"]["walk_v003"] = take_entry
        with open(self.manifest_path, "w", encoding="utf-8") as stream:
            json.dump(data, stream)

    def test_unlisted_take_is_untouched(self):
        self.write_manifest({"steps": [{"script": "custom/mark.py", "params": {"note": "x"}}]})
        host = build_leg_host()
        result = apply.apply_manifest(self.manifest_path, ["run_v001"], host=host, log=lambda text: None)
        self.assertEqual(apply.STATUS_NONE, result["status"])
        self.assertEqual([], host.key_calls)

    def test_script_and_fix_steps_apply(self):
        self.write_manifest({"seed": 7, "frame_range": [0, 29], "steps": [
            {"script": "custom/mark.py", "params": {"note": "hello"}},
            {"fix": "foot_lock", "frames": [10, 20], "nodes": ["left_up_leg_jnt", "left_leg_jnt", "left_foot_jnt"]},
        ]})
        host = build_leg_host()
        result = apply.apply_manifest(self.manifest_path, ["WALK_V003"], seed=7, host=host, log=lambda text: None)
        self.assertEqual(apply.STATUS_APPLIED, result["status"])
        self.assertEqual("hello", result["steps"][0]["note"])
        self.assertEqual(3, len(host.key_calls))

    def test_fingerprint_mismatch_skips(self):
        self.write_manifest({"seed": 7, "steps": [{"fix": "foot_lock", "frames": [10, 20],
                                                   "params": {"side": "left"}}]})
        host = build_leg_host()
        result = apply.apply_manifest(self.manifest_path, ["walk_v003"], seed=8, host=host, log=lambda text: None)
        self.assertEqual(apply.STATUS_SKIPPED, result["status"])
        self.assertEqual([], host.key_calls)

    def test_failed_step_raises_when_asked(self):
        self.write_manifest({"steps": [{"fix": "foot_lock", "frames": [10, 20], "params": {"side": "left"}}]},
                            on_error="fail")
        host = build_leg_host()
        with self.assertRaises(apply.PatchError):
            apply.apply_manifest(self.manifest_path, ["walk_v003"], host=host, log=lambda text: None)

    def test_failed_step_warns_by_default(self):
        self.write_manifest({"steps": [{"fix": "foot_lock", "frames": [10, 20], "params": {"side": "left"}}]})
        host = build_leg_host()
        result = apply.apply_manifest(self.manifest_path, ["walk_v003"], host=host, log=lambda text: None)
        self.assertEqual(apply.STATUS_FAILED, result["status"])


if __name__ == "__main__":
    unittest.main()
