"""Tests for ccwhat.task_segments.evidence (tasks 4.1-4.4)."""

from __future__ import annotations

import json
import os
import unittest

from ccwhat.task_segments.models import NormalizedEvent
from ccwhat.task_segments.evidence import (
    extract_evidence,
    normalize_path,
    detect_final_claim,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RULES_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ccwhat",
    "assets",
    "task_segment_rules.json",
)

with open(RULES_PATH, encoding="utf-8") as _f:
    RULES = json.load(_f)


def _event(
    event_type: str = "tool_call",
    tool_name: str | None = None,
    files: list[str] | None = None,
    command: str | None = None,
    text: str = "",
    source: str = "main",
    agent_id: str = "main",
    turn_index: int = 0,
    raw_ref: dict | None = None,
    metadata: dict | None = None,
) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=f"{agent_id}:{turn_index}",
        source=source,
        agent_id=agent_id,
        turn_index=turn_index,
        event_type=event_type,
        text=text,
        tool_name=tool_name,
        files=files or [],
        command=command,
        raw_ref=raw_ref or {},
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Task 4.2 – normalize_path
# ---------------------------------------------------------------------------

class TestNormalizePath(unittest.TestCase):

    def test_absolute_inside_repo(self):
        repo = "/home/user/project"
        path = "/home/user/project/src/foo.py"
        self.assertEqual(normalize_path(path, repo), "src/foo.py")

    def test_absolute_outside_repo(self):
        repo = "/home/user/project"
        path = "/home/other/file.py"
        result = normalize_path(path, repo)
        # Should start with "../" internally, so original is preserved
        self.assertEqual(result, path)

    def test_relative_path_unchanged(self):
        result = normalize_path("src/foo.py", "/home/user/project")
        self.assertEqual(result, "src/foo.py")

    def test_no_repo_root(self):
        path = "/absolute/path/file.py"
        self.assertEqual(normalize_path(path, None), path)

    def test_repo_root_exact_match(self):
        repo = "/project"
        path = "/project/a/b/c.py"
        self.assertEqual(normalize_path(path, repo), "a/b/c.py")


# ---------------------------------------------------------------------------
# Task 4.3 – detect_final_claim
# ---------------------------------------------------------------------------

class TestDetectFinalClaim(unittest.TestCase):

    def _make_assistant(self, text: str) -> NormalizedEvent:
        return _event(event_type="assistant_text", text=text)

    def test_long_zh_claim(self):
        text = "已完成所有功能的实现，现在可以运行测试来验证结果，代码已经通过了所有检查。"
        ev = self._make_assistant(text)
        result = detect_final_claim(ev, RULES)
        self.assertIsNotNone(result)
        self.assertIn("已完成", result)

    def test_long_en_claim(self):
        text = "All tests pass and the implementation is now complete. You can run the suite."
        ev = self._make_assistant(text)
        result = detect_final_claim(ev, RULES)
        self.assertIsNotNone(result)

    def test_short_text_rejected(self):
        ev = self._make_assistant("好了")
        result = detect_final_claim(ev, RULES)
        self.assertIsNone(result)

    def test_non_assistant_event_rejected(self):
        ev = _event(event_type="tool_result", text="All tests pass, implementation done!")
        result = detect_final_claim(ev, RULES)
        self.assertIsNone(result)

    def test_no_marker_returns_none(self):
        text = "这是一段没有结束标记的普通文字，内容很长，但不包含任何完成相关的词语。"
        ev = self._make_assistant(text)
        result = detect_final_claim(ev, RULES)
        self.assertIsNone(result)

    def test_summary_truncated_to_200(self):
        text = "done " + "x" * 300
        ev = self._make_assistant(text)
        result = detect_final_claim(ev, RULES)
        self.assertIsNotNone(result)
        self.assertLessEqual(len(result), 200)

    def test_no_rules_returns_none(self):
        text = "done and all tests pass, implementation complete!"
        ev = self._make_assistant(text)
        result = detect_final_claim(ev, rules=None)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Task 4.1 – extract_evidence
# ---------------------------------------------------------------------------

class TestExtractEvidence(unittest.TestCase):

    def test_read_tool_populates_files_read(self):
        ev = _event(tool_name="Read", files=["/repo/src/foo.py"])
        bundle = extract_evidence([ev], repo_root="/repo")
        self.assertIn("src/foo.py", bundle.files_read)
        self.assertEqual(bundle.files_changed, [])

    def test_edit_tool_populates_files_changed(self):
        ev = _event(tool_name="Edit", files=["/repo/src/bar.py"])
        bundle = extract_evidence([ev], repo_root="/repo")
        self.assertIn("src/bar.py", bundle.files_changed)
        self.assertEqual(bundle.files_read, [])

    def test_write_tool_populates_files_changed(self):
        ev = _event(tool_name="Write", files=["/repo/src/new.py"])
        bundle = extract_evidence([ev], repo_root="/repo")
        self.assertIn("src/new.py", bundle.files_changed)

    def test_bash_tool_populates_commands(self):
        ev = _event(tool_name="Bash", command="ls -la")
        bundle = extract_evidence([ev])
        self.assertIn("ls -la", bundle.commands)

    def test_command_event_populates_commands(self):
        ev = _event(event_type="command", command="git status")
        bundle = extract_evidence([ev])
        self.assertIn("git status", bundle.commands)

    def test_pytest_command_is_test_command(self):
        ev = _event(tool_name="Bash", command="uv run pytest tests/ -v")
        bundle = extract_evidence([ev])
        self.assertIn("uv run pytest tests/ -v", bundle.test_commands)

    def test_npm_test_command_is_test_command(self):
        ev = _event(tool_name="Bash", command="npm test")
        bundle = extract_evidence([ev])
        self.assertIn("npm test", bundle.test_commands)

    def test_npm_run_build_is_test_command(self):
        ev = _event(tool_name="Bash", command="npm run build")
        bundle = extract_evidence([ev])
        self.assertIn("npm run build", bundle.test_commands)

    def test_non_test_command_not_in_test_commands(self):
        ev = _event(tool_name="Bash", command="git diff HEAD")
        bundle = extract_evidence([ev])
        self.assertEqual(bundle.test_commands, [])

    def test_error_event_populates_errors(self):
        ev = _event(event_type="error", text="Something went wrong")
        bundle = extract_evidence([ev])
        self.assertIn("Something went wrong", bundle.errors)

    def test_traceback_in_raw_ref_populates_errors(self):
        raw = {"result": "Traceback (most recent call last):\n  File 'x.py'\nValueError"}
        ev = _event(event_type="tool_result", raw_ref=raw)
        bundle = extract_evidence([ev])
        self.assertTrue(len(bundle.errors) > 0)
        self.assertIn("Traceback", bundle.errors[0])

    def test_traceback_in_text_populates_errors(self):
        ev = _event(
            event_type="tool_result",
            text="Traceback (most recent call last):\n  File 'x.py'\nValueError: bad",
        )
        bundle = extract_evidence([ev])
        self.assertTrue(len(bundle.errors) > 0)

    def test_skill_tool_populates_skills(self):
        ev = _event(
            tool_name="Skill",
            metadata={"skill": "test-driven-development"},
        )
        bundle = extract_evidence([ev])
        self.assertIn("test-driven-development", bundle.skills)

    def test_skill_tool_name_fallback(self):
        ev = _event(
            tool_name="Skill",
            text="brainstorming",
            metadata={},
        )
        bundle = extract_evidence([ev])
        self.assertIn("brainstorming", bundle.skills)

    def test_subagent_user_message_populates_subagent_ids(self):
        ev = _event(
            event_type="user_message",
            source="subagent",
            agent_id="agent-abc",
        )
        bundle = extract_evidence([ev])
        self.assertIn("agent-abc", bundle.subagent_ids)

    def test_main_user_message_not_in_subagent_ids(self):
        ev = _event(event_type="user_message", source="main", agent_id="main")
        bundle = extract_evidence([ev])
        self.assertEqual(bundle.subagent_ids, [])

    def test_final_claim_event_type(self):
        ev = _event(event_type="final_claim", text="Implementation complete.")
        bundle = extract_evidence([ev])
        self.assertIn("Implementation complete.", bundle.final_claims)

    def test_final_claim_via_rules(self):
        text = "All tests pass and the feature is now implemented and ready."
        ev = _event(event_type="assistant_text", text=text)
        bundle = extract_evidence([ev], rules=RULES)
        self.assertTrue(len(bundle.final_claims) > 0)

    def test_deduplication_files_read(self):
        ev1 = _event(tool_name="Read", files=["/repo/a.py"])
        ev2 = _event(tool_name="Read", files=["/repo/a.py"])
        bundle = extract_evidence([ev1, ev2], repo_root="/repo")
        self.assertEqual(bundle.files_read.count("a.py"), 1)

    def test_mixed_events(self):
        events = [
            _event(tool_name="Read", files=["/repo/src/main.py"]),
            _event(tool_name="Edit", files=["/repo/src/main.py"]),
            _event(tool_name="Bash", command="pytest tests/"),
            _event(tool_name="Skill", metadata={"skill": "brainstorming"}),
            _event(event_type="error", text="SyntaxError: unexpected indent"),
        ]
        bundle = extract_evidence(events, repo_root="/repo")
        self.assertIn("src/main.py", bundle.files_read)
        self.assertIn("src/main.py", bundle.files_changed)
        self.assertIn("pytest tests/", bundle.commands)
        self.assertIn("pytest tests/", bundle.test_commands)
        self.assertIn("brainstorming", bundle.skills)
        self.assertIn("SyntaxError: unexpected indent", bundle.errors)

    def test_grep_and_glob_tools(self):
        ev_grep = _event(tool_name="Grep", files=["/repo/src/util.py"])
        ev_glob = _event(tool_name="Glob", files=["/repo/tests/test_x.py"])
        bundle = extract_evidence([ev_grep, ev_glob], repo_root="/repo")
        self.assertIn("src/util.py", bundle.files_read)
        self.assertIn("tests/test_x.py", bundle.files_read)

    def test_file_event_types(self):
        ev_read = _event(event_type="file_read", files=["/repo/a.py"])
        ev_edit = _event(event_type="file_edit", files=["/repo/b.py"])
        bundle = extract_evidence([ev_read, ev_edit], repo_root="/repo")
        self.assertIn("a.py", bundle.files_read)
        self.assertIn("b.py", bundle.files_changed)

    def test_unittest_command_is_test_command(self):
        ev = _event(tool_name="Bash", command="python -m unittest discover")
        bundle = extract_evidence([ev])
        self.assertIn("python -m unittest discover", bundle.test_commands)

    def test_path_outside_repo_kept_absolute(self):
        ev = _event(tool_name="Read", files=["/other/project/file.py"])
        bundle = extract_evidence([ev], repo_root="/repo")
        self.assertIn("/other/project/file.py", bundle.files_read)


if __name__ == "__main__":
    unittest.main()
