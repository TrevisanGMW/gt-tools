"""Focused pure-Python regression tests for Kimodo batch task behavior."""

import json
import os
import tempfile
import unittest
import types
from unittest import mock
from gt.utils import kimodo
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tasks import task_kimodo_base as data
from gt.tools.batch_processor.tasks import task_kimodo_definition as definition_task
from gt.tools.batch_processor.tasks import task_kimodo_generate as generation
from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition
from gt.tools.batch_processor.tasks.task_kimodo_generate import TaskKimodoGenerate
from gt.tools.batch_processor.tasks.task_kimodo_base import write_record


class TestKimodoData(unittest.TestCase):
    """Tests timing, marker semantics, naming, and reproducible variations."""

    def test_marker_modes_and_endpoints(self):
        """Unions endpoints and explicit frames without duplicating held markers."""
        markers = [(1, True), (2, True), (3, False), (4, True), (5, True)]
        self.assertEqual([1, 2, 4, 5], definition_task.select_frames(1, 5, markers=markers))
        self.assertEqual([1, 4, 5], definition_task.select_frames(1, 5, markers=markers, mode="rising"))
        self.assertEqual([1, 3, 4, 5], definition_task.select_frames(1, 5, [3, 5], markers=markers, mode="rising"))

    def test_frame_parsing_and_bounds(self):
        """Parses fractional frames and rejects malformed or unbounded requests."""
        self.assertEqual([1, 2, 3, 4.5], kimodo.parse_scene_frames("1:3, 2, 4.5"))
        for expression in ("1:10:0", "nan", "5:1", "1:1000000"):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                kimodo.parse_scene_frames(expression)
        with self.assertRaises(ValueError):
            definition_task.select_frames(1, 10, [11])

    def test_example_timing_and_different_fps(self):
        """Preserves source timestamps and makes duration retiming explicit."""
        self.assertEqual(([0, 127, 352], 353), kimodo.map_constraint_frames([296, 423, 648], 296, 648, 30, 30))
        self.assertEqual(([0, 30], 31), kimodo.map_constraint_frames([101, 125], 101, 125, 24, 30))
        self.assertEqual(([0, 59], 60), kimodo.map_constraint_frames([101, 125], 101, 125, 24, 30, 60))
        with self.assertRaises(ValueError):
            kimodo.map_constraint_frames([1, 2], 1, 120, 120, 30)

    def test_bridge_duration_rounding(self):
        """Ensures bridge truncation yields exactly the requested sample count."""
        definition = kimodo.KimodoGenerationDefinition("Walk").as_dict()
        for count in range(2, 900):
            kimodo.set_definition_frame_count(definition, count, 30)
            self.assertEqual(count, int(definition["prompts"][0]["duration_seconds"] * 30))

    def test_setup_normalization(self):
        """Drops disabled authoring constraints and detaches the normalized definition."""
        definition = kimodo.KimodoGenerationDefinition("Walk").as_dict()
        constraint = {"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]}
        setup = {"definition": definition, "constraints": [
            {"enabled": True, "parameters": constraint}, {"enabled": False, "parameters": constraint}]}
        normalized = kimodo.normalize_definition(setup)
        self.assertEqual([constraint], normalized["constraints"])
        self.assertEqual([], definition["constraints"])

    def test_seed_variations_are_order_independent(self):
        """Derives choices from source identity, variation, and base seed."""
        task = TaskKimodoDefinition()
        task.settings.update(variation_ranges={"guidance_text": [1, 3]}, prompt_choices="Walk\nRun")
        definition = task.settings["definition"]
        first = definition_task.vary_definition(definition, task.settings, "folder/a.ma", 1)
        definition_task.vary_definition(definition, task.settings, "folder/b.ma", 1)
        repeated = definition_task.vary_definition(definition, task.settings, "folder/a.ma", 1)
        self.assertEqual(first["parameters"], repeated["parameters"])
        self.assertEqual(first["prompts"], repeated["prompts"])
        self.assertNotEqual(first["id"], repeated["id"])
        self.assertNotEqual(first["parameters"]["seed"],
                            definition_task.vary_definition(definition, task.settings, "folder/a.ma", 2)
                            ["parameters"]["seed"])

    def test_names_and_path_tokens(self):
        """Builds collision-safe names and rejects executable-looking field expressions."""
        self.assertEqual("walk", data.output_name("{source}", "walk"))
        self.assertEqual("walk_v002_s003", data.output_name("{source}", "walk", 2, sample=3, variations=2, samples=3))
        self.assertEqual("walk_002", data.output_name("{source}_{variation:03d}", "walk", 2, variations=2))
        self.assertEqual("_CON", data.output_name("{source}", "CON"))
        with self.assertRaises(ValueError):
            data.output_name("{source.__class__}", "walk")
        self.assertEqual("", data.resolve_path("", None))
        with self.assertRaises(ValueError):
            data.resolve_path("relative/path", None)

    def test_prompt_replacements_apply_per_variation_without_cascading(self):
        """Applies both walk/walking rules to every segment without consuming longer matches."""
        task = TaskKimodoDefinition(settings={"variations": 3, "prompt_replacements": [
            {"variation": 1, "search": "walk", "replace": "run"},
            {"variation": 1, "search": "walking", "replace": "running"},
            {"variation": 1, "search": "run", "replace": "sprint"},
            {"variation": 2, "search": "walk", "replace": "jog"},
            {"variation": 2, "search": "walking", "replace": "jogging"},
        ]})
        task.settings["definition"]["prompts"] = [
            {"text": "walk then walking", "duration_seconds": 4},
            {"text": "walking then walk", "duration_seconds": 4},
        ]
        for number, expected in ((1, ["run then running", "running then run"]),
                                 (2, ["jog then jogging", "jogging then jog"]),
                                 (3, ["walk then walking", "walking then walk"])):
            resolved = definition_task.vary_definition(task.base_definition(None), task.settings, "walk.ma", number)
            self.assertEqual(expected, [prompt["text"] for prompt in resolved["prompts"]])
        self.assertEqual("walk then walking", task.settings["definition"]["prompts"][0]["text"])
        restored = tasks.create_task_from_dict(task.to_dict())
        self.assertEqual(task.settings["prompt_replacements"], restored.settings["prompt_replacements"])

    def test_prompt_replacements_are_literal_and_follow_prompt_choices(self):
        """Uses literal case-sensitive matching after choosing the first prompt."""
        task = TaskKimodoDefinition(settings={"prompt_choices": "walk.* Walk", "prompt_replacements": [
            {"variation": 1, "search": "walk.*", "replace": "run\\1"},
            {"variation": 1, "search": " Walk", "replace": ""},
        ]})
        resolved = definition_task.vary_definition(task.base_definition(None), task.settings, "walk.ma", 1)
        self.assertEqual("run\\1", resolved["prompts"][0]["text"])

    def test_prompt_replacement_validation_checks_every_variation(self):
        """Rejects incomplete, out-of-range, and ambiguous rules before scene capture."""
        valid = {"variation": 2, "search": "walk", "replace": "run"}
        for rules in ([dict(valid, variation=3)], [dict(valid, variation=1.5)],
                      [dict(valid, search="")], [valid, valid], [dict(valid, replace=None)]):
            task = TaskKimodoDefinition(settings={"variations": 2, "prompt_replacements": rules})
            with self.subTest(rules=rules):
                self.assertTrue(any("[Variations]" in error for error in task.validate(None).errors))

    def test_task_serialization_and_registry(self):
        """Preserves nested settings through the production task registry."""
        for task in (TaskKimodoDefinition(), TaskKimodoGenerate()):
            restored = tasks.create_task_from_dict(task.to_dict())
            self.assertEqual(type(task), type(restored))
            self.assertEqual(task.settings, restored.settings)
            self.assertEqual([], restored.validate(None).errors)

    def test_default_name_migration_preserves_custom_names(self):
        """Migrates old built-in labels without changing task identity or user labels."""
        definition = TaskKimodoDefinition(display_name="Create Kimodo Definitions")
        generation_task = TaskKimodoGenerate(display_name="Generate Kimodo Animations")
        self.assertEqual("Kimodo Definition", definition.display_name)
        self.assertEqual("Kimodo Generate", generation_task.display_name)
        self.assertEqual("Custom", TaskKimodoDefinition(display_name="Custom").display_name)
        self.assertNotEqual(definition.icon, generation_task.icon)
        self.assertTrue(os.path.isfile(definition.icon))
        self.assertTrue(os.path.isfile(generation_task.icon))

    def test_shared_json_reader_retains_strict_errors(self):
        """Uses core I/O's strict mode so corrupted recovery files cannot silently reset a job."""
        from gt.core import io as core_io

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "invalid.json")
            core_io.write_data(path, "{")
            with self.assertRaises(ValueError):
                data.read_json(path)
            with self.assertRaises(FileNotFoundError):
                data.read_json(os.path.join(directory, "missing.json"))

    def test_capture_mapping_and_variants(self):
        """Builds portable path definitions using source timestamps and reproducible seeds."""
        task = TaskKimodoDefinition(settings={"variations": 2})
        captured = {"frames": [], "start": 296, "end": 648, "source_fps": 30, "poses": [],
                    "path_frames": [296, 423, 648], "path": {
                        "type": "root2d", "frame_indices": [0, 1, 2], "smooth_root_2d": [[0, 0], [0, 1], [0, 2]]}}
        definitions = task.build_definitions(captured, task.base_definition(None), "example.ma")
        self.assertEqual(2, len(definitions))
        self.assertEqual([0, 127, 352], definitions[0]["constraints"][0]["frame_indices"])
        self.assertEqual(353, int(definitions[0]["prompts"][0]["duration_seconds"] * 30))
        self.assertNotEqual(definitions[0]["parameters"]["seed"], definitions[1]["parameters"]["seed"])

    def test_path_mask_keeps_active_frames(self):
        """Drops root path frames where the mask is zero and rejects masks that leave too few."""
        expected = [1, 5, 9]
        self.assertEqual(expected, definition_task.mask_path_frames([1, 3, 5, 7, 9], [1, 0, 1.0, 0.0, 1]))
        with self.assertRaises(ValueError):
            definition_task.mask_path_frames([1, 3, 5], [1, 0, 0])
        with self.assertRaises(ValueError):
            definition_task.mask_path_frames([1, 3], [1])

    def test_dense_capture_packs_pose_samples(self):
        """Keeps dense marker runs within the bridge's constraint-object limit."""
        task = TaskKimodoDefinition()
        pose = {"type": "fullbody", "frame_indices": [0], "root_positions": [[0, 0, 0]],
                "local_joints_rot": [[[0, 0, 0] for unused_joint in range(22)]]}
        captured = {"frames": list(range(300)), "start": 0, "end": 299, "source_fps": 30,
                    "poses": [pose for unused_frame in range(300)], "path": None, "path_frames": []}
        definitions = task.build_definitions(captured, task.base_definition(None), "dense.ma")
        self.assertEqual(1, len(definitions[0]["constraints"]))
        self.assertEqual(list(range(300)), definitions[0]["constraints"][0]["frame_indices"])

    def test_dense_hips_capture_keeps_end_effector_joint_names(self):
        """Packs hips-only poses as one end-effector constraint with a single joint list."""
        task = TaskKimodoDefinition(settings={"pose_type": "hips"})
        pose = {"type": "end-effector", "joint_names": ["Hips"], "frame_indices": [0],
                "root_positions": [[0, 0.55, 0]], "local_joints_rot": [[[0, 0, 0] for unused_joint in range(22)]]}
        captured = {"frames": list(range(300)), "start": 0, "end": 299, "source_fps": 30,
                    "poses": [pose for unused_frame in range(300)], "path": None, "path_frames": []}
        constraint = task.build_definitions(captured, task.base_definition(None), "dense.ma")[0]["constraints"][0]
        self.assertEqual("end-effector", constraint["type"])
        self.assertEqual(["Hips"], constraint["joint_names"])
        self.assertEqual(300, len(constraint["root_positions"]))

    def test_packaged_presets_load(self):
        """Loads Kimodo presets through the real project serializer and template loader."""
        from gt.tools.batch_processor import batch_processor_model

        folder = os.path.join(os.path.dirname(tasks.__file__), "templates", "package_templates")
        names = ["Kimodo Animations.batch", "Kimodo From Strings.batch"]
        self.assertEqual(names, sorted(name for name in os.listdir(folder) if name.startswith("Kimodo")))
        for name in names:
            project = batch_processor_model.BatchProcessorModel()
            project.load_from_file(os.path.join(folder, name))
            self.assertEqual("kimodo_generate", project.tasks[-1].task_type)
            self.assertEqual(True, project.tasks[-1].settings["add_humanik"])
            self.assertEqual("{project-file-dir}", project.environment_variables["project-dir"])
        from gt.tools.batch_processor import batch_processor_templates

        loaders = {}
        batch_processor_templates.BatchProcessorTemplates.populate_with_template_files(folder, loaders)
        for name in ("Kimodo_Animations", "Kimodo_From_Strings"):
            project = loaders[name]()
            self.assertEqual("{project-file-dir}", project.environment_variables["project-dir"])
            self.assertIsNone(project.project_file_path)
            with tempfile.TemporaryDirectory() as directory:
                project.project_file_path = os.path.join(directory, "example.batch")
                self.assertEqual(os.path.normcase(directory), os.path.normcase(project.get_project_dir()))

    def test_saved_playback_range_without_semicolon(self):
        """Reads saved timeline data without executing the scene's script node."""
        from gt.tools.batch_processor.tasks import task_kimodo_definition

        commands = mock.Mock()
        commands.ls.return_value = ["sceneConfigurationScriptNode"]
        commands.getAttr.return_value = "playbackOptions -min 296 -max 648 -ast 1 -aet 800 "
        maya = types.ModuleType("maya")
        maya.cmds = commands
        with mock.patch.dict("sys.modules", {"maya": maya, "maya.cmds": commands}):
            self.assertEqual((296, 648), task_kimodo_definition.scene_range({"range_mode": "playback"}))
            self.assertEqual((1, 800), task_kimodo_definition.scene_range({"range_mode": "animation"}))
        commands.playbackOptions.assert_not_called()


class TestKimodoGeneration(unittest.TestCase):
    """Exercises restart, publication, and retry behavior without a GPU or Maya."""

    def setUp(self):
        """Creates an isolated definition and mock bridge."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = self.temporary.name
        self.source = os.path.join(self.root, "input", "walk.json")
        self.definition = kimodo.KimodoGenerationDefinition("Walk", num_samples=2).as_dict()
        write_record(self.source, self.definition)
        self.item = tasks.WorkItem(self.source)
        self.output = os.path.join(self.root, "output")
        self.task = TaskKimodoGenerate()
        self.client = mock.Mock()
        self.client.connection.url = kimodo.DEFAULT_URL
        self.client.capabilities.return_value = {"models": [{"id": kimodo.DEFAULT_MODEL, "fps": 30}]}
        self.result = {"status": "succeeded", "resolved": {"fps": 30, "samples": ["motion.json", "sample_1.json"]}}
        self.client.status.return_value = self.result
        self.paths = {"motion.json": "motion.json", "sample_1.json": "sample_1.json"}
        self.client.download.return_value = self.paths

    def save_scene(self, motion, path, settings, cache):
        """Writes a stand-in output used to verify publication and restart decisions.

        Args:
            motion (str): Mock source motion.
            path (str): Output file.
            settings (dict): Task settings.
            cache (str): Recovery folder.
        """
        write_record(path, {"motion": motion})

    def test_definition_attributes_carry_resolved_and_batch_definitions(self):
        """Passes the resolved definition and unresolved batch settings to every published scene."""
        captured = []

        def capture_settings(motion, path, settings, cache):
            """Records the publish settings before writing a stand-in scene.

            Args:
                motion (str): Mock source motion.
                path (str): Output file.
                settings (dict): Task settings.
                cache (str): Recovery folder.
            """
            captured.append(settings.get("definition_attributes"))
            self.save_scene(motion, path, settings, cache)

        self.assertEqual(True, self.task.settings["include_definition_attribute"])
        definition_task = TaskKimodoDefinition(settings={"prompt_text": "{input-string}"})
        project = types.SimpleNamespace(tasks=[definition_task, self.task], project_name="Cards",
                                        project_file_path="", get_custom_environment_variables=dict)
        self.item.metadata.update(last_task_id=definition_task.id, input_string="[[2, \"Walk\"]]",
                                  input_file="walk")
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene", side_effect=capture_settings), \
                mock.patch.object(self.task, "resolved_settings", return_value=dict(self.task.settings)):
            self.task.execute(self.item, project, self.output)
        self.assertEqual(2, len(captured))
        resolved = json.loads(captured[0][generation.DEFINITION_ATTRIBUTE])
        batch = json.loads(captured[0][generation.BATCH_DEFINITION_ATTRIBUTE])
        self.assertEqual("Walk", resolved["prompts"][0]["text"])
        self.assertIsInstance(resolved["parameters"]["seed"], int)
        self.assertEqual("{input-string}", batch["definition_task"]["parameters"]["prompt_text"])
        self.assertEqual("walk", batch["input"]["input_file"])
        self.assertEqual(self.task.id, batch["generate_task"]["id"])

    def test_definition_attributes_can_be_disabled(self):
        """Publishes scenes without definition attributes when the option is off."""
        captured = []
        self.task.settings["include_definition_attribute"] = False
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene",
                                  side_effect=lambda motion, path, settings, cache: captured.append(
                                      settings.get("definition_attributes"))):
            self.task.execute(self.item, None, self.output)
        self.assertEqual([None, None], captured)

    def test_multiple_samples_and_existing_outputs(self):
        """Publishes every sample and skips completed outputs before connecting."""
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene", side_effect=self.save_scene):
            result = self.task.execute(self.item, None, self.output)
        self.assertEqual(["walk_s001.ma", "walk_s002.ma"], [os.path.basename(item.current_path) for item in result])
        self.assertEqual(["walk_s001.ma", "walk_s002.ma"], sorted(os.listdir(self.output)))
        with mock.patch.object(generation, "connect") as connect, self.assertRaises(tasks.TaskSkip) as skipped:
            self.task.execute(self.item, None, self.output)
        connect.assert_not_called()
        self.assertEqual(2, len(skipped.exception.work_item))
        self.assertEqual(["walk_s001.ma", "walk_s002.ma"], sorted(os.listdir(self.output)))

    def test_import_incoming_scene_uses_captured_provenance_for_every_sample(self):
        """Passes the captured scene into each output without mutating stored task settings."""
        self.assertFalse(self.task.settings["import_incoming_scene"])
        scene = os.path.join(self.root, "captured.ma")
        write_record(scene, {"source": True})
        original_scene = os.path.join(self.root, "original.ma")
        self.item.source_path = original_scene
        self.item.metadata["kimodo"] = {"source_scene": scene}
        self.task.settings["import_incoming_scene"] = True
        self.assertEqual([], self.task.validate_work_items([self.item], None, self.output).errors)
        with mock.patch.object(generation, "connect", return_value=self.client), mock.patch.object(
            generation, "publish_scene", side_effect=self.save_scene
        ) as save:
            self.task.execute(self.item, None, self.output)
        self.assertEqual(2, save.call_count)
        self.assertEqual([scene, scene], [call.args[2]["incoming_scene_path"] for call in save.call_args_list])
        self.assertNotIn("incoming_scene_path", self.task.settings)

    def test_import_incoming_scene_rejects_missing_source_before_contacting_bridge(self):
        """Reports missing scene provenance before submitting a costly generation job."""
        self.task.settings["import_incoming_scene"] = True
        self.assertTrue(self.task.validate_work_items([self.item], None, self.output).errors)
        with mock.patch.object(generation, "connect") as connect, self.assertRaisesRegex(
            ValueError, "requires a Maya scene"
        ):
            self.task.execute(self.item, None, self.output)
        connect.assert_not_called()
        self.task.settings["result_mode"] = "artifacts"
        self.assertEqual([], self.task.validate_work_items([self.item], None, self.output).errors)

    def test_virtual_string_definitions_have_no_scene_to_import(self):
        """Accepts Input Strings provenance without trying to import its nonexistent scene."""
        self.item.source_path = os.path.join(self.root, "virtual.ma")
        self.item.metadata["input_string_path"] = self.item.source_path
        self.task.settings["import_incoming_scene"] = True
        self.assertEqual("", generation.incoming_scene_path(self.item))

    def test_cleanup_options_are_independent(self):
        """Keeps requested diagnostics while purging the other kind of temporary data."""
        self.task.settings["purge_coordination_on_finish"] = False
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene", side_effect=self.save_scene):
            self.task.execute(self.item, None, self.output)
        self.assertTrue(os.path.isdir(os.path.join(self.output, ".kimodo-coordination")))
        self.assertFalse(os.path.exists(os.path.join(self.output, ".kimodo-cache")))
        self.task.settings.update(purge_coordination_on_finish=True, purge_cache_on_success=False)
        with self.assertRaises(tasks.TaskSkip):
            self.task.execute(self.item, None, self.output)
        self.assertFalse(os.path.exists(os.path.join(self.output, ".kimodo-coordination")))
        self.assertTrue(os.path.isfile(os.path.join(self.task.recovery_directory(self.item, self.output),
                                                    "generation.json")))

    def test_partial_publication_resumes_same_remote_job(self):
        """Keeps sample one and reuses the job when sample two fails to save."""
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene", side_effect=[None, RuntimeError("save failed")]), \
                self.assertRaises(RuntimeError):
            self.task.execute(self.item, None, self.output)
        job_id = self.client.submit.call_args.kwargs["job_id"]
        write_record(os.path.join(self.output, "walk_s001.ma"), {"saved": True})
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene", side_effect=self.save_scene) as save:
            self.task.execute(self.item, None, self.output)
        self.assertEqual(job_id, self.client.submit.call_args.kwargs["job_id"])
        self.assertEqual(1, save.call_count)

    def test_submission_retry_keeps_job_id(self):
        """Retries a lost submission response without requesting duplicate GPU work."""
        self.client.submit.side_effect = [ConnectionError("lost response"), {}]
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene", side_effect=self.save_scene), \
                mock.patch.object(generation.time, "sleep"):
            self.task.execute(self.item, None, self.output)
        self.assertEqual(self.client.submit.call_args_list[0].kwargs["job_id"],
                         self.client.submit.call_args_list[1].kwargs["job_id"])

    def test_rate_mismatch_does_not_submit(self):
        """Rejects model timing mismatch before generation."""
        self.client.capabilities.return_value["models"][0]["fps"] = 60
        with mock.patch.object(generation, "connect", return_value=self.client), self.assertRaises(ValueError):
            self.task.execute(self.item, None, self.output)
        self.client.submit.assert_not_called()

    def test_output_ownership_rejects_other_source(self):
        """Blocks two source files from reserving the same published name."""
        path = os.path.join(self.output, "same.ma")
        self.task.reserve_outputs(self.item, [path], self.output)
        self.task.reserve_outputs(self.item, [path], self.output)
        with self.assertRaises(ValueError):
            self.task.reserve_outputs(tasks.WorkItem(os.path.join(self.root, "other.json")), [path], self.output)

    def test_artifacts_only_preserves_all_files(self):
        """Returns a manifest work item and reuses a verified bundle without importing Maya."""
        self.task.settings["result_mode"] = "artifacts"
        record_directory = self.task.recovery_directory(self.item, self.output)
        cache_artifacts = os.path.join(self.root, "mock_artifacts")
        paths = {}
        for name in ("motion.json", "sample_1.json", "definition.json", "motion.npz", "result.json"):
            path = os.path.join(cache_artifacts, name)
            write_record(path, {"placeholder": True})
            paths[name] = path

        def download(unused_job_id, unused_directory, reuse_existing):
            """Builds a result manifest with the submitted request ID.

            Args:
                unused_job_id (str): Submitted job ID.
                unused_directory (str): Download target.
                reuse_existing (bool): Requested reuse flag.

            Returns:
                dict: Mock artifact paths.
            """
            record = data.read_json(os.path.join(record_directory, "generation.json"))
            write_record(paths["result.json"], {"job_id": record["job_id"], "artifacts": [
                {"name": name, "sha256": kimodo.artifact_digest(path)}
                for name, path in paths.items() if name != "result.json"]})
            return paths

        self.client.download.side_effect = download
        with mock.patch.object(generation, "connect", return_value=self.client), \
                mock.patch.object(generation, "publish_scene") as publish:
            output = self.task.execute(self.item, None, self.output)
            with self.assertRaises(tasks.TaskSkip) as skipped:
                self.task.execute(self.item, None, self.output)
            repeated = skipped.exception.work_item
        publish.assert_not_called()
        self.assertEqual(1, len(output))
        self.assertEqual(output[0].current_path, repeated[0].current_path)
        self.assertEqual(sorted(paths), sorted(os.listdir(os.path.dirname(output[0].current_path))))

    def test_cancel_context_targets_only_owned_job(self):
        """Cancels the registered job when a cooperative worker predicate is set."""
        with self.assertRaises(RuntimeError):
            generation.check_cancel(self.client, "owned_job", {"cancel_requested": lambda: True})
        self.client.cancel.assert_called_once_with("owned_job")

    def test_tracker_cancellation_uses_registered_job(self):
        """Connects tracker cancellation to the correct bridge ID and environment token."""
        from gt.tools.batch_processor.tracker import tracker_scheduler

        process = {"remote_jobs": [{"url": kimodo.DEFAULT_URL, "remote_id": "owned_job",
                                     "token_environment": "GT_TEST_KIMODO_TOKEN"}]}
        scheduler = object.__new__(tracker_scheduler.TrackerScheduler)
        with mock.patch.dict(os.environ, {"GT_TEST_KIMODO_TOKEN": "test-token"}), \
                mock.patch.object(kimodo, "KimodoClient", return_value=self.client) as client:
            scheduler._cancel_remote_jobs(process)
        self.assertEqual("test-token", client.call_args.args[0].token)
        self.client.cancel.assert_called_once_with("owned_job")

    def test_timeout_does_not_cancel_unless_enabled(self):
        """Distinguishes a local wait timeout from remote cancellation."""
        self.client.status.return_value = {"status": "queued", "stage": "queued"}
        record = {"job_id": "a" * 32}
        path = os.path.join(self.root, "record.json")
        settings = self.task.settings
        settings["queue_timeout"] = 1
        with mock.patch.object(generation.time, "monotonic", side_effect=[0, 2]), self.assertRaises(TimeoutError):
            generation.wait_for_job(self.client, self.definition, record, path, settings, {})
        self.client.cancel.assert_not_called()
        settings["cancel_on_timeout"] = True
        with mock.patch.object(generation.time, "monotonic", side_effect=[0, 2]), self.assertRaises(TimeoutError):
            generation.wait_for_job(self.client, self.definition, record, path, settings, {})
        self.client.cancel.assert_called_once_with("a" * 32)


class TestKimodoPathLengths(unittest.TestCase):
    """Keeps owned cache and claim paths short, compatible with older layouts, and checked early."""

    def setUp(self):
        """Creates an isolated definition input and output folder."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = temporary.name
        self.source = os.path.join(self.root, "input", "walk.json")
        write_record(self.source, kimodo.KimodoGenerationDefinition("Walk").as_dict())
        self.item = tasks.WorkItem(self.source)
        self.output = os.path.join(self.root, "output")
        self.task = TaskKimodoGenerate(settings={"target_path": self.output})

    def test_recovery_folder_is_short_and_reuses_legacy_folder(self):
        """Uses a 12-character identity, but resumes from an existing 24-character folder."""
        cache = self.task.recovery_directory(self.item, self.output)
        identity = os.path.basename(cache)
        self.assertEqual(data.RECOVERY_IDENTITY_LENGTH, len(identity))
        legacy_identity = data.fingerprint([self.task.id, os.path.normcase(os.path.abspath(self.source))])[:24]
        legacy = os.path.join(os.path.dirname(cache), legacy_identity)
        os.makedirs(legacy)
        self.assertEqual(legacy, self.task.recovery_directory(self.item, self.output))
        os.makedirs(cache)
        self.assertEqual(cache, self.task.recovery_directory(self.item, self.output))

    def test_download_folders_are_short_and_unused(self):
        """Names download folders dl_<8 hex> and never returns an existing folder."""
        directory = generation.new_download_directory(self.root)
        self.assertRegex(os.path.basename(directory), r"^dl_[0-9a-f]{8}$")
        self.assertFalse(os.path.exists(directory))

    def test_claims_are_short_and_respect_legacy_claims(self):
        """Writes 32-character claim keys and still honors full-digest claims from older versions."""
        path = os.path.join(self.output, "walk.ma")
        outputs = os.path.join(self.output, ".kimodo-coordination", "outputs")
        self.task.reserve_outputs(self.item, [path], self.output)
        self.assertEqual([32], [len(os.path.splitext(name)[0]) for name in os.listdir(outputs)
                                if name.endswith(".json")])
        other = os.path.join(self.output, "other.ma")
        key = data.fingerprint(os.path.normcase(os.path.abspath(other)))
        write_record(os.path.join(outputs, f"{key}.json"), {"source": "someone_else", "output": other})
        with self.assertRaises(ValueError):
            self.task.reserve_outputs(self.item, [other], self.output)
        self.assertTrue(data.purge_coordination(self.output))

    def test_deep_targets_fail_validation_without_long_path_support(self):
        """Reports the needed path length before any generation when the limit would be exceeded."""
        deep = os.path.join(self.root, *["deep_folder_name_for_testing"] * 8)
        with mock.patch.object(data, "long_paths_supported", return_value=False):
            result = self.task.validate_work_items([self.item], None, self.output)
            self.assertEqual([], [error for error in result.errors if "Windows limit" in error])
            result = self.task.validate_work_items([self.item], None, deep)
            self.assertEqual(1, len([error for error in result.errors if "Windows limit" in error]))
        with mock.patch.object(data, "long_paths_supported", return_value=True):
            result = self.task.validate_work_items([self.item], None, deep)
            self.assertEqual([], [error for error in result.errors if "Windows limit" in error])

    def test_path_estimate_covers_cache_files(self):
        """Includes the deepest download file below the recovery folder."""
        path = self.task.output_path(self.item, self.output)
        cache = self.task.recovery_directory(self.item, self.output)
        deepest = os.path.join(cache, "dl_00000000", "0" * 32, "result.json.00000000.tmp")
        self.assertGreaterEqual(max(self.task.owned_path_lengths(self.item, self.output, path)), len(deepest))


if __name__ == "__main__":
    unittest.main()
