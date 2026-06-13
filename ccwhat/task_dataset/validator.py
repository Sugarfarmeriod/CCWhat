"""Validator for Task Dataset v1 directories and tar archives."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from typing import Any

from .models import (
    DATASET_JSONL_PATH,
    DATASET_SCHEMA_VERSION,
    MANIFEST_PATH,
    SCORES_JSONL_PATH,
    TRACES_DIR,
    ValidationIssue,
    ValidationResult,
)


def validate_dataset_path(path: str | Path) -> ValidationResult:
    """Validate a Dataset v1 directory or existing tar/tar.gz archive."""
    source = Path(path)
    if source.is_dir():
        return validate_dataset(*_read_directory(source))
    if source.is_file() and tarfile.is_tarfile(source):
        return validate_dataset(*_read_tar(source))
    return ValidationResult(
        ok=False,
        errors=[ValidationIssue(str(source), "Path is not a Dataset directory or tar archive.")],
    )


def validate_dataset(
    files: dict[str, bytes],
    directories: set[str] | None = None,
) -> ValidationResult:
    """Validate normalized Dataset files loaded from any storage backend."""
    dirs = directories or set()
    errors: list[ValidationIssue] = []

    _check_required_paths(files, dirs, errors)

    manifest = _parse_json(files, MANIFEST_PATH, errors)
    dataset_rows = _parse_jsonl(files, DATASET_JSONL_PATH, errors)
    score_rows = _parse_jsonl(files, SCORES_JSONL_PATH, errors)

    trace_paths = sorted(
        path for path in files
        if path.startswith(f"{TRACES_DIR}/") and path.endswith(".json")
    )
    traces: dict[str, Any] = {}
    for trace_path in trace_paths:
        traces[trace_path] = _parse_json(files, trace_path, errors)

    counts = {
        "dataset_items": len(dataset_rows),
        "traces": len(trace_paths),
        "scores": len(score_rows),
    }

    if isinstance(manifest, dict):
        _validate_manifest(manifest, counts, errors)

    for row in dataset_rows:
        _validate_dataset_row_trace(row, traces, errors)

    return ValidationResult(
        ok=not errors,
        errors=errors,
        counts=counts,
    )


def _read_directory(root: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    for child in root.rglob("*"):
        rel_path = child.relative_to(root).as_posix()
        if child.is_dir():
            directories.add(rel_path.rstrip("/") + "/")
        elif child.is_file():
            files[rel_path] = child.read_bytes()
    return files, directories


def _read_tar(path: Path) -> tuple[dict[str, bytes], set[str]]:
    raw_files: dict[str, bytes] = {}
    raw_dirs: set[str] = set()
    with tarfile.open(path, "r:*") as tar:
        for member in tar.getmembers():
            name = _clean_member_name(member.name)
            if not name:
                continue
            if member.isdir():
                raw_dirs.add(name.rstrip("/") + "/")
            elif member.isfile():
                extracted = tar.extractfile(member)
                if extracted is not None:
                    raw_files[name] = extracted.read()
    return _strip_common_tar_root(raw_files, raw_dirs)


def _clean_member_name(name: str) -> str:
    return name.lstrip("./").rstrip("/")


def _strip_common_tar_root(
    files: dict[str, bytes],
    directories: set[str],
) -> tuple[dict[str, bytes], set[str]]:
    if MANIFEST_PATH in files:
        return files, directories
    required_names = {MANIFEST_PATH, DATASET_JSONL_PATH, SCORES_JSONL_PATH}
    roots = {path.split("/", 1)[0] for path in files if "/" in path}
    for root in sorted(roots):
        prefix = f"{root}/"
        stripped_files = {
            path.removeprefix(prefix): data
            for path, data in files.items()
            if path.startswith(prefix)
        }
        if required_names.issubset(stripped_files):
            stripped_dirs = {
                directory.removeprefix(prefix)
                for directory in directories
                if directory.startswith(prefix)
            }
            return stripped_files, stripped_dirs
    return files, directories


def _check_required_paths(
    files: dict[str, bytes],
    directories: set[str],
    errors: list[ValidationIssue],
) -> None:
    for required in (MANIFEST_PATH, DATASET_JSONL_PATH, SCORES_JSONL_PATH):
        if required not in files:
            errors.append(ValidationIssue(required, f"Missing required path: {required}"))
    has_traces = any(path.startswith(f"{TRACES_DIR}/") for path in files) or f"{TRACES_DIR}/" in directories
    if not has_traces:
        errors.append(ValidationIssue(f"{TRACES_DIR}/", "Missing required path: traces/"))


def _parse_json(
    files: dict[str, bytes],
    path: str,
    errors: list[ValidationIssue],
) -> Any:
    if path not in files:
        return None
    try:
        return json.loads(files[path].decode("utf-8"))
    except UnicodeDecodeError as exc:
        errors.append(ValidationIssue(path, f"File is not valid UTF-8: {exc}"))
    except json.JSONDecodeError as exc:
        errors.append(ValidationIssue(path, f"Invalid JSON: {exc.msg}", line=exc.lineno))
    return None


def _parse_jsonl(
    files: dict[str, bytes],
    path: str,
    errors: list[ValidationIssue],
) -> list[Any]:
    if path not in files:
        return []
    try:
        text = files[path].decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(ValidationIssue(path, f"File is not valid UTF-8: {exc}"))
        return []

    rows: list[Any] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(
                ValidationIssue(path, f"Invalid JSONL: {exc.msg}", line=line_number)
            )
    return rows


def _validate_manifest(
    manifest: dict[str, Any],
    counts: dict[str, int],
    errors: list[ValidationIssue],
) -> None:
    if manifest.get("schema_version") != DATASET_SCHEMA_VERSION:
        errors.append(
            ValidationIssue(
                MANIFEST_PATH,
                f"manifest.schema_version must be {DATASET_SCHEMA_VERSION!r}.",
                field="schema_version",
            )
        )
    manifest_counts = manifest.get("counts")
    if not isinstance(manifest_counts, dict):
        errors.append(
            ValidationIssue(MANIFEST_PATH, "manifest.counts must be an object.", field="counts")
        )
        return
    for key, actual in counts.items():
        expected = manifest_counts.get(key)
        if expected != actual:
            errors.append(
                ValidationIssue(
                    MANIFEST_PATH,
                    f"Count mismatch for counts.{key}: manifest has {expected!r}, actual is {actual}.",
                    field=f"counts.{key}",
                )
            )


def _validate_dataset_row_trace(
    row: Any,
    traces: dict[str, Any],
    errors: list[ValidationIssue],
) -> None:
    if not isinstance(row, dict):
        errors.append(ValidationIssue(DATASET_JSONL_PATH, "Dataset row must be an object."))
        return
    item_id = row.get("id")
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        errors.append(
            ValidationIssue(
                DATASET_JSONL_PATH,
                f"Dataset item {item_id!r} metadata must be an object.",
                field="metadata",
            )
        )
        return
    trace_path = metadata.get("trace_path")
    if not isinstance(trace_path, str) or not trace_path:
        errors.append(
            ValidationIssue(
                DATASET_JSONL_PATH,
                f"Dataset item {item_id!r} metadata.trace_path is required.",
                field="metadata.trace_path",
            )
        )
        return
    trace = traces.get(trace_path)
    if trace is None:
        errors.append(
            ValidationIssue(
                trace_path,
                f"Dataset item {item_id!r} references missing trace path {trace_path!r}.",
                field="metadata.trace_path",
            )
        )
        return
    if not isinstance(trace, dict):
        errors.append(ValidationIssue(trace_path, "Trace JSON must be an object."))
        return
    if trace.get("task_id") != item_id:
        errors.append(
            ValidationIssue(
                trace_path,
                f"Dataset item id {item_id!r} does not match trace.task_id {trace.get('task_id')!r}.",
                field="task_id",
            )
        )
