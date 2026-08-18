"""Maya runtime service for Copy/Paste Animation."""

from gt.core import anim as core_anim
from gt.tools.anim_copy_paste import anim_copy_paste_model as copy_model


class AnimCopyPasteService:
    """Stores and restores reusable Maya animation clips."""

    def __init__(self, cmds_module=None):
        """Initializes the service.

        Args:
            cmds_module (module, optional): Injected maya.cmds-compatible module.
        """
        self._cmds = cmds_module

    def get_selection(self):
        """Gets the Maya selection in selection order.

        Returns:
            list: Long Maya object paths.
        """
        return self._get_cmds().ls(selection=True, long=True) or []

    def get_current_frame(self):
        """Gets the current Maya frame.

        Returns:
            float: Current timeline frame.
        """
        return float(self._get_cmds().currentTime(query=True))

    def copy(self, nodes, copy_scope=copy_model.AnimCopyPasteConstants.CopyScope.ALL):
        """Extracts animation in the requested scope and saves it to the cache.

        Args:
            nodes (list): Maya nodes whose animation should be stored.
            copy_scope (str, optional): All, selected, before-current, or
                after-current copy scope.

        Returns:
            dict: Portable copied animation data.
        """
        copy_scope = str(copy_scope or copy_model.AnimCopyPasteConstants.CopyScope.ALL)
        if copy_scope == copy_model.AnimCopyPasteConstants.CopyScope.SELECTED:
            clip_data = core_anim.extract_selected_animation_clip(nodes=nodes or None)
        elif copy_scope == copy_model.AnimCopyPasteConstants.CopyScope.BEFORE_CURRENT:
            clip_data = core_anim.extract_animation_clip(
                nodes=nodes,
                end_frame=self.get_current_frame(),
            )
        elif copy_scope == copy_model.AnimCopyPasteConstants.CopyScope.AFTER_CURRENT:
            clip_data = core_anim.extract_animation_clip(
                nodes=nodes,
                start_frame=self.get_current_frame(),
            )
        else:
            clip_data = core_anim.extract_animation_clip(nodes=nodes)
        core_anim.write_animation_clip(clip_data)
        return clip_data

    def load_cached_clip(self):
        """Loads the persistent shared animation cache.

        Returns:
            dict: Portable animation data.
        """
        return core_anim.read_animation_clip()

    def clear_cached_clip(self):
        """Removes the persistent shared animation cache.

        Returns:
            bool: True when a cache file was removed.
        """
        return core_anim.delete_animation_clip()

    def import_clip(self, file_path):
        """Imports JSON animation data into the shared cache.

        Args:
            file_path (str): JSON file to import.

        Returns:
            dict: Imported animation data.
        """
        clip_data = core_anim.read_animation_clip(file_path=file_path)
        core_anim.write_animation_clip(clip_data)
        return clip_data

    def export_clip(self, clip_data, file_path):
        """Exports animation data to JSON.

        Args:
            clip_data (dict): Animation payload to export.
            file_path (str): Destination JSON path.

        Returns:
            str: Written JSON path.
        """
        return core_anim.write_animation_clip(clip_data=clip_data, file_path=file_path)

    def get_summary(self, clip_data):
        """Gets a concise copied-animation description.

        Args:
            clip_data (dict): Portable animation data.

        Returns:
            str: User-facing summary.
        """
        return core_anim.get_animation_clip_summary(clip_data)

    def get_details(self, clip_data):
        """Gets a complete user-facing report of copied animation data.

        Args:
            clip_data (dict): Portable animation data.

        Returns:
            str: Multi-line copied-animation report.
        """
        return core_anim.get_animation_clip_details(clip_data)

    def paste(
        self,
        clip_data,
        targets,
        paste_time,
        mode,
        mapping_mode,
        source_attribute,
        destination_attribute,
        source_namespace="",
        target_namespace="",
        apply_euler_filter=False,
    ):
        """Pastes an animation clip onto target objects.

        Args:
            clip_data (dict): Copied animation data.
            targets (list): Selected destination objects.
            paste_time (float): Destination start frame.
            mode (str): Insert or replace paste behavior.
            mapping_mode (str): Selection-order or namespace/name matching.
            source_attribute (str): Optional source channel filter.
            destination_attribute (str): Optional destination channel override.
            source_namespace (str, optional): Namespace to replace for the
                namespace-swap mapping mode.
            target_namespace (str, optional): Destination namespace for the
                namespace-swap mapping mode.
            apply_euler_filter (bool, optional): Whether to Euler filter pasted curves.

        Returns:
            dict: Core paste operation result.
        """
        result = core_anim.paste_animation_clip(
            clip_data=clip_data,
            targets=targets or None,
            paste_time=paste_time,
            mode=mode,
            mapping_mode=mapping_mode,
            source_attribute=source_attribute,
            destination_attribute=destination_attribute,
            source_namespace=source_namespace,
            target_namespace=target_namespace,
        )
        if apply_euler_filter:
            core_anim.filter_animation_curves(result.get("curves"))
        return result

    def warn(self, message):
        """Displays a Maya warning.

        Args:
            message (str): Warning text.
        """
        self._get_cmds().warning(message)

    def _get_cmds(self):
        """Gets maya.cmds lazily.

        Returns:
            module: Maya command module.
        """
        if self._cmds is None:
            import maya.cmds as cmds

            self._cmds = cmds
        return self._cmds
