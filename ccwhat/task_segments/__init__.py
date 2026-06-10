"""Rule-based task segmentation for AI coding agent sessions."""

from ccwhat.task_segments.segmenter import segment_session
from ccwhat.task_segments.models import (
    TaskSegment,
    TaskSegmentationResult,
    NormalizedEvent,
    EvidenceBundle,
    BoundaryDecision,
)

__all__ = [
    "segment_session",
    "TaskSegment",
    "TaskSegmentationResult",
    "NormalizedEvent",
    "EvidenceBundle",
    "BoundaryDecision",
]
