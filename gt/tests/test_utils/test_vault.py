import os
import sys
import tempfile
import unittest
from pathlib import Path

test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for path in (package_root_dir, os.path.dirname(package_root_dir)):
    if path not in sys.path:
        sys.path.append(path)

from gt.utils import vault


@unittest.skipUnless(vault.is_supported(), "Current-user encryption requires Windows.")
class TestVault(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_round_trip_does_not_store_plain_text(self):
        secret = "sk-test-0123456789"
        vault.store_secret("vlm_openai", secret, self.directory)
        file_text = (self.directory / "vlm_openai.secret").read_text(encoding="utf-8")
        self.assertNotIn(secret, file_text)
        expected = secret
        result = vault.load_secret("vlm_openai", self.directory)
        self.assertEqual(expected, result)

    def test_wrong_entropy_cannot_decrypt(self):
        vault.store_secret("key", "value", self.directory, entropy=b"one")
        with self.assertRaises(vault.VaultError):
            vault.load_secret("key", self.directory, entropy=b"two")

    def test_missing_secret_is_empty_and_delete_reports_state(self):
        self.assertEqual("", vault.load_secret("absent", self.directory))
        self.assertFalse(vault.has_secret("absent", self.directory))
        vault.store_secret("present", "value", self.directory)
        self.assertTrue(vault.has_secret("present", self.directory))
        self.assertTrue(vault.delete_secret("present", self.directory))
        self.assertFalse(vault.delete_secret("present", self.directory))

    def test_invalid_name_and_empty_value_are_rejected(self):
        with self.assertRaises(vault.VaultError):
            vault.store_secret("../escape", "value", self.directory)
        with self.assertRaises(vault.VaultError):
            vault.store_secret("key", "", self.directory)


if __name__ == "__main__":
    unittest.main()
