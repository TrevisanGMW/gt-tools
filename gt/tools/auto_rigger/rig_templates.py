"""
Templates

Import Line:
    import gt.tools.auto_rigger.rig_templates as tools_rig_templates
"""

import gt.tools.auto_rigger.templates.template_generic_root as tools_template_root
import gt.tools.auto_rigger.templates.template_biped as tools_templates_biped
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.ui.resource_library as ui_res_lib
import gt.ui.file_dialog as ui_file_dialog
import gt.core.prefs as core_prefs
import gt.core.uuid as core_uuid
import gt.core.io as core_io
import logging
import shutil
import types
import copy
import os
import sys

# File Templates Source Folders
_PREFS_FILENAME = tools_rig_const.RiggerConstants.PREFS_FILENAME


def get_template_source_dir():
    """Gets the auto rigger template source directory.

    Returns:
        str: Path to the auto rigger template directory.
    """
    prefs_dir = core_prefs.Prefs(_PREFS_FILENAME).get_dir_path()
    return os.path.join(prefs_dir, f"{_PREFS_FILENAME}_templates")


def get_template_resources_dir():
    """Gets the auto rigger template resources directory.

    Returns:
        str: Auto rigger template resources directory.
    """
    prefs_dir = core_prefs.Prefs(_PREFS_FILENAME).get_dir_path()
    return os.path.join(prefs_dir, f"{_PREFS_FILENAME}_resources")


def get_package_template_source_dir():
    """Gets the package-provided auto rigger template directory.

    Returns:
        str: Path to the package template directory.
    """
    tool_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tool_dir, "templates", "package_templates")


def get_package_template_resources_dir():
    """Gets the package-provided auto rigger template resources directory.

    Returns:
        str: Path to the package template resources directory.
    """
    tool_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tool_dir, "templates", "package_resources")


TEMPLATE_SOURCE_DIR = get_template_source_dir()
TEMPLATE_RESOURCES_DIR = get_template_resources_dir()
PACKAGE_TEMPLATE_SOURCE_DIR = get_package_template_source_dir()
PACKAGE_TEMPLATE_RESOURCES_DIR = get_package_template_resources_dir()


def get_project_template_data(rig_project):
    """Gets a project serialization payload configured for use as a template.

    The current project is not modified. Its project directory is reset so a
    project created from the template can establish its own working directory.

    Args:
        rig_project (RigProject): Project to serialize as a template.

    Returns:
        dict or None: Template-ready project data, or None when the project is
        invalid.
    """
    if not isinstance(rig_project, tools_rig_frm.RigProject):
        logging.warning("Unable to create template data. Invalid rig project.")
        return

    template_data = copy.deepcopy(rig_project.get_project_as_dict())
    preferences = template_data.get("preferences", {})
    if not isinstance(preferences, dict):
        preferences = {}
        template_data["preferences"] = preferences
    preferences["project_dir"] = ""
    return template_data


def get_project_resource_source_dir(rig_project):
    """Gets a saved project's configured resource directory when available.

    A project must have an existing project file before its directory can be
    considered for template resources. This prevents an unsaved project's
    default path from resolving against the current working directory.

    Args:
        rig_project (RigProject): Project whose resource directory is queried.

    Returns:
        str: Absolute resource directory, or an empty string when unavailable.
    """
    if not isinstance(rig_project, tools_rig_frm.RigProject):
        return ""

    project_file_dir = rig_project.get_project_file_dir_path()
    if not project_file_dir:
        return ""

    project_dir = rig_project.get_project_dir_path(parse_vars=True)
    if not project_dir or "{" in project_dir or "}" in project_dir:
        return ""

    if not os.path.isabs(project_dir):
        project_dir = os.path.join(project_file_dir, project_dir)

    project_dir = os.path.normpath(project_dir)
    if not os.path.isdir(project_dir):
        return ""
    return project_dir


def project_directory_has_resources(rig_project):
    """Determines whether a saved project directory has template resources.

    The rig project file itself is ignored. Any other file or subdirectory is
    considered a resource, including an empty subdirectory.

    Args:
        rig_project (RigProject): Project whose directory is checked.

    Returns:
        bool: True when resource content is available to copy.
    """
    source_dir = get_project_resource_source_dir(rig_project)
    if not source_dir:
        return False

    project_file_path = os.path.normcase(os.path.abspath(str(rig_project.project_file_path)))
    for root_dir, directory_names, file_names in os.walk(source_dir):
        if directory_names:
            return True
        for file_name in file_names:
            file_path = os.path.normcase(os.path.abspath(os.path.join(root_dir, file_name)))
            if file_path != project_file_path:
                return True
    return False


def copy_project_resources(rig_project, target_dir, overwrite=False):
    """Copies a saved project's resources without copying its project file.

    Existing files are retained by default. The target must not be inside the
    source project directory, preventing a recursive self-copy.

    Args:
        rig_project (RigProject): Project whose resources are copied.
        target_dir (str): Destination directory for the template resources.
        overwrite (bool, optional): Whether existing resource files are
            replaced. Defaults to False.

    Returns:
        dict: Copy counts with ``copied`` and ``skipped`` keys, or None when
        the source or target is invalid.
    """
    source_dir = get_project_resource_source_dir(rig_project)
    if (
        not source_dir
        or not isinstance(target_dir, str)
        or not target_dir
        or not os.path.isabs(target_dir)
    ):
        return

    target_dir = os.path.normpath(os.path.abspath(target_dir))
    try:
        if os.path.commonpath([source_dir, target_dir]) == source_dir:
            logging.warning("Unable to copy template resources into the project directory.")
            return
    except ValueError:
        pass

    project_file_path = os.path.normcase(os.path.abspath(str(rig_project.project_file_path)))
    copy_results = {"copied": 0, "skipped": 0}
    try:
        for root_dir, directory_names, file_names in os.walk(source_dir):
            relative_dir = os.path.relpath(root_dir, source_dir)
            destination_dir = target_dir if relative_dir == os.curdir else os.path.join(target_dir, relative_dir)
            os.makedirs(destination_dir, exist_ok=True)

            for directory_name in directory_names:
                os.makedirs(os.path.join(destination_dir, directory_name), exist_ok=True)

            for file_name in file_names:
                source_file = os.path.join(root_dir, file_name)
                if os.path.normcase(os.path.abspath(source_file)) == project_file_path:
                    continue

                target_file = os.path.join(destination_dir, file_name)
                if os.path.exists(target_file) and not overwrite:
                    copy_results["skipped"] += 1
                    continue

                shutil.copy2(source_file, target_file)
                copy_results["copied"] += 1
    except OSError as exception:
        logging.warning(f"Unable to copy template resources. Issue: {exception}")
        return
    return copy_results


class RigTemplates:
    # Icons
    icon_python = ui_res_lib.Icon.ui_templates_python
    icon_files = ui_res_lib.Icon.ui_templates
    icon_package_files = ui_res_lib.Icon.ui_templates_package

    # Python Templates
    TemplateBiped = tools_templates_biped.create_template_biped
    TemplateGenericRoot = tools_template_root.create_template_generic_root
    # File Templates (Auto Populated from Directory)
    file_templates = {}
    package_file_templates = {}

    def __init__(self, include_package_templates=False):
        """Populates user and optional package file templates.

        Args:
            include_package_templates (bool, optional): Whether package templates
                should also be loaded. Defaults to False.
        """
        RigTemplates.file_templates = {}
        RigTemplates.package_file_templates = {}
        if os.path.isdir(TEMPLATE_SOURCE_DIR):
            self.populate_with_template_files(folder_path=TEMPLATE_SOURCE_DIR)
        else:
            sys.stdout.write(f"Template source directory '{TEMPLATE_SOURCE_DIR}' not found. Skipping.\n")
        if include_package_templates and os.path.isdir(PACKAGE_TEMPLATE_SOURCE_DIR):
            self.populate_with_template_files(
                folder_path=PACKAGE_TEMPLATE_SOURCE_DIR,
                template_resources_dir=PACKAGE_TEMPLATE_RESOURCES_DIR,
                template_store=RigTemplates.package_file_templates,
            )

    @staticmethod
    def get_dict_templates(include_py_templates=True, include_file_templates=True, include_package_templates=False):
        """
        Gets all available modules as a dictionary. Key is the name of the module and value is the class.
        Args:
            include_py_templates (bool, optional): If True python templates will be included.
            include_file_templates (bool, optional): If True file templates will be included. (from source folder)
            include_package_templates (bool, optional): If True package file
                templates will be included. Defaults to False.
        Returns:
            dict: Dictionary where the key is the name of the module and value is the class.
                  e.g. 'ModuleBipedArm': <class 'ModuleBipedArm'>
        """
        _templates = {}
        if include_py_templates:
            _templates.update(vars(RigTemplates))
        if include_file_templates:
            _templates.update(RigTemplates.file_templates)
        if include_package_templates:
            _templates.update(RigTemplates.package_file_templates)
        callable_attributes = {
            name: value
            for name, value in _templates.items()
            if isinstance(value, types.FunctionType) and not name.startswith("_")
        }
        return callable_attributes

    @staticmethod
    def get_templates(include_py_templates=True, include_file_templates=True, include_package_templates=False):
        """
        Gets the available template functions. The output of these callable functions is a RigProject.
        Args:
            include_py_templates (bool, optional): If True python templates will be included.
            include_file_templates (bool, optional): If True file templates will be included. (from source folder)
            include_package_templates (bool, optional): If True package file
                templates will be included. Defaults to False.
        Returns:
            list: A list of template functions, these are of the type callable.
                  When called, they produce a RigProject describing the template.
        """
        # if include_py_templates:
        #     _templates =
        return list(
            RigTemplates.get_dict_templates(
                include_py_templates, include_file_templates, include_package_templates
            ).values()
        )

    @staticmethod
    def get_template_names(include_py_templates=True, include_file_templates=True, include_package_templates=False):
        """
        Gets the name of all available templates.
        Args:
            include_py_templates (bool, optional): If True python templates will be included.
            include_file_templates (bool, optional): If True file templates will be included. (from source folder)
            include_package_templates (bool, optional): If True package file
                templates will be included. Defaults to False.
        Returns:
            list: A list of template names (strings)
        """
        return list(
            RigTemplates.get_dict_templates(
                include_py_templates, include_file_templates, include_package_templates
            ).keys()
        )

    @staticmethod
    def populate_with_template_files(folder_path, template_resources_dir=None, template_store=None):
        """Populates `RigTemplateFunctions` with functions that load template files.

        This method reads all files in the given folder (or the default folder if `folder_path`
        is `None`) and adds a new function to `RigTemplateFunctions` for each template file.
        Each function loads a project from the corresponding file and cleans up its load path.

        Args:
            folder_path (str): The folder path where template files are stored.
                Defaults to `RigTemplateFiles.folder_path` if not provided.
            template_resources_dir (str, optional): Directory containing resources
                associated with the template files. Defaults to the user template
                resources directory.
            template_store (dict, optional): Dictionary receiving the generated
                template loaders. Defaults to the user template store.

        """
        if template_resources_dir is None:
            template_resources_dir = TEMPLATE_RESOURCES_DIR
        if template_store is None:
            template_store = RigTemplates.file_templates

        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(tools_rig_const.RiggerConstants.PROJECT_EXTENSION):
                # Remove the extension and sanitize the name if necessary
                variable_name = os.path.splitext(filename)[0]
                variable_name = variable_name.replace("-", "_").replace(" ", "_")

                file_path = os.path.join(folder_path, filename)

                # Bind file_path to the current iteration using a default argument
                def file_loader(dir_path=file_path):
                    """
                    Helper Sub-function used to initialize rig project from template.
                    Reads template projects into a RigProject object and clears it to act as template.
                    Args:
                        dir_path (str): Path to the template JSON file.

                    Returns:
                        RigProject: Initialized project object based on the template.
                    """
                    _project = tools_rig_frm.RigProject()
                    data = core_io.read_json_dict(dir_path)
                    _project.read_data_from_dict(data)
                    _project.set_project_dir_path("")  # No project path (template)
                    _project.set_uuid(core_uuid.generate_uuid(short=True, short_length=6))  # Randomize UUID
                    try:
                        resource_path = get_template_resource_path(
                            os.path.splitext(os.path.basename(dir_path))[0], template_resources_dir
                        )
                        if resource_path:
                            project_path = open_resource_copy_dialog(resource_path)
                            if project_path and os.path.isdir(project_path):
                                _project.set_project_dir_path(project_path)  # Project was set as expected.
                    except Exception as e:
                        logging.warning(f"Fail to detect potential template resources. Issue: {e}")
                    return _project

                template_store[variable_name] = file_loader


def get_template_resource_path(template_name, template_resources_dir=None):
    """
    Detects if a template has resources and returns the path to the template resource folder if that's the case.

    Args:
        template_name (str): Name of the template used to determine if resource is available.
        template_resources_dir (str, optional): Directory containing template
            resource folders. Defaults to the user template resources directory.

    Returns:
        str: A path to the template resource folder (when available)
    """
    if template_resources_dir is None:
        template_resources_dir = TEMPLATE_RESOURCES_DIR
    if not os.path.exists(template_resources_dir) or not os.path.isdir(template_resources_dir):
        return

    for resource_dir in os.listdir(template_resources_dir):
        if resource_dir.lower() == template_name.lower():
            return os.path.join(template_resources_dir, resource_dir)


def open_resource_copy_dialog(resource_path):
    """
    Presents the user with a dialog asking to copy or ignore extra resources.
    If a project path is set, resources are then copied to the provided path.
    Args:
        resource_path (str): The source path (where extra files come from)
    Returns:
        str: A path to the set project or None if the operation was canceled.
    """
    # Show Save Dialog
    import gt.ui.qt_import as ui_qt

    message_box = ui_qt.QtWidgets.QMessageBox()
    message_box.setWindowTitle("Template Resources Detected!")
    message_box.setText(
        "The selected template has extra resource files. \n"
        "Would you like to set a project path and copy these files into it?"
    )

    # Add custom buttons for Save, Don't Save, and Cancel
    save_button = message_box.addButton("Set Project Path", ui_qt.QtWidgets.QMessageBox.AcceptRole)
    message_box.addButton("Ignore Resources", ui_qt.QtWidgets.QMessageBox.DestructiveRole)

    # Execute the message box and get the user response
    message_box.exec_()

    # Handle button clicks
    if message_box.clickedButton() == save_button:
        _target_path = ui_file_dialog.file_dialog(
            caption="Set Rig Project Location",
            write_mode=False,
            dir_only=True,
            ok_caption="Set Project Path",
            cancel_caption="Cancel",
        )
        if _target_path and os.path.isdir(_target_path):
            core_io.copy_directory(source_path=resource_path, target_path=_target_path, verbose=True)
            return _target_path
        else:
            sys.stdout.write(f"No project path selected. Resources ignored.")


if __name__ == "__main__":
    import pprint

    # _initialized_rig_templates = RigTemplates()
    # pprint.pprint(RigTemplates.get_dict_templates())
    # pprint.pprint(RigTemplates.get_template_names())
    # pprint.pprint(RigTemplates.get_templates())

