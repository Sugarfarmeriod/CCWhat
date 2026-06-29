#!/bin/bash
# CCWhat PostToolUse Hook - Records file changes for incremental diff tracking
# This hook is triggered after each tool use and notifies the CCWhat controller

# Check if CCWhat tracking is enabled
if [[ "$CCWHAT_ENABLED" != "1" ]]; then
    exit 0
fi

# Check if controller port is available
if [[ -z "$CCWHAT_RUNTIME_CONTROL_PORT" ]]; then
    exit 0
fi

# Read JSON payload from stdin
read -r payload

# Extract tool_name using jq if available, otherwise use grep/sed
if command -v jq &> /dev/null; then
    tool_name=$(echo "$payload" | jq -r '.tool_name // empty')
    file_path=$(echo "$payload" | jq -r '.tool_input.file_path // empty')
    bash_command=$(echo "$payload" | jq -r '.tool_input.command // empty')
else
    # Fallback without jq
    tool_name=$(echo "$payload" | grep -o '"tool_name"[^,}]*' | cut -d'"' -f4)
    file_path=$(echo "$payload" | grep -o '"file_path"[^,}]*' | cut -d'"' -f4)
    bash_command=$(echo "$payload" | grep -o '"command"[^,}]*' | cut -d'"' -f4)
fi

# Handle file modification tools (Write/Edit/MultiEdit)
if [[ "$tool_name" =~ ^(Write|Edit|MultiEdit)$ && -n "$file_path" ]]; then
    # Notify controller (fire-and-forget)
    curl -s -X POST "http://127.0.0.1:${CCWHAT_RUNTIME_CONTROL_PORT}/step" \
        -H "Content-Type: application/json" \
        -d "{\"tool_name\":\"$tool_name\",\"file_path\":\"$file_path\"}" \
        > /dev/null 2>&1 &
    exit 0
fi

# Any Bash command may modify files (mv, sed, cp, echo >, rm, ...).
# Sync the whole workspace so the backend reconciles actual disk state.
if [[ "$tool_name" == "Bash" ]]; then
    curl -s -X POST "http://127.0.0.1:${CCWHAT_RUNTIME_CONTROL_PORT}/step" \
        -H "Content-Type: application/json" \
        -d "{\"tool_name\":\"Bash\",\"file_path\":\"\",\"action\":\"sync\"}" \
        > /dev/null 2>&1 &
    exit 0
fi

exit 0
