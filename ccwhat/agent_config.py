"""Auto-detect recording domains from coding agent config files.

Reads each agent's own config to find API provider base URLs,
so users don't need to run `ccwhat setup` before recording.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# JSONC comment stripping
# ---------------------------------------------------------------------------

def _strip_jsonc_comments(text: str) -> str:
    """Remove // line comments and /* */ block comments, skipping string literals."""
    result: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        c = text[i]
        if in_string:
            if c == "\\":
                result.append(c)
                if i + 1 < n:
                    result.append(text[i + 1])
                    i += 2
                else:
                    i += 1
                continue
            elif c == '"':
                in_string = False
            result.append(c)
            i += 1
        else:
            if c == '"':
                in_string = True
                result.append(c)
                i += 1
            elif c == "/" and i + 1 < n and text[i + 1] == "/":
                while i < n and text[i] != "\n":
                    i += 1
            elif c == "/" and i + 1 < n and text[i + 1] == "*":
                i += 2
                while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
            else:
                result.append(c)
                i += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# Host extraction helper
# ---------------------------------------------------------------------------

def _host_from_url(url: str) -> str | None:
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    try:
        parsed = urlparse(url)
        return parsed.hostname or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Per-agent detectors
# ---------------------------------------------------------------------------

def _detect_opencode_domains(home: Path | None = None) -> list[str]:
    config_path = (home or Path.home()) / ".config" / "opencode" / "opencode.jsonc"
    try:
        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(_strip_jsonc_comments(raw))
        providers = data.get("provider", {})
        hosts: list[str] = []
        for provider_cfg in providers.values():
            base_url = provider_cfg.get("options", {}).get("baseURL", "")
            host = _host_from_url(base_url)
            if host and host not in hosts:
                hosts.append(host)
        return hosts if hosts else ["api.anthropic.com"]
    except Exception:
        return ["api.anthropic.com"]


def _detect_claude_domains(home: Path | None = None) -> list[str]:
    config_path = (home or Path.home()) / ".claude" / "settings.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        base_url = data.get("env", {}).get("ANTHROPIC_BASE_URL", "")
        host = _host_from_url(base_url)
        return [host] if host else ["api.anthropic.com"]
    except Exception:
        return ["api.anthropic.com"]


def _detect_codex_domains(home: Path | None = None) -> list[str]:
    if tomllib is None:
        return ["api.openai.com"]
    config_path = (home or Path.home()) / ".codex" / "config.toml"
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        env_set = data.get("shell_environment_policy", {}).get("set", {})
        hosts: list[str] = []
        for key, value in env_set.items():
            if key.endswith("_BASE_URL") and isinstance(value, str):
                host = _host_from_url(value)
                if host and host not in hosts:
                    hosts.append(host)
        return hosts if hosts else ["api.openai.com"]
    except Exception:
        return ["api.openai.com"]


# ---------------------------------------------------------------------------
# Default paths per agent type
# ---------------------------------------------------------------------------

_AGENT_DEFAULT_PATHS: dict[str, list[str]] = {
    "opencode": ["/v1/messages", "/v1/chat/completions"],
    "claude": ["/v1/messages"],
    "codex": ["/v1/responses"],
}

_AGENT_DETECTORS = {
    "opencode": _detect_opencode_domains,
    "claude": _detect_claude_domains,
    "codex": _detect_codex_domains,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_domains(agent_name: str, _home: Path | None = None) -> list[str]:
    """Return deduplicated recording domains inferred from agent config.

    Returns [] for unknown agents. Never raises.
    _home is an optional override for the user home directory (used in tests).
    """
    detector = _AGENT_DETECTORS.get(agent_name.lower())
    if detector is None:
        return []
    try:
        hosts = detector(_home)
    except Exception:
        return []
    seen: list[str] = []
    for h in hosts:
        if h not in seen:
            seen.append(h)
    return seen


def detect_default_paths(agent_name: str) -> list[str]:
    """Return default path filters for a known agent, empty list otherwise."""
    return list(_AGENT_DEFAULT_PATHS.get(agent_name.lower(), []))
