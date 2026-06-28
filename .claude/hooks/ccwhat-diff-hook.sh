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

# Handle Bash tool for file deletions
if [[ "$tool_name" == "Bash" && -n "$bash_command" ]]; then
    # Check if this looks like a file deletion command
    # Matches: rm file, rm -f file, rm -rf dir, unlink file, etc.
    if echo "$bash_command" | grep -qE '^\s*(rm|unlink)\s+'; then
        # Extract deleted paths (simplified: take all arguments after rm/unlink)
        deleted_paths=$(echo "$bash_command" | sed -E 's/^\s*(rm|unlink)\s+(-[a-zA-Z]+\s+)*//')
        for path in $deleted_paths; do
            # Skip flags/options
            [[ "$path" == -* ]] && continue
            # Notify controller about deletion
            curl -s -X POST "http://127.0.0.1:${CCWHAT_RUNTIME_CONTROL_PORT}/step" \
                -H "Content-Type: application/json" \
                -d "{\"tool_name\":\"Bash\",\"file_path\":\"$path\",\"action\":\"delete\"}" \
                > /dev/null 2>&1 &
        done
    fi
fi

exit 0
