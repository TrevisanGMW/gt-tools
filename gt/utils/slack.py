"""Optional Slack notifications using only the Python standard library.

Credentials come from the caller or environment. Message
formatting and application-specific notification policies belong to callers.
"""

import json
import os
from urllib import error, request


SLACK_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


class _NoRedirect(request.HTTPRedirectHandler):
    """Prevents forwarding the bot credential to a redirected endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Rejects HTTP redirects.

        Args:
            req (Request): Original request.
            fp (object): HTTP response stream.
            code (int): Response status.
            msg (str): Response reason.
            headers (object): Response headers.
            newurl (str): Redirect destination.

        Returns:
            None: Redirects are disabled.
        """
        return None


def post_message(channel_id, text, token=None, blocks=None, attachments=None, timeout=10):
    """Posts a message without raising network or credential errors.

    Args:
        channel_id (str): Target Slack channel ID.
        text (str): Accessible fallback text.
        token (str, optional): Bot OAuth token; defaults to SLACK_BOT_TOKEN.
        blocks (list, optional): Slack Block Kit content.
        attachments (list, optional): Slack attachments.
        timeout (float, optional): Network timeout in seconds.

    Returns:
        dict: status is succeeded, skipped, or failed. No token is returned.
    """
    token = token or os.environ.get("SLACK_BOT_TOKEN", "")
    if not token or not channel_id:
        return {"status": "skipped", "reason": "Slack token or channel ID is not configured."}
    try:
        payload = {"channel": channel_id, "text": text, "unfurl_links": False, "unfurl_media": False}
        if blocks:
            payload["blocks"] = blocks
        if attachments:
            payload["attachments"] = attachments
        http_request = request.Request(
            SLACK_MESSAGE_URL, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
        )
        opener = request.build_opener(_NoRedirect())
        with opener.open(http_request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict) or result.get("ok") is not True:
            return {"status": "failed", "reason": "Slack rejected the notification; check access and token."}
        return {"status": "succeeded", "channel": result.get("channel"), "timestamp": result.get("ts")}
    except error.HTTPError as exception:
        try:
            exception.close()
        except Exception:
            pass
        return {"status": "failed", "reason": "Slack returned an HTTP error."}
    except Exception:
        # Exceptions and response bodies may contain credentials; never log them.
        return {"status": "failed", "reason": "Slack notification could not be sent."}
