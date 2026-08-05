"""Tests for Retargeter preferences."""

import unittest

from gt.tools.retargeter import retargeter_preferences


class MockPrefs:
    """In-memory replacement for the shared Prefs backend."""

    def __init__(self, values=None):
        """Initializes the backend.

        Args:
            values (dict, optional): Initial preference values.
        """
        self.preferences = dict(values or {})
        self.saved = False

    def load(self):
        """Loads preferences from memory."""

    def get_raw_preferences(self):
        """Gets stored values.

        Returns:
            dict: Stored preferences.
        """
        return self.preferences

    def set_raw_preferences(self, values):
        """Replaces stored values.

        Args:
            values (dict): New preferences.
        """
        self.preferences = dict(values)

    def save(self):
        """Marks the backend as saved."""
        self.saved = True


class TestRetargeterPreferences(unittest.TestCase):
    """Tests the explicit preference schema and persistence."""

    def test_defaults_are_available(self):
        """Tests that defaults populate an empty backend."""
        preferences = retargeter_preferences.RetargeterPreferences(MockPrefs())

        expected = True
        result = preferences.get("skip_existing_files")

        self.assertEqual(expected, result)

    def test_load_ignores_unknown_keys(self):
        """Tests that old view attributes are not serialized implicitly."""
        backend = MockPrefs({"skip_existing_files": False, "unexpected_widget_state": 10})
        preferences = retargeter_preferences.RetargeterPreferences(backend)

        expected = False
        result = preferences.get("skip_existing_files")

        self.assertEqual(expected, result)
        self.assertNotIn("unexpected_widget_state", preferences.as_dict())

    def test_constrained_values_are_sanitized(self):
        """Tests that tab and worker values stay inside their UI ranges."""
        backend = MockPrefs({"active_tab": 99, "multi_process_max_instances": 0})
        preferences = retargeter_preferences.RetargeterPreferences(backend)

        expected = (2, 1)
        result = (
            preferences.get("active_tab"),
            preferences.get("multi_process_max_instances"),
        )

        self.assertEqual(expected, result)

    def test_save_writes_only_schema_values(self):
        """Tests that saving writes a deterministic preference payload."""
        backend = MockPrefs({"unknown": "value"})
        preferences = retargeter_preferences.RetargeterPreferences(backend)
        preferences.set("batch_status", True)

        preferences.save()

        self.assertTrue(backend.saved)
        self.assertEqual(retargeter_preferences.PREFERENCE_DEFAULTS.keys(), backend.preferences.keys())
        self.assertTrue(backend.preferences["batch_status"])


if __name__ == "__main__":
    unittest.main()
