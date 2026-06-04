"""Tests for ccwhat setup (first-run onboarding) command."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from ccwhat.commands.setup import setup
from ccwhat.config import load_config


class SetupNonInteractiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_setup_preset_claude_yes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            result = self.runner.invoke(setup, ["--preset", "claude", "--yes", "--config", str(config_path)])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("saved", result.output.lower())
            cfg = load_config(config_path)
            self.assertIsNotNone(cfg)
            assert cfg is not None
            self.assertEqual(cfg.preset, "claude")
            self.assertTrue(cfg.onboarding_complete)
            self.assertIn("api.anthropic.com", cfg.effective_domains())

    def test_setup_preset_codex_yes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            result = self.runner.invoke(setup, ["--preset", "codex", "--yes", "--config", str(config_path)])
            self.assertEqual(result.exit_code, 0, result.output)
            cfg = load_config(config_path)
            self.assertIsNotNone(cfg)
            assert cfg is not None
            self.assertEqual(cfg.preset, "codex")
            self.assertTrue(cfg.onboarding_complete)
            self.assertIn("api.openai.com", cfg.effective_domains())
            self.assertIn("/v1/responses", cfg.effective_paths())

    def test_setup_domain_and_path_yes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            result = self.runner.invoke(setup, [
                "--domain", "gateway.example.com",
                "--path", "/v1/messages",
                "--yes",
                "--config", str(config_path),
            ])
            self.assertEqual(result.exit_code, 0, result.output)
            cfg = load_config(config_path)
            self.assertIsNotNone(cfg)
            assert cfg is not None
            self.assertIn("gateway.example.com", cfg.effective_domains())
            self.assertIn("/v1/messages", cfg.effective_paths())

    def test_setup_yes_without_preset_or_domain_fails(self) -> None:
        result = self.runner.invoke(setup, ["--yes"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--preset", result.output)

    def test_setup_unknown_preset_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            result = self.runner.invoke(setup, ["--preset", "nonexistent", "--yes", "--config", str(config_path)])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("unknown preset", result.output.lower())

    def test_setup_invalid_domain_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            result = self.runner.invoke(setup, [
                "--domain", "https://bad-domain.com",
                "--yes",
                "--config", str(config_path),
            ])
            self.assertNotEqual(result.exit_code, 0)
            # No partial config written
            self.assertFalse(config_path.exists())


class SetupInteractiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_interactive_official_claude_saves_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            # Choose option 1 (official Claude), confirm save
            result = self.runner.invoke(
                setup,
                ["--config", str(config_path)],
                input="1\ny\n",
                catch_exceptions=False,
            )
            self.assertEqual(result.exit_code, 0, result.output)
            cfg = load_config(config_path)
            self.assertIsNotNone(cfg)
            assert cfg is not None
            self.assertEqual(cfg.preset, "claude")

    def test_interactive_official_codex_saves_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            result = self.runner.invoke(
                setup,
                ["--config", str(config_path)],
                input="2\ny\n",
                catch_exceptions=False,
            )
            self.assertEqual(result.exit_code, 0, result.output)
            cfg = load_config(config_path)
            self.assertIsNotNone(cfg)
            assert cfg is not None
            self.assertEqual(cfg.preset, "codex")
            self.assertIn("api.openai.com", cfg.effective_domains())

    def test_interactive_keep_existing_no_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            # Pre-create config
            from ccwhat.config import RecordingConfig, save_config
            save_config(RecordingConfig(preset="claude", onboarding_complete=True), config_path)

            # User chooses not to reconfigure
            result = self.runner.invoke(
                setup,
                ["--config", str(config_path)],
                input="n\n",
                catch_exceptions=False,
            )
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("no changes", result.output.lower())


if __name__ == "__main__":
    unittest.main()
