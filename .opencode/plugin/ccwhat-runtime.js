// CCWHAT MANAGED OPENCODE RUNTIME TASK COMMAND v1
async function callController(action) {
  const port = process.env.CCWHAT_RUNTIME_CONTROL_PORT
  const token = process.env.CCWHAT_RUNTIME_TOKEN || ""
  if (!port) throw new Error("CCWhat runtime controller is not available for this OpenCode session")
  const response = await fetch(`http://127.0.0.1:${port}/${action}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CCWhat-Run-Token": token,
    },
    body: JSON.stringify({
      agent: "opencode",
      integration: "opencode_command_execute_before",
      model_visible: true,
      agent_log_visible: true,
      confidence: "medium",
    }),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `CCWhat ${action} failed`)
  }
  return payload.data || {}
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
      const data = await callController(action)
      console.error(`CCWhat ${action} recorded locally${data.task_id ? ` (${data.task_id})` : ""}.`)
    },
  }
}
