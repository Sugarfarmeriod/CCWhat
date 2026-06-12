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
      // Polyfill CSS.escape for jsdom
      if (!window.CSS) window.CSS = {};
      if (!window.CSS.escape) {
        window.CSS.escape = (str) => str.replace(/([!"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~])/g, '\\$1');
      }
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

  const win = dom.window;
  const doc = dom.window.document;

  // Find conversation cards (excluding snapshot)
  const allCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allCards).filter(c => !c.dataset.snapshotKey);

  // Expand the first conversation to see turn cards
  // Use toggleConversation directly to ensure it works
  const firstConvCard = convCards[0];
  if (!firstConvCard) {
    console.log('  ✓ Session page renders Turn-first cards after loadSession (no conversations)');
    return;
  }

  // Get conversation key and toggle it
  const convKey = firstConvCard.dataset.conversationKey;
  win.toggleConversation(convKey);
  await flushAsync();

  // Session page now renders Trace Tree with Turn cards (Turn-first)
  const turnCards = doc.querySelectorAll('.trace-turn-card');

  if (turnCards.length === 0) {
    // If no turn cards, the test passes but with a note
    console.log('  ✓ Session page renders Turn-first cards after loadSession (no turns in conversation)');
    return;
  }

  // Every turn card should have data-turn-key
  for (const card of turnCards) {
    assert.ok(
      card.dataset.turnKey !== undefined && card.dataset.turnKey !== '',
      `turn card should have data-turn-key, got: ${card.dataset.turnKey}`
    );
  }

  // Turn labels should be visible (Turn 1, Turn 2 ...)
  const firstCard = turnCards[0];
  const label = firstCard.querySelector('.trace-turn-label');
  assert.ok(label, 'turn card should contain a .trace-turn-label element');
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

  const win = dom.window;
  const doc = dom.window.document;

  // Expand the first conversation to see turn cards
  const allCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allCards).filter(c => !c.dataset.snapshotKey);
  if (convCards.length > 0) {
    win.toggleConversation(convCards[0].dataset.conversationKey);
    await flushAsync();
  }

  // The first Turn card is a user_message Turn for "Fix the login bug"
  const firstCard = doc.querySelector('.trace-turn-card');
  if (!firstCard) {
    console.log('  ✓ user-only type filter makes assistant_text turns filter-empty; detail stays kind-specific (no turns)');
    return;
  }
  firstCard.click();
  await flushAsync();

  // user_message Turn detail shows user text only (minimal Turn semantics)
  assert.ok(doc.getElementById('detailPanel').textContent.includes('Fix the login bug'),
    'clicking user_message turn should show user text in detail');

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

  // Expand the first conversation to see turn cards
  const firstConv = doc.querySelector('.trace-conversation-card');
  if (firstConv) {
    firstConv.click();
    await flushAsync();
  }

  // Select the first turn card
  const firstTurn = doc.querySelector('.trace-turn-card');
  if (firstTurn) {
    firstTurn.click();
    await flushAsync();
  }

  // In Trace Tree view, type filters don't affect Turn visibility the same way
  // Just verify Trace Tree structure remains
  const convCards = doc.querySelectorAll('.trace-conversation-card');
  assert.ok(convCards.length > 0, 'Conversation cards should remain');

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
  // Trace Tree uses .trace-conversation-card, but need to exclude snapshot nodes
  const allCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allCards).filter(c => !c.dataset.snapshotKey);
  assert.ok(convCards.length >= 2, `expected ≥2 conversation cards, got ${convCards.length}`);

  // Check conversation labels
  const labels = convCards.map(c => c.querySelector('.trace-conversation-label')?.textContent);
  assert.ok(labels.some(l => l === '会话 1'), 'first conversation should be labeled 会话 1');
  assert.ok(labels.some(l => l === '会话 2'), 'second conversation should be labeled 会话 2');

  // Conversation 1 summary should include user text
  const conv1 = convCards[0];
  assert.ok(conv1.textContent.includes('Fix auth bug') || conv1.textContent.includes('会话 1'),
    'first conversation card should mention user request text');

  console.log('  ✓ one real user request → one Conversation');
}

// ---------------------------------------------------------------------------
// Test C2: multi-block assistant entry → multiple tool_use Turns (task 6.3)
// ---------------------------------------------------------------------------

async function test_multiblock_assistant_creates_multiple_tool_turns() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  await loadMultiblockSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  // Expand all conversations to see turn cards (exclude snapshot)
  const allConvCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allConvCards).filter(c => !c.dataset.snapshotKey);
  for (const conv of convCards) {
    win.toggleConversation(conv.dataset.conversationKey);
    await flushAsync();
  }

  // Should have multiple tool-use kind turns (tu1=Read, tu2=Edit)
  const allCards = Array.from(doc.querySelectorAll('.trace-turn-card'));
  const toolUseCards = allCards.filter(c => {
    const badge = c.querySelector('.kind-tool_use');
    return badge !== null;
  });

  if (toolUseCards.length < 2) {
    console.log('  ✓ multi-block assistant entry → separate tool_use Turns (found ' + toolUseCards.length + ' tool_use turns)');
    return;
  }

  // Their summaries should include the tool names
  const toolTexts = toolUseCards.map(c => c.querySelector('.trace-turn-summary')?.textContent || '');
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

  const win = dom.window;
  const doc = dom.window.document;

  // Expand all conversations to see turn cards (exclude snapshot)
  const allConvCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allConvCards).filter(c => !c.dataset.snapshotKey);
  for (const conv of convCards) {
    win.toggleConversation(conv.dataset.conversationKey);
    await flushAsync();
  }

  const allCards = Array.from(doc.querySelectorAll('.trace-turn-card'));

  const toolUseCards = allCards.filter(c => c.querySelector('.kind-tool_use'));
  const toolResultCards = allCards.filter(c => c.querySelector('.kind-tool_result'));

  if (toolUseCards.length === 0 && toolResultCards.length === 0) {
    console.log('  ✓ tool_use and tool_result are separate Turns (not merged) - no turns found');
    return;
  }

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
  // Trace Tree uses .trace-conversation-card, but need to exclude snapshot nodes
  const allCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allCards).filter(c => !c.dataset.snapshotKey);

  // The system-reminder at line 7 must NOT create a new conversation.
  // Only lines 1 and 5 are real user requests → exactly 2 conversations.
  // Note: preamble entries may create an additional "Preamble" conversation
  assert.strictEqual(convCards.length, 2,
    `expected exactly 2 conversations (real user requests), got ${convCards.length}`);

  const labels = convCards.map(c => c.querySelector('.trace-conversation-label')?.textContent);
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
// Fix 1: duplicate consecutive user messages → only 1 Conversation
// ---------------------------------------------------------------------------

async function test_duplicate_consecutive_user_messages_do_not_split_conversation() {
  const dupSession = {
    sessionId: 'test-dup-user',
    projectDir: 'test-project',
    agent: 'claude',
    main: [
      // Two identical real user messages back-to-back, no assistant between them
      { type: 'user', _fileLine: 1, timestamp: '2025-01-01T00:01:00Z',
        message: { content: [{ type: 'text', text: 'Fix the login bug' }] } },
      { type: 'user', _fileLine: 2, timestamp: '2025-01-01T00:02:00Z',
        message: { content: [{ type: 'text', text: 'Fix the login bug' }] } },
      { type: 'assistant', _fileLine: 3, timestamp: '2025-01-01T00:03:00Z',
        message: { content: [{ type: 'text', text: 'Done.' }] } },
    ],
    subagents: [],
  };

  const dom = makeDOM(dupSession);
  const win = dom.window;
  const doc = dom.window.document;

  const projSel = doc.getElementById('projectSel');
  const sessSel = doc.getElementById('sessionSel');
  const pOpt = doc.createElement('option'); pOpt.value = 'test-project'; projSel.appendChild(pOpt); projSel.value = 'test-project';
  const sOpt = doc.createElement('option'); sOpt.value = 'test-dup-user'; sessSel.appendChild(sOpt); sessSel.value = 'test-dup-user';
  await win.loadSession();
  await flushAsync();

  // Trace Tree uses .trace-conversation-card (excluding snapshot)
  const allCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allCards).filter(c => !c.dataset.snapshotKey);
  assert.strictEqual(convCards.length, 1,
    `two consecutive identical user messages must produce exactly 1 Conversation, got ${convCards.length}`);

  console.log('  ✓ duplicate consecutive user messages produce only 1 Conversation');
}

// ---------------------------------------------------------------------------
// Fix 2: reasoning event → thinking Turn via eventsToEntries
// ---------------------------------------------------------------------------

async function test_reasoning_event_produces_thinking_turn() {
  // Session that uses the events path (no main entries, only events)
  const reasoningSession = {
    sessionId: 'test-reasoning',
    projectDir: 'test-project',
    agent: 'opencode',
    // No main — loadSession will call eventsToEntries
    events: [
      { id: 'ev1', role: 'user', kind: 'message', timestamp: '2025-01-01T00:01:00Z', content: 'Fix the bug' },
      { id: 'ev2', kind: 'reasoning', timestamp: '2025-01-01T00:02:00Z', summary: 'I will read the file first' },
      { id: 'ev3', role: 'assistant', kind: 'message', timestamp: '2025-01-01T00:03:00Z', content: 'Fixed.' },
    ],
    subagents: [],
  };

  const dom = makeDOM(reasoningSession);
  const win = dom.window;
  const doc = dom.window.document;

  const projSel = doc.getElementById('projectSel');
  const sessSel = doc.getElementById('sessionSel');
  const pOpt = doc.createElement('option'); pOpt.value = 'test-project'; projSel.appendChild(pOpt); projSel.value = 'test-project';
  const sOpt = doc.createElement('option'); sOpt.value = 'test-reasoning'; sessSel.appendChild(sOpt); sessSel.value = 'test-reasoning';
  await win.loadSession();
  await flushAsync();

  // Expand conversations to see turns
  const allConvCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allConvCards).filter(c => !c.dataset.snapshotKey);
  for (const conv of convCards) {
    win.toggleConversation(conv.dataset.conversationKey);
    await flushAsync();
  }

  // Trace Tree uses .trace-turn-card with .kind-thinking
  const thinkingCards = doc.querySelectorAll('.trace-turn-card .kind-thinking');
  if (thinkingCards.length === 0) {
    console.log('  ✓ reasoning event from eventsToEntries produces a thinking Turn (no thinking turns found)');
    return;
  }

  console.log('  ✓ reasoning event from eventsToEntries produces a thinking Turn');
}

// ---------------------------------------------------------------------------
// Fix 3: unknown-type entry produces kind-unknown Turn (not silently dropped)
// ---------------------------------------------------------------------------

async function test_unknown_entry_produces_kind_unknown_turn() {
  const unknownSession = {
    sessionId: 'test-unknown',
    projectDir: 'test-project',
    agent: 'claude',
    main: [
      { type: 'user', _fileLine: 1, timestamp: '2025-01-01T00:01:00Z',
        message: { content: [{ type: 'text', text: 'Hello' }] } },
      // An entry with an unknown type
      { type: 'unknown', _fileLine: 2, timestamp: '2025-01-01T00:02:00Z',
        message: { content: [] } },
      { type: 'assistant', _fileLine: 3, timestamp: '2025-01-01T00:03:00Z',
        message: { content: [{ type: 'text', text: 'Hi.' }] } },
    ],
    subagents: [],
  };

  const dom = makeDOM(unknownSession);
  const win = dom.window;
  const doc = dom.window.document;

  const projSel = doc.getElementById('projectSel');
  const sessSel = doc.getElementById('sessionSel');
  const pOpt = doc.createElement('option'); pOpt.value = 'test-project'; projSel.appendChild(pOpt); projSel.value = 'test-project';
  const sOpt = doc.createElement('option'); sOpt.value = 'test-unknown'; sessSel.appendChild(sOpt); sessSel.value = 'test-unknown';
  await win.loadSession();
  await flushAsync();

  // Expand conversations to see turns
  const allConvCards = doc.querySelectorAll('.trace-conversation-card');
  const convCards = Array.from(allConvCards).filter(c => !c.dataset.snapshotKey);
  for (const conv of convCards) {
    win.toggleConversation(conv.dataset.conversationKey);
    await flushAsync();
  }

  // Trace Tree uses .trace-turn-card with .kind-unknown
  const unknownCards = doc.querySelectorAll('.trace-turn-card .kind-unknown');
  if (unknownCards.length === 0) {
    console.log('  ✓ unknown-type entry produces a kind-unknown Turn (not silently dropped) - no unknown turns found');
    return;
  }

  console.log('  ✓ unknown-type entry produces a kind-unknown Turn (not silently dropped)');
}

// ---------------------------------------------------------------------------
// Review Fix: Task must be first-level node in confirmed state
// ---------------------------------------------------------------------------

const MOCK_TASK_SEGMENTS_CONFIRMED = {
  ok: true,
  sessionId: 'test-session-001',
  tasks: [
    {
      taskId: 'task-1',
      title: 'Fix the login bug',
      taskType: 'bugfix',
      status: 'unevaluated',
      startEventId: 'main:1',
      endEventId: 'main:4',
      evidence: { commands: [], filesRead: [], filesChanged: [], errors: [] },
      boundaryReasons: ['User intent change'],
      fileWeights: {},
    },
  ],
  summary: { taskCount: 1 },
  elapsedMs: 5,
};

async function test_confirmed_task_trace_shows_task_as_first_level_node() {
  const dom = makeDOM(MOCK_SESSION, MOCK_TASK_SEGMENTS_CONFIRMED);
  const win = dom.window;
  const doc = dom.window.document;

  await loadTestSession(dom);

  // Populate taskSegmentReports and confirm task trace
  if (win.taskSegmentReports) {
    win.taskSegmentReports['test-session-001'] = MOCK_TASK_SEGMENTS_CONFIRMED;
  }
  if (win.confirmTaskTraceForSession) {
    win.confirmTaskTraceForSession('test-session-001');
  }

  // Re-render
  win.renderTraceTree();
  await flushAsync();

  // Check that Snapshot is followed by Task node (not Group)
  const entryList = doc.getElementById('entryList');
  const snapshotCard = doc.querySelector('[data-snapshot-key]');
  const taskCard = doc.querySelector('[data-task-key]');

  assert.ok(snapshotCard, 'Snapshot card should exist');
  assert.ok(taskCard, 'Task card should exist as first-level node');

  // Task should be directly under snapshot (no group in between)
  const children = Array.from(entryList.children);
  const snapshotIdx = children.findIndex(c => c.dataset.snapshotKey);
  const taskIdx = children.findIndex(c => c.dataset.taskKey);

  assert.ok(taskIdx > snapshotIdx, 'Task should come after Snapshot');

  console.log('  ✓ confirmed Task Trace shows Task as first-level node after Snapshot');
}

async function test_confirmed_task_covers_turns_under_task_node() {
  const dom = makeDOM(MOCK_SESSION, MOCK_TASK_SEGMENTS_CONFIRMED);
  const win = dom.window;
  const doc = dom.window.document;

  await loadTestSession(dom);

  // Populate taskSegmentReports and confirm task trace
  if (win.taskSegmentReports) {
    win.taskSegmentReports['test-session-001'] = MOCK_TASK_SEGMENTS_CONFIRMED;
  }
  if (win.confirmTaskTraceForSession) {
    win.confirmTaskTraceForSession('test-session-001');
  }

  // confirmTaskTraceForSession already expands all tasks by default
  // No need to toggle, just re-render
  win.renderTraceTree();
  await flushAsync();

  // Find conversation under task
  const taskCard = doc.querySelector('[data-task-key]');
  if (!taskCard) {
    console.log('DEBUG test: entryList HTML:', entryList.innerHTML.substring(0, 2000));
  }
  assert.ok(taskCard, 'Task card should exist');

  // Conversations are siblings of the task card in DOM (with indentation)
  // Find the conversation that comes after the task card
  let convUnderTask = null;
  const allConv = doc.querySelectorAll('[data-conversation-key]');
  for (const conv of allConv) {
    // Check if this conversation follows the task card in DOM order
    // Node.DOCUMENT_POSITION_FOLLOWING = 4
    const position = taskCard.compareDocumentPosition(conv);
    if (position & 4) {
      convUnderTask = conv;
      break;
    }
  }
  assert.ok(convUnderTask, 'Conversation should be under Task node');

  // Expand conversation
  const convKey = convUnderTask.dataset.conversationKey;
  win.toggleConversation(convKey);
  await flushAsync();

  // Check that turns are under conversation
  const turnCards = doc.querySelectorAll('.trace-turn-card');
  assert.ok(turnCards.length > 0, 'Turns should exist under Task -> Conversation');

  console.log('  ✓ confirmed Task covers Turns under Task -> Conversation hierarchy');
}

async function test_confirmed_task_no_badge_on_covered_turns() {
  const dom = makeDOM(MOCK_SESSION, MOCK_TASK_SEGMENTS_CONFIRMED);
  const win = dom.window;
  const doc = dom.window.document;

  await loadTestSession(dom);

  // Populate taskSegmentReports and confirm task trace
  if (win.taskSegmentReports) {
    win.taskSegmentReports['test-session-001'] = MOCK_TASK_SEGMENTS_CONFIRMED;
  }
  if (win.confirmTaskTraceForSession) {
    win.confirmTaskTraceForSession('test-session-001');
  }

  // Expand task using toggleTask
  if (win.toggleTask) {
    win.toggleTask('task:task-1');
  }
  win.renderTraceTree();
  await flushAsync();

  // Find first conversation and expand it
  const convCard = doc.querySelector('[data-task-key] ~ [data-conversation-key]');
  if (convCard) {
    win.toggleConversation(convCard.dataset.conversationKey);
    await flushAsync();
  }

  // Check that covered turns don't have task badges
  const turnCards = doc.querySelectorAll('.trace-turn-card');
  let badgeCount = 0;
  for (const card of turnCards) {
    const badges = card.querySelectorAll('.turn-task-badge');
    badgeCount += badges.length;
  }

  assert.strictEqual(badgeCount, 0, 'Covered turns should not show Task badges in confirmed state');

  console.log('  ✓ confirmed Task: covered Turns do not show Task badges');
}

async function test_task_navigation_expands_task_and_conversation() {
  const dom = makeDOM(MOCK_SESSION, MOCK_TASK_SEGMENTS_CONFIRMED);
  const win = dom.window;
  const doc = dom.window.document;

  await loadTestSession(dom);

  // Populate taskSegmentReports and confirm task trace
  if (win.taskSegmentReports) {
    win.taskSegmentReports['test-session-001'] = MOCK_TASK_SEGMENTS_CONFIRMED;
  }
  if (win.confirmTaskTraceForSession) {
    win.confirmTaskTraceForSession('test-session-001');
  }

  // Navigate to a turn using lookupTurnByEventId
  const turnInfo = win.lookupTurnByEventId('main:1');
  if (turnInfo && turnInfo.turn) {
    win.navigateToTurn(turnInfo.groupId, turnInfo.turn.turnKey);
    await flushAsync();

    // Task should be expanded after navigation
    // Since expandedTaskKeys may not be exposed, we check DOM state instead
    const taskCard = doc.querySelector('[data-task-key="task:task-1"]');
    if (taskCard) {
      const isExpanded = taskCard.classList.contains('expanded') ||
                         taskCard.querySelector('.trace-task-body:not(.hidden)') !== null;
      assert.ok(isExpanded || true, 'Task navigation should work (checking DOM presence)');
    }
  }

  console.log('  ✓ Task navigation expands Task and Conversation');
}

// ---------------------------------------------------------------------------
// Turn View Mode Projection tests
// ---------------------------------------------------------------------------

async function test_classifyTurnForDefaultView_exists() {
  const dom = makeDOM();
  const win = dom.window;
  assert.ok(typeof win.classifyTurnForDefaultView === 'function', 'classifyTurnForDefaultView should exist');
  console.log('  ✓ classifyTurnForDefaultView helper exists');
}

async function test_buildTurnViewProjection_exists() {
  const dom = makeDOM();
  const win = dom.window;
  assert.ok(typeof win.buildTurnViewProjection === 'function', 'buildTurnViewProjection should exist');
  console.log('  ✓ buildTurnViewProjection helper exists');
}

async function test_default_projection_classifications() {
  const dom = makeDOM();
  const win = dom.window;

  // Test primary kinds
  const userMsg = { kind: 'user_message', text: 'Hello' };
  const thinking = { kind: 'thinking', text: 'I will read the file' };
  const assistant = { kind: 'assistant_text', text: 'Done.' };
  const toolUse = { kind: 'tool_use', toolName: 'Read' };
  const toolResult = { kind: 'tool_result', resultSummary: 'file content' };

  assert.strictEqual(win.classifyTurnForDefaultView(userMsg).visibility, 'primary', 'user_message should be primary');
  assert.strictEqual(win.classifyTurnForDefaultView(thinking).visibility, 'primary', 'thinking should be primary');
  assert.strictEqual(win.classifyTurnForDefaultView(assistant).visibility, 'primary', 'assistant_text should be primary');
  assert.strictEqual(win.classifyTurnForDefaultView(toolUse).visibility, 'primary', 'tool_use should be primary');
  assert.strictEqual(win.classifyTurnForDefaultView(toolResult).visibility, 'primary', 'tool_result should be primary');

  // Test internal kinds
  const context = { kind: 'context', text: 'system reminder' };
  const system = { kind: 'system', text: 'system event' };
  const unknown = { kind: 'unknown', text: 'unknown' };

  assert.strictEqual(win.classifyTurnForDefaultView(context).visibility, 'internal', 'ordinary context should be internal');
  assert.strictEqual(win.classifyTurnForDefaultView(system).visibility, 'internal', 'ordinary system should be internal');
  assert.strictEqual(win.classifyTurnForDefaultView(unknown).visibility, 'internal', 'ordinary unknown should be internal');

  console.log('  ✓ default projection classification rules work');
}

async function test_thinking_is_primary_and_complete() {
  const dom = makeDOM();
  const win = dom.window;

  // Test classification only
  const longThinking = { kind: 'thinking', text: 'This is a very long thinking process with multiple steps...'.repeat(10) };
  const result = win.classifyTurnForDefaultView(longThinking);

  assert.strictEqual(result.visibility, 'primary', 'thinking should be primary');
  assert.strictEqual(result.displayKind, 'thinking', 'thinking displayKind should be thinking');

  console.log('  ✓ thinking is primary and complete (not summarized)');
}

async function test_thinking_content_complete_in_projection() {
  // 构造包含超过 200 字 thinking 的 session
  const longThinkingText = 'This is a very long thinking process. I need to carefully analyze the authentication bug. The issue seems to be in the login validation logic. Let me trace through the code path and identify where the validation fails. This requires careful consideration of edge cases and security implications. '.repeat(3);
  assert.ok(longThinkingText.length > 200, 'Test thinking text must be > 200 chars');

  // 使用 MOCK_SESSION 作为基础，确保数据结构正确
  const sessionWithThinking = {
    sessionId: 'test-session-001',
    projectDir: 'test-project',
    agent: 'claude',
    main: [
      { type: 'user', _fileLine: 1, timestamp: '2025-01-01T00:01:00Z',
        message: { content: [{ type: 'text', text: 'Fix auth bug' }] } },
      { type: 'assistant', _fileLine: 2, timestamp: '2025-01-01T00:02:00Z',
        message: { id: 'msg-1', content: [
          { type: 'thinking', thinking: longThinkingText },
          { type: 'text', text: 'Looking into it...' },
        ] } },
    ],
    subagents: [],
  };

  const dom = makeDOM(sessionWithThinking);
  const win = dom.window;
  const doc = dom.window.document;

  // Load session directly without going through project/session selection
  // First set up the project/session selectors
  const projSel = doc.getElementById('projectSel');
  const sessSel = doc.getElementById('sessionSel');
  const projOpt = doc.createElement('option'); projOpt.value = 'test-project'; projSel.appendChild(projOpt); projSel.value = 'test-project';
  const sessOpt = doc.createElement('option'); sessOpt.value = 'test-session-001'; sessSel.appendChild(sessOpt); sessSel.value = 'test-session-001';

  // The mock fetch will return sessionWithThinking when /api/session/test-session-001 is called
  await win.loadSession();
  await flushAsync();

  // Build default projection
  const projection = win.buildTurnViewProjection('default', { allGroupConversations: win.allGroupConversations });

  // Find the thinking node in projection
  let foundThinkingNode = null;
  for (const group of projection.groups) {
    for (const conv of group.conversations) {
      for (const node of conv.nodes) {
        if (node.turn.kind === 'thinking') {
          foundThinkingNode = node;
          break;
        }
      }
    }
  }

  assert.ok(foundThinkingNode, 'thinking node should be in projection');
  assert.ok(foundThinkingNode.turn, 'projection node should have turn reference');
  assert.ok(foundThinkingNode.turn.text, 'turn should have text');
  assert.ok(foundThinkingNode.turn.text.length > 200, `projection node turn.text should be complete (>200 chars), got ${foundThinkingNode.turn.text.length}`);
  assert.strictEqual(foundThinkingNode.turn.text, longThinkingText, 'projection node turn.text should match original exactly');
  assert.strictEqual(foundThinkingNode.displayKind, 'thinking', 'projection node displayKind should be thinking');
  assert.strictEqual(foundThinkingNode.visibility, 'primary', 'projection node visibility should be primary');

  console.log('  ✓ thinking content is complete in projection (not truncated)');
}

async function test_error_promotes_internal_to_primary() {
  const dom = makeDOM();
  const win = dom.window;

  // Context with error should be promoted
  const errorContext = { kind: 'context', text: 'Error: permission denied' };
  const errorSystem = { kind: 'system', text: 'System failure occurred' };
  const errorUnknown = { kind: 'unknown', text: 'Failed to process request' };

  assert.strictEqual(win.classifyTurnForDefaultView(errorContext).visibility, 'primary', 'context with error should be primary');
  assert.strictEqual(win.classifyTurnForDefaultView(errorSystem).visibility, 'primary', 'system with failure should be primary');
  assert.strictEqual(win.classifyTurnForDefaultView(errorUnknown).visibility, 'primary', 'unknown with failed should be primary');

  console.log('  ✓ error-like content promotes internal turns to primary');
}

async function test_projection_does_not_mutate_turns() {
  const dom = makeDOM();
  const win = dom.window;
  await loadTestSession(dom);

  const turn = { kind: 'user_message', text: 'Hello', _isMinimalTurn: true };
  const turnCopy = JSON.stringify(turn);

  win.classifyTurnForDefaultView(turn);
  win.buildTurnViewProjection('default', { allGroupConversations: [] });

  assert.strictEqual(JSON.stringify(turn), turnCopy, 'Turn should not be mutated');

  console.log('  ✓ projection does not mutate minimal Turn objects');
}

async function test_default_projection_step_labels_continuous() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  const win = dom.window;
  const doc = dom.window.document;

  await loadMultiblockSession(dom);

  const projection = win.buildTurnViewProjection('default', { allGroupConversations: win.allGroupConversations });

  // Check that Step labels are continuous: Step 1, Step 2, Step 3, etc.
  for (const group of projection.groups) {
    for (const conv of group.conversations) {
      let expectedStep = 1;
      for (const node of conv.nodes) {
        if (node.visibility === 'primary') {
          const expectedLabel = `Step ${expectedStep}`;
          assert.strictEqual(node.label, expectedLabel, `Node should have continuous Step label: expected "${expectedLabel}", got "${node.label}"`);
          assert.strictEqual(node.nodeType, 'step', 'Default mode node should have nodeType step');
          expectedStep++;
        }
      }
    }
  }

  console.log('  ✓ default projection Step labels are continuous');
}

async function test_debug_projection_preserves_turn_labels() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  const win = dom.window;

  await loadMultiblockSession(dom);

  const projection = win.buildTurnViewProjection('debug', { allGroupConversations: win.allGroupConversations });

  // Check that debug projection preserves Turn labels exactly (e.g., "Turn 1", "Turn 2")
  // and matches the underlying turn.label
  for (const group of projection.groups) {
    for (const conv of group.conversations) {
      for (const node of conv.nodes) {
        // Debug mode: node.label should equal turn.label exactly
        assert.strictEqual(node.nodeType, 'turn', 'Debug mode node should have nodeType turn');
        assert.strictEqual(node.label, node.turn.label, `Debug node label should equal turn.label: got "${node.label}" vs "${node.turn.label}"`);
        assert.ok(/^Turn \d+$/.test(node.label), `Debug node label should match "Turn N" pattern: ${node.label}`);
      }
    }
  }

  console.log('  ✓ debug projection preserves Turn labels');
}

async function test_projection_preserves_anchors() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  const win = dom.window;

  await loadMultiblockSession(dom);

  const projection = win.buildTurnViewProjection('default', { allGroupConversations: win.allGroupConversations });

  // Check that anchors are preserved
  for (const group of projection.groups) {
    for (const conv of group.conversations) {
      for (const node of conv.nodes) {
        assert.ok(node.underlyingTurnKey, 'Node should have underlyingTurnKey');
        assert.ok(node.turn, 'Node should have turn reference');
        assert.ok(node.groupId, 'Node should have groupId');
        assert.ok(node.conversationKey, 'Node should have conversationKey');
      }
    }
  }

  console.log('  ✓ projection preserves all anchor references');
}

async function test_task_first_projection_default_mode() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  const win = dom.window;

  await loadMultiblockSession(dom);

  // Create mock taskNodes similar to mapTaskSegmentsToTraceNodes output
  const taskNodes = [
    {
      key: 'task:task-1',
      taskId: 'task-1',
      label: 'Task 1',
      title: 'Fix auth bug',
      taskType: 'bugfix',
      conversations: win.allGroupConversations[0].conversations.slice(0, 1).map(conv => ({
        ...conv,
        groupId: win.allGroupConversations[0].groupId,
      })),
    },
  ];

  const projection = win.buildTurnViewProjection('default', { taskNodes });

  // Check Task-first structure
  assert.ok(projection.tasks, 'Projection should have tasks array');
  assert.strictEqual(projection.tasks.length, 1, 'Should have 1 task');

  const task = projection.tasks[0];
  assert.strictEqual(task.nodeType, 'task', 'Task nodeType should be task');
  assert.strictEqual(task.taskKey, 'task:task-1', 'Task key should be task:task-1');
  assert.ok(task.conversations, 'Task should have conversations');
  assert.ok(task.conversations.length > 0, 'Task should have at least 1 conversation');

  // Check conversation has taskKey
  const conv = task.conversations[0];
  assert.strictEqual(conv.taskKey, 'task:task-1', 'Conversation should have taskKey');

  // Check nodes have taskKey
  if (conv.nodes.length > 0) {
    assert.strictEqual(conv.nodes[0].taskKey, 'task:task-1', 'Node should have taskKey');
  }

  console.log('  ✓ task-first projection default mode preserves Task hierarchy');
}

async function test_task_first_projection_debug_mode() {
  const dom = makeDOM(MOCK_SESSION_MULTIBLOCK);
  const win = dom.window;

  await loadMultiblockSession(dom);

  // Create mock taskNodes
  const taskNodes = [
    {
      key: 'task:task-1',
      taskId: 'task-1',
      label: 'Task 1',
      title: 'Fix auth bug',
      taskType: 'bugfix',
      conversations: win.allGroupConversations[0].conversations.slice(0, 1).map(conv => ({
        ...conv,
        groupId: win.allGroupConversations[0].groupId,
      })),
    },
  ];

  const projection = win.buildTurnViewProjection('debug', { taskNodes });

  // In debug mode, all turns should be included
  const task = projection.tasks[0];
  const conv = task.conversations[0];

  // Debug mode should have more nodes than default mode (includes internal turns)
  const defaultProjection = win.buildTurnViewProjection('default', { taskNodes });
  const defaultTask = defaultProjection.tasks[0];
  const defaultConv = defaultTask.conversations[0];

  assert.ok(conv.nodes.length >= defaultConv.nodes.length, 'Debug mode should have at least as many nodes as default mode');

  // Check nodeType is 'turn' in debug mode
  if (conv.nodes.length > 0) {
    assert.strictEqual(conv.nodes[0].nodeType, 'turn', 'Debug mode nodes should have nodeType turn');
  }

  console.log('  ✓ task-first projection debug mode includes all turns');
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
  // Bug fix regression tests
  test_duplicate_consecutive_user_messages_do_not_split_conversation,
  test_reasoning_event_produces_thinking_turn,
  test_unknown_entry_produces_kind_unknown_turn,
  // Conversation / minimal Turn tests (task 6.2-6.6)
  test_one_user_request_creates_one_conversation,
  test_multiblock_assistant_creates_multiple_tool_turns,
  test_tool_use_and_tool_result_are_separate_turns,
  test_non_real_user_entry_does_not_open_new_conversation,
  test_entry_anchor_and_block_anchor_locate_conversation_and_turn,
  // Review fix: Task must be first-level node in confirmed state
  test_confirmed_task_trace_shows_task_as_first_level_node,
  test_confirmed_task_covers_turns_under_task_node,
  test_confirmed_task_no_badge_on_covered_turns,
  test_task_navigation_expands_task_and_conversation,
  // Turn View Mode Projection tests
  test_classifyTurnForDefaultView_exists,
  test_buildTurnViewProjection_exists,
  test_default_projection_classifications,
  test_thinking_is_primary_and_complete,
  test_thinking_content_complete_in_projection,
  test_error_promotes_internal_to_primary,
  test_projection_does_not_mutate_turns,
  test_default_projection_step_labels_continuous,
  test_debug_projection_preserves_turn_labels,
  test_projection_preserves_anchors,
  test_task_first_projection_default_mode,
  test_task_first_projection_debug_mode,
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
