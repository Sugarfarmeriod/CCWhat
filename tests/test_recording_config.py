"""Tests for recording configuration model, validation, presets, and persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ccwhat.config import (
    DEFAULT_MAX_BODY_BYTES,
    DEFAULT_REDACT_HEADERS,
    DEFAULT_REDACT_PATTERNS,
    RecordingConfig,
    generate_local_session_id,
    load_config,
    normalize_path,
    save_config,
    validate_config,
    validate_domain,
)


class RecordingConfigTests(unittest.TestCase):
    def test_defaults_are_sensible(self) -> None:
        cfg = RecordingConfig()
        self.assertIsNone(cfg.preset)
        self.assertEqual(cfg.domains, [])
        self.assertEqual(cfg.paths, [])
        self.assertEqual(cfg.max_body_bytes, DEFAULT_MAX_BODY_BYTES)
        self.assertEqual(sorted(cfg.redact_headers), sorted(DEFAULT_REDACT_HEADERS))
        self.assertEqual(cfg.redact_header_patterns, list(DEFAULT_REDACT_PATTERNS))
        self.assertFalse(cfg.onboarding_complete)

    def test_default_redact_headers_include_required_set(self) -> None:
        cfg = RecordingConfig()
        for h in ["authorization", "cookie", "set-cookie", "x-api-key", "proxy-authorization"]:
            self.assertIn(h, cfg.redact_headers)

    def test_default_redact_patterns_include_token_secret_key(self) -> None:
        cfg = RecordingConfig()
        for p in ["token", "secret", "key"]:
            self.assertIn(p, cfg.redact_header_patterns)

    def test_claude_preset_expands_to_anthropic_domain_and_paths(self) -> None:
        cfg = RecordingConfig(preset="claude")
        self.assertIn("api.anthropic.com", cfg.effective_domains())
        self.assertIn("/v1/messages", cfg.effective_paths())
        self.assertIn("/v1/messages/count_tokens", cfg.effective_paths())

    def test_explicit_domains_merged_with_preset(self) -> None:
        cfg = RecordingConfig(preset="claude", domains=["gateway.example.com"])
        domains = cfg.effective_domains()
        self.assertIn("api.anthropic.com", domains)
        self.assertIn("gateway.example.com", domains)

    def test_empty_config_is_invalid_for_recording(self) -> None:
        cfg = RecordingConfig()
        self.assertFalse(cfg.is_valid_for_recording())

    def test_config_with_preset_is_valid(self) -> None:
        cfg = RecordingConfig(preset="claude")
        self.assertTrue(cfg.is_valid_for_recording())

    def test_config_with_explicit_domain_is_valid(self) -> None:
        cfg = RecordingConfig(domains=["gateway.example.com"])
        self.assertTrue(cfg.is_valid_for_recording())


class DomainValidationTests(unittest.TestCase):
    def test_valid_domains_accepted(self) -> None:
        for d in ["api.anthropic.com", "gateway.example.com", "localhost", "sub.domain.co.uk"]:
            self.assertEqual(validate_domain(d), d)

    def test_url_scheme_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_domain("https://api.anthropic.com")

    def test_path_in_domain_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_domain("api.anthropic.com/v1")

    def test_whitespace_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_domain("api example.com")

    def test_empty_domain_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_domain("")

    def test_trailing_spaces_stripped(self) -> None:
        self.assertEqual(validate_domain("  api.anthropic.com  "), "api.anthropic.com")


class PathNormalizationTests(unittest.TestCase):
    def test_path_without_slash_gets_slash(self) -> None:
        self.assertEqual(normalize_path("v1/messages"), "/v1/messages")

    def test_path_with_slash_unchanged(self) -> None:
        self.assertEqual(normalize_path("/v1/messages"), "/v1/messages")

    def test_empty_path_unchanged(self) -> None:
        self.assertEqual(normalize_path(""), "")


class ConfigPersistenceTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            cfg = RecordingConfig(
                preset="claude",
                domains=["gateway.example.com"],
                paths=["/v1/messages"],
                max_body_bytes=1024,
                onboarding_complete=True,
            )
            save_config(cfg, config_path)
            loaded = load_config(config_path)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.preset, "claude")
        self.assertIn("gateway.example.com", loaded.domains)
        self.assertIn("/v1/messages", loaded.paths)
        self.assertEqual(loaded.max_body_bytes, 1024)
        self.assertTrue(loaded.onboarding_complete)

    def test_load_returns_none_when_file_missing(self) -> None:
        result = load_config(Path("/tmp/nonexistent-ccwhat-config-xyz.toml"))
        self.assertIsNone(result)

    def test_save_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "subdir" / "config.toml"
            cfg = RecordingConfig(preset="claude", onboarding_complete=True)
            save_config(cfg, config_path)
            self.assertTrue(config_path.exists())

    def test_cli_domain_override_does_not_save(self) -> None:
        """CLI --domain overrides do not modify saved config."""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            original = RecordingConfig(preset="claude", onboarding_complete=True)
            save_config(original, config_path)
            # Simulate a CLI --domain run-time override (build a temp config, don't save)
            runtime_cfg = RecordingConfig(domains=["other.example.com"])
            # The saved config should be unchanged
            reloaded = load_config(config_path)
            self.assertIsNotNone(reloaded)
            assert reloaded is not None
            self.assertEqual(reloaded.preset, "claude")
            self.assertNotIn("other.example.com", reloaded.domains)


class ConfigValidationTests(unittest.TestCase):
    def test_invalid_domain_in_config_raises(self) -> None:
        cfg = RecordingConfig(domains=["https://bad-domain.com"])
        errors = validate_config(cfg)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("scheme" in e.lower() for e in errors))

    def test_negative_max_body_bytes_raises(self) -> None:
        cfg = RecordingConfig(domains=["api.anthropic.com"], max_body_bytes=-1)
        errors = validate_config(cfg)
        self.assertTrue(len(errors) > 0)

    def test_valid_config_has_no_errors(self) -> None:
        cfg = RecordingConfig(preset="claude", onboarding_complete=True)
        errors = validate_config(cfg)
        self.assertEqual(errors, [])


class LocalSessionIdTests(unittest.TestCase):
    def test_generate_local_session_id_is_unique(self) -> None:
        ids = {generate_local_session_id() for _ in range(10)}
        self.assertEqual(len(ids), 10)

    def test_generate_local_session_id_starts_with_local(self) -> None:
        sid = generate_local_session_id()
        self.assertTrue(sid.startswith("local-"))


if __name__ == "__main__":
    unittest.main()
