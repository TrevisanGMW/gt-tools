"""Lazy Maya operations and safety boundaries for HumanIK Utilities.

Native HumanIK setup and baking require Autodesk's MEL procedures. Those calls
remain inside the existing gt.utils.hik Python wrappers; pose work uses Python.
"""

from contextlib import contextmanager
import json
import os
import re
import tempfile

from gt.tools.anim_hik_utils import anim_hik_utils_model as tool_model


class AnimHikUtilsService:
    """Adapts shared HumanIK utilities to interactive, character-scoped actions."""

    def __init__(self, cmds_module=None, hik_module=None):
        """Stores optional runtime dependencies for focused testing.

        Args:
            cmds_module (module, optional): Maya commands or test double.
            hik_module (module, optional): HumanIK helpers or test double.
        """
        self._cmds = cmds_module
        self._hik = hik_module

    def runtime(self):
        """Loads Maya and HumanIK only when an action needs them.

        Returns:
            tuple: Maya commands and shared HumanIK helper modules.
        """
        if self._cmds is None:
            from maya import cmds

            self._cmds = cmds
        if not self._cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            self._cmds.loadPlugin("mayaHIK")
        if self._hik is None:
            from gt.utils import hik

            self._hik = hik
        return self._cmds, self._hik

    def characters(self):
        """Lists exact character names, including their namespaces.

        Returns:
            list: Sorted HumanIK character nodes.
        """
        unused_cmds, hik = self.runtime()
        return sorted(hik.get_hik_characters(), key=str.casefold)

    def require_character(self, character, writable=False):
        """Rejects stale, invalid, and optionally protected character targets.

        Args:
            character (str): Exact character node name.
            writable (bool): Reject referenced or locked definition nodes.

        Returns:
            str: Validated character name.
        """
        cmds, unused_hik = self.runtime()
        if not character or character not in self.characters():
            raise ValueError("Choose an existing HumanIK character and refresh the list if needed.")
        tool_model.validate_node_name(character)
        if writable and (
            cmds.referenceQuery(character, isNodeReferenced=True)
            or any(cmds.lockNode(character, query=True, lock=True) or [])
        ):
            raise ValueError("This definition is referenced or locked and cannot be edited here.")
        return character

    @contextmanager
    def scene_edit(self, label):
        """Groups edits and restores time, selection, and automatic keying.

        Args:
            label (str): Undo chunk label.

        Yields:
            None: Scene edit scope.
        """
        cmds, unused_hik = self.runtime()
        selection = cmds.ls(selection=True, long=True) or []
        current_time = cmds.currentTime(query=True)
        auto_key = cmds.autoKeyframe(query=True, state=True)
        cmds.undoInfo(openChunk=True, chunkName=label)
        try:
            cmds.autoKeyframe(state=False)
            yield
        finally:
            try:
                if cmds.currentTime(query=True) != current_time:
                    cmds.currentTime(current_time)
                existing = [node for node in selection if cmds.objExists(node)]
                if existing:
                    cmds.select(existing, replace=True)
                else:
                    cmds.select(clear=True)
            finally:
                try:
                    cmds.autoKeyframe(state=auto_key)
                finally:
                    cmds.undoInfo(closeChunk=True)

    def inspect_character(self, character):
        """Collects current definition, skeleton, and control-rig information.

        Args:
            character (str): Character to inspect.

        Returns:
            dict: Scene details suitable for display and selection.
        """
        self.require_character(character)
        cmds, hik = self.runtime()
        skeleton = sorted(set(cmds.listConnections(
            character, source=True, destination=False, type="joint"
        ) or []))
        sources = self.character_sources(character)
        return {
            "character": character,
            "namespace": hik.get_character_namespace(character),
            "locked": bool(cmds.getAttr(f"{character}.InputCharacterizationLock")),
            "source": ", ".join(sources) or "No character source",
            "skeleton": skeleton,
            "control_rig": hik.get_hik_control_rig(character),
            "controls": hik.get_hik_control_rig_controls(character),
            "property_node": hik.get_hik_property_node(character),
        }

    def character_sources(self, character):
        """Finds source definitions through the target's native retargeter graph.

        Args:
            character (str): Exact target character node.

        Returns:
            list: Connected source definitions, including retarget layers.
        """
        cmds, unused_hik = self.runtime()
        definition_plug = f"{character}.OutputCharacterDefinition"
        retargeters = cmds.listConnections(
            definition_plug, source=False, destination=True, type="HIKRetargeterNode"
        ) or []
        sources = set()
        for retargeter in retargeters:
            if cmds.isConnected(definition_plug, f"{retargeter}.InputCharacterDefinitionDst"):
                sources.update(cmds.listConnections(
                    f"{retargeter}.InputCharacterDefinitionSrc", source=True,
                    destination=False, type="HIKCharacterNode",
                ) or [])
        return sorted(sources)

    def select_nodes(self, character, kind):
        """Selects the chosen character's definition, joints, controls, or properties.

        Args:
            character (str): Character to inspect.
            kind (str): Detail field to select.

        Returns:
            int: Selected node count.
        """
        details = self.inspect_character(character)
        nodes = details[kind]
        nodes = [nodes] if isinstance(nodes, str) and nodes else nodes
        if not nodes:
            raise ValueError(f"No {kind.replace('_', ' ')} found for this character.")
        cmds, unused_hik = self.runtime()
        cmds.select(nodes, replace=True)
        return len(nodes)

    def pose(self, character, operation, settings, file_path=None):
        """Mirrors, flips, or imports the current control-rig pose.

        Args:
            character (str): Target character.
            operation (str): left, right, flip, or import.
            settings (dict): Coordinate-space and center options.
            file_path (str, optional): Pose file for import.

        Returns:
            list: Controls reported as modified by the shared utility.
        """
        self.require_character(character)
        unused_cmds, hik = self.runtime()
        options = {key: settings[key] for key in ("affect_center", "world_space")}
        with self.scene_edit("HumanIK Pose"):
            if operation == "import":
                result = hik.import_hik_pose(character, file_path, world_space=None)
            elif operation == "flip":
                result = hik.flip_hik_pose(character, **options)
            elif operation in ("left", "right"):
                result = hik.mirror_hik_pose(character, source_side=operation, **options)
            else:
                raise ValueError("Unknown pose operation.")
        if not result:
            raise RuntimeError("No controls changed. Check the control rig and writable channels.")
        return result

    def playback_range(self):
        """Reads the current playback range at action time.

        Returns:
            tuple: Start and end frames.
        """
        cmds, unused_hik = self.runtime()
        return cmds.playbackOptions(query=True, minTime=True), cmds.playbackOptions(query=True, maxTime=True)

    def animation(self, character, operation, settings, start, end, sample_by=1.0):
        """Delegates sampled animation edits to the shared HIK utility.

        Args:
            character (str): Target definition.
            operation (str): left, right, or flip.
            settings (dict): Mirror space and center options.
            start (float): First frame.
            end (float): Last frame.
            sample_by (float): Positive sample interval.

        Returns:
            dict: Modified controls, samples, and skipped channels.
        """
        self.require_character(character)
        unused_cmds, hik = self.runtime()
        options = {key: settings[key] for key in ("affect_center", "world_space")}
        if operation == "flip":
            return hik.flip_hik_animation(character, start, end, sample_by=sample_by, **options)
        if operation not in ("left", "right"):
            raise ValueError("Unknown animation operation.")
        return hik.mirror_hik_animation(character, start, end, source_side=operation,
                                        sample_by=sample_by, **options)

    def definition_action(self, character, operation, value=None):
        """Creates, renames, locks, unlocks, or changes the source of a definition.

        Args:
            character (str): Target character; unused when creating.
            operation (str): create, rename, lock, unlock, or source.
            value (str, optional): New name or source character.

        Returns:
            str or bool: Result from the shared utility.
        """
        unused_cmds, hik = self.runtime()
        if operation != "create":
            self.require_character(character, writable=True)
        if operation in ("create", "rename"):
            value = tool_model.validate_node_name(value)
        if operation == "source" and value:
            self.require_character(value)
            pending = [value]
            visited = set()
            while pending:
                source = pending.pop()
                if source == character:
                    raise ValueError("This source would create a HumanIK character cycle.")
                if source not in visited:
                    visited.add(source)
                    pending.extend(self.character_sources(source))
        with self.scene_edit("HumanIK Definition"):
            if operation == "create":
                result = hik.create_definition(value)
            elif operation == "rename":
                result = hik.rename_definition(character, value)
            elif operation in ("lock", "unlock"):
                result = hik.set_definition_lock(character, lock_state=operation == "lock")
            elif operation == "source":
                result = hik.set_definition_source(character, value or None)
            else:
                raise ValueError("Unknown definition operation.")
        if not result:
            raise RuntimeError("HumanIK could not complete the operation. See the Script Editor.")
        return result

    def preview_definition(self, character, file_path, settings):
        """Checks all XML mappings before any scene edits.

        Args:
            character (str): Target definition.
            file_path (str): Native XML path.
            settings (dict): Prefix and namespace substitution options.

        Returns:
            list: Tuples containing slot, bone, and validation status.
        """
        self.require_character(character, writable=True)
        cmds, hik = self.runtime()
        rows = []
        for slot, bone in tool_model.read_definition(
            file_path, **{key: settings[key] for key in ("prefix", "search_namespace", "replace_namespace")}
        ):
            matches = [] if re.search(r"[*?\[\]]", bone) else (cmds.ls(bone, long=True) or [])
            status = "Ready"
            if slot not in hik.HIK_CHARACTERIZE_KEYS:
                status = "Unknown slot"
            elif len(matches) != 1:
                status = "Missing" if not matches else "Ambiguous"
            elif not cmds.objectType(matches[0], isAType="transform"):
                status = "Not a transform"
            elif cmds.objExists(f"{bone}.Character") and any(
                owner != character for owner in (cmds.listConnections(
                    f"{bone}.Character", source=True, destination=False, type="HIKCharacterNode"
                ) or [])
            ):
                status = "Used by another definition"
            rows.append((slot, bone, status))
        return rows

    def import_definition(self, character, file_path, settings):
        """Imports a fully resolved match list and leaves it unlocked for review.

        Args:
            character (str): Target definition.
            file_path (str): Native XML path.
            settings (dict): Mapping options.

        Returns:
            int: Number of mapped slots.
        """
        rows = self.preview_definition(character, file_path, settings)
        if any(status != "Ready" for unused_slot, unused_bone, status in rows):
            raise ValueError("Resolve missing, ambiguous, or unsupported XML mappings before import.")
        cmds, hik = self.runtime()
        with self.scene_edit("Import HumanIK Definition"):
            result = hik.import_definition_from_xml(
                character, file_path,
                **{key: settings[key] for key in ("prefix", "search_namespace", "replace_namespace")},
            )
        if not result:
            raise RuntimeError("HumanIK definition import failed. See the Script Editor.")
        for slot, bone, unused_status in rows:
            attribute = slot if cmds.attributeQuery(slot, node=character, exists=True) else slot[0].lower() + slot[1:]
            connections = cmds.listConnections(
                f"{character}.{attribute}", source=True, destination=False
            ) or []
            expected = cmds.ls(bone, long=True) or []
            actual = cmds.ls(connections, long=True) if connections else []
            if not set(expected).intersection(actual or []):
                raise RuntimeError(f"Mapping {slot} was not applied. Review the scene or use Undo.")
        return len(rows)

    def apply_properties(self, character, properties):
        """Applies portable retarget settings and returns the actual applied keys.

        Args:
            character (str): Target character.
            properties (dict): Property names and scalar values.

        Returns:
            dict: Successfully applied properties.
        """
        self.require_character(character, writable=True)
        unused_cmds, hik = self.runtime()
        with self.scene_edit("Apply HumanIK Properties"):
            return hik.set_hik_properties(character, properties, create_if_missing=True)

    def properties(self, character):
        """Captures current retarget settings.

        Args:
            character (str): Source character.

        Returns:
            dict: Portable property values.
        """
        self.require_character(character)
        unused_cmds, hik = self.runtime()
        result = hik.get_hik_properties(character)
        if not result:
            raise ValueError("No writable HumanIK properties were found for this character.")
        return result

    def export_file(self, character, kind, file_path, settings):
        """Stages an export before replacing the user-confirmed destination.

        Args:
            character (str): Source character.
            kind (str): pose, definition, or properties.
            file_path (str): Destination already confirmed by the file dialog.
            settings (dict): Export coordinate space and XML prefix.
        """
        self.require_character(character)
        unused_cmds, hik = self.runtime()
        temporary_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                dir=os.path.dirname(os.path.abspath(file_path)), suffix=".tmp", delete=False
            ) as stream:
                temporary_path = stream.name
            if kind == "pose":
                result = hik.export_hik_pose(character, temporary_path, world_space=settings["world_space"])
            elif kind == "definition":
                prefix = settings["prefix"]
                if prefix and not all(character.isalnum() or character in "_:" for character in prefix):
                    raise ValueError("XML prefix may only contain letters, numbers, underscores, and colons.")
                result = hik.export_definition_to_xml(character, temporary_path, prefix=prefix)
            elif kind == "properties":
                properties = self.properties(character)
                with open(temporary_path, "w", encoding="utf-8") as stream:
                    json.dump(properties, stream, indent=4, sort_keys=True, allow_nan=False)
                    stream.write("\n")
                result = True
            else:
                raise ValueError("Unknown export format.")
            if not result:
                raise RuntimeError("HumanIK export failed. The destination was not changed.")
            os.replace(temporary_path, file_path)
        finally:
            if temporary_path and os.path.isfile(temporary_path):
                os.remove(temporary_path)

    def bake(self, character, destination, force_proxy=False):
        """Bakes using the current playback range after the controller confirms.

        Args:
            character (str): Target character.
            destination (str): skeleton or controls.
            force_proxy (bool): Force the helper's Python skeleton bake.
        """
        self.require_character(character, writable=True)
        unused_cmds, hik = self.runtime()
        with self.scene_edit("Bake HumanIK Animation"):
            if destination == "skeleton":
                result = hik.bake_to_skeleton(character, force_proxy=force_proxy)
            elif destination == "controls":
                result = hik.bake_to_control_rig(character)
            else:
                raise ValueError("Unknown bake destination.")
        if not result:
            raise RuntimeError("HumanIK bake failed. Inspect the Script Editor before continuing.")

    def empty_definitions(self):
        """Previews empty local definitions without rigs or character connections.

        Returns:
            list: Safe candidates for a separately confirmed cleanup.
        """
        cmds, hik = self.runtime()
        candidates = []
        for character in self.characters():
            protected = (
                cmds.referenceQuery(character, isNodeReferenced=True)
                or any(cmds.lockNode(character, query=True, lock=True) or [])
                or cmds.listConnections(character, source=True, destination=False, type="transform")
                or cmds.listConnections(character, type="HIKCharacterNode")
                or cmds.listConnections(character, type="HIKRetargeterNode")
                or hik.get_hik_control_rig(character)
            )
            if not protected:
                candidates.append(character)
        return candidates

    def delete_empty_definitions(self, candidates):
        """Deletes only the previewed definitions after rechecking their state.

        Args:
            candidates (list): Exact names approved by the user.

        Returns:
            int: Number of deleted definitions.
        """
        current = self.empty_definitions()
        if not candidates or any(character not in current for character in candidates):
            raise ValueError("Cleanup candidates changed. Preview the empty definitions again.")
        cmds, unused_hik = self.runtime()
        with self.scene_edit("Delete Empty HumanIK Definitions"):
            cmds.delete(candidates)
        return len(candidates)
