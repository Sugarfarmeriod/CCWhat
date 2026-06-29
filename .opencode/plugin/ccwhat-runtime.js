// CCWHAT MANAGED OPENCODE RUNTIME TASK COMMAND v1
async function callController(action, body = {}) {
  const port = process.env.CCWHAT_RUNTIME_CONTROL_PORT
  const token = process.env.CCWHAT_RUNTIME_TOKEN || ""
  if (!port) return null
  const response = await fetch(`http://127.0.0.1:${port}/${action}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CCWhat-Run-Token": token,
    },
    body: JSON.stringify(body),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload.ok === false) {
    console.error(`CCWhat ${action} failed:`, payload.error)
    return null
  }
  return payload.data || {}
}

function detectFileOperation(toolName, toolInput) {
  // OpenCode tool names are lowercase: write, edit, bash
  if (["write", "edit"].includes(toolName)) {
    const filePath = toolInput?.filePath || toolInput?.file_path || toolInput?.path
    if (filePath) return { tool: toolName, path: filePath, action: "add" }
  }
  // Check for file deletion via bash
  if (toolName === "bash") {
    const cmd = toolInput?.command || ""
    const rmMatch = cmd.match(/(?:^|[;&|]\s*)\s*(rm|unlink)\s+(?:-[a-zA-Z]+\s+)*(.+?)$/)
    if (rmMatch) {
      const paths = rmMatch[2].split(/\s+/).filter(p => p && !p.startsWith("-"))
      return paths.map(p => ({ tool: "bash", path: p, action: "delete" }))
    }
  }
  return null
}

export default async function ccwhatRuntimePlugin() {
  return {
    "command.execute.before": async (input, output) => {
      const actions = {
        "ccwhat:start": "start",
        "ccwhat:finish": "finish",
        "ccwhat-start": "start",
        "ccwhat-finish": "finish",
      }
      const action = actions[input.command]
      if (!action) return
      const data = await callController(action, {
        agent: "opencode",
        integration: "opencode_command_execute_before",
      })
      if (data) {
        console.error(`CCWhat ${action} recorded locally${data.task_id ? ` (${data.task_id})` : ""}.`)
      }
    },
    "tool.execute.after": async (input, output) => {
      // Skip if CCWhat is not enabled
      if (!process.env.CCWHAT_ENABLED) return
      const toolName = input?.tool
      const toolInput = input?.args
      const operations = detectFileOperation(toolName, toolInput)
      if (!operations) return
      const ops = Array.isArray(operations) ? operations : [operations]
      for (const op of ops) {
        await callController("step", {
          tool_name: op.tool,
          file_path: op.path,
          action: op.action,
        })
      }
    },
  }
}
