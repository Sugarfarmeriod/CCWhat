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
// Test 2: turn root has data-idx in DOM after loadSession
// ---------------------------------------------------------------------------

async function test_turn_root_has_data_idx_in_dom() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const doc = dom.window.document;
  const turnHdrs = doc.querySelectorAll('.turn-hdr');

  // There should be turn headers
  assert.ok(turnHdrs.length > 0, 'turn headers should exist after loadSession');

  // Every turn header should have data-idx
  for (const hdr of turnHdrs) {
    assert.ok(
      hdr.dataset.idx !== undefined && hdr.dataset.idx !== '',
      `turn header should have data-idx, got: ${hdr.dataset.idx}`
    );
    // data-idx should be a valid number
    assert.ok(!isNaN(Number(hdr.dataset.idx)), `data-idx should be numeric`);
  }

  console.log('  ✓ turn headers have data-idx after loadSession');
}

// ---------------------------------------------------------------------------
// Test 3: focusEntryInNav finds the turn root (not a no-op)
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

  // Find the index for main:1 (turn root)
  const idx = win.findEntryByEventId('main:1');
  assert.ok(idx >= 0, `main:1 should be findable, got ${idx}`);

  // Expand turns so the element is visible (not collapsed)
  // Turn roots are turn-hdr elements — make sure we can find [data-idx="idx"]
  const targetEl = doc.querySelector(`[data-idx="${idx}"]`);
  assert.ok(targetEl !== null, `[data-idx="${idx}"] should exist in DOM after load`);

  // Call focusEntryInNav — should not throw and should trigger scrollIntoView
  let scrollCalled = false;
  const origScroll = win.HTMLElement.prototype.scrollIntoView;
  win.HTMLElement.prototype.scrollIntoView = function() { scrollCalled = true; };
  win.focusEntryInNav(idx);
  win.HTMLElement.prototype.scrollIntoView = origScroll;

  assert.ok(scrollCalled, 'scrollIntoView should be called when focusing turn root');
  console.log('  ✓ focusEntryInNav works on turn root (no longer a no-op)');
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
// Test 7: clicking Tasks auto-runs segmentation for the loaded session
// ---------------------------------------------------------------------------

async function test_tasks_page_auto_segments_loaded_session() {
  const dom = makeDOM();
  await loadTestSession(dom);

  const win = dom.window;
  const doc = dom.window.document;

  win.navigateToPage('tasks');
  await flushAsync();

  assert.strictEqual(win.__taskSegmentRequests.length, 1, 'Tasks page should request segmentation once');
  assert.deepStrictEqual(win.__taskSegmentRequests[0], { sessionId: 'test-session-001' });
  assert.strictEqual(doc.querySelector('.page.active').dataset.page, 'tasks');
  assert.ok(doc.getElementById('taskSegContent').textContent.includes('Fix the login bug'));
  console.log('  ✓ Tasks page auto-runs segmentation for the loaded session');
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
// Run all tests
// ---------------------------------------------------------------------------

const tests = [
  test_map_populated_after_load,
  test_turn_root_has_data_idx_in_dom,
  test_focusEntryInNav_turn_root_visible,
  test_focusEntryInNav_child_entry,
  test_make_nav_btn_disabled_for_unknown_event,
  test_show_nav_hint,
  test_tasks_page_auto_segments_loaded_session,
  test_session_tasks_session_roundtrip_keeps_logs_visible,
  test_missing_page_falls_back_to_session,
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
