"""Job polling, automatic downloads, and explicitly confirmed cleanup actions."""

import copy
import os
from gt.ui.qt_import import QtWidgets
from gt.utils import kimodo
from gt.tools.kimodo_generator import kimodo_generator_results as results
from gt.tools.kimodo_generator import kimodo_generator_export as scene_export


class KimodoJobActions:
    """Controller actions sharing the owning MVC's network dispatcher and status field."""

    def save_auto_download(self):
        """Persists automatic download mode independently of unfinished prompt inputs."""
        if not self.loading:
            self.model.auto_download = self.view.auto_download.isChecked()
            self.model.save_preferences()
            self.poll_jobs()

    def poll_jobs(self):
        """Polls active jobs and schedules completed downloads or confirmed cleanup."""
        if self.closed or not self._results_view_is_valid():
            if not self.closed:
                self._view_destroyed()
            return
        self.populate_jobs()
        for job in list(self.model.jobs):
            if job.get("cleanup_requested"):
                if job.get("status") in kimodo.TERMINAL_STATUSES or job.get("server_missing"):
                    if not job.get("cleanup_error"):
                        self._cleanup_job(job)
            elif (self.model.auto_download and job.get("status") == "succeeded"
                  and job.get("operation") != "download_model" and not job.get("server_missing")
                  and not job.get("download_error") and results.local_status(job) == "not downloaded"):
                if sum(key.startswith("download:") for key in self.pending) < 2:
                    self._download_job(job)
            elif (self.model.auto_maya_file and job.get("status") == "succeeded"
                  and job.get("operation") != "download_model" and results.local_status(job) == "downloaded"
                  and not job.get("maya_files") and not job.get("maya_export_error")):
                if not any(key.startswith("maya:") for key in self.pending):
                    self._create_maya_files(job)
        if "poll" not in self.pending:
            jobs = [job for job in self.model.jobs if job["status"] not in
                    kimodo.TERMINAL_STATUSES + ("submitting", "submission_unknown") and not job.get("server_missing")]
            if jobs:
                self._refresh_jobs(jobs)

    def _refresh_jobs(self, jobs):
        """Refreshes origins independently so one unavailable server cannot block others.

        Args:
            jobs (list): Entries from the local history.
        """
        clients = [(job, self._job_client(job)) for job in jobs]

        def operation():
            """Reads statuses without mutating MVC state.

            Returns:
                list: Per-job response/error pairs.
            """
            responses = []
            for job, client in clients:
                try:
                    responses.append((client.status(job["job_id"]), None))
                except Exception as error:
                    responses.append((None, str(error)))
            return responses

        def updated(responses):
            """Merges remote states while retaining local paths and cleanup intent.

            Args:
                responses (list): Worker status/error pairs.
            """
            for (job, unused), (response, error) in zip(clients, responses):
                if job not in self.model.jobs:
                    continue
                if response:
                    job.update(response)
                    job.pop("refresh_error", None)
                    job.pop("server_missing", None)
                else:
                    job["refresh_error"] = error
                    job["server_missing"] = "HTTP 404" in error and "Unknown job" in error
            self.model.save_preferences()
            self.populate_jobs()
        self.run_network("poll", operation, updated)

    def refresh_job(self):
        """Refreshes remote state and immediately flags missing downloaded files."""
        job = self.selected_job()
        self.populate_jobs()
        self._refresh_jobs([job])

    def download_results(self):
        """Downloads or repairs the selected generation without replacing verified files."""
        self.save_output_folder()
        self._download_job(self.selected_job(), manual=True)

    def _download_job(self, job, manual=False):
        """Queues one verified download using its original bridge and saved destination.

        Args:
            job (dict): Completed generation history entry.
            manual (bool): Explicit retry after a failed/missing download.
        """
        if job.get("cleanup_requested"):
            raise ValueError("This job is being cleaned; wait for cleanup before downloading.")
        if job.get("status") != "succeeded" or job.get("operation") == "download_model":
            raise ValueError("Select a successful generation job; model-download jobs have no motion results.")
        if job.get("downloading"):
            return
        if results.local_status(job) == "downloaded":
            if manual:
                self.message("Results are already downloaded. Select a sample to import.")
            return
        directory = self.model.output_directory
        paths = job.get("paths", {})
        # Repair missing files in their original job directory, not a new duplicate.
        if paths and not (manual and job.get("download_error")):
            directory = os.path.dirname(os.path.dirname(next(iter(paths.values()))))
        client = self._job_client(job)
        if not directory or not os.path.isabs(directory):
            raise ValueError("Choose an absolute download folder before downloading results.")
        job["download_directory"] = os.path.join(directory, job["job_id"])
        job["downloading"] = True
        job.pop("download_error", None)

        def operation():
            """Downloads without Maya/Qt or worker-thread model mutations.

            Returns:
                tuple: Paths and optional actionable error text.
            """
            try:
                return client.download(job["job_id"], directory, reuse_existing=True), None
            except Exception as error:
                return None, str(error)

        def downloaded(payload):
            """Updates local status and stops repeated automatic retries on failure.

            Args:
                payload (tuple): Downloaded paths/error.
            """
            paths, error = payload
            job.pop("downloading", None)
            if error:
                job["download_error"] = error
                self.message(f"Download failed: {error}. Use Download Results to retry.", warning=True)
            else:
                job["paths"] = paths
                if self.model.auto_maya_file:
                    self.message("Results downloaded. Maya + HumanIK files will be created automatically.")
                else:
                    self.message("Results downloaded. Select a sample and click Import Sample.")
            self.model.save_preferences()
            self.populate_jobs()
        self.run_network(f"download:{job['url']}:{job['job_id']}", operation, downloaded)
        self.populate_jobs()

    def save_auto_maya_file(self):
        """Persists automatic scene creation independently of prompt/connection inputs."""
        if not self.loading:
            self.model.auto_maya_file = self.view.auto_maya_file.isChecked()
            self.model.save_preferences()
            self.poll_jobs()

    def save_auto_import_maya(self):
        """Persists automatic import and enables its dependent scene-clear option."""
        if not self.loading:
            self.model.auto_import_maya = self.view.auto_import_maya.isChecked()
            for widget in (self.view.auto_import_all_samples, self.view.auto_clear_scene,
                           self.view.auto_frame_rate, self.view.auto_frame_range):
                widget.setEnabled(self.model.auto_import_maya)
            self.model.save_preferences()
            self.update_project_summary()

    def save_auto_import_all_samples(self):
        """Persists whether automatic import brings every sample into the current scene."""
        if not self.loading:
            self.model.auto_import_all_samples = self.view.auto_import_all_samples.isChecked()
            self.model.save_preferences()
            self.update_project_summary()

    def save_auto_clear_scene(self):
        """Persists force-clearing the current scene before an automatic Maya import."""
        if not self.loading:
            self.model.auto_clear_scene = self.view.auto_clear_scene.isChecked()
            self.model.save_preferences()
            self.update_project_summary()

    def save_auto_frame_rate(self):
        """Persists matching Maya's time unit to the generated motion rate on auto-import."""
        if not self.loading:
            self.model.auto_frame_rate = self.view.auto_frame_rate.isChecked()
            self.model.save_preferences()
            self.update_project_summary()

    def save_auto_frame_range(self):
        """Persists matching the playback range to the generated motion length on auto-import."""
        if not self.loading:
            self.model.auto_frame_range = self.view.auto_frame_range.isChecked()
            self.model.save_preferences()
            self.update_project_summary()

    def create_maya_files(self):
        """Creates or repairs scenes for every downloaded sample in the selected job."""
        job = self.selected_job()
        if results.local_status(job) != "downloaded":
            raise ValueError("Download Results first, then create Maya files.")
        if any(key.startswith("maya:") for key in self.pending):
            raise ValueError("Wait for the current Maya export to finish before starting another.")
        self._create_maya_files(job)

    def _create_maya_files(self, job):
        """Schedules isolated scene processing without invoking Maya on a UI worker thread.

        Args:
            job (dict): Downloaded generation history entry.
        """
        if job.get("cleanup_requested"):
            raise ValueError("This job is being cleaned. Wait for cleanup to finish.")
        paths, settings = copy.deepcopy(job["paths"]), copy.deepcopy(self.model.humanik)
        job["exporting_maya"] = True
        job.pop("maya_export_error", None)

        def operation():
            """Runs a separate mayapy process and reports failures for manual retry.

            Returns:
                tuple: Exported file paths and optional error.
            """
            try:
                return scene_export.export_maya_files(paths, settings), None
            except Exception as error:
                return None, str(error)

        def exported(payload):
            """Records output paths only after the standalone worker finishes.

            Args:
                payload (tuple): Output paths/error.
            """
            files, error = payload
            job.pop("exporting_maya", None)
            if error:
                job["maya_export_error"] = error
                self.message(f"Maya export failed: {error}. Use Create Maya Files to retry.", warning=True)
            else:
                job["maya_files"] = files
                self.message(f"Created {len(files)} Maya file(s) with locked HumanIK definitions.")
            self.model.save_preferences()
            self.populate_jobs()
            if not error and self.model.auto_import_maya:
                try:
                    self.import_generated_maya_file(job, automatic=True)
                except Exception as import_error:
                    job["maya_import_error"] = str(import_error)
                    self.model.save_preferences()
                    self.populate_jobs()
                    self.message(f"Automatic Maya import failed: {import_error}", warning=True)
        self.run_network(f"maya:{job['url']}:{job['job_id']}", operation, exported)
        self.populate_jobs()

    def print_server_location(self):
        """Queries and prints the selected job's actual server-side directory."""
        job = self.selected_job()
        client = self._job_client(job)

        def located(response):
            """Prints server-native paths without assuming a Windows/WSL mount mapping.

            Args:
                response (dict): Server job status with its directory.
            """
            directory = response.get("server_directory")
            if not directory:
                self.message("Restart the Kimodo bridge with the updated code to report file locations.", warning=True)
                return
            job["server_directory"] = directory
            self.model.save_preferences()
            print(f"Kimodo bridge: {job['url']}\nJob: {job['job_id']}\nServer job directory: {directory}")
            self.message(f"Server job directory (also printed to Script Editor): {directory}")
        self.run_network(f"location:{job['url']}:{job['job_id']}", lambda: client.status(job["job_id"]), located)

    def copy_job_id(self):
        """Copies the selected server job identifier to the system clipboard."""
        job = self.selected_job()
        QtWidgets.QApplication.clipboard().setText(job["job_id"])
        self.message(f"Copied job ID: {job['job_id']}")

    def copy_server_location(self):
        """Copies the known server directory, querying it first when necessary."""
        job = self.selected_job()
        directory = job.get("server_directory")
        if directory:
            QtWidgets.QApplication.clipboard().setText(directory)
            self.message(f"Copied server directory: {directory}")
            return
        client = self._job_client(job)

        def located(response):
            """Stores and copies a queried server-native directory.

            Args:
                response (dict): Server job status response.
            """
            path = response.get("server_directory")
            if not path:
                raise ValueError("The bridge did not report a server directory. Restart it and retry.")
            job["server_directory"] = path
            self.model.save_preferences()
            QtWidgets.QApplication.clipboard().setText(path)
            self.message(f"Copied server directory: {path}")

        key = f"copy_location:{job['url']}:{job['job_id']}"
        self.run_network(key, lambda: client.status(job["job_id"]), located)

    def clear_selected_job(self):
        """Opens the scoped cleanup confirmation for the selected history entry."""
        self._confirm_cleanup([self.selected_job()])

    def clear_finished(self):
        """Confirms cleanup of succeeded, failed and cancelled jobs only."""
        self._confirm_cleanup([job for job in self.model.jobs if job["status"] in kimodo.TERMINAL_STATUSES])

    def delete_server_files(self):
        """Deletes server directories for completed tracked jobs but keeps local history/files."""
        current_url = self.view.url.text().strip().rstrip("/")
        if not current_url:
            raise ValueError("Enter the bridge URL whose completed server files should be deleted.")
        jobs = [job for job in self.model.jobs
                if job.get("status") in kimodo.TERMINAL_STATUSES and not job.get("server_missing")
                and (job.get("url") or current_url).rstrip("/") == current_url]
        if not jobs:
            raise ValueError("No completed server jobs for this bridge are tracked in Results history.")
        answer = QtWidgets.QMessageBox.question(
            self.view, "Delete Completed Server Files",
            f"Permanently delete the server job records and folders for {len(jobs)} completed job(s) on "
            f"{current_url}?\n\n"
            "Local Maya history and downloaded files will remain. Active jobs, model weights, and text encoders "
            "are not affected.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        snapshots = copy.deepcopy(jobs)
        for job in snapshots:
            job["url"] = job.get("url") or current_url

        def operation():
            """Deletes each exact terminal job remotely without touching local artifacts."""
            outcomes = []
            for job in snapshots:
                try:
                    response = self._job_client(job).delete_job(job["job_id"])
                    outcomes.append({"url": job["url"], "job_id": job["job_id"],
                                     "deleted": True, "response": response})
                except Exception as error:
                    outcomes.append({"url": job["url"], "job_id": job["job_id"],
                                     "deleted": False, "error": str(error)})
            return outcomes

        def completed(outcomes):
            """Marks server cleanup outcomes while retaining local job rows and downloads.

            Args:
                outcomes (list[dict]): Per-job server deletion results with URL, job ID,
                    deletion status, and a response or error.
            """
            deleted = 0
            failed = 0
            by_key = {(job.get("url") or current_url, job["job_id"]): job for job in self.model.jobs}
            for outcome in outcomes:
                job = by_key.get((outcome["url"], outcome["job_id"]))
                if not job:
                    continue
                if outcome["deleted"]:
                    job["server_missing"] = True
                    job["server_files_deleted"] = True
                    job.pop("server_cleanup_error", None)
                    deleted += 1
                else:
                    job["server_cleanup_error"] = outcome["error"]
                    failed += 1
            self.model.save_preferences()
            self.populate_jobs()
            if failed:
                self.message(f"Deleted server files for {deleted} job(s); {failed} cleanup(s) failed. "
                             "Failed jobs remain available for retry.", warning=True)
            else:
                self.message(f"Deleted server files and folders for {deleted} completed job(s). "
                             "Local history and downloads were preserved.")

        self.run_network("delete_server_files", operation, completed)

    def clear_history(self):
        """Confirms cleanup of all tracked jobs, cancelling active work first."""
        self._confirm_cleanup(list(self.model.jobs))

    def _confirm_cleanup(self, jobs):
        """Previews scope and asks explicitly which files to permanently remove.

        Args:
            jobs (list): Exact tracked jobs selected by this cleanup action.
        """
        if not jobs:
            raise ValueError("No matching jobs to clear.")
        if "generate" in self.pending or any(job.get("downloading") or job.get("exporting_maya") for job in jobs):
            raise ValueError("Wait for submission/download/Maya export to finish before cleaning these jobs.")
        dialog = QtWidgets.QDialog(self.view)
        dialog.setWindowTitle("Clean Kimodo Results")
        layout = QtWidgets.QVBoxLayout(dialog)
        text = QtWidgets.QLabel(
            f"Clear {len(jobs)} history entries across {len({job['url'] for job in jobs})} server(s)?\n"
            "Active jobs will be cancelled and kept visible until they stop.\n"
            "Deletion is permanent. Imported Maya animation, added scene files, and model weights are not deleted.")
        text.setWordWrap(True)
        layout.addWidget(text)
        server = QtWidgets.QCheckBox("Delete server job files (including WSL copies)")
        server.setChecked(True)
        server.setToolTip("Permanently remove these exact server job folders after completion. "
                          "If a server is unavailable/outdated, keep history so cleanup can be retried.")
        local = QtWidgets.QCheckBox("Also delete verified downloaded artifacts on this computer")
        local.setToolTip("Only unchanged, recorded artifacts are deleted. Edited files and extra Maya scenes "
                         "are preserved. Uncheck to keep downloaded results while removing server duplicates.")
        layout.addWidget(server)
        layout.addWidget(local)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Clean Results")
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setDefault(True)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._request_cleanup(jobs, server.isChecked(), local.isChecked())

    def _request_cleanup(self, jobs, server, local):
        """Records confirmed cleanup intent before cancellation or filesystem work.

        Args:
            jobs (list): Explicitly confirmed entries.
            server (bool): Delete remote job cache.
            local (bool): Delete verified local artifacts.
        """
        for job in jobs:
            job["cleanup_requested"] = {"server": server, "local": local}
            job.pop("cleanup_error", None)
            self._cleanup_job(job)
        self.model.save_preferences()
        self.populate_jobs()

    def _cleanup_job(self, job):
        """Cancels active work or removes an explicitly scoped finished job.

        Args:
            job (dict): History entry carrying confirmed cleanup options.
        """
        key = f"cleanup:{job['url']}:{job['job_id']}"
        if key in self.pending:
            return
        snapshot = copy.deepcopy(job)
        client = self._job_client(job)

        def operation():
            """Performs cancellable, scoped network and filesystem cleanup.

            Returns:
                dict: State or deletion outcome; errors retain the history entry.
            """
            try:
                if snapshot["status"] not in kimodo.TERMINAL_STATUSES and not snapshot.get("server_missing"):
                    try:
                        state = client.status(snapshot["job_id"])
                    except RuntimeError as error:
                        if "HTTP 404" in str(error) and "Unknown job" in str(error):
                            return {"state": {"server_missing": True}}
                        raise
                    if state["status"] in kimodo.TERMINAL_STATUSES:
                        return {"state": state}
                    return {"state": client.cancel(snapshot["job_id"])}
                options = snapshot["cleanup_requested"]
                if options["local"]:
                    results.delete_local_artifacts(snapshot, dry_run=True)
                if options["server"]:
                    client.delete_job(snapshot["job_id"])
                local_result = results.delete_local_artifacts(snapshot) if options["local"] else {"preserved": []}
                return {"removed": True, "preserved": local_result["preserved"],
                        "directory": local_result.get("directory", "")}
            except Exception as error:
                return {"error": str(error)}

        def cleaned(payload):
            """Retains failed work for retry and removes rows only after acknowledged cleanup.

            Args:
                payload (dict): Cleanup outcome.
            """
            if payload.get("error"):
                job["cleanup_error"] = payload["error"]
                self.message(f"Cleanup retained {job['job_id'][:12]}: {payload['error']}", warning=True)
            elif payload.get("removed"):
                if job in self.model.jobs:
                    self.model.jobs.remove(job)
                kept = len(payload["preserved"])
                self.message(f"Cleared {job['job_id'][:12]}. Requested artifact deletion is permanent. "
                             f"Preserved {kept} edited/extra local files. "
                             f"{payload.get('directory', '') if kept else ''}")
            else:
                job.update(payload["state"])
                self.message("Cancellation requested; cleanup will finish when the job stops.")
            self.model.save_preferences()
            self.populate_jobs()
        self.run_network(key, operation, cleaned)
