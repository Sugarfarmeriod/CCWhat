"""Tests for discovery mode — metadata-only, scoring, no payload storage."""

from __future__ import annotations

import unittest

from ccwhat.commands.discover import _score_candidate, _score_and_deduplicate


class DiscoveryScoringTests(unittest.TestCase):
    def test_anthropic_messages_path_scores_high(self) -> None:
        score, reason = _score_candidate("api.anthropic.com", "POST", "/v1/messages", 200, "application/json", False)
        self.assertGreater(score, 5)
        self.assertIn("Anthropic", reason)

    def test_sse_response_scores_high(self) -> None:
        score, reason = _score_candidate("gateway.example.com", "POST", "/v1/chat", 200, "text/event-stream", True)
        self.assertGreater(score, 5)
        self.assertIn("streaming", reason.lower())

    def test_non_model_host_scores_zero(self) -> None:
        score, reason = _score_candidate("github.com", "GET", "/repos/owner/repo", 200, "application/json", False)
        self.assertEqual(score, 0)

    def test_deduplicate_returns_highest_score_per_host_path(self) -> None:
        records = [
            {"host": "api.anthropic.com", "method": "POST", "path": "/v1/messages",
             "status": 200, "resp_content_type": "text/event-stream", "is_sse": True},
            {"host": "api.anthropic.com", "method": "POST", "path": "/v1/messages",
             "status": 200, "resp_content_type": "application/json", "is_sse": False},
        ]
        candidates, all_hosts = _score_and_deduplicate(records)
        # Should deduplicate to one entry for (api.anthropic.com, /v1/messages)
        self.assertEqual(len(candidates), 1)
        self.assertIn("api.anthropic.com", all_hosts)

    def test_no_sensitive_fields_in_metadata_records(self) -> None:
        """Discovery records must not contain body or auth values."""
        # The discovery addon code should not store body or auth
        from ccwhat.commands.discover import _DISCOVERY_ADDON_CODE
        self.assertNotIn("req_body", _DISCOVERY_ADDON_CODE)
        self.assertNotIn("resp_body", _DISCOVERY_ADDON_CODE)
        # Auth header values must not be stored
        self.assertNotIn("authorization_value", _DISCOVERY_ADDON_CODE)

    def test_non_model_hosts_not_preselected(self) -> None:
        records = [
            {"host": "telemetry.example.com", "method": "GET", "path": "/t",
             "status": 200, "resp_content_type": "application/json", "is_sse": False},
            {"host": "api.anthropic.com", "method": "POST", "path": "/v1/messages",
             "status": 200, "resp_content_type": "text/event-stream", "is_sse": True},
        ]
        candidates, all_hosts = _score_and_deduplicate(records)
        candidate_hosts = [c["host"] for c in candidates]
        self.assertIn("api.anthropic.com", candidate_hosts)
        self.assertNotIn("telemetry.example.com", candidate_hosts)
        # But it should appear in observed hosts
        self.assertIn("telemetry.example.com", all_hosts)


if __name__ == "__main__":
    unittest.main()
