import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils import cleanup_utils


class TestCleanUpUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_delete_unused_nodes(self):
        node = maya_test_tools.cmds.createNode("multiplyDivide")
        num_deleted_nodes = cleanup_utils.delete_unused_nodes(verbose=False)
        result = maya_test_tools.cmds.objExists(node)
        self.assertFalse(result, f'Expected to not find "{node}. But it was found."')
        expected_num_deleted_nodes = 1
        self.assertEqual(expected_num_deleted_nodes, num_deleted_nodes)

    def test_delete_nucleus_nodes(self):
        types_to_test = ['nParticle',
                         'spring',
                         'particle',
                         'nRigid',
                         'nCloth',
                         'pfxHair',
                         'hairSystem',
                         'dynamicConstraint',
                         'pointEmitter',
                         'nucleus',
                         'instancer']
        nodes = []
        for node_type in types_to_test:
            new_node = maya_test_tools.cmds.createNode(node_type)
            nodes.append(new_node)
            exists_result = maya_test_tools.cmds.objExists(new_node)
            self.assertTrue(exists_result, f'Missing expected node: "{str(new_node)}".')

        num_deleted_nodes = cleanup_utils.delete_nucleus_nodes(verbose=False, include_fields=False)
        expected_num_deleted_nodes = len(types_to_test)
        self.assertEqual(expected_num_deleted_nodes, num_deleted_nodes)

        for node in nodes:
            exists_result = maya_test_tools.cmds.objExists(node)
            self.assertFalse(exists_result, f'Found unexpected node: "{node}".')

    def test_delete_nucleus_nodes_include_fields(self):
        types_to_test = ['airField',
                         'dragField',
                         'newtonField',
                         'radialField',
                         'turbulenceField',
                         'uniformField',
                         'vortexField',
                         'volumeAxisField']
        nodes = []
        for node_type in types_to_test:
            new_node = maya_test_tools.cmds.createNode(node_type)
            nodes.append(new_node)
            exists_result = maya_test_tools.cmds.objExists(new_node)
            self.assertTrue(exists_result, f'Missing expected node: "{str(new_node)}".')

        num_deleted_nodes = cleanup_utils.delete_nucleus_nodes(verbose=False, include_fields=False)
        expected_num_deleted_nodes = 0
        self.assertEqual(expected_num_deleted_nodes, num_deleted_nodes)
        num_deleted_nodes = cleanup_utils.delete_nucleus_nodes(verbose=False, include_fields=True)
        expected_num_deleted_nodes = len(types_to_test)
        self.assertEqual(expected_num_deleted_nodes, num_deleted_nodes)

        for node in nodes:
            exists_result = maya_test_tools.cmds.objExists(node)
            self.assertFalse(exists_result, f'Found unexpected node: "{node}".')
