"""Runtime run registry for task recording."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import uuid

from ccwhat.config import CCWHAT_DIR


RUNTIME_RUNS_DIR = CCWHAT_DIR / "runtime-runs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class RuntimeRun:
    run_id: str
    agent: str
    workspace: str
    started_at: str
    status: str = "starting"
    finished_at: str | None = None
    target_args: list[str] = field(default_factory=list)
    agent_process: dict[str, int | str | None] = field(default_factory=dict)
    proxy: dict[str, int | bool | None] = field(default_factory=dict)
    viewer: dict[str, int | bool | None] = field(default_factory=dict)
    control: dict[str, int | str | None] = field(default_factory=dict)
    active_task_id: str | None = None


class RunRegistry:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or RUNTIME_RUNS_DIR

    def run_dir(self, run_id: str) -> Path:
        legacy = self.root / run_id
        if (legacy / "run.json").exists():
            return legacy
        if self.root.exists():
            matches = sorted(self.root.glob(f"*/{run_id}"))
            for match in matches:
                if (match / "run.json").exists():
                    return match
        return self.root / run_id

    def _run_dir_for_run(self, run: RuntimeRun) -> Path:
        return self.root / _safe_agent_dir(run.agent) / run.run_id

    def run_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "run.json"

    def create_run(
        self,
        *,
        agent: str,
        workspace: Path,
        target_args: tuple[str, ...],
        proxy_port: int,
        viewer_port: int | None,
        control_port: int,
        proxy_auto_allocated: bool = True,
        viewer_auto_allocated: bool = True,
    ) -> RuntimeRun:
        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        token = secrets.token_urlsafe(24)
        run = RuntimeRun(
            run_id=run_id,
            agent=agent,
            workspace=str(workspace.resolve()),
            started_at=utc_now(),
            target_args=list(target_args),
            proxy={"port": proxy_port, "auto_allocated": proxy_auto_allocated},
            viewer={"port": viewer_port, "auto_allocated": viewer_port is not None and viewer_auto_allocated},
            control={"port": control_port, "host": "127.0.0.1", "token": token},
        )
        self.save(run)
        return run

    def load(self, run_id: str) -> RuntimeRun:
        data = json.loads(self.run_path(run_id).read_text(encoding="utf-8"))
        return RuntimeRun(**data)

    def save(self, run: RuntimeRun) -> None:
        existing = self.run_dir(run.run_id)
        run_dir = existing if (existing / "run.json").exists() else self._run_dir_for_run(run)
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "run.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(run), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def update(self, run_id: str, **changes: object) -> RuntimeRun:
        run = self.load(run_id)
        for key, value in changes.items():
            if not hasattr(run, key):
                raise AttributeError(key)
            setattr(run, key, value)
        self.save(run)
        return run

    def set_active_task(self, run_id: str, task_id: str | None) -> RuntimeRun:
        return self.update(run_id, active_task_id=task_id)


def _safe_agent_dir(agent: str) -> str:
    value = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in agent.lower())
    return value or "unknown"
