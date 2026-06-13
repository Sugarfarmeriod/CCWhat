"""Task Dataset v1 core APIs."""

from .builder import (
    DatasetBuildError,
    build_dataset_bundle,
    build_dataset_bundle_from_segments,
)
from .change_evidence import extract_change_evidence
from .models import (
    CHANGE_CONFIDENCES,
    CHANGE_KINDS,
    DATASET_SCHEMA_VERSION,
    DatasetBundle,
    DatasetChangeEvidence,
    DatasetItemRow,
    DatasetManifest,
    DatasetPatchEvidence,
    DatasetScoreRow,
    DatasetTrace,
    PATCH_CONFIDENCES,
    PATCH_FORMATS,
    ValidationIssue,
    ValidationResult,
)
from .validator import validate_dataset, validate_dataset_path

__all__ = [
    "DATASET_SCHEMA_VERSION",
    "CHANGE_CONFIDENCES",
    "CHANGE_KINDS",
    "DatasetBuildError",
    "DatasetBundle",
    "DatasetChangeEvidence",
    "DatasetItemRow",
    "DatasetManifest",
    "DatasetPatchEvidence",
    "DatasetScoreRow",
    "DatasetTrace",
    "PATCH_CONFIDENCES",
    "PATCH_FORMATS",
    "ValidationIssue",
    "ValidationResult",
    "build_dataset_bundle",
    "build_dataset_bundle_from_segments",
    "extract_change_evidence",
    "validate_dataset",
    "validate_dataset_path",
]
