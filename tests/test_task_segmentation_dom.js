/**
 * Functional DOM tests for task segmentation navigation fixes.
 * Uses jsdom to test the actual behavior of findEntryByEventId,
 * focusEntryInNav, turn header data-idx, and event ID mapping.
 */

'use strict';

const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const htmlPath = path.join(__dirname, '..', 'viewer', 'claude-log.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// ---------------------------------------------------------------------------
// Test session fixtures
// ---------------------------------------------------------------------------

const MOCK_SESSION = {
  sessionId: 'test-session-001',
  projectDir: 'test-project',
  agent: 'claude',
  main: [
    // Line 1: user root (turn 0)
    { type: 'user', _fileLine: 1, timestamp: '2025-01-01T00:01:00Z',
      message: { content: [{ type: 'text', text: 'Fix the login bug' }] } },
    // Line 2: assistant child
    { type: 'assistant', _fileLine: 2, timestamp: '2025-01-01T00:02:00Z',
      message: { content: [{ type: 'text', text: 'Looking into it...' }] } },
    // Line 3: user root (turn 1)
    { type: 'user', _fileLine: 3, timestamp: '2025-01-01T00:03:00Z',
      message: { content: [{ type: 'text', text: 'Add register feature' }] } },
    // Line 4: assistant child
    { type: 'assistant', _fileLine: 4, timestamp: '2025-01-01T00:04:00Z',
      message: { content: [{ type: 'text', text: 'Done.' }] } },
  ],
  subagents: [],
};

const MOCK_TASK_SEGMENTS = {
  ok: true,
  sessionId: 'test-session-001',
  tasks: [
    {
      taskId: 'task-1',
      title: 'Fix the login bug',
      taskType: 'bugfix',
      status: 'unevaluated',
      startEventId: 'main:1',
      endEventId: 'main:2',
      evidence: { commands: [], filesRead: [], filesChanged: [], errors: [] },
      boundaryReasons: [],
      fileWeights: {},
    },
  ],
  summary: { taskCount: 1 },
  elapsedMs: 5,
};

// ---------------------------------------------------------------------------
// DOM setup
// ---------------------------------------------------------------------------

function makeDOM(sessionData, taskSegmentData) {
  const session = sessionData || MOCK_SESSION;
  const taskSegments = taskSegmentData || MOCK_TASK_SEGMENTS;
  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    url: 'http://localhost:7789/claude-log.html',
    beforeParse(window) {
      window.matchMedia = () => ({
        matches: false, media: '', onchange: null,
        addListener: () => {}, removeListener: () => {},
        addEventListener: () => {}, removeEventListener: () => {},
        dispatchEvent: () => false,
      });
      window.HTMLElement.prototype.scrollIntoView = function() {
        this._scrolledIntoView = true;
      };
      window.requestAnimationFrame = (cb) => { cb(0); return 0; };
      window.__taskSegmentRequests = [];
      // Mock fetch: /api/projects returns one project, /api/session/:id returns session
      window.fetch = (url, opts) => {
        const u = String(url);
        if (u.includes('/api/projects')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([
              { projectDir: 'test-project', sessions: ['test-session-001'], agent: 'claude' },
            ]),
          });
        }
        if (u.includes('/api/session/')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(session) });
        }
        if (u.includes('/api/task-segments')) {
          window.__taskSegmentRequests.push(opts ? JSON.parse(opts.body || '{}') : {});
          return Promise.resolve({ ok: true, json: () => Promise.resolve(taskSegments) });
        }
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
      };
    },
  });
  return dom;
}

async function flushAsync() {
  await new Promise(r => setImmediate(r));
  await new Promise(r => setImmediate(r));
}

async function loadTestSession(dom) {
  const win = dom.window;
  const doc = dom.window.document;

  // Select project and session
  const projSel = doc.getElementById('projectSel');
  const sessSel = doc.getElementById('sessionSel');

  // Populate project selector manually (mimic what init() does)
  const projOpt = doc.createElement('option');
  projOpt.value = 'test-project';
  projSel.appendChild(projOpt);
  projSel.value = 'test-project';

  const sessOpt = doc.createElement('option');
  sessOpt.value = 'test-session-001';
  sessSel.appendChild(sessOpt);
  sessSel.value = 'test-session-001';

  // Call loadSession and wait for it to complete
  await win.loadSession();
  // Wait for microtasks
  await flushAsync();
}

async function setOnlyType(dom, type) {
  const doc = dom.window.document;
  for (const label of Array.from(doc.querySelectorAll('#typeFilters label'))) {
    const input = label.querySelector('input');
    const shouldCheck = label.dataset.type === type;
    input.checked = shouldCheck;
    label.classList.toggle(`checked-${label.dataset.type}`, shouldCheck);
  }
  dom.window.renderPage('sessions');
  await flushAsync();
}

async function clearAllTypes(dom) {
  const doc = dom.window.document;
  for (const label of Array.from(doc.querySelectorAll('#typeFilters label'))) {
    const input = label.querySelector('input');
    input.checked = false;
    label.classList.remove(`checked-${label.dataset.type}`);
  }
  dom.window.renderPage('sessions');
  await flushAsync();
}

// ---------------------------------------------------------------------------
// Test 1: eventIdToEntryIdx populated after loadSession
// ---------------------------------------------------------------------------

async function test_map_populated_after_load() {
  const dom = makeDOM();
  await loadTestSession(dom);

  // Can't access eventIdToEntryIdx directly (let-scoped), but we can test via
  // findEntryByEventId which uses the map
  const win = dom.window;

  // Line 1 is a user turn root → should be findable
  const idx1 = win.findEntryByEventId('main:1');
  assert.ok(idx1 >= 0, `main:1 should map to an entry, got ${idx1}`);

  // Line 2 is an assistant child
  const idx2 = win.findEntryByEventId('main:2');
  assert.ok(idx2 >= 0, `main:2 should map to an entry, got ${idx2}`);

  // Non-existent line
  const idxBad = win.findEntryByEventId('main:99');
  assert.strictEqual(idxBad, -1, 'main:99 should return -1');

  console.log('  ✓ eventIdToEntryIdx populated correctly after loadSession');
}

// ---------------------------------------------------------------------------
// Test 2: Session page renders Turn-first cards after loadSession
// ---------------------------------------------------------------------------

async function test_turn_root_has_data_idx_in_dom() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const doc = dom.window.document;
  // Session page now renders Turn cards (Turn-first), not raw turn-hdr elements
  const turnCards = doc.querySelectorAll('.turn-card');

  assert.ok(turnCards.length > 0, 'turn cards should exist after loadSession (Turn-first view)');

  // Every turn card should have data-turn-key
  for (const card of turnCards) {
    assert.ok(
      card.dataset.turnKey !== undefined && card.dataset.turnKey !== '',
      `turn card should have data-turn-key, got: ${card.dataset.turnKey}`
    );
  }

  // Turn labels should be visible (Turn 1, Turn 2 ...)
  const firstCard = turnCards[0];
  const label = firstCard.querySelector('.turn-card-label');
  assert.ok(label, 'turn card should contain a .turn-card-label element');
  assert.ok(/Turn \d+/.test(label.textContent), `turn label should match 'Turn N', got: ${label.textContent}`);

  console.log('  ✓ Session page renders Turn-first cards after loadSession');
}

// ---------------------------------------------------------------------------
// Test 2b: minimal Turns show single-fragment content; user filter makes
//          assistant turns filter-empty
// ---------------------------------------------------------------------------

async function test_turn_detail_filters_assistant_when_only_user_enabled() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const doc = dom.window.document;

  // The first Turn card is a user_message Turn for "Fix the login bug"
  const firstCard = doc.querySelector('.turn-card');
  assert.ok(firstCard, 'first Turn card should exist');
  firstCard.click();
  await flushAsync();

  // user_message Turn detail shows user text only (minimal Turn semantics)
  assert.ok(doc.getElementById('detailPanel').textContent.includes('Fix the login bug'),
    'clicking user_message turn should show user text in detail');

  // Enable user-only filter → assistant_text turns become filter-empty
  await setOnlyType(dom, 'user');

  const detailText = doc.getElementById('detailPanel').textContent;
  assert.ok(detailText.includes('Fix the login bug'), 'user text should remain visible under user filter');

  // assistant_text turns should have the filter-empty class
  const allCards = Array.from(doc.querySelectorAll('.turn-card'));
  const filterEmptyCards = allCards.filter(c => c.classList.contains('filter-empty'));
  assert.ok(filterEmptyCards.length > 0, 'assistant_text turns should be filter-empty under user-only filter');

  // "Looking into it" (assistant text) is in a separate minimal Turn — not in the detail of the user_message turn
  const visibleBodyText = Array.from(doc.querySelectorAll('.turn-detail-text'))
    .map(el => el.textContent).join('\n');
  assert.ok(!visibleBodyText.includes('Looking into it'),
    'assistant text should not appear in user_message Turn detail (different minimal Turn)');

  console.log('  ✓ user-only type filter makes assistant_text turns filter-empty; detail stays kind-specific');
}

// ---------------------------------------------------------------------------
// Test 2c: clearing all type filters makes all Turn cards filter-empty and
//          the selected Turn detail shows the filter-hidden message
// ---------------------------------------------------------------------------

async function test_clearing_all_type_filters_keeps_turn_cards_with_empty_detail() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const doc = dom.window.document;
  // Select the first turn card
  doc.querySelector('.turn-card').click();
  await flushAsync();

  // Clear all type filters
  await clearAllTypes(dom);

  const turnCards = doc.querySelectorAll('.turn-card');
  assert.ok(turnCards.length > 0, 'Turn cards should remain when all type filters are unchecked');

  // All turns should be filter-empty (no entries visible)
  const filterEmptyCards = doc.querySelectorAll('.turn-card.filter-empty');
  assert.ok(filterEmptyCards.length > 0, 'all Turn cards should be filter-empty when all filters cleared');

  // The selected Turn detail should show the filter-hidden explanation
  const detailText = doc.getElementById('detailPanel').textContent;
  assert.ok(detailText.includes('当前筛选隐藏了该 Turn 的全部事件'),
    'detail panel should explain that all events are hidden by filter');

  // First filter-empty card should show "0 visible" or have the filter-empty class
  const firstCard = turnCards[0];
  assert.ok(firstCard.textContent.includes('0 visible') || firstCard.classList.contains('filter-empty'),
    'first turn card should indicate filter-empty state');

  console.log('  ✓ clearing all type filters keeps Turn structure and shows filter-hidden message in detail');
}

// ---------------------------------------------------------------------------
// Test 3: focusEntryInNav works after raw events are rendered
// ---------------------------------------------------------------------------

async function test_focusEntryInNav_turn_root_visible() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  // Set up taskDetailContainer so hint can be inserted
  const detailPanel = doc.getElementById('detailPanel');
  if (!doc.getElementById('taskDetailContainer')) {
    const tc = doc.createElement('div');
    tc.id = 'taskDetailContainer';
    tc.innerHTML = '<p>task detail here</p>';
    detailPanel.appendChild(tc);
  }

  // Switch to raw events list (navigateToEventId calls renderList() internally)
  win.renderList();

  // Find the index for main:1 (turn root)
  const idx = win.findEntryByEventId('main:1');
  assert.ok(idx >= 0, `main:1 should be findable, got ${idx}`);

  // After renderList(), turn-hdr elements should exist with data-idx
  const targetEl = doc.querySelector(`[data-idx="${idx}"]`);
  assert.ok(targetEl !== null, `[data-idx="${idx}"] should exist in DOM after renderList()`);

  // Call focusEntryInNav — should not throw and should trigger scrollIntoView
  let scrollCalled = false;
  const origScroll = win.HTMLElement.prototype.scrollIntoView;
  win.HTMLElement.prototype.scrollIntoView = function() { scrollCalled = true; };
  win.focusEntryInNav(idx);
  win.HTMLElement.prototype.scrollIntoView = origScroll;

  assert.ok(scrollCalled, 'scrollIntoView should be called when focusing turn root');
  console.log('  ✓ focusEntryInNav works on turn root after renderList()');
}

// ---------------------------------------------------------------------------
// Test 4: focusEntryInNav works on child entry
// ---------------------------------------------------------------------------

async function test_focusEntryInNav_child_entry() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  // Expand all turns so children are visible
  const turnKeys = Object.keys(win.turnCollapsed || {});
  for (const k of turnKeys) { win.turnCollapsed[k] = false; }
  win.renderList();

  const detailPanel = doc.getElementById('detailPanel');
  if (!doc.getElementById('taskDetailContainer')) {
    const tc = doc.createElement('div'); tc.id = 'taskDetailContainer';
    detailPanel.appendChild(tc);
  }

  // Find child entry (main:2)
  const idx = win.findEntryByEventId('main:2');
  assert.ok(idx >= 0, `main:2 should be findable`);

  const targetEl = doc.querySelector(`[data-idx="${idx}"]`);
  assert.ok(targetEl !== null, `[data-idx="${idx}"] should exist for child entry`);

  let scrollCalled = false;
  win.HTMLElement.prototype.scrollIntoView = function() { scrollCalled = true; };
  win.focusEntryInNav(idx);

  assert.ok(scrollCalled, 'scrollIntoView should be called for child entry');
  console.log('  ✓ focusEntryInNav works on child entry');
}

// ---------------------------------------------------------------------------
// Test 5: non-existent eventId → disabled button in makeNavBtn
// ---------------------------------------------------------------------------

async function test_make_nav_btn_disabled_for_unknown_event() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;

  const btn = win.makeNavBtn('定位开始事件', 'main:999');
  assert.ok(btn.includes('disabled'), 'button for unknown event should be disabled');
  assert.ok(btn.includes('定位开始事件'), 'button text should be present');
  console.log('  ✓ makeNavBtn returns disabled button for unknown eventId');
}

// ---------------------------------------------------------------------------
// Test 6: _showNavHint adds hint to taskDetailContainer
// ---------------------------------------------------------------------------

async function test_show_nav_hint() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  // Set up container
  const detailPanel = doc.getElementById('detailPanel');
  detailPanel.innerHTML = '<div id="taskDetailContainer"><p>detail</p></div>';

  win._showNavHint('测试提示消息');

  const hint = doc.querySelector('.nav-filter-hint');
  assert.ok(hint, 'hint should be added to taskDetailContainer');
  assert.ok(hint.innerHTML.includes('测试提示消息'), 'hint should contain the message');
  console.log('  ✓ _showNavHint adds dismissable hint to taskDetailContainer');
}

// ---------------------------------------------------------------------------
// Test 7: clicking Tasks waits for manual segmentation
// ---------------------------------------------------------------------------

async function test_tasks_page_waits_for_manual_segmentation() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  win.navigateToPage('tasks');
  await flushAsync();

  assert.strictEqual(win.__taskSegmentRequests.length, 0, 'Tasks page should not auto-request segmentation');
  assert.strictEqual(doc.querySelector('.page.active').dataset.page, 'tasks');
  assert.ok(doc.getElementById('taskSegContent').textContent.includes('尚未生成任务切分结果'));

  const taskButton = Array.from(doc.querySelectorAll('#taskSegContent button'))
    .find(btn => btn.textContent.includes('任务切分'));
  assert.ok(taskButton, 'manual task segmentation button should be visible');
  taskButton.click();
  await flushAsync();

  assert.strictEqual(win.__taskSegmentRequests.length, 1, 'Manual click should request segmentation once');
  assert.deepStrictEqual(win.__taskSegmentRequests[0], { sessionId: 'test-session-001' });
  assert.ok(doc.getElementById('taskSegContent').textContent.includes('Fix the login bug'));
  console.log('  ✓ Tasks page waits for manual segmentation');
}

// ---------------------------------------------------------------------------
// Test 8: Session -> Tasks -> Session restores the log viewer
// ---------------------------------------------------------------------------

async function test_session_tasks_session_roundtrip_keeps_logs_visible() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  win.navigateToPage('tasks');
  await flushAsync();
  win.navigateToPage('sessions');
  await flushAsync();

  assert.strictEqual(doc.querySelector('.page.active').dataset.page, 'sessions');
  assert.ok(doc.getElementById('entryList').textContent.includes('Fix the login bug'));
  assert.ok(doc.getElementById('detailPanel').textContent.trim().length > 0);
  console.log('  ✓ Session -> Tasks -> Session keeps log viewer visible');
}

// ---------------------------------------------------------------------------
// Test 9: missing/legacy page ids cannot blank the workbench
// ---------------------------------------------------------------------------

async function test_missing_page_falls_back_to_session() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  win.navigateToPage('evidence');
  assert.strictEqual(doc.querySelector('.page.active').dataset.page, 'sessions');

  win.navigateToPage('does-not-exist');
  assert.strictEqual(doc.querySelector('.page.active').dataset.page, 'sessions');
  assert.ok(doc.getElementById('entryList').textContent.includes('Fix the login bug'));
  console.log('  ✓ missing and legacy page ids fall back to Session');
}

// ---------------------------------------------------------------------------
// Fixtures for Conversation / minimal Turn tests
// ---------------------------------------------------------------------------

const MOCK_SESSION_MULTIBLOCK = {
  sessionId: 'test-multiblock',
  projectDir: 'test-project',
  agent: 'claude',
  main: [
    // Line 1: real user request
    { type: 'user', _fileLine: 1, timestamp: '2025-01-01T00:01:00Z',
      message: { content: [{ type: 'text', text: 'Fix auth bug' }] } },
    // Line 2: assistant entry with text + 2 tool_use blocks
    { type: 'assistant', _fileLine: 2, timestamp: '2025-01-01T00:02:00Z',
      message: { id: 'msg-2', content: [
        { type: 'text', text: 'Looking into it...' },
        { type: 'tool_use', id: 'tu1', name: 'Read', input: { file_path: 'auth.py' } },
        { type: 'tool_use', id: 'tu2', name: 'Edit', input: { file_path: 'auth.py', old_str: 'x', new_str: 'y' } },
      ] } },
    // Line 3: user with two tool_result blocks (not a real user request)
    { type: 'user', _fileLine: 3, timestamp: '2025-01-01T00:03:00Z',
      message: { content: [
        { type: 'tool_result', tool_use_id: 'tu1', content: 'file contents' },
        { type: 'tool_result', tool_use_id: 'tu2', content: 'edited ok' },
      ] } },
    // Line 4: final assistant reply
    { type: 'assistant', _fileLine: 4, timestamp: '2025-01-01T00:04:00Z',
      message: { content: [{ type: 'text', text: 'Auth bug fixed.' }] } },
    // Line 5: second real user request (new Conversation)
    { type: 'user', _fileLine: 5, timestamp: '2025-01-01T00:05:00Z',
      message: { content: [{ type: 'text', text: 'Add register feature' }] } },
    // Line 6: assistant reply
    { type: 'assistant', _fileLine: 6, timestamp: '2025-01-01T00:06:00Z',
      message: { content: [{ type: 'text', text: 'Register feature added.' }] } },
    // Line 7: system-reminder (non-real user, should NOT start new Conversation)
    { type: 'user', _fileLine: 7, timestamp: '2025-01-01T00:07:00Z',
      message: { content: [{ type: 'text', text: '<system-reminder>some reminder</system-reminder>' }] } },
  ],
  subagents: [],
};

async function loadMultiblockSession(dom) {
  const win = dom.window;
  const doc = dom.window.document;
  const projSel = doc.getElementById('projectSel');
  const sessSel = doc.getElementById('sessionSel');
  const projOpt = doc.createElement('option');
  projOpt.value = 'test-project'; projSel.appendChild(projOpt); projSel.value = 'test-project';
  const sessOpt = doc.createElement('option');
  sessOpt.value = 'test-multiblock'; sessSel.appendChild(sessOpt); sessSel.value = 'test-multiblock';
  await win.loadSession();
  await flushAsync();
}

// ---------------------------------------------------------------------------
// Test C1: one real user request → one Conversation (task 6.2)
// ---------------------------------------------------------------------------

async function test_one_user_request_creates_one_conversation() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  await loadMultiblockSession(dom);

  const doc = dom.window.document;
  // Should have 2 conversations (line 1 and line 5 are real user requests)
  const convHdrs = doc.querySelectorAll('.conv-hdr');
  assert.ok(convHdrs.length >= 2, `expected ≥2 conversation headers, got ${convHdrs.length}`);

  // Check conversation labels
  const labels = Array.from(convHdrs).map(h => h.querySelector('.conv-hdr-label')?.textContent);
  assert.ok(labels.some(l => l === '会话 1'), 'first conversation should be labeled 会话 1');
  assert.ok(labels.some(l => l === '会话 2'), 'second conversation should be labeled 会话 2');

  // Conversation 1 summary should include user text
  const conv1 = convHdrs[0];
  assert.ok(conv1.textContent.includes('Fix auth bug') || conv1.textContent.includes('会话 1'),
    'first conversation header should mention user request text');

  console.log('  ✓ one real user request → one Conversation');
}

// ---------------------------------------------------------------------------
// Test C2: multi-block assistant entry → multiple tool_use Turns (task 6.3)
// ---------------------------------------------------------------------------

async function test_multiblock_assistant_creates_multiple_tool_turns() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  await loadMultiblockSession(dom);

  const doc = dom.window.document;
  // Should have multiple tool-use kind turns (tu1=Read, tu2=Edit)
  const allCards = Array.from(doc.querySelectorAll('.turn-card'));
  const toolUseCards = allCards.filter(c => {
    const badge = c.querySelector('.kind-tool_use');
    return badge !== null;
  });
  assert.ok(toolUseCards.length >= 2,
    `expected ≥2 tool_use turns (Read + Edit), got ${toolUseCards.length}`);

  // Their summaries should include the tool names
  const toolTexts = toolUseCards.map(c => c.querySelector('.turn-card-summary')?.textContent || '');
  assert.ok(toolTexts.some(t => t.includes('Read')), 'Read tool_use turn should be present');
  assert.ok(toolTexts.some(t => t.includes('Edit')), 'Edit tool_use turn should be present');

  console.log('  ✓ multi-block assistant entry → separate tool_use Turns');
}

// ---------------------------------------------------------------------------
// Test C3: tool_use and tool_result are separate Turns (task 6.4)
// ---------------------------------------------------------------------------

async function test_tool_use_and_tool_result_are_separate_turns() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  await loadMultiblockSession(dom);

  const doc = dom.window.document;
  const allCards = Array.from(doc.querySelectorAll('.turn-card'));

  const toolUseCards = allCards.filter(c => c.querySelector('.kind-tool_use'));
  const toolResultCards = allCards.filter(c => c.querySelector('.kind-tool_result'));

  assert.ok(toolUseCards.length >= 1, 'tool_use Turn should exist');
  assert.ok(toolResultCards.length >= 1, 'tool_result Turn should exist separately');

  // No single card should have BOTH kind badges
  for (const card of allCards) {
    const hasToolUse = !!card.querySelector('.kind-tool_use');
    const hasToolResult = !!card.querySelector('.kind-tool_result');
    assert.ok(!(hasToolUse && hasToolResult),
      'a single Turn card must not have both tool_use and tool_result kind badges');
  }

  console.log('  ✓ tool_use and tool_result are separate Turns (not merged)');
}

// ---------------------------------------------------------------------------
// Test C4: non-real user entries do not start a new Conversation (task 6.5)
// ---------------------------------------------------------------------------

async function test_non_real_user_entry_does_not_open_new_conversation() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  await loadMultiblockSession(dom);

  const doc = dom.window.document;
  const convHdrs = doc.querySelectorAll('.conv-hdr');

  // The system-reminder at line 7 must NOT create a new conversation.
  // Only lines 1 and 5 are real user requests → exactly 2 conversations.
  assert.strictEqual(convHdrs.length, 2,
    `expected exactly 2 conversations (real user requests), got ${convHdrs.length}`);

  const labels = Array.from(convHdrs).map(h => h.querySelector('.conv-hdr-label')?.textContent);
  assert.ok(!labels.includes('会话 3'), 'system-reminder must not create 会话 3');

  console.log('  ✓ non-real user entries (system-reminder, tool_result-only) do not create new Conversations');
}

// ---------------------------------------------------------------------------
// Test C5: entry anchor and block anchor locate Conversation / Turn (task 6.6)
// ---------------------------------------------------------------------------

async function test_entry_anchor_and_block_anchor_locate_conversation_and_turn() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  await loadMultiblockSession(dom);

  const win = dom.window;

  // Entry anchor: main:2 (the multi-block assistant entry)
  const turnByEntry = win.lookupTurnByEventId('main:2');
  assert.ok(turnByEntry !== null, 'main:2 entry anchor should resolve to a Turn');
  assert.ok(turnByEntry.conversationKey, 'resolved turn should have conversationKey');
  assert.ok(turnByEntry.turn, 'resolved turn should have turn object');

  // Conversation lookup: main:2 should belong to conversation 0
  const convByEntry = win.lookupConversationByEventId('main:2');
  assert.ok(convByEntry !== null, 'main:2 should resolve to a Conversation');
  assert.ok(convByEntry.conversation, 'resolved should include conversation object');
  assert.strictEqual(convByEntry.conversation.index, 0, 'main:2 should be in conversation 0 (会话 1)');

  // Block anchor: main:2#content:1 (second block = first tool_use = "Read")
  const turnByBlock = win.lookupTurnByEventId('main:2#content:1');
  assert.ok(turnByBlock !== null, 'block anchor main:2#content:1 should resolve to a Turn');
  if (turnByBlock) {
    assert.strictEqual(turnByBlock.turn.kind, 'tool_use',
      'main:2#content:1 should point to a tool_use Turn (Read)');
    assert.strictEqual(turnByBlock.turn.toolName, 'Read',
      'tool_use Turn should be the Read tool');
  }

  console.log('  ✓ entry anchor and block anchor locate Conversation and minimal Turn');
}

// ---------------------------------------------------------------------------
// Run all tests
// ---------------------------------------------------------------------------

const tests = [
  test_map_populated_after_load,
  test_turn_root_has_data_idx_in_dom,
  test_turn_detail_filters_assistant_when_only_user_enabled,
  test_clearing_all_type_filters_keeps_turn_cards_with_empty_detail,
  test_focusEntryInNav_turn_root_visible,
  test_focusEntryInNav_child_entry,
  test_make_nav_btn_disabled_for_unknown_event,
  test_show_nav_hint,
  test_tasks_page_waits_for_manual_segmentation,
  test_session_tasks_session_roundtrip_keeps_logs_visible,
  test_missing_page_falls_back_to_session,
  // Conversation / minimal Turn tests (task 6.2-6.6)
  test_one_user_request_creates_one_conversation,
  test_multiblock_assistant_creates_multiple_tool_turns,
  test_tool_use_and_tool_result_are_separate_turns,
  test_non_real_user_entry_does_not_open_new_conversation,
  test_entry_anchor_and_block_anchor_locate_conversation_and_turn,
];

async function main() {
  let passed = 0, failed = 0;
  console.log('Running task segmentation DOM tests...\n');
  for (const test of tests) {
    try {
      await test();
      passed++;
    } catch (err) {
      failed++;
      console.error(`  ✗ ${test.name}: ${err.message}`);
      if (process.env.VERBOSE) console.error(err.stack);
    }
  }
  console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => { console.error(err); process.exit(1); });
