from __future__ import annotations

import json
import io
import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from ccwhat.cli import cli
from ccwhat.config import RecordingConfig
from ccwhat.runtime.claude_integration import (
    ClaudeIntegrationConflict,
    install_claude_integration,
)
from ccwhat.runtime.client import call_controller
from ccwhat.runtime.controller import RuntimeController
from ccwhat.runtime.claude_hook import main as claude_hook_main
from ccwhat.runtime.ports import allocate_port, resolve_runtime_ports
from ccwhat.runtime.registry import RunRegistry


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, check=True, stdout=subprocess.PIPE)


def test_run_registry_isolates_active_tasks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = RunRegistry(Path(tmp))
        run_a = registry.create_run(
            agent="claude",
            workspace=Path(tmp),
            target_args=("claude",),
            proxy_port=11001,
            viewer_port=11002,
            control_port=11003,
        )
        run_b = registry.create_run(
            agent="claude",
            workspace=Path(tmp),
            target_args=("claude",),
            proxy_port=12001,
            viewer_port=12002,
            control_port=12003,
        )

        registry.set_active_task(run_a.run_id, "task-001")

        assert registry.load(run_a.run_id).active_task_id == "task-001"
        assert registry.load(run_b.run_id).active_task_id is None
        assert registry.run_path(run_a.run_id) != registry.run_path(run_b.run_id)


def test_runtime_ports_allocate_distinct_ports_and_keep_explicit_values() -> None:
    proxy, viewer, control = resolve_runtime_ports(proxy_port=None, viewer_port=None, need_viewer=True)
    assert len({proxy, viewer, control}) == 3

    explicit_proxy = allocate_port()
    explicit_viewer = allocate_port({explicit_proxy})
    proxy, viewer, control = resolve_runtime_ports(
        proxy_port=explicit_proxy,
        viewer_port=explicit_viewer,
        need_viewer=True,
    )
    assert proxy == explicit_proxy
    assert viewer == explicit_viewer
    assert control not in {explicit_proxy, explicit_viewer}


def test_controller_start_finish_writes_runtime_task_staging() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "repo"
        workspace.mkdir()
        _init_repo(workspace)

        registry = RunRegistry(root / "runtime")
        port = allocate_port()
        run = registry.create_run(
            agent="claude",
            workspace=workspace,
            target_args=("claude",),
            proxy_port=11001,
            viewer_port=11002,
            control_port=port,
        )
        controller = RuntimeController(registry, run.run_id, port)
        controller.start()
        try:
            token = str(run.control["token"])
            started = call_controller(
                port,
                token,
                "start",
                {
                    "title": "runtime task",
                    "integration": "claude_user_prompt_expansion",
                    "model_visible": False,
                    "confidence": "high",
                },
            )
            assert started["ok"] is True
            noted = call_controller(
                port,
                token,
                "note",
                {
                    "raw_args": "important runtime note",
                    "integration": "claude_user_prompt_expansion",
                    "model_visible": False,
                    "confidence": "high",
                },
            )
            assert noted["ok"] is True

            (workspace / "README.md").write_text("after\n", encoding="utf-8")
            finished = call_controller(
                port,
                token,
                "finish",
                {
                    "integration": "claude_user_prompt_expansion",
                    "model_visible": False,
                    "confidence": "high",
                },
            )
            assert finished["ok"] is True
        finally:
            controller.stop()

        task_dir = registry.run_dir(run.run_id) / "tasks" / "task-001"
        task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
        assert task["status"] == "finalized"
        assert task["evidence_availability"]["repo_before"] is True
        assert task["evidence_availability"]["repo_after"] is True
        assert task["evidence_availability"]["diff"] is True
        assert (task_dir / "repo_before.tar.gz").exists()
        assert (task_dir / "repo_after.tar.gz").exists()
        assert "-before" in (task_dir / "diff.patch").read_text(encoding="utf-8")
        assert "+after" in (task_dir / "diff.patch").read_text(encoding="utf-8")
        events = (task_dir / "control_events.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(events) == 3
        assert json.loads(events[0])["model_visible"] is False
        assert json.loads(events[1])["command"] == "note"


def test_controller_rejects_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "repo"
        workspace.mkdir()
        _init_repo(workspace)
        registry = RunRegistry(root / "runtime")
        port = allocate_port()
        run = registry.create_run(
            agent="claude",
            workspace=workspace,
            target_args=("claude",),
            proxy_port=11001,
            viewer_port=None,
            control_port=port,
        )
        controller = RuntimeController(registry, run.run_id, port)
        controller.start()
        try:
            token = str(run.control["token"])
            assert call_controller(port, token, "finish", {})["ok"] is False
            assert call_controller(port, token, "start", {"title": "one"})["ok"] is True
            assert call_controller(port, token, "start", {"title": "two"})["ok"] is False
        finally:
            controller.stop()


def test_controller_rejects_non_git_workspace_on_start() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "not-git"
        workspace.mkdir()
        registry = RunRegistry(root / "runtime")
        port = allocate_port()
        run = registry.create_run(
            agent="claude",
            workspace=workspace,
            target_args=("claude",),
            proxy_port=11001,
            viewer_port=None,
            control_port=port,
        )
        controller = RuntimeController(registry, run.run_id, port)
        controller.start()
        try:
            result = call_controller(port, str(run.control["token"]), "start", {"title": "bad"})
        finally:
            controller.stop()

        assert result["ok"] is False
        assert "not a git repository" in result["error"]
        assert not (registry.run_dir(run.run_id) / "tasks").exists()


def test_claude_integration_generates_managed_files_and_detects_conflicts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        written = install_claude_integration(workspace)

        start_command = workspace / ".claude" / "commands" / "ccwhat" / "start.md"
        finish_command = workspace / ".claude" / "commands" / "ccwhat" / "finish.md"
        hook = workspace / ".claude" / "hooks" / "ccwhat-runtime-hook.sh"
        settings = workspace / ".claude" / "settings.local.json"
        assert start_command in written
        assert "CCWHAT_COMMAND=start" in start_command.read_text(encoding="utf-8")
        assert finish_command.exists()
        assert hook.exists()
        assert "UserPromptExpansion" in settings.read_text(encoding="utf-8")

        start_command.write_text("user file\n", encoding="utf-8")
        try:
            install_claude_integration(workspace)
        except ClaudeIntegrationConflict as exc:
            assert "refusing to overwrite" in str(exc)
        else:
            raise AssertionError("expected ClaudeIntegrationConflict")


def test_claude_hook_command_drives_controller_and_staging() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "repo"
        workspace.mkdir()
        _init_repo(workspace)

        registry = RunRegistry(root / "runtime")
        port = allocate_port()
        run = registry.create_run(
            agent="claude",
            workspace=workspace,
            target_args=("claude",),
            proxy_port=11001,
            viewer_port=11002,
            control_port=port,
        )
        controller = RuntimeController(registry, run.run_id, port)
        controller.start()
        env = {
            "CCWHAT_RUNTIME_CONTROL_PORT": str(port),
            "CCWHAT_RUNTIME_TOKEN": str(run.control["token"]),
        }
        try:
            with mock.patch.dict(os.environ, env), \
                 mock.patch("sys.stdin", io.StringIO('{"prompt":"CCWHAT_COMMAND=start\\nCCWHAT_ARGS=hook task"}')), \
                 mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                assert claude_hook_main() == 2
                assert "decision" in stdout.getvalue()

            (workspace / "README.md").write_text("after hook\n", encoding="utf-8")
            with mock.patch.dict(os.environ, env), \
                 mock.patch("sys.stdin", io.StringIO('{"prompt":"CCWHAT_COMMAND=finish\\nCCWHAT_ARGS="}')), \
                 mock.patch("sys.stdout", new_callable=io.StringIO):
                assert claude_hook_main() == 2
        finally:
            controller.stop()

        task_dir = registry.run_dir(run.run_id) / "tasks" / "task-001"
        assert (task_dir / "task.json").exists()
        assert (task_dir / "control_events.jsonl").exists()
        assert (task_dir / "repo_before.tar.gz").exists()
        assert (task_dir / "repo_after.tar.gz").exists()
        assert (task_dir / "diff.patch").exists()
        task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
        assert task["title"] == "hook task"
        assert task["status"] == "finalized"


def test_top_level_claude_run_creates_runtime_and_injects_env() -> None:
    runner = CliRunner()
    captured_env: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        runtime_root = Path(tmp) / "runtime"
        registry = RunRegistry(runtime_root)

        def fake_popen(args, env=None, **kwargs):
            captured_env.update(env or {})
            proc = mock.MagicMock()
            proc.pid = 1234
            proc.wait.return_value = 0
            return proc

        with runner.isolated_filesystem():
            _init_repo(Path.cwd())
            with mock.patch("ccwhat.commands.run.load_config", return_value=RecordingConfig(preset="claude")), \
                 mock.patch("ccwhat.commands.run.RunRegistry", return_value=registry), \
                 mock.patch("ccwhat.commands.run.RuntimeController") as controller_cls, \
                 mock.patch("ccwhat.commands.run.install_claude_integration") as install_integration, \
                 mock.patch("ccwhat.commands.run.resolve_runtime_ports", return_value=(19001, 19002, 19003)), \
                 mock.patch("ccwhat.commands.run._proxy_is_running", return_value=True), \
                 mock.patch("ccwhat.commands.run._start_managed_web", return_value=None), \
                 mock.patch("ccwhat.commands.run.subprocess.Popen", side_effect=fake_popen):
                controller_cls.return_value.start.return_value = None
                controller_cls.return_value.stop.return_value = None
                result = runner.invoke(cli, ["--", "claude"])

        assert result.exit_code == 0
        install_integration.assert_called_once()
        assert captured_env["CCWHAT_RUNTIME_CONTROL_PORT"] == "19003"
        assert captured_env["CCWHAT_RUNTIME_RUN_ID"]
        run_path = next(runtime_root.glob("*/run.json"))
        run = json.loads(run_path.read_text(encoding="utf-8"))
        assert run["proxy"]["port"] == 19001
        assert run["viewer"]["port"] == 19002
        assert run["control"]["port"] == 19003
        assert run["agent_process"]["pid"] == 1234
