"""Session state and pure helpers for World Space Baker."""


class WorldSpaceBakerModel:
    """Stores the active targets, frame range, and extracted animation data."""

    DEFAULT_START_FRAME = 1
    DEFAULT_END_FRAME = 120

    def __init__(self):
        """Initializes empty session state."""
        self.targets = []
        self.start_frame = self.DEFAULT_START_FRAME
        self.end_frame = self.DEFAULT_END_FRAME
        self.animation_data = {}

    def set_targets(self, targets):
        """Stores a unique, ordered target list and clears stale animation data.

        Args:
            targets (list): Maya object names.

        Returns:
            list: Sanitized target names.
        """
        clean_targets = []
        for target in targets or []:
            target = str(target or "").strip()
            if target and target not in clean_targets:
                clean_targets.append(target)
        self.targets = clean_targets
        self.animation_data = {}
        return list(self.targets)

    def set_frame_range(self, start_frame, end_frame):
        """Updates the extraction frame range.

        Args:
            start_frame (int): First frame to extract.
            end_frame (int): Last frame to extract.
        """
        self.start_frame = int(start_frame)
        self.end_frame = int(end_frame)

    def validate_frame_range(self):
        """Validates that the range contains at least two ordered frames.

        Returns:
            tuple: Boolean validity and a user-facing message.
        """
        if self.start_frame >= self.end_frame:
            return False, "The start frame must be lower than the end frame."
        return True, ""

    def set_animation_data(self, animation_data):
        """Replaces the currently extracted animation data.

        Args:
            animation_data (dict): World-space samples grouped by target and channel.
        """
        self.animation_data = dict(animation_data or {})

    def get_target_label(self):
        """Builds the compact target-button label.

        Returns:
            str: Target name or object count.
        """
        if len(self.targets) == 1:
            return self.targets[0]
        return f"{len(self.targets)} objects"

    def get_stored_summary(self):
        """Builds a concise description of the extracted data.

        Returns:
            str: Stored target count and frame range.
        """
        target_count = len(self.animation_data)
        object_label = "object" if target_count == 1 else "objects"
        return f"{target_count} {object_label} stored. Frames: {self.start_frame}-{self.end_frame}"
