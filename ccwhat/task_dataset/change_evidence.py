"""Extract Dataset change and patch evidence from normalized task events."""

from __future__ import annotations

from typing import Any

from ccwhat.task_segments.models import NormalizedEvent


class _EvidenceBuilder:
    def __init__(self) -> None:
        self.changes: list[dict[str, Any]] = []
        self.patches: list[dict[str, Any]] = []

    def add_change(
        self,
        *,
        event_id: str,
        file: str | None,
        kind: str,
        source: str,
        old_string: str | None = None,
        new_string: str | None = None,
        content: str | None = None,
        patch_id: str | None = None,
        confidence: str,
    ) -> dict[str, Any]:
        change = {
            "change_id": f"change-{len(self.changes) + 1:03d}",
            "event_id": event_id,
            "file": file,
            "kind": kind,
            "source": source,
            "old_string": old_string,
            "new_string": new_string,
            "content": content,
            "patch_id": patch_id,
            "confidence": confidence,
        }
        self.changes.append(change)
        return change

    def add_patch(
        self,
        *,
        file: str | None,
        source: str,
        format: str,
        patch: str,
        confidence: str = "high",
        scope: str = "step",
    ) -> dict[str, Any]:
        patch_entry = {
            "patch_id": f"patch-{len(self.patches) + 1:03d}",
            "scope": scope,
            "file": file,
            "source": source,
            "format": format,
            "confidence": confidence,
            "patch": patch,
        }
        self.patches.append(patch_entry)
        return patch_entry


def extract_change_evidence(
    events: list[NormalizedEvent],
    agent: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return Dataset v1 ``changes`` and ``patches`` from task-scoped events.

    The caller supplies events already sliced to one task boundary. This
    function only uses data already present on the normalized event and its
    minimal raw/metadata payload.
    """
    builder = _EvidenceBuilder()
    agent_hint = (agent or "").lower()
    for event in events:
        evidence_payload = _event_payload(event)
        raw_event = _raw_event(event)
        tool_name = (event.tool_name or "").lower()
        raw_agent = str(_deep_get(raw_event, ("agent",)) or "").lower()
        event_agent = agent_hint or raw_agent

        if _is_codex_patch_apply_end(event, raw_event):
            _extract_codex_patch_apply_end(builder, event, raw_event)
            continue

        if event.event_type == "tool_call":
            if event_agent == "opencode" or _looks_opencode(event, evidence_payload, raw_event):
                _extract_opencode_tool(builder, event, evidence_payload, raw_event)
            elif event_agent == "claude" or tool_name in {"edit", "multiedit", "write", "bash"}:
                _extract_claude_tool(builder, event, evidence_payload)
            else:
                _extract_claude_tool(builder, event, evidence_payload)

    return builder.changes, builder.patches


def _extract_claude_tool(
    builder: _EvidenceBuilder,
    event: NormalizedEvent,
    payload: dict[str, Any],
) -> None:
    tool_name = event.tool_name or ""
    tool_key = tool_name.lower()
    if tool_key == "edit":
        file_path = _file_from_payload(payload, event)
        old, new = _old_new_strings(payload)
        if file_path and (old is not None or new is not None):
            builder.add_change(
                event_id=event.event_id,
                file=file_path,
                kind="edit",
                source="claude_edit",
                old_string=old,
                new_string=new,
                confidence="medium",
            )
    elif tool_key == "multiedit":
        file_path = _file_from_payload(payload, event)
        edits = payload.get("edits")
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                old, new = _old_new_strings(edit)
                if file_path and (old is not None or new is not None):
                    builder.add_change(
                        event_id=event.event_id,
                        file=file_path,
                        kind="edit",
                        source="claude_edit",
                        old_string=old,
                        new_string=new,
                        confidence="medium",
                    )
    elif tool_key == "write":
        file_path = _file_from_payload(payload, event)
        content = _string_value(payload, "content")
        if file_path and content is not None:
            builder.add_change(
                event_id=event.event_id,
                file=file_path,
                kind="write",
                source="claude_write",
                content=content,
                confidence="medium",
            )
    elif tool_key == "bash" or event.command:
        command = event.command or _string_value(payload, "command")
        if command:
            builder.add_change(
                event_id=event.event_id,
                file=None,
                kind="command",
                source="bash_command",
                content=command,
                confidence="low",
            )


def _extract_opencode_tool(
    builder: _EvidenceBuilder,
    event: NormalizedEvent,
    payload: dict[str, Any],
    raw_event: dict[str, Any],
) -> None:
    file_path = _file_from_payload(payload, event) or _file_from_payload(raw_event, event)
    old, new = _old_new_strings(payload)
    if old is None and new is None:
        old, new = _old_new_strings(raw_event)
    if file_path and (old is not None or new is not None):
        builder.add_change(
            event_id=event.event_id,
            file=file_path,
            kind="edit",
            source="opencode_edit",
            old_string=old,
            new_string=new,
            confidence="medium",
        )

    for diff_value, diff_file in _opencode_diffs(payload, raw_event, file_path):
        patch = builder.add_patch(
            file=diff_file,
            source="opencode_edit",
            format="opencode_diff",
            patch=diff_value,
            confidence="high",
        )
        builder.add_change(
            event_id=event.event_id,
            file=diff_file,
            kind="patch",
            source="opencode_edit",
            patch_id=patch["patch_id"],
            confidence="high",
        )

    patch_text = _find_first_string_by_keys(payload, ("patchText", "patch_text"))
    if patch_text is None:
        patch_text = _find_first_string_by_keys(raw_event, ("patchText", "patch_text"))
    tool_name = (event.tool_name or "").lower()
    if patch_text and ("apply_patch" in tool_name or "patch" in tool_name or patch_text):
        patch = builder.add_patch(
            file=file_path,
            source="opencode_patch",
            format="apply_patch",
            patch=patch_text,
            confidence="high",
        )
        builder.add_change(
            event_id=event.event_id,
            file=file_path,
            kind="patch",
            source="opencode_patch",
            patch_id=patch["patch_id"],
            confidence="high",
        )

    if (event.tool_name or "").lower() == "bash" or event.command:
        command = event.command or _string_value(payload, "command")
        if command:
            builder.add_change(
                event_id=event.event_id,
                file=None,
                kind="command",
                source="bash_command",
                content=command,
                confidence="low",
            )


def _extract_codex_patch_apply_end(
    builder: _EvidenceBuilder,
    event: NormalizedEvent,
    raw_event: dict[str, Any],
) -> None:
    payload = raw_event.get("payload") if isinstance(raw_event.get("payload"), dict) else raw_event
    changes = payload.get("changes") if isinstance(payload, dict) else None
    if not isinstance(changes, dict):
        return
    for file_path, file_change in changes.items():
        if not isinstance(file_change, dict):
            continue
        unified_diff = _string_value(file_change, "unified_diff") or _string_value(file_change, "unifiedDiff")
        content = _string_value(file_change, "content")
        patch_id: str | None = None
        kind = "write" if content is not None and not unified_diff else "patch"
        if unified_diff:
            patch = builder.add_patch(
                file=str(file_path),
                source="codex_patch_apply_end",
                format="unified_diff",
                patch=unified_diff,
                confidence="high",
            )
            patch_id = patch["patch_id"]
        if unified_diff or content is not None:
            builder.add_change(
                event_id=event.event_id,
                file=str(file_path),
                kind=kind,
                source="codex_patch_apply_end",
                content=content,
                patch_id=patch_id,
                confidence="high",
            )


def _event_payload(event: NormalizedEvent) -> dict[str, Any]:
    candidates = [
        event.raw_ref.get("tool_input"),
        event.raw_ref.get("content"),
        event.metadata.get("tool_input"),
    ]
    raw_event = _raw_event(event)
    if isinstance(raw_event, dict):
        candidates.extend([
            raw_event.get("content"),
            _deep_get(raw_event, ("raw", "payload")),
            _deep_get(raw_event, ("payload",)),
        ])
    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate
    return {}


def _raw_event(event: NormalizedEvent) -> dict[str, Any]:
    raw_event = event.raw_ref.get("raw_event") or event.raw_ref.get("raw") or event.metadata.get("raw_event")
    return raw_event if isinstance(raw_event, dict) else {}


def _is_codex_patch_apply_end(event: NormalizedEvent, raw_event: dict[str, Any]) -> bool:
    payload_type = _deep_get(raw_event, ("payload", "type"))
    raw_type = raw_event.get("type")
    return (
        payload_type == "patch_apply_end"
        or raw_type == "patch_apply_end"
        or event.raw_ref.get("type") == "patch_apply_end"
        or event.metadata.get("type") == "patch_apply_end"
    )


def _looks_opencode(
    event: NormalizedEvent,
    payload: dict[str, Any],
    raw_event: dict[str, Any],
) -> bool:
    return (
        str(event.raw_ref.get("agent") or "").lower() == "opencode"
        or str(raw_event.get("agent") or "").lower() == "opencode"
        or _find_first_string_by_keys(payload, ("oldString", "newString", "patchText")) is not None
        or _find_first_string_by_keys(raw_event, ("oldString", "newString", "patchText")) is not None
    )


def _old_new_strings(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    old = (
        _string_value(payload, "old_string")
        or _string_value(payload, "oldString")
        or _string_value(payload, "old_str")
    )
    new = (
        _string_value(payload, "new_string")
        or _string_value(payload, "newString")
        or _string_value(payload, "new_str")
    )
    return old, new


def _file_from_payload(payload: dict[str, Any], event: NormalizedEvent) -> str | None:
    value = _file_from_mapping(payload)
    if value:
        return value
    if event.files:
        return event.files[0]
    return None


def _file_from_mapping(payload: dict[str, Any]) -> str | None:
    for key in ("file_path", "path", "file", "filename", "target_file"):
        value = _string_value(payload, key)
        if value:
            return value
    return None


def _opencode_diffs(
    payload: dict[str, Any],
    raw_event: dict[str, Any],
    fallback_file: str | None,
) -> list[tuple[str, str | None]]:
    result: list[tuple[str, str | None]] = []
    _collect_opencode_diffs(payload, fallback_file, result)
    _collect_opencode_diffs(raw_event, fallback_file, result)
    deduped: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for item in result:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _collect_opencode_diffs(
    value: Any,
    fallback_file: str | None,
    result: list[tuple[str, str | None]],
) -> None:
    if isinstance(value, dict):
        for key in ("diff", "filediff", "fileDiff"):
            diff_value = value.get(key)
            if isinstance(diff_value, str) and diff_value:
                result.append((diff_value, _file_from_mapping(value) or fallback_file))
            elif isinstance(diff_value, dict):
                for file_path, patch in diff_value.items():
                    if isinstance(patch, str) and patch:
                        result.append((patch, str(file_path)))
        for child in value.values():
            _collect_opencode_diffs(child, fallback_file, result)
    elif isinstance(value, list):
        for child in value:
            _collect_opencode_diffs(child, fallback_file, result)


def _find_first_string_by_keys(value: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            item = value.get(key)
            if isinstance(item, str) and item:
                return item
        for item in value.values():
            found = _find_first_string_by_keys(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_first_string_by_keys(item, keys)
            if found is not None:
                return found
    return None


def _string_value(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value != "" else None


def _deep_get(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
