"""Tests for ccwhat.adapters — adapter interface, ClaudeAdapter, registry."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ccwhat.adapters.base import AdapterNotImplementedError, AgentAdapter
from ccwhat.adapters.claude import ClaudeAdapter, _normalize_event, _normalize_usage
from ccwhat.adapters.registry import (
    create_adapter,
    infer_agent_from_target,
    is_implemented,
    normalize_agent_name,
)


class TestNormalizeAgentName(unittest.TestCase):
    def test_claude(self) -> None:
        self.assertEqual(normalize_agent_name("claude"), "claude")
        self.assertEqual(normalize_agent_name("claude-code"), "claude")
        self.assertEqual(normalize_agent_name("Claude"), "claude")
        self.assertEqual(normalize_agent_name("CLAUDE-CODE"), "claude")

    def test_codex(self) -> None:
        self.assertEqual(normalize_agent_name("codex"), "codex")
        self.assertEqual(normalize_agent_name("Codex"), "codex")

    def test_opencode(self) -> None:
        self.assertEqual(normalize_agent_name("opencode"), "opencode")
        self.assertEqual(normalize_agent_name("open-code"), "opencode")
        self.assertEqual(normalize_agent_name("open_code"), "opencode")
        self.assertEqual(normalize_agent_name("OpenCode"), "opencode")
        self.assertEqual(normalize_agent_name("OPEN-CODE"), "opencode")

    def test_unknown(self) -> None:
        self.assertEqual(normalize_agent_name("unknown-tool"), "unknown-tool")


class TestIsImplemented(unittest.TestCase):
    def test_claude_implemented(self) -> None:
        self.assertTrue(is_implemented("claude"))

    def test_codex_not_implemented(self) -> None:
        self.assertFalse(is_implemented("codex"))

    def test_opencode_not_implemented(self) -> None:
        self.assertFalse(is_implemented("opencode"))

    def test_unknown_not_implemented(self) -> None:
        self.assertFalse(is_implemented("unknown"))


class TestCreateAdapter(unittest.TestCase):
    def test_create_claude_adapter(self) -> None:
        adapter = create_adapter("claude")
        self.assertIsInstance(adapter, ClaudeAdapter)
        self.assertEqual(adapter.name, "claude")

    def test_create_claude_code_adapter(self) -> None:
        adapter = create_adapter("claude-code")
        self.assertIsInstance(adapter, ClaudeAdapter)

    def test_create_codex_raises(self) -> None:
        with self.assertRaises(AdapterNotImplementedError) as ctx:
            create_adapter("codex")
        self.assertIn("codex", str(ctx.exception))

    def test_create_opencode_raises(self) -> None:
        with self.assertRaises(AdapterNotImplementedError) as ctx:
            create_adapter("opencode")
        self.assertIn("opencode", str(ctx.exception))

    def test_create_open_code_raises(self) -> None:
        with self.assertRaises(AdapterNotImplementedError) as ctx:
            create_adapter("open-code")
        self.assertIn("open-code", str(ctx.exception))

    def test_create_unknown_raises(self) -> None:
        with self.assertRaises(AdapterNotImplementedError) as ctx:
            create_adapter("unknown-tool")
        self.assertIn("unknown-tool", str(ctx.exception))

    def test_create_with_projects_dir(self) -> None:
        path = Path("/tmp/test-projects")
        adapter = create_adapter("claude", projects_dir=path)
        self.assertEqual(adapter.projects_dir, path)


class TestInferAgentFromTarget(unittest.TestCase):
    def test_infer_claude(self) -> None:
        self.assertEqual(infer_agent_from_target(("claude",)), "claude")
        self.assertEqual(infer_agent_from_target(("claude-code",)), "claude")

    def test_infer_codex(self) -> None:
        self.assertEqual(infer_agent_from_target(("codex",)), "codex")

    def test_infer_opencode(self) -> None:
        self.assertEqual(infer_agent_from_target(("opencode",)), "opencode")
        self.assertEqual(infer_agent_from_target(("open-code",)), "opencode")
        self.assertEqual(infer_agent_from_target(("open_code",)), "opencode")

    def test_infer_unknown_returns_as_is(self) -> None:
        self.assertEqual(infer_agent_from_target(("my-ai",)), "my-ai")

    def test_infer_empty_defaults_to_claude(self) -> None:
        self.assertEqual(infer_agent_from_target(()), "claude")


class TestClaudeAdapter(unittest.TestCase):
    def make_session_file(self, dir: Path, session_id: str, entries: list[dict]) -> Path:
        path = dir / f"{session_id}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return path

    def make_subagent_file(self, dir: Path, session_id: str, agent_id: str, entries: list[dict]) -> Path:
        sub_dir = dir / session_id / "subagents"
        sub_dir.mkdir(parents=True, exist_ok=True)
        path = sub_dir / f"agent-{agent_id}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        meta_path = sub_dir / f"agent-{agent_id}.meta.json"
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump({"name": f"Agent {agent_id}"}, f)
        return path

    def test_list_projects_empty_dir(self) -> None:
        with TemporaryDirectory() as tmp:
            adapter = ClaudeAdapter(Path(tmp))
            projects = adapter.list_projects()
            self.assertEqual(projects, [])

    def test_list_projects_with_sessions(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "my-project"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            self.make_session_file(proj_dir, session_id, [
                {"type": "user", "content": "hello", "timestamp": "2025-01-01T00:00:00"},
                {"type": "assistant", "content": "hi", "timestamp": "2025-01-01T00:00:01"},
            ])
            adapter = ClaudeAdapter(tmp_path)
            projects = adapter.list_projects()
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0]["projectDir"], "my-project")
            self.assertEqual(len(projects[0]["sessions"]), 1)
            self.assertEqual(projects[0]["sessions"][0]["id"], session_id)

    def test_list_projects_ignores_non_uuid_jsonl(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "my-project"
            proj_dir.mkdir()
            (proj_dir / "not-a-uuid.jsonl").write_text(
                json.dumps({"type": "user"}) + "\n"
            )
            adapter = ClaudeAdapter(tmp_path)
            projects = adapter.list_projects()
            self.assertEqual(len(projects), 0)

    def test_load_session_found(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "my-project"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            self.make_session_file(proj_dir, session_id, [
                {"type": "user", "content": "hello"},
                {"type": "assistant", "message": {"content": "hi"}},
            ])
            adapter = ClaudeAdapter(tmp_path)
            session = adapter.load_session(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(session["sessionId"], session_id)
            self.assertEqual(session["projectDir"], "my-project")
            self.assertEqual(len(session["main"]), 2)
            self.assertEqual(session["agent"], "claude")
            self.assertTrue("events" in session)

    def test_load_session_not_found(self) -> None:
        with TemporaryDirectory() as tmp:
            adapter = ClaudeAdapter(Path(tmp))
            session = adapter.load_session("nonexistent")
            self.assertIsNone(session)

    def test_load_session_with_subagents(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "my-project"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            self.make_session_file(proj_dir, session_id, [
                {"type": "user", "content": "hello"},
            ])
            self.make_subagent_file(proj_dir, session_id, "sub1", [
                {"type": "assistant", "content": "from subagent"},
            ])
            adapter = ClaudeAdapter(tmp_path)
            session = adapter.load_session(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(len(session["subagents"]), 1)
            self.assertEqual(session["subagents"][0]["agentId"], "sub1")
            self.assertEqual(session["subagents"][0]["meta"]["name"], "Agent sub1")
            self.assertEqual(len(session["subagents"][0]["entries"]), 1)

    def test_jsonl_parse_skip_bad_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "my-project"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            path = proj_dir / f"{session_id}.jsonl"
            with path.open("w", encoding="utf-8") as f:
                f.write('{"type": "user", "content": "good"}\n')
                f.write("not valid json\n")
                f.write('{"type": "assistant", "content": "also good"}\n')
            adapter = ClaudeAdapter(tmp_path)
            session = adapter.load_session(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(len(session["main"]), 2)


class TestNormalizedEvents(unittest.TestCase):
    def test_normalize_user_event(self) -> None:
        entry = {"type": "user", "content": "hello world", "timestamp": "2025-01-01T00:00:00"}
        event = _normalize_event(entry, "session-1")
        self.assertEqual(event["kind"], "user")
        self.assertEqual(event["role"], "user")
        self.assertEqual(event["content"], "hello world")
        self.assertEqual(event["sessionId"], "session-1")
        self.assertEqual(event["agent"], "claude")

    def test_normalize_assistant_event(self) -> None:
        entry = {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "hello back"}]},
            "timestamp": "2025-01-01T00:00:01",
        }
        event = _normalize_event(entry, "session-1")
        self.assertEqual(event["kind"], "assistant")
        self.assertEqual(event["role"], "assistant")
        self.assertEqual(event["content"], "hello back")

    def test_normalize_tool_call_event(self) -> None:
        entry = {"type": "tool_call", "tool_name": "bash", "parts": [{"command": "ls"}], "timestamp": "2025-01-01T00:00:02"}
        event = _normalize_event(entry, "session-1")
        self.assertEqual(event["kind"], "tool_call")
        self.assertEqual(event["toolName"], "bash")

    def test_normalize_tool_result_event(self) -> None:
        entry = {"type": "tool_result", "tool_name": "bash", "content": "file1.txt\nfile2.txt", "timestamp": "2025-01-01T00:00:03"}
        event = _normalize_event(entry, "session-1")
        self.assertEqual(event["kind"], "tool_result")
        self.assertEqual(event["toolName"], "bash")

    def test_normalize_reasoning_event(self) -> None:
        entry = {"type": "reasoning", "content": "thinking...", "timestamp": "2025-01-01T00:00:04"}
        event = _normalize_event(entry, "session-1")
        self.assertEqual(event["kind"], "reasoning")

    def test_normalize_error_event(self) -> None:
        entry = {"type": "error", "content": "something went wrong", "timestamp": "2025-01-01T00:00:05"}
        event = _normalize_event(entry, "session-1")
        self.assertEqual(event["kind"], "error")

    def test_events_sorted_in_session(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "proj"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            path = proj_dir / f"{session_id}.jsonl"
            with path.open("w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "user", "content": "first"}) + "\n")
                f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "second"}]}}) + "\n")
            adapter = ClaudeAdapter(tmp_path)
            session = adapter.load_session(session_id)
            events = session["events"]
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["kind"], "user")
            self.assertEqual(events[1]["kind"], "assistant")


class TestUsageMapping(unittest.TestCase):
    def test_usage_from_message_usage(self) -> None:
        entry = {
            "message": {
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_read_input_tokens": 10,
                    "cache_write_input_tokens": 5,
                    "reasoning_tokens": 20,
                }
            }
        }
        usage = _normalize_usage(entry)
        self.assertEqual(usage.get("inputTokens"), 100)
        self.assertEqual(usage.get("outputTokens"), 50)
        self.assertEqual(usage.get("reasoningTokens"), 20)
        self.assertEqual(usage.get("cacheReadTokens"), 10)
        self.assertEqual(usage.get("cacheWriteTokens"), 5)
        self.assertEqual(usage.get("totalTokens"), 150)
        self.assertEqual(usage.get("scope"), "event")
        self.assertEqual(usage.get("source"), "agent_log")

    def test_usage_camelcase_keys(self) -> None:
        entry = {
            "message": {
                "usage": {
                    "inputTokens": 200,
                    "outputTokens": 100,
                    "cacheReadInputTokens": 20,
                    "cacheWriteInputTokens": 10,
                }
            }
        }
        usage = _normalize_usage(entry)
        self.assertEqual(usage.get("inputTokens"), 200)

    def test_usage_missing_fields_empty(self) -> None:
        entry = {"type": "user", "content": "hello"}
        usage = _normalize_usage(entry)
        self.assertEqual(usage.get("inputTokens"), None)
        self.assertEqual(usage.get("outputTokens"), None)
        self.assertEqual(usage.get("totalTokens"), None)
        self.assertEqual(usage.get("cacheHitRate"), None)

    def test_usage_no_cache_hit_rate_default(self) -> None:
        entry = {
            "message": {
                "usage": {
                    "input_tokens": 50,
                    "output_tokens": 25,
                }
            }
        }
        usage = _normalize_usage(entry)
        self.assertNotIn("cacheHitRate", usage)


class TestClaudeAdapterListAndSession(unittest.TestCase):
    def test_list_projects_with_agent_field(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "test-project"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            path = proj_dir / f"{session_id}.jsonl"
            with path.open("w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "user", "content": "hi"}) + "\n")
            adapter = ClaudeAdapter(tmp_path)
            projects = adapter.list_projects()
            self.assertEqual(len(projects), 1)
            # Agent field should be present in the project dict
            # (the server adds it, but adapter shouldn't need to)
            self.assertNotIn("agent", projects[0])

    def test_load_session_has_events(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proj_dir = tmp_path / "p"
            proj_dir.mkdir()
            session_id = "550e8400-e29b-41d4-a716-446655440000"
            path = proj_dir / f"{session_id}.jsonl"
            with path.open("w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "user", "content": "hello"}) + "\n")
            adapter = ClaudeAdapter(tmp_path)
            session = adapter.load_session(session_id)
            self.assertTrue("events" in session)
            self.assertGreater(len(session["events"]), 0)
            self.assertEqual(session["events"][0]["kind"], "user")
