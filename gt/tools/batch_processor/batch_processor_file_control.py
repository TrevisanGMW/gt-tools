"""Explicit per-file filtering and routing, independent of Maya at import time."""

from contextlib import contextmanager
import os
import re
import shutil
import tempfile
import uuid

from gt.tools.batch_processor import batch_processor_task_base as task_base


ISSUE_ACTIONS = ["Existing behavior", "Stop processing file", "Copy to folder and stop"]
DESTINATION_MODES = ["Subfolder", "Custom folder"]


class FileFiltered(task_base.TaskSkip):
    """Signals intentional removal from the current processing stream."""

    filters_file = True


@contextmanager
def destination_lock(destination):
    """Claims one routed destination and removes only this operation's lock.

    Args:
        destination (str): Absolute output path.

    Yields:
        None: The caller owns the destination claim.
    """
    lock_path = f"{destination}.filter.lock"
    owner = uuid.uuid4().hex
    created = False
    try:
        with open(lock_path, "x", encoding="utf-8") as lock_file:
            created = True
            lock_file.write(owner)
    except FileExistsError as exception:
        raise RuntimeError(f"Filtered destination is already in use: {destination}") from exception
    except OSError:
        if created:
            os.remove(lock_path)
        raise
    try:
        yield
    finally:
        try:
            with open(lock_path, encoding="utf-8") as lock_file:
                owned = lock_file.read() == owner
            if owned:
                os.remove(lock_path)
        except FileNotFoundError:
            pass


class FileControl:
    """Provides immediate stop and save/copy-and-stop actions to file scripts."""

    def __init__(self, task, project, work_item, output_path, write_scene=False, preview=False):
        """Stores the current file's execution scope.

        Args:
            task (BatchTask): Current task.
            project (BatchProcessorModel): Project used to resolve path templates.
            work_item (WorkItem): Current input, or None for project scripts.
            output_path (str): Planned file output path.
            write_scene (bool, optional): Save the loaded scene instead of copying input bytes.
            preview (bool, optional): Reject file actions during editor previews.
        """
        self.task = task
        self.project = project
        self.work_item = work_item
        self.output_path = output_path
        self.write_scene = write_scene
        self.preview = preview

    def check_scope(self):
        """Rejects actions outside a real per-file execution."""
        if self.preview or self.work_item is None:
            raise ValueError("File filtering is available only during a per-file run, not a preview or run-once task.")

    def skip_file(self, reason="Filtered by script"):
        """Immediately stops this file without the task's automatic save.

        Args:
            reason (str, optional): Explanation recorded by the tracker.
        """
        self.check_scope()
        raise FileFiltered(f"[FILTERED] {reason}")

    def save_to_subfolder(self, folder="filtered", reason="Filtered by script"):
        """Saves or copies into a subfolder and stops this file.

        Args:
            folder (str, optional): Relative subfolder of the planned output folder.
            reason (str, optional): Explanation recorded by the tracker.
        """
        self.route(folder, "Subfolder", reason)

    def save_to_folder(self, folder, reason="Filtered by script"):
        """Saves or copies into a project-relative or absolute folder template.

        Args:
            folder (str): Destination template, e.g. ``{project-dir}/{output-dir}/filtered``.
            reason (str, optional): Explanation recorded by the tracker.
        """
        self.route(folder, "Custom folder", reason)

    def resolve_destination(self, folder, mode):
        """Resolves a destination without allowing source overwrite.

        Args:
            folder (str): Folder name or environment-variable template.
            mode (str): Subfolder or Custom folder.

        Returns:
            str: Absolute destination file path.
        """
        self.check_scope()
        if self.task.modifies_in_place():
            raise ValueError("Disable Modify before routing a file to another folder.")
        if not self.output_path or not os.path.isabs(self.output_path):
            raise ValueError("The planned output folder must resolve to an absolute path before routing.")
        if mode not in DESTINATION_MODES:
            raise ValueError(f"Unknown filtered destination mode: {mode}")
        template = str(folder or "").strip()
        expanded = self.project.resolve_template(template, task=self.task)
        if not expanded or re.search(r"\{[^{}]+\}", str(expanded)):
            raise ValueError(f"Filtered destination is empty or contains unresolved variables: {template}")
        if mode == "Subfolder":
            if os.path.isabs(expanded) or os.path.splitdrive(expanded)[0]:
                raise ValueError("Use Custom folder for an absolute destination.")
            base_dir = os.path.abspath(os.path.dirname(self.output_path))
            destination_dir = os.path.abspath(os.path.join(base_dir, expanded))
            if os.path.commonpath([base_dir, destination_dir]) != base_dir or destination_dir == base_dir:
                raise ValueError("Subfolder must remain inside the planned output folder.")
        else:
            destination_dir = self.project.resolve_template_path(template, task=self.task)
            if not destination_dir:
                raise ValueError("Set the project folder before using a relative filtered destination.")
        destination = os.path.join(destination_dir, os.path.basename(self.output_path))
        for source in (self.work_item.source_path, self.work_item.current_path):
            if os.path.normcase(os.path.realpath(source)) == os.path.normcase(os.path.realpath(destination)):
                raise ValueError("Filtered destination must not overwrite an input file.")
            if os.path.exists(source) and os.path.exists(destination) and os.path.samefile(source, destination):
                raise ValueError("Filtered destination refers to an input file.")
        return destination

    def route(self, folder, mode, reason):
        """Publishes a complete routed output and stops downstream processing.

        Args:
            folder (str): Destination folder template.
            mode (str): Destination mode.
            reason (str): Tracker explanation.
        """
        destination = self.resolve_destination(folder, mode)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with destination_lock(destination):
            if os.path.exists(destination) and not self.task.settings.get("overwrite", False):
                raise FileFiltered(f"[FILTERED] {reason}; existing destination preserved: {destination}")
            descriptor, temporary = tempfile.mkstemp(
                prefix=".filtered_", suffix=os.path.splitext(destination)[1], dir=os.path.dirname(destination)
            )
            os.close(descriptor)
            try:
                if self.write_scene:
                    from gt.tools.batch_processor import batch_processor_maya

                    batch_processor_maya.save_scene(temporary)
                    if not os.path.getsize(temporary):
                        raise RuntimeError(f"Maya did not write a complete filtered scene: {destination}")
                else:
                    shutil.copyfile(self.work_item.current_path, temporary)
                os.replace(temporary, destination)
                if self.write_scene:
                    batch_processor_maya.get_maya_cmds().file(rename=destination)
            finally:
                if os.path.exists(temporary):
                    os.remove(temporary)
        raise FileFiltered(f"[FILTERED] {reason}; saved to: {destination}")


def apply_issue_action(task, project, work_item, output_dir, has_issues):
    """Applies an optional validation disposition after writing its report.

    Args:
        task (BatchTask): Validation task.
        project (BatchProcessorModel): Active project.
        work_item (WorkItem): Validated file.
        output_dir (str): Task output folder.
        has_issues (bool): Whether validation found issues.
    """
    if not has_issues:
        return
    action = task.settings.get("issue_action", ISSUE_ACTIONS[0])
    control = FileControl(task, project, work_item, os.path.join(output_dir, os.path.basename(work_item.current_path)))
    reason = f"{task.display_name}: validation found issues"
    if action == ISSUE_ACTIONS[1]:
        control.skip_file(reason)
    if action == ISSUE_ACTIONS[2]:
        control.route(
            task.settings.get("filter_folder", "filtered"),
            task.settings.get("filter_destination_mode", "Subfolder"), reason,
        )
