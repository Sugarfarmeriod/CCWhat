"""Regression checks for req-resp viewer replay UI helpers."""

from __future__ import annotations

from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "viewer" / "req-resp.html").read_text(
    encoding="utf-8"
)


def _function_snippet(name: str) -> str:
    start = HTML.index(f"function {name}")
    next_start = HTML.find("\nfunction ", start + len("function "))
    if next_start == -1:
        return HTML[start:]
    return HTML[start:next_start]


def test_replay_user_text_filters_leading_system_blocks() -> None:
    snippet = _function_snippet("extractReplayUserText")
    assert "stripLeadingSystemText(block.text)" in snippet
    assert "block?.type !== 'text'" in snippet
    assert "tool_result" not in snippet


def test_replay_uses_last_real_user_message() -> None:
    snippet = _function_snippet("findReplayUserMessage")
    assert "msg?.role !== 'user'" in snippet
    assert "extractReplayUserText(msg)" in snippet
    assert "return msg" in snippet


def test_replay_send_uses_filtered_original_text() -> None:
    snippet = _function_snippet("sendReplayFromModal")
    assert "findReplayUserMessage(msgs)" in snippet
    assert "extractReplayUserText(userMsg)" in snippet
    assert "content.find" not in snippet


def test_replay_diff_reconstructs_original_sse_response() -> None:
    snippet = _function_snippet("renderReplayDiffView")
    assert "parseSseEvents(currentModalRecord.sse_events)" in snippet
    assert "convertOriginalResponseToResult" in snippet
    assert "renderResponseMarkdownNoThinking(originalResult)" in snippet
