"""
Batch Processor Framework

Programmatic API for creating, configuring, serializing, and running batch
processor projects without loading the MVC user interface.
"""

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks
from gt.tools.batch_processor import batch_processor_worker


class BatchProject(batch_processor_model.BatchProcessorModel):
    """Batch processor project that can be used without the UI."""

    def __init__(self, name=None):
        """Initializes a batch processor project.

        Args:
            name (str, optional): Project name.
        """
        super().__init__()
        if name:
            self.project_name = str(name)

    def add_to_tasks(self, task):
        """Adds a task to this project.

        Args:
            task (BatchTask): Task to add.

        Returns:
            BatchTask: Added task.
        """
        return self.add_task(task)

    def add_task_type(self, task_type):
        """Creates and adds a task by type.

        Args:
            task_type (str): Task type key.

        Returns:
            BatchTask: Added task.
        """
        return self.add_task_by_type(task_type=task_type)

    def set_environment_variable(self, key, value):
        """Sets a project environment variable.

        Args:
            key (str): Variable key with or without braces.
            value (str): Variable value.
        """
        normalized_key = batch_processor_model.normalize_environment_key(key)
        self.environment_variables[normalized_key] = value

    def run(self, run_from_task_id=None, runner=None):
        """Runs this batch project.

        Args:
            run_from_task_id (str, optional): Task id to start from.
            runner (SingleInstanceBatchRunner, optional): Custom runner.

        Returns:
            BatchProgressTracker: Tracker containing final run state.
        """
        runner = runner or batch_processor_worker.SingleInstanceBatchRunner()
        return runner.run(self, run_from_task_id=run_from_task_id)


def create_default_project(name=None):
    """Creates a default batch project.

    Args:
        name (str, optional): Project name.

    Returns:
        BatchProject: New batch project.
    """
    return BatchProject(name=name)


# Convenience exports for framework users.
BatchTask = batch_processor_tasks.BatchTask
TaskInput = batch_processor_tasks.TaskInput
TaskMayaImport = batch_processor_tasks.TaskMayaImport
TaskRename = batch_processor_tasks.TaskRename
TaskPythonScript = batch_processor_tasks.TaskPythonScript
TaskMotionBuilderScript = batch_processor_tasks.TaskMotionBuilderScript
TaskBlenderScript = batch_processor_tasks.TaskBlenderScript
TaskUnrealScript = batch_processor_tasks.TaskUnrealScript
TaskMayaSave = batch_processor_tasks.TaskMayaSave
TaskExportUsd = batch_processor_tasks.TaskExportUsd
TaskExportFbx = batch_processor_tasks.TaskExportFbx
TaskRetarget = batch_processor_tasks.TaskRetarget
TaskRetargetHumanIK = batch_processor_tasks.TaskRetargetHumanIK
TaskAutoRigBuild = batch_processor_tasks.TaskAutoRigBuild
TaskClipSplit = batch_processor_tasks.TaskClipSplit
TaskClipSnapshot = batch_processor_tasks.TaskClipSnapshot
TaskAnnotationSnapshot = batch_processor_tasks.TaskAnnotationSnapshot
TaskMapHierarchy = batch_processor_tasks.TaskMapHierarchy
TaskDeleteProjectFiles = batch_processor_tasks.TaskDeleteProjectFiles
TaskArchive = batch_processor_tasks.TaskArchive
TaskValidationMayaScene = batch_processor_tasks.TaskValidationMayaScene
TaskValidationFileIntegrity = batch_processor_tasks.TaskValidationFileIntegrity
TaskValidationFolderCompare = batch_processor_tasks.TaskValidationFolderCompare
TaskCaptureThumbnail = batch_processor_tasks.TaskCaptureThumbnail
TaskCapturePlayblast = batch_processor_tasks.TaskCapturePlayblast
WorkItem = batch_processor_tasks.WorkItem
ValidationResult = batch_processor_tasks.ValidationResult
