"""Evidence extraction from normalized events."""

from __future__ import annotations

import os
from typing import Any

from .models import EvidenceBundle, NormalizedEvent

# Tool name sets for classification
_READ_TOOLS = {"Read", "Grep", "Glob", "Find"}
_EDIT_TOOLS = {"Edit", "Write", "Patch", "MultiEdit", "str_replace_editor"}

# Substrings that identify test/build commands
_TEST_PATTERNS = ("pytest", "unittest", "npm test", "npm run test", "npm run build")

# Substrings that indicate an error result
_ERROR_PATTERNS = ("Traceback", "Error:", "failed", "FAILED")


# ---------------------------------------------------------------------------
# Task 4.2 – path normalisation
# ---------------------------------------------------------------------------

def normalize_path(path: str, repo_root: str | None = None) -> str:
    """Return a repo-relative path when possible, otherwise the original path.

    Rules:
    - If *path* is absolute and *repo_root* is provided, compute the relative
      path via ``os.path.relpath``.
    - If the result starts with ``../`` the path escapes the repo, so keep the
      original absolute path.
    - Otherwise return the relative path.
    - If *path* is already relative, or *repo_root* is None, return *path*
      unchanged.
    """
    if repo_root and os.path.isabs(path):
        rel = os.path.relpath(path, repo_root)
        if rel.startswith("../"):
            return path
        return rel
    return path


# ---------------------------------------------------------------------------
# Task 4.3 – final-claim detection
# ---------------------------------------------------------------------------

def detect_final_claim(
    event: NormalizedEvent,
    rules: dict[str, Any] | None = None,
) -> str | None:
    """Return a text summary if *event* looks like a final claim, else None.

    Conditions (all must hold):
    1. ``event.event_type == "assistant_text"``
    2. ``len(event.text) > 30``
    3. The text contains at least one marker from ``rules["final_claim_markers"]``
    """
    if event.event_type != "assistant_text":
        return None
    if len(event.text) < 20:
        return None

    if rules is None:
        return None

    markers_cfg = rules.get("final_claim_markers", {})
    zh_phrases: list[str] = markers_cfg.get("zh_phrases", [])
    en_words: list[str] = markers_cfg.get("en_words", [])

    text_lower = event.text.lower()
    for phrase in zh_phrases:
        if phrase in event.text:
            return event.text[:200]
    for word in en_words:
        if word in text_lower:
            return event.text[:200]

    return None


# ---------------------------------------------------------------------------
# Task 4.1 – evidence extraction
# ---------------------------------------------------------------------------

def extract_evidence(
    events: list[NormalizedEvent],
    repo_root: str | None = None,
    rules: dict[str, Any] | None = None,
) -> EvidenceBundle:
    """Aggregate evidence from a list of *NormalizedEvent* objects.

    Parameters
    ----------
    events:
        Ordered list of normalised events belonging to one task segment.
    repo_root:
        Optional absolute path to the repository root; used to relativise file
        paths via :func:`normalize_path`.
    rules:
        Parsed content of ``task_segment_rules.json``; forwarded to
        :func:`detect_final_claim`.  When *None*, final-claim detection is
        skipped.

    Returns
    -------
    EvidenceBundle
        Populated bundle; duplicate paths within each list are deduplicated
        while preserving first-seen order.
    """
    bundle = EvidenceBundle()

    # Helper: append to a list only if not already present
    def _add(lst: list[str], value: str) -> None:
        if value not in lst:
            lst.append(value)

    def _norm_files(files: list[str]) -> list[str]:
        return [normalize_path(f, repo_root) for f in files]

    for event in events:
        etype = event.event_type
        tname = event.tool_name or ""

        # ------------------------------------------------------------------ #
        # Files read
        # ------------------------------------------------------------------ #
        if etype == "file_read" or tname in _READ_TOOLS:
            for f in _norm_files(event.files):
                _add(bundle.files_read, f)
            # Some events carry the path in text when files list is empty
            if not event.files and event.text:
                _add(bundle.files_read, normalize_path(event.text.strip(), repo_root))

        # ------------------------------------------------------------------ #
        # Files changed
        # ------------------------------------------------------------------ #
        elif etype == "file_edit" or tname in _EDIT_TOOLS:
            for f in _norm_files(event.files):
                _add(bundle.files_changed, f)
            if not event.files and event.text:
                _add(bundle.files_changed, normalize_path(event.text.strip(), repo_root))

        # ------------------------------------------------------------------ #
        # Commands
        # ------------------------------------------------------------------ #
        elif etype == "command" or tname == "Bash":
            cmd = event.command or event.text
            if cmd:
                _add(bundle.commands, cmd)
                # Identify test / build commands
                cmd_lower = cmd.lower()
                for pat in _TEST_PATTERNS:
                    if pat in cmd_lower:
                        _add(bundle.test_commands, cmd)
                        break

        # ------------------------------------------------------------------ #
        # Errors
        # ------------------------------------------------------------------ #
        if etype == "error":
            _add(bundle.errors, event.text)
        elif event.raw_ref:
            result_text = str(event.raw_ref.get("result", ""))
            for pat in _ERROR_PATTERNS:
                if pat in result_text:
                    _add(bundle.errors, result_text)
                    break
        # Also check event.text for error patterns when it's a tool_result
        if etype == "tool_result":
            for pat in _ERROR_PATTERNS:
                if pat in event.text:
                    _add(bundle.errors, event.text)
                    break

        # ------------------------------------------------------------------ #
        # Skills
        # ------------------------------------------------------------------ #
        if tname == "Skill":
            skill_name = (
                event.metadata.get("skill")
                or event.metadata.get("skill_name")
                or event.metadata.get("name")
            )
            if not skill_name and event.text:
                skill_name = event.text.strip()
            if skill_name:
                _add(bundle.skills, str(skill_name))

        # ------------------------------------------------------------------ #
        # Subagent dispatch events
        # ------------------------------------------------------------------ #
        if event.source == "subagent" and etype == "user_message":
            _add(bundle.subagent_ids, event.agent_id)

        # ------------------------------------------------------------------ #
        # Final claims
        # ------------------------------------------------------------------ #
        if etype == "final_claim":
            _add(bundle.final_claims, event.text[:200])
        elif rules is not None:
            claim = detect_final_claim(event, rules)
            if claim:
                _add(bundle.final_claims, claim)

    # Compute file weights from accumulated files_read / files_changed
    from .overlap import compute_file_weights
    bundle.file_weights = compute_file_weights(
        files_read=bundle.files_read,
        files_changed=bundle.files_changed,
        rules=rules,
    )
    return bundle
