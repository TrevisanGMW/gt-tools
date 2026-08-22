"""Updates userPrefs.mel and session variables for playback defaults, caching, and file dialog URLs."""

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
    # Add more paths here to guarantee they appear in the favorites box.
]


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
        for key, val in PLAYBACK_VARS.items():
            pattern = r'^(\s*-fv\s+"{}"\s+)([\d\.-]+)(.*)'.format(key)
            match = re.match(pattern, line)
            if match:
                new_lines.append(f'{match.group(1)}{val}{match.group(3)}\n')
                found_vars.add(key)
                modified = True
                break
        if modified: continue

        # Cached playback variables
        for key, val in CACHED_PLAYBACK_VARS.items():
            pattern = r'^(\s*-iv\s+"{}"\s+)([\d-]+)(.*)'.format(key)
            match = re.match(pattern, line)
            if match:
                new_lines.append(f'{match.group(1)}{val}{match.group(3)}\n')
                found_vars.add(key)
                modified = True
                break
        if modified: continue

        # File dialog sidebar URLs
        url_pattern = r'^\s*-sva\s+"CustomFileDialogSidebarUrls"\s+"(.*?)"'
        match = re.match(url_pattern, line)
        if match:
            found_urls.add(match.group(1))

        new_lines.append(line)

    # Append missing variables
    missing_playback = set(PLAYBACK_VARS.keys()) - found_vars
    missing_cached = set(CACHED_PLAYBACK_VARS.keys()) - found_vars
    missing_urls = set(SIDEBAR_URLS) - found_urls

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
for k, v in PLAYBACK_VARS.items():
    cmds.optionVar(floatValue=(k, float(v)))
    
for k, v in CACHED_PLAYBACK_VARS.items():
    cmds.optionVar(intValue=(k, int(v)))

current_urls = []
if cmds.optionVar(exists="CustomFileDialogSidebarUrls"):
    current_urls = cmds.optionVar(q="CustomFileDialogSidebarUrls") or []
    
for url in SIDEBAR_URLS:
    if url not in current_urls:
        cmds.optionVar(stringValueAppend=("CustomFileDialogSidebarUrls", url))