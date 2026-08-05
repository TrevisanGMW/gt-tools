"""Structured event transport for Batch Processor workers."""

import datetime
import json
import os

from gt.tools.batch_processor.tracker import tracker_constants


def utc_now_iso():
    """Gets a timezone-explicit UTC timestamp.

    Returns:
        str: ISO-formatted UTC timestamp.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def parse_timestamp(value):
    """Parses an ISO timestamp.

    Args:
        value (str): ISO timestamp.

    Returns:
        datetime.datetime or None: Parsed value, or None when unparsable.
    """
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return None


def elapsed_seconds(started_at, completed_at=""):
    """Gets elapsed seconds between two ISO timestamps.

    Args:
        started_at (str): Start timestamp.
        completed_at (str, optional): End timestamp, or now when empty.

    Returns:
        float: Elapsed seconds, clamped to be non-negative.
    """
    start = parse_timestamp(started_at)
    if not start:
        return 0.0
    end = parse_timestamp(completed_at) or datetime.datetime.now(datetime.timezone.utc)
    return max(0.0, (end - start).total_seconds())


class EventWriter:
    """Writes append-only JSON-line worker events."""

    def __init__(self, file_path, job_id):
        """Initializes an event writer.

        Args:
            file_path (str): Event stream path.
            job_id (str): Stable job identifier.
        """
        self.file_path = file_path
        self.job_id = job_id
        self.sequence = 0
        self.file_handle = None

    def open(self):
        """Opens the event stream, creating its directory when needed."""
        if not self.file_path or self.file_handle:
            return
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        self.file_handle = open(self.file_path, "a", encoding="utf-8")

    def emit(self, event_name, **payload):
        """Writes and flushes one event.

        Args:
            event_name (str): Event type.
            **payload: JSON-compatible event values.
        """
        if not self.file_path:
            return
        self.open()
        self.sequence += 1
        data = {
            "schema_version": tracker_constants.EVENT_SCHEMA_VERSION,
            "event": event_name,
            "job_id": self.job_id,
            "sequence": self.sequence,
            "timestamp": utc_now_iso(),
        }
        data.update(payload)
        self.file_handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")
        self.file_handle.flush()

    def close(self):
        """Closes the event stream."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None


class EventReader:
    """Incrementally reads a JSON-line event stream."""

    def __init__(self, file_path):
        """Initializes an event reader.

        Args:
            file_path (str): Event stream path.
        """
        self.file_path = file_path
        self.offset = 0
        self.pending_text = ""

    def read_new(self):
        """Reads newly appended complete events.

        Returns:
            list: Parsed event dictionaries.
        """
        if not self.file_path or not os.path.isfile(self.file_path):
            return []
        try:
            file_size = os.path.getsize(self.file_path)
            if file_size < self.offset:
                self.offset = 0
                self.pending_text = ""
            with open(self.file_path, "r", encoding="utf-8", errors="replace") as event_file:
                event_file.seek(self.offset)
                text = event_file.read()
                self.offset = event_file.tell()
        except OSError:
            return []
        text = self.pending_text + text
        lines = text.splitlines(keepends=True)
        self.pending_text = ""
        if lines and not lines[-1].endswith(("\n", "\r")):
            self.pending_text = lines.pop()
        events = []
        for line in lines:
            try:
                event = json.loads(line)
            except (TypeError, ValueError):
                continue
            if event.get("schema_version") == tracker_constants.EVENT_SCHEMA_VERSION:
                events.append(event)
        return events

