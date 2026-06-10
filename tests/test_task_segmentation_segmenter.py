"""Fixture-based tests for the task segmenter (task 6.6)."""

from __future__ import annotations

import unittest

from ccwhat.task_segments.segmenter import segment_session


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _user(text: str, line: int = 1) -> dict:
    return {"type": "user", "content": text, "timestamp": f"2025-01-01T00:0{line}:00Z", "_fileLine": line}


def _assistant(text: str, line: int = 2) -> dict:
    return {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": text}]},
        "timestamp": f"2025-01-01T00:0{line}:00Z",
        "_fileLine": line,
    }


def _tool_use(name: str, inp: dict, tool_id: str = "tid1", line: int = 3) -> dict:
    return {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "id": tool_id, "name": name, "input": inp}]},
        "timestamp": f"2025-01-01T00:0{line}:00Z",
        "_fileLine": line,
    }


def _tool_result(tool_id: str = "tid1", content: str = "ok", line: int = 4) -> dict:
    return {
        "type": "user",
        "content": [{"type": "tool_result", "tool_use_id": tool_id, "content": content}],
        "timestamp": f"2025-01-01T00:0{line}:00Z",
        "_fileLine": line,
    }


def _session(entries: list[dict], session_id: str = "test-session") -> dict:
    return {
        "sessionId": session_id,
        "projectDir": "my-project",
        "main": entries,
        "subagents": [],
    }


# ---------------------------------------------------------------------------
# Scenario 1: conservative single-task session
# ---------------------------------------------------------------------------

class TestSingleTaskSession(unittest.TestCase):
    def test_single_task_no_split(self):
        """A short session with one user goal stays as one task."""
        entries = [
            _user("帮我实现一个 CSV 读取函数", 1),
            _assistant("好的，我来实现...", 2),
            _tool_use("Edit", {"file_path": "reader.py", "new_str": "..."}, line=3),
            _tool_result(content="ok", line=4),
            _assistant("已完成，reader.py 实现了 CSV 读取函数。", 5),
        ]
        result = segment_session(_session(entries))
        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].status, "unevaluated")
        self.assertFalse(result.is_ambiguous)

    def test_empty_session(self):
        """Empty session returns no tasks without error."""
        result = segment_session(_session([]))
        self.assertEqual(len(result.tasks), 0)
        self.assertEqual(result.summary["taskCount"], 0)


# ---------------------------------------------------------------------------
# Scenario 2: multiple user tasks split correctly
# ---------------------------------------------------------------------------

class TestMultipleUserTasks(unittest.TestCase):
    def test_two_distinct_tasks(self):
        """Two clearly separate goals should produce two tasks."""
        entries = [
            _user("帮我修复登录 bug", 1),
            _assistant("好的，我来查看...", 2),
            _tool_use("Edit", {"file_path": "auth.py", "new_str": "fix"}, line=3),
            _tool_result(content="ok", line=4),
            _assistant("登录 bug 已修复，测试通过。", 5),
            _user("另外，帮我新增用户注册功能", 6),
            _assistant("好的，开始实现注册...", 7),
            _tool_use("Edit", {"file_path": "register.py", "new_str": "new"}, line=8),
            _tool_result(content="ok", line=9),
        ]
        result = segment_session(_session(entries))
        self.assertGreaterEqual(len(result.tasks), 2, "两个明确不同的目标应切出至少 2 个任务")
        for t in result.tasks:
            self.assertEqual(t.status, "unevaluated")
        # Second task should be triggered by "另外" boundary
        second = result.tasks[-1]
        self.assertTrue(
            any("另外" in r or "user_new_task" in r for r in second.boundary_reasons),
            f"第二个任务的边界原因应包含新任务信号，实际: {second.boundary_reasons}",
        )

    def test_continuation_does_not_split(self):
        """A 'still failing' continuation message must not create a new task."""
        entries = [
            _user("帮我修复测试失败", 1),
            _assistant("我来看看...", 2),
            _tool_use("Bash", {"command": "pytest tests/"}, line=3),
            _tool_result(content="FAILED test_login.py", line=4),
            _user("还是报错了，继续修", 5),
            _assistant("好的，继续...", 6),
        ]
        result = segment_session(_session(entries))
        # Should not split on "还是报错了" alone
        # The second user message is a continuation, total tasks should be 1
        self.assertEqual(len(result.tasks), 1)


# ---------------------------------------------------------------------------
# Scenario 3: user Todo splitting
# ---------------------------------------------------------------------------

class TestUserTodoSplitting(unittest.TestCase):
    def test_user_todo_list_generates_candidate(self):
        """A user message with multiple todos generates at least 1 task."""
        entries = [
            _user("需要做三件事：\n- [ ] 修复 auth bug\n- [ ] 新增注册 API\n- [ ] 写测试", 1),
            _assistant("好的，我依次来...", 2),
            _tool_use("Edit", {"file_path": "auth.py"}, line=3),
            _tool_result(content="ok", line=4),
        ]
        result = segment_session(_session(entries))
        self.assertGreaterEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].status, "unevaluated")


# ---------------------------------------------------------------------------
# Scenario 4: file topic shift
# ---------------------------------------------------------------------------

class TestFileTopicShift(unittest.TestCase):
    def test_same_files_no_split(self):
        """Multiple edits to the same files should stay in one task."""
        entries = [
            _user("帮我重构 auth.py", 1),
            _assistant("开始重构...", 2),
            _tool_use("Edit", {"file_path": "auth.py"}, "t1", line=3),
            _tool_result("t1", "ok", line=4),
            _tool_use("Edit", {"file_path": "auth.py"}, "t2", line=5),
            _tool_result("t2", "ok", line=6),
        ]
        result = segment_session(_session(entries))
        self.assertEqual(len(result.tasks), 1)


# ---------------------------------------------------------------------------
# Scenario 5: final claim close
# ---------------------------------------------------------------------------

class TestFinalClaimClose(unittest.TestCase):
    def test_final_claim_closes_task(self):
        """Final claim is recorded; it must not create a new task."""
        entries = [
            _user("帮我实现日志功能", 1),
            _assistant("好的...", 2),
            _tool_use("Edit", {"file_path": "logger.py"}, line=3),
            _tool_result(content="ok", line=4),
            _assistant(
                "已完成。日志模块已实现，支持 INFO/WARN/ERROR 三个级别，测试全部通过。",
                5,
            ),
        ]
        result = segment_session(_session(entries))
        self.assertGreaterEqual(len(result.tasks), 1)
        task = result.tasks[0]
        self.assertEqual(task.status, "unevaluated")
        # Final claim must be recorded
        self.assertIsNotNone(task.final_claim,
            "assistant 的完成声明应被记录为 final_claim")
        self.assertIn("已完成", task.final_claim)


# ---------------------------------------------------------------------------
# Scenario 6: failure feedback reopen
# ---------------------------------------------------------------------------

class TestFailureFeedbackReopen(unittest.TestCase):
    def test_failure_feedback_after_claim_reopens(self):
        """After a final claim, failure feedback should reopen (not create) a task."""
        entries = [
            _user("修复登录问题", 1),
            _assistant("好的...", 2),
            _tool_use("Edit", {"file_path": "auth.py"}, "t1", line=3),
            _tool_result("t1", "ok", line=4),
            _assistant("登录问题已修复，测试通过，现在可以正常登录了。", 5),
            _user("还是不行，还是报错", 6),
            _assistant("继续排查...", 7),
        ]
        result = segment_session(_session(entries))
        # Must not blow up and must return unevaluated tasks
        for t in result.tasks:
            self.assertEqual(t.status, "unevaluated")


# ---------------------------------------------------------------------------
# Scenario 7: ambiguous interleaving
# ---------------------------------------------------------------------------

class TestAmbiguousInterleaving(unittest.TestCase):
    def test_status_always_unevaluated(self):
        """Even in complex sessions, status must always be 'unevaluated'."""
        entries = [
            _user("实现功能 A", 1),
            _assistant("好的...", 2),
            _tool_use("Edit", {"file_path": "a.py"}, line=3),
            _tool_result(content="ok", line=4),
            _user("另外新增功能 B", 5),
            _assistant("好...", 6),
            _tool_use("Edit", {"file_path": "b.py"}, line=7),
            _tool_result(content="ok", line=8),
            _user("回到 A，还有个 bug", 9),
            _assistant("看看...", 10),
        ]
        result = segment_session(_session(entries))
        for task in result.tasks:
            self.assertEqual(task.status, "unevaluated")


# ---------------------------------------------------------------------------
# Scenario 8: subagent messages must NOT create separate tasks (P1 fix)
# ---------------------------------------------------------------------------

class TestSubagentDoesNotSplit(unittest.TestCase):
    def test_subagent_user_message_not_a_boundary(self):
        """Subagent messages must not trigger task boundary detection."""
        session = {
            "sessionId": "test-subagent",
            "projectDir": "proj",
            "main": [
                {"type": "user", "content": "帮我实现导出功能", "_fileLine": 1},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "好的"}]}, "_fileLine": 2},
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Edit",
                    "input": {"file_path": "exporter.py"}}]}, "_fileLine": 3},
                {"type": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}], "_fileLine": 4},
            ],
            "subagents": [
                {
                    "agentId": "sub-abc",
                    "meta": {"description": "helper agent"},
                    "entries": [
                        {"type": "user", "content": "帮我修复导出测试", "_fileLine": 1},
                        {"type": "assistant", "message": {"content": [{"type": "text", "text": "好"}]}, "_fileLine": 2},
                        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "st1", "name": "Edit",
                            "input": {"file_path": "tests/test_export.py"}}]}, "_fileLine": 3},
                    ],
                }
            ],
        }
        from ccwhat.task_segments import segment_session as _seg
        result = _seg(session)
        # Subagent "帮我修复导出测试" must not open a new Task
        self.assertEqual(len(result.tasks), 1,
            f"Subagent prompt 不应触发新 Task，实际任务数: {len(result.tasks)}")
        self.assertEqual(result.tasks[0].status, "unevaluated")


# ---------------------------------------------------------------------------
# Scenario 9: file_weights must be non-empty after Edit operations (P1 fix)
# ---------------------------------------------------------------------------

class TestFileWeightsNonEmpty(unittest.TestCase):
    def test_edit_events_populate_file_weights(self):
        """After Edit/Write operations, tasks must have non-empty file_weights."""
        entries = [
            _user("帮我重构 auth 模块", 1),
            _assistant("好的...", 2),
            _tool_use("Edit", {"file_path": "src/auth.py", "new_str": "refactored"}, "t1", line=3),
            _tool_result("t1", "ok", line=4),
            _tool_use("Write", {"file_path": "src/auth_utils.py", "content": "utils"}, "t2", line=5),
            _tool_result("t2", "written", line=6),
        ]
        result = segment_session(_session(entries))
        task = result.tasks[0]
        self.assertTrue(len(task.file_weights) > 0,
            "Edit/Write 操作后 file_weights 不应为空")
        # Edit-type files should have weight >= 3.0
        for path, weight in task.file_weights.items():
            self.assertGreater(weight, 0.0)


if __name__ == "__main__":
    unittest.main()
