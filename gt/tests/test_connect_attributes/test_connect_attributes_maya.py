"""Maya scene regressions for an explicitly enabled, isolated mayapy process.

Initialize Maya standalone outside this module and set
GT_CONNECT_ATTRIBUTES_MAYA_TESTS=1 before running unittest discovery.
"""

import os
import unittest

from gt.tools.connect_attributes.connect_attributes_service import ConnectAttributesService


@unittest.skipUnless(
    os.environ.get("GT_CONNECT_ATTRIBUTES_MAYA_TESTS") == "1",
    "Requires an explicitly enabled Maya standalone test process.",
)
class TestConnectAttributesMaya(unittest.TestCase):
    """Checks native Maya behavior without initializing Maya at import time."""

    def setUp(self):
        """Creates temporary nodes in a batch session and records existing nodes."""
        import maya.cmds as cmds

        self.cmds = cmds
        if not cmds.about(batch=True):
            self.skipTest("These tests require an isolated Maya batch session.")
        self.original_nodes = set(cmds.ls(long=True))
        self.source = cmds.createNode("transform", name="connectAttributesTestSource#")
        self.target = cmds.createNode("transform", name="connectAttributesTestTarget#")
        self.service = ConnectAttributesService()
        self.request = {
            "operation": "connect", "source_object": self.source, "source_attribute": "translateX",
            "target_objects": [self.target], "target_attributes": ["translateX"],
        }

    def tearDown(self):
        """Deletes only nodes created during the current test."""
        created = set(self.cmds.ls(long=True)) - self.original_nodes
        for node in created:
            if self.cmds.objExists(node):
                if self.cmds.nodeType(node) == "transform":
                    self.cmds.setAttr(f"{node}.translate", lock=False)
                    self.cmds.setAttr(f"{node}.translateX", lock=False)
                self.cmds.delete(node)

    def test_numeric_conversion_is_ready_and_idempotent(self):
        """Allows Maya unit conversion and recognizes its existing connection."""
        self.request["target_attributes"] = ["rotateX"]
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])
        result = self.service.execute(self.request)
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["succeeded"])
        self.assertTrue(self.cmds.isConnected(
            f"{self.source}.translateX", f"{self.target}.rotateX", ignoreUnitConversion=True,
        ))
        self.assertEqual("skipped", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(1, self.service.execute(self.request)["skipped"])

    def test_preview_is_read_only_with_utility_options(self):
        """Does not create utilities or change selection while inspecting a chain."""
        self.request.update(
            use_utility_node=True, utility_node_type="multiplyDivide", add_reverse_node=True,
            use_shared_input=True, shared_input_node_type="condition",
        )
        self.cmds.select(self.target)
        before_nodes = self.cmds.ls(long=True)
        before_selection = self.cmds.ls(selection=True, long=True)
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(before_nodes, self.cmds.ls(long=True))
        self.assertEqual(before_selection, self.cmds.ls(selection=True, long=True))

    def test_locked_parent_blocks_target_child(self):
        """Detects inherited locks and rechecks them during execution."""
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])
        self.cmds.setAttr(f"{self.target}.translate", lock=True)
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        result = self.service.execute(self.request)
        self.assertEqual(0, result["succeeded"])
        self.assertIn("locked", result["errors"][0])

    def test_missing_attribute_does_not_create_shared_nodes(self):
        """Reports missing target names without creating attributes or utilities."""
        self.request.update(
            target_attributes=["missingAttribute"], use_utility_node=True,
            utility_node_type="multiplyDivide", use_shared_input=True, shared_input_node_type="condition",
        )
        before_nodes = self.cmds.ls(long=True)
        result = self.service.execute(self.request)
        self.assertEqual(0, result["succeeded"])
        self.assertEqual(before_nodes, self.cmds.ls(long=True))
        self.assertFalse(self.cmds.objExists(f"{self.target}.missingAttribute"))

    def test_invert_computes_one_minus_input(self):
        """Executes a Reverse chain and evaluates its resulting scalar value."""
        self.cmds.setAttr(f"{self.source}.translateX", 0.2)
        self.request["add_reverse_node"] = True
        result = self.service.execute(self.request)
        self.assertEqual([], result["errors"])
        self.assertEqual(1, len(result["created_nodes"]))
        self.assertAlmostEqual(0.8, self.cmds.getAttr(f"{self.target}.translateX"), places=5)

    def test_vector_utility_and_shared_input_connections(self):
        """Builds a vector utility chain with one shared secondary-input node."""
        self.request.update(
            source_attribute="translate", target_attributes=["translate"],
            use_utility_node=True, utility_node_type="plusMinusAverage",
            use_shared_input=True, shared_input_node_type="condition",
        )
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])
        result = self.service.execute(self.request)
        self.assertEqual([], result["errors"])
        self.assertEqual(2, len(result["created_nodes"]))

    def test_existing_input_is_only_replaced_when_enabled(self):
        """Leaves the existing connection intact until replacement is explicit."""
        self.cmds.connectAttr(f"{self.source}.rotateX", f"{self.target}.translateX")
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(0, self.service.execute(self.request)["succeeded"])
        self.request["force_connection"] = True
        self.assertEqual("warning", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(1, self.service.execute(self.request)["succeeded"])
        self.assertTrue(self.cmds.isConnected(f"{self.source}.translateX", f"{self.target}.translateX"))

    def test_compound_disconnect_lists_and_removes_exact_child_connection(self):
        """Disconnects actual child inputs once despite overlapping attribute names."""
        self.cmds.connectAttr(f"{self.source}.translateX", f"{self.target}.translateX")
        self.request.update(operation="disconnect", target_attributes=["translate", "translateX"])
        rows = self.service.inspect(self.request)
        self.assertEqual(1, len(rows))
        self.assertEqual(f"{self.target}.translateX", rows[0]["target"])
        self.assertEqual(1, self.service.execute(self.request)["succeeded"])
        self.assertFalse(self.cmds.isConnected(f"{self.source}.translateX", f"{self.target}.translateX"))

    def test_known_dimension_mismatch_is_blocked(self):
        """Detects compound-to-scalar connections before invoking connectAttr."""
        self.request["source_attribute"] = "translate"
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(0, self.service.execute(self.request)["succeeded"])

    def test_array_disconnect_inspects_existing_elements(self):
        """Finds actual connected array elements without allocating new ones."""
        utility = self.cmds.createNode("plusMinusAverage")
        self.cmds.connectAttr(f"{self.source}.translateX", f"{utility}.input1D[3]")
        self.request.update(
            operation="disconnect", target_objects=[utility], target_attributes=["input1D"],
        )
        rows = self.service.inspect(self.request)
        self.assertEqual(1, len(rows))
        self.assertEqual(f"{utility}.input1D[3]", rows[0]["target"])
        self.assertEqual([3], self.cmds.getAttr(f"{utility}.input1D", multiIndices=True))
        self.assertEqual(1, self.service.execute(self.request)["succeeded"])

    def test_array_connection_requires_explicit_element(self):
        """Reports unindexed array fields before Run attempts to connect them."""
        utility = self.cmds.createNode("plusMinusAverage")
        self.request.update(target_objects=[utility], target_attributes=["input1D"])
        row = self.service.inspect(self.request)[0]
        self.assertEqual("blocked", row["status"])
        self.assertIn("explicit array element", row["details"])

    def test_preview_does_not_allocate_uncreated_array_elements(self):
        """Uses schema metadata because getAttr(type=True) allocates array elements."""
        source_array = self.cmds.createNode("plusMinusAverage")
        target_array = self.cmds.createNode("plusMinusAverage")
        self.cmds.addAttr(source_array, longName="values", attributeType="double", multi=True, readable=True)
        self.request.update(
            source_object=source_array, source_attribute="values[7]",
            target_objects=[target_array], target_attributes=["input1D[5]"],
        )
        source_indices = self.cmds.getAttr(f"{source_array}.values", multiIndices=True)
        target_indices = self.cmds.getAttr(f"{target_array}.input1D", multiIndices=True)
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(source_indices, self.cmds.getAttr(f"{source_array}.values", multiIndices=True))
        self.assertEqual(target_indices, self.cmds.getAttr(f"{target_array}.input1D", multiIndices=True))


if __name__ == "__main__":
    unittest.main()
