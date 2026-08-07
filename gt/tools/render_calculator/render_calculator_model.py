"""Pure Python model for the Render Calculator tool."""

import datetime
import logging


logger = logging.getLogger(__name__)

UNIT_LABELS = ("Second(s)", "Minute(s)", "Hour(s)")
MAX_INPUT_VALUE = 999999
PREFS_NAME = "render_calculator"


def calculate_render_time(input_time, num_frames=1, num_machines=1, unit="seconds"):
    """Calculates a human-readable render duration.

    Args:
        input_time (int): Average time required to render one frame.
        num_frames (int): Number of frames to render.
        num_machines (int): Number of machines sharing the render.
        unit (str): Unit used by ``input_time``. Supports seconds, minutes,
            and hours.

    Returns:
        str: Duration formatted as one non-empty unit per line.

    Raises:
        ValueError: If a frame count or machine count is not positive.
    """
    if num_frames <= 0:
        raise ValueError("The number of frames must be greater than zero.")
    if num_machines <= 0:
        raise ValueError("The number of machines must be greater than zero.")

    processed_time = int(input_time * num_frames / num_machines)
    unit_multipliers = {"seconds": 1, "minutes": 60, "hours": 60 * 60}
    normalized_unit = str(unit or "").lower()
    if normalized_unit not in unit_multipliers:
        logger.warning("Unable to determine unit. Using seconds.")
        normalized_unit = "seconds"

    total_seconds = processed_time * unit_multipliers[normalized_unit]
    duration_components = _get_duration_components(total_seconds)
    duration_parts = []
    duration_names = ("year", "month", "day", "hour", "minute", "second")
    for value, unit_name in zip(duration_components, duration_names):
        if value > 0:
            plural_suffix = "" if value == 1 else "s"
            duration_parts.append(f" {value} {unit_name}{plural_suffix}\n")
    return "".join(duration_parts)


def _get_duration_components(total_seconds):
    """Splits seconds into calendar-based duration components.

    Args:
        total_seconds (int): Total duration in seconds.

    Returns:
        tuple: Years, months, days, hours, minutes, and seconds.
    """
    try:
        duration_date = datetime.datetime(1, 1, 1) + datetime.timedelta(
            seconds=total_seconds
        )
        return (
            duration_date.year - 1,
            duration_date.month - 1,
            duration_date.day - 1,
            duration_date.hour,
            duration_date.minute,
            duration_date.second,
        )
    except OverflowError:
        return _get_large_duration_components(total_seconds)


def _get_large_duration_components(total_seconds):
    """Splits a duration too large for ``datetime`` using Gregorian cycles.

    Args:
        total_seconds (int): Total duration in seconds.

    Returns:
        tuple: Years, months, days, hours, minutes, and seconds.
    """
    seconds_per_day = 24 * 60 * 60
    total_days, remaining_seconds = divmod(total_seconds, seconds_per_day)
    hours, remaining_seconds = divmod(remaining_seconds, 60 * 60)
    minutes, seconds = divmod(remaining_seconds, 60)

    cycle_days = 146097
    cycle_count, remaining_days = divmod(total_days, cycle_days)
    years = cycle_count * 400
    for year_offset in range(400):
        days_in_year = 366 if _is_leap_year(year_offset + 1) else 365
        if remaining_days < days_in_year:
            years += year_offset
            break
        remaining_days -= days_in_year

    month_lengths = [
        31,
        29 if _is_leap_year(years + 1) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]
    months = 0
    for days_in_month in month_lengths:
        if remaining_days < days_in_month:
            break
        remaining_days -= days_in_month
        months += 1

    return years, months, remaining_days, hours, minutes, seconds


def _is_leap_year(year):
    """Determines whether a Gregorian calendar year is a leap year.

    Args:
        year (int): Calendar year to inspect.

    Returns:
        bool: True when the year contains a leap day.
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


class RenderCalculatorModel:
    """Stores calculator inputs and produces the render-time summary."""

    def __init__(self, time_per_frame=1, num_frames=1, num_machines=1,
                 unit="Second(s)", preferences=None):
        """Initializes the calculator state.

        Args:
            time_per_frame (int): Average render time for one frame.
            num_frames (int): Number of frames to render.
            num_machines (int): Number of machines sharing the render.
            unit (str): Display label or normalized key for the time unit.
            preferences (Prefs, optional): Injected preference object for tests
                or custom preference locations.
        """
        self._preferences = preferences
        self.has_persisted_frame_count = False
        self.time_per_frame = self._normalize_input(time_per_frame)
        self.num_frames = self._normalize_input(num_frames)
        self.num_machines = self._normalize_input(num_machines)
        self.unit = self.normalize_unit(unit)
        self.load_preferences()

    def _get_preferences(self):
        """Gets or lazily creates the Render Calculator preferences.

        Returns:
            Prefs or None: Preference object when available.
        """
        if self._preferences is not None:
            return self._preferences
        try:
            from gt.core.prefs import Prefs

            self._preferences = Prefs(PREFS_NAME)
        except Exception as exception:
            logger.debug("Unable to initialize Render Calculator preferences: %s", exception)
        return self._preferences

    def load_preferences(self):
        """Loads saved numeric values and the selected unit from Prefs."""
        preferences = self._get_preferences()
        if not preferences:
            return
        try:
            stored_values = preferences.get_raw_preferences() or {}
        except Exception as exception:
            logger.debug("Unable to load Render Calculator preferences: %s", exception)
            return
        if not isinstance(stored_values, dict):
            return

        self.time_per_frame = self._normalize_input(
            stored_values.get("time_per_frame", self.time_per_frame)
        )
        self.num_frames = self._normalize_input(
            stored_values.get("num_frames", self.num_frames)
        )
        self.num_machines = self._normalize_input(
            stored_values.get("num_machines", self.num_machines)
        )
        self.unit = self.normalize_unit(stored_values.get("unit", self.unit))
        self.has_persisted_frame_count = "num_frames" in stored_values

    def save_preferences(self):
        """Saves all calculator values through Prefs.

        Returns:
            bool: True when preferences were saved successfully.
        """
        preferences = self._get_preferences()
        if not preferences:
            return False
        settings = {
            "time_per_frame": self.time_per_frame,
            "num_frames": self.num_frames,
            "num_machines": self.num_machines,
            "unit": self.unit,
        }
        try:
            preferences.set_raw_preferences(settings)
            preferences.save()
            return True
        except Exception as exception:
            logger.warning("Unable to save Render Calculator preferences: %s", exception)
            return False

    @staticmethod
    def _normalize_input(value):
        """Normalizes a positive calculator input to the UI range.

        Args:
            value (int): Value supplied by a UI control or caller.

        Returns:
            int: Clamped positive integer.
        """
        try:
            normalized_value = int(value)
        except (TypeError, ValueError):
            normalized_value = 1
        return max(1, min(MAX_INPUT_VALUE, normalized_value))

    @staticmethod
    def normalize_unit(unit):
        """Normalizes a display unit label to its calculation key.

        Args:
            unit (str): Display label or calculation key.

        Returns:
            str: One of seconds, minutes, or hours.
        """
        normalized_unit = str(unit or "").strip().lower().replace("(s)", "s")
        if normalized_unit.startswith("second"):
            return "seconds"
        if normalized_unit.startswith("minute"):
            return "minutes"
        if normalized_unit.startswith("hour"):
            return "hours"
        return "seconds"

    def set_time_per_frame(self, value):
        """Updates the average render time for one frame.

        Args:
            value (int): New time-per-frame value.
        """
        self.time_per_frame = self._normalize_input(value)
        self.save_preferences()

    def set_num_frames(self, value):
        """Updates the number of frames in the render.

        Args:
            value (int): New frame count.
        """
        self.num_frames = self._normalize_input(value)
        self.has_persisted_frame_count = True
        self.save_preferences()

    def set_num_machines(self, value):
        """Updates the number of machines sharing the render.

        Args:
            value (int): New machine count.
        """
        self.num_machines = self._normalize_input(value)
        self.save_preferences()

    def set_unit(self, value):
        """Updates the selected time unit.

        Args:
            value (str): New display label or calculation key.
        """
        self.unit = self.normalize_unit(value)
        self.save_preferences()

    def reset_numbers(self):
        """Resets all numeric inputs to one and persists the values."""
        self.time_per_frame = 1
        self.num_frames = 1
        self.num_machines = 1
        self.unit = "seconds"
        self.has_persisted_frame_count = True
        self.save_preferences()

    def get_unit_label(self):
        """Gets the display label for the selected unit.

        Returns:
            str: Human-readable unit label.
        """
        labels_by_unit = {
            "seconds": "Second(s)",
            "minutes": "Minute(s)",
            "hours": "Hour(s)",
        }
        return labels_by_unit[self.unit]

    def get_render_summary(self):
        """Builds the multiline result shown by the view.

        Returns:
            str: Current render-time calculation and input summary.
        """
        result = (
            f"Time per frame {self.time_per_frame} "
            f"{self.get_unit_label().lower()}\n"
        )
        result += f"Frame Count {self.num_frames} frames(s)\n"
        result += "Total render time:\n"
        result += calculate_render_time(
            self.time_per_frame,
            self.num_frames,
            self.num_machines,
            unit=self.unit,
        )
        if self.num_machines != 1:
            result += f"Per computer (Number of computers: {self.num_machines})"
        return result
