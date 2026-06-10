## 1. UI Entry and State

- [x] 1.1 Add a `taskSegmentsBtn` button to the Claude Log topbar next to the analysis button
- [x] 1.2 Add frontend state for `taskSegmentReports`, `taskSegmentsInFlight`, and selected task id
- [x] 1.3 Update session load/reset flow so the task segmentation button is disabled before load and reflects cached state after load
- [x] 1.4 Keep task segmentation cache in memory only and avoid localStorage/session persistence

## 2. API Request and Cache Behavior

- [x] 2.1 Implement `requestTaskSegments(sessionId)` using `POST /api/task-segments`
- [x] 2.2 Ensure request body contains only `{sessionId}` and does not include turns, filters, raw logs, or multi-session parameters
- [x] 2.3 Implement `showCachedTaskSegments()` and `runTaskSegmentationForCurrentSession()` with loading, success, and error states
- [x] 2.4 Implement “重新切分” behavior that overwrites cache only on success and preserves previous cached result on failure

## 3. Task Segmentation Overview Rendering

- [x] 3.1 Render a task segmentation header with task count, ambiguous state, topic flips, elapsed time, and actions
- [x] 3.2 Render empty state when `tasks` is empty
- [x] 3.3 Render task cards showing id, title, task type, status, evidence counts, subagent count, final-claim indicator, and ambiguous badge
- [x] 3.4 Implement selected task card state and default selection of the first task

## 4. Task Detail Rendering

- [x] 4.1 Render selected task overview with title, type, status, startEventId, endEventId, and finalClaim
- [x] 4.2 Render evidence sections for filesRead, filesChanged, commands, testCommands, errors, subagentIds, and todosUser
- [x] 4.3 Render boundaryReasons preserving original signal and score text
- [x] 4.4 Render fileWeights sorted by descending weight
- [x] 4.5 Render escaped, collapsed raw task JSON

## 5. Event Navigation

- [x] 5.1 Implement helper to map `main:<line>` and `agent-<id>:<line>` event ids to existing `allEntries` indices
- [x] 5.2 Add “定位开始事件” and “定位结束事件” actions to task detail
- [x] 5.3 When an event is found, select and expand the matching original log entry using existing list/detail behavior
- [x] 5.4 When an event cannot be found, disable the action or show a clear unavailable state without throwing script errors

## 6. Debug Boundaries and Styling

- [x] 6.1 Render `debugBoundaries` in a collapsed debug section with eventId, score, shouldSplit, and reasons
- [x] 6.2 Add compact, scan-friendly CSS for task cards, evidence chips/lists, file weights, boundary reasons, and debug rows
- [x] 6.3 Ensure long text, paths, commands, and errors wrap without overlapping or resizing fixed controls
- [x] 6.4 Preserve existing analysis report, export modal, search/filter, and raw log detail behavior

## 7. Tests and Validation

- [x] 7.1 Add frontend static regression tests for the task segmentation button and request shape
- [x] 7.2 Add frontend static regression tests for cache, reload, and re-segmentation behavior
- [x] 7.3 Add frontend static regression tests for task card/detail/evidence/boundary/fileWeights rendering functions
- [x] 7.4 Add frontend static regression tests for event id mapping and navigation helpers
- [x] 7.5 Run task segmentation tests and existing viewer/current-session analysis tests
- [x] 7.6 Run Python compile checks for touched files
- [x] 7.7 Run `openspec validate viewer-task-segmentation-panel --strict`
- [x] 7.8 Manually verify the task segmentation panel against one realistic session using the local viewer server
