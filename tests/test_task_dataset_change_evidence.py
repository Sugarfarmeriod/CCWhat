"""Tests for Dataset change and patch evidence extraction."""

from __future__ import annotations

import unittest

from ccwhat.task_dataset import build_dataset_bundle, validate_dataset
from ccwhat.task_segments.models import NormalizedEvent, TaskSegment, TaskSegmentationResult


def _event(
    event_id: str,
    *,
    agent_id: str,
    event_type: str = "tool_call",
    text: str = "",
    tool_name: str | None = None,
    command: str | None = None,
    files: list[str] | None = None,
    raw_ref: dict | None = None,
    turn_index: int = 1,
) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=event_id,
        source="main",
        agent_id=agent_id,
        turn_index=turn_index,
        event_type=event_type,
        text=text,
        tool_name=tool_name,
        command=command,
        files=files or [],
        raw_ref=raw_ref or {},
    )


def _bundle(
    *,
    agent: str,
    events: list[NormalizedEvent],
    tasks: list[TaskSegment] | None = None,
):
    if tasks is None:
        tasks = [
            TaskSegment(
                task_id="task-001",
                title="任务 1",
                task_type="feature",
                status="unevaluated",
                start_event_id=events[0].event_id,
                end_event_id=events[-1].event_id,
            )
        ]
    return build_dataset_bundle(
        session_metadata={"agent": agent, "project_dir": "/repo", "repo": "CCWhat"},
        events=events,
        segmentation=TaskSegmentationResult(session_id=f"{agent}-session", tasks=tasks),
        created_at="2026-06-14T00:00:00Z",
    )


class TestDatasetChangeEvidence(unittest.TestCase):
    def test_claude_edit_write_and_bash_generate_changes_without_patches(self) -> None:
        events = [
            _event("main:1", agent_id="main", event_type="user_message", text="change files"),
            _event(
                "main:2",
                agent_id="main",
                tool_name="Edit",
                files=["src/app.py"],
                raw_ref={"tool_input": {
                    "file_path": "src/app.py",
                    "old_string": "old",
                    "new_string": "new",
                }},
            ),
            _event(
                "main:3",
                agent_id="main",
                tool_name="Write",
                files=["src/new.py"],
                raw_ref={"tool_input": {"file_path": "src/new.py", "content": "hello"}},
            ),
            _event("main:4", agent_id="main", tool_name="Bash", command="python script.py"),
        ]
        bundle = _bundle(agent="claude", events=events)
        trace = bundle.traces["trace-task-001"]

        self.assertEqual([c["change_id"] for c in trace["changes"]], ["change-001", "change-002", "change-003"])
        self.assertEqual([c["source"] for c in trace["changes"]], ["claude_edit", "claude_write", "bash_command"])
        self.assertEqual(trace["changes"][0]["old_string"], "old")
        self.assertEqual(trace["changes"][1]["content"], "hello")
        self.assertEqual(trace["changes"][2]["content"], "python script.py")
        self.assertEqual(trace["patches"], [])
        self.assertTrue(validate_dataset(bundle.to_bytes_files()).ok)

    def test_opencode_edit_diff_and_apply_patch_generate_patch_evidence(self) -> None:
        events = [
            _event("oc:1", agent_id="main", event_type="user_message", text="patch files"),
            _event(
                "oc:2",
                agent_id="main",
                tool_name="edit",
                files=["src/app.py"],
                raw_ref={
                    "agent": "opencode",
                    "content": {
                        "file": "src/app.py",
                        "oldString": "old",
                        "newString": "new",
                        "metadata": {"diff": "@@\n-old\n+new\n"},
                    },
                },
            ),
            _event(
                "oc:3",
                agent_id="main",
                tool_name="apply_patch",
                raw_ref={
                    "agent": "opencode",
                    "content": {"patchText": "*** Begin Patch\n*** End Patch"},
                },
            ),
        ]
        bundle = _bundle(agent="opencode", events=events)
        trace = bundle.traces["trace-task-001"]

        self.assertEqual(len(trace["patches"]), 2)
        self.assertEqual([p["format"] for p in trace["patches"]], ["opencode_diff", "apply_patch"])
        self.assertIn("patch-001", {c["patch_id"] for c in trace["changes"]})
        self.assertIn("patch-002", {c["patch_id"] for c in trace["changes"]})
        self.assertTrue(validate_dataset(bundle.to_bytes_files()).ok)

    def test_codex_patch_apply_end_generates_diff_and_content_evidence(self) -> None:
        events = [
            _event("codex:1", agent_id="main", event_type="user_message", text="apply patch"),
            _event(
                "codex:2",
                agent_id="main",
                event_type="assistant_text",
                raw_ref={"raw_event": {
                    "agent": "codex",
                    "payload": {
                        "type": "patch_apply_end",
                        "changes": {
                            "src/app.py": {"unified_diff": "@@\n-old\n+new\n"},
                            "src/new.py": {"content": "new file"},
                        },
                    },
                }},
            ),
        ]
        bundle = _bundle(agent="codex", events=events)
        trace = bundle.traces["trace-task-001"]

        self.assertEqual(len(trace["patches"]), 1)
        self.assertEqual(trace["patches"][0]["source"], "codex_patch_apply_end")
        self.assertEqual(trace["patches"][0]["format"], "unified_diff")
        self.assertEqual(len(trace["changes"]), 2)
        self.assertEqual(trace["changes"][0]["patch_id"], "patch-001")
        self.assertIsNone(trace["changes"][1]["patch_id"])
        self.assertEqual(trace["changes"][1]["content"], "new file")
        self.assertTrue(validate_dataset(bundle.to_bytes_files()).ok)

    def test_task_boundary_prevents_patch_leakage(self) -> None:
        events = [
            _event("main:1", agent_id="main", event_type="user_message", text="first"),
            _event("main:2", agent_id="main", tool_name="Bash", command="echo first"),
            _event("main:3", agent_id="main", event_type="user_message", text="second"),
            _event(
                "main:4",
                agent_id="main",
                event_type="assistant_text",
                raw_ref={"raw_event": {
                    "agent": "codex",
                    "payload": {
                        "type": "patch_apply_end",
                        "changes": {"src/second.py": {"unified_diff": "@@\n-a\n+b\n"}},
                    },
                }},
            ),
        ]
        tasks = [
            TaskSegment("task-001", "任务 1", "feature", "unevaluated", "main:1", "main:2"),
            TaskSegment("task-002", "任务 2", "feature", "unevaluated", "main:3", "main:4"),
        ]
        bundle = _bundle(agent="codex", events=events, tasks=tasks)

        first = bundle.traces["trace-task-001"]
        second = bundle.traces["trace-task-002"]
        self.assertEqual(first["patches"], [])
        self.assertEqual(first["changes"][0]["source"], "bash_command")
        self.assertEqual(len(second["patches"]), 1)
        self.assertEqual(second["patches"][0]["file"], "src/second.py")

    def test_bash_only_generates_command_change_without_patch(self) -> None:
        events = [
            _event("main:1", agent_id="main", event_type="user_message", text="run command"),
            _event("main:2", agent_id="main", tool_name="Bash", command="cat > file.py"),
        ]
        bundle = _bundle(agent="claude", events=events)
        trace = bundle.traces["trace-task-001"]

        self.assertEqual(len(trace["changes"]), 1)
        self.assertEqual(trace["changes"][0]["kind"], "command")
        self.assertEqual(trace["changes"][0]["patch_id"], None)
        self.assertEqual(trace["patches"], [])
