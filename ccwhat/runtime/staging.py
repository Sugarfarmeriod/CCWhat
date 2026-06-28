"""Runtime task staging with incremental diff tracking."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from ccwhat.runtime.index import CCWhatIndex
from ccwhat.runtime.models import StepDiffBuffer
from ccwhat.runtime.registry import RunRegistry, RuntimeRun, utc_now
from ccwhat.runtime.trace_extractor import extract_task_trace


class RuntimeTaskError(RuntimeError):
    pass


class TaskStaging:
    def __init__(self, registry: RunRegistry) -> None:
        self.registry = registry
        self._index: CCWhatIndex | None = None
        self._diff_buffer: StepDiffBuffer | None = None
        self._current_task_dir: Path | None = None

    def start_task(self, run: RuntimeRun, title: str) -> dict[str, Any]:
        if run.active_task_id:
            raise RuntimeTaskError(f"task already recording: {run.active_task_id}")
        workspace = Path(run.workspace)
        self._ensure_git_workspace(workspace)
        task_id = self._next_task_id(run.run_id)
        task_dir = self._task_dir(run.run_id, task_id)
        task_dir.mkdir(parents=True, exist_ok=False)

        now = utc_now()
        task = {
            "schema": "ccwhat-runtime-task-v1",
            "task_id": task_id,
            "run_id": run.run_id,
            "title": self._task_title(task_id),
            "status": "recording",
            "started_at": now,
            "finished_at": None,
            "workspace": run.workspace,
            "git": {
                "before_commit": self._git_output(workspace, ["rev-parse", "HEAD"], allow_fail=True),
                "before_status": self._git_output(workspace, ["status", "--short"], allow_fail=True) or "",
                "after_commit": None,
                "after_status": None,
            },
            "instruction": title or None,
            "success_criteria": None,
            "expected_tests": [],
            "paths": {
                "repo_before": None,
                "repo_after": None,
                "diff": None,
                "control_events": None,
                "task_trace": None,
            },
            "evidence_availability": {
                "repo_before": False,
                "repo_after": False,
                "diff": False,
                "control_events": False,
                "task_trace": False,
            },
        }
        self._write_json(task_dir / "task.json", task)
        self.registry.set_active_task(run.run_id, task_id)

        # Initialize incremental diff tracking
        self._index = CCWhatIndex(workspace)
        self._index.init()
        self._diff_buffer = StepDiffBuffer()
        self._current_task_dir = task_dir

        return task

    def finish_task(self, run: RuntimeRun) -> dict[str, Any]:
        if not run.active_task_id:
            raise RuntimeTaskError("no active task to finish")
        workspace = Path(run.workspace)
        self._ensure_git_workspace(workspace)
        task_dir = self._task_dir(run.run_id, run.active_task_id)
        task = self._read_json(task_dir / "task.json")

        finished_at = utc_now()
        task["status"] = "finalized"
        task["finished_at"] = finished_at
        task["git"]["after_commit"] = self._git_output(workspace, ["rev-parse", "HEAD"], allow_fail=True)
        task["git"]["after_status"] = self._git_output(workspace, ["status", "--short"], allow_fail=True) or ""
        task["paths"]["repo_after"] = None

        # Write diff.patch if we have recorded steps
        if self._diff_buffer is not None and not self._diff_buffer.is_empty():
            patch_content = self._diff_buffer.format_patch()
            (task_dir / "diff.patch").write_text(patch_content, encoding="utf-8")
            task["paths"]["diff"] = "diff.patch"
            task["evidence_availability"]["diff"] = True
        else:
            task["paths"]["diff"] = None
            task["evidence_availability"]["diff"] = False

        task["evidence_availability"]["repo_after"] = False

        trace = extract_task_trace(
            workspace=run.workspace,
            started_at=task["started_at"],
            finished_at=finished_at,
            agent=run.agent,
        )
        trace["task_id"] = run.active_task_id
        trace["run_id"] = run.run_id
        trace["repo_state"]["base_commit"] = task["git"].get("before_commit")
        trace["repo_state"]["head_commit"] = task["git"].get("after_commit")
        self._write_json(task_dir / "task_trace.json", trace)
        task["paths"]["task_trace"] = "task_trace.json"
        task["evidence_availability"]["task_trace"] = True
        if trace.get("first_user_message"):
            task["instruction"] = trace["first_user_message"]
        if trace.get("test_commands"):
            task["expected_tests"] = trace["test_commands"]

        self._write_json(task_dir / "task.json", task)
        self.registry.set_active_task(run.run_id, None)

        # Clear internal state
        self._index = None
        self._diff_buffer = None
        self._current_task_dir = None

        return task

    def abort_task(self, run: RuntimeRun) -> dict[str, Any]:
        if not run.active_task_id:
            raise RuntimeTaskError("no active task to abort")
        task_dir = self._task_dir(run.run_id, run.active_task_id)
        task = self._read_json(task_dir / "task.json")
        task["status"] = "aborted"
        task["finished_at"] = utc_now()
        self._write_json(task_dir / "task.json", task)
        self.registry.set_active_task(run.run_id, None)

        # Clear internal state
        self._index = None
        self._diff_buffer = None
        self._current_task_dir = None

        return task

    def status(self, run: RuntimeRun) -> dict[str, Any]:
        return {
            "run_id": run.run_id,
            "status": "recording" if run.active_task_id else "idle",
            "active_task_id": run.active_task_id,
        }

    def record_step(self, tool_name: str, file_path: str) -> int:
        """Record a step diff for a file change.

        Args:
            tool_name: Name of the tool (e.g., "Write", "Edit")
            file_path: Path to the changed file

        Returns:
            The assigned step index

        Raises:
            RuntimeTaskError: If no active task or index not initialized
        """
        if self._index is None or self._diff_buffer is None:
            raise RuntimeTaskError("no active task for recording step")

        # Add file to isolated index
        self._index.add(file_path)

        # Generate diff from HEAD to current index
        diff = self._index.diff("HEAD")

        # Add to buffer (only if there's actual diff content)
        step_index = self._diff_buffer.add_step(tool_name, file_path, diff)

        return step_index


    def _next_task_id(self, run_id: str) -> str:
        tasks_dir = self.registry.run_dir(run_id) / "tasks"
        existing = sorted(tasks_dir.glob("task-*")) if tasks_dir.exists() else []
        return f"task-{len(existing) + 1:03d}"

    def _task_title(self, task_id: str) -> str:
        try:
            return f"Task{int(task_id.rsplit('-', 1)[1])}"
        except (IndexError, ValueError):
            return task_id

    def _task_dir(self, run_id: str, task_id: str) -> Path:
        return self.registry.run_dir(run_id) / "tasks" / task_id


    def _ensure_git_workspace(self, workspace: Path) -> None:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0 or result.stdout.strip() != "true":
            raise RuntimeTaskError(f"workspace is not a git repository: {workspace}")

    def _write_snapshot(self, workspace: Path, output: Path) -> None:
        files = self._git_files(workspace)
        with tarfile.open(output, "w:gz") as tar:
            for rel in files:
                path = workspace / rel
                if path.is_file():
                    tar.add(path, arcname=rel)

    def _git_files(self, workspace: Path) -> list[str]:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return [line for line in result.stdout.splitlines() if line]

    def _git_output(self, workspace: Path, args: list[str], *, allow_fail: bool = False) -> str | None:
        result = subprocess.run(
            ["git", *args],
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            if allow_fail:
                return None
            raise RuntimeTaskError(result.stderr.strip() or "git command failed")
        return result.stdout.strip()

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
