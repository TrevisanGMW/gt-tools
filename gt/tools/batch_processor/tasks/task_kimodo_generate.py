"""Generates characterized Maya animations from portable Kimodo definitions."""

import copy
import os
import re
import uuid
import shutil
import tempfile
import time
from gt.utils import kimodo
from gt.ui import resource_library as resources
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor.tasks.task_kimodo_base import (
    TaskKimodoBase, ClipSnapshotFileLock, report_message, write_record, read_json, fingerprint, resolve_path,
)
from gt.tools.kimodo_generator import kimodo_generator_hik as humanik


class TaskKimodoGenerate(TaskKimodoBase):
    """Runs resumable bridge jobs and emits one Maya work item per generated sample."""

    task_type = constants.TaskType.KIMODO_GENERATE
    default_display_name = "Kimodo Generate"
    icon = resources.Icon.batch_task_kimodo_generate
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_kimodo_animations"
    extensions = (".json",)

    def get_default_settings(self):
        """Returns connection, output, and characterization defaults.

        Returns:
            dict: Serializable generation task settings, excluding credentials.
        """
        settings = super().get_default_settings()
        settings.update(
            connection={"url": kimodo.DEFAULT_URL, "mode": "existing", "python_path": "",
                        "distribution": "", "device": "auto", "text_encoder_url": "http://127.0.0.1:9550",
                        "start_encoder": True, "timeout": 10},
            token_environment="", startup_timeout=180, queue_timeout=7200, generation_timeout=1200,
            poll_interval=1, network_retries=5, cancel_on_timeout=False, retry_failed=False,
            result_mode="maya", output_extension=".ma", namespace="kimodo", import_start_frame=1,
            add_humanik=True, humanik=humanik.default_settings(), expected_model_fps=30,
        )
        return settings

    def resolved_settings(self, project):
        """Resolves optional local profile paths without modifying serialized task data.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            dict: Runtime settings.
        """
        settings = copy.deepcopy(self.settings)
        if settings["result_mode"] == "artifacts" or not settings["add_humanik"]:
            return settings
        for key in ("definition_path", "tpose_path"):
            settings["humanik"][key] = resolve_path(settings["humanik"].get(key), project, self)
        return settings

    def validate(self, project):
        """Validates output, bridge, and HumanIK settings without submitting work.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Collected diagnostics.
        """
        result = super().validate(project)
        area = "Connection"
        try:
            settings = self.settings
            kimodo.KimodoConnection(**settings["connection"])

            area = "Results"
            if settings["result_mode"] not in ("maya", "maya_and_artifacts", "artifacts"):
                raise ValueError("Unknown result mode.")
            if settings["output_extension"] not in (".ma", ".mb"):
                raise ValueError("Maya output extension must be .ma or .mb.")
            kimodo._positive_number(float(settings["expected_model_fps"]), "expected_model_fps")
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", settings["namespace"]):
                raise ValueError("Use a simple Maya namespace containing letters, numbers, and underscores.")

            area = "Recovery and Timeouts"
            for key in ("startup_timeout", "queue_timeout", "generation_timeout", "poll_interval"):
                kimodo._positive_number(float(settings[key]), key)
            if not 0 <= int(settings["network_retries"]) <= 100:
                raise ValueError("Network retries must be from 0 through 100.")
            if not isinstance(settings.get("purge_cache_on_success", True), bool):
                raise ValueError("Purge cache after success must be enabled or disabled.")

            area = "HumanIK"
            if settings["add_humanik"] and settings["result_mode"] != "artifacts":
                humanik_settings = self.resolved_settings(project)["humanik"]
                humanik.validate_settings(humanik_settings, check_files=True)
        except (ValueError, TypeError, KeyError, OSError) as error:
            self.add_area_error(result, area, error)
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Generates or resumes an item, retaining successful files after partial failures.

        Args:
            work_item (WorkItem): Definition input.
            project (BatchProcessorModel): Owning project.
            step_output_dir (str): Target root.
            context (dict, optional): Tracker context.

        Returns:
            list: Maya outputs, or one artifact-manifest work item.
        """
        self.check_source(work_item)
        errors = self.validate(project).errors
        if errors:
            raise ValueError("; ".join(errors))
        settings = self.resolved_settings(project)
        definition = kimodo.normalize_definition(read_json(work_item.current_path))
        cache = self.recovery_directory(work_item, step_output_dir)
        record_path = os.path.join(cache, "generation.json")
        with self.recovery_lock(work_item, step_output_dir, timeout_seconds=86400, context=context):
            try:
                with ClipSnapshotFileLock(record_path, timeout_seconds=86400):
                    items = self.run_generation(work_item, step_output_dir, context or {}, settings,
                                                definition, cache, record_path)
            except base.TaskSkip:
                self.cleanup_recovery_cache(work_item, step_output_dir, cache, context)
                raise
            self.cleanup_recovery_cache(work_item, step_output_dir, cache, context)
            return items

    def run_generation(self, item, directory, context, settings, definition, cache, record_path):
        """Runs one generation under an exclusive per-input recovery lock.

        Args:
            item (WorkItem): Input definition item.
            directory (str): Output root.
            context (dict): Tracker context.
            settings (dict): Runtime settings.
            definition (dict): Validated input definition.
            cache (str): Owned cache directory.
            record_path (str): Recovery record.

        Returns:
            list: Output work items.
        """
        signature = fingerprint([definition, settings["connection"]["url"]])
        record = read_json(record_path) if os.path.isfile(record_path) else {}
        if record.get("signature") != signature:
            record = {"signature": signature, "job_id": uuid.uuid4().hex, "source": item.current_path,
                      "definition": copy.deepcopy(definition), "outputs": {}}
            if record["definition"]["parameters"]["seed"] is None:
                import secrets
                record["definition"]["parameters"]["seed"] = secrets.randbits(32)
            write_record(record_path, record)
        definition = record["definition"]
        count = definition["parameters"]["num_samples"]
        paths = [self.output_path(item, directory, seed=definition["parameters"]["seed"],
                                  sample=index, samples=count, definition=definition)
                 for index in range(1, count + 1)]
        bundle = os.path.splitext(self.output_path(
            item, directory, seed=definition["parameters"]["seed"], definition=definition))[0]
        planned = paths if settings["result_mode"] != "artifacts" else []
        if settings["result_mode"] != "maya":
            planned = planned + [f"{bundle}_artifacts"]
        self.reserve_outputs(item, planned, directory)
        metadata = {"job_id": record["job_id"], "definition": item.current_path,
                    "seed": definition["parameters"]["seed"]}
        if not settings.get("purge_cache_on_success", True):
            metadata["manifest"] = record_path
        if not settings["overwrite"]:
            scenes_ready = settings["result_mode"] == "artifacts" or all(
                os.path.isfile(path) and os.path.getsize(path) for path in paths)
            artifact_manifest = record.get("artifact_manifest")
            artifact_job_id = record["job_id"]
            if settings["result_mode"] != "maya" and not artifact_manifest:
                artifact_manifest, artifact_job_id = find_published_bundle(f"{bundle}_artifacts")
            bundle_ready = settings["result_mode"] == "maya" or verify_bundle(
                artifact_manifest, artifact_job_id)
            if scenes_ready and bundle_ready:
                if artifact_manifest:
                    metadata["job_id"] = artifact_job_id
                    metadata["artifacts"] = artifact_manifest
                outputs = ([self.output_item(item, artifact_manifest, metadata)]
                           if settings["result_mode"] == "artifacts" else [
                               self.output_item(item, path, dict(metadata, sample=index))
                               for index, path in enumerate(paths, 1)])
                raise base.TaskSkip("All Kimodo outputs already exist.", work_item=outputs)
        client = connect(settings, context)
        models = {model["id"]: model for model in client.capabilities()["models"]}
        if definition["model"] not in models:
            raise ValueError(f"Model unavailable on bridge: {definition['model']}")
        expected_fps = item.metadata.get("kimodo", {}).get("model_fps", settings["expected_model_fps"])
        actual_fps = models[definition["model"]].get("fps")
        if actual_fps is not None and float(actual_fps) != float(expected_fps):
            raise ValueError(f"Definition timing expects {expected_fps} fps; model uses {actual_fps} fps.")
        if settings["retry_failed"] and record.get("status") in ("failed", "cancelled"):
            record.update(job_id=uuid.uuid4().hex, status="pending", outputs={})
            record.pop("downloads", None)
            write_record(record_path, record)
        result = wait_for_job(client, definition, record, record_path, settings, context)
        resolved = result.get("resolved", {})
        if float(resolved.get("fps", expected_fps)) != float(expected_fps):
            raise ValueError("Generated sample rate differs from definition timing; outputs were not published.")
        artifacts = download_results(client, record, record_path, cache)
        samples = resolved.get("samples") or ["motion.json"]
        if len(samples) != count or any(name not in artifacts for name in samples):
            raise ValueError("Bridge returned an unexpected sample list.")
        metadata["job_id"] = record["job_id"]
        items = []
        if settings["result_mode"] != "artifacts":
            for index, (sample_name, path) in enumerate(zip(samples, paths), 1):
                check_cancel(client, record["job_id"], context)
                if os.path.exists(path) and not settings["overwrite"]:
                    if not os.path.isfile(path) or not os.path.getsize(path):
                        raise ValueError(f"Existing output is empty or invalid: {path}")
                    report_message(context, f"Skipped existing Maya scene: {path}")
                else:
                    publish_scene(artifacts[sample_name], path, settings, cache)
                    report_message(context, f"Saved Maya scene: {path}")
                record["outputs"][sample_name] = path
                write_record(record_path, record)
                items.append(self.output_item(item, path, dict(metadata, sample=index)))
        if settings["result_mode"] != "maya":
            manifest = publish_artifacts(artifacts, f"{bundle}_artifacts", record["job_id"])
            record["artifact_manifest"] = manifest
            metadata["artifacts"] = manifest
            for output_item in items:
                output_item.metadata["kimodo"]["artifacts"] = manifest
            if settings["result_mode"] == "artifacts":
                items.append(self.output_item(item, manifest, metadata))
        record["status"] = "published"
        write_record(record_path, record)
        return items


def connect(settings, context=None):
    """Connects to a bridge, serializing optional local startup across worker processes.

    Args:
        settings (dict): Connection options and token environment variable name.
        context (dict, optional): Tracker context.

    Returns:
        KimodoClient: Healthy bridge client.
    """
    token_name = settings.get("token_environment", "")
    token = os.environ.get(token_name) if token_name else None
    if token_name and not token:
        raise ValueError(f"Bridge token environment variable is unset: {token_name}")
    connection = kimodo.KimodoConnection(token=token, **settings["connection"])
    client = kimodo.KimodoClient(connection)
    if connection.mode == "existing":
        client.health()
    else:
        lock_path = os.path.join(tempfile.gettempdir(), f"gt_kimodo_start_{fingerprint(connection.url)[:24]}")
        with ClipSnapshotFileLock(lock_path, timeout_seconds=float(settings["startup_timeout"]) + 30):
            try:
                client.health()
            except ConnectionError:
                report_message(context, "Starting the configured local bridge.")
                connection.start_local(startup_timeout=float(settings["startup_timeout"]))
            client.health()
    return client


def check_cancel(client, job_id, context):
    """Cooperatively cancels only this task's remote job when the worker requests it.

    Args:
        client (KimodoClient): Originating server client.
        job_id (str): Owned job identifier.
        context (dict): Runtime context with an optional cancellation predicate.
    """
    predicate = (context or {}).get("cancel_requested")
    if callable(predicate) and predicate():
        client.cancel(job_id)
        raise RuntimeError(f"Kimodo job canceled by batch request: {job_id}")


def wait_for_job(client, definition, record, record_path, settings, context):
    """Submits idempotently and polls progress with separate queue and generation limits.

    Args:
        client (KimodoClient): Healthy bridge client.
        definition (dict): Fully resolved generation definition.
        record (dict): Mutable recovery record.
        record_path (str): Recovery file.
        settings (dict): Timeouts and retry controls.
        context (dict): Tracker context.

    Returns:
        dict: Successful server result.
    """
    job_id = record["job_id"]
    register = (context or {}).get("register_remote_job")
    if callable(register):
        register(client.connection.url, job_id, settings.get("token_environment", ""))
    deadline = time.monotonic() + float(settings["queue_timeout"])
    retries = int(settings["network_retries"])
    attempt = 0
    while True:
        check_cancel(client, job_id, context)
        try:
            client.submit(kimodo.KimodoGenerationDefinition.from_dict(definition), job_id=job_id)
            break
        except (ConnectionError, RuntimeError) as error:
            queue_full = "queue is full" in str(error)
            transient = isinstance(error, ConnectionError) or queue_full
            if not transient or (not queue_full and attempt >= retries) or time.monotonic() >= deadline:
                raise
            attempt += 1
            report_message(context, f"{'Queue full' if queue_full else 'Submission retry'}: {job_id}")
            time.sleep(min(2 ** min(attempt, 3), 5))
    generating_since = None
    last_stage = None
    failures = 0
    while True:
        check_cancel(client, job_id, context)
        try:
            result = client.status(job_id)
            failures = 0
        except ConnectionError:
            failures += 1
            if failures > retries:
                raise
            time.sleep(min(2 ** failures, 5))
            continue
        stage = (result["status"], result.get("stage"))
        if stage != last_stage:
            report_message(context, f"Job {job_id}: {stage[0]} / {stage[1]}")
            last_stage = stage
            record["status"] = result["status"]
            write_record(record_path, record)
        progress = (context or {}).get("report_progress")
        if callable(progress):
            progress(int(float(result.get("progress", 0)) * 100), 100, "Kimodo generation")
        if result["status"] in ("succeeded", "failed", "cancelled"):
            unregister = (context or {}).get("unregister_remote_job")
            if callable(unregister):
                unregister(job_id)
        if result["status"] == "succeeded":
            return result
        if result["status"] in ("failed", "cancelled"):
            raise RuntimeError(f"Kimodo {job_id}: {result.get('error') or result['status']}")
        if result["status"] != "queued" and generating_since is None:
            generating_since = time.monotonic()
        timed_out = (time.monotonic() >= deadline if generating_since is None else
                     time.monotonic() - generating_since >= float(settings["generation_timeout"]))
        if timed_out:
            if settings["cancel_on_timeout"]:
                client.cancel(job_id)
            raise TimeoutError(f"Kimodo job {job_id} timed out; recovery record: {record_path}")
        time.sleep(float(settings["poll_interval"]))


def download_results(client, record, record_path, cache):
    """Downloads verified artifacts, retaining incomplete attempts for diagnosis.

    Args:
        client (KimodoClient): Originating server client.
        record (dict): Mutable recovery record.
        record_path (str): Recovery file.
        cache (str): Owned cache root.

    Returns:
        dict: Artifact names mapped to verified files.
    """
    directory = record.get("downloads") or os.path.join(cache, f"download_{uuid.uuid4().hex}")
    job_directory = os.path.join(directory, record["job_id"])
    if os.path.isdir(job_directory) and any(name.endswith(".part") for name in os.listdir(job_directory)):
        directory = os.path.join(cache, f"download_{uuid.uuid4().hex}")
    record["downloads"] = directory
    write_record(record_path, record)
    return client.download(record["job_id"], directory, reuse_existing=True)


def publish_scene(motion_path, path, settings, cache):
    """Stages one Maya scene and atomically publishes it after a successful save.

    Args:
        motion_path (str): Verified motion file.
        path (str): Final output scene.
        settings (dict): Import settings.
        cache (str): Owned staging/cache folder on the destination filesystem.
    """
    os.makedirs(cache, exist_ok=True)
    staging = tempfile.mkdtemp(prefix="scene_", dir=cache)
    staged_path = os.path.join(staging, os.path.basename(path))
    save_motion_scene(motion_path, staged_path, settings)
    if not os.path.isfile(staged_path) or not os.path.getsize(staged_path):
        raise RuntimeError("Maya did not create a nonempty output scene.")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and not settings["overwrite"]:
        raise FileExistsError(f"Output appeared during generation: {path}")
    os.replace(staged_path, path)
    os.rmdir(staging)


def publish_artifacts(paths, directory, job_id):
    """Publishes verified artifacts into an owned bundle, preserving prior jobs.

    Args:
        paths (dict): Downloaded artifact paths.
        directory (str): Bundle parent.
        job_id (str): Generation job identifier.

    Returns:
        str: Published result manifest path.
    """
    destination = os.path.join(directory, job_id)
    manifest = os.path.join(destination, "result.json")
    if os.path.isfile(manifest):
        if read_json(manifest).get("job_id") != job_id:
            raise ValueError(f"Artifact folder belongs to another job: {destination}")
        for name, source in paths.items():
            published = os.path.join(destination, name)
            if not os.path.isfile(published) or kimodo.artifact_digest(published) != kimodo.artifact_digest(source):
                raise ValueError(f"Existing artifact bundle is incomplete or changed: {published}")
        return manifest
    os.makedirs(directory, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".staging_", dir=directory)
    for name, path in paths.items():
        shutil.copy2(path, os.path.join(staging, name))
    os.rename(staging, destination)
    return manifest


def verify_bundle(manifest, job_id):
    """Verifies a previously published bundle before skipping it without a server.

    Args:
        manifest (str): Published result manifest.
        job_id (str): Expected generation job.

    Returns:
        bool: Whether a complete bundle is present.
    """
    if not manifest or not os.path.isfile(manifest):
        return False
    result = read_json(manifest)
    if result.get("job_id") != job_id or not isinstance(result.get("artifacts"), list):
        return False
    root = os.path.dirname(manifest)
    for artifact in result["artifacts"]:
        name = artifact["name"]
        if name != os.path.basename(name) or "\\" in name or name in (".", ".."):
            raise ValueError("Invalid published artifact filename.")
        path = os.path.join(root, name)
        if not os.path.isfile(path) or kimodo.artifact_digest(path) != artifact["sha256"]:
            raise ValueError(f"Published artifact is missing or changed: {path}")
    return True


def find_published_bundle(directory):
    """Finds a valid persisted artifact bundle after its recovery cache was purged.

    Args:
        directory (str): Bundle directory containing job-specific subfolders.

    Returns:
        tuple: Manifest path and job ID, or (None, None) when no complete bundle exists.
    """
    if not os.path.isdir(directory):
        return None, None
    for name in sorted(os.listdir(directory)):
        job_directory = os.path.join(directory, name)
        manifest = os.path.join(job_directory, "result.json")
        if os.path.islink(job_directory) or not os.path.isfile(manifest):
            continue
        try:
            job_id = read_json(manifest).get("job_id")
            if job_id and verify_bundle(manifest, job_id):
                return manifest, job_id
        except (KeyError, OSError, TypeError, ValueError):
            continue
    return None, None


def save_motion_scene(motion_path, output_path, settings):
    """Imports and characterizes one result in a fresh worker scene, then saves it.

    Args:
        motion_path (str): Verified portable motion JSON.
        output_path (str): Owned staging output path.
        settings (dict): Import and HumanIK options.

    Returns:
        dict: Imported motion metadata.
    """
    from gt.tools.batch_processor import batch_processor_maya as maya

    cmds = maya.get_maya_cmds()
    maya.new_scene()
    motion = kimodo.validate_motion(read_json(motion_path))
    cmds.currentUnit(time=f"{motion['fps']:g}fps")
    result = kimodo.import_motion(motion_path, namespace=settings["namespace"],
                                  start_frame=float(settings["import_start_frame"]))
    if settings["add_humanik"]:
        kimodo.create_humanik_definition(result["group"], settings=settings["humanik"])
    cmds.playbackOptions(minTime=result["start_frame"], maxTime=result["end_frame"],
                         animationStartTime=result["start_frame"], animationEndTime=result["end_frame"])
    maya.save_scene(output_path, file_type=maya.get_maya_file_type(output_path))
    return result
