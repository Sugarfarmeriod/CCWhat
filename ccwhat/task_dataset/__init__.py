"""Task Dataset v1 core APIs."""

from .builder import (
    DatasetBuildError,
    build_dataset_bundle,
    build_dataset_bundle_from_segments,
)
from .models import (
    DATASET_SCHEMA_VERSION,
    DatasetBundle,
    DatasetItemRow,
    DatasetManifest,
    DatasetScoreRow,
    DatasetTrace,
    ValidationIssue,
    ValidationResult,
)
from .validator import validate_dataset, validate_dataset_path

__all__ = [
    "DATASET_SCHEMA_VERSION",
    "DatasetBuildError",
    "DatasetBundle",
    "DatasetItemRow",
    "DatasetManifest",
    "DatasetScoreRow",
    "DatasetTrace",
    "ValidationIssue",
    "ValidationResult",
    "build_dataset_bundle",
    "build_dataset_bundle_from_segments",
    "validate_dataset",
    "validate_dataset_path",
]
