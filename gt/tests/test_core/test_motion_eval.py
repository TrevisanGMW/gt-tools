"""Unit tests for the pure motion evaluation modules (no Maya required)."""

import tempfile
import unittest
import math
import io
import os
import sys
from unittest import mock

from gt.core.motion_eval import batch_summary
from gt.core.motion_eval import checks_base
from gt.core.motion_eval import evaluation
from gt.core.motion_eval import math_utils
from gt.core.motion_eval import outputs
from gt.core.motion_eval import runner
from gt.core.motion_eval import presets
from gt.core.motion_eval import report_graphs
from gt.core.motion_eval import scoring
from gt.core.motion_eval import templates
from gt.core.motion_eval import usd_scene

FPS = 30.0
FRAME_COUNT = 90

# Synthetic biped in centimeters (Y up). Names are generic test names, not a real skeleton.
REST_POSE = {
    "hips": (0.0, 95.0, 0.0),
    "spine": (0.0, 105.0, 0.0),
    "chest": (0.0, 130.0, 0.0),
    "neck": (0.0, 150.0, 0.0),
    "head": (0.0, 160.0, 0.0),
    "left_up_leg": (10.0, 90.0, 0.0),
    "left_leg": (10.0, 48.0, 1.0),
    "left_foot": (10.0, 8.0, 0.0),
    "left_toe": (10.0, 2.0, 14.0),
    "right_up_leg": (-10.0, 90.0, 0.0),
    "right_leg": (-10.0, 48.0, 1.0),
    "right_foot": (-10.0, 8.0, 0.0),
    "right_toe": (-10.0, 2.0, 14.0),
    "left_arm": (18.0, 145.0, 0.0),
    "left_forearm": (24.0, 118.0, 0.0),
    "left_hand": (27.0, 95.0, 2.0),
    "right_arm": (-18.0, 145.0, 0.0),
    "right_forearm": (-24.0, 118.0, 0.0),
    "right_hand": (-27.0, 95.0, 2.0),
}
PARENTS = {
    "spine": "hips",
    "chest": "spine",
    "neck": "chest",
    "head": "neck",
    "left_up_leg": "hips",
    "left_leg": "left_up_leg",
    "left_foot": "left_leg",
    "left_toe": "left_foot",
    "right_up_leg": "hips",
    "right_leg": "right_up_leg",
    "right_foot": "right_leg",
    "right_toe": "right_foot",
    "left_arm": "chest",
    "left_forearm": "left_arm",
    "left_hand": "left_forearm",
    "right_arm": "chest",
    "right_forearm": "right_arm",
    "right_hand": "right_forearm",
}
UPPER_BODY = ["hips", "spine", "chest", "neck", "head", "left_arm", "left_forearm", "left_hand",
              "right_arm", "right_forearm", "right_hand"]


def build_matrix(position):
    """Builds an identity-rotation matrix at a position.

    Args:
        position (tuple): Translation.

    Returns:
        list: Sixteen matrix values.
    """
    return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, position[0], position[1], position[2], 1.0]


def build_rotated_matrix(position, axis, degrees):
    """Builds a matrix rotated around an axis at a position.

    Args:
        position (tuple): Translation.
        axis (tuple): Unit rotation axis.
        degrees (float): Rotation angle in degrees.

    Returns:
        list: Sixteen matrix values.
    """
    rows = [math_utils.rotate_vector(basis, axis, math.radians(degrees))
            for basis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))]
    return [rows[0][0], rows[0][1], rows[0][2], 0.0, rows[1][0], rows[1][1], rows[1][2], 0.0,
            rows[2][0], rows[2][1], rows[2][2], 0.0, position[0], position[1], position[2], 1.0]


def build_idle_positions(frame_count=FRAME_COUNT):
    """Builds a gentle standing idle: smooth upper-body sway, planted feet.

    Args:
        frame_count (int): Number of frames.

    Returns:
        dict: Role to list of positions.
    """
    positions = {role: [] for role in REST_POSE}
    for frame_index in range(frame_count):
        sway = 1.5 * math.sin(2.0 * math.pi * frame_index / 60.0)
        for role, rest in REST_POSE.items():
            offset = sway if role in UPPER_BODY else 0.0
            positions[role].append((rest[0] + offset, rest[1], rest[2]))
    return positions


def build_sample(positions, meters_per_unit=0.01, rotations=None):
    """Builds a sample dictionary from role positions.

    Args:
        positions (dict): Role to positions.
        meters_per_unit (float): Scene unit size.
        rotations (dict, optional): Role to {frame index: (axis, degrees)} rotations. Other frames use identity.

    Returns:
        dict: Sample dictionary.
    """
    rotations = rotations or {}
    nodes = {}
    for role, role_positions in positions.items():
        parent = PARENTS.get(role)
        role_rotations = rotations.get(role) or {}
        matrices = []
        for index, position in enumerate(role_positions):
            if index in role_rotations:
                matrices.append(build_rotated_matrix(position, *role_rotations[index]))
            else:
                matrices.append(build_matrix(position))
        nodes[f"|{role}_jnt"] = {
            "matrices": matrices,
            "parent": f"|{parent}_jnt" if parent else None,
        }
    return {
        "fps": FPS,
        "start_frame": 1,
        "frame_count": len(positions["hips"]),
        "up_axis": "y",
        "meters_per_unit": meters_per_unit,
        "nodes": nodes,
        "roles": {role: f"|{role}_jnt" for role in positions},
    }


def get_check_entry(report, check_key):
    """Finds a check entry in a report.

    Args:
        report (dict): Evaluation report.
        check_key (str): Check key.

    Returns:
        dict: Check entry.
    """
    return [entry for entry in report["checks"] if entry["key"] == check_key][0]


class TestMotionEvalMath(unittest.TestCase):
    def test_quadratic_smooth_preserves_parabola(self):
        values = [0.5 * index * index - 3.0 * index for index in range(10)]
        smoothed = math_utils.quadratic_smooth(values, half_window=2)
        for expected, result in zip(values, smoothed):
            self.assertAlmostEqual(expected, result, places=6)

    def test_indexes_to_spans(self):
        expected = [[1, 3], [7, 7], [9, 10]]
        self.assertEqual(expected, math_utils.indexes_to_spans([3, 1, 2, 7, 9, 10]))

    def test_filter_minimum_run(self):
        expected = {4, 5, 6}
        self.assertEqual(expected, math_utils.filter_minimum_run([1, 4, 5, 6, 9], 3))

    def test_segment_segment_distance_parallel(self):
        result = math_utils.segment_segment_distance((0, 0, 0), (0, 10, 0), (3, 0, 0), (3, 10, 0))
        self.assertAlmostEqual(3.0, result)

    def test_segment_segment_distance_crossing(self):
        result = math_utils.segment_segment_distance((-5, 0, 0), (5, 0, 0), (0, -5, 2), (0, 5, 2))
        self.assertAlmostEqual(2.0, result)

    def test_fit_parabola_recovers_gravity(self):
        time_step = 1.0 / 30.0
        heights = [100.0 + 300.0 * index * time_step - 0.5 * 981.0 * (index * time_step) ** 2 for index in range(12)]
        self.assertAlmostEqual(-981.0, math_utils.fit_parabola(heights, time_step), places=4)

    def test_rotation_angle_between(self):
        angle = math.radians(30.0)
        rotated = [math.cos(angle), math.sin(angle), 0, 0, -math.sin(angle), math.cos(angle), 0, 0, 0, 0, 1, 0,
                   0, 0, 0, 1]
        self.assertAlmostEqual(30.0, math_utils.rotation_angle_between(build_matrix((0, 0, 0)), rotated), places=5)


class TestMotionEvalTemplates(unittest.TestCase):
    def test_builtin_templates_are_valid_bipeds(self):
        for template_key in templates.get_builtin_template_keys():
            template = templates.get_builtin_template(template_key)
            self.assertEqual([], templates.validate_template(template, require_biped=True))

    def test_resolve_with_prefix_and_namespace(self):
        template = templates.get_builtin_template("maya_humanik")
        nodes = [f"|grp|hero:Character1_{name[0]}" for name in template["roles"].values()]
        resolution = templates.resolve_template_roles(template, nodes)
        self.assertEqual([], resolution["missing_required"])
        self.assertEqual("|grp|hero:Character1_Hips", resolution["roles"]["hips"])
        self.assertEqual("hero:Character1_", resolution["group"])

    def test_resolve_does_not_confuse_similar_names(self):
        template = templates.get_builtin_template("maya_humanik")
        resolution = templates.resolve_template_roles(template, ["|Hips", "|LeftUpLeg"])
        self.assertNotIn("left_leg", resolution["roles"])
        self.assertEqual("|LeftUpLeg", resolution["roles"]["left_up_leg"])

    def test_resolve_prefers_group_with_most_roles(self):
        template = templates.get_builtin_template("unreal_mannequin")
        nodes = ["|a:pelvis", "|b:pelvis", "|b:thigh_l", "|b:calf_l"]
        resolution = templates.resolve_template_roles(template, nodes)
        self.assertEqual("|b:pelvis", resolution["roles"]["hips"])

    def test_detect_builtin_template(self):
        nodes = [f"|{names[0]}" for names in templates.BUILTIN_TEMPLATES["unreal_mannequin"]["roles"].values()]
        template_key, _resolution = templates.detect_builtin_template(nodes)
        self.assertEqual("unreal_mannequin", template_key)

    def test_save_and_load_round_trip(self):
        template = templates.create_template("Custom", {"hips": "root_hips, pelvis", "head": ["head_jnt"]})
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "nested", "custom.json")
            templates.save_template(template, file_path)
            loaded = templates.load_template(file_path)
        self.assertEqual(["root_hips", "pelvis"], loaded["roles"]["hips"])
        self.assertEqual("Custom", loaded["name"])


class TestMotionEvalPresets(unittest.TestCase):
    def test_default_preset_resolves_every_check(self):
        resolved = presets.resolve_preset(presets.DEFAULT_PRESET)
        self.assertEqual(set(presets.CHECKS_BY_KEY.keys()), set(resolved["checks"].keys()))

    def test_compact_preset_keeps_only_overrides(self):
        preset = presets.set_check_value(presets.DEFAULT_PRESET, "foot_slide", "slide_speed", 1.5)
        preset = presets.set_check_value(preset, "jitter", "fail_below", 20)
        expected = {"foot_slide": {"parameters": {"slide_speed": 1.5}}, "jitter": {"fail_below": 20}}
        self.assertEqual(expected, preset["checks"])

    def test_setting_default_value_removes_override(self):
        preset = presets.set_check_value(presets.DEFAULT_PRESET, "jitter", "weight", 2.0)
        preset = presets.set_check_value(preset, "jitter", "weight", 1.0)
        self.assertEqual({}, preset["checks"])

    def test_values_are_clamped(self):
        preset = presets.set_check_value(presets.DEFAULT_PRESET, "jitter", "fail_below", 500)
        self.assertEqual(100, presets.resolve_preset(preset)["checks"]["jitter"]["fail_below"])

    def test_parse_frame_ranges(self):
        expected = [[10, 24], [80, 80], [5, 7]]
        self.assertEqual(expected, presets.parse_frame_ranges("10-24, 80 7-5"))

    def test_invalid_frame_range_is_reported(self):
        preset = presets.set_global_value(presets.DEFAULT_PRESET, "ignore_ranges", "abc")
        self.assertTrue(presets.validate_preset(preset))

    def test_save_and_load_round_trip(self):
        preset = presets.set_global_value(presets.create_preset("Loose", "biped"), "overall_fail_below", 30)
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "loose.json")
            presets.save_preset(preset, file_path)
            loaded = presets.load_preset(file_path)
        self.assertEqual({"overall_fail_below": 30}, loaded["settings"])
        self.assertEqual("biped", loaded["mode"])


class TestMotionEvalScoring(unittest.TestCase):
    def test_penalty_sum(self):
        entries = [{"score": 90, "weight": 1.0}, {"score": 50, "weight": 0.5}]
        self.assertEqual(65, scoring.combine_scores(entries, presets.SCORE_METHOD_PENALTY_SUM))

    def test_weighted_average(self):
        entries = [{"score": 90, "weight": 1.0}, {"score": 60, "weight": 0.5}]
        self.assertEqual(80, scoring.combine_scores(entries, presets.SCORE_METHOD_WEIGHTED_AVERAGE))

    def test_skipped_checks_do_not_count(self):
        entries = [{"score": None, "weight": 1.0}, {"score": 70, "weight": 1.0}]
        self.assertEqual(70, scoring.combine_scores(entries, presets.SCORE_METHOD_MINIMUM))

    def test_allow_failure_downgrades_to_warning(self):
        values = {"fail_below": 50, "warn_below": 85, "allow_failure": True}
        self.assertEqual(checks_base.STATUS_WARNING, scoring.get_check_status(10, values))


class TestMotionEvalEvaluation(unittest.TestCase):
    def setUp(self):
        self.biped_preset = presets.create_preset(mode=checks_base.MODE_BIPED)

    def test_clean_idle_scores_high(self):
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), self.biped_preset)
        failing = [entry["key"] for entry in report["checks"] if entry["status"] in ("warning", "failed")]
        self.assertEqual([], failing)
        self.assertEqual(100, report["score"])
        self.assertEqual(checks_base.STATUS_PASSED, report["status"])

    def test_reference_length_is_leg_length(self):
        data = checks_base.MotionData(build_sample(build_idle_positions()), mode=checks_base.MODE_BIPED)
        self.assertAlmostEqual(82.0, data.get_reference_length(), delta=0.5)

    def test_position_pop_is_detected(self):
        positions = build_idle_positions()
        for role in UPPER_BODY:
            hips = positions[role][40]
            positions[role][40] = (hips[0] + 40.0, hips[1], hips[2])
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        entry = get_check_entry(report, "position_pops")
        self.assertEqual([[41, 41]], entry["spans"])
        self.assertLess(entry["score"], 100)

    def test_foot_slide_is_detected(self):
        positions = build_idle_positions()
        step = 0.4 * 82.0 / FPS
        for role in ("left_foot", "left_toe"):
            positions[role] = [
                (position[0], position[1], position[2] + step * min(max(index - 30, 0), 30))
                for index, position in enumerate(positions[role])
            ]
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        entry = get_check_entry(report, "foot_slide")
        self.assertGreater(entry["flagged_frames"], 20)
        self.assertEqual("left foot", entry["offenders"][0]["name"])

    def test_jitter_is_detected(self):
        positions = build_idle_positions()
        positions["head"] = [
            (position[0] + (3.0 if index % 2 else -3.0), position[1], position[2])
            for index, position in enumerate(positions["head"])
        ]
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        entry = get_check_entry(report, "jitter")
        self.assertGreater(entry["flagged_frames"], 40)
        self.assertEqual(checks_base.STATUS_FAILED, entry["status"])

    def test_ignore_ranges_remove_findings(self):
        positions = build_idle_positions()
        for role in UPPER_BODY:
            hips = positions[role][40]
            positions[role][40] = (hips[0] + 40.0, hips[1], hips[2])
        preset = presets.set_global_value(self.biped_preset, "ignore_ranges", "38-45")
        report = evaluation.evaluate_sample(build_sample(positions), preset)
        self.assertEqual(0, get_check_entry(report, "position_pops")["events"])

    def test_disabled_check_is_reported_disabled(self):
        preset = presets.set_check_value(self.biped_preset, "jitter", "enabled", False)
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), preset)
        self.assertEqual(checks_base.STATUS_DISABLED, get_check_entry(report, "jitter")["status"])

    def test_missing_roles_skip_biped_checks(self):
        positions = build_idle_positions()
        positions.pop("left_leg")
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        entry = get_check_entry(report, "knee_hyperextension")
        self.assertEqual(checks_base.STATUS_SKIPPED, entry["status"])
        self.assertIn("left_leg", entry["skip_reason"])

    def test_knee_hyperextension_is_detected(self):
        positions = build_idle_positions()
        for index in range(20, 50):
            knee = positions["left_leg"][index]
            positions["left_leg"][index] = (knee[0], knee[1], knee[2] - 9.0)
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        entry = get_check_entry(report, "knee_hyperextension")
        self.assertEqual(30, entry["flagged_frames"])
        self.assertEqual("left knee", entry["offenders"][0]["name"])

    def test_general_mode_has_no_biped_checks(self):
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), presets.create_preset())
        self.assertNotIn("foot_slide", [entry["key"] for entry in report["checks"]])

    def test_floating_and_gravity(self):
        positions = build_idle_positions(frame_count=120)
        for index in range(30, 90):
            for role in positions:
                position = positions[role][index]
                positions[role][index] = (position[0], position[1] + 50.0, position[2])
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        self.assertGreater(get_check_entry(report, "floating")["flagged_frames"], 0)
        self.assertGreater(get_check_entry(report, "airborne_gravity")["flagged_frames"], 0)

    def test_hand_through_torso(self):
        positions = build_idle_positions()
        for index in range(20, 40):
            spine = positions["spine"][index]
            positions["left_hand"][index] = (spine[0], spine[1] + 5.0, spine[2])
            positions["left_forearm"][index] = (spine[0] + 2.0, spine[1] + 12.0, spine[2] + 1.0)
        report = evaluation.evaluate_sample(build_sample(positions), self.biped_preset)
        self.assertGreater(get_check_entry(report, "limb_intersection")["flagged_frames"], 0)

    def test_z_up_matches_y_up(self):
        positions = build_idle_positions()
        z_up_positions = {
            role: [(position[0], -position[2], position[1]) for position in role_positions]
            for role, role_positions in positions.items()
        }
        z_up_sample = build_sample(z_up_positions)
        z_up_sample["up_axis"] = "z"
        report = evaluation.evaluate_sample(z_up_sample, self.biped_preset)
        self.assertEqual(100, report["score"])

    def test_summary_lines(self):
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), self.biped_preset)
        lines = evaluation.summarize_report(report)
        self.assertTrue(lines[0].startswith("Score: 100/100"))

    def test_evaluator_name_has_no_package_prefix(self):
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), self.biped_preset)
        self.assertEqual("core.motion_eval", report["evaluator"])

    def test_series_are_only_stored_when_requested(self):
        sample = build_sample(build_idle_positions())
        report = evaluation.evaluate_sample(sample, self.biped_preset)
        self.assertFalse(any("chart" in entry for entry in report["checks"]))
        report = evaluation.evaluate_sample(sample, self.biped_preset, include_series=True)
        chart = get_check_entry(report, "foot_slide")["chart"]
        self.assertEqual(["left foot (planted)", "right foot (planted)"], [item["label"] for item in chart["series"]])
        self.assertEqual(FRAME_COUNT, len(chart["series"][0]["values"]))
        self.assertEqual(0.3, chart["threshold"])

    def test_every_enabled_check_records_a_series(self):
        preset = self.biped_preset
        for check_key in ("balance", "gait_asymmetry", "below_ground", "t_pose", "elbow_side_bend"):
            preset = presets.set_check_value(preset, check_key, "enabled", True)
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), preset, include_series=True)
        missing = [entry["key"] for entry in report["checks"] if not entry.get("chart")]
        self.assertEqual([], missing)

    def test_strip_series_keeps_the_original(self):
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), self.biped_preset,
                                            include_series=True)
        stripped = evaluation.strip_series(report)
        self.assertFalse(any("chart" in entry for entry in stripped["checks"]))
        self.assertTrue(any("chart" in entry for entry in report["checks"]))

    def test_ignored_ranges_are_reported_as_frames(self):
        preset = presets.set_global_value(self.biped_preset, "ignore_ranges", "10-12")
        report = evaluation.evaluate_sample(build_sample(build_idle_positions()), preset)
        self.assertEqual([[10, 12]], report["ignored_ranges"])


def set_limb_bend(positions, side, parts, index, upper_length, lower_length, bend, side_angle=0.0,
                  bend_direction=1.0):
    """Places a straight-down limb bent forward (or backward) and optionally sideways on one frame.

    Args:
        positions (dict): Role to positions (edited in place).
        side (str): "left" or "right".
        parts (tuple): Upper, middle, and lower role suffixes.
        index (int): Frame index.
        upper_length (float): Upper bone length.
        lower_length (float): Lower bone length.
        bend (float): Bend in degrees towards bend_direction (negative bends the other way).
        side_angle (float): Sideways angle out of the bend plane, in degrees.
        bend_direction (float): 1.0 bends towards +Z (elbows), -1.0 towards -Z (knees).
    """
    upper_role, middle_role, lower_role = [f"{side}_{part}" for part in parts]
    start = positions[upper_role][index]
    middle = (start[0], start[1] - upper_length, start[2])
    bend_radians = math.radians(bend)
    side_radians = math.radians(side_angle)
    direction = (math.sin(side_radians), -math.cos(side_radians) * math.cos(bend_radians),
                 bend_direction * math.cos(side_radians) * math.sin(bend_radians))
    positions[middle_role][index] = middle
    positions[lower_role][index] = math_utils.add(middle, math_utils.scale(direction, lower_length))


def set_arm_elevation(positions, index, elevation):
    """Places both arms straight and sideways at an elevation on one frame.

    Args:
        positions (dict): Role to positions (edited in place).
        index (int): Frame index.
        elevation (float): Degrees above horizontal (0 = T-pose, -80 = arms down).
    """
    radians = math.radians(elevation)
    for side, side_sign in (("left", 1.0), ("right", -1.0)):
        shoulder = positions[f"{side}_arm"][index]
        direction = (side_sign * math.cos(radians), math.sin(radians), 0.0)
        positions[f"{side}_forearm"][index] = math_utils.add(shoulder, math_utils.scale(direction, 27.0))
        positions[f"{side}_hand"][index] = math_utils.add(shoulder, math_utils.scale(direction, 50.0))


def build_elevation_positions(elevations):
    """Builds an idle whose straight arms follow an elevation per frame.

    Args:
        elevations (list): Arm elevation in degrees per frame.

    Returns:
        dict: Role to positions.
    """
    positions = build_idle_positions(frame_count=len(elevations))
    for index, elevation in enumerate(elevations):
        set_arm_elevation(positions, index, elevation)
    return positions


def ramp(start_value, end_value, count):
    """Builds evenly spaced values.

    Args:
        start_value (float): First value.
        end_value (float): Last value.
        count (int): Number of values.

    Returns:
        list: Values from start to end.
    """
    return [start_value + (end_value - start_value) * step / max(count - 1, 1) for step in range(count)]


class TestMotionEvalDirections(unittest.TestCase):
    def test_signed_angle_around_axis(self):
        self.assertAlmostEqual(90.0, math_utils.signed_angle((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        self.assertAlmostEqual(-90.0, math_utils.signed_angle((1, 0, 0), (0, 1, 0), (0, 0, -1)))

    def test_rotate_from_to(self):
        result = math_utils.rotate_from_to((0, 0, 1), (1, 0, 0), (0, 1, 0))
        for expected, value in zip((0.0, 0.0, 1.0), result):
            self.assertAlmostEqual(expected, value)

    def test_local_world_round_trip(self):
        rotation = math_utils.matrix_rotation(build_rotated_matrix((0, 0, 0), (0.0, 1.0, 0.0), 35.0))
        vector = (0.3, -0.2, 0.9)
        result = math_utils.to_world(rotation, math_utils.to_local(rotation, vector))
        for expected, value in zip(vector, result):
            self.assertAlmostEqual(expected, value)

    def test_circular_median_wraps(self):
        self.assertAlmostEqual(180.0, abs(math_utils.circular_median_degrees([170.0, -170.0, 180.0])))

    def test_perpendicular_vector(self):
        direction = math_utils.normalize((0.2, -0.9, 0.1))
        self.assertAlmostEqual(0.0, math_utils.dot(direction, math_utils.perpendicular_vector(direction)))


class TestMotionEvalJointLimits(unittest.TestCase):
    def setUp(self):
        self.biped_preset = presets.create_preset(mode=checks_base.MODE_BIPED)

    def evaluate(self, positions, rotations=None, preset=None):
        """Evaluates a synthetic clip.

        Args:
            positions (dict): Role to positions.
            rotations (dict, optional): See build_sample.
            preset (dict, optional): Preset; defaults to the biped preset.

        Returns:
            dict: Report.
        """
        return evaluation.evaluate_sample(build_sample(positions, rotations=rotations), preset or self.biped_preset)

    def test_idle_passes_every_limit(self):
        report = self.evaluate(build_idle_positions())
        for check_key in ("elbow_hyperextension", "knee_side_bend", "wrist_bend", "forearm_twist", "head_turn"):
            self.assertEqual(checks_base.STATUS_PASSED, get_check_entry(report, check_key)["status"])

    def test_unbent_hinge_is_reported_not_measured(self):
        entry = get_check_entry(self.evaluate(build_idle_positions()), "elbow_hyperextension")
        self.assertIn("never bends", entry["details"][0])

    def test_elbow_hyperextension_is_detected(self):
        positions = build_idle_positions()
        for index in range(FRAME_COUNT):
            bend = -45.0 if 60 <= index < 80 else 70.0
            set_limb_bend(positions, "left", ("arm", "forearm", "hand"), index, 27.0, 23.0, bend)
        preset = presets.set_check_value(self.biped_preset, "elbow_side_bend", "enabled", True)
        report = self.evaluate(positions, preset=preset)
        entry = get_check_entry(report, "elbow_hyperextension")
        self.assertEqual(20, entry["flagged_frames"])
        self.assertEqual("left elbow", entry["offenders"][0]["name"])
        self.assertEqual(0, get_check_entry(report, "elbow_side_bend")["flagged_frames"])

    def test_elbow_side_bend_is_detected(self):
        positions = build_idle_positions()
        for index in range(FRAME_COUNT):
            side_angle = 70.0 if 60 <= index < 80 else 0.0
            set_limb_bend(positions, "left", ("arm", "forearm", "hand"), index, 27.0, 23.0, 70.0, side_angle)
        preset = presets.set_check_value(self.biped_preset, "elbow_side_bend", "enabled", True)
        report = self.evaluate(positions, preset=preset)
        self.assertEqual(20, get_check_entry(report, "elbow_side_bend")["flagged_frames"])
        self.assertEqual(0, get_check_entry(report, "elbow_hyperextension")["flagged_frames"])

    def test_knee_side_bend_is_detected(self):
        positions = build_idle_positions()
        for index in range(FRAME_COUNT):
            side_angle = 55.0 if 60 <= index < 80 else 0.0
            set_limb_bend(positions, "left", ("up_leg", "leg", "foot"), index, 42.0, 40.0, 60.0, side_angle,
                          bend_direction=-1.0)
        entry = get_check_entry(self.evaluate(positions), "knee_side_bend")
        self.assertEqual(20, entry["flagged_frames"])
        self.assertEqual("left knee", entry["offenders"][0]["name"])

    def test_wrist_bend_is_detected(self):
        rotations = {"left_hand": {index: ((1.0, 0.0, 0.0), 120.0) for index in range(40, 60)}}
        report = self.evaluate(build_idle_positions(), rotations)
        entry = get_check_entry(report, "wrist_bend")
        self.assertEqual(20, entry["flagged_frames"])
        self.assertEqual("left wrist", entry["offenders"][0]["name"])

    def test_forearm_twist_is_detected_without_wrist_bend(self):
        rest = REST_POSE
        axis = math_utils.normalize(math_utils.subtract(rest["left_hand"], rest["left_forearm"]))
        rotations = {"left_hand": {index: (axis, 150.0) for index in range(40, 60)}}
        report = self.evaluate(build_idle_positions(), rotations)
        entry = get_check_entry(report, "forearm_twist")
        self.assertEqual(20, entry["flagged_frames"])
        self.assertEqual("left forearm", entry["offenders"][0]["name"])
        self.assertEqual(0, get_check_entry(report, "wrist_bend")["flagged_frames"])

    def test_head_turn_is_detected(self):
        rotations = {"head": {index: ((0.0, 1.0, 0.0), 130.0) for index in range(40, 60)}}
        entry = get_check_entry(self.evaluate(build_idle_positions(), rotations), "head_turn")
        self.assertEqual(20, entry["flagged_frames"])

    def test_limits_match_in_z_up(self):
        rotations = {"head": {index: ((0.0, 1.0, 0.0), 130.0) for index in range(40, 60)}}
        sample = build_sample(build_idle_positions(), rotations=rotations)
        for node in sample["nodes"].values():
            converted = []
            for matrix in node["matrices"]:
                rows = [matrix[0:3], matrix[4:7], matrix[8:11], matrix[12:15]]
                rows = [(row[0], -row[2], row[1]) for row in rows]
                converted.append([rows[0][0], rows[0][1], rows[0][2], 0.0, rows[1][0], rows[1][1], rows[1][2], 0.0,
                                  rows[2][0], rows[2][1], rows[2][2], 0.0, rows[3][0], rows[3][1], rows[3][2], 1.0])
            node["matrices"] = converted
        sample["up_axis"] = "z"
        report = evaluation.evaluate_sample(sample, self.biped_preset)
        self.assertEqual(20, get_check_entry(report, "head_turn")["flagged_frames"])

    def test_missing_arm_roles_skip_arm_limits(self):
        positions = build_idle_positions()
        for role in ("left_hand", "right_hand"):
            positions.pop(role)
        entry = get_check_entry(self.evaluate(positions), "wrist_bend")
        self.assertEqual(checks_base.STATUS_SKIPPED, entry["status"])


class TestMotionEvalTPose(unittest.TestCase):
    def setUp(self):
        self.preset = presets.set_check_value(presets.create_preset(mode=checks_base.MODE_BIPED),
                                              "t_pose", "enabled", True)

    def evaluate(self, elevations, **parameters):
        """Evaluates a clip of straight arms at the given elevations.

        Args:
            elevations (list): Arm elevation per frame.
            **parameters: T-pose parameter overrides.

        Returns:
            dict: T-pose check entry.
        """
        preset = self.preset
        for key, value in parameters.items():
            preset = presets.set_check_value(preset, "t_pose", key, value)
        report = evaluation.evaluate_sample(build_sample(build_elevation_positions(elevations)), preset)
        return get_check_entry(report, "t_pose")

    def test_off_by_default(self):
        self.assertFalse(presets.get_check_defaults("t_pose")["enabled"])

    def test_held_t_pose_at_start_is_detected(self):
        entry = self.evaluate([0.0] * 30 + ramp(0.0, -80.0, 10) + [-80.0] * 50)
        self.assertEqual(1, entry["events"])
        self.assertEqual(1, entry["spans"][0][0])
        self.assertEqual(checks_base.STATUS_FAILED, entry["status"])

    def test_held_t_pose_at_end_is_detected(self):
        entry = self.evaluate([-80.0] * 50 + ramp(-80.0, 0.0, 10) + [0.0] * 30)
        self.assertEqual(1, entry["events"])
        self.assertEqual(90, entry["spans"][0][1])

    def test_middle_t_pose_needs_search_anywhere(self):
        elevations = [-80.0] * 25 + ramp(-80.0, 0.0, 10) + [0.0] * 20 + ramp(0.0, -80.0, 10) + [-80.0] * 25
        self.assertEqual(0, self.evaluate(elevations, edge_seconds=0.5)["events"])
        self.assertEqual(1, self.evaluate(elevations, search="anywhere")["events"])

    def test_passing_through_t_pose_is_ignored(self):
        elevations = [-80.0] * 30 + ramp(-80.0, 80.0, 15) + ramp(80.0, -80.0, 15) + [-80.0] * 30
        self.assertEqual(0, self.evaluate(elevations, search="anywhere")["events"])

    def test_a_pose_needs_pose_type(self):
        elevations = [-45.0] * 30 + ramp(-45.0, -80.0, 10) + [-80.0] * 50
        self.assertEqual(0, self.evaluate(elevations)["events"])
        self.assertEqual(1, self.evaluate(elevations, pose_type="both")["events"])
        self.assertEqual(1, self.evaluate(elevations, pose_type="a")["events"])

    def test_arms_down_idle_is_not_a_pose(self):
        self.assertEqual(0, self.evaluate([-80.0] * FRAME_COUNT, search="anywhere")["events"])


class TestMotionEvalGraphs(unittest.TestCase):
    def setUp(self):
        positions = build_idle_positions()
        for role in UPPER_BODY:
            hips = positions[role][40]
            positions[role][40] = (hips[0] + 40.0, hips[1], hips[2])
        preset = presets.create_preset(mode=checks_base.MODE_BIPED)
        self.report = evaluation.evaluate_sample(build_sample(positions), preset, include_series=True)

    def test_check_chart_description(self):
        chart = report_graphs.build_check_chart(self.report, get_check_entry(self.report, "position_pops"))
        self.assertEqual("Position Pops", chart["title"])
        self.assertEqual(1, chart["start_frame"])
        self.assertEqual([[41, 41]], chart["spans"])
        self.assertLess(chart["minimum"], chart["maximum"])

    def test_spikes_are_clipped_relative_to_threshold(self):
        series = [{"label": "node", "values": [0.0, 1.0, 100.0]}]
        minimum, maximum, clipped = report_graphs.get_value_range(series, 2.0, checks_base.CHART_ABOVE)
        self.assertTrue(clipped)
        self.assertLess(maximum, 10.0)

    def test_summary_lists_enabled_checks(self):
        summary = report_graphs.build_summary_chart(self.report)
        labels = [row["label"] for row in summary["rows"]]
        self.assertIn("Position Pops", labels)
        self.assertNotIn("Balance", labels)

    def test_only_issue_entries(self):
        keys = [entry["key"] for entry in report_graphs.get_graph_entries(self.report, only_issues=True)]
        self.assertIn("position_pops", keys)
        self.assertNotIn("foot_slide", keys)

    def test_safe_file_name(self):
        self.assertEqual("walk_01_final", report_graphs.safe_file_name("Walk 01 (final)"))
        self.assertEqual("untitled", report_graphs.safe_file_name(""))


class TestMotionEvalBatchSummary(unittest.TestCase):
    def setUp(self):
        positions = build_idle_positions()
        clean = evaluation.evaluate_sample(build_sample(positions), presets.create_preset())
        for role in UPPER_BODY:
            hips = positions[role][40]
            positions[role][40] = (hips[0] + 40.0, hips[1], hips[2])
        broken = evaluation.evaluate_sample(build_sample(positions), presets.create_preset())
        self.entries = [
            batch_summary.build_batch_entry(clean, "D:/anims/clean.ma"),
            batch_summary.build_batch_entry(broken, "D:/anims/broken.ma"),
        ]

    def test_entries_sort_lowest_score_first(self):
        names = [entry["name"] for entry in batch_summary.sort_batch_entries(self.entries)]
        self.assertEqual(["broken.ma", "clean.ma"], names)

    def test_disabled_checks_are_left_out(self):
        keys = [check["key"] for check in self.entries[0]["checks"]]
        self.assertNotIn("below_ground", keys)

    def test_totals_count_statuses(self):
        totals = batch_summary.build_batch_totals(self.entries)
        self.assertEqual(2, totals["files"])
        self.assertEqual(1, totals["statuses"]["passed"])
        pops = totals["checks"]["position_pops"]
        self.assertGreater(pops["failed"] + pops["warning"], 0)

    def test_summary_lists_worst_file_first(self):
        text = "\n".join(batch_summary.build_batch_summary_lines(self.entries))
        self.assertLess(text.index("broken.ma"), text.index("clean.ma"))
        self.assertIn("Position Pops", text)

    def test_batch_chart_has_a_cell_per_check(self):
        chart = batch_summary.build_batch_chart(self.entries)
        self.assertEqual("broken.ma", chart["rows"][0]["label"])
        self.assertEqual(len(chart["columns"]), len(chart["rows"][0]["cells"]))

    def test_batch_chart_renders(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, "batch.png")
            self.assertTrue(report_graphs.render_batch_chart(batch_summary.build_batch_chart(self.entries), file_path))
            self.assertTrue(os.path.isfile(file_path))


class TestMotionEvalOutputs(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.report = evaluation.evaluate_sample(build_sample(build_idle_positions()), presets.create_preset())

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_options_fill_defaults(self):
        options = outputs.resolve_output_options({"graphs_per_file": 1, "unknown": True})
        self.assertTrue(options["graphs_per_file"])
        self.assertTrue(options["file_folders"])
        self.assertNotIn("unknown", options)

    def test_file_folder_option(self):
        with_folders = outputs.get_file_output_dir("D:/out", "D:/in/Walk 01.ma")
        without_folders = outputs.get_file_output_dir("D:/out", "D:/in/Walk 01.ma", {"file_folders": False})
        self.assertEqual(os.path.join("D:/out", "walk_01"), with_folders)
        self.assertEqual("D:/out", without_folders)

    def test_file_and_batch_outputs_are_written(self):
        options = {"summary_per_file": True, "report_per_file": True, "report_batch": True}
        written = outputs.write_file_outputs(self.report, "D:/in/walk.ma", self.temp_dir.name, options)
        self.assertEqual(["walk_summary.txt", "walk_report.json"], [os.path.basename(path) for path in written])
        entries = [batch_summary.build_batch_entry(self.report, "D:/in/walk.ma")]
        batch = outputs.write_batch_outputs(entries, self.temp_dir.name, options)
        self.assertEqual([outputs.BATCH_SUMMARY_FILE_NAME, outputs.BATCH_REPORT_FILE_NAME],
                         [os.path.basename(path) for path in batch])


class TestMotionEvalRunnerJob(unittest.TestCase):
    def test_create_job_merges_nested_options(self):
        job = runner.create_job(outputs={"graphs_batch": True}, skeleton="maya_humanik")
        self.assertTrue(job["outputs"]["graphs_batch"])
        self.assertTrue(job["outputs"]["summary_batch"])
        self.assertEqual("motionScore", job["score"]["score_attribute"])

    def test_skeleton_decides_the_mode(self):
        self.assertIsNone(runner.resolve_skeleton("none"))
        template = runner.resolve_skeleton("maya_humanik")
        biped = runner.resolve_job_preset(presets.create_preset(mode=checks_base.MODE_GENERAL), template)
        general = runner.resolve_job_preset(presets.create_preset(mode=checks_base.MODE_BIPED), None)
        self.assertEqual(checks_base.MODE_BIPED, presets.resolve_preset(biped)["mode"])
        self.assertEqual(checks_base.MODE_GENERAL, presets.resolve_preset(general)["mode"])

    def test_validate_job_needs_an_output_folder(self):
        self.assertTrue(runner.validate_job(runner.create_job()))
        self.assertEqual([], runner.validate_job(runner.create_job(output_dir="D:/out")))

    def test_job_round_trips_through_json(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, "job.json")
            runner.save_job(runner.create_job(skeleton="unreal_mannequin", output_dir="D:/out"), file_path)
            job = runner.load_job(file_path)
        self.assertEqual("unreal_mannequin", job["skeleton"])
        self.assertIn("graphs_only_on_failure", job["outputs"])

    def test_relative_job_paths_start_from_base_dir(self):
        job = runner.resolve_job_paths(
            runner.create_job(input_dir="01_input", output_dir="D:/out", skeleton="data/rig.json"), "D:/project"
        )
        self.assertEqual(os.path.normpath("D:/project/01_input"), job["input_dir"])
        self.assertEqual("D:/out", job["output_dir"])
        self.assertEqual(os.path.normpath("D:/project/data/rig.json"), job["skeleton"])

    def test_builtin_skeleton_is_not_treated_as_a_path(self):
        job = runner.resolve_job_paths(runner.create_job(skeleton="maya_humanik"), "D:/project")
        self.assertEqual("maya_humanik", job["skeleton"])

    def test_find_scene_files(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "sub"))
            for name in ("a.ma", "b.txt", os.path.join("sub", "c.MB")):
                open(os.path.join(directory, name), "w").close()
            names = [os.path.basename(path) for path in runner.find_scene_files(directory)]
            top_only = [os.path.basename(path) for path in runner.find_scene_files(directory, include_subfolders=False)]
        self.assertEqual(["a.ma", "c.MB"], names)
        self.assertEqual(["a.ma"], top_only)

    def test_describe_job(self):
        self.assertIn("Maya HumanIK", runner.describe_job(runner.create_job(skeleton="maya_humanik")))
        self.assertIn("General checks only", runner.describe_job(runner.create_job()))

    def test_run_rejects_a_missing_input_folder(self):
        with self.assertRaises(ValueError):
            runner.run(runner.create_job(input_dir="missing_folder", output_dir="D:/out"), base_dir="D:/nowhere",
                       show_progress=False)

    def test_relative_dir(self):
        self.assertEqual("walks", runner.get_relative_dir("D:/in/walks/a.ma", "D:/in"))
        self.assertEqual("", runner.get_relative_dir("E:/other/a.ma", "D:/in"))

    def test_quiet_output_swaps_and_restores_python_streams(self):
        original = sys.stdout
        with runner.quiet_output(True):
            print("hidden")
            self.assertIsNot(original, sys.stdout)
        self.assertIs(original, sys.stdout)

    def test_run_job_continues_after_an_unexpected_file_error(self):
        with mock.patch.object(runner, "evaluate_file", side_effect=RuntimeError("broken scene")):
            run_result = runner.run_job(["D:/in/a.ma", "D:/in/b.ma"], runner.create_job(output_dir="D:/out",
                                                                                       outputs={"summary_batch": False}))
        self.assertEqual(["error", "error"], [result["status"] for result in run_result["results"]])
        self.assertEqual("RuntimeError: broken scene", run_result["errors"]["D:/in/b.ma"])
        self.assertEqual(["D:/in/a.ma", "D:/in/b.ma"], run_result["failed_files"])

    def test_progress_printer_shows_running_file_then_result(self):
        stream = io.StringIO()
        printer = runner.ProgressPrinter(stream=stream)
        printer.start(1, 2, "D:/in/walk_01.ma")
        printer(1, 2, {"error": "", "score": 75, "status": "warning", "source": "D:/in/walk_01.ma"})
        lines = stream.getvalue().splitlines()
        self.assertEqual("[1/2] running... walk_01.ma", lines[0])
        self.assertTrue(lines[1].startswith("[1/2] 1 left, ~"))
        self.assertTrue(lines[1].endswith("WARNING score  75 | walk_01.ma"))


class TestMotionEvalUsdScene(unittest.TestCase):
    def test_is_usd_file(self):
        self.assertTrue(usd_scene.is_usd_file("D:/anims/walk.USDC"))
        self.assertFalse(usd_scene.is_usd_file("D:/anims/walk.mb"))

    def test_time_unit(self):
        self.assertEqual("ntsc", usd_scene.get_time_unit(30.0))
        self.assertEqual("12fps", usd_scene.get_time_unit(12))

    def test_up_axis_rotation(self):
        self.assertEqual(-90.0, usd_scene.get_up_axis_rotation("Z", "y"))
        self.assertEqual(90.0, usd_scene.get_up_axis_rotation("y", "z"))
        self.assertEqual(0.0, usd_scene.get_up_axis_rotation("y", "y"))

    def test_unit_scale(self):
        self.assertAlmostEqual(1.0, usd_scene.get_unit_scale(0.01, "cm"))
        self.assertAlmostEqual(100.0, usd_scene.get_unit_scale(1.0, "cm"))
        self.assertAlmostEqual(1.0, usd_scene.get_unit_scale(None, "cm"))

    def test_default_extensions_include_usd(self):
        self.assertIn(".usd", runner.create_job()["extensions"])
        self.assertTrue(runner.create_job()["align_up_axis"])


class TestMotionEvalModeLabels(unittest.TestCase):
    def test_mode_labels_include_check_counts(self):
        general_count = len(presets.get_checks_for_mode(checks_base.MODE_GENERAL))
        self.assertEqual(f"General ({general_count} checks)",
                         presets.get_mode_display_label(checks_base.MODE_GENERAL))

    def test_biped_summary_lists_both_groups(self):
        summary = presets.get_mode_check_summary(checks_base.MODE_BIPED)
        self.assertIn("General", summary)
        self.assertIn("Biped", summary)


if __name__ == "__main__":
    unittest.main()
