"""
Motion Evaluation Check Framework - Check definitions, parameters, results, and sampled motion data.

Pure module: works on sampled data dictionaries produced by ``sampling`` (or by tests).

Sample layout:
    {
        "fps": 30.0,
        "start_frame": 1,
        "frame_count": 120,
        "up_axis": "y",
        "meters_per_unit": 0.01,
        "nodes": {"|Hips": {"matrices": [[16 floats], ...], "parent": None}, ...},
        "roles": {"hips": "|Hips", ...},
    }
"""

from . import math_utils

MODE_GENERAL = "general"
MODE_BIPED = "biped"
MODE_VALUES = [MODE_GENERAL, MODE_BIPED]
MODE_LABELS = {MODE_GENERAL: "General", MODE_BIPED: "Biped"}

STATUS_PASSED = "passed"
STATUS_WARNING = "warning"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_DISABLED = "disabled"
STATUS_SEVERITY = {
    STATUS_DISABLED: 0,
    STATUS_SKIPPED: 0,
    STATUS_PASSED: 1,
    STATUS_WARNING: 2,
    STATUS_FAILED: 3,
}

GRAVITY_METERS_PER_SECOND_SQUARED = 9.81
CHART_ABOVE = "above"
CHART_BELOW = "below"
GENERAL_FALLBACK_REFERENCE_METERS = 0.9


class ParameterSpec:
    """Describes one tunable detection parameter of a check."""

    def __init__(self, key, label, default, minimum=None, maximum=None, tooltip="", decimals=3, choices=None):
        """Initializes the parameter description.

        Args:
            key (str): Stable parameter key stored in presets.
            label (str): User-facing label.
            default (float, int, bool, or str): Default value. Its type defines the value type.
            minimum (float, optional): Lowest allowed value for numbers.
            maximum (float, optional): Highest allowed value for numbers.
            tooltip (str): Explanation shown in the UI.
            decimals (int): Decimal places shown for floats.
            choices (list, optional): Allowed values for string parameters.
        """
        self.key = key
        self.label = label
        self.default = default
        self.minimum = minimum
        self.maximum = maximum
        self.tooltip = tooltip
        self.decimals = decimals
        self.choices = list(choices) if choices else None

    @property
    def value_type(self):
        """Gets the Python type of the parameter.

        Returns:
            type: bool, int, float, or str.
        """
        return type(self.default)

    def coerce(self, value):
        """Converts and clamps a value to this parameter's type and range.

        Args:
            value (object): Raw value.

        Returns:
            object: Valid value, or the default when conversion fails.
        """
        try:
            if self.value_type is bool:
                coerced = bool(value)
            elif self.value_type is int:
                coerced = int(round(float(value)))
            elif self.value_type is float:
                coerced = float(value)
            else:
                coerced = str(value)
        except (TypeError, ValueError):
            return self.default
        if self.choices and coerced not in self.choices:
            return self.default
        if self.value_type in (int, float):
            if self.minimum is not None:
                coerced = max(self.value_type(self.minimum), coerced)
            if self.maximum is not None:
                coerced = min(self.value_type(self.maximum), coerced)
        return coerced


class CheckDefinition:
    """Describes one evaluation check and its default scoring."""

    def __init__(
        self,
        key,
        label,
        mode,
        description,
        function,
        parameters=None,
        required_roles=None,
        required_data=None,
        enabled=True,
        weight=1.0,
        warn_below=85,
        fail_below=50,
        event_penalty=0.0,
        frame_penalty=2.0,
    ):
        """Initializes the check definition.

        Args:
            key (str): Stable check key stored in presets and reports.
            label (str): User-facing name.
            mode (str): MODE_GENERAL (runs in every mode) or MODE_BIPED.
            description (str): What the check detects.
            function (callable): ``function(data, parameters)`` returning a CheckResult.
            parameters (list, optional): ParameterSpec objects.
            required_roles (list, optional): Roles that must be resolved, otherwise the check is skipped.
            required_data (list, optional): Extra scene data keys the check reads with MotionData.get_extra
                (data that is not a world matrix, see SceneHost.get_extra_data). Hosts that cannot provide
                a key make the check skip with a reason instead of failing.
            enabled (bool): Default enabled state.
            weight (float): Default contribution to the overall score.
            warn_below (int): Default score below which the check warns.
            fail_below (int): Default score below which the check fails. 0 means warn only.
            event_penalty (float): Default points removed per detected issue span.
            frame_penalty (float): Default points removed per percent of flagged frames.
        """
        self.key = key
        self.label = label
        self.mode = mode
        self.description = description
        self.function = function
        self.parameters = list(parameters or [])
        self.required_roles = list(required_roles or [])
        self.required_data = list(required_data or [])
        self.enabled = enabled
        self.weight = weight
        self.warn_below = warn_below
        self.fail_below = fail_below
        self.event_penalty = event_penalty
        self.frame_penalty = frame_penalty

    def get_parameter_defaults(self):
        """Gets the default detection parameters.

        Returns:
            dict: Parameter key to default value.
        """
        return {parameter.key: parameter.default for parameter in self.parameters}

    def get_scoring_defaults(self):
        """Gets the default scoring settings.

        Returns:
            dict: Enabled, weight, thresholds, penalties, and allow-failure defaults.
        """
        return {
            "enabled": self.enabled,
            "weight": self.weight,
            "warn_below": self.warn_below,
            "fail_below": self.fail_below,
            "allow_failure": False,
            "event_penalty": self.event_penalty,
            "frame_penalty": self.frame_penalty,
        }

    def is_available_in_mode(self, mode):
        """Checks whether the check runs in an evaluation mode.

        Args:
            mode (str): Evaluation mode.

        Returns:
            bool: True for general checks or biped checks in biped mode.
        """
        return self.mode == MODE_GENERAL or self.mode == mode


class CheckResult:
    """Raw findings of one check before scoring."""

    def __init__(self, flagged=None, details=None, offenders=None, skip_reason="", event_count=None):
        """Initializes the result.

        Args:
            flagged (iterable, optional): Flagged frame indexes.
            details (list, optional): Readable finding lines.
            offenders (dict, optional): Node or pair label to flagged frame count.
            skip_reason (str): Non-empty when the check could not run.
            event_count (int, optional): Explicit event count. Defaults to the number of flagged spans.
        """
        self.flagged = set(flagged or [])
        self.details = list(details or [])
        self.offenders = dict(offenders or {})
        self.skip_reason = skip_reason
        self.event_count = event_count
        self.series = []
        self.chart = None

    @classmethod
    def skipped(cls, reason):
        """Creates a skipped result.

        Args:
            reason (str): Why the check could not run.

        Returns:
            CheckResult: Skipped result.
        """
        return cls(skip_reason=reason)

    def flag(self, frame_index, offender=None):
        """Flags one frame, optionally counting an offender.

        Args:
            frame_index (int): Frame index.
            offender (str, optional): Node or pair label responsible.
        """
        self.flagged.add(frame_index)
        if offender:
            self.offenders[offender] = self.offenders.get(offender, 0) + 1

    def flag_many(self, frame_indexes, offender=None):
        """Flags several frames.

        Args:
            frame_indexes (iterable): Frame indexes.
            offender (str, optional): Node or pair label responsible.
        """
        for frame_index in frame_indexes:
            self.flag(frame_index, offender=offender)

    def add_series(self, label, values):
        """Records a measured per-frame signal so reports can graph what the check analyzed.

        Args:
            label (str): Series name, for example "left foot".
            values (list): One value per frame index. None marks frames the check did not measure.
        """
        self.series.append({"label": label, "values": list(values)})

    def set_chart(self, unit, threshold=None, threshold_label="", direction=CHART_ABOVE):
        """Describes how the recorded series compare to the check threshold.

        Args:
            unit (str): Unit of the series values, shown on the graph.
            threshold (float, optional): Value the series are compared against.
            threshold_label (str): Readable threshold name.
            direction (str): CHART_ABOVE when values above the threshold are bad, CHART_BELOW otherwise.
        """
        self.chart = {
            "unit": unit,
            "threshold": threshold,
            "threshold_label": threshold_label,
            "direction": direction,
        }

    def get_chart_data(self, digits=5):
        """Builds the graph payload stored in a report entry.

        Args:
            digits (int): Significant digits kept per value.

        Returns:
            dict or None: Chart description with rounded series, or None when nothing was recorded.
        """
        if not self.series:
            return None

        def round_value(value):
            """Rounds a series value to the requested significant digits.

            Args:
                value (float or None): Raw value.

            Returns:
                float or None: Rounded value. Non-finite values become None.
            """
            if value is None or value != value or value in (float("inf"), float("-inf")):
                return None
            return float(f"{value:.{digits}g}")

        chart = dict(self.chart or {"unit": "", "threshold": None, "threshold_label": "", "direction": CHART_ABOVE})
        chart["series"] = [
            {"label": series["label"], "values": [round_value(value) for value in series["values"]]}
            for series in self.series
        ]
        return chart


def worst_per_frame(frame_count, value_lists, use_minimum=False):
    """Combines per-node series into the worst value per frame.

    Args:
        frame_count (int): Number of frames.
        value_lists (list): Lists of per-frame values (None entries are ignored).
        use_minimum (bool): Keep the smallest value instead of the largest.

    Returns:
        list: Worst value per frame, or None where nothing was measured.
    """
    combined = [None] * frame_count
    for values in value_lists:
        for index, value in enumerate(values[:frame_count]):
            if value is None:
                continue
            current = combined[index]
            if current is None or (value < current if use_minimum else value > current):
                combined[index] = value
    return combined


class MotionData:
    """Read-only access to sampled motion with lazy, cached derived series."""

    def __init__(self, sample, mode=MODE_GENERAL, settings=None):
        """Initializes motion data.

        Args:
            sample (dict): Sample dictionary (see module docstring).
            mode (str): Evaluation mode.
            settings (dict, optional): Resolved global preset settings.
        """
        self.sample = sample
        self.mode = mode
        self.settings = dict(settings or {})
        self.fps = float(sample.get("fps") or 30.0)
        self.start_frame = int(sample.get("start_frame") or 0)
        self.frame_count = int(sample.get("frame_count") or 0)
        self.up_axis = str(sample.get("up_axis") or "y").lower()
        self.meters_per_unit = float(sample.get("meters_per_unit") or 0.01)
        self.nodes = sample.get("nodes") or {}
        self.roles = dict(sample.get("roles") or {})
        self.extra = dict(sample.get("extra") or {})
        self._positions = {}
        self._rotations = {}
        self._reference_length = None
        self.cache = {}

    # ------------------------------------------------ Nodes ------------------------------------------------
    @property
    def node_paths(self):
        """Gets every sampled node path.

        Returns:
            list: Node paths in a stable order.
        """
        return sorted(self.nodes.keys())

    def get_parent(self, node_path):
        """Gets the sampled parent of a node.

        Args:
            node_path (str): Node path.

        Returns:
            str or None: Direct DAG parent when it was sampled, otherwise None.
        """
        parent = (self.nodes.get(node_path) or {}).get("parent")
        return parent if parent in self.nodes else None

    def get_root_nodes(self):
        """Gets sampled nodes without a sampled parent.

        Returns:
            list: Top-level sampled node paths.
        """
        return [path for path in self.node_paths if self.get_parent(path) is None]

    def get_matrices(self, node_path):
        """Gets the world matrices of a node.

        Args:
            node_path (str): Node path.

        Returns:
            list: Flat 16-value matrices, one per frame.
        """
        return (self.nodes.get(node_path) or {}).get("matrices") or []

    def get_positions(self, node_path):
        """Gets Y-up world positions of a node.

        Args:
            node_path (str): Node path.

        Returns:
            list: (x, y, z) positions where Y is always up.
        """
        if node_path not in self._positions:
            positions = [math_utils.matrix_position(matrix) for matrix in self.get_matrices(node_path)]
            if self.up_axis == "z":
                positions = [(position[0], position[2], -position[1]) for position in positions]
            self._positions[node_path] = positions
        return self._positions[node_path]

    def get_rotations(self, node_path):
        """Gets Y-up world rotation axes of a node (same space as get_positions).

        Args:
            node_path (str): Node path.

        Returns:
            list: Per frame, three unit axis vectors (X, Y, Z axes of the node in world space).
        """
        if node_path not in self._rotations:
            rotations = [math_utils.matrix_rotation(matrix) for matrix in self.get_matrices(node_path)]
            if self.up_axis == "z":
                rotations = [[(axis[0], axis[2], -axis[1]) for axis in rotation] for rotation in rotations]
            self._rotations[node_path] = rotations
        return self._rotations[node_path]

    def get_extra(self, data_key):
        """Gets extra scene data collected for checks with required_data.

        Args:
            data_key (str): Extra data key (see SceneHost.get_extra_data).

        Returns:
            object or None: JSON-compatible data, or None when the host did not provide it.
        """
        return self.extra.get(data_key)

    def has_role(self, role_key):
        """Checks whether a role was resolved and sampled.

        Args:
            role_key (str): Role key.

        Returns:
            bool: True when available.
        """
        return self.roles.get(role_key) in self.nodes

    def get_role_path(self, role_key):
        """Gets the node path of a role.

        Args:
            role_key (str): Role key.

        Returns:
            str or None: Node path when available.
        """
        return self.roles.get(role_key) if self.has_role(role_key) else None

    def get_role_positions(self, role_key):
        """Gets Y-up positions of a role.

        Args:
            role_key (str): Role key.

        Returns:
            list or None: Positions, or None when the role is unavailable.
        """
        path = self.get_role_path(role_key)
        return self.get_positions(path) if path else None

    def missing_roles(self, role_keys):
        """Lists roles that are not available.

        Args:
            role_keys (list): Role keys to test.

        Returns:
            list: Unavailable role keys.
        """
        return [role_key for role_key in role_keys if not self.has_role(role_key)]

    def get_label(self, node_path):
        """Gets a short label for a node, preferring its role.

        Args:
            node_path (str): Node path.

        Returns:
            str: Short readable label.
        """
        for role_key, role_path in self.roles.items():
            if role_path == node_path:
                return f"{node_path.split('|')[-1]} ({role_key})"
        return str(node_path).split("|")[-1]

    # ------------------------------------------------ Scale ------------------------------------------------
    def get_meters_to_units(self, meters):
        """Converts meters to scene units.

        Args:
            meters (float): Distance in meters.

        Returns:
            float: Distance in scene units.
        """
        return meters / max(self.meters_per_unit, 1e-12)

    def get_reference_length(self):
        """Gets the length every distance threshold is scaled by.

        Biped mode uses the median measured leg length. General mode uses half of
        the vertical extent of the sampled nodes, falling back to 0.9 meters.

        Returns:
            float: Reference length in scene units.
        """
        if self._reference_length is not None:
            return self._reference_length
        reference_length = 0.0
        if self.mode == MODE_BIPED:
            reference_length = self.measure_leg_length()
        if reference_length <= 1e-6:
            reference_length = self.measure_vertical_extent() * 0.5
        if reference_length <= 1e-6:
            reference_length = self.get_meters_to_units(GENERAL_FALLBACK_REFERENCE_METERS)
        self._reference_length = reference_length
        return reference_length

    def measure_leg_length(self):
        """Measures the median thigh plus shin length of both legs.

        Returns:
            float: Leg length, or 0.0 when the leg roles are unavailable.
        """
        lengths = []
        for side in ("left", "right"):
            hip = self.get_role_positions(f"{side}_up_leg")
            knee = self.get_role_positions(f"{side}_leg")
            ankle = self.get_role_positions(f"{side}_foot")
            if not hip or not knee or not ankle:
                continue
            for frame_index in range(self.frame_count):
                lengths.append(
                    math_utils.distance(hip[frame_index], knee[frame_index])
                    + math_utils.distance(knee[frame_index], ankle[frame_index])
                )
        return math_utils.median(lengths)

    def measure_vertical_extent(self):
        """Measures the vertical extent of the sampled nodes on the first frame.

        Returns:
            float: Height range in scene units.
        """
        heights = [self.get_positions(path)[0][1] for path in self.node_paths if self.get_positions(path)]
        if len(heights) < 2:
            return 0.0
        return max(heights) - min(heights)

    def get_speed_nodes(self):
        """Gets nodes whose travel speed represents the character speed.

        Returns:
            list: Hips in biped mode when available, otherwise the top-level sampled nodes.
        """
        if self.mode == MODE_BIPED and self.has_role("hips"):
            return [self.get_role_path("hips")]
        return self.get_root_nodes()

    def get_character_speeds(self):
        """Gets smoothed planar speed of the character in scene units per second.

        Returns:
            list: Speed per frame.
        """
        if "character_speeds" not in self.cache:
            speed_nodes = self.get_speed_nodes()
            if not speed_nodes:
                self.cache["character_speeds"] = [0.0] * self.frame_count
            else:
                speeds = math_utils.speeds(self.get_positions(speed_nodes[0]), self.fps, planar=True)
                window = max(3, int(round(self.fps * 0.2)))
                self.cache["character_speeds"] = math_utils.moving_average(speeds, window)
        return self.cache["character_speeds"]


def format_frame_spans(spans, start_frame, max_spans=12):
    """Converts index spans into frame-number spans for reports.

    Args:
        spans (list): Inclusive [start, end] index spans.
        start_frame (int): Frame number of index zero.
        max_spans (int): Maximum spans returned.

    Returns:
        list: Inclusive [start_frame, end_frame] spans.
    """
    return [[start + start_frame, end + start_frame] for start, end in spans[:max_spans]]
