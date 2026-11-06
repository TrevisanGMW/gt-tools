"""Tests for finding where environment-variable tokens are used."""

import os
import sys
import unittest

tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.core.environment_references as core_env_refs


class TestEnvironmentReferences(unittest.TestCase):
    """Tests the import-safe reference scanner."""

    def test_find_tokens_in_text_counts_uses_in_first_use_order(self):
        """Finds braced tokens once per key with their use counts."""
        text = "{output-dir}/{task-name}/{output-dir}"

        expected = [("output-dir", 0, 2), ("task-name", 13, 1)]
        result = core_env_refs.find_tokens_in_text(text)
        self.assertEqual(expected, result)

    def test_find_tokens_in_text_finds_code_access(self):
        """Finds env[...] and env.get(...) access when code names are provided."""
        code_pattern = core_env_refs.build_code_access_pattern(("env",))
        text = "path = env['output-dir']\nname = env.get(\"task-name\", '')\nother['x']"

        expected = ["output-dir", "task-name"]
        result = [
            key for key, _index, _count in core_env_refs.find_tokens_in_text(
                text, code_pattern=code_pattern
            )
        ]
        self.assertEqual(expected, result)

    def test_find_tokens_in_text_applies_normalizer(self):
        """Uses the tool normalizer to merge spellings of the same token."""
        text = "{Output_Dir} and {output-dir}"

        expected = [("output-dir", 0, 2)]
        result = core_env_refs.find_tokens_in_text(
            text, normalize_key=lambda key: key.lower().replace("_", "-")
        )
        self.assertEqual(expected, result)

    def test_direct_references_record_nested_field_line_and_snippet(self):
        """Records list and dictionary field paths with the matching line."""
        sources = [
            {
                "kind": "task",
                "id": "task-a",
                "label": "#01 Export",
                "enabled": False,
                "data": {"parameters": {"items": [1, {"code": "a = 1\nb = '{output-dir}'"}]}},
            }
        ]

        result = core_env_refs.find_direct_references(sources)
        self.assertEqual(1, len(result))
        reference = result[0]
        self.assertEqual("output-dir", reference["token"])
        self.assertEqual("parameters.items[1].code", reference["field"])
        self.assertEqual(2, reference["line"])
        self.assertEqual("b = '{output-dir}'", reference["snippet"])
        self.assertFalse(reference["enabled"])
        self.assertEqual([], reference["via"])

    def test_find_references_follows_variable_chains(self):
        """Reports task uses of a variable built from another variable as indirect."""
        sources = [
            {"kind": "variable", "id": "out", "label": "{out}", "data": "{root}/out", "defines": "out"},
            {"kind": "variable", "id": "fbx", "label": "{fbx}", "data": "{out}/fbx", "defines": "fbx"},
            {"kind": "task", "id": "task-a", "label": "#01 Export", "data": {"path": "{fbx}/a.fbx"}},
        ]

        result = core_env_refs.find_references(sources)
        root_references = result["root"]
        expected = [([], "variable"), (["out", "fbx"], "task")]
        self.assertEqual(
            expected,
            [(reference["via"], reference["source_kind"]) for reference in root_references],
        )
        expected = [([], "variable"), (["fbx"], "task")]
        self.assertEqual(
            expected,
            [(reference["via"], reference["source_kind"]) for reference in result["out"]],
        )

    def test_find_references_stops_on_loops(self):
        """Avoids infinite loops when variables reference each other."""
        sources = [
            {"kind": "variable", "id": "a", "label": "{a}", "data": "{b}", "defines": "a"},
            {"kind": "variable", "id": "b", "label": "{b}", "data": "{a}", "defines": "b"},
            {"kind": "task", "id": "task", "label": "Task", "data": "{a}"},
        ]

        result = core_env_refs.find_references(sources)
        expected = [[], ["a"]]
        self.assertEqual(expected, [reference["via"] for reference in result["b"]])

    def test_summarize_references_counts_sources_by_kind(self):
        """Counts distinct direct sources by kind and adds indirect sources."""
        references = [
            {"source_kind": "task", "source_id": "a", "defines": "", "via": []},
            {"source_kind": "task", "source_id": "a", "defines": "", "via": []},
            {"source_kind": "task", "source_id": "b", "defines": "", "via": []},
            {"source_kind": "variable", "source_id": "x", "defines": "x", "via": []},
            {"source_kind": "task", "source_id": "c", "defines": "", "via": ["x"]},
        ]
        kind_labels = {"task": ("task", "tasks"), "variable": ("variable", "variables")}

        expected = "2 tasks, 1 variable (+1 indirect)"
        result = core_env_refs.summarize_references(references, kind_labels)
        self.assertEqual(expected, result)
        self.assertEqual("", core_env_refs.summarize_references([], kind_labels))

    def test_build_snippet_trims_long_lines_around_match(self):
        """Keeps long snippets short while showing the matched token."""
        text = f"{'a' * 300}{{token}}{'b' * 300}"

        result = core_env_refs.build_snippet(text, 300)
        self.assertIn("{token}", result)
        self.assertTrue(result.startswith("..."))
        self.assertTrue(result.endswith("..."))


if __name__ == "__main__":
    unittest.main()
