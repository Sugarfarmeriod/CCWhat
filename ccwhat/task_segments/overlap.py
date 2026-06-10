"""File-evidence overlap utilities for task segmentation."""

from __future__ import annotations

import os


# ---------------------------------------------------------------------------
# Task 5.3 – compute_file_weights
# ---------------------------------------------------------------------------

_DEFAULT_RULES: dict = {
    "edit_ops": ["Edit", "Write", "Patch", "MultiEdit", "str_replace_editor"],
    "edit_weight": 3.0,
    "read_ops": ["Read", "Grep", "Glob", "Find"],
    "read_weight": 1.0,
    "test_weight": 2.0,
    "downgrade_patterns": {
        "readme": 0.3,
        "lock": 0.3,
        "pyproject": 0.5,
        "package.json": 0.5,
        "setup.cfg": 0.5,
        "docs/": 0.3,
        "doc/": 0.3,
        ".gitignore": 0.2,
        "changelog": 0.2,
        "license": 0.1,
    },
}

_MAX_WEIGHT = 6.0


def _downgrade_factor(path: str, downgrade_patterns: dict[str, float]) -> float:
    """Return the minimum downgrade multiplier that matches *path*, or 1.0."""
    path_lower = path.lower()
    basename = os.path.basename(path_lower)
    factor = 1.0
    for pattern, mult in downgrade_patterns.items():
        if pattern.endswith("/"):
            # directory pattern – check if it appears anywhere in the path
            if pattern in path_lower or ("/" + pattern.rstrip("/") + "/") in path_lower:
                factor = min(factor, mult)
        else:
            if pattern in basename or pattern in path_lower:
                factor = min(factor, mult)
    return factor


def compute_file_weights(
    files_read: list[str],
    files_changed: list[str],
    rules: dict | None = None,
) -> dict[str, float]:
    """Compute per-file evidence weights.

    Parameters
    ----------
    files_read:
        Files accessed via read-like operations (weight 1.0 each occurrence).
    files_changed:
        Files accessed via edit/write-like operations (weight 3.0 each occurrence).
    rules:
        Optional rules dict (expects a ``file_weights`` sub-key matching the
        structure in ``task_segment_rules.json``).  Falls back to
        ``_DEFAULT_RULES`` when *None* or when the sub-key is missing.

    Returns
    -------
    dict[str, float]
        Mapping of file path → accumulated weight, capped at ``_MAX_WEIGHT``.
    """
    fw: dict = _DEFAULT_RULES
    if rules is not None:
        fw = rules.get("file_weights", _DEFAULT_RULES)

    edit_weight: float = float(fw.get("edit_weight", 3.0))
    read_weight: float = float(fw.get("read_weight", 1.0))
    downgrade_patterns: dict[str, float] = fw.get("downgrade_patterns", {})

    weights: dict[str, float] = {}

    def _add(path: str, base_weight: float) -> None:
        factor = _downgrade_factor(path, downgrade_patterns)
        delta = base_weight * factor
        current = weights.get(path, 0.0)
        weights[path] = min(current + delta, _MAX_WEIGHT)

    for path in files_read:
        _add(path, read_weight)

    for path in files_changed:
        _add(path, edit_weight)

    return weights


# ---------------------------------------------------------------------------
# Task 5.4 – weighted_jaccard, module_weights, compute_overlap
# ---------------------------------------------------------------------------


def weighted_jaccard(a: dict[str, float], b: dict[str, float]) -> float:
    """Weighted Jaccard similarity between two weight dicts.

    intersection = sum(min(a[k], b[k]) for k in common keys)
    union        = sum(max(a[k], b[k]) for k in all keys)
    """
    all_keys = set(a) | set(b)
    if not all_keys:
        return 0.0
    intersection = sum(min(a.get(k, 0.0), b.get(k, 0.0)) for k in all_keys)
    union = sum(max(a.get(k, 0.0), b.get(k, 0.0)) for k in all_keys)
    if union == 0.0:
        return 0.0
    return intersection / union


def module_weights(file_weights: dict[str, float], depth: int = 2) -> dict[str, float]:
    """Aggregate file weights by the first *depth* directory components.

    Parameters
    ----------
    file_weights:
        Per-file weight mapping.
    depth:
        Number of leading path segments to use as the module key.

    Returns
    -------
    dict[str, float]
        Mapping of module prefix → summed weight.
    """
    result: dict[str, float] = {}
    for path, weight in file_weights.items():
        # Normalise separators
        norm = path.replace("\\", "/")
        parts = [p for p in norm.split("/") if p]
        module = "/".join(parts[:depth]) if parts else path
        result[module] = result.get(module, 0.0) + weight
    return result


def compute_overlap(
    task_weights: dict[str, float],
    window_weights: dict[str, float],
) -> tuple[float, float]:
    """Compute file-level and module-level overlap between two weight dicts.

    Parameters
    ----------
    task_weights:
        File weights for the current task segment.
    window_weights:
        File weights for the comparison window (e.g. previous task).

    Returns
    -------
    tuple[float, float]
        ``(file_overlap, module_overlap)`` – both are weighted Jaccard scores
        in ``[0, 1]``.
    """
    file_overlap = weighted_jaccard(task_weights, window_weights)
    mod_a = module_weights(task_weights)
    mod_b = module_weights(window_weights)
    module_overlap = weighted_jaccard(mod_a, mod_b)
    return file_overlap, module_overlap
