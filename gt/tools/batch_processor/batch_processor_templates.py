"""
Batch Processor Templates
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
import json
import logging
import os
import sys
import types

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_PREFS_FILENAME = "batch_processor"


def get_default_prefs_dir():
    """Gets the default gt-tools prefs directory.

    Returns:
        str: Path to the gt-tools prefs directory.
    """
    try:
        import gt.core.prefs as core_prefs

        return core_prefs.Prefs(_PREFS_FILENAME).get_dir_path()
    except Exception as exception:
        logger.debug("Unable to resolve prefs path through gt.core.prefs: %s", exception)
        return os.path.join(os.path.expanduser("~"), "Documents", "maya", "gt-tools", "prefs")


def get_template_source_dir():
    """Gets the batch processor template source directory.

    Returns:
        str: Path to the batch processor template directory.
    """
    return os.path.join(get_default_prefs_dir(), "{0}_templates".format(_PREFS_FILENAME))


def get_package_template_source_dir():
    """Gets the package-provided batch processor template directory.

    Returns:
        str: Path to the package template directory.
    """
    tool_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tool_dir, "templates", "package_templates")


def save_project_template(project, template_path):
    """Saves a project as a template without changing the active project.

    Args:
        project (BatchProcessorModel): Project to serialize as a template.
        template_path (str): Destination `.batch` template file path.

    Returns:
        str: Saved template file path.
    """
    if not isinstance(project, batch_processor_model.BatchProcessorModel):
        raise TypeError("Expected a BatchProcessorModel project.")

    template_dir = os.path.dirname(template_path)
    if template_dir and not os.path.isdir(template_dir):
        os.makedirs(template_dir)
    batch_processor_model.BatchProcessorModel._atomic_write_json(template_path, project.to_dict())
    logger.info('Saved batch project template: "%s"', template_path)
    return template_path


TEMPLATE_SOURCE_DIR = get_template_source_dir()
PACKAGE_TEMPLATE_SOURCE_DIR = get_package_template_source_dir()


class BatchProcessorTemplates:
    """Discovers user and optional package batch processor project templates."""

    icon_files = "ui_templates"
    icon_package_files = "ui_templates_package"
    file_templates = {}
    package_file_templates = {}

    def __init__(self, include_package_templates=False):
        """Refreshes user and optional package template registries.

        Args:
            include_package_templates (bool, optional): Whether package templates
                should also be loaded. Defaults to False.
        """
        BatchProcessorTemplates.file_templates = {}
        BatchProcessorTemplates.package_file_templates = {}
        if os.path.isdir(TEMPLATE_SOURCE_DIR):
            self.populate_with_template_files(folder_path=TEMPLATE_SOURCE_DIR)
        else:
            sys.stdout.write('Template source directory "{0}" not found. Skipping.\n'.format(TEMPLATE_SOURCE_DIR))
        if include_package_templates and os.path.isdir(PACKAGE_TEMPLATE_SOURCE_DIR):
            self.populate_with_template_files(
                folder_path=PACKAGE_TEMPLATE_SOURCE_DIR,
                template_store=BatchProcessorTemplates.package_file_templates,
            )

    @staticmethod
    def get_dict_templates(include_file_templates=True, include_package_templates=False):
        """Gets available template loader functions.

        Args:
            include_file_templates (bool, optional): Whether user file templates
                should be included. Defaults to True.
            include_package_templates (bool, optional): Whether package templates
                should be included. Defaults to False.

        Returns:
            dict: Template name to loader function mapping.
        """
        template_store = {}
        if include_file_templates:
            template_store.update(BatchProcessorTemplates.file_templates)
        if include_package_templates:
            template_store.update(BatchProcessorTemplates.package_file_templates)
        return {
            name: value
            for name, value in template_store.items()
            if isinstance(value, types.FunctionType) and not name.startswith("_")
        }

    @staticmethod
    def get_template_names(include_file_templates=True, include_package_templates=False):
        """Gets the available template names.

        Args:
            include_file_templates (bool, optional): Whether user file templates
                should be included. Defaults to True.
            include_package_templates (bool, optional): Whether package templates
                should be included. Defaults to False.

        Returns:
            list: Template names.
        """
        return list(
            BatchProcessorTemplates.get_dict_templates(
                include_file_templates=include_file_templates,
                include_package_templates=include_package_templates,
            ).keys()
        )

    @staticmethod
    def populate_with_template_files(folder_path, template_store=None):
        """Populates the template registry with `.batch` project files.

        Args:
            folder_path (str): Folder containing batch templates.
            template_store (dict, optional): Dictionary receiving the generated
                template loaders. Defaults to the user template store.
        """
        if template_store is None:
            template_store = BatchProcessorTemplates.file_templates
        for filename in sorted(os.listdir(folder_path)):
            if not filename.endswith(constants.Project.EXTENSION):
                continue
            variable_name = os.path.splitext(filename)[0]
            variable_name = variable_name.replace("-", "_").replace(" ", "_")
            file_path = os.path.join(folder_path, filename)

            def file_loader(template_path=file_path):
                """Loads a batch project from a template file.

                Args:
                    template_path (str): Template file path.

                Returns:
                    BatchProcessorModel: Project initialized from template data.
                """
                with open(template_path, "r", encoding="utf-8") as template_file:
                    data = json.load(template_file)
                project = batch_processor_model.BatchProcessorModel()
                project.read_data_from_dict(data)
                project.project_file_path = None
                project.environment_variables["project-dir"] = ""
                return project

            template_store[variable_name] = file_loader
