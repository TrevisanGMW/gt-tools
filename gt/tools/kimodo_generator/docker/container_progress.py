"""Periodic, non-terminal encoder download and readiness reporting inside Docker."""

import json
import logging
import os
import threading
import time


class EncoderProgress:
    """Captures Hugging Face byte callbacks without estimating preallocated file sizes."""

    def __init__(self, path="/data/logs/encoder-progress.json", probe=None, interval=3):
        """Creates a tracker without starting a background thread.

        Args:
            path (str): Shared progress file location.
            probe (callable, optional): Returns when the encoder API is ready.
            interval (float): Reporting interval in seconds.
        """
        self.path = path
        self.probe = probe
        self.interval = interval
        self.started_at = time.time()
        self.downloads = {}
        self.lock = threading.RLock()
        self.stopped = threading.Event()
        self.thread = None
        self.failed = False
        self.next_download = 0

    def install(self, module, progress_class=None):
        """Installs a progress class on Hugging Face's file-download module.

        Args:
            module (module): huggingface_hub.file_download module.
            progress_class (type, optional): Standard tqdm-compatible base for validation.
        """
        tracker = self
        if progress_class is None:
            from tqdm.auto import tqdm
            progress_class = tqdm

        class DownloadProgress(progress_class):
            """Retains byte callbacks while replacing terminal redraws with periodic logs."""

            def __init__(self, *args, **kwargs):
                """Enables accounting even when the container has no terminal.

                Args:
                    *args: Upstream progress arguments.
                    **kwargs: Upstream progress settings.
                """
                kwargs["disable"] = False
                kwargs.pop("name", None)
                super().__init__(*args, **kwargs)
                self._kimodo_progress_id = None
                if self.unit == "B" and self.total:
                    with tracker.lock:
                        tracker.next_download += 1
                        self._kimodo_progress_id = tracker.next_download
                        tracker.downloads[self._kimodo_progress_id] = {
                            "downloaded": self.n, "total": self.total, "closed": False}

            def update(self, increment=1):
                """Records bytes supplied by HTTP or Xet download callbacks.

                Args:
                    increment (float): Newly downloaded bytes.

                Returns:
                    object: Upstream update result.
                """
                result = super().update(increment)
                with tracker.lock:
                    key = getattr(self, "_kimodo_progress_id", None)
                    if key in tracker.downloads:
                        tracker.downloads[key]["downloaded"] = self.n
                return result

            def display(self, *args, **kwargs):
                """Suppresses carriage-return redraws in Docker's line-oriented logs.

                Args:
                    *args: Upstream display arguments.
                    **kwargs: Upstream display settings.
                """
                return None

            def close(self):
                """Marks a download complete without inventing missing bytes."""
                with tracker.lock:
                    key = getattr(self, "_kimodo_progress_id", None)
                    if key in tracker.downloads:
                        tracker.downloads[key].update(downloaded=self.n, closed=True)
                super().close()

        module.tqdm = DownloadProgress
        original_context = getattr(module, "_get_progress_bar_context", None)
        if original_context:
            def download_context(*args, **kwargs):
                """Injects byte accounting when Hugging Face's context helper owns the bar class.

                Args:
                    *args: Upstream context arguments.
                    **kwargs: Upstream context settings.

                Returns:
                    object: Upstream progress context using the accounting bar.
                """
                kwargs["tqdm_class"] = DownloadProgress
                return original_context(*args, **kwargs)
            module._get_progress_bar_context = download_context

    def snapshot(self):
        """Builds a thread-safe, credential-free download summary.

        Returns:
            dict: Stage, known byte totals, timestamps, and active transfer count.
        """
        with self.lock:
            transfers = list(self.downloads.values())
            downloaded = sum(min(item["downloaded"], item["total"]) for item in transfers)
            total = sum(item["total"] for item in transfers)
            active = sum(not item["closed"] for item in transfers)
        stage = "failed" if self.failed else "downloading" if active else "loading"
        return {"stage": stage, "downloaded_bytes": int(downloaded), "total_bytes": int(total),
                "active_downloads": active, "started_at": self.started_at, "updated_at": time.time()}

    def report(self):
        """Writes progress atomically and emits a readable Docker log line.

        Returns:
            dict: Current download/loading/readiness summary.
        """
        data = self.snapshot()
        if self.probe and not self.failed:
            try:
                self.probe()
                data["stage"] = "ready"
            except (OSError, RuntimeError, ValueError):
                pass
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        temporary = f"{self.path}.tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(data, stream)
        os.replace(temporary, self.path)
        if data["stage"] == "downloading":
            completed, total = data["downloaded_bytes"], data["total_bytes"]
            percent = completed * 100 / total if total else 0
            message = (f"Encoder downloading: {completed / 1024 ** 3:.2f} / {total / 1024 ** 3:.2f} GiB "
                       f"({percent:.1f}% of known downloads), {data['active_downloads']} active file(s)")
        else:
            message = {"loading": "Encoder loading model weights; no active downloads.",
                       "ready": "Encoder READY: model loaded and embedding API available.",
                       "failed": "Encoder initialization failed; inspect the text-encoder traceback."}[data["stage"]]
        logging.getLogger(__name__).info(message)
        return data

    def start(self):
        """Starts periodic reporting after writing the initial startup state."""
        self.report()

        def monitor():
            """Reports download/loading progress until the API is ready or tracking stops."""
            while not self.stopped.wait(self.interval):
                try:
                    if self.report()["stage"] in ("ready", "failed"):
                        break
                except OSError:
                    logging.getLogger(__name__).exception("Could not write encoder progress.")
        self.thread = threading.Thread(target=monitor, name="EncoderProgress", daemon=True)
        self.thread.start()

    def close(self, failed=False):
        """Stops monitoring and optionally records initialization failure.

        Args:
            failed (bool): Whether encoder initialization failed.
        """
        self.stopped.set()
        if self.thread:
            self.thread.join(timeout=self.interval + 2)
        self.failed = failed
        self.report()
