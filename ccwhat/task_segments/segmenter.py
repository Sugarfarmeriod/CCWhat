"""Task segmentation algorithm — rule-based, no LLM."""

from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import detect_final_claim, extract_evidence
from .models import (
    BoundaryDecision,
    EvidenceBundle,
    IntentResult,
    NormalizedEvent,
    TaskSegment,
    TaskSegmentationResult,
)
from .bm25 import BM25
from .overlap import compute_file_weights, compute_overlap
from .rules import classify_intent, extract_todos, load_rules

_EDIT_TOOLS = frozenset({"Edit", "Write", "Patch", "MultiEdit", "str_replace_editor"})
_READ_TOOLS = frozenset({"Read", "Grep", "Glob", "Find"})

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOOKAHEAD_EVENTS = 30
_LOOKAHEAD_TURNS = 3
_MERGE_OVERLAP_THRESHOLD = 0.75   # merge adjacent segments if overlap > this
_AMBIGUOUS_FLIP_THRESHOLD = 3     # >=3 low-overlap topic flips → ambiguous
_TODO_SPLIT_MIN = 2               # min todos in first message to attempt splitting


def _short_title(text: str, max_chars: int = 32) -> str:
    """Extract a short title from a user message, stripping todo/list markers."""
    import re as _re
    clean = text.strip()
    # Strip "- [ ]", "- [x]", "* [ ]", numbered list prefixes
    clean = _re.sub(r"^[-*\d.\s]*\[[x ]\]\s*", "", clean)
    clean = _re.sub(r"^[-*\d.\s]+", "", clean).strip()
    line = clean.split("\n")[0].strip()
    return line[:max_chars] + ("…" if len(line) > max_chars else "")


# ---------------------------------------------------------------------------
# 6.1  Boundary candidate detection
# ---------------------------------------------------------------------------

@dataclass
class _Candidate:
    event_index: int
    event_id: str
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    intent: IntentResult | None = None
    final_claim: str | None = None
    user_todos: list[str] = field(default_factory=list)


def _candidate_from_user_message(
    idx: int,
    event: NormalizedEvent,
    rules: dict,
    prev_had_final_claim: bool,
) -> _Candidate:
    intent = classify_intent(event.text, rules)
    user_todos, _, _ = extract_todos(event.text)
    c = _Candidate(event_index=idx, event_id=event.event_id, intent=intent,
                   user_todos=user_todos)

    if intent.is_veto:
        c.reasons.append(f"veto:continuation:-{intent.continuation_score:.1f}")
        return c

    score = 0.0
    if intent.new_task_score > 0:
        score += intent.new_task_score
        c.reasons.append(f"user_new_task:{intent.task_type}:+{intent.new_task_score:.1f}")
    if user_todos:
        # Base todo score; will be boosted by BM25 evidence match in _score_boundary
        score += 1.0
        c.reasons.append(f"user_todos:{len(user_todos)}:+1.0")
    if prev_had_final_claim:
        score += 1.0
        c.reasons.append("prev_final_claim:+1.0")
    c.score = score
    return c


# ---------------------------------------------------------------------------
# 6.2  Lookahead window
# ---------------------------------------------------------------------------

def _lookahead_evidence(
    events: list[NormalizedEvent],
    start_idx: int,
    rules: dict,
) -> EvidenceBundle:
    """Build evidence bundle from the next N events after start_idx."""
    window = events[start_idx : start_idx + _LOOKAHEAD_EVENTS]
    return extract_evidence(window, rules=rules)


# ---------------------------------------------------------------------------
# 6.3  Boundary scoring
# ---------------------------------------------------------------------------

def _score_boundary(
    candidate: _Candidate,
    window_evidence: EvidenceBundle,
    current_weights: dict[str, float],
    rules: dict,
) -> BoundaryDecision:
    score = candidate.score
    reasons = list(candidate.reasons)

    if candidate.intent and candidate.intent.is_veto:
        return BoundaryDecision(
            event_id=candidate.event_id,
            score=0.0,
            should_split=False,
            reasons=reasons,
        )

    # Positive: edit/test evidence in the lookahead window
    edit_weight = sum(window_evidence.file_weights.get(f, 0) for f in window_evidence.files_changed)
    if edit_weight >= 3.0:
        score += 1.5
        reasons.append(f"window_edit_weight:{edit_weight:.1f}:+1.5")
    if window_evidence.test_commands:
        score += 1.0
        reasons.append(f"window_test_cmds:{len(window_evidence.test_commands)}:+1.0")

    # Suppression: only reads / no edits
    if window_evidence.files_changed == [] and window_evidence.files_read:
        score -= 1.0
        reasons.append("window_read_only:-1.0")

    # BM25: boost score when user todos have relevant evidence in the window
    if candidate.user_todos and (
        window_evidence.files_changed
        or window_evidence.commands
        or window_evidence.errors
    ):
        corpus = (
            window_evidence.files_changed
            + window_evidence.commands[:5]
            + window_evidence.errors[:3]
        )
        if corpus:
            try:
                bm25 = BM25(corpus)
                query = " ".join(candidate.user_todos[:3])
                top = bm25.rank(query)
                if top and top[0][1] > 0:
                    boost = min(top[0][1] * 0.5, 1.5)
                    score += boost
                    reasons.append(f"bm25_todo_evidence:{boost:.2f}:+{boost:.2f}")
            except Exception:
                pass

    # File overlap suppression
    if current_weights and window_evidence.file_weights:
        file_ov, mod_ov = compute_overlap(current_weights, window_evidence.file_weights)
        thresholds = rules.get("thresholds", {})
        low_file = thresholds.get("file_overlap_low", 0.25)
        low_mod = thresholds.get("module_overlap_low", 0.5)
        if file_ov < low_file and mod_ov < low_mod and edit_weight >= 3.0:
            score += 2.0
            reasons.append(f"file_overlap_low:{file_ov:.2f}:+2.0")
        elif file_ov > 0.5:
            score -= 1.5
            reasons.append(f"file_overlap_high:{file_ov:.2f}:-1.5")

    threshold = rules.get("thresholds", {}).get("split_score", 3.0)
    return BoundaryDecision(
        event_id=candidate.event_id,
        score=score,
        should_split=score >= threshold,
        reasons=reasons,
    )


# ---------------------------------------------------------------------------
# 6.4  Task Segment state machine
# ---------------------------------------------------------------------------

class _Segmenter:
    def __init__(self, rules: dict) -> None:
        self.rules = rules
        self.segments: list[TaskSegment] = []
        self._current: TaskSegment | None = None
        self._current_weights: dict[str, float] = {}
        self._seg_counter = 0
        self._topic_flip_count = 0
        # For todo-based retroactive splitting (P1-2)
        self._first_msg_todos: list[str] = []
        self._first_msg_event_id: str = ""

    # ── helpers ────────────────────────────────────────────────────────────

    def _new_segment(
        self,
        start_event_id: str,
        title: str = "",
        task_type: str = "unknown",
        boundary_reasons: list[str] | None = None,
    ) -> TaskSegment:
        self._seg_counter += 1
        seg = TaskSegment(
            task_id=f"task-{self._seg_counter:03d}",
            title=title or f"任务 {self._seg_counter}",
            task_type=task_type,
            status="unevaluated",
            start_event_id=start_event_id,
            end_event_id=None,
            boundary_reasons=boundary_reasons or [],
        )
        return seg

    def _close_current(self, end_event_id: str) -> None:
        if self._current:
            self._current.end_event_id = end_event_id
            self._current.is_open = False
            self.segments.append(self._current)
            self._current = None

    def _open_new(
        self,
        event: NormalizedEvent,
        reasons: list[str],
        task_type: str,
        title: str = "",
    ) -> None:
        self._current = self._new_segment(
            start_event_id=event.event_id,
            title=title,
            task_type=task_type,
            boundary_reasons=reasons,
        )
        self._current_weights = {}

    def _reopen_last(self, event: NormalizedEvent) -> None:
        """Reopen the most recently closed segment on failure feedback."""
        if not self.segments:
            return
        last = self.segments[-1]
        if not last.is_open:
            last.is_open = True
            last.end_event_id = None
            self.segments.pop()
            self._current = last
            self._current.boundary_reasons.append(
                f"reopen:failure_feedback:{event.event_id}"
            )

    def _is_failure_feedback(self, intent: IntentResult) -> bool:
        """True if the message looks like follow-up on a failed task."""
        return intent.is_veto and intent.continuation_score >= 2.0

    def _should_reopen(
        self,
        intent: IntentResult,
        window_evidence: EvidenceBundle,
    ) -> bool:
        if not self._is_failure_feedback(intent):
            return False
        if not self.segments:
            return False
        last = self.segments[-1]
        if last.final_claim is None:
            return False
        # Overlap with last segment's files
        if last.file_weights and window_evidence.file_weights:
            ov, _ = compute_overlap(last.file_weights, window_evidence.file_weights)
            return ov > 0.3
        return True

    # ── accumulate evidence into current segment ───────────────────────────

    def _accumulate(self, event: NormalizedEvent, rules: dict) -> None:
        if self._current is None:
            return
        fc = detect_final_claim(event, rules)
        if fc:
            self._current.final_claim = fc
        # Accumulate file weights — use tool_name (events are classified as
        # tool_call with tool_name="Edit"/"Read", not "file_edit"/"file_read")
        if event.files and event.event_type == "tool_call":
            is_edit = event.tool_name in _EDIT_TOOLS
            is_read = event.tool_name in _READ_TOOLS
            new_w = compute_file_weights(
                files_read=event.files if is_read else [],
                files_changed=event.files if is_edit else [],
                rules=rules,
            )
            for k, v in new_w.items():
                self._current_weights[k] = min(
                    self._current_weights.get(k, 0) + v, 6.0
                )
                self._current.file_weights[k] = self._current_weights[k]

    # ── main entry ─────────────────────────────────────────────────────────

    def run(
        self,
        events: list[NormalizedEvent],
        session_id: str,
    ) -> TaskSegmentationResult:
        debug_boundaries: list[BoundaryDecision] = []

        # Initialise first segment
        first_id = events[0].event_id if events else "start"
        self._current = self._new_segment(first_id, title="任务 1")

        user_msg_count = 0  # skip splitting on the very first user message

        for idx, event in enumerate(events):
            self._accumulate(event, self.rules)

            if event.event_type != "user_message":
                continue

            # Subagent messages are evidence for the parent task, never boundaries
            if event.source != "main":
                continue

            # Live check: current task already has a final claim → closing signal
            prev_had_final_claim = bool(self._current and self._current.final_claim)

            user_msg_count += 1
            if user_msg_count == 1:
                # Back-fill first task's type/title from the first user message
                first_intent = classify_intent(event.text, self.rules)
                if first_intent.task_type != "unknown":
                    self._current.task_type = first_intent.task_type
                if event.text.strip():
                    self._current.title = _short_title(event.text)
                # Store todos from first message for later retroactive splitting
                # Include both user and assistant todos — they all come from the
                # user's message, the distinction is only about verb strength
                first_u, first_a, _ = extract_todos(event.text)
                all_first_todos = first_u + first_a
                if len(all_first_todos) >= 2:
                    self._first_msg_todos = all_first_todos
                    self._first_msg_event_id = event.event_id
                # First message never creates a boundary (nothing before it)
                continue

            # Build candidate
            candidate = _candidate_from_user_message(
                idx, event, self.rules, prev_had_final_claim
            )
            window_ev = _lookahead_evidence(events, idx + 1, self.rules)

            # Check reopen first
            if candidate.intent and self._should_reopen(candidate.intent, window_ev):
                self._reopen_last(event)
                continue

            decision = _score_boundary(
                candidate, window_ev, self._current_weights, self.rules
            )
            debug_boundaries.append(decision)

            if decision.should_split:
                self._close_current(events[idx - 1].event_id if idx > 0 else event.event_id)
                self._open_new(
                    event,
                    reasons=decision.reasons,
                    task_type=candidate.intent.task_type if candidate.intent else "unknown",
                )
                # Count topic flips for ambiguity detection
                if any("file_overlap_low" in r for r in decision.reasons):
                    self._topic_flip_count += 1

        # Close final segment
        if events:
            self._close_current(events[-1].event_id)
        elif self._current:
            self._close_current("end")
            self.segments.append(self._current)

        # Post-process: merge highly-overlapping adjacent, mark ambiguous
        segments = _merge_adjacent(self.segments)
        is_ambiguous = self._topic_flip_count >= _AMBIGUOUS_FLIP_THRESHOLD
        if is_ambiguous:
            for seg in segments:
                seg.is_ambiguous = True

        # Retroactive todo split: if only 1 segment and first message had ≥2 todos
        if (
            len(segments) == 1
            and len(self._first_msg_todos) >= _TODO_SPLIT_MIN
        ):
            todo_segs = _retroactive_todo_split(
                segments[0], events, self._first_msg_todos,
                self._first_msg_event_id, self._seg_counter, self.rules
            )
            if todo_segs and len(todo_segs) > 1:
                segments = todo_segs

        # Extract final evidence per segment
        _attach_evidence(segments, events, self.rules)

        # Renumber task IDs to be consecutive from task-001
        for i, seg in enumerate(segments, 1):
            seg.task_id = f"task-{i:03d}"
            seg.title = f"任务 {i}"

        # Build summary
        summary = {
            "sessionId": session_id,
            "taskCount": len(segments),
            "ambiguous": is_ambiguous,
            "topicFlips": self._topic_flip_count,
        }

        return TaskSegmentationResult(
            session_id=session_id,
            tasks=segments,
            summary=summary,
            is_ambiguous=is_ambiguous,
            debug_boundaries=debug_boundaries,
        )


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

def _retroactive_todo_split(
    single_seg: TaskSegment,
    all_events: list[NormalizedEvent],
    todos: list[str],
    first_event_id: str,
    seg_counter_base: int,
    rules: dict,
) -> list[TaskSegment]:
    """Split a single segment into per-todo segments.

    Strategy: sequential assignment.  Claude almost always processes user todos
    in order, so we split the main-thread tool events into N consecutive chunks
    (one per todo) using edit-cluster detection.  BM25 is used as a tiebreaker
    when a cluster boundary falls mid-file-group.
    """
    import re as _re

    # Build event_id -> index map for correct start/end computation
    event_id_to_idx: dict[str, int] = {e.event_id: i for i, e in enumerate(all_events)}

    # Only main tool_call events carry edit evidence worth splitting on
    tool_events = [
        e for e in all_events
        if e.event_type == "tool_call" and e.source == "main"
        and e.tool_name in _EDIT_TOOLS
    ]

    if len(tool_events) < len(todos):
        return []  # not enough distinct edit events to split

    n = len(todos)
    total = len(tool_events)

    # Attempt BM25-assisted boundary detection:
    # Build corpus using file stems (bridge the English-file / Chinese-todo gap)
    import os as _os
    corpus_texts = []
    for e in tool_events:
        stems = []
        for f in e.files:
            base = _os.path.basename(f)
            stem = _os.path.splitext(base)[0]
            stems.append(stem)
        corpus_texts.append(" ".join(stems) if stems else e.text or "")

    # Continuous uniform distribution: todo 0 gets events [0..k-1], todo 1 gets [k..2k-1], …
    # This keeps related edits together instead of scattering them round-robin.
    assignments: list[int] = [min(i * n // total, n - 1) for i in range(total)]

    # BM25 override: only accepted when every event has a positive match AND
    # the resulting assignment is monotonically non-decreasing (no back-tracking
    # from a later todo to an earlier one).  This prevents weak/zero BM25 scores
    # from scrambling files across boundaries.
    if any(t.strip() for t in corpus_texts):
        try:
            bm25 = BM25(corpus_texts)
            bm25_assign: list[int] = []
            all_positive = True
            for di in range(total):
                best_ti, best_s = 0, -1.0
                for ti, todo in enumerate(todos):
                    s = bm25.score(todo, di)
                    if s > best_s:
                        best_s = s
                        best_ti = ti
                if best_s <= 0:
                    all_positive = False
                bm25_assign.append(best_ti)
            # Accept only when BM25 produced meaningful differentiation AND is monotone
            is_monotone = all(
                bm25_assign[i] <= bm25_assign[i + 1]
                for i in range(len(bm25_assign) - 1)
            )
            if all_positive and is_monotone and len(set(bm25_assign)) > 1:
                assignments = bm25_assign
        except Exception:
            pass

    if len(set(assignments)) <= 1:
        return []

    # Clean a todo string: strip "- [ ]", "- [x]", "* [ ]", "* [x]", "- ", "* " prefixes
    def _clean_todo(raw: str) -> str:
        cleaned = _re.sub(r"^[-*\s]*\[[x ]\]\s*", "", raw.strip())
        cleaned = _re.sub(r"^[-*\s]+", "", cleaned).strip()
        return cleaned

    # Determine the first-task start event id: use first_event_id (first user message)
    # For subsequent tasks: start at their first edit tool_call event
    # For end: the event just before the next task's start tool event, or last event

    # Group tool_events by todo assignment to find per-todo first tool events
    # We need to know the index of the first tool_event for each todo group
    # Build the segment boundaries first (list of (start_tool_event_idx_in_tool_events, todo_idx))
    group_starts: list[tuple[int, int]] = []  # (index in tool_events, todo_idx)
    current_todo_idx = assignments[0]
    group_starts.append((0, current_todo_idx))
    for i, todo_idx in enumerate(assignments):
        if todo_idx != current_todo_idx:
            group_starts.append((i, todo_idx))
            current_todo_idx = todo_idx

    # Build segments
    segments: list[TaskSegment] = []
    counter = seg_counter_base

    for gi, (tool_start_i, todo_idx) in enumerate(group_starts):
        # Determine end tool event index for this group
        if gi + 1 < len(group_starts):
            next_tool_start_i = group_starts[gi + 1][0]
            end_tool_event = tool_events[next_tool_start_i - 1]
        else:
            end_tool_event = tool_events[-1]

        # Compute start_event_id:
        # - first group: use first_event_id (the first user message event)
        # - subsequent groups: use the first edit tool_call event of this group
        if gi == 0:
            seg_start_event_id = first_event_id
        else:
            seg_start_event_id = tool_events[tool_start_i].event_id

        # Compute end_event_id:
        # - for all but the last group: the event just before the next group's
        #   first tool_call event in all_events
        # - for the last group: single_seg.end_event_id (last event of session)
        if gi + 1 < len(group_starts):
            next_tool_event_id = tool_events[group_starts[gi + 1][0]].event_id
            next_tool_global_idx = event_id_to_idx.get(next_tool_event_id)
            if next_tool_global_idx is not None and next_tool_global_idx > 0:
                seg_end_event_id = all_events[next_tool_global_idx - 1].event_id
            else:
                seg_end_event_id = end_tool_event.event_id
        else:
            seg_end_event_id = single_seg.end_event_id or all_events[-1].event_id

        # Clean todo text and classify type
        todo_clean = _clean_todo(todos[todo_idx])
        intent = classify_intent(todo_clean, rules)
        task_type = intent.task_type if intent.task_type != "unknown" else "unknown"

        counter += 1
        seg = TaskSegment(
            task_id=f"task-{counter:03d}",
            title=_short_title(todos[todo_idx]),
            task_type=task_type,
            status="unevaluated",
            start_event_id=seg_start_event_id,
            end_event_id=seg_end_event_id,
            boundary_reasons=[f"todo_split:todo_{todo_idx}"],
        )
        # Set todos_user evidence from the cleaned todo text
        seg.evidence.todos_user = [todo_clean]
        segments.append(seg)

    return segments


def _merge_adjacent(segments: list[TaskSegment]) -> list[TaskSegment]:
    if len(segments) <= 1:
        return segments
    merged: list[TaskSegment] = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        if i + 1 < len(segments):
            nxt = segments[i + 1]
            if seg.file_weights and nxt.file_weights:
                ov, _ = compute_overlap(seg.file_weights, nxt.file_weights)
                if ov >= _MERGE_OVERLAP_THRESHOLD:
                    seg.end_event_id = nxt.end_event_id
                    seg.boundary_reasons.append(
                        f"merged_with:{nxt.task_id}:overlap:{ov:.2f}"
                    )
                    merged.append(seg)
                    i += 2
                    continue
        merged.append(seg)
        i += 1
    return merged


def _attach_evidence(
    segments: list[TaskSegment],
    events: list[NormalizedEvent],
    rules: dict,
) -> None:
    """Attach accumulated evidence to each segment by slicing events."""
    event_by_id = {e.event_id: i for i, e in enumerate(events)}
    for seg in segments:
        # Preserve any todos_user set before evidence extraction (e.g. by todo split)
        pre_todos_user = list(seg.evidence.todos_user)
        start_i = event_by_id.get(seg.start_event_id, 0)
        end_i = event_by_id.get(seg.end_event_id, len(events) - 1) if seg.end_event_id else len(events) - 1
        seg_events = events[start_i : end_i + 1]
        seg.evidence = extract_evidence(seg_events, rules=rules)
        # Restore pre-set todos_user (takes priority over auto-extracted)
        if pre_todos_user:
            seg.evidence.todos_user = pre_todos_user
        # Set final_claim on the segment from evidence if not already set
        if seg.final_claim is None and seg.evidence.final_claims:
            seg.final_claim = seg.evidence.final_claims[0]


# ---------------------------------------------------------------------------
# 6.5  Public entry point
# ---------------------------------------------------------------------------

def segment_session(session: dict) -> TaskSegmentationResult:
    """Segment a session dict into TaskSegments using pure rules.

    The session dict may come from ClaudeAdapter (with 'main'/'subagents' lists)
    or contain 'sessionId', 'projectDir', etc.
    """
    from .events import normalize_session_events

    session_id = str(session.get("sessionId") or "unknown")
    rules = load_rules()
    events = normalize_session_events(session)

    if not events:
        return TaskSegmentationResult(
            session_id=session_id,
            tasks=[],
            summary={"sessionId": session_id, "taskCount": 0, "ambiguous": False},
        )

    return _Segmenter(rules).run(events, session_id)
