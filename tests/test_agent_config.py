"""Tests for ccwhat.agent_config — auto-detection of recording domains."""

from __future__ import annotations

import json
from pathlib import Path

from ccwhat.agent_config import (
    _strip_jsonc_comments,
    detect_default_paths,
    detect_domains,
)


# ---------------------------------------------------------------------------
# JSONC comment stripping (task 3.3)
# ---------------------------------------------------------------------------

class TestStripJsoncComments:
    def test_line_comment_removed(self):
        src = '{"a": 1} // this is a comment\n'
        result = _strip_jsonc_comments(src)
        assert "//" not in result
        assert json.loads(result) == {"a": 1}

    def test_block_comment_removed(self):
        src = '{"a": /* ignore this */ 1}'
        result = _strip_jsonc_comments(src)
        assert "/*" not in result
        assert json.loads(result) == {"a": 1}

    def test_mixed_comments(self):
        src = '// header\n{"a": /* block */ 1} // tail\n'
        result = _strip_jsonc_comments(src)
        assert json.loads(result.strip()) == {"a": 1}

    def test_no_comments_unchanged(self):
        src = '{"x": "y"}'
        assert _strip_jsonc_comments(src) == src


# ---------------------------------------------------------------------------
# opencode domain detection (task 3.1)
# ---------------------------------------------------------------------------

class TestDetectOpencodeDomains:
    def _write_opencode_config(self, home: Path, providers: dict) -> Path:
        config_dir = home / ".config" / "opencode"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "opencode.jsonc"
        config_file.write_text(json.dumps({"provider": providers}), encoding="utf-8")
        return config_file

    def test_single_provider(self, tmp_path):
        self._write_opencode_config(tmp_path, {
            "friday": {"options": {"baseURL": "https://aigc.sankuai.com/v1/openai/native"}}
        })
        result = detect_domains("opencode", _home=tmp_path)
        assert result == ["aigc.sankuai.com"]

    def test_multiple_providers(self, tmp_path):
        self._write_opencode_config(tmp_path, {
            "p1": {"options": {"baseURL": "https://a.example.com/v1"}},
            "p2": {"options": {"baseURL": "https://b.example.com/api"}},
        })
        result = detect_domains("opencode", _home=tmp_path)
        assert "a.example.com" in result
        assert "b.example.com" in result
        assert len(result) == 2

    def test_duplicate_providers_deduped(self, tmp_path):
        self._write_opencode_config(tmp_path, {
            "p1": {"options": {"baseURL": "https://same.example.com/v1"}},
            "p2": {"options": {"baseURL": "https://same.example.com/v2"}},
        })
        result = detect_domains("opencode", _home=tmp_path)
        assert result == ["same.example.com"]

    def test_missing_config_returns_default(self, tmp_path):
        result = detect_domains("opencode", _home=tmp_path)
        assert result == ["api.anthropic.com"]

    def test_invalid_config_returns_default(self, tmp_path):
        config_dir = tmp_path / ".config" / "opencode"
        config_dir.mkdir(parents=True)
        (config_dir / "opencode.jsonc").write_text("not valid json {{{{", encoding="utf-8")
        result = detect_domains("opencode", _home=tmp_path)
        assert result == ["api.anthropic.com"]

    def test_jsonc_with_comments_parsed(self, tmp_path):
        config_dir = tmp_path / ".config" / "opencode"
        config_dir.mkdir(parents=True)
        content = (
            '// top comment\n'
            '{"provider": {"p": {"options": {"baseURL": "https://gw.example.com"}}}}'
        )
        (config_dir / "opencode.jsonc").write_text(content, encoding="utf-8")
        result = detect_domains("opencode", _home=tmp_path)
        assert result == ["gw.example.com"]


# ---------------------------------------------------------------------------
# claude domain detection (task 3.2)
# ---------------------------------------------------------------------------

class TestDetectClaudeDomains:
    def _write_claude_settings(self, home: Path, env: dict) -> None:
        config_dir = home / ".claude"
        config_dir.mkdir(parents=True)
        (config_dir / "settings.json").write_text(
            json.dumps({"env": env}), encoding="utf-8"
        )

    def test_custom_base_url(self, tmp_path):
        self._write_claude_settings(tmp_path, {"ANTHROPIC_BASE_URL": "https://mcli.sankuai.com"})
        assert detect_domains("claude", _home=tmp_path) == ["mcli.sankuai.com"]

    def test_no_base_url_returns_default(self, tmp_path):
        self._write_claude_settings(tmp_path, {"ANTHROPIC_MODEL": "opus"})
        assert detect_domains("claude", _home=tmp_path) == ["api.anthropic.com"]

    def test_missing_config_returns_default(self, tmp_path):
        assert detect_domains("claude", _home=tmp_path) == ["api.anthropic.com"]


# ---------------------------------------------------------------------------
# codex domain detection (task 3.2)
# ---------------------------------------------------------------------------

class TestDetectCodexDomains:
    def _write_codex_config(self, home: Path, content: str) -> None:
        config_dir = home / ".codex"
        config_dir.mkdir(parents=True)
        (config_dir / "config.toml").write_text(content, encoding="utf-8")

    def test_custom_base_url(self, tmp_path):
        toml = '[shell_environment_policy.set]\nOPENAI_BASE_URL = "https://gw.example.com"\n'
        self._write_codex_config(tmp_path, toml)
        assert detect_domains("codex", _home=tmp_path) == ["gw.example.com"]

    def test_no_base_url_returns_default(self, tmp_path):
        toml = '[shell_environment_policy.set]\nANTHROPIC_MODEL = "opus"\n'
        self._write_codex_config(tmp_path, toml)
        assert detect_domains("codex", _home=tmp_path) == ["api.openai.com"]

    def test_missing_config_returns_default(self, tmp_path):
        assert detect_domains("codex", _home=tmp_path) == ["api.openai.com"]


# ---------------------------------------------------------------------------
# Unknown agent (task 3.4)
# ---------------------------------------------------------------------------

class TestUnknownAgent:
    def test_returns_empty_list(self):
        assert detect_domains("unknown-agent") == []

    def test_empty_string_returns_empty(self):
        assert detect_domains("") == []


# ---------------------------------------------------------------------------
# detect_default_paths
# ---------------------------------------------------------------------------

class TestDetectDefaultPaths:
    def test_opencode_paths(self):
        paths = detect_default_paths("opencode")
        assert "/v1/messages" in paths

    def test_claude_paths(self):
        assert detect_default_paths("claude") == ["/v1/messages"]

    def test_codex_paths(self):
        assert detect_default_paths("codex") == ["/v1/responses"]

    def test_unknown_agent_empty(self):
        assert detect_default_paths("unknown") == []
