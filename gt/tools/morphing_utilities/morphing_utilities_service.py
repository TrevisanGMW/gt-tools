"""Maya runtime service for Morphing Utilities."""

import html
import logging
import re
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class MorphingUtilitiesService:
    """Performs Maya scene operations used by Morphing Utilities."""

    def __init__(self, cmds_module=None):
        """Initializes the service.

        Args:
            cmds_module (module, optional): Maya commands-compatible object for
                tests. When omitted, Maya commands are imported lazily.
        """
        self._cmds = cmds_module

    def _get_cmds(self):
        """Gets Maya commands without importing Maya during module import.

        Returns:
            module: Maya commands module or injected test double.

        Raises:
            RuntimeError: If Maya commands are unavailable.
        """
        if self._cmds is None:
            try:
                from maya import cmds
            except ImportError as exception:
                raise RuntimeError("Morphing Utilities requires Maya commands.") from exception
            self._cmds = cmds
        return self._cmds

    @contextmanager
    def undo_chunk(self, chunk_name="Morphing Utilities"):
        """Groups a scene operation into one Maya undo step.

        Args:
            chunk_name (str): Name shown by Maya's undo system.
        """
        cmds = self._get_cmds()
        opened = False
        try:
            cmds.undoInfo(openChunk=True, chunkName=chunk_name)
            opened = True
            yield
        finally:
            if opened:
                cmds.undoInfo(closeChunk=True, chunkName=chunk_name)

    @contextmanager
    def preserve_selection(self):
        """Restores the Maya selection after a utility operation."""
        cmds = self._get_cmds()
        original_selection = cmds.ls(selection=True) or []
        try:
            yield
        finally:
            try:
                if original_selection:
                    cmds.select(original_selection, replace=True)
                else:
                    cmds.select(clear=True)
            except Exception:
                logger.debug("Unable to restore the Maya selection.", exc_info=True)

    def get_selection(self):
        """Gets the current Maya selection.

        Returns:
            list: Selected object names.
        """
        return self._get_cmds().ls(selection=True) or []

    def select_existing_object(self, object_name):
        """Selects a loaded object if it still exists.

        Args:
            object_name (str): Maya object to select.

        Returns:
            bool: True if the object was selected.
        """
        cmds = self._get_cmds()
        if not object_name or not cmds.objExists(object_name):
            return False
        cmds.select(object_name, replace=True)
        return True

    def get_blendshape_nodes(self, object_name):
        """Finds blendShape nodes in an object's construction history.

        Args:
            object_name (str): Maya object to inspect.

        Returns:
            list: Blend shape node names in history order.
        """
        cmds = self._get_cmds()
        if not object_name or not cmds.objExists(object_name):
            return []
        history = cmds.listHistory(object_name, pruneDagObjects=True) or []
        return cmds.ls(history, type="blendShape") or []

    def node_exists(self, node_name):
        """Checks whether a Maya node exists.

        Args:
            node_name (str): Maya node name.

        Returns:
            bool: True when the node exists.
        """
        return bool(node_name and self._get_cmds().objExists(node_name))

    def get_target_names(self, blend_node):
        """Gets target aliases from a blendShape node.

        Args:
            blend_node (str): Blend shape node name.

        Returns:
            list: Ordered target alias names.
        """
        if not self.node_exists(blend_node):
            return []
        return self._get_cmds().listAttr(f"{blend_node}.w", multi=True) or []

    def get_target_index(self, blend_node, target_name):
        """Gets a target alias's logical weight index.

        Args:
            blend_node (str): Blend shape node name.
            target_name (str): Target alias.

        Returns:
            int: Logical target index.

        Raises:
            ValueError: If the target alias cannot be found.
        """
        cmds = self._get_cmds()
        aliases = cmds.aliasAttr(blend_node, query=True) or []
        for index in range(0, len(aliases) - 1, 2):
            alias_name = aliases[index]
            plug_name = aliases[index + 1]
            if alias_name == target_name:
                match = re.search(r"\[(\d+)\]", plug_name)
                if match:
                    return int(match.group(1))
        raise ValueError(f'Unable to find target "{target_name}" on "{blend_node}".')

    def get_next_target_index(self, blend_node):
        """Gets the next available logical target index.

        Args:
            blend_node (str): Blend shape node name.

        Returns:
            int: Next available index.
        """
        indices = []
        for target_name in self.get_target_names(blend_node):
            try:
                indices.append(self.get_target_index(blend_node, target_name))
            except ValueError:
                logger.debug("Unable to resolve target index for %s.", target_name)
        return max(indices) + 1 if indices else 0

    def get_blend_mesh(self, blend_node):
        """Finds the transform driven by a blendShape node.

        Args:
            blend_node (str): Blend shape node name.

        Returns:
            str or None: Driven mesh transform, when found.
        """
        cmds = self._get_cmds()
        if not self.node_exists(blend_node):
            return None

        connections = cmds.listConnections(
            f"{blend_node}.outputGeometry",
            source=False,
            destination=True,
        ) or []
        for connection in connections:
            if cmds.nodeType(connection) == "mesh":
                parents = cmds.listRelatives(connection, parent=True, fullPath=True) or []
                if parents:
                    return parents[0]
            if cmds.nodeType(connection) == "transform":
                return connection
        return None

    def delete_all_blendshape_targets(self):
        """Deletes targets from every blendShape node in the scene.

        Returns:
            int: Number of target aliases removed.
        """
        cmds = self._get_cmds()
        removed_count = 0
        with self.preserve_selection():
            for blend_node in cmds.ls(type="blendShape") or []:
                removed_count += self.delete_blendshape_targets(blend_node)
        return removed_count

    def delete_blendshape_targets(self, blend_node):
        """Deletes all target entries from one blendShape node.

        Args:
            blend_node (str): Blend shape node to edit.

        Returns:
            int: Number of target aliases removed.
        """
        cmds = self._get_cmds()
        removed_count = 0
        for target_name in list(self.get_target_names(blend_node)):
            try:
                target_index = self.get_target_index(blend_node, target_name)
            except ValueError:
                continue
            cmds.removeMultiInstance(f"{blend_node}.weight[{target_index}]", b=True)
            cmds.removeMultiInstance(
                f"{blend_node}.inputTarget[0].inputTargetGroup[{target_index}]",
                b=True,
            )
            removed_count += 1
        return removed_count

    def delete_all_blendshape_nodes(self):
        """Deletes every blendShape node in the scene.

        Returns:
            int: Number of blendShape nodes deleted.
        """
        cmds = self._get_cmds()
        with self.preserve_selection():
            blend_nodes = cmds.ls(type="blendShape") or []
            if blend_nodes:
                cmds.delete(blend_nodes)
        return len(blend_nodes)

    def rename_targets(self, blend_node, rename_pairs):
        """Renames target aliases on a blendShape node.

        Args:
            blend_node (str): Blend shape node to edit.
            rename_pairs (list): Pairs containing old and new aliases.

        Returns:
            dict: Succeeded count and error messages.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "errors": []}
        current_names = set(self.get_target_names(blend_node))
        for old_name, new_name in rename_pairs:
            if old_name == new_name:
                continue
            if old_name not in current_names:
                result["errors"].append(f'Target "{old_name}" no longer exists.')
                continue
            if new_name in current_names:
                result["errors"].append(f'Target "{new_name}" already exists.')
                continue
            try:
                target_index = self.get_target_index(blend_node, old_name)
                cmds.aliasAttr(new_name, f"{blend_node}.weight[{target_index}]")
                current_names.remove(old_name)
                current_names.add(new_name)
                result["succeeded"] += 1
            except Exception as exception:
                result["errors"].append(f"{old_name}: {exception}")
        return result

    def duplicate_targets(self, blend_node, duplicate_pairs, operation, symmetry_axis, mirror_direction):
        """Duplicates and flips or mirrors target geometry using Maya commands.

        Args:
            blend_node (str): Blend shape node to edit.
            duplicate_pairs (list): Pairs containing source and new aliases.
            operation (str): Either ``flip`` or ``mirror``.
            symmetry_axis (str): Axis used for the operation.
            mirror_direction (str): Direction sign for mirror operations.

        Returns:
            dict: Succeeded count and error messages.
        """
        result = {"succeeded": 0, "errors": []}
        existing_names = set(self.get_target_names(blend_node))
        with self.preserve_selection():
            for source_name, requested_name in duplicate_pairs:
                try:
                    new_name = self._make_unique_target_name(requested_name, existing_names)
                    self._duplicate_target(
                        blend_node=blend_node,
                        source_name=source_name,
                        target_name=new_name,
                        operation=operation,
                        symmetry_axis=symmetry_axis,
                        mirror_direction=mirror_direction,
                    )
                    existing_names.add(new_name)
                    result["succeeded"] += 1
                except Exception as exception:
                    result["errors"].append(f"{source_name}: {exception}")
                    logger.exception("Unable to duplicate target %s.", source_name)
        return result

    def _duplicate_target(
        self,
        blend_node,
        source_name,
        target_name,
        operation,
        symmetry_axis,
        mirror_direction,
    ):
        """Creates a temporary target mesh and adds it to a blendShape node.

        Args:
            blend_node (str): Blend shape node to edit.
            source_name (str): Existing target alias.
            target_name (str): New target alias.
            operation (str): Either ``flip`` or ``mirror``.
            symmetry_axis (str): Axis used by Maya.
            mirror_direction (str): Direction sign.
        """
        cmds = self._get_cmds()
        base_mesh = self.get_blend_mesh(blend_node)
        if not base_mesh:
            raise RuntimeError(f'Unable to find the mesh driven by "{blend_node}".')

        original_values = {}
        temporary_mesh = None
        target_names = self.get_target_names(blend_node)
        try:
            for target_name_entry in target_names:
                attribute = f"{blend_node}.{target_name_entry}"
                original_values[target_name_entry] = cmds.getAttr(attribute)
                cmds.setAttr(attribute, 0)

            cmds.setAttr(f"{blend_node}.{source_name}", 1)
            temporary_name = f"{self._short_name(base_mesh)}_{source_name}_temp"
            temporary_mesh = (cmds.duplicate(base_mesh, name=temporary_name) or [None])[0]
            if not temporary_mesh:
                raise RuntimeError("Unable to create a temporary target mesh.")
            cmds.setAttr(f"{blend_node}.{source_name}", 0)

            target_index = self.get_next_target_index(blend_node)
            cmds.blendShape(
                blend_node,
                edit=True,
                target=(base_mesh, target_index, temporary_mesh, 1.0),
                topologyCheck=False,
            )
            cmds.aliasAttr(target_name, f"{blend_node}.weight[{target_index}]")

            if operation == "flip":
                cmds.blendShape(
                    blend_node,
                    edit=True,
                    flipTarget=[(0, target_index)],
                    symmetryAxis=symmetry_axis,
                    symmetrySpace=1,
                )
            elif operation == "mirror":
                mirror_direction_value = 1 if mirror_direction == "+" else 0
                cmds.blendShape(
                    blend_node,
                    edit=True,
                    mirrorTarget=[(0, target_index)],
                    mirrorDirection=mirror_direction_value,
                    symmetryAxis=symmetry_axis,
                    symmetrySpace=1,
                )
            else:
                raise ValueError(f"Unsupported duplicate operation: {operation}")

            cmds.setAttr(f"{blend_node}.{target_name}", 0)
        finally:
            if temporary_mesh and cmds.objExists(temporary_mesh):
                cmds.delete(temporary_mesh)
            for target_name_entry, value in original_values.items():
                try:
                    if cmds.objExists(f"{blend_node}.{target_name_entry}"):
                        cmds.setAttr(f"{blend_node}.{target_name_entry}", value)
                except Exception:
                    logger.debug("Unable to restore %s.%s.", blend_node, target_name_entry)

    @staticmethod
    def _make_unique_target_name(requested_name, existing_names):
        """Adds a numeric suffix when a requested alias already exists.

        Args:
            requested_name (str): Preferred alias.
            existing_names (set): Existing aliases.

        Returns:
            str: Unique alias.
        """
        requested_name = requested_name or "Target"
        if requested_name not in existing_names:
            return requested_name
        suffix = 1
        while f"{requested_name}_{suffix}" in existing_names:
            suffix += 1
        return f"{requested_name}_{suffix}"

    @staticmethod
    def _short_name(object_name):
        """Gets a safe short name from a Maya DAG path.

        Args:
            object_name (str): Maya DAG path.

        Returns:
            str: Short name suitable for a temporary or duplicate node name.
        """
        short_name = str(object_name).split("|")[-1]
        return re.sub(r"[^a-zA-Z0-9_]+", "_", short_name).strip("_") or "mesh"

    def set_all_target_values(self, blend_node, value):
        """Sets every target weight on a blendShape node.

        Args:
            blend_node (str): Blend shape node to edit.
            value (float): New target weight.

        Returns:
            dict: Succeeded count and error messages.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "errors": []}
        for target_name in self.get_target_names(blend_node):
            try:
                cmds.setAttr(f"{blend_node}.{target_name}", float(value))
                result["succeeded"] += 1
            except Exception as exception:
                result["errors"].append(f"{target_name}: {exception}")
        return result

    def bake_current_state(self, blend_node):
        """Extracts each target at its current weight as an independent mesh.

        Args:
            blend_node (str): Blend shape node to extract.

        Returns:
            dict: Number of created meshes and error messages.
        """
        cmds = self._get_cmds()
        result = {"created": 0, "errors": []}
        base_mesh = self.get_blend_mesh(blend_node)
        if not base_mesh:
            result["errors"].append(f'Unable to find the mesh driven by "{blend_node}".')
            return result

        target_values = {}
        target_names = self.get_target_names(blend_node)
        with self.preserve_selection():
            try:
                for target_name in target_names:
                    target_values[target_name] = cmds.getAttr(f"{blend_node}.{target_name}")
                    cmds.setAttr(f"{blend_node}.{target_name}", 0)

                for target_name in target_names:
                    value = target_values[target_name]
                    cmds.setAttr(f"{blend_node}.{target_name}", value)
                    duplicate_name = (
                        f"{self._short_name(base_mesh)}_{target_name}_"
                        f"{int(float(value) * 100)}pct"
                    )
                    cmds.duplicate(base_mesh, name=duplicate_name)
                    result["created"] += 1
                    cmds.setAttr(f"{blend_node}.{target_name}", 0)
            except Exception as exception:
                result["errors"].append(str(exception))
                logger.exception("Unable to extract current target values.")
            finally:
                for target_name, value in target_values.items():
                    try:
                        cmds.setAttr(f"{blend_node}.{target_name}", value)
                    except Exception:
                        logger.debug("Unable to restore %s.%s.", blend_node, target_name)
        return result

    def show_feedback(self, number_of_changes, action="affected"):
        """Shows a concise in-view Maya feedback message.

        Args:
            number_of_changes (int): Number of affected items.
            action (str): Verb describing the action.
        """
        cmds = self._get_cmds()
        count_text = str(number_of_changes)
        noun = "item" if number_of_changes == 1 else "items"
        message = (
            f'<span style="color:#FF0000;text-decoration:underline;">{html.escape(count_text)}'
            f'</span><span style="color:#FFFFFF;"> {html.escape(action)} {noun}.</span>'
        )
        cmds.inViewMessage(amg=message, pos="botLeft", fade=True, alpha=0.9)

    def warn(self, message):
        """Displays a Maya warning.

        Args:
            message (str): Warning message.
        """
        self._get_cmds().warning(message)

    def open_documentation(self):
        """Opens the Morphing Utilities documentation page."""
        self._get_cmds().showHelp(
            "https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-morphing-utilities-",
            absolute=True,
        )
