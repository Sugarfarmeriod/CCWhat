"""Runtime task staging with git snapshots and diff evidence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import tarfile
from typing import Any

from ccwhat.runtime.registry import RunRegistry, RuntimeRun, utc_now


class RuntimeTaskError(RuntimeError):
    pass


@dataclass
class ControlEvidence:
    command: str
    raw_args: str = ""
    agent: str = "claude"
    integration: str = "claude_user_prompt_submit"
    model_visible: bool = False
    agent_log_visible: bool = False
    confidence: str = "high"


class TaskStaging:
    def __init__(self, registry: RunRegistry) -> None:
        self.registry = registry

    def start_task(self, run: RuntimeRun, title: str, evidence: ControlEvidence) -> dict[str, Any]:
        if run.active_task_id:
            raise RuntimeTaskError(f"task already recording: {run.active_task_id}")
        workspace = Path(run.workspace)
        self._ensure_git_workspace(workspace)
        task_id = self._next_task_id(run.run_id)
        task_dir = self._task_dir(run.run_id, task_id)
        task_dir.mkdir(parents=True, exist_ok=False)

        now = utc_now()
        before_path = task_dir / "repo_before.tar.gz"
        self._write_snapshot(workspace, before_path)
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
            "paths": {
                "repo_before": "repo_before.tar.gz",
                "repo_after": None,
                "diff": None,
                "control_events": "control_events.jsonl",
            },
            "evidence_availability": {
                "repo_before": True,
                "repo_after": False,
                "diff": False,
                "control_events": True,
            },
        }
        self._write_json(task_dir / "task.json", task)
        self._append_control_event(task_dir, evidence, {"task_id": task_id, "status": "recording"})
        self.registry.set_active_task(run.run_id, task_id)
        return task

    def finish_task(self, run: RuntimeRun, evidence: ControlEvidence) -> dict[str, Any]:
        if not run.active_task_id:
            raise RuntimeTaskError("no active task to finish")
        workspace = Path(run.workspace)
        self._ensure_git_workspace(workspace)
        task_dir = self._task_dir(run.run_id, run.active_task_id)
        task = self._read_json(task_dir / "task.json")

        self._write_snapshot(workspace, task_dir / "repo_after.tar.gz")
        diff = self._git_output(workspace, ["diff", "--binary", "HEAD"], allow_fail=True) or ""
        (task_dir / "diff.patch").write_text(diff, encoding="utf-8")

        task["status"] = "finalized"
        task["finished_at"] = utc_now()
        task["git"]["after_commit"] = self._git_output(workspace, ["rev-parse", "HEAD"], allow_fail=True)
        task["git"]["after_status"] = self._git_output(workspace, ["status", "--short"], allow_fail=True) or ""
        task["paths"]["repo_after"] = "repo_after.tar.gz"
        task["paths"]["diff"] = "diff.patch"
        task["evidence_availability"]["repo_after"] = True
        task["evidence_availability"]["diff"] = True
        self._write_json(task_dir / "task.json", task)
        self._append_control_event(task_dir, evidence, {"task_id": run.active_task_id, "status": "finalized"})
        self.registry.set_active_task(run.run_id, None)
        return task

    def abort_task(self, run: RuntimeRun, evidence: ControlEvidence) -> dict[str, Any]:
        if not run.active_task_id:
            raise RuntimeTaskError("no active task to abort")
        task_dir = self._task_dir(run.run_id, run.active_task_id)
        task = self._read_json(task_dir / "task.json")
        task["status"] = "aborted"
        task["finished_at"] = utc_now()
        self._write_json(task_dir / "task.json", task)
        self._append_control_event(task_dir, evidence, {"task_id": run.active_task_id, "status": "aborted"})
        self.registry.set_active_task(run.run_id, None)
        return task

    def status(self, run: RuntimeRun, evidence: ControlEvidence | None = None) -> dict[str, Any]:
        payload = {
            "run_id": run.run_id,
            "status": "recording" if run.active_task_id else "idle",
            "active_task_id": run.active_task_id,
        }
        if run.active_task_id and evidence is not None:
            self._append_control_event(
                self._task_dir(run.run_id, run.active_task_id),
                evidence,
                payload,
            )
        return payload

    def note(self, run: RuntimeRun, evidence: ControlEvidence) -> dict[str, Any]:
        if not run.active_task_id:
            raise RuntimeTaskError("no active task for note")
        payload = {
            "run_id": run.run_id,
            "status": "recording",
            "active_task_id": run.active_task_id,
        }
        self._append_control_event(self._task_dir(run.run_id, run.active_task_id), evidence, payload)
        return payload

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

    def _append_control_event(self, task_dir: Path, evidence: ControlEvidence, result: dict[str, Any]) -> None:
        event = {
            "timestamp": utc_now(),
            "command": evidence.command,
            "raw_args": evidence.raw_args,
            "agent": evidence.agent,
            "integration": evidence.integration,
            "model_visible": evidence.model_visible,
            "agent_log_visible": evidence.agent_log_visible,
            "confidence": evidence.confidence,
            "result": result,
        }
        with (task_dir / "control_events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

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
