"""Maya runtime service for Offset Keyframes."""

from gt.core import anim as core_anim
from gt.core import undo as core_undo


class OffsetKeyframesService:
    """Executes reusable keyframe-offset operations in Maya."""

    def __init__(self, cmds_module=None):
        """Initializes the service.

        Args:
            cmds_module (module, optional): Injected maya.cmds-compatible module.
        """
        self._cmds = cmds_module

    def get_selection(self):
        """Gets the current selection in Maya selection order.

        Returns:
            list: Long Maya object paths.
        """
        return self._get_cmds().ls(selection=True, long=True) or []

    def offset(self, nodes, offset, scope, apply_euler_filter=False):
        """Offsets selected objects' time keys.

        Args:
            nodes (list): Maya animation targets.
            offset (float): Signed frame offset.
            scope (str): Key offset scope.
            apply_euler_filter (bool, optional): Whether to filter affected curves.

        Returns:
            dict: Core offset operation result.
        """
        with core_undo.UndoChunk(chunk_name="Offset Keyframes"):
            result = core_anim.offset_time_keyframes(nodes=nodes, offset=offset, scope=scope)
            if apply_euler_filter:
                core_anim.filter_animation_curves(result.get("curves"))
        return result

    def stagger(self, nodes, step, scope, apply_euler_filter=False):
        """Staggers selected objects' time keys in selection order.

        Args:
            nodes (list): Ordered Maya animation targets.
            step (float): Signed frame increment.
            scope (str): Key offset scope.
            apply_euler_filter (bool, optional): Whether to filter affected curves.

        Returns:
            dict: Core stagger operation result.
        """
        with core_undo.UndoChunk(chunk_name="Stagger Keyframes"):
            result = core_anim.stagger_time_keyframes(nodes=nodes, step=step, scope=scope)
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
