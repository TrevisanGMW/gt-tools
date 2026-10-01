"""Updates userPrefs.mel and session variables for playback defaults and valid file dialog URLs."""

import os
import re
import maya.cmds as cmds


# Editable preference defaults
PLAYBACK_VARS = {
    "playbackMaxDefault": 120,
    "playbackMaxRange": 120,
    "playbackMaxRangeDefault": 120,
    "playbackMin": 0,
    "playbackMinDefault": 1,
    "playbackMinRange": 0,
    "playbackMinRangeDefault": 1
}

CACHED_PLAYBACK_VARS = {
    "cachedPlaybackEnable": 0
}

# Custom Path Example
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop").replace("\\", "/")

SIDEBAR_URLS = [
    DESKTOP_PATH,
    # Add existing absolute directory paths here to show them in the favorites box.
]


def get_valid_sidebar_path(path):
    """Gets a normalized Maya file-dialog sidebar directory path.

    Args:
        path (str): Requested directory path.

    Returns:
        str: Existing absolute directory with forward slashes, or an empty string.
    """
    if not isinstance(path, str):
        return ""
    expanded_path = os.path.expanduser(os.path.expandvars(path.strip()))
    if not expanded_path:
        return ""
    if re.match(r"^[a-zA-Z]:[^/\\]", expanded_path):
        return ""
    if not os.path.isabs(expanded_path):
        return ""
    normalized_path = os.path.normpath(os.path.abspath(expanded_path))
    if not os.path.isdir(normalized_path):
        return ""
    return normalized_path.replace("\\", "/")


def get_sidebar_path_key(path):
    """Builds a canonical key for comparing valid sidebar directory paths.

    Args:
        path (str): Sidebar directory path.

    Returns:
        str: Case-normalized path key, or an empty string for an invalid path.
    """
    valid_path = get_valid_sidebar_path(path)
    if not valid_path:
        return ""
    return os.path.normcase(valid_path).replace("\\", "/")


def get_valid_sidebar_urls(paths):
    """Filters sidebar URLs to unique existing absolute directory paths.

    Args:
        paths (list[str]): Requested sidebar directory paths.

    Returns:
        list[str]: Valid normalized sidebar paths in their original order.
    """
    valid_urls = []
    known_path_keys = set()
    for path in paths if isinstance(paths, (list, tuple)) else []:
        valid_path = get_valid_sidebar_path(path)
        path_key = get_sidebar_path_key(valid_path)
        if not path_key or path_key in known_path_keys:
            continue
        known_path_keys.add(path_key)
        valid_urls.append(valid_path)
    return valid_urls


VALID_SIDEBAR_URLS = get_valid_sidebar_urls(SIDEBAR_URLS)


# Update the userPrefs.mel file on disk
prefs_dir = cmds.internalVar(userPrefDir=True)
prefs_file = os.path.join(prefs_dir, "userPrefs.mel")

if os.path.exists(prefs_file):
    with open(prefs_file, 'r') as f:
        lines = f.readlines()

    new_lines = []
    found_vars = set()
    found_urls = set()

    for line in lines:
        modified = False
        
        # Playback variables
        for key, value in PLAYBACK_VARS.items():
            pattern = rf'^(\s*-fv\s+"{key}"\s+)([\d\.-]+)(.*)'
            match = re.match(pattern, line)
            if match:
                new_lines.append(f'{match.group(1)}{value}{match.group(3)}\n')
                found_vars.add(key)
                modified = True
                break
        if modified: continue

        # Cached playback variables
        for key, value in CACHED_PLAYBACK_VARS.items():
            pattern = rf'^(\s*-iv\s+"{key}"\s+)([\d-]+)(.*)'
            match = re.match(pattern, line)
            if match:
                new_lines.append(f'{match.group(1)}{value}{match.group(3)}\n')
                found_vars.add(key)
                modified = True
                break
        if modified: continue

        # File dialog sidebar URLs
        url_pattern = r'^\s*-sva\s+"CustomFileDialogSidebarUrls"\s+"(.*?)"'
        match = re.match(url_pattern, line)
        if match:
            path_key = get_sidebar_path_key(match.group(1))
            if path_key:
                found_urls.add(path_key)

        new_lines.append(line)

    # Append missing variables
    missing_playback = set(PLAYBACK_VARS) - found_vars
    missing_cached = set(CACHED_PLAYBACK_VARS) - found_vars
    missing_urls = [
        url for url in VALID_SIDEBAR_URLS if get_sidebar_path_key(url) not in found_urls
    ]

    if missing_playback or missing_cached or missing_urls:
        new_lines.append("\n// Appended by custom setup script\n")
        new_lines.append("optionVar\n")
        for key in missing_playback:
            new_lines.append(f' -fv "{key}" {PLAYBACK_VARS[key]}\n')
        for key in missing_cached:
            new_lines.append(f' -iv "{key}" {CACHED_PLAYBACK_VARS[key]}\n')
        for url in missing_urls:
            new_lines.append(f' -sva "CustomFileDialogSidebarUrls" "{url}"\n')
        new_lines.append(";\n")

    with open(prefs_file, 'w') as f:
        f.writelines(new_lines)


# Update current session memory
for key, value in PLAYBACK_VARS.items():
    cmds.optionVar(floatValue=(key, float(value)))
    
for key, value in CACHED_PLAYBACK_VARS.items():
    cmds.optionVar(intValue=(key, int(value)))

current_urls = []
if cmds.optionVar(exists="CustomFileDialogSidebarUrls"):
    current_urls = cmds.optionVar(q="CustomFileDialogSidebarUrls") or []
if isinstance(current_urls, str):
    current_urls = [current_urls]

current_url_keys = set()
for current_url in current_urls:
    path_key = get_sidebar_path_key(current_url)
    if path_key:
        current_url_keys.add(path_key)
    
for url in VALID_SIDEBAR_URLS:
    path_key = get_sidebar_path_key(url)
    if path_key not in current_url_keys:
        cmds.optionVar(stringValueAppend=("CustomFileDialogSidebarUrls", url))
        current_url_keys.add(path_key)
