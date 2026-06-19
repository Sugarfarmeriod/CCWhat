'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const html = fs.readFileSync(path.join(__dirname, '..', 'viewer', 'claude-log.html'), 'utf8');

function assertContains(needle, message) {
  assert.ok(html.includes(needle), message || `missing ${needle}`);
}

function assertNotContains(needle, message) {
  assert.ok(!html.includes(needle), message || `unexpected ${needle}`);
}

function functionBody(name) {
  const marker = `function ${name}(`;
  const start = html.indexOf(marker);
  assert.notStrictEqual(start, -1, `missing function ${name}`);
  const bodyStart = html.indexOf('{', start);
  let depth = 0;
  for (let i = bodyStart; i < html.length; i++) {
    if (html[i] === '{') depth++;
    if (html[i] === '}') depth--;
    if (depth === 0) return html.slice(bodyStart + 1, i);
  }
  throw new Error(`unterminated function ${name}`);
}

function testSearchEntryAndDefaultScope() {
  assertNotContains('data-page="search"', 'Search should not be a left-nav page');
  assertContains('id="globalSearchWrap"', 'Top search wrapper should exist');
  assertContains('id="searchBox"', 'Top search input should exist');
  assertContains('onkeydown="onTopSearchKeydown(event)"', 'Top search should run scoped search on Enter');
  assertContains('id="globalSearchScope"', 'Scope selector should exist');
  assertContains('id="globalSearchToggleBtn"', 'Search results toggle should exist');
  assertContains('id="globalSearchPopover"', 'Search results popover should exist');
  assertContains('id="globalSearchClearBtn"', 'Clear/Stop button should exist');
  assertContains('global-search-actions', 'Clear/Stop should sit beside Fold result in the popover');
  assertContains('.global-search-clear-btn { display: none;', 'Clear/Stop should be hidden when not searching');
  assertContains('id="globalSearchLayout"', 'Search results should use grouped columns');
  assertContains('id="globalSearchProjects"', 'Grouped search should render projects first');
  assertContains('id="globalSearchSessions"', 'Grouped search should render sessions after project selection');
  assertContains('id="globalSearchResults"', 'Grouped search should render result details after session selection');
  assertContains('Fold result', 'Expanded results should expose an in-popover fold control');
  assertContains('Unfold result', 'Folded results should replace the search controls with an unfold button');
  assertContains('position: relative; z-index: 200;', 'Topbar should layer above the workspace');
  assertContains('z-index: 220;', 'Search popover should have an explicit high layer');
  assertContains('<option value="current_session">Current session</option>', 'Current session should be first/default option');
  assertContains('<option value="current_project">Current project</option>', 'Current project scope should be offered');
  assertContains('<option value="all_projects">All projects</option>', 'All projects scope should be offered');
  assertNotContains("case 'search': renderGlobalSearchState(); break;", 'Search should not be routed as a standalone page');
}

function testSearchRequestUsesExplicitScope() {
  const body = functionBody('runGlobalSearch');
  assert.ok(body.includes("document.getElementById('searchBox')"), 'runGlobalSearch should use top search input');
  assert.ok(body.includes('setGlobalSearchPopoverOpen(true)'), 'Search button should open the popover immediately');
  assert.ok(body.includes('globalSearchState.renderId ='), 'new searches should invalidate in-flight old searches');
  assert.ok(body.includes("scopeEl?.value || 'current_session'"), 'runGlobalSearch should default to current_session');
  assert.ok(body.includes("new URLSearchParams({ q: query, scope, limit: '50' })"), 'scope should be sent to /api/search');
  assert.ok(body.includes("params.set('session', sessionId)"), 'session id should be included when available');
  assert.ok(body.includes("params.set('project', projectDir)"), 'project should be included when available');
  assert.ok(body.includes('/api/search?'), 'runGlobalSearch should call the backend search API');
}

function testResultRenderingAndNavigationHooks() {
  const rowBody = functionBody('makeGlobalSearchResultRow');
  assert.ok(rowBody.includes("row.className = 'global-search-result'"), 'results should render as clickable rows');
  assert.ok(rowBody.includes('row.dataset.sessionId'), 'result rows should expose session id');
  assert.ok(rowBody.includes('row.dataset.resultType'), 'result rows should expose result type');
  assert.ok(rowBody.includes('navigateToGlobalSearchResult(result)'), 'result rows should navigate on click');
  assertContains('function globalSearchResultTitle(result)', 'results should use readable titles');
  assertContains('function globalSearchResultSource(result)', 'results should show project/session source');
  assertContains('global-search-source', 'project/source should have visible styling');
  assertContains('-webkit-line-clamp: 3', 'long snippets should be visually clamped');
  assertContains('position: fixed; top: 36px; left: 50%; transform: translateX(-50%); width: min(920px, calc(100vw - 24px));', 'popover should remain bounded inside the viewport');
  assertContains('max-height: min(520px, calc(100vh - 90px))', 'popover should not expand into a full-page panel');
  assertContains('max-height: 112px', 'result rows should have a bounded height');
  assertContains('flex: 0 0 auto', 'result rows should not overlap inside the flex column');
  assertContains('overflow-x: hidden', 'search popover should not show horizontal scrolling');
  assertContains('grid-template-columns: auto 1fr', 'result header should use stable rows/columns');
  assertContains('overflow-wrap: anywhere', 'long snippets should not expand card width');
  assertContains('function compactSearchText(value, maxLen)', 'visible result text should be hard-truncated');
  assertContains('function renderGlobalSearchHierarchy()', 'results should be grouped by project/session');
  assertContains('function toggleGlobalSearchPopover()', 'results popover should be collapsible');
  assertContains('function collapseGlobalSearchPopover()', 'selecting a result should collapse the popover');
  assertContains('id="globalSearchSpinner"', 'search status should have a spinner beside the text');
  assertContains('id="globalSearchTypeFilters"', 'results should expose type filters');
  assertContains('value="session" onchange="onGlobalSearchTypeFilterChange()"', 'session results should be optional, not default');
  assertContains("spinner.style.display = globalSearchState.inFlight ? 'inline-block' : 'none'", 'spinner should only show while searching');
  assertContains('scope-current-project', 'current project scope should use a two-column layout');
  assertContains('scope-current-session', 'current session scope should use a one-column layout');
  assertContains("wrap.classList.toggle('folded'", 'folded results should replace search controls in the top bar');
  assertContains("clearBtn.classList.toggle('visible', !!globalSearchState.inFlight)", 'Clear/Stop visibility should follow active search state');
  assertContains('function syncGlobalSearchTopSelectors(projectDir, sessionId)', 'group/result selection should sync top project/session selectors');
  assertContains('function clearOrStopGlobalSearch()', 'search should support clear/stop');
  assertContains('function selectedGlobalSearchTypes()', 'result type filters should be multi-select');
  assertContains("typeFilters: new Set(['task', 'turn', 'event'])", 'session results should be hidden by default');
  assertContains('if (!globalSearchTypeAllowed(result)) continue;', 'grouping should respect result type filters');
  assertContains('userCollapsed', 'manual folding should be tracked while search continues');
  assertContains('!globalSearchState.userCollapsed', 'new results should not automatically reopen a manually folded popover');
  assertContains('function clientTaskSearchResultsForSessions(query, allowed)', 'client-side task search should support explicit sessions');
  assertContains('userIntent: task.userIntent', 'manual/edited task names should be searchable');
  assertContains('const wasSelected = globalSearchState.selectedSession === sessionId', 'clicking a selected session should clear the filter');
  assertContains('const resultSessions = session ? [session] : sessions', 'results should show all session results when no session is selected');
  assertContains('loadSession().catch', 'selecting a session group should start loading without blocking search UI');
  assertContains("document.addEventListener('click', event =>", 'outside clicks should collapse the popover');
  assertContains('event.composedPath', 'inside clicks should not be mistaken for outside clicks after rerender');
  assertContains('saveGlobalSearchScrollPositions()', 'collapsed results should preserve scroll position');
  assertContains('function runGlobalSearchAcrossSessions(query, scope, projectDir)', 'cross-session search should scan per session');
  assertContains("scope: 'current_session'", 'cross-session search should issue per-session API calls');
  assertContains('appendGlobalSearchResults(null, [', 'per-session results should update grouped state as each request finishes');
  assertContains('session(s) could not be read', 'read failures should be explained as unreadable sessions');

  const navBody = functionBody('navigateToGlobalSearchResult');
  assert.ok(navBody.includes('collapseGlobalSearchPopover()'), 'choosing a result should collapse the result popover');
  assert.ok(navBody.includes('await loadSession()'), 'navigation should reuse loadSession dirty-overlay guard');
  assert.ok(navBody.includes("navigateToPage('tasks')"), 'task result should navigate to Tasks');
  assert.ok(navBody.includes('selectTaskSegment(result.taskId, sessionId)'), 'task result should select task when available');
  assert.ok(navBody.includes('navigateToEventId(result.eventId)'), 'event/turn result should locate event');
  assert.ok(navBody.includes('lookupTurnByEventId(result.eventId)'), 'event/turn result should prefer Trace Tree navigation');
  assert.ok(navBody.includes('navigateToTurn(foundTurn.groupId, foundTurn.turn.turnKey)'), 'event/turn result should open the session trace tree when possible');
}

function testCachedTaskSourceSearch() {
  const body = functionBody('clientTaskSearchResultsForSessions');
  assert.ok(body.includes('activeTaskTraceData(sid) || taskSegmentReports[sid]'), 'cached task source should be searched');
  assert.ok(body.includes("type: 'task'"), 'cached task matches should render as task results');
  assert.ok(!body.includes('runTaskSegmentationForCurrentSession'), 'search must not auto-run task segmentation');
}

testSearchEntryAndDefaultScope();
testSearchRequestUsesExplicitScope();
testResultRenderingAndNavigationHooks();
testCachedTaskSourceSearch();
console.log('global session search DOM/static JS tests passed');
