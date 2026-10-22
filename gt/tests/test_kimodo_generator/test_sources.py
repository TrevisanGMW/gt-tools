"""Source resolution and real local Git checkout safety without network access."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gt.tools.kimodo_generator import kimodo_generator_sources as sources


class TestKimodoSourceResolution(unittest.TestCase):
    """Validates latest resolution and concrete stable fallback identities."""

    def test_latest_revisions_resolve_both_default_branches(self):
        """Records hashes rather than moving branch names or tags."""
        with patch.object(sources, "run_git", side_effect=[f"{'a' * 40}\tHEAD", f"{'b' * 40}\tHEAD"]) as git:
            self.assertEqual({"kimodo_revision": "a" * 40, "viser_revision": "b" * 40}, sources.latest_revisions())
        self.assertEqual(2, git.call_count)
        self.assertEqual(["ls-remote", sources.KIMODO_REPOSITORY, "HEAD"], git.call_args_list[0].args[0])

    def test_invalid_or_empty_latest_commit_is_rejected(self):
        """Never accepts error text as a revision or quietly substitutes a moving branch."""
        for output in ("", "main HEAD", "error: unavailable"):
            with patch.object(sources, "run_git", return_value=output):
                with self.assertRaises(ValueError):
                    sources.latest_revisions()


@unittest.skipUnless(shutil.which("git"), "Requires a local Git executable.")
class TestKimodoSourceCheckout(unittest.TestCase):
    """Exercises clean upgrades and preservation of user changes in disposable repos."""

    def setUp(self):
        """Creates two local commits with no global Git configuration changes."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.origin = self.root / "origin"
        self.checkout = self.root / "generated"
        sources.run_git(["init", str(self.origin)])
        self.tracked = "source.txt"
        (self.origin / self.tracked).write_text("first\n", encoding="utf-8")
        self.first = self.commit("first")
        (self.origin / self.tracked).write_text("second\n", encoding="utf-8")
        (self.origin / "new.txt").write_text("upstream\n", encoding="utf-8")
        self.second = self.commit("second")
        sources.checkout_source(self.checkout, str(self.origin), self.first)

    def commit(self, message):
        """Commits only this fixture repository with command-local author identity.

        Args:
            message (str): Fixture commit message.

        Returns:
            str: Full commit hash.
        """
        sources.run_git(["-C", str(self.origin), "add", "."])
        sources.run_git(["-C", str(self.origin), "-c", "user.name=GT Tools Test", "-c",
                         "user.email=tests@localhost", "commit", "-m", message])
        return sources.run_git(["-C", str(self.origin), "rev-parse", "HEAD"])

    def test_clean_recorded_source_updates_and_can_return_to_stable(self):
        """Upgrades and fallback checkouts preserve their recorded commit contract."""
        sources.checkout_source(self.checkout, str(self.origin), self.second, self.first)
        self.assertEqual("second\n", (self.checkout / self.tracked).read_text())
        sources.checkout_source(self.checkout, str(self.origin), self.first, self.second)
        self.assertEqual("first\n", (self.checkout / self.tracked).read_text())

    def test_tracked_edits_and_unrecorded_commits_are_left_unchanged(self):
        """Never resets a user's modified or manually checked out source tree."""
        path = self.checkout / self.tracked
        path.write_text("user work\n", encoding="utf-8")
        with self.assertRaises(sources.SourceCheckoutError):
            sources.checkout_source(self.checkout, str(self.origin), self.second, self.first)
        self.assertEqual("user work\n", path.read_text())
        path.write_text("first\n", encoding="utf-8")
        with self.assertRaises(sources.SourceCheckoutError):
            sources.checkout_source(self.checkout, str(self.origin), self.second, "c" * 40)
        self.assertEqual(self.first, sources.run_git(["-C", str(self.checkout), "rev-parse", "HEAD"]))

    def test_untracked_file_conflicts_are_not_overwritten(self):
        """Lets non-force Git checkout refuse conflicting untracked user files."""
        path = self.checkout / "new.txt"
        path.write_text("user work\n", encoding="utf-8")
        with self.assertRaises(sources.subprocess.CalledProcessError):
            sources.checkout_source(self.checkout, str(self.origin), self.second, self.first)
        self.assertEqual("user work\n", path.read_text())
