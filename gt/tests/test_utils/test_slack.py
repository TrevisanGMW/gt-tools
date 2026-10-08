"""Generic Slack messaging tests use fake HTTP responses and never send messages."""

import json
import os
import unittest
from unittest import mock

from gt.utils import slack


class TestSlack(unittest.TestCase):
    """Covers reusable notifications without application-specific message formatting."""

    def test_missing_credentials_skips_without_http(self):
        """Keeps credentials optional and never creates a network request."""
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(slack.request, "build_opener") as opener:
            result = slack.post_message("", "A tool finished")
        self.assertEqual("skipped", result["status"])
        opener.assert_not_called()

    def test_fake_success_posts_expected_json(self):
        """Supplies credentials through an authorization header only."""
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true, "channel": "C_SAMPLE", "ts": "123"}'
        opener = mock.Mock()
        opener.open.return_value = response
        with mock.patch.object(slack.request, "build_opener", return_value=opener):
            result = slack.post_message("C_SAMPLE", "Render complete", token="xoxb-fake", timeout=2)
        self.assertEqual("succeeded", result["status"])
        http_request = opener.open.call_args.args[0]
        self.assertEqual(slack.SLACK_MESSAGE_URL, http_request.full_url)
        self.assertEqual("Bearer xoxb-fake", http_request.get_header("Authorization"))
        self.assertEqual("C_SAMPLE", json.loads(http_request.data)["channel"])
        self.assertNotIn("xoxb", http_request.data.decode())
        self.assertEqual(2, opener.open.call_args.kwargs["timeout"])

    def test_network_failure_and_invalid_token_do_not_raise(self):
        """Never returns an exception containing the token or server response."""
        opener = mock.Mock()
        with mock.patch.object(slack.request, "build_opener", return_value=opener):
            opener.open.side_effect = OSError("xoxb-fake should not be exposed")
            result = slack.post_message("C_SAMPLE", "Render complete", token="xoxb-fake")
            self.assertEqual("failed", result["status"])
            self.assertNotIn("xoxb", str(result))
            opener.open.side_effect = None
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = b'{"ok": false, "error": "invalid_auth"}'
            opener.open.return_value = response
            self.assertEqual("failed", slack.post_message("C_SAMPLE", "Render complete", token="xoxb-fake")["status"])

    def test_redirects_are_rejected(self):
        """Does not forward credentials to a redirect destination."""
        self.assertIsNone(slack._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com"))
