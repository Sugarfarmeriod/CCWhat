"""Tests for ccwhat.task_segments.events (tasks 2.1-2.4)."""

import unittest

from ccwhat.task_segments.events import (
    normalize_main_entries,
    normalize_subagent_entries,
    normalize_session_events,
)
from ccwhat.task_segments.models import NormalizedEvent


class TestNormalizeMainEntries(unittest.TestCase):
    """Task 2.1 – main session event normalization."""

    def _make_user(self, text: str, line: int = 1) -> dict:
        return {"type": "user", "content": text, "_fileLine": line}

    def _make_assistant_text(self, text: str, line: int = 2) -> dict:
        return {"type": "assistant", "content": [{"type": "text", "text": text}], "_fileLine": line}

    def _make_tool_call(self, name: str, tool_id: str, inp: dict, line: int = 3) -> dict:
        return {
            "type": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": name,
                    "input": inp,
                }
            ],
            "_fileLine": line,
        }

    def _make_tool_result_user(self, tool_id: str, result: str, line: int = 4) -> dict:
        return {
            "type": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                }
            ],
            "_fileLine": line,
        }

    # ---- basic event_id / source / agent_id ----

    def test_event_id_uses_file_line(self):
        entries = [self._make_user("hi", line=10)]
        events = normalize_main_entries(entries, "sess1")
        self.assertEqual(events[0].event_id, "main:10")

    def test_event_id_falls_back_to_idx(self):
        entry = {"type": "user", "content": "hi"}  # no _fileLine
        events = normalize_main_entries([entry], "sess1")
        self.assertEqual(events[0].event_id, "main:1")

    def test_source_and_agent_id(self):
        entries = [self._make_user("hi")]
        ev = normalize_main_entries(entries, "sess1")[0]
        self.assertEqual(ev.source, "main")
        self.assertEqual(ev.agent_id, "main")

    # ---- user message ----

    def test_user_message_type(self):
        entries = [self._make_user("hello world")]
        ev = normalize_main_entries(entries, "sess1")[0]
        self.assertEqual(ev.event_type, "user_message")
        self.assertEqual(ev.text, "hello world")

    def test_turn_index_increments_on_user(self):
        entries = [
            self._make_user("first", line=1),
            self._make_assistant_text("reply", line=2),
            self._make_user("second", line=3),
        ]
        events = normalize_main_entries(entries, "sess1")
        user_events = [e for e in events if e.event_type == "user_message"]
        self.assertEqual(user_events[0].turn_index, 1)
        self.assertEqual(user_events[1].turn_index, 2)

    def test_assistant_turn_index_does_not_increment(self):
        entries = [
            self._make_user("q", line=1),
            self._make_assistant_text("a", line=2),
        ]
        events = normalize_main_entries(entries, "sess1")
        assistant_ev = next(e for e in events if e.event_type == "assistant_text")
        self.assertEqual(assistant_ev.turn_index, 1)

    # ---- assistant text ----

    def test_assistant_text_type(self):
        entries = [self._make_assistant_text("here is the answer")]
        ev = normalize_main_entries(entries, "sess1")[0]
        self.assertEqual(ev.event_type, "assistant_text")
        self.assertEqual(ev.text, "here is the answer")

    def test_assistant_plain_string_content(self):
        entry = {"type": "assistant", "content": "plain text", "_fileLine": 5}
        ev = normalize_main_entries([entry], "sess1")[0]
        self.assertEqual(ev.event_type, "assistant_text")
        self.assertEqual(ev.text, "plain text")

    # ---- tool_call ----

    def test_tool_call_type(self):
        entries = [self._make_tool_call("Bash", "tu-1", {"command": "ls"}, line=5)]
        ev = normalize_main_entries(entries, "sess1")[0]
        self.assertEqual(ev.event_type, "tool_call")
        self.assertEqual(ev.tool_name, "Bash")
        self.assertEqual(ev.tool_use_id, "tu-1")
        self.assertEqual(ev.command, "ls")

    def test_tool_call_extracts_file_path(self):
        entries = [
            self._make_tool_call(
                "Read", "tu-2", {"file_path": "/some/file.py"}, line=6
            )
        ]
        ev = normalize_main_entries(entries, "sess1")[0]
        self.assertIn("/some/file.py", ev.files)

    def test_multiple_tool_use_blocks_produce_multiple_events(self):
        entry = {
            "type": "assistant",
            "content": [
                {"type": "tool_use", "id": "tu-a", "name": "Read", "input": {"file_path": "/a.py"}},
                {"type": "tool_use", "id": "tu-b", "name": "Bash", "input": {"command": "echo hi"}},
            ],
            "_fileLine": 7,
        }
        events = normalize_main_entries([entry], "sess1")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].tool_name, "Read")
        self.assertEqual(events[1].tool_name, "Bash")

    # ---- tool_result (user message with tool_result blocks) ----

    def test_tool_result_type(self):
        entries = [self._make_tool_result_user("tu-1", "output text", line=8)]
        events = normalize_main_entries(entries, "sess1")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "tool_result")
        self.assertEqual(events[0].tool_use_id, "tu-1")
        self.assertEqual(events[0].text, "output text")

    # ---- legacy top-level "tool" type ----

    def test_legacy_tool_type(self):
        entry = {
            "type": "tool",
            "tool_use_id": "tu-99",
            "content": "legacy result",
            "_fileLine": 9,
        }
        events = normalize_main_entries([entry], "sess1")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "tool_result")
        self.assertEqual(events[0].tool_use_id, "tu-99")
        self.assertEqual(events[0].text, "legacy result")

    # ---- timestamp and raw_ref ----

    def test_timestamp_preserved(self):
        entry = {"type": "user", "content": "hi", "_fileLine": 1, "timestamp": "2024-01-01T00:00:00Z"}
        ev = normalize_main_entries([entry], "sess1")[0]
        self.assertEqual(ev.timestamp, "2024-01-01T00:00:00Z")

    def test_raw_ref_contains_file_line(self):
        entry = {"type": "user", "content": "hi", "_fileLine": 42}
        ev = normalize_main_entries([entry], "sess1")[0]
        self.assertEqual(ev.raw_ref["_fileLine"], 42)


class TestToolCallAssociation(unittest.TestCase):
    """Task 2.2 – tool call id association."""

    def test_tool_result_updates_tool_call_metadata(self):
        entries = [
            {
                "type": "assistant",
                "content": [
                    {"type": "tool_use", "id": "tu-assoc", "name": "Bash", "input": {"command": "pwd"}}
                ],
                "_fileLine": 1,
            },
            {
                "type": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "tu-assoc", "content": "/home/user"}
                ],
                "_fileLine": 2,
            },
        ]
        events = normalize_main_entries(entries, "sess1")
        tool_call_ev = next(e for e in events if e.event_type == "tool_call")
        self.assertEqual(tool_call_ev.metadata.get("result_text"), "/home/user")

    def test_unmatched_tool_result_does_not_crash(self):
        entries = [
            {
                "type": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "no-such-id", "content": "orphan"}
                ],
                "_fileLine": 1,
            }
        ]
        # Should not raise
        events = normalize_main_entries(entries, "sess1")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "tool_result")

    def test_multiple_tool_calls_associated_independently(self):
        entries = [
            {
                "type": "assistant",
                "content": [
                    {"type": "tool_use", "id": "tu-x", "name": "Read", "input": {}},
                    {"type": "tool_use", "id": "tu-y", "name": "Bash", "input": {"command": "ls"}},
                ],
                "_fileLine": 1,
            },
            {
                "type": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "tu-x", "content": "file content"},
                    {"type": "tool_result", "tool_use_id": "tu-y", "content": "dir listing"},
                ],
                "_fileLine": 2,
            },
        ]
        events = normalize_main_entries(entries, "sess1")
        ev_x = next(e for e in events if e.tool_use_id == "tu-x")
        ev_y = next(e for e in events if e.tool_use_id == "tu-y" and e.event_type == "tool_call")
        self.assertEqual(ev_x.metadata.get("result_text"), "file content")
        self.assertEqual(ev_y.metadata.get("result_text"), "dir listing")


class TestNormalizeSubagentEntries(unittest.TestCase):
    """Task 2.3 – subagent event normalization."""

    def _make_subagent(self, agent_id: str, entries: list[dict], meta: dict | None = None) -> dict:
        return {
            "agentId": agent_id,
            "meta": meta or {},
            "entries": entries,
        }

    def test_subagent_event_id_prefix(self):
        subagent = self._make_subagent(
            "agent-abc",
            [{"type": "user", "content": "do something", "_fileLine": 5}],
        )
        events = normalize_subagent_entries([subagent])
        self.assertEqual(events[0].event_id, "agent-agent-abc:5")

    def test_subagent_source_and_agent_id(self):
        subagent = self._make_subagent(
            "sa-42",
            [{"type": "user", "content": "task", "_fileLine": 1}],
        )
        ev = normalize_subagent_entries([subagent])[0]
        self.assertEqual(ev.source, "subagent")
        self.assertEqual(ev.agent_id, "sa-42")

    def test_subagent_metadata_includes_agent_type_and_description(self):
        subagent = self._make_subagent(
            "sa-1",
            [{"type": "user", "content": "x", "_fileLine": 1}],
            meta={"agentType": "worker", "description": "does stuff"},
        )
        ev = normalize_subagent_entries([subagent])[0]
        self.assertEqual(ev.metadata.get("agentType"), "worker")
        self.assertEqual(ev.metadata.get("description"), "does stuff")

    def test_multiple_subagents(self):
        subagents = [
            self._make_subagent("sa-1", [{"type": "user", "content": "a", "_fileLine": 1}]),
            self._make_subagent("sa-2", [{"type": "user", "content": "b", "_fileLine": 1}]),
        ]
        events = normalize_subagent_entries(subagents)
        self.assertEqual(len(events), 2)
        agent_ids = {e.agent_id for e in events}
        self.assertEqual(agent_ids, {"sa-1", "sa-2"})

    def test_subagent_tool_call_still_works(self):
        subagent = self._make_subagent(
            "sa-3",
            [
                {
                    "type": "assistant",
                    "content": [
                        {"type": "tool_use", "id": "tu-sub", "name": "Bash", "input": {"command": "echo"}}
                    ],
                    "_fileLine": 2,
                }
            ],
        )
        events = normalize_subagent_entries([subagent])
        self.assertEqual(events[0].event_type, "tool_call")
        self.assertEqual(events[0].agent_id, "sa-3")


class TestNormalizeSessionEvents(unittest.TestCase):
    """normalize_session_events – integration."""

    def test_empty_session_does_not_crash(self):
        session: dict = {}
        events = normalize_session_events(session)
        self.assertEqual(events, [])

    def test_session_with_only_main(self):
        session = {
            "sessionId": "s1",
            "entries": [{"type": "user", "content": "hi", "_fileLine": 1}],
        }
        events = normalize_session_events(session)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].source, "main")

    def test_session_combines_main_and_subagent(self):
        session = {
            "sessionId": "s2",
            "entries": [{"type": "user", "content": "main msg", "_fileLine": 1}],
            "subagents": [
                {
                    "agentId": "sub-1",
                    "meta": {},
                    "entries": [{"type": "user", "content": "sub msg", "_fileLine": 1}],
                }
            ],
        }
        events = normalize_session_events(session)
        self.assertEqual(len(events), 2)
        sources = {e.source for e in events}
        self.assertEqual(sources, {"main", "subagent"})

    def test_empty_subagents_list(self):
        session = {
            "sessionId": "s3",
            "entries": [],
            "subagents": [],
        }
        events = normalize_session_events(session)
        self.assertEqual(events, [])

    def test_subagent_inserted_after_spawn_not_after_all_main_events(self):
        """Without timestamps, subagent events must follow their Agent tool_use,
        not appear after all main events (which would mis-attribute evidence)."""
        session = {
            "sessionId": "test",
            "main": [
                {"type": "user", "content": "任务1", "_fileLine": 1},
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t1",
                                "name": "Agent",
                                "input": {"description": "helper"},
                            }
                        ]
                    },
                    "_fileLine": 2,
                },
                {
                    "type": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": "t1", "content": "done"}
                    ],
                    "_fileLine": 3,
                },
                {"type": "user", "content": "任务2", "_fileLine": 4},
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "t2",
                                "name": "Edit",
                                "input": {"file_path": "importer.py"},
                            }
                        ]
                    },
                    "_fileLine": 5,
                },
                {
                    "type": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": "t2", "content": "ok"}
                    ],
                    "_fileLine": 6,
                },
            ],
            "subagents": [
                {
                    "agentId": "abc",
                    "meta": {},
                    "entries": [
                        {"type": "user", "content": "做子任务", "_fileLine": 1},
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": "st1",
                                        "name": "Read",
                                        "input": {"file_path": "export.py"},
                                    }
                                ]
                            },
                            "_fileLine": 2,
                        },
                    ],
                }
            ],
        }
        events = normalize_session_events(session)
        event_ids = [e.event_id for e in events]

        # The subagent's Read export.py event must come before main:4 (任务2)
        subagent_read_idx = next(
            i for i, e in enumerate(events)
            if e.source == "subagent" and "export.py" in e.files
        )
        task2_idx = next(
            i for i, e in enumerate(events)
            if e.event_id == "main:4"
        )
        self.assertLess(
            subagent_read_idx,
            task2_idx,
            msg=(
                f"subagent Read(export.py) at index {subagent_read_idx} should be "
                f"before main:4 (任务2) at index {task2_idx}. "
                f"Order: {event_ids}"
            ),
        )

        # Sanity: Agent tool_use (main:2) must come before the subagent events
        agent_spawn_idx = next(
            i for i, e in enumerate(events)
            if e.event_id == "main:2" and e.tool_name == "Agent"
        )
        self.assertLess(agent_spawn_idx, subagent_read_idx)


if __name__ == "__main__":
    unittest.main()
