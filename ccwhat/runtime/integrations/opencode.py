"""OpenCode command/plugin integration for CCWhat runtime recording."""

from __future__ import annotations

from pathlib import Path


INTEGRATION_VERSION = "1"
MANAGED_MARKER = "CCWHAT MANAGED OPENCODE RUNTIME TASK COMMAND"
COMMANDS = {
    "start": "CCWhat Task start",
    "finish": "CCWhat Task finish",
}
OBSOLETE_COMMAND_NAMES = ("ccwhat-start", "ccwhat-finish")


class OpenCodeIntegrationConflict(RuntimeError):
    pass


def install_opencode_integration(workspace: Path) -> list[Path]:
    opencode_dir = workspace / ".opencode"
    command_dir = opencode_dir / "command"
    plugin_dir = opencode_dir / "plugin"
    written: list[Path] = []

    for directory in (command_dir, plugin_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for obsolete_name in OBSOLETE_COMMAND_NAMES:
        _remove_managed(command_dir / f"{obsolete_name}.md")

    for name, description in COMMANDS.items():
        path = command_dir / f"ccwhat:{name}.md"
        _write_managed(path, _command_content(name, description), "OpenCode command")
        written.append(path)

    plugin_path = plugin_dir / "ccwhat-runtime.js"
    _write_managed(plugin_path, _plugin_content(), "OpenCode plugin")
    written.append(plugin_path)
    return written


def _command_content(name: str, description: str) -> str:
    boundary = "start" if name == "start" else "finish"
    return (
        "---\n"
        f"description: {description}\n"
        "---\n\n"
        f"<!-- {MANAGED_MARKER} v{INTEGRATION_VERSION} -->\n"
        f"CCWHAT_COMMAND={name}\n"
        "\n"
        "This is a CCWhat local task-boundary marker for OpenCode.\n"
        f"Boundary action: {boundary}.\n"
        "Do not inspect files, run tools, or explain CCWhat.\n"
        "Reply exactly with: 收到\n"
    )


def _plugin_content() -> str:
    return (
        f"// {MANAGED_MARKER} v{INTEGRATION_VERSION}\n"
        "async function callController(action) {\n"
        "  const port = process.env.CCWHAT_RUNTIME_CONTROL_PORT\n"
        "  const token = process.env.CCWHAT_RUNTIME_TOKEN || \"\"\n"
        "  if (!port) throw new Error(\"CCWhat runtime controller is not available for this OpenCode session\")\n"
        "  const response = await fetch(`http://127.0.0.1:${port}/${action}`, {\n"
        "    method: \"POST\",\n"
        "    headers: {\n"
        "      \"Content-Type\": \"application/json\",\n"
        "      \"X-CCWhat-Run-Token\": token,\n"
        "    },\n"
        "    body: JSON.stringify({\n"
        "      agent: \"opencode\",\n"
        "      integration: \"opencode_command_execute_before\",\n"
        "      model_visible: true,\n"
        "      agent_log_visible: true,\n"
        "      confidence: \"medium\",\n"
        "    }),\n"
        "  })\n"
        "  const payload = await response.json().catch(() => ({}))\n"
        "  if (!response.ok || payload.ok === false) {\n"
        "    throw new Error(payload.error || `CCWhat ${action} failed`)\n"
        "  }\n"
        "  return payload.data || {}\n"
        "}\n\n"
        "export default async function ccwhatRuntimePlugin() {\n"
        "  return {\n"
        "    \"command.execute.before\": async (input, output) => {\n"
        "      const actions = {\n"
        "        \"ccwhat:start\": \"start\",\n"
        "        \"ccwhat:finish\": \"finish\",\n"
        "        \"ccwhat-start\": \"start\",\n"
        "        \"ccwhat-finish\": \"finish\",\n"
        "      }\n"
        "      const action = actions[input.command]\n"
        "      if (!action) return\n"
        "      const data = await callController(action)\n"
        "      console.error(`CCWhat ${action} recorded locally${data.task_id ? ` (${data.task_id})` : \"\"}.`)\n"
        "    },\n"
        "  }\n"
        "}\n"
    )


def _remove_managed(path: Path) -> None:
    if not path.exists():
        return
    existing = path.read_text(encoding="utf-8", errors="replace")
    if MANAGED_MARKER in existing:
        path.unlink()


def _write_managed(path: Path, content: str, kind: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if MANAGED_MARKER not in existing:
            raise OpenCodeIntegrationConflict(f"refusing to overwrite non-CCWhat {kind}: {path}")
        if existing == content:
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
