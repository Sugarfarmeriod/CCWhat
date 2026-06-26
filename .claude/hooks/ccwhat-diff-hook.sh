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
else
    # Fallback without jq
    tool_name=$(echo "$payload" | grep -o '"tool_name"[^,}]*' | cut -d'"' -f4)
    file_path=$(echo "$payload" | grep -o '"file_path"[^,}]*' | cut -d'"' -f4)
fi

# Only process file modification tools
if [[ ! "$tool_name" =~ ^(Write|Edit|MultiEdit)$ ]]; then
    exit 0
fi

# Skip if no file path
if [[ -z "$file_path" ]]; then
    exit 0
fi

# Notify controller (fire-and-forget)
curl -s -X POST "http://127.0.0.1:${CCWHAT_RUNTIME_CONTROL_PORT}/step" \
    -H "Content-Type: application/json" \
    -d "{\"tool_name\":\"$tool_name\",\"file_path\":\"$file_path\"}" \
    > /dev/null 2>&1 &

exit 0
