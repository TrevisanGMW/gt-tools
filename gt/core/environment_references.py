"""Import-safe helpers for finding where environment-variable tokens are used.

Tools describe their data as a list of "sources". Each source is a dictionary
with the following keys:

    kind (str): Source category, such as "task", "module", "variable", or "project".
    id (str): Stable identifier used to navigate back to the source.
    label (str): User-facing name of the source.
    enabled (bool, optional): Whether the source is active. Defaults to True.
    data (object): JSON-compatible data scanned for tokens.
    defines (str, optional): Token key defined by this source. References found in
        a defining source make that token depend on the referenced tokens, which is
        used to report indirect uses.

References are returned as plain dictionaries so they remain easy to test,
serialize, and display.
"""

import re

TOKEN_PATTERN = re.compile(r"\{([a-zA-Z0-9_-]+)\}")
SNIPPET_MAX_LENGTH = 160


def strip_token_braces(token):
    """Removes surrounding whitespace and braces from a token.

    Args:
        token (str): Braced or unbraced token.

    Returns:
        str: Token key without braces.
    """
    return str(token or "").strip().strip("{}")


def build_code_access_pattern(code_names):
    """Builds a pattern that finds dictionary-style token access in code.

    Matches expressions such as ``env["output-dir"]`` and ``env.get('output-dir')``.

    Args:
        code_names (list, tuple): Names of variables exposing tokens in code.

    Returns:
        re.Pattern or None: Compiled pattern, or None when no names are provided.
    """
    names = [re.escape(name) for name in code_names or () if name]
    if not names:
        return None
    joined_names = "|".join(names)
    return re.compile(
        rf"\b(?:{joined_names})\s*(?:\[\s*|\.get\(\s*)(['\"])([a-zA-Z0-9_-]+)\1"
    )


def iter_text_fields(data, field_path=""):
    """Yields every string stored in nested JSON-compatible data.

    Args:
        data (object): Dictionary, list, tuple, string, or other value.
        field_path (str, optional): Path of ``data`` inside its source.

    Yields:
        tuple: Field path (str) and text value (str).
    """
    if isinstance(data, str):
        yield field_path, data
    elif isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{field_path}.{key}" if field_path else str(key)
            for item in iter_text_fields(value, child_path):
                yield item
    elif isinstance(data, (list, tuple)):
        for index, value in enumerate(data):
            for item in iter_text_fields(value, f"{field_path}[{index}]"):
                yield item


def build_snippet(text, start_index):
    """Gets the trimmed line containing a match.

    Args:
        text (str): Full field text.
        start_index (int): Character index of the match.

    Returns:
        str: Single-line snippet around the match.
    """
    line_start = text.rfind("\n", 0, start_index) + 1
    line_end = text.find("\n", start_index)
    if line_end < 0:
        line_end = len(text)
    raw_line = text[line_start:line_end]
    line_text = raw_line.strip()
    if len(line_text) <= SNIPPET_MAX_LENGTH:
        return line_text
    leading_whitespace = len(raw_line) - len(raw_line.lstrip())
    match_offset = start_index - line_start - leading_whitespace
    window_start = max(0, match_offset - SNIPPET_MAX_LENGTH // 2)
    snippet = line_text[window_start:window_start + SNIPPET_MAX_LENGTH]
    prefix = "..." if window_start > 0 else ""
    suffix = "..." if window_start + SNIPPET_MAX_LENGTH < len(line_text) else ""
    return f"{prefix}{snippet}{suffix}"


def find_tokens_in_text(text, normalize_key=None, code_pattern=None):
    """Finds token keys used in a string.

    Args:
        text (str): Text to scan.
        normalize_key (callable, optional): Converts a raw token key to the key
            used by the tool. Defaults to removing braces only.
        code_pattern (re.Pattern, optional): Pattern from ``build_code_access_pattern``.

    Returns:
        list: Tuples of (key, first_index, count) in first-use order.
    """
    normalize_key = normalize_key or strip_token_braces
    found_tokens = {}
    raw_matches = [(match.group(1), match.start()) for match in TOKEN_PATTERN.finditer(text)]
    if code_pattern is not None:
        raw_matches.extend(
            (match.group(2), match.start()) for match in code_pattern.finditer(text)
        )
    for raw_key, start_index in sorted(raw_matches, key=lambda raw_match: raw_match[1]):
        key = normalize_key(raw_key)
        if not key:
            continue
        if key in found_tokens:
            found_tokens[key][1] += 1
        else:
            found_tokens[key] = [start_index, 1]
    return [(key, values[0], values[1]) for key, values in found_tokens.items()]


def find_direct_references(sources, normalize_key=None, code_names=()):
    """Finds every direct token use in the provided sources.

    Args:
        sources (list): Source dictionaries described in this module docstring.
        normalize_key (callable, optional): Converts raw token keys to tool keys.
        code_names (list, tuple, optional): Code variable names that expose tokens,
            such as ``("env",)``.

    Returns:
        list: Reference dictionaries with token, source, field, line, count, and snippet data.
    """
    code_pattern = build_code_access_pattern(code_names)
    references = []
    for source in sources or []:
        for field_path, text in iter_text_fields(source.get("data")):
            for key, start_index, count in find_tokens_in_text(
                text, normalize_key=normalize_key, code_pattern=code_pattern
            ):
                references.append(
                    {
                        "token": key,
                        "source_kind": source.get("kind", ""),
                        "source_id": source.get("id", ""),
                        "source_label": source.get("label", ""),
                        "enabled": bool(source.get("enabled", True)),
                        "defines": source.get("defines") or "",
                        "field": field_path,
                        "line": text.count("\n", 0, start_index) + 1,
                        "count": count,
                        "snippet": build_snippet(text, start_index),
                        "via": [],
                    }
                )
    return references


def find_indirect_references(direct_references):
    """Finds uses that reach a token through variables that reference it.

    For example, when ``{output-dir}`` is defined as ``{project-dir}/out`` and a task
    uses ``{output-dir}``, that task indirectly uses ``{project-dir}`` via
    ``output-dir``. Chains are followed with a loop guard.

    Args:
        direct_references (list): References returned by ``find_direct_references``.

    Returns:
        list: Indirect reference dictionaries whose ``via`` lists the variable chain.
    """
    dependents_by_token = {}
    uses_by_token = {}
    for reference in direct_references:
        defined_key = reference.get("defines")
        if defined_key:
            dependents = dependents_by_token.setdefault(reference["token"], [])
            if defined_key not in dependents and defined_key != reference["token"]:
                dependents.append(defined_key)
        else:
            uses_by_token.setdefault(reference["token"], []).append(reference)

    indirect_references = []
    for token in list(dependents_by_token):
        visited_keys = {token}
        pending_chains = [[dependent] for dependent in dependents_by_token[token]]
        while pending_chains:
            chain = pending_chains.pop(0)
            variable_key = chain[-1]
            if variable_key in visited_keys:
                continue
            visited_keys.add(variable_key)
            for reference in uses_by_token.get(variable_key, []):
                indirect_reference = dict(reference)
                indirect_reference["token"] = token
                indirect_reference["via"] = list(chain)
                indirect_references.append(indirect_reference)
            for dependent in dependents_by_token.get(variable_key, []):
                if dependent not in visited_keys:
                    pending_chains.append(chain + [dependent])
    return indirect_references


def find_references(sources, normalize_key=None, code_names=()):
    """Finds direct and indirect token uses grouped by token key.

    Args:
        sources (list): Source dictionaries described in this module docstring.
        normalize_key (callable, optional): Converts raw token keys to tool keys.
        code_names (list, tuple, optional): Code variable names that expose tokens.

    Returns:
        dict: Token key (str) mapped to a list of reference dictionaries. Direct
            references come first, followed by indirect ones, each in source order.
    """
    direct_references = find_direct_references(
        sources, normalize_key=normalize_key, code_names=code_names
    )
    references_by_token = {}
    for reference in direct_references + find_indirect_references(direct_references):
        references_by_token.setdefault(reference["token"], []).append(reference)
    return references_by_token


def summarize_references(references, kind_labels=None):
    """Builds a short, user-facing summary for a token's references.

    Args:
        references (list): References for one token.
        kind_labels (dict, optional): Source kind mapped to (singular, plural) labels.

    Returns:
        str: Summary such as "2 tasks, 1 variable (+3 indirect)", or "" when unused.
    """
    kind_labels = kind_labels or {}
    direct_sources = {}
    indirect_sources = set()
    for reference in references or []:
        source_key = (
            reference.get("source_kind"),
            reference.get("source_id"),
            reference.get("defines"),
        )
        if reference.get("via"):
            indirect_sources.add(source_key)
        else:
            direct_sources.setdefault(reference.get("source_kind"), set()).add(source_key)

    parts = []
    for kind, kind_sources in direct_sources.items():
        singular, plural = kind_labels.get(kind, ("reference", "references"))
        count = len(kind_sources)
        parts.append(f"{count} {singular if count == 1 else plural}")
    summary = ", ".join(parts)
    if indirect_sources:
        indirect_text = f"{len(indirect_sources)} indirect"
        summary = f"{summary} (+{indirect_text})" if summary else indirect_text
    return summary
