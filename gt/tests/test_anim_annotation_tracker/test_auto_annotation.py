"""Regression tests for automatic annotation and portable pose calibration."""

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from gt.tools.annotation_tracker import annotation_tracker_model, auto_annotation
from gt.tools.annotation_tracker import auto_annotation_local as local
from gt.tools.annotation_tracker import auto_annotation_model as model
from gt.tools.annotation_tracker import auto_annotation_motion as motion
from gt.tools.annotation_tracker import auto_annotation_quality as quality
from gt.tools.annotation_tracker import auto_annotation_rules as rules
from gt.tools.annotation_tracker import auto_annotation_scene as scene
from gt.tools.annotation_tracker import auto_annotation_vlm as vlm


class TestAutoAnnotation(unittest.TestCase):
    """Exercises automation contracts without launching Maya."""

    def setUp(self):
        """Loads the bundled schema used by default automation."""
        self.schema = annotation_tracker_model.read_schema(annotation_tracker_model.get_sample_schema_path())

    @staticmethod
    def sample_motion(fps=30, scale=1.0, seated=False, in_place=False):
        """Builds synthetic standing, seated, and locomotion examples.

        Args:
            fps (int): Frames per second.
            scale (float): Character scale multiplier.
            seated (bool): Whether the subject is sitting.
            in_place (bool): Whether to use an alternating cycle with a fixed pelvis.

        Returns:
            dict: Synthetic scene samples.
        """
        positions = []
        for frame in range(3 * fps):
            seconds = frame / fps
            travel = 0.0 if in_place or seated else max(0.0, seconds - 1.0)
            height = 0.50 if seated else 1.0
            sample = {"pelvis": (0, height, travel), "chest": (0, height + 0.50, travel)}
            for side, x_position, phase in (("left", 0.12, 0.0), ("right", -0.12, math.pi)):
                angle = 2 * math.pi * seconds + phase
                stride = 0.26 * math.cos(angle) if in_place else 0.0
                lift = max(0.0, 0.15 * math.sin(angle)) if in_place else 0.0
                advance = 0.5 if seated else stride
                sample[f"{side}_upper_leg"] = x_position, height, travel
                sample[f"{side}_knee"] = (x_position, height, travel + advance) if seated else (
                    x_position, height * 0.5 + lift * 0.5, travel + stride * 0.5
                )
                sample[f"{side}_foot"] = x_position, lift, travel + advance
            positions.append({name: tuple(value * scale for value in point) for name, point in sample.items()})
        return {"start": 1, "fps": fps, "positions": positions}

    def test_speed_is_normalized_and_ranges_respect_gaps(self):
        """Checks locomotion across character sizes and frame rates."""
        for fps, scale in ((30, 1.0), (60, 100.0)):
            with self.subTest(fps=fps, scale=scale):
                analysis = motion.analyze_motion(self.sample_motion(fps, scale))
                gaps = [(1, fps // 2), (fps * 2, fps * 3)]
                ranges = motion.generate_ranges(analysis, gaps, self.schema, {}, "stance")
                self.assertEqual(
                    [(1, fps // 2, "idle"), (fps * 2, fps * 3, "walk")],
                    [(item["start"], item["end"], item["custom_data"]["state"]) for item in ranges],
                )

    def test_an_in_place_gait_is_detected_without_root_translation(self):
        """Checks alternating foot travel can identify an in-place walk."""
        analysis = motion.analyze_motion(self.sample_motion(in_place=True))
        ranges = motion.generate_ranges(analysis, [(31, 61)], self.schema, {}, "stance")
        self.assertEqual(["walk"], [item["custom_data"]["state"] for item in ranges])

    def test_pose_examples_are_portable_and_extend_existing_labels(self):
        """Checks examples accumulate without scene names or rig paths."""
        seated = motion.analyze_motion(self.sample_motion(seated=True))
        moving = motion.analyze_motion(self.sample_motion())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotation_data" / "profile.json"
            model.add_profile_examples(path, motion.collect_examples(seated, [(1, 50, "sit")]))
            model.add_profile_examples(path, motion.collect_examples(moving, [(1, 24, "stand")]))
            model.add_profile_examples(path, motion.collect_examples(seated, [(1, 50, "sit")]))
            profile = model.read_profile(path)
            ranges = motion.generate_ranges(seated, [(1, 90)], self.schema, profile, "stance")
            self.assertEqual({"profile_version", "poses"}, set(json.loads(path.read_text(encoding="utf-8"))))
            self.assertEqual({"sit", "stand"}, set(profile["poses"]))
            self.assertEqual(1, len(profile["poses"]["sit"]))
            self.assertEqual("sit", ranges[0]["custom_data"]["stance"])
            self.assertEqual("stand", motion.match_pose(moving["descriptors"][10], profile["poses"]))

    def test_legacy_profile_drops_local_scene_details(self):
        """Checks version 1 settings import compatible normalized thresholds."""
        legacy = {
            "profile_version": 1, "scene": {"fps": 30, "leg_length": 90},
            "skeleton": {"root_joint": "PrivateRoot"},
            "calibration": {
                "source": "private.ma", "idle_max_velocity": 1.8,
                "locomotion_bands": [{"state": "walk", "max_velocity": 9.0}],
            },
        }
        profile = model.normalize_profile(legacy)
        self.assertEqual({"idle_max_speed": 0.6, "walk_max_speed": 3.0}, profile["locomotion"])
        self.assertNotIn("PrivateRoot", json.dumps(profile))
        self.assertNotIn("private.ma", json.dumps(profile))

    def test_distinctive_lean_cue_cannot_be_drowned_out_by_other_matches(self):
        """Checks a single taught leaning pose stays distinct from upright standing."""
        upright = motion.analyze_motion(self.sample_motion())["descriptors"][15]
        tilted = dict(upright, torso_pitch=14.0)
        poses = {"lean_forward": [model.summarize_example([tilted] * 20)]}
        self.assertEqual("", motion.match_pose(upright, poses))
        self.assertEqual("lean_forward", motion.match_pose(dict(tilted, torso_pitch=11.0), poses))

    def test_locomotion_thresholds_accumulate_from_distinct_examples(self):
        """Checks calibration can add speeds from different scenes."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            for state, speed in (("idle", 0.1), ("walk", 1.2), ("run", 3.6)):
                example = model.summarize_example([{"speed": speed}] * 20, ("speed",))
                profile = model.add_profile_examples(path, {}, {state: [example]})
        self.assertEqual({"idle_max_speed": 0.65, "walk_max_speed": 2.4}, profile["locomotion"])
        self.assertEqual({"idle", "walk", "run"}, set(profile["locomotion_examples"]))

    def test_hierarchy_requires_a_single_character(self):
        """Checks two similarly named rigs cannot be mixed or guessed."""
        relative = [
            "Hips", "Hips|LeftUpLeg", "Hips|LeftUpLeg|LeftLeg", "Hips|LeftUpLeg|LeftLeg|LeftFoot",
            "Hips|RightUpLeg", "Hips|RightUpLeg|RightLeg", "Hips|RightUpLeg|RightLeg|RightFoot",
        ]
        paths = [f"|{root}|{joint}" for root in ("rig1", "rig2") for joint in relative]
        cmds = Mock()
        cmds.ls.side_effect = lambda *args, **kwargs: (
            ["|rig2"] if args and kwargs.get("type") == "transform" else [] if args else paths
        )
        with self.assertRaisesRegex(ValueError, "Multiple skeleton candidates"):
            scene.resolve_skeleton(cmds)
        mapping = scene.resolve_skeleton(cmds, skeleton_root="|rig2")
        self.assertEqual("|rig2|Hips|RightUpLeg|RightLeg|RightFoot", mapping["right_foot"])

    def test_annotation_setup_is_visible_and_manually_invoked(self):
        """Checks a checked automation run cannot open Annotation Setup."""
        folder = annotation_tracker_model.get_default_automation_directory()
        scripts = annotation_tracker_model.get_automation_displays(folder)
        by_label = {script["label"]: script for script in scripts}
        self.assertEqual({"Auto Annotate", "Annotation Setup", "VLM Preview Request"}, set(by_label))
        self.assertFalse(by_label["Annotation Setup"]["hidden"])
        self.assertFalse(by_label["Annotation Setup"]["run_checked"])
        self.assertTrue(by_label["Auto Annotate"].get("run_checked", True))

    def test_explicit_profile_options_take_precedence(self):
        """Checks batch JSON and Python overrides use the same settings model."""
        context = {
            "environment_variables": {"GT_ANNOTATION_OPTIONS": '{"profile_path":"calibration/profile.json"}'},
            "annotation_options": {"vlm_mode": "review", "use_profile": False},
        }
        with patch.object(model, "load_settings", return_value=dict(model.DEFAULT_SETTINGS)):
            settings, _ = auto_annotation._effective_settings(
                context, {"vlm_mode": "off", "profile_path": "other_profile.json"}
            )
        self.assertTrue(settings["use_profile"])
        self.assertEqual("custom", settings["profile_location"])
        self.assertEqual("other_profile.json", settings["profile_path"])
        self.assertEqual("off", settings["vlm_mode"])

    def test_exported_settings_replace_local_preferences_for_the_run(self):
        """Checks a project-relative file carries settings, calibration, and schema together."""
        calibration = model.merge_profile_examples(
            {"profile_version": model.PROFILE_VERSION, "pose_cues": ["torso_pitch"]},
            {"lean": [model.summarize_example([{"torso_pitch": 22.0}] * 20)]},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset" / "annotation.json"
            model.write_settings_file(
                path,
                {"schema": self.schema, "use_profile": True, "calibration": calibration,
                 "commercial_use": False, "vlm_mode": "review", "short_name_fallback": False},
            )
            context = {
                "project_dir": directory,
                "environment_variables": {"annotation-settings": "dataset/annotation.json"},
            }
            with patch.object(model, "load_settings") as preferences:
                settings, explicit = auto_annotation._effective_settings(context, {"vlm_mode": "off"})
                restored = auto_annotation.load_annotation_settings(path)
                from_mapping, _ = auto_annotation._effective_settings({}, {"settings": restored})
            preferences.assert_not_called()
        self.assertEqual(calibration, auto_annotation._get_profile(settings, explicit, context))
        self.assertEqual(self.schema, settings["schema"])
        self.assertEqual("off", settings["vlm_mode"])
        self.assertFalse(settings["commercial_use"])
        self.assertFalse(settings["short_name_fallback"])
        self.assertEqual("review", from_mapping["vlm_mode"])

    def test_annotation_settings_exports_use_unprefixed_format_and_accept_legacy(self):
        """Checks interchange writes the new identifier and reads older files."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            model.write_settings_file(path, {"use_profile": False})
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("auto_annotation", document["format"])
            document["format"] = "gt_auto_annotation"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(model.DEFAULT_SETTINGS, model.read_settings_file(path))

    def test_duplicate_default_calibration_is_an_independent_snapshot(self):
        """Checks the default rules and thresholds are captured in an editable copy."""
        profile = model.copy_default_profile()
        self.assertEqual(rules.DEFAULT_RULES, profile["rules"])
        self.assertEqual(
            {"idle_max_speed": model.DEFAULT_IDLE_SPEED, "walk_max_speed": model.DEFAULT_WALK_SPEED},
            profile["locomotion"],
        )
        profile["rules"]["gap_frames"] += 1
        self.assertEqual(rules.DEFAULT_RULES, model.copy_default_profile()["rules"])

    def test_standalone_calibration_is_embedded_independently_of_its_source(self):
        """Checks removing a source calibration file leaves the settings usable."""
        sample = model.summarize_example([{"speed": 0.03, "pelvis_height": 0.9}] * 12)
        calibration = model.merge_profile_examples(None, {"stand": [sample]})
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "calibration.json"
            settings_path = folder / "settings.json"
            model.write_profile(source, calibration)
            model.write_settings_file(settings_path, {"calibration": model.read_profile(source), "use_profile": True})
            source.unlink()
            settings = model.read_settings_file(settings_path)
        self.assertEqual(calibration, settings["calibration"])
        self.assertTrue(settings["use_profile"])
        self.assertNotIn("profile_path", settings)

    def test_legacy_settings_copy_linked_calibration_on_save(self):
        """Checks migration preserves measurements after the old file moves."""
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            legacy = folder / "legacy.json"
            prefs = folder / f"{model.PREFS_NAME}.json"
            profile = model.merge_profile_examples(
                None, {"sit": [model.summarize_example([{"pelvis_height": 0.53}] * 12)]}
            )
            model.write_profile(legacy, profile)
            prefs.write_text(
                json.dumps({"use_profile": True, "profile_location": "custom", "profile_path": str(legacy)}),
                encoding="utf-8",
            )
            with patch.object(model, "_maya_preferences", return_value=None):
                with patch.object(model, "_prefs_directory", return_value=folder):
                    settings = model.load_settings()
                    model.save_settings(settings)
                    legacy.unlink()
                    self.assertEqual(profile, model.load_settings()["calibration"])
            self.assertNotIn("profile_path", json.loads(prefs.read_text(encoding="utf-8")))

    def test_reset_can_keep_embedded_calibration_or_remove_all_preferences(self):
        """Checks resetting defaults can retain independently imported measurements."""
        calibration = model.merge_profile_examples(
            None, {"sit": [model.summarize_example([{"pelvis_height": 0.53}] * 12)]}
        )
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            prefs = folder / f"{model.PREFS_NAME}.json"
            with patch.object(model, "_maya_preferences", return_value=None):
                with patch.object(model, "_prefs_directory", return_value=folder):
                    model.save_settings({"vlm_mode": "review", "calibration": calibration, "use_profile": True})
                    defaults = model.reset_settings(calibration, use_profile=True)
                    self.assertEqual("off", defaults["vlm_mode"])
                    self.assertEqual(calibration, model.load_settings()["calibration"])
                    self.assertEqual(model.DEFAULT_SETTINGS, model.reset_settings())
                    self.assertFalse(prefs.exists())

    def test_pose_matching_uses_only_selected_cues(self):
        """Checks cue selection changes matching without losing the other measurements."""
        measured = {"torso_pitch": 20.0, "speed": 0.0, "pelvis_height": 0.8, "knee_flexion": 12.0}
        poses = {"lean": [model.summarize_example([measured] * 20)]}
        query = dict(measured, pelvis_height=0.4, knee_flexion=70.0)
        self.assertEqual("", motion.match_pose(query, poses))
        self.assertEqual("lean", motion.match_pose(query, poses, {"torso_pitch"}))
        self.assertEqual("", motion.match_pose(query, poses, set()))
        self.assertIn("pelvis_height", poses["lean"][0]["features"])

    def test_stationary_activity_has_one_arrival_without_false_departures(self):
        """Checks apparent speed spikes during a stationary activity stay idle."""
        speeds = [1.3] * 25 + [0.0] * 10 + [0.45] * 14 + [0.0] * 12 + [0.48] * 15 + [0.0] * 25
        ground = [(min(index, 25) / 20, 0) for index in range(len(speeds))]
        analysis = {
            "start": 1, "fps": 30, "root_ground": ground,
            "descriptors": [{"speed": speed, "pelvis_height": 1.0} for speed in speeds],
        }
        duration = len(speeds)
        actual = motion.generate_ranges(analysis, [(1, duration)], self.schema, {}, rules.RANGE_NAME_FIELD)
        self.assertEqual(["walk", "enter", "idle"], [item["name"] for item in actual])
        self.assertEqual(duration, actual[-1]["end"])
        self.assertEqual(actual[-2]["end"] + 1, actual[-1]["start"])

    def test_transition_pairing_requires_arrival_followed_by_departure(self):
        """Checks the matching rule keeps only complete activity boundaries."""
        moving = [True] * 18 + [False] * 35 + [True] * 18
        writable = [True] * len(moving)
        options = dict(rules.DEFAULT_RULES, require_paired_transitions=True, transition_buffer_frames=3)
        labels = {"enter", "exit"}
        self.assertEqual(
            [("enter", 15, 17), ("exit", 53, 55)],
            rules.transition_markers(moving, options, labels, writable),
        )
        writable[53] = False
        self.assertEqual([], rules.transition_markers(moving, options, labels, writable))
        self.assertEqual([], rules.transition_markers(moving[:40], options, labels, writable[:40]))

    def test_initial_departure_is_opt_in_for_activity_markers(self):
        """Checks a walk from rest toward an activity labels its arrival only by default."""
        moving = [False] * 16 + [True] * 20 + [False] * 50
        writable = [True] * len(moving)
        labels = {"enter", "exit"}
        self.assertEqual([("enter", 30, 35)], rules.transition_markers(moving, rules.DEFAULT_RULES, labels, writable))
        options = dict(rules.DEFAULT_RULES, allow_initial_departure=True)
        self.assertEqual(
            [("exit", 16, 21), ("enter", 30, 35)], rules.transition_markers(moving, options, labels, writable),
        )

    def test_each_pose_example_requires_its_own_hold_and_adds_its_suffix(self):
        """Checks short matches clear and a held example names the generated range."""
        lean = {"speed": 0.0, "pelvis_height": 1.0, "torso_pitch": 20.0}
        neutral = dict(lean, torso_pitch=0.0)
        example = dict(
            model.summarize_example([lean] * 20), threshold=0.1, minimum_frames=10, suffix="wall lean"
        )
        profile = model.normalize_profile({
            "profile_version": model.PROFILE_VERSION, "pose_cues": ["torso_pitch"],
            "poses": {"leaning": [example]}, "rules": {"pose_minimum_frames": 2},
            "label_source": rules.RANGE_NAME_FIELD,
        })
        analysis = {
            "start": 1, "fps": 30, "descriptors": [neutral] * 12 + [lean] * 5 + [neutral] * 12 + [lean] * 20
        }
        ranges = motion.generate_ranges(analysis, [(1, 49)], self.schema, profile, rules.RANGE_NAME_FIELD)
        self.assertEqual(
            [("idle", 1, 29), ("idle_wall lean", 30, 49)],
            [(item["name"], item["start"], item["end"]) for item in ranges],
        )
        self.assertEqual("idle", ranges[1]["custom_data"]["state"])
        self.assertEqual("range_name", profile["label_source"])

    def test_training_can_use_named_activities_or_schema_fields(self):
        """Checks named ranges add custom examples and state is measured independently."""
        item = {"name": "wall lean", "custom_data": {"stance": "stand", "state": "idle"}}
        field = model.get_schema_fields(self.schema, "frame_range")["stance"]
        self.assertEqual(("wall lean", "idle"), model.get_training_labels(item, rules.RANGE_NAME_FIELD))
        self.assertEqual(("stand", "idle"), model.get_training_labels(item, "stance", field))
        self.assertEqual(("", "walk"), model.get_training_labels({"name": "walk"}, rules.RANGE_NAME_FIELD))
        generated = {"name": "activity_wall lean", "custom_data": {"state": "activity"}}
        self.assertEqual(("wall lean", ""), model.get_training_labels(generated, rules.RANGE_NAME_FIELD))

    def test_trained_activity_assigns_state_on_stationary_frames(self):
        """Checks a trained activity is distinguished from idle and preserves travel."""
        item = {"name": "vending machine", "custom_data": {"state": "activity"}}
        activity = {"speed": 0.0, "torso_pitch": 20.0, "pelvis_height": 1.0}
        neutral = dict(activity, torso_pitch=0.0)
        travel = dict(activity, speed=1.0)
        analysis = {"start": 1, "fps": 30, "descriptors": [travel] * 20 + [activity] * 20 + [neutral] * 20}
        example = model.summarize_example([activity] * 20)
        example.update(state="activity", threshold=0.1)
        profile = model.merge_profile_examples(
            {"profile_version": model.PROFILE_VERSION, "pose_cues": ["torso_pitch"],
             "rules": {"transition_mode": "off"}},
            {"vending machine": [example]},
        )
        self.assertTrue(model.is_activity_example(item))
        self.assertEqual(("vending machine", ""), model.get_training_labels(item, "stance"))
        spans = motion.generate_ranges(analysis, [(1, 60)], self.schema, profile, rules.RANGE_NAME_FIELD)
        self.assertEqual(["walk", "activity", "idle"], [row["custom_data"]["state"] for row in spans])
        self.assertEqual("activity_vending machine", spans[1]["name"])
        baseline = motion.generate_ranges(analysis, [(1, 60)], self.schema, {}, rules.RANGE_NAME_FIELD)
        self.assertEqual(["walk", "enter", "idle"], [row["custom_data"]["state"] for row in baseline])

    def test_sprint_uses_a_calibrated_run_limit(self):
        """Checks only a distinct calibrated sprint band changes running output."""
        training = {
            "run": [model.summarize_example([{"speed": 3.8}] * 20)],
            "sprint": [model.summarize_example([{"speed": 6.2}] * 20)],
        }
        profile = model.merge_profile_examples(None, {}, training)
        self.assertEqual(5.0, profile["locomotion"]["run_max_speed"])
        model.normalize_profile(profile)
        analysis = {
            "start": 1, "fps": 30,
            "descriptors": [
                {"speed": speed, "pelvis_height": 1.0} for speed in [3.8] * 20 + [6.2] * 20
            ],
        }
        calibrated = motion.generate_ranges(analysis, [(1, 40)], self.schema, profile, rules.RANGE_NAME_FIELD)
        baseline = motion.generate_ranges(analysis, [(1, 40)], self.schema, {}, rules.RANGE_NAME_FIELD)
        self.assertEqual(["run", "sprint"], [row["custom_data"]["state"] for row in calibrated])
        self.assertEqual(["run"], [row["custom_data"]["state"] for row in baseline])

    def test_retraining_preserves_existing_examples_and_updates_activity_state(self):
        """Checks new measured entries append and duplicate measurements keep their settings."""
        existing = model.summarize_example([{"torso_pitch": 20.0}] * 12)
        initial = model.merge_profile_examples(None, {"lean": [dict(existing, threshold=0.4, suffix="wall")]})
        new = model.summarize_example([{"torso_pitch": 30.0}] * 12)
        profile = model.merge_profile_examples(
            initial, {"lean": [dict(existing, state="activity"), new]}
        )
        first, second = profile["poses"]["lean"]
        self.assertEqual(("activity", 0.4, "wall"), (first["state"], first["threshold"], first["suffix"]))
        self.assertEqual(new, second)
        self.assertNotIn("state", initial["poses"]["lean"][0])

    def test_scene_payload_prefers_live_tracker_when_available(self):
        """Checks training can use pending annotation edits from the Tracker."""
        cmds = Mock()
        payload = {"file_data": {}, "range_data": [{"id": "live"}]}
        self.assertEqual(payload, scene.read_payload(cmds, {"get_annotation_payload": lambda: payload}))
        cmds.objExists.assert_not_called()

    def test_manual_dag_path_respects_short_name_fallback(self):
        """Checks stale paths fall back within one selected hierarchy when enabled."""
        paths = ["|New|A:Hips|A:Foot", "|Other|B:Hips|B:Foot"]
        saved_path = "|Old|A:Hips|A:Foot"
        actual = scene._resolve_manual_joint(saved_path, paths, "|New|A:Hips")
        self.assertEqual("|New|A:Hips|A:Foot", actual)
        with self.assertRaisesRegex(ValueError, "enable Short-name fallback"):
            scene._resolve_manual_joint(saved_path, paths, "|New|A:Hips", short_name_fallback=False)

        cmds = Mock()
        cmds.ls.side_effect = lambda *names, **kwargs: (
            ["|New|Root"] if names == ("Root",) and kwargs["type"] == "transform" else []
        )
        self.assertEqual("|New|Root", scene._find_skeleton_root(cmds, "|Old|Root", True))
        with self.assertRaisesRegex(ValueError, "root is missing"):
            scene._find_skeleton_root(cmds, "|Old|Root", False)

    def test_plan_images_splits_long_ranges_within_the_image_limit(self):
        """Checks long ranges get extra images and the total never exceeds the limit."""
        from gt.tools.annotation_tracker import auto_annotation_capture as capture

        spans = [(0, 1, 30), (1, 31, 330)]
        plan = capture.plan_images(spans, 4, 6, 30)
        self.assertEqual(4, len(plan))
        self.assertEqual([1], [item["parts"] for item in plan if item["range_index"] == 0])
        self.assertEqual({3}, {item["parts"] for item in plan if item["range_index"] == 1})
        covered = [(item["first"], item["last"]) for item in plan if item["range_index"] == 1]
        self.assertEqual((31, 330), (covered[0][0], covered[-1][1]))

    def test_plan_images_samples_ranges_evenly_when_over_the_limit(self):
        """Checks too many ranges are thinned evenly while keeping the first and last."""
        from gt.tools.annotation_tracker import auto_annotation_capture as capture

        spans = [(index, index * 10 + 1, index * 10 + 10) for index in range(10)]
        plan = capture.plan_images(spans, 3, 6, 30)
        self.assertEqual([0, 4, 9], [item["range_index"] for item in plan])

    def test_preview_request_writes_images_and_prompt_without_sending(self):
        """Checks the review folder is built from drawn sheets and no request is made."""
        from gt.tools.annotation_tracker import auto_annotation_capture as capture

        pose = {
            "pelvis": (0, 1, 0), "chest": (0, 1.5, 0), "left_upper_leg": (0, 1, -0.1), "right_upper_leg": (0, 1, 0.1),
            "left_knee": (0, 0.5, -0.1), "right_knee": (0, 0.5, 0.1), "left_foot": (0, 0, -0.1),
            "right_foot": (0, 0, 0.1),
        }
        analysis = {
            "start": 1, "fps": 30, "positions": [pose] * 40, "leg_length": 1.0, "floor": 0.0,
            "descriptors": [{"pelvis_height": 1.0}] * 40,
        }
        payload = {"file_data": {}, "range_data": [
            {"id": "a", "name": "idle", "start": 1, "end": 40, "locked": False, "custom_data": {"state": "idle"}},
        ]}
        settings = dict(model.DEFAULT_SETTINGS, vlm_mode="review")
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(capture, "get_cache_directory", return_value=Path(temporary)):
                with patch.object(vlm.urllib.request, "urlopen", side_effect=AssertionError("sent")):
                    result = vlm.preview_request(Mock(), settings, self.schema, payload, 1, 40, analysis)
                self.assertIsNotNone(result["folder"], result["warnings"])
                names = sorted(path.name for path in result["folder"].iterdir())
                purged = capture.purge_debug_files()
        self.assertEqual(1, result["images"])
        self.assertEqual([
                "image_01_range_1_frames_1-40.png", "prompt_01_file.txt", "prompt_02_range_1.txt",
                "prompt_03_file_context.txt", "request.json",
            ], names)
        self.assertEqual(5, purged)

    def _vlm_run_fixture(self):
        """Builds a two-range payload and fake images for request-splitting tests."""
        ranges = [
            {"start": 1, "end": 20, "locked": False, "name": "idle", "custom_data": {"state": "idle"}},
            {"start": 21, "end": 40, "locked": False, "name": "vending_machine", "custom_data": {"state": "activity"}},
        ]
        images = [(10, "image/png", "", "range_1 frames 1-20"), (30, "image/png", "", "range_2 frames 21-40")]
        settings = dict(model.DEFAULT_SETTINGS, vlm_mode="auto", vlm_local_auto_load=False)
        return {"file_data": {}, "range_data": ranges}, images, settings

    def test_vlm_sends_one_small_request_per_range_with_context(self):
        """Checks each range is requested alone, with its name and neighbours as evidence."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_style_recheck=False)
        calls = []

        def fake_request(provider_settings, prompt, sent_images, timeout, **kwargs):
            calls.append((prompt, sent_images))
            return []

        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", side_effect=fake_request):
                vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        self.assertEqual(4, len(calls))
        range_two = next(call for call in calls if '"range_2"' in call[0])
        self.assertEqual([images[1]], range_two[1])
        self.assertIn('"range_name": "vending_machine"', range_two[0])
        self.assertIn('"previous_range": {"name": "idle"', range_two[0])

    def test_vlm_keeps_good_replies_when_one_request_fails(self):
        """Checks a timed-out range does not discard other ranges' suggestions."""
        payload, images, settings = self._vlm_run_fixture()
        replies = {"range_1": [{"target": "range_1", "field": "stance", "value": "stand", "confidence": 0.95}]}

        def fake_request(provider_settings, prompt, sent_images, timeout, **kwargs):
            if '"range_2"' in prompt or '"file"' in prompt:
                raise ValueError("timed out")
            return replies["range_1"]

        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", side_effect=fake_request):
                result = vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        self.assertEqual(1, result["applied"])
        self.assertEqual("stand", payload["range_data"][0]["custom_data"]["stance"])
        self.assertTrue(any("failed" in message for message in result["warnings"]))

    def test_vlm_only_offers_the_allowed_fields(self):
        """Checks disabled fields never appear as targets."""
        payload, images, _ = self._vlm_run_fixture()
        targets, _ = vlm._targets(
            payload, self.schema, None, [10, 30], False, allowed_fields=["stance"], file_name="combat_walk"
        )
        offered = {field for spec in targets.values() for field in spec["fields"]}
        self.assertEqual({"stance"}, offered)
        self.assertNotIn("file", targets)

    def test_vlm_ignores_none_and_override_that_repeats_the_file_style(self):
        """Checks 'none' values and redundant style overrides are dropped and explained."""
        file_data = {"style": "relaxed"}
        options = {"type": "enum", "options": ["none", "relaxed", "tense"]}
        destinations = {
            "file": (file_data, {"style": options}, "File", {}),
            "range_1": ({}, {"override_style": options}, "Range", {}),
        }
        replies = [
            {"target": "range_1", "field": "override_style", "value": "none", "confidence": 0.99},
            {"target": "range_1", "field": "override_style", "value": "relaxed", "confidence": 0.9},
        ]
        dropped = []
        result = vlm._validated_suggestions(replies, destinations, dropped)
        self.assertEqual([], result)
        self.assertEqual(2, len(dropped))
        self.assertIn("none", dropped[0])
        self.assertIn("same as the file style", dropped[1])

    def test_vlm_targets_never_offer_none_as_a_choice(self):
        """Checks 'none' is removed from the options shown to the model."""
        payload, images, _ = self._vlm_run_fixture()
        targets, _ = vlm._targets(payload, self.schema, None, [10, 30], False, allowed_fields=["override_style"])
        options = targets["range_1"]["fields"]["override_style"]
        self.assertNotIn("none", options)
        self.assertIn("relaxed", options)

    def test_vlm_change_log_lists_before_and_after(self):
        """Checks each suggestion is described with its status."""
        proposal = {
            "label": "Range (1-20)", "field": "stance", "value": "sit", "confidence": 0.9, "compatible": True,
            "data": {},
        }
        weak = dict(proposal, field="override_style", value="tense", confidence=0.4)
        lines = vlm._describe_changes([proposal, weak], [proposal], 0.85, ["x ignored"])
        self.assertEqual("applied: Range (1-20) · stance: (empty) -> sit (90%)", lines[0])
        self.assertTrue(lines[1].startswith("deferred (confidence below 85%)"))
        self.assertEqual("x ignored", lines[2])

    def _run_replace_case(self, replace_existing, confidence):
        """Runs Auto-accept over a range whose stance is already stand and returns the stance afterward."""
        payload, images, settings = self._vlm_run_fixture()
        payload["range_data"][0]["custom_data"]["stance"] = "stand"
        settings.update(vlm_replace_existing=replace_existing, vlm_fields=["stance"])
        reply = [{"target": "range_1", "field": "stance", "value": "sit", "confidence": confidence}]
        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", return_value=reply):
                vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        return payload["range_data"][0]["custom_data"]["stance"]

    def test_auto_accept_replaces_existing_values_only_with_high_confidence(self):
        """Checks replacing needs the higher threshold and can be switched off."""
        self.assertEqual("sit", self._run_replace_case(True, 0.97))
        self.assertEqual("stand", self._run_replace_case(True, 0.88))
        self.assertEqual("stand", self._run_replace_case(False, 0.99))

    def test_vlm_targets_include_schema_descriptions(self):
        """Checks field descriptions from the schema reach the model."""
        payload, images, _ = self._vlm_run_fixture()
        targets, _ = vlm._targets(payload, self.schema, None, [10, 30], False, allowed_fields=["interaction_type"])
        self.assertIn("interaction_type", targets["range_1"]["field_notes"])

    def test_parse_suggestions_tolerates_fences_prose_and_bare_lists(self):
        """Checks common non-strict model replies still produce suggestions."""
        item = {"target": "range_1", "field": "stance", "value": "sit", "confidence": 0.9}
        wrapped = json.dumps({"suggestions": [item]})
        replies = [
            wrapped, f"```json\n{wrapped}\n```", f"Here is my answer: {wrapped} Hope that helps!",
            json.dumps([item]), json.dumps(item),
        ]
        for reply in replies:
            self.assertEqual([item], vlm.parse_suggestions(reply), reply)

    def test_parse_suggestions_keeps_the_raw_reply_when_unusable(self):
        """Checks an unusable reply raises an error that carries the text for inspection."""
        with self.assertRaises(vlm.VlmReplyError) as context:
            vlm.parse_suggestions("I think the character is walking.")
        self.assertEqual("I think the character is walking.", context.exception.raw)

    def test_vlm_retries_once_when_the_reply_is_not_json(self):
        """Checks a malformed reply is retried with a stricter note and then accepted."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["stance"])
        good = [{"target": "range_1", "field": "stance", "value": "stand", "confidence": 0.95}]
        prompts = []

        def fake_request(provider_settings, prompt, sent_images, timeout, **kwargs):
            prompts.append(prompt)
            if len(prompts) == 1:
                raise vlm.VlmReplyError("bad", raw="not json")
            return good

        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", side_effect=fake_request):
                result = vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        self.assertEqual(1, result["applied"])
        self.assertTrue(prompts[1].endswith(vlm.RETRY_NOTE))

    def test_local_request_asks_for_schema_json_and_zero_temperature(self):
        """Checks local requests force JSON output."""
        body = vlm._request_body("local", "model", "prompt", [(1, "image/png", "", "caption")], structured=True)
        self.assertEqual("json_schema", body["response_format"]["type"])
        self.assertEqual(0, body["temperature"])
        self.assertNotIn("response_format", vlm._request_body("local", "model", "prompt", [], structured=False))

    def test_empty_reply_from_a_token_limit_names_the_cause(self):
        """Checks a reasoning model that runs out of tokens gets a clear explanation."""
        response = {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}
        with self.assertRaisesRegex(vlm.VlmReplyError, "ran out of tokens"):
            vlm._response_text("local", response)

    def test_truncated_reply_is_retried_with_a_larger_token_budget(self):
        """Checks a reply cut off by the token limit is retried once with double the budget."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["stance"], vlm_max_tokens=2048)
        good = [{"target": "range_1", "field": "stance", "value": "stand", "confidence": 0.95}]
        budgets = []

        def fake_request(provider_settings, prompt, sent_images, timeout, **kwargs):
            budgets.append(kwargs["max_tokens"])
            if len(budgets) == 1:
                raise vlm.VlmReplyError("cut off", truncated=True)
            return good

        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", side_effect=fake_request):
                result = vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        self.assertEqual([2048, 4096], budgets[:2])
        self.assertEqual(1, result["applied"])

    def test_source_is_found_in_a_parent_folder_by_pattern(self):
        """Checks a deep parent folder is found by pattern regardless of the folders in between."""
        pattern = r"[A-Z][a-z]+_Set-[A-Za-z]+_\d{3}"
        path = r"Z:\data\Alpha_Set-Walk_001\02_tasks\04_post\Batch_015\clip_001.ma"
        self.assertEqual("Alpha_Set-Walk_001", model.find_source_in_path(path, pattern, 0))
        self.assertEqual("Alpha_Set-Walk_001", model.find_source_in_path(path.replace("\\", "/"), pattern, 4))
        self.assertEqual("", model.find_source_in_path(path, pattern, 2))

    def test_source_is_extracted_from_a_longer_folder_name(self):
        """Checks the matching part of a longer folder name is used when the parent folder is out of reach."""
        path = r"Z:\data\Alpha_Set-Walk_001\runs\Alpha_Set-Walk_001_r21_testing-walk\02_tasks\04_post\Batch_015\c.ma"
        pattern = r"^([A-Z][a-z]+_Set-[A-Za-z]+_\d{3})"
        self.assertEqual("", model.find_source_in_path(path, pattern, 3))
        self.assertEqual("Alpha_Set-Walk_001", model.find_source_in_path(path, pattern, 4))

    def test_source_without_pattern_uses_the_whole_folder_and_order_matters(self):
        """Checks the blank pattern and the search direction."""
        path = r"Z:\data\Outer_001\inner\Batch_015\clip.ma"
        self.assertEqual("Batch_015", model.find_source_in_path(path))
        self.assertEqual("data", model.find_source_in_path(path, "", 0, "outermost"))
        self.assertEqual("Outer_001", model.find_source_in_path(path, r"Outer_\d+", 0, "outermost"))

    def test_invalid_source_pattern_is_rejected(self):
        """Checks a broken regular expression is reported when settings are validated."""
        with self.assertRaises(ValueError):
            model.normalize_settings({"file_source_pattern": "([a-z"})

    def test_unlimited_tokens_omit_the_limit_except_for_anthropic(self):
        """Checks 0 means no limit for local requests while Anthropic still gets a value."""
        local = vlm._request_body("local", "model", "prompt", [], max_tokens=0)
        self.assertNotIn("max_tokens", local)
        anthropic = vlm._request_body("anthropic", "model", "prompt", [], max_tokens=0)
        self.assertEqual(vlm.MAX_REPLY_TOKENS, anthropic["max_tokens"])

    def test_source_presets_extract_what_they_describe(self):
        """Checks each example pattern on its sample folder name."""
        expected = {
            "Three parts, last is 3 digits (whole folder name)": "set-a_walk_001_r21_testing",
            "Three parts, last is 3 digits (stop after the digits)": "set-a_walk_001",
            "Text followed by a number (name_001)": "walkset_012",
            "Everything before the first underscore": "walkset",
            "Everything before a version or run tag (_v001, _r21)": "set-a_walk_001",
        }
        for label, pattern, sample in model.SOURCE_PATTERN_PRESETS:
            self.assertEqual(expected[label], model.preview_source_preset(pattern, sample), label)

    def test_source_fallback_uses_text_or_the_nearest_folder(self):
        """Checks what is used when no folder matches the pattern."""
        cmds = Mock()
        cmds.file.return_value = r"Z:\data\Plain_folder\clip.ma"
        base = dict(model.DEFAULT_SETTINGS, file_source_mode="path", file_source_pattern=r"^\d{9}$", file_source="Manual")
        self.assertEqual("", auto_annotation._resolve_source(cmds, dict(base, file_source_fallback="none")))
        self.assertEqual("Manual", auto_annotation._resolve_source(cmds, dict(base, file_source_fallback="text")))
        self.assertEqual("Plain_folder", auto_annotation._resolve_source(cmds, dict(base, file_source_fallback="folder")))

    def test_empty_file_style_uses_its_own_lower_threshold(self):
        """Checks a 60% file style passes while a 60% range stance is still deferred."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["style", "stance"], file_style_source="vlm", vlm_style_threshold=0.5)
        replies = [
            {"target": "file", "field": "style", "value": "relaxed", "confidence": 0.6},
            {"target": "range_1", "field": "stance", "value": "stand", "confidence": 0.6},
        ]
        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", return_value=replies):
                result = vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        self.assertEqual("relaxed", payload["file_data"]["style"])
        self.assertNotIn("stance", payload["range_data"][0]["custom_data"])
        self.assertEqual(1, result["applied"])

    def test_file_context_request_is_text_only_and_uses_the_range_timeline(self):
        """Checks the context request has no images, comes last, and includes new confident range values."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["context", "stance"], vlm_context_images=False)
        prompts = []

        def fake_request(provider_settings, prompt, sent_images, timeout, **kwargs):
            prompts.append((prompt, sent_images))
            if '"range_1"' in prompt and "Timeline" not in prompt:
                return [{"target": "range_1", "field": "stance", "value": "crouch", "confidence": 0.95}]
            if "Timeline" in prompt:
                return [{
                    "target": "file_context", "field": "context", "value": "The character crouches.", "confidence": 0.9,
                }]
            return []

        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", side_effect=fake_request):
                result = vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        context_prompt, context_images = prompts[-1]
        self.assertEqual([], context_images)
        self.assertIn("Timeline", context_prompt)
        self.assertIn("vending_machine", context_prompt)
        self.assertIn("stance=crouch", context_prompt)
        self.assertEqual("The character crouches.", payload["file_data"]["context"])
        self.assertEqual(2, result["applied"])

    def test_build_timeline_keeps_the_ends_of_long_scenes(self):
        """Checks very long scenes are shortened around an omission note."""
        ranges = [
            {"start": index * 10 + 1, "end": index * 10 + 10, "name": f"r{index}", "custom_data": {}}
            for index in range(10)
        ]
        lines = vlm.build_timeline({"range_data": ranges, "file_data": {}}, [], 10, 0.8, limit=4).splitlines()
        self.assertEqual(5, len(lines))
        self.assertTrue(lines[0].startswith("r0 "))
        self.assertIn("6 ranges omitted", lines[2])
        self.assertTrue(lines[-1].startswith("r9 "))

    def test_none_counts_as_unset_for_vlm_and_is_never_a_file_style(self):
        """Checks an existing 'none' can be filled, and settings never keep 'none' as the file style."""
        payload, images, settings = self._vlm_run_fixture()
        payload["file_data"]["style"] = "none"
        targets, _ = vlm._targets(
            payload, self.schema, None, [10, 30], True, allowed_fields=["style"], file_name="walk_01"
        )
        self.assertIn("file", targets)
        self.assertEqual("", model.normalize_settings({"file_style": "none", "file_style_source": "fixed"})["file_style"])

    def test_file_style_prompt_demands_an_answer_and_uses_the_file_name(self):
        """Checks the style request does not tell the model it may leave the field out."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["style"], file_style_source="vlm")
        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_scene_file_stem", return_value="combat_walk_01"):
                request = vlm.build_request(Mock(), settings, self.schema, payload, 1, 40, None)
        prompt = request["groups"][0]["prompt"]
        self.assertIn("always answer with your best choice", prompt)
        self.assertNotIn("Leaving a field out is always correct", prompt)
        self.assertIn("combat_walk_01", prompt)

    def test_file_context_can_use_pose_sheets_and_the_file_name(self):
        """Checks the context request carries a few images and the file name when enabled."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["context"], vlm_context_images=True)
        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_scene_file_stem", return_value="combat_walk_01"):
                request = vlm.build_request(Mock(), settings, self.schema, payload, 1, 40, None)
        group = request["groups"][-1]
        self.assertEqual(["file_context"], group["target_names"])
        self.assertTrue(group["images"])
        self.assertIn("'combat_walk_01'", group["prompt"])
        self.assertIn("pose sheets", group["prompt"])

    def _style_run(self, replies, **overrides):
        """Runs Auto-accept for the file style only and returns the sent requests and the final style."""
        payload, images, settings = self._vlm_run_fixture()
        settings.update(vlm_fields=["style"], file_style_source="vlm", vlm_threshold=0.85, **overrides)
        calls = []

        def fake_request(provider_settings, prompt, sent_images, timeout, **kwargs):
            calls.append((prompt, sent_images, kwargs))
            return replies[min(len(calls), len(replies)) - 1]

        with patch.object(vlm, "_capture_images", return_value=images):
            with patch.object(vlm, "_request", side_effect=fake_request):
                vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        return calls, payload["file_data"].get("style")

    def test_forced_style_accepts_a_low_confidence_answer_and_constrains_local_replies(self):
        """Checks a forced style ignores confidence and local servers get an enum schema."""
        low = [{"target": "file", "field": "style", "value": "relaxed", "confidence": 0.2}]
        calls, style = self._style_run([low], vlm_style_forced=True, vlm_style_recheck=False)
        self.assertEqual("relaxed", style)
        schema = calls[0][2]["response_schema"]
        self.assertEqual(["file"], schema["properties"]["suggestions"]["items"]["properties"]["target"]["enum"])
        self.assertIn("relaxed", schema["properties"]["suggestions"]["items"]["properties"]["value"]["enum"])
        self.assertNotIn("none", schema["properties"]["suggestions"]["items"]["properties"]["value"]["enum"])
        _, unforced = self._style_run([low], vlm_style_forced=False, vlm_style_recheck=False, vlm_style_threshold=0.5)
        self.assertIsNone(unforced)

    def test_uncertain_style_triggers_a_second_request_with_more_images(self):
        """Checks a low-confidence style is asked again with the timeline and the better answer wins."""
        weak = [{"target": "file", "field": "style", "value": "tense", "confidence": 0.4}]
        better = [{"target": "file", "field": "style", "value": "relaxed", "confidence": 0.9}]
        calls, style = self._style_run([weak, better], vlm_style_forced=True, vlm_style_recheck=True)
        recheck = next(call for call in calls if "Looking again" in call[0] or "first look" in call[0])
        self.assertIn("40%", recheck[0])
        self.assertIn("Timeline in order", recheck[0])
        self.assertEqual("relaxed", style)

    def test_confident_style_is_not_rechecked(self):
        """Checks a sure first answer costs no extra request."""
        sure = [{"target": "file", "field": "style", "value": "relaxed", "confidence": 0.95}]
        calls, style = self._style_run([sure], vlm_style_forced=True, vlm_style_recheck=True)
        self.assertEqual("relaxed", style)
        self.assertEqual(0, sum("first look" in call[0] for call in calls))

    def test_clear_ranges_keeps_locked_and_outside_frames(self):
        """Checks overwrite mode removes only unlocked ranges inside the analyzed frames."""
        ranges = [
            {"id": "a", "start": 1, "end": 100, "locked": False},
            {"id": "b", "start": 101, "end": 200, "locked": True},
            {"id": "c", "start": 201, "end": 300, "locked": False},
        ]
        expected = (
            [
                {"id": "a", "start": 1, "end": 49, "locked": False},
                {"id": "b", "start": 101, "end": 200, "locked": True},
                {"id": "c", "start": 251, "end": 300, "locked": False},
            ],
            2,
        )
        self.assertEqual(expected, model.clear_ranges(ranges, 50, 250))

    def test_vlm_file_target_includes_file_name(self):
        """Checks the scene name is offered as evidence for the file style."""
        payload = {"file_data": {}, "range_data": []}
        targets, _ = vlm._targets(payload, self.schema, None, [], False, file_name="combat_walk_01")
        self.assertEqual({"file_name": "combat_walk_01"}, targets["file"]["evidence"])

    def test_describe_profile_names_the_active_profile(self):
        """Checks the run summary tells built-in and custom profiles apart."""
        profile = {"name": "Vending", "poses": {"vending_machine": [{"sample_count": 3, "features": {}}]}}
        self.assertIn("Built-in", model.describe_profile(profile, False))
        self.assertIn("'Vending'", model.describe_profile(profile, True))

    def test_vlm_accepts_only_supported_empty_unlocked_fields(self):
        """Checks model output cannot replace manual values or locked data."""
        ranges = [
            {"start": 1, "end": 20, "locked": False, "custom_data": {"state": "walk", "override_style": "relaxed"}},
            {"start": 21, "end": 40, "locked": True, "custom_data": {}},
        ]
        payload = {"file_data": {}, "range_data": ranges}
        replies = [
            {"target": "file", "field": "style", "value": "tense", "confidence": 0.96},
            {"target": "range_1", "field": "override_style", "value": "tense", "confidence": 0.99},
            {"target": "range_1", "field": "stance", "value": "sit", "confidence": 0.95},
            {"target": "range_1", "field": "interaction_type", "value": "navigate", "confidence": 0.45},
            {"target": "range_2", "field": "stance", "value": "sit", "confidence": 0.99},
        ]
        settings = dict(model.DEFAULT_SETTINGS, vlm_mode="auto", vlm_local_auto_load=False)
        with patch.object(vlm, "_capture_images", return_value=[(10, "image/png", ""), (30, "image/png", "")]):
            with patch.object(vlm, "_request", return_value=replies):
                result = vlm.apply_vlm(Mock(), {}, settings, self.schema, payload, 1, 40, None)
        self.assertEqual(1, result["applied"])
        self.assertEqual(2, len(result["deferred"]))
        self.assertEqual({"style": "tense"}, payload["file_data"])
        self.assertEqual({"state": "walk", "override_style": "relaxed"}, ranges[0]["custom_data"])
        self.assertEqual({}, ranges[1]["custom_data"])

    def test_local_preflight_starts_server_and_loads_installed_vision_model(self):
        """Checks the CLI starts only when needed and loads the requested model."""
        from unittest.mock import call

        model_key = "test-vision"
        models = [{"key": model_key, "capabilities": {"vision": True}, "loaded_instances": []}]
        endpoint = "http://127.0.0.1:1234/v1/chat/completions"
        with patch.object(local, "_list_models", side_effect=[OSError("offline"), models]):
            with patch.object(local, "_run_lms") as command:
                local.prepare_local_model(endpoint, model_key, "", 90, Mock())
        self.assertEqual(
            [
                call(["server", "start", "--port", "1234", "--bind", "127.0.0.1"], 90),
                call(["load", model_key, "--identifier", model_key, "--yes"], 90),
            ],
            command.call_args_list,
        )
        models[0]["loaded_instances"] = [{"id": model_key}]
        with patch.object(local, "_list_models", return_value=models):
            with patch.object(local, "_run_lms") as command:
                local.prepare_local_model(endpoint, model_key, "", 90, Mock())
        command.assert_not_called()

    def test_local_response_explains_errors_and_unexpected_endpoint(self):
        """Checks server diagnostics replace the raw choices KeyError."""
        with self.assertRaisesRegex(ValueError, "Model not loaded"):
            vlm._response_text("local", {"error": {"message": "Model not loaded"}})
        with self.assertRaisesRegex(ValueError, "/v1/chat/completions"):
            vlm._response_text("local", {"data": []})

    def test_bionic_base_url_resolves_to_chat_completions(self):
        """Checks that the base URL shown by Bionic works as a preference."""
        base = "http://localhost:1234"
        for suffix in ("", "/", "/v1", "/v1/", "/api/v1", "/v1/chat/completions"):
            with self.subTest(suffix=suffix):
                options = dict(model.DEFAULT_SETTINGS, vlm_endpoint=f"{base}{suffix}")
                self.assertEqual(f"{base}/v1/chat/completions", vlm.get_provider_settings(options)[1])

    def test_local_picker_filters_for_vision_and_includes_loaded_aliases(self):
        """Checks discovery exposes usable IDs without trying to start or load anything."""
        models = [
            {"key": "vision", "display_name": "Vision Model", "capabilities": {"vision": True},
             "loaded_instances": [{"id": "vision_alias"}]},
            {"key": "text", "capabilities": {"vision": False}},
        ]
        with patch.object(local, "_list_models", return_value=models):
            result = local.discover_vision_models("http://localhost:1234/v1", "", Mock())
        self.assertEqual(
            [("vision_alias", "Vision Model", True), ("vision", "Vision Model", False)], result
        )

    def test_bionic_eject_only_unloads_other_idle_language_models(self):
        """Checks the selected model, embeddings, and busy models are kept."""
        selected = {"type": "llm", "loaded_instances": [{"id": "selected"}]}
        models = [
            selected,
            {"type": "llm", "loaded_instances": [{"id": "spare"}, {"id": "active"}, {"id": "queued"}]},
            {"type": "embedding", "loaded_instances": [{"id": "embedding"}]},
        ]
        statuses = [
            {"identifier": "selected", "type": "llm", "status": "idle"},
            {"identifier": "spare", "type": "llm", "status": "idle"},
            {"identifier": "active", "type": "llm", "status": "running"},
            {"identifier": "queued", "type": "llm", "status": "idle", "queued": 1},
            {"identifier": "embedding", "type": "embedding", "status": "idle"},
        ]
        endpoint = "http://localhost:1234/v1"
        with patch.object(local, "get_running_local_endpoint", return_value=endpoint):
            with patch.object(local, "_run_lms", side_effect=[json.dumps(statuses), ""]) as command:
                warnings = local._eject_other_idle_models(models, selected, endpoint, 90)
        self.assertEqual(
            ["Kept these Bionic models loaded because they were not idle local models: active, queued."], warnings
        )
        self.assertEqual([["ps", "--json"], ["unload", "spare"]], [entry.args[0] for entry in command.call_args_list])

    def test_preferences_reject_api_key_values_and_redact_provider_errors(self):
        """Checks a pasted credential cannot be saved even when VLM is off."""
        secret = "sk-example-secret"
        with patch.object(model, "_maya_preferences") as prefs:
            with self.assertRaisesRegex(ValueError, "environment variable name"):
                model.save_settings(dict(model.DEFAULT_SETTINGS, vlm_key_env=secret))
            with self.assertRaisesRegex(ValueError, "URL without credentials"):
                settings = dict(model.DEFAULT_SETTINGS, vlm_endpoint=f"https://example.invalid?api_key={secret}")
                model.save_settings(settings)
        prefs.assert_not_called()
        with self.assertRaises(ValueError) as error:
            vlm._response_text("openai", {"error": {"message": f"Invalid API key {secret}"}}, secret)
        self.assertIn("[redacted]", str(error.exception))
        self.assertNotIn(secret, str(error.exception))

    def test_batch_does_not_initialize_interactive_progress(self):
        """Checks batch calls do not create a dialog or query Maya UI state."""
        cmds = Mock()
        with vlm._progress_context(cmds, {"parent": object(), "control": object()}) as progress:
            self.assertIsNone(progress)
        cmds.about.assert_not_called()

    def test_metadata_switches_preserve_manual_values(self):
        """Checks metadata preferences fill only opted-in and empty fields."""
        fields = model.get_schema_fields(self.schema, "file_level")
        data = {"style": "relaxed"}
        options = dict(
            model.DEFAULT_SETTINGS, commercial_use=False, file_style_source="fixed",
            file_style="tense", auto_set_clipped=False,
        )
        with patch.object(scene, "has_valid_clips") as has_clips:
            auto_annotation._apply_file_data(Mock(), data, options, fields, [])
        has_clips.assert_not_called()
        self.assertEqual({"style": "relaxed", "commercial_use": False}, data)
        payload = {"file_data": {}, "range_data": []}
        targets, _ = vlm._targets(payload, self.schema, None, [], True, allow_file_style=False)
        self.assertNotIn("file", targets)
        self.assertEqual({"context"}, set(targets["file_context"]["fields"]))

    def test_quality_uses_registered_evaluator_and_selected_scope(self):
        """Checks quality evaluates only the resolved skeleton with preset settings."""
        from gt.core.motion_eval import evaluation, presets, sampling

        cmds = Mock()
        cmds.listRelatives.return_value = ["|Hips|LeftFoot", "|Hips|RightFoot"]
        mapping = {"pelvis": "|Hips", "left_foot": "|Hips|LeftFoot", "right_foot": "|Hips|RightFoot"}
        preset = presets.create_preset()
        preset["settings"]["overall_warn_below"] = 76
        expected = {"score": 81, "checks": [{"score": 81, "weight": 1}]}
        with patch.object(sampling, "sample_scene", return_value={"nodes": dict.fromkeys(mapping.values())}) as sample:
            with patch.object(evaluation, "evaluate_sample", return_value=expected) as evaluate:
                report = quality.evaluate_quality(cmds, mapping, (1, 60), preset)
        self.assertEqual(expected, report)
        self.assertEqual(list(mapping.values()), sample.call_args.kwargs["node_names"])
        self.assertEqual({"hips", "left_foot", "right_foot"}, set(evaluate.call_args.args[0]["roles"]))
        self.assertEqual(76, evaluate.call_args.kwargs["preset"]["settings"]["overall_warn_below"])
