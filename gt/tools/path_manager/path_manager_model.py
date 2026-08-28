"""Maya runtime and pure path logic for Path Manager."""

import logging
import os
import re

from gt.tools.path_manager import path_manager_constants as constants


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_maya_cmds():
    """Gets maya.cmds only when Maya runtime work is requested.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


def get_path_basename(path):
    """Gets a basename without resolving a relative path against the CWD.

    Args:
        path (str): Path to process.

    Returns:
        str: Final file or directory name, or an empty string.
    """
    normalized_path = str(path or "").replace("\\", "/").rstrip("/")
    if not normalized_path:
        return ""
    return normalized_path.rsplit("/", 1)[-1]


def build_path_pattern(path):
    """Builds a filename pattern for UDIM and frame-token source paths.

    Args:
        path (str): Source path containing an optional token.

    Returns:
        Pattern or None: Compiled matcher when a supported token is present.
    """
    filename = get_path_basename(path)
    if not filename:
        return None
    pattern = re.escape(filename)
    has_token = False
    for token, expression in (("<UDIM>", r"\d{4}"), ("<f>", r"\d+"), ("<F>", r"\d+")):
        escaped_token = re.escape(token)
        if escaped_token in pattern:
            pattern = pattern.replace(escaped_token, expression)
            has_token = True
    if not has_token:
        return None
    return re.compile(f"^{pattern}$")


def find_matching_path(candidate_paths, source_path):
    """Finds a matching indexed path for a source path.

    Exact filenames are preferred. UDIM and frame-token paths fall back to a
    token-aware filename matcher.

    Args:
        candidate_paths (list): Paths available below a selected search root.
        source_path (str): Original path that should be located.

    Returns:
        str or None: First matching candidate path, when found.
    """
    source_name = get_path_basename(source_path)
    if not source_name:
        return None
    for candidate_path in candidate_paths:
        if get_path_basename(candidate_path) == source_name:
            return candidate_path
    pattern = build_path_pattern(source_path)
    if not pattern:
        return None
    for candidate_path in candidate_paths:
        if pattern.match(get_path_basename(candidate_path)):
            return candidate_path
    return None


class PathManagerModel:
    """Collects, updates, and repairs Maya file paths."""

    def get_path_items(self):
        """Collects supported Maya nodes and the paths they own.

        Returns:
            list: Path-item dictionaries ordered by Maya node discovery.
        """
        cmds = get_maya_cmds()
        available_node_types = set(cmds.ls(nodeTypes=True) or [])
        node_names = []
        for node_type in constants.PATH_NODE_CONFIG:
            if node_type == "reference":
                continue
            if node_type != "file" and node_type not in available_node_types:
                continue
            try:
                node_names.extend(cmds.ls(type=node_type) or [])
            except RuntimeError as exception:
                logger.debug("Unable to list %s nodes. Issue: %s", node_type, exception)
        try:
            node_names.extend(cmds.ls(rf=True) or [])
        except RuntimeError as exception:
            logger.debug("Unable to list reference nodes. Issue: %s", exception)

        reference_paths = self.get_reference_paths()
        path_items = []
        seen_nodes = set()
        for node_name in node_names:
            if node_name in seen_nodes:
                continue
            seen_nodes.add(node_name)
            path_item = self.get_path_item(node_name, reference_paths=reference_paths)
            if path_item:
                path_items.append(path_item)
        return path_items

    def get_path_item(self, node_name, reference_paths=None):
        """Builds table-ready data for one Maya path node.

        Args:
            node_name (str): Maya node to inspect.
            reference_paths (dict, optional): Reference-node to path mapping.

        Returns:
            dict or None: Path item data, or None when the node is unsupported.
        """
        cmds = get_maya_cmds()
        if not cmds.objExists(node_name):
            return None
        node_type = cmds.objectType(node_name) or ""
        config = constants.PATH_NODE_CONFIG.get(node_type)
        if not config:
            return None
        path = self.get_node_path(node_name, node_type, reference_paths=reference_paths)
        is_directory = bool(config.get("is_directory"))
        is_valid = os.path.isdir(path) if is_directory else os.path.isfile(path)
        return {
            "node_name": node_name,
            "node_type": node_type,
            "display_type": config["display_name"],
            "icon": config["icon"],
            "attribute": config["attribute"],
            "path": path,
            "is_directory": is_directory,
            "is_valid": is_valid,
        }

    def get_node_path(self, node_name, node_type, reference_paths=None):
        """Gets the path represented by a Maya node.

        Args:
            node_name (str): Maya node to inspect.
            node_type (str): Maya node type.
            reference_paths (dict, optional): Reference-node to path mapping.

        Returns:
            str: Current path, or an empty string when it cannot be read.
        """
        cmds = get_maya_cmds()
        config = constants.PATH_NODE_CONFIG.get(node_type) or {}
        try:
            if node_type == "cacheFile":
                cache_path = cmds.getAttr(f"{node_name}.cachePath") or ""
                cache_name = cmds.getAttr(f"{node_name}.cacheName") or ""
                return os.path.join(cache_path, f"{cache_name}.xml")
            if node_type == "reference":
                reference_paths = reference_paths or self.get_reference_paths()
                return str(reference_paths.get(node_name) or "")
            return str(cmds.getAttr(f"{node_name}{config.get('attribute', '')}") or "")
        except (RuntimeError, TypeError, ValueError) as exception:
            logger.debug("Unable to read a path from %s. Issue: %s", node_name, exception)
            return ""

    def get_reference_paths(self):
        """Gets reference file paths without requiring a loaded reference.

        Returns:
            dict: Mapping of Maya reference node names to paths.
        """
        try:
            import maya.OpenMaya as open_maya

            iterator = open_maya.MItDependencyNodes(open_maya.MFn.kReference)
            reference_paths = {}
            while not iterator.isDone():
                reference_object = iterator.thisNode()
                reference_function = open_maya.MFnReference(reference_object)
                reference_name = reference_function.absoluteName().lstrip(":")
                reference_paths[reference_name] = reference_function.fileName(False, False, False)
                iterator.next()
            return reference_paths
        except (ImportError, RuntimeError, TypeError) as exception:
            logger.debug("Unable to collect reference paths. Issue: %s", exception)
            return {}

    def select_node(self, node_name):
        """Selects an existing Maya node.

        Args:
            node_name (str): Node to select.

        Returns:
            bool: True when the node was selected.
        """
        cmds = get_maya_cmds()
        if not node_name or not cmds.objExists(node_name):
            return False
        cmds.select(node_name)
        return True

    def rename_node(self, node_name, new_name):
        """Renames a Maya node and returns Maya's final unique name.

        Args:
            node_name (str): Node to rename.
            new_name (str): Requested new name.

        Returns:
            tuple: Success flag, final node name, and a user-facing message.
        """
        cmds = get_maya_cmds()
        requested_name = str(new_name or "").strip()
        if not requested_name:
            return False, node_name, "A node name cannot be empty."
        if requested_name == node_name:
            return True, node_name, ""
        try:
            actual_name = cmds.rename(node_name, requested_name)
            return True, actual_name, ""
        except RuntimeError as exception:
            return False, node_name, f"Unable to rename '{node_name}': {exception}"

    def set_path(self, path_item, new_path):
        """Updates a Maya node path using its appropriate runtime operation.

        Args:
            path_item (dict): Current path item data.
            new_path (str): New path value.

        Returns:
            tuple: Success flag and a user-facing message.
        """
        node_name = path_item.get("node_name")
        node_type = path_item.get("node_type")
        new_path = str(new_path or "")
        if not node_name:
            return False, "The selected row does not identify a Maya node."
        if node_type == "cacheFile":
            return self._set_cache_file_path(node_name, new_path)
        if node_type == "reference":
            return self._set_reference_path(node_name, new_path)
        cmds = get_maya_cmds()
        try:
            cmds.setAttr(f"{node_name}{path_item.get('attribute', '')}", new_path, type="string")
            return True, ""
        except RuntimeError as exception:
            return False, f"Unable to update '{node_name}': {exception}"

    def replace_paths(self, search_text, replace_text):
        """Replaces text in all current paths.

        Args:
            search_text (str): Required text to find.
            replace_text (str): Replacement text, which may be empty.

        Returns:
            tuple: Updated count, skipped count, and an optional message.
        """
        search_text = str(search_text or "")
        if not search_text:
            return 0, 0, "The search text cannot be empty."
        updated_count = 0
        skipped_count = 0
        for path_item in self.get_path_items():
            old_path = path_item.get("path") or ""
            if search_text not in old_path:
                continue
            new_path = old_path.replace(search_text, str(replace_text or ""))
            success, _ = self.set_path(path_item, new_path)
            if success:
                updated_count += 1
            else:
                skipped_count += 1
        return updated_count, skipped_count, ""

    def repair_paths(self, search_directory):
        """Repairs invalid paths by finding matching names below a directory.

        Args:
            search_directory (str): Existing folder to search recursively.

        Returns:
            tuple: Repaired count, skipped count, and an optional message.
        """
        search_directory = str(search_directory or "")
        if not os.path.isdir(search_directory):
            return 0, 0, "The search directory does not exist. Select a valid directory and try again."
        file_paths, directory_paths = self._index_search_directory(search_directory)
        repaired_count = 0
        skipped_count = 0
        for path_item in self.get_path_items():
            if path_item.get("is_valid"):
                continue
            candidates = directory_paths if path_item.get("is_directory") else file_paths
            resolved_path = find_matching_path(candidates, path_item.get("path"))
            if not resolved_path:
                skipped_count += 1
                continue
            success, _ = self.set_path(path_item, resolved_path)
            if success:
                repaired_count += 1
            else:
                skipped_count += 1
        return repaired_count, skipped_count, ""

    @staticmethod
    def _index_search_directory(search_directory):
        """Indexes files and folders below a search directory once.

        Args:
            search_directory (str): Existing directory to traverse.

        Returns:
            tuple: Lists of file paths and directory paths.
        """
        file_paths = []
        directory_paths = []
        for root_directory, directory_names, file_names in os.walk(search_directory):
            directory_paths.extend(os.path.join(root_directory, name) for name in directory_names)
            file_paths.extend(os.path.join(root_directory, name) for name in file_names)
        return file_paths, directory_paths

    @staticmethod
    def _set_cache_file_path(node_name, new_path):
        """Updates a cacheFile node from an XML cache file path.

        Args:
            node_name (str): cacheFile node to update.
            new_path (str): Path to a cache XML file.

        Returns:
            tuple: Success flag and a user-facing message.
        """
        normalized_path = os.path.normpath(new_path)
        if not os.path.isfile(normalized_path):
            return False, "Cache paths must point to an existing XML file."
        cache_name = os.path.splitext(os.path.basename(normalized_path))[0]
        cache_directory = os.path.dirname(normalized_path)
        cmds = get_maya_cmds()
        try:
            cmds.setAttr(f"{node_name}.cachePath", cache_directory, type="string")
            cmds.setAttr(f"{node_name}.cacheName", cache_name, type="string")
            return True, ""
        except RuntimeError as exception:
            return False, f"Unable to update cache '{node_name}': {exception}"

    @staticmethod
    def _set_reference_path(node_name, new_path):
        """Loads an existing file as a reference node's new source path.

        Args:
            node_name (str): Reference node to update.
            new_path (str): Existing reference file path.

        Returns:
            tuple: Success flag and a user-facing message.
        """
        if not os.path.isfile(new_path):
            return False, "Reference paths must point to an existing file."
        cmds = get_maya_cmds()
        try:
            cmds.file(new_path, loadReference=node_name)
            return True, ""
        except RuntimeError as exception:
            return False, f"Unable to update reference '{node_name}': {exception}"
