import gt.core.session as core_session
import gt.ui.qt_import as ui_qt


def file_dialog(
    caption="Open File",
    parent=None,
    write_mode=False,
    starting_directory=None,
    file_filter="All Files (*);;",
    dir_only=False,
    ok_caption="Open",
    cancel_caption="Cancel",
    multiple_files=False,
):
    """
    Shows a file dialog to open/select or write a file or directory.

    Args:
        ok_caption (str): Caption for the OK button. (Only when in Maya)
        cancel_caption (str): Caption for the Cancel button. (Only when in Maya)
        caption (str): Caption for the file dialog window. (Title of the window)
        write_mode (bool): If True, the dialog allows selecting or writing a file;
                           If False, it allows only selecting/opening.
        starting_directory (str, optional): The initial directory.
        file_filter (str): Filter for file types, separate multiple filters with ";;".
                           e.g., "All Files (*);;JSON Files (*.json)"
        dir_only (bool, optional): If True, the dialog allows selecting directories only.
        parent: Parent widget. Automatically retrieved from context if not provided.
        multiple_files (bool): If True, allows selecting multiple files. The function
                               will return a list of strings instead of a single string.
                               This is ignored if write_mode or dir_only is True.

    Returns:
        str or list[str]: Path to the selected file/directory. If multiple_files is True,
                          returns a list of paths. Returns an empty string or empty list
                          if the dialog is cancelled.
    """
    # Within Maya --------------------------------------------------------------------------
    if core_session.is_script_in_interactive_maya():
        import maya.cmds as cmds

        params = {
            "fileFilter": file_filter,
            "dialogStyle": 2,  # Use a custom file, which is consistent across platforms.
            "fileMode": 1,  # Default to "Open a single file"
            "okCaption": ok_caption,
            "cancelCaption": cancel_caption,
            "caption": caption,
        }

        # Determine File Mode based on arguments
        if write_mode:
            params["fileMode"] = 0  # Write File
        elif dir_only:
            params["fileMode"] = 3  # Select a directory. Use 3 for modern Maya consistency.
        elif multiple_files:
            params["fileMode"] = 4  # Open multiple files

        if starting_directory and isinstance(starting_directory, str):
            params["startingDirectory"] = starting_directory

        # Execute the dialog and process results
        results = cmds.fileDialog2(**params) or []

        if not results:  # User cancelled
            return [] if multiple_files else ""

        if multiple_files:
            return results  # Return the full list of selected files
        else:
            return results[0]  # Maintain original behavior, return first item

    # Outside Maya (Standard Qt) ----------------------------------------------------------
    else:
        options = ui_qt.QtWidgets.QFileDialog.Options()

        params = {
            "parent": parent,
            "caption": caption,
            "directory": starting_directory if starting_directory else "",
            "filter": file_filter,
            "options": options,
        }

        # Determine which dialog to show
        if write_mode and not dir_only:  # Write File
            file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(**params)
            return file_path

        elif dir_only:  # Directory Only
            # The 'filter' argument is not used by getExistingDirectory
            params.pop("filter", None)
            dir_path = ui_qt.QtWidgets.QFileDialog.getExistingDirectory(**params)
            return dir_path

        elif multiple_files:  # Open Multiple Files
            file_paths, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileNames(**params)
            return file_paths

        else:  # Open Single File (default behavior)
            file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(**params)
            return file_path


if __name__ == "__main__":
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        selected_file = file_dialog(file_filter="All Files (*);;JSON Files (*.json)")
        print(selected_file)
