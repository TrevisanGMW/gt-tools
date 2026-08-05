"""Model and pure helpers for the Shape Text to Curve tool."""

import logging
import re


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_FONT = "MS Shell Dlg 2"
DEFAULT_TEXT = "hello, world"


def parse_text_entries(raw_text):
    """Parses comma-separated or newline-separated text into non-empty entries.

    Args:
        raw_text (str): Text entered by the user.

    Returns:
        list: Clean, non-empty text entries in input order.
    """
    if not isinstance(raw_text, str):
        return []
    return [entry.strip() for entry in re.split(r"[,\n]", raw_text) if entry.strip()]


class ShapeTextToCurveModel:
    """Stores tool state and creates text curves through the shared curve API."""

    def __init__(self, font=DEFAULT_FONT, curve_factory=None):
        """Initializes the Shape Text to Curve model.

        Args:
            font (str, optional): Initial Maya font descriptor.
            curve_factory (callable, optional): Function used to create a curve.
        """
        self.font = font or DEFAULT_FONT
        self._curve_factory = curve_factory

    def set_font(self, font):
        """Sets the Maya font descriptor used for new curves.

        Args:
            font (str): Maya font descriptor returned by ``fontDialog``.

        Returns:
            bool: True when a valid font was stored.
        """
        if not isinstance(font, str) or not font.strip():
            return False
        self.font = font.strip()
        return True

    def get_font_display_name(self):
        """Gets the concise family name shown in the interface.

        Returns:
            str: Font family name.
        """
        return self.font.split("|", 1)[0]

    def generate_curves(self, raw_text):
        """Creates one text curve for each parsed text entry.

        Args:
            raw_text (str): Comma-separated text entries.

        Returns:
            list: Names of the created Maya curve transforms.
        """
        text_entries = parse_text_entries(raw_text)
        if not text_entries:
            return []

        curve_factory = self._curve_factory
        if curve_factory is None:
            from gt.core import curve as core_curve

            curve_factory = core_curve.create_text

        created_curves = []
        for text_entry in text_entries:
            created_curves.append(curve_factory(text=text_entry, font=self.font))
        logger.info("Created %s text curve(s).", len(created_curves))
        return created_curves
