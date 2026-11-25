"""Maya time-unit choices for generated scenes."""

# Matches the FPS entries in Maya 2025's Time Slider menu.
TIME_UNITS = (
    ("2 FPS", "2fps"), ("3 FPS", "3fps"), ("4 FPS", "4fps"), ("5 FPS", "5fps"),
    ("6 FPS", "6fps"), ("8 FPS", "8fps"), ("10 FPS", "10fps"), ("12 FPS", "12fps"),
    ("15 FPS (Game)", "game"), ("16 FPS", "16fps"), ("20 FPS", "20fps"),
    ("23.976 FPS", "23.976fps"), ("24 FPS (Film)", "film"), ("25 FPS (PAL)", "pal"),
    ("29.97 FPS", "29.97fps"), ("29.97 FPS Drop Frame", "29.97df"), ("30 FPS (NTSC)", "ntsc"),
    ("40 FPS", "40fps"), ("47.952 FPS", "47.952fps"), ("48 FPS (Show)", "show"),
    ("50 FPS (PAL Field)", "palf"), ("59.94 FPS", "59.94fps"), ("60 FPS (NTSC Field)", "ntscf"),
    ("75 FPS", "75fps"), ("80 FPS", "80fps"), ("90 FPS", "90fps"), ("100 FPS", "100fps"),
    ("119.88 FPS", "119.88fps"), ("120 FPS", "120fps"), ("125 FPS", "125fps"),
    ("150 FPS", "150fps"), ("200 FPS", "200fps"), ("240 FPS", "240fps"),
    ("250 FPS", "250fps"), ("300 FPS", "300fps"), ("375 FPS", "375fps"),
    ("400 FPS", "400fps"), ("500 FPS", "500fps"), ("600 FPS", "600fps"),
    ("750 FPS", "750fps"), ("1200 FPS", "1200fps"), ("1500 FPS", "1500fps"),
    ("2000 FPS", "2000fps"), ("3000 FPS", "3000fps"), ("6000 FPS", "6000fps"),
    ("44100 FPS", "44100fps"), ("48000 FPS", "48000fps"),
)


def valid_time_unit(value):
    """Checks a saved output time unit, including the empty model-rate default.

    Args:
        value (str): Maya time unit or empty string.

    Returns:
        bool: Whether the unit is supported.
    """
    return value == "" or value in {unit for label, unit in TIME_UNITS}
