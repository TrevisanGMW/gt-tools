"""Shared Auto Rigger path-information helpers."""

import os

import gt.ui.python_output_view as ui_python_output_view


def build_path_information_lines(configured_path, parsed_path, exists=False, is_dir=False, is_file=False):
    """Builds detailed path information for the output window.

    Args:
        configured_path (str): Unresolved path stored by the tool.
        parsed_path (str): Resolved path value.
        exists (bool, optional): Whether the parsed path exists.
        is_dir (bool, optional): Whether the parsed path is a directory.
        is_file (bool, optional): Whether the parsed path is a file.

    Returns:
        list: Text lines describing the path.
    """
    return [
        "Configured Path:",
        str(configured_path or ""),
        "",
        "Parsed Path:",
        str(parsed_path or ""),
        "",
        f"Exists: {bool(exists)}",
        f"Directory: {bool(is_dir)}",
        f"File: {bool(is_file)}",
    ]


def list_files_from_path(path):
    """Lists files represented by a file or directory path.

    Args:
        path (str): File or directory path to inspect.

    Returns:
        list: Sorted normalized file paths.
    """
    if not path:
        return []
    normalized_path = os.path.normpath(path)
    if os.path.isfile(normalized_path):
        return [normalized_path]
    if not os.path.isdir(normalized_path):
        return []
    file_paths = []
    for root_dir, _, file_names in os.walk(normalized_path):
        for file_name in file_names:
            file_path = os.path.join(root_dir, file_name)
            if os.path.isfile(file_path):
                file_paths.append(os.path.normpath(file_path))
    return sorted(set(file_paths))


def show_path_information(parent, configured_path, parsed_path, title="Path Information"):
    """Shows path details and discovered files in a highlighted text window.

    Args:
        parent (QWidget): Parent widget for the output window.
        configured_path (str): Unresolved path stored by the tool.
        parsed_path (str): Resolved path value.
        title (str, optional): Window title.

    Returns:
        PythonOutputView: Created path-information window.
    """
    parsed_path = str(parsed_path or "")
    exists = os.path.exists(parsed_path)
    is_dir = os.path.isdir(parsed_path)
    is_file = os.path.isfile(parsed_path)
    info_lines = build_path_information_lines(
        configured_path=configured_path,
        parsed_path=parsed_path,
        exists=exists,
        is_dir=is_dir,
        is_file=is_file,
    )
    file_paths = list_files_from_path(parsed_path)
    output_window = ui_python_output_view.PythonOutputView(parent=parent, editable=False)
    output_window.setWindowTitle(title)
    output_lines = [str(line) for line in info_lines]
    output_lines.extend(["", f"Count: {len(file_paths)}", ""])
    output_lines.extend(file_paths or ["No files found."])
    output_window.set_python_output_text("\n".join(output_lines))
    output_window.show()
    return output_window
