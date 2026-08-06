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
import types
import sys
import os

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


TEMPLATE_SOURCE_DIR = get_template_source_dir()
TEMPLATE_RESOURCES_DIR = get_template_resources_dir()

class RigTemplates:
    # Icons
    icon_python = ui_res_lib.Icon.ui_templates_python
    icon_files = ui_res_lib.Icon.ui_templates

    # Python Templates
    TemplateBiped = tools_templates_biped.create_template_biped
    TemplateGenericRoot = tools_template_root.create_template_generic_root
    # File Templates (Auto Populated from Directory)
    file_templates = {}

    def __init__(self):
        """Clean and Retrieve file templates (re-populate class with file templates)"""
        RigTemplates.file_templates = {}
        if os.path.isdir(TEMPLATE_SOURCE_DIR):
            self.populate_with_template_files(folder_path=TEMPLATE_SOURCE_DIR)
        else:
            sys.stdout.write(f"Template source directory '{TEMPLATE_SOURCE_DIR}' not found. Skipping.\n")

    @staticmethod
    def get_dict_templates(include_py_templates=True, include_file_templates=True):
        """
        Gets all available modules as a dictionary. Key is the name of the module and value is the class.
        Args:
            include_py_templates (bool, optional): If True python templates will be included.
            include_file_templates (bool, optional): If True file templates will be included. (from source folder)
        Returns:
            dict: Dictionary where the key is the name of the module and value is the class.
                  e.g. 'ModuleBipedArm': <class 'ModuleBipedArm'>
        """
        _templates = {}
        if include_py_templates:
            _templates.update(vars(RigTemplates))
        if include_file_templates:
            _templates.update(RigTemplates.file_templates)
        callable_attributes = {
            name: value
            for name, value in _templates.items()
            if isinstance(value, types.FunctionType) and not name.startswith("_")
        }
        return callable_attributes

    @staticmethod
    def get_templates(include_py_templates=True, include_file_templates=True):
        """
        Gets the available template functions. The output of these callable functions is a RigProject.
        Args:
            include_py_templates (bool, optional): If True python templates will be included.
            include_file_templates (bool, optional): If True file templates will be included. (from source folder)
        Returns:
            list: A list of template functions, these are of the type callable.
                  When called, they produce a RigProject describing the template.
        """
        # if include_py_templates:
        #     _templates =
        return list(RigTemplates.get_dict_templates(include_py_templates, include_file_templates).values())

    @staticmethod
    def get_template_names(include_py_templates=True, include_file_templates=True):
        """
        Gets the name of all available templates.
        Args:
            include_py_templates (bool, optional): If True python templates will be included.
            include_file_templates (bool, optional): If True file templates will be included. (from source folder)
        Returns:
            list: A list of template names (strings)
        """
        return list(RigTemplates.get_dict_templates(include_py_templates, include_file_templates).keys())

    @staticmethod
    def populate_with_template_files(folder_path):
        """Populates `RigTemplateFunctions` with functions that load template files.

        This method reads all files in the given folder (or the default folder if `folder_path`
        is `None`) and adds a new function to `RigTemplateFunctions` for each template file.
        Each function loads a project from the corresponding file and cleans up its load path.

        Args:
            folder_path (str): The folder path where template files are stored.
                Defaults to `RigTemplateFiles.folder_path` if not provided.

        """
        for filename in os.listdir(folder_path):
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
                        resource_path = get_template_resource_path(os.path.splitext(os.path.basename(dir_path))[0])
                        if resource_path:
                            project_path = open_resource_copy_dialog(resource_path)
                            if project_path and os.path.isdir(project_path):
                                _project.set_project_dir_path(project_path)  # Project was set as expected.
                    except Exception as e:
                        logging.warning(f"Fail to detect potential template resources. Issue: {e}")
                    return _project

                RigTemplates.file_templates[variable_name] = file_loader


def get_template_resource_path(template_name):
    """
    Detects if a template has resources and returns the path to the template resource folder if that's the case.

    Args:
        template_name (str): Name of the template used to determine if resource is available.

    Returns:
        str: A path to the template resource folder (when available)
    """
    if not os.path.exists(TEMPLATE_RESOURCES_DIR) or not os.path.isdir(TEMPLATE_RESOURCES_DIR):
        return

    for resource_dir in os.listdir(TEMPLATE_RESOURCES_DIR):
        if resource_dir.lower() == template_name.lower():
            return os.path.join(TEMPLATE_RESOURCES_DIR, resource_dir)


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

