"""Pure name filtering for the cleanup utility option windows."""

from gt.core import str as core_str


MATCH_MODES = ("Starts With", "Contains", "Ends With")


def get_names_to_delete(names, ignore_text="", match_mode="Starts With", namespaces=False):
    """Filters deletion candidates while preserving ignored namespace hierarchies.

    Args:
        names (list): Display layer names or root-relative namespace paths.
        ignore_text (str, optional): Literal, case-sensitive text to ignore.
        match_mode (str, optional): One of ``MATCH_MODES``.
        namespaces (bool, optional): Protect ancestors and descendants of matches.

    Returns:
        list: Deletion candidates in their original order.

    Raises:
        ValueError: If the matching mode is unsupported.
    """
    matchers = {
        "Starts With": core_str.filter_strings_by_prefix,
        "Contains": core_str.filter_strings_containing,
        "Ends With": core_str.filter_strings_by_suffix,
    }
    if match_mode not in matchers:
        raise ValueError(f"Unsupported name matching mode: {match_mode}")
    if not ignore_text:
        return list(names)
    ignored_names = set(matchers[match_mode](names, ignore_text))
    if not namespaces:
        return [name for name in names if name not in ignored_names]
    return [
        name for name in names
        if not any(
            name == ignored
            or name.startswith(f"{ignored}:")
            or ignored.startswith(f"{name}:")
            for ignored in ignored_names
        )
    ]
