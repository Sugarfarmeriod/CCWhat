## ADDED Requirements

### Requirement: Turn View Mode Projection
Claude Log Viewer SHALL provide a frontend data projection layer for Trace view modes without modifying the underlying minimal Turn data.

#### Scenario: Build default projection
- **WHEN** a session has loaded Conversation and minimal Turn data
- **THEN** the viewer SHALL be able to build a `default` view projection
- **AND** the projection SHALL contain only primary Step nodes
- **AND** the projection SHALL preserve group, conversation, task, turn and anchor references for every visible Step

#### Scenario: Build debug projection
- **WHEN** a session has loaded Conversation and minimal Turn data
- **THEN** the viewer SHALL be able to build a `debug` view projection
- **AND** the projection SHALL contain every minimal Turn in original order
- **AND** the projection SHALL preserve group, conversation, task, turn and anchor references for every Turn

#### Scenario: Projection does not mutate minimal Turns
- **WHEN** the viewer builds either `default` or `debug` projection
- **THEN** the underlying minimal Turn objects SHALL NOT be mutated with view-only labels or visibility fields
- **AND** repeated projection builds SHALL produce stable labels and references

### Requirement: Default View Primary Classification
Claude Log Viewer SHALL classify user-visible execution steps as primary in the default view.

#### Scenario: User message is primary
- **WHEN** a minimal Turn kind is `user_message`
- **THEN** default projection SHALL include it as a primary Step
- **AND** its display kind SHALL indicate user request

#### Scenario: Thinking is primary and complete
- **WHEN** a minimal Turn kind is `thinking` or equivalent reasoning content
- **THEN** default projection SHALL include it as a primary Step
- **AND** the Step SHALL preserve the full underlying thinking content
- **AND** the Step SHALL NOT be summarized, weakened, folded into internal events, or hidden by default

#### Scenario: Assistant text is primary
- **WHEN** a minimal Turn kind is `assistant_text`
- **THEN** default projection SHALL include it as a primary Step
- **AND** its display kind SHALL indicate Agent reply

#### Scenario: Tool use and tool result are primary
- **WHEN** a minimal Turn kind is `tool_use` or `tool_result`
- **THEN** default projection SHALL include it as a primary Step
- **AND** tool errors SHALL remain primary

#### Scenario: Execution-affecting permission is primary
- **WHEN** a permission-related Turn represents a request, approval, denial, waiting state, or execution-affecting permission change
- **THEN** default projection SHALL include it as a primary Step

### Requirement: Default View Internal Classification
Claude Log Viewer SHALL hide ordinary internal runtime events from the default projection while keeping them available in debug projection.

#### Scenario: Ordinary system is internal
- **WHEN** a minimal Turn represents ordinary system prompt injection or stable system context
- **THEN** default projection SHALL classify it as internal and omit it from primary Steps
- **AND** debug projection SHALL still include it in original order

#### Scenario: Ordinary context and hook are internal
- **WHEN** a minimal Turn represents ordinary context injection, `PostToolUse` hook, `last-prompt`, or equivalent internal lifecycle event
- **THEN** default projection SHALL classify it as internal and omit it from primary Steps
- **AND** debug projection SHALL still include it in original order

#### Scenario: Ordinary snapshots and queue events are internal
- **WHEN** a minimal Turn represents ordinary `file-history-snapshot`, `queue-operation`, attachment metadata, or ordinary unknown internal event
- **THEN** default projection SHALL classify it as internal and omit it from primary Steps
- **AND** debug projection SHALL still include it in original order

#### Scenario: Error-like internal event is promoted
- **WHEN** an otherwise internal Turn contains clear error, warning, failed, denied, rejected, blocked, or permission-impacting content
- **THEN** default projection SHALL promote it to primary
- **AND** the projection SHALL preserve the full underlying Turn content

### Requirement: View Labels
Claude Log Viewer SHALL use different display labels for default Step projection and debug Turn projection.

#### Scenario: Default labels are continuous Step labels
- **WHEN** default projection is built for a conversation or task range
- **THEN** visible nodes SHALL be labeled `Step 1`, `Step 2`, `Step 3`, and so on within their display scope
- **AND** hidden internal Turns SHALL NOT create gaps in Step numbering

#### Scenario: Debug labels preserve Turn labels
- **WHEN** debug projection is built
- **THEN** visible nodes SHALL preserve the underlying Turn labels such as `Turn 1`, `Turn 2`, `Turn 3`
- **AND** debug projection SHALL NOT renumber after filtering out nothing

### Requirement: Projection Preserves Task and Conversation Boundaries
Claude Log Viewer SHALL preserve existing Task, Conversation and Turn boundaries when building view projections.

#### Scenario: Task range unchanged
- **WHEN** an active Task Trace Overlay or confirmed Task Trace covers a range of underlying Turns
- **THEN** default projection SHALL only hide internal Turns within that range
- **AND** debug projection SHALL include all underlying Turns within that range
- **AND** neither projection SHALL change Task start or end anchors

#### Scenario: Conversation range unchanged
- **WHEN** a Conversation contains both primary and internal Turns
- **THEN** default projection SHALL preserve the Conversation node and include its primary Steps
- **AND** debug projection SHALL preserve the Conversation node and include all Turns

#### Scenario: Empty default projection range
- **WHEN** a Task or Conversation contains no primary Steps in default projection
- **THEN** projection SHALL expose metadata indicating that no default-visible Steps exist
- **AND** debug projection SHALL still expose the underlying Turns

### Requirement: First Change Does Not Modify UI Rendering
This change SHALL only introduce projection data and tests; it SHALL NOT replace Trace tree UI or Detail rendering.

#### Scenario: Existing UI remains on old source
- **WHEN** this change is implemented
- **THEN** existing Trace tree rendering MAY continue to consume the previous data source
- **AND** the new projection SHALL be available for follow-up UI changes

#### Scenario: Detail unchanged
- **WHEN** this change is implemented
- **THEN** right-side Detail behavior SHALL remain unchanged
- **AND** full Detail evidence behavior SHALL be handled by a later change
