"""Unit tests for Connect Attributes state and validation."""

import unittest

from gt.tools.connect_attributes.connect_attributes_model import ConnectAttributesModel


class MockPreferences:
    """Small Prefs-compatible test double."""

    def __init__(self, values=None):
        """Initializes stored values.

        Args:
            values (dict, optional): Initial preference values.
        """
        self.values = dict(values or {})
        self.save_count = 0

    def get_raw_preferences(self):
        """Gets stored values.

        Returns:
            dict: Stored preference values.
        """
        return dict(self.values)

    def set_raw_preferences(self, pref_dict):
        """Replaces stored values.

        Args:
            pref_dict (dict): New preference values.
        """
        self.values = dict(pref_dict)

    def save(self):
        """Records a save call."""
        self.save_count += 1


class TestConnectAttributesModel(unittest.TestCase):
    """Tests pure model behavior outside Maya."""

    def test_parse_attributes_cleans_and_deduplicates(self):
        """Parses only unique non-empty attribute names."""
        result = ConnectAttributesModel.parse_attributes(" translateX, , visibility, translateX ")

        expected = ["translateX", "visibility"]
        self.assertEqual(expected, result)

    def test_load_preferences_sanitizes_unsupported_choices(self):
        """Falls back to defaults for unsupported enum-like preferences."""
        preferences = MockPreferences(
            {
                "operation": "invalid",
                "utility_node_type": "unknownNode",
                "source_attribute": "rotateY",
            }
        )

        model = ConnectAttributesModel(preferences=preferences)

        self.assertEqual("connect", model.settings.get("operation"))
        self.assertEqual("plusMinusAverage", model.settings.get("utility_node_type"))
        self.assertEqual("rotateY", model.settings.get("source_attribute"))

    def test_set_setting_saves_known_value(self):
        """Saves a supported setting through the injected Prefs object."""
        preferences = MockPreferences()
        model = ConnectAttributesModel(preferences=preferences)

        result = model.set_setting("force_connection", True)

        self.assertTrue(result)
        self.assertTrue(preferences.values.get("force_connection"))
        self.assertEqual(1, preferences.save_count)

    def test_set_setting_rejects_unknown_key(self):
        """Does not add arbitrary preference keys."""
        model = ConnectAttributesModel(preferences=MockPreferences())

        result = model.set_setting("unknown", True)

        self.assertFalse(result)
        self.assertNotIn("unknown", model.settings)

    def test_build_connect_request_uses_ordered_selection(self):
        """Treats the first selected node as source and the rest as targets."""
        model = ConnectAttributesModel(preferences=MockPreferences())

        request, issues = model.build_request(["source", "targetA", "targetB", "targetA"])

        self.assertEqual("source", request.get("source_object"))
        self.assertEqual(["targetA", "targetB"], request.get("target_objects"))
        self.assertEqual([], issues)

    def test_build_disconnect_request_uses_every_selected_node(self):
        """Treats every selected node as a target while disconnecting."""
        model = ConnectAttributesModel(preferences=MockPreferences())
        model.set_setting("operation", "disconnect", save=False)

        request, issues = model.build_request(["targetA", "targetB"])

        self.assertIsNone(request.get("source_object"))
        self.assertEqual(["targetA", "targetB"], request.get("target_objects"))
        self.assertEqual([], issues)

    def test_loaded_nodes_are_not_written_to_preferences(self):
        """Keeps scene-specific object names out of persistent preferences."""
        preferences = MockPreferences()
        model = ConnectAttributesModel(preferences=preferences)
        model.set_source_object("sceneSource")
        model.set_target_objects(["sceneTarget"])

        model.save_preferences()

        self.assertNotIn("source_object", preferences.values)
        self.assertNotIn("target_objects", preferences.values)

    def test_build_preview_lines_lists_direct_connections(self):
        """Lists every source-to-target plug combination."""
        request = {
            "operation": "connect",
            "source_object": "source",
            "source_attribute": "output",
            "target_objects": ["targetA", "targetB"],
            "target_attributes": ["translateX", "visibility"],
            "use_utility_node": False,
            "add_reverse_node": False,
        }

        result = ConnectAttributesModel.build_preview_lines(request)

        expected = [
            "source.output -> targetA.translateX",
            "source.output -> targetA.visibility",
            "source.output -> targetB.translateX",
            "source.output -> targetB.visibility",
        ]
        self.assertEqual(expected, result)

    def test_build_preview_lines_describes_connection_chain(self):
        """Includes requested utility and reverse nodes in the preview chain."""
        request = {
            "operation": "connect",
            "source_object": "source",
            "source_attribute": "output",
            "target_objects": ["target"],
            "target_attributes": ["input"],
            "use_utility_node": True,
            "utility_node_type": "multiplyDivide",
            "add_reverse_node": True,
        }

        result = ConnectAttributesModel.build_preview_lines(request)

        expected = ["source.output -> [multiplyDivide] -> [reverse] -> target.input"]
        self.assertEqual(expected, result)

    def test_build_preview_lines_lists_disconnections(self):
        """Lists every target plug whose incoming connection would be removed."""
        request = {
            "operation": "disconnect",
            "target_objects": ["target"],
            "target_attributes": ["translateX", "visibility"],
        }

        result = ConnectAttributesModel.build_preview_lines(request)

        expected = [
            "Disconnect incoming -> target.translateX",
            "Disconnect incoming -> target.visibility",
        ]
        self.assertEqual(expected, result)

    def test_reset_preferences_restores_defaults(self):
        """Restores and saves all default settings."""
        preferences = MockPreferences()
        model = ConnectAttributesModel(preferences=preferences)
        model.set_setting("source_attribute", "customAttr", save=False)

        model.reset_preferences()

        self.assertEqual(ConnectAttributesModel.DEFAULT_SETTINGS, model.settings)
        self.assertEqual(ConnectAttributesModel.DEFAULT_SETTINGS, preferences.values)


if __name__ == "__main__":
    unittest.main()
