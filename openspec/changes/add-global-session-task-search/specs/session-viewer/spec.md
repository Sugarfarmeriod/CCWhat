## ADDED Requirements

### Requirement: Backend API — scoped session and task search

Viewer server SHALL provide a scoped search API for sessions and task sources without requiring the frontend to load every searchable session.

#### Scenario: Default to current session scope

- **WHEN** the frontend calls the search API without an explicit scope
- **THEN** the backend SHALL treat the request as `scope: "current_session"`
- **AND** the backend SHALL require a valid current `sessionId`
- **AND** the backend SHALL NOT scan other sessions or projects

#### Scenario: Search current session by keyword

- **WHEN** the frontend calls the global search API with a non-empty query
- **AND** the effective scope is `current_session`
- **THEN** the backend SHALL search only the specified current session
- **AND** the response SHALL include `ok: true`, the normalized query, a `results` array, and a `truncated` flag
- **AND** each session result SHALL include `type: "session"`, `sessionId`, `projectDir`, `matchedFields`, and a short `snippet`

#### Scenario: Search across sessions in the current project

- **WHEN** the frontend calls the search API with `scope: "current_project"`
- **AND** the request includes the current project identifier
- **THEN** the backend SHALL search sessions within that project
- **AND** the backend SHALL NOT search sessions from other projects

#### Scenario: Search across projects

- **WHEN** the frontend calls the search API with `scope: "all_projects"`
- **THEN** the backend SHALL search locally discoverable sessions across projects
- **AND** the response SHALL preserve each result's `projectDir`

#### Scenario: Search session turns or events

- **WHEN** the query matches user text, assistant text, tool names, commands, file paths, errors, or event summaries inside a session
- **THEN** the backend SHALL return a result with `type: "turn"` or `type: "event"`
- **AND** the result SHALL include enough navigation metadata to load the session and locate the matched turn or event when available
- **AND** the result SHALL include a bounded text snippet rather than the full raw event payload

#### Scenario: Search existing task sources

- **WHEN** an existing task source is available for a session
- **THEN** the backend or frontend search flow SHALL support matching task title, task id, task type, boundary metadata, and evidence fields
- **AND** task results SHALL include `type: "task"`, `sessionId`, `taskId`, `title`, `taskType`, `matchedFields`, and a short `snippet`

#### Scenario: Do not create synthetic tasks

- **WHEN** a session has not been task-segmented and no saved task source is available
- **THEN** scoped search SHALL NOT invent task results for that session
- **AND** matching content MAY still appear as session, turn, or event results

#### Scenario: Limit and truncate results

- **WHEN** the number of matches exceeds the requested or default limit
- **THEN** the response SHALL include only the bounded result set
- **AND** `truncated` SHALL be `true`
- **AND** the response SHALL NOT load or return unbounded raw session content

#### Scenario: Invalid or empty query

- **WHEN** the query is empty or below the minimum supported length
- **THEN** the API SHALL return HTTP 400
- **AND** the response SHALL include `ok: false` and a readable error message

#### Scenario: Partial session read failure

- **WHEN** one or more sessions cannot be read during search
- **THEN** the API SHALL continue searching other sessions where possible
- **AND** the response SHALL include warning metadata describing skipped sessions
- **AND** the API SHALL NOT fail the entire request unless no searchable session source is available

### Requirement: Frontend — scoped search entry point

Claude Log Viewer SHALL provide a search entry point with an explicit scope selector.

#### Scenario: Open scoped search

- **WHEN** the user activates the search entry point
- **THEN** the Viewer SHALL show a search input, scope selector, and empty state
- **AND** the scope selector SHALL default to current session
- **AND** the selector SHALL offer current session, cross-session within current project, and cross-project options

#### Scenario: Search scope is explicit

- **WHEN** the user has not changed the scope selector
- **THEN** the search request SHALL use current session scope
- **AND** the Viewer SHALL NOT issue cross-session or cross-project search requests

#### Scenario: Render scoped search results

- **WHEN** the scoped search API returns results
- **THEN** the Viewer SHALL render a result list grouped or labeled by result type
- **AND** each result SHALL show the active search scope, matched session, result type, matched field summary, and snippet
- **AND** empty results SHALL render a readable empty state

#### Scenario: Navigate to a session result

- **WHEN** the user selects a session result
- **THEN** the Viewer SHALL load that session
- **AND** the Viewer SHALL navigate to the Session page

#### Scenario: Navigate to a task result

- **WHEN** the user selects a task result
- **THEN** the Viewer SHALL load the result session
- **AND** the Viewer SHALL navigate to the Tasks page and select the result task when the task source is available
- **AND** if the task source is not currently available, the Viewer SHALL show a readable prompt instead of silently failing

#### Scenario: Navigate to a turn or event result

- **WHEN** the user selects a turn or event result
- **THEN** the Viewer SHALL load the result session
- **AND** the Viewer SHALL navigate to the Session page and attempt to locate the matched turn or event
- **AND** if the target is hidden by current filters, the Viewer SHALL show a filter hint using the existing navigation hint pattern

#### Scenario: Protect dirty task overlay on cross-session navigation

- **WHEN** the current session has a dirty Task Trace Overlay
- **AND** the user selects a global search result from another session
- **THEN** the Viewer SHALL reuse the existing dirty overlay protection flow before switching sessions
- **AND** cancelling the switch SHALL keep the current session and overlay state unchanged
