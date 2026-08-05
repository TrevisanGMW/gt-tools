"""Maya runtime operations for World Space Baker."""


class WorldSpaceBakerService:
    """Extracts and bakes world-space transform samples in Maya."""

    TRANSLATE_ATTRIBUTES = ["translateX", "translateY", "translateZ"]
    ROTATE_ATTRIBUTES = ["rotateX", "rotateY", "rotateZ"]

    def __init__(self, cmds_module=None):
        """Initializes the runtime service.

        Args:
            cmds_module (module, optional): Injected maya.cmds-compatible module.
        """
        self._cmds = cmds_module

    def get_selection(self):
        """Gets the current Maya selection using unambiguous long names.

        Returns:
            list: Selected Maya object paths.
        """
        return self._get_cmds().ls(selection=True, long=True) or []

    def get_current_frame(self):
        """Gets the current Maya timeline frame.

        Returns:
            int: Rounded current frame.
        """
        return int(round(self._get_cmds().currentTime(query=True)))

    def warn(self, message):
        """Displays a Maya warning.

        Args:
            message (str): Warning text.
        """
        self._get_cmds().warning(message)

    def select_existing(self, targets):
        """Selects stored objects that still exist.

        Args:
            targets (list): Maya object paths.

        Returns:
            tuple: Existing and missing target lists.
        """
        cmds = self._get_cmds()
        existing = [target for target in targets or [] if cmds.objExists(target)]
        missing = [target for target in targets or [] if target not in existing]
        if existing:
            cmds.select(existing, replace=True)
        return existing, missing

    def extract(self, targets, start_frame, end_frame):
        """Extracts world-space translate and rotate values over a frame range.

        Args:
            targets (list): Maya object paths to sample.
            start_frame (int): First frame to sample.
            end_frame (int): Last frame to sample.

        Returns:
            dict: Samples grouped by target and transform channel.
        """
        cmds = self._get_cmds()
        available_targets = [target for target in targets or [] if cmds.objExists(target)]
        if not available_targets:
            return {}

        original_time = cmds.currentTime(query=True)
        animation_data = {}
        try:
            cmds.refresh(suspend=True)
            for target in available_targets:
                target_data = self._extract_target(target, start_frame, end_frame)
                if target_data:
                    animation_data[target] = target_data
        finally:
            cmds.currentTime(original_time)
            cmds.refresh(suspend=False)
        return animation_data

    def _extract_target(self, target, start_frame, end_frame):
        """Extracts supported world-space channels for one Maya object.

        Args:
            target (str): Maya object path.
            start_frame (int): First frame to sample.
            end_frame (int): Last frame to sample.

        Returns:
            dict: Translate and rotate samples available for the target.
        """
        cmds = self._get_cmds()
        animatable_attributes = cmds.listAnimatable(target) or []
        attribute_names = {attribute.rsplit(".", 1)[-1] for attribute in animatable_attributes}
        use_translate = any(attribute.startswith("translate") for attribute in attribute_names)
        use_rotate = any(attribute.startswith("rotate") for attribute in attribute_names)
        if not use_translate and not use_rotate:
            return {}

        target_data = {}
        if use_translate:
            target_data["translate"] = []
        if use_rotate:
            target_data["rotate"] = []
        for frame in range(int(start_frame), int(end_frame) + 1):
            cmds.currentTime(frame)
            if use_translate:
                value = list(cmds.xform(target, worldSpace=True, query=True, translation=True))
                target_data["translate"].append([frame, value])
            if use_rotate:
                value = list(cmds.xform(target, worldSpace=True, query=True, rotation=True))
                target_data["rotate"].append([frame, value])
        return target_data

    def bake(self, animation_data):
        """Bakes extracted translate and rotate samples back onto Maya objects.

        Args:
            animation_data (dict): Samples grouped by target and channel.

        Returns:
            dict: Counts of baked and missing targets.
        """
        cmds = self._get_cmds()
        if not animation_data:
            return {"baked": 0, "missing": 0}

        original_time = cmds.currentTime(query=True)
        baked_count = 0
        missing_count = 0
        undo_opened = False
        try:
            cmds.refresh(suspend=True)
            cmds.undoInfo(openChunk=True, chunkName="World Space Baker")
            undo_opened = True
            for target, target_data in animation_data.items():
                if not cmds.objExists(target):
                    missing_count += 1
                    continue
                self._bake_channel(target, "translate", target_data.get("translate", []))
                self._bake_channel(target, "rotate", target_data.get("rotate", []))
                baked_count += 1
        finally:
            if undo_opened:
                cmds.undoInfo(closeChunk=True, chunkName="World Space Baker")
            cmds.currentTime(original_time)
            cmds.refresh(suspend=False)
        return {"baked": baked_count, "missing": missing_count}

    def _bake_channel(self, target, channel, samples):
        """Applies and keys all samples for one transform channel.

        Args:
            target (str): Maya object path.
            channel (str): Translate or rotate.
            samples (list): Frame and vector pairs.
        """
        cmds = self._get_cmds()
        is_translate = channel == "translate"
        attributes = self.TRANSLATE_ATTRIBUTES if is_translate else self.ROTATE_ATTRIBUTES
        for frame, value in samples:
            cmds.currentTime(frame)
            if is_translate:
                cmds.xform(target, worldSpace=True, translation=value)
            else:
                cmds.xform(target, worldSpace=True, rotation=value)
            cmds.setKeyframe(target, time=frame, attribute=attributes)

    def _get_cmds(self):
        """Gets maya.cmds lazily.

        Returns:
            module: maya.cmds or the injected test double.
        """
        if self._cmds is None:
            import maya.cmds as cmds

            self._cmds = cmds
        return self._cmds
