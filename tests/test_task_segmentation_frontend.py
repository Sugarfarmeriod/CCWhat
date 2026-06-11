"""Frontend static regression tests for the task segmentation panel (tasks 7.1-7.4)."""

from __future__ import annotations

import unittest
from pathlib import Path

_HTML = (Path(__file__).resolve().parents[1] / "viewer" / "claude-log.html").read_text(encoding="utf-8")


class TestTaskSegmentationButton(unittest.TestCase):
    """7.1 — button existence and request shape"""

    def test_button_exists_in_topbar(self):
        self.assertIn('id="taskSegmentsBtn"', _HTML)

    def test_button_has_onclick_handler(self):
        self.assertIn('onclick="onTaskSegmentsBtnClick()"', _HTML)

    def test_button_initially_disabled(self):
        idx = _HTML.index('id="taskSegmentsBtn"')
        snippet = _HTML[max(0, idx - 200):idx + 200]
        self.assertIn('disabled', snippet)

    def test_request_body_only_contains_session_id(self):
        # POST body must be JSON.stringify({ sessionId }) — no extra keys
        self.assertIn("JSON.stringify({ sessionId })", _HTML)

    def test_post_endpoint_is_api_task_segments(self):
        self.assertIn("/api/task-segments", _HTML)

    def test_request_method_is_post(self):
        self.assertIn("method: 'POST'", _HTML)


class TestSessionTasksWorkbenchScope(unittest.TestCase):
    """Session + Tasks scoped workbench regression tests."""

    def test_session_is_default_active_page(self):
        self.assertIn("activeView: 'sessions'", _HTML)
        session_nav_idx = _HTML.index('data-page="sessions"')
        session_nav_snippet = _HTML[max(0, session_nav_idx - 80):session_nav_idx + 160]
        self.assertIn("nav-item active", session_nav_snippet)

    def test_left_nav_core_modules_are_session_and_tasks(self):
        nav_start = _HTML.index('<nav class="left-nav">')
        nav_end = _HTML.index('</nav>', nav_start)
        nav = _HTML[nav_start:nav_end]
        self.assertIn('data-page="sessions"', nav)
        self.assertIn('> Session', nav)
        self.assertIn('data-page="tasks"', nav)
        self.assertNotIn('data-page="overview"', nav)
        self.assertNotIn('data-page="raw-events"', nav)
        self.assertNotIn('data-page="differential"', nav)

    def test_session_page_contains_migrated_log_viewer(self):
        self.assertIn('data-page="sessions"', _HTML)
        self.assertIn('id="entryList"', _HTML)
        self.assertIn('id="detailPanel"', _HTML)
        self.assertIn('id="typeFilters"', _HTML)
        self.assertIn('id="countBadge"', _HTML)

    def test_session_load_error_includes_backend_detail_and_url(self):
        self.assertIn("async function apiError", _HTML)
        self.assertIn("data?.error", _HTML)
        self.assertIn("(${url})", _HTML)
        fn_start = _HTML.index("async function loadSession")
        fn_end = _HTML.index("function resetAnalysisState", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("throw await apiError(resp, url)", snippet)

    def test_raw_events_alias_routes_to_session(self):
        self.assertIn("pageId === 'raw-events'", _HTML)
        self.assertIn("pageId === 'session'", _HTML)

    def test_evidence_alias_routes_to_session(self):
        self.assertIn("pageId === 'evidence'", _HTML)

    def test_missing_page_falls_back_to_session(self):
        fn_start = _HTML.index("function navigateToPage")
        fn_end = _HTML.index("function renderPage", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn('.page[data-page="${normalizedPageId}"]', snippet)
        self.assertIn("if (!page)", snippet)
        self.assertIn("normalizedPageId = 'sessions'", snippet)

    def test_load_session_does_not_auto_jump_without_tasks(self):
        fn_start = _HTML.index("async function loadSession")
        fn_end = _HTML.index("function resetAnalysisState", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertNotIn("navigateToPage('raw-events')", snippet)
        # loadSession must refresh the active workbench view after loading
        self.assertIn("_renderView(activeView)", snippet)


class TestTaskSegmentationCache(unittest.TestCase):
    """7.2 — cache and state behavior"""

    def test_cache_dict_declared(self):
        self.assertIn("const taskSegmentReports = {}", _HTML)

    def test_in_flight_flag_declared(self):
        self.assertIn("let taskSegmentsInFlight = false", _HTML)

    def test_selected_id_declared(self):
        self.assertIn("let selectedTaskSegmentId = null", _HTML)

    def test_no_localstorage_write(self):
        # Must not write task segment data to localStorage
        self.assertNotIn("localStorage.setItem", _HTML.split("taskSegmentReports")[1].split("// ── Init")[0])

    def test_rerun_function_exists(self):
        self.assertIn("function runTaskSegmentationForCurrentSession", _HTML)

    def test_show_cached_function_exists(self):
        self.assertIn("function showCachedTaskSegments", _HTML)

    def test_update_button_function_exists(self):
        self.assertIn("function updateTaskSegmentsButton", _HTML)

    def test_on_click_handler_exists(self):
        self.assertIn("function onTaskSegmentsBtnClick", _HTML)

    def test_tasks_page_auto_runs_for_loaded_session(self):
        fn_start = _HTML.index("function renderTasksPage")
        fn_end = _HTML.index("function renderReqRespPage", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("sessionId !== currentLoadedSessionId", snippet)
        self.assertIn("正在切分当前 Session 的任务", snippet)
        self.assertIn("runTaskSegmentationForCurrentSession({ navigate: false })", snippet)

    def test_task_runner_accepts_navigation_option(self):
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        snippet = _HTML[fn_start:fn_start + 500]
        self.assertIn("{ navigate = true } = {}", snippet)
        self.assertIn("if (navigate && workbenchState.activeView !== 'tasks')", snippet)

    def test_reset_calls_update_button(self):
        idx = _HTML.index("function resetAnalysisState")
        snippet = _HTML[idx:idx + 700]
        self.assertIn("updateTaskSegmentsButton", snippet)

    def test_load_session_calls_update_button(self):
        idx = _HTML.index("async function loadSession")
        end = _HTML.index("function resetAnalysisState", idx)
        snippet = _HTML[idx:end]
        self.assertIn("updateTaskSegmentsButton", snippet)


class TestTaskSegmentationRendering(unittest.TestCase):
    """7.3 — rendering functions"""

    def test_render_task_segments_function_exists(self):
        self.assertIn("function renderTaskSegments", _HTML)

    def test_render_task_detail_function_exists(self):
        self.assertIn("function renderTaskDetail", _HTML)

    def test_select_task_segment_function_exists(self):
        self.assertIn("function selectTaskSegment", _HTML)

    def test_task_card_css_exists(self):
        self.assertIn(".task-card", _HTML)
        self.assertIn(".task-card.selected", _HTML)

    def test_evidence_chips_css_exists(self):
        self.assertIn(".evidence-chips", _HTML)
        self.assertIn(".evidence-chip", _HTML)

    def test_file_weight_css_exists(self):
        self.assertIn(".file-weight-row", _HTML)
        self.assertIn(".file-weight-bar", _HTML)

    def test_boundary_reason_css_exists(self):
        self.assertIn(".boundary-reason-row", _HTML)

    def test_debug_boundary_css_exists(self):
        self.assertIn(".debug-boundary-row", _HTML)

    def test_task_badge_type_bugfix_css(self):
        self.assertIn(".task-badge-type-bugfix", _HTML)

    def test_task_badge_type_feature_css(self):
        self.assertIn(".task-badge-type-feature", _HTML)

    def test_empty_state_rendered(self):
        self.assertIn("未识别到任务片段", _HTML)

    def test_re_segment_button_in_header(self):
        self.assertIn("重新切分", _HTML)

    def test_task_card_title_uses_render_order_not_api_title(self):
        fn_start = _HTML.index("function renderTaskSegments")
        fn_end = _HTML.index("function selectTaskSegment", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("for (const [taskIdx, t] of tasks.entries())", snippet)
        self.assertIn("const taskTitle = `任务 ${taskIdx + 1}`", snippet)
        self.assertIn('${esc(taskTitle)}', snippet)
        self.assertNotIn("${esc(t.title || '(无标题)')}", snippet)

    def test_final_claim_badge_css(self):
        self.assertIn(".task-badge-final-claim", _HTML)

    def test_ambiguous_badge_css(self):
        self.assertIn(".task-badge-ambiguous", _HTML)

    def test_evidence_sections_rendered(self):
        # Key evidence labels
        self.assertIn("已修改文件", _HTML)
        self.assertIn("已读取文件", _HTML)
        self.assertIn("测试命令", _HTML)
        self.assertIn("用户目标 Todo", _HTML)

    def test_file_weights_sorted_desc_logic(self):
        # sort desc by weight
        self.assertIn(".sort((a, b) => b[1] - a[1])", _HTML)

    def test_raw_json_collapsed(self):
        self.assertIn("原始 JSON", _HTML)

    def test_debug_boundaries_collapsed(self):
        self.assertIn("调试边界", _HTML)


class TestTaskSegmentationNavigation(unittest.TestCase):
    """7.4 — event id mapping and navigation"""

    def test_find_entry_function_exists(self):
        self.assertIn("function findEntryByEventId", _HTML)

    def test_navigate_function_exists(self):
        self.assertIn("function navigateToEventId", _HTML)

    def test_make_nav_btn_function_exists(self):
        self.assertIn("function makeNavBtn", _HTML)

    def test_nav_btn_css_exists(self):
        self.assertIn(".nav-btn", _HTML)

    def test_start_event_nav_label(self):
        self.assertIn("定位开始事件", _HTML)

    def test_end_event_nav_label(self):
        self.assertIn("定位结束事件", _HTML)

    def test_main_event_id_parsing(self):
        # main:<line> pattern handled
        self.assertIn("parts[0] === 'main'", _HTML)

    def test_agent_event_id_parsing(self):
        # agent-<id>:<line> pattern handled in fallback (map is primary)
        fn_start = _HTML.index("function findEntryByEventId")
        fn_end = _HTML.index("function makeNavBtn", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("agent-", snippet)   # agent prefix stripping present

    def test_disabled_nav_btn_on_not_found(self):
        # When idx < 0, button is disabled
        fn_start = _HTML.index("function makeNavBtn")
        fn_end = _HTML.index("function navigateToEventId")
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("disabled", snippet)

    def test_navigate_calls_focus_entry_in_nav(self):
        fn_start = _HTML.index("function navigateToEventId")
        snippet = _HTML[fn_start:fn_start + 200]
        self.assertIn("focusEntryInNav", snippet)


class TestBugFixes(unittest.TestCase):
    """Regression tests for P1/P2 bug fixes."""

    def test_stale_session_guard_in_run(self):
        """P1: success path must check current session still matches."""
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        snippet = _HTML[fn_start:fn_start + 800]
        self.assertIn("currentSession !== sessionId", snippet)

    def test_stale_guard_in_catch_path(self):
        """P1: failure/catch path must also check current session (stale guard)."""
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        snippet = _HTML[fn_start:fn_start + 1200]
        # Must appear in both try (success) and catch (failure) paths
        first_guard = snippet.index("currentSession !== sessionId")
        second_guard = snippet.index("currentSession !== sessionId", first_guard + 1)
        self.assertIsNotNone(second_guard)

    def test_stale_guard_still_caches_result(self):
        """P1: stale guard must cache result before returning."""
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        snippet = _HTML[fn_start:fn_start + 800]
        # Cache write must come before the stale guard check
        cache_pos = snippet.index("taskSegmentReports[sessionId] = data")
        stale_pos = snippet.index("currentSession !== sessionId")
        self.assertLess(cache_pos, stale_pos)

    def test_debug_boundaries_passed_from_top_level_data(self):
        """P1: renderTaskDetailWithTabs called with data.debugBoundaries, not task.debugBoundaries."""
        self.assertIn("renderTaskDetailWithTabs(selTask, data.debugBoundaries)", _HTML)

    def test_render_task_detail_accepts_debug_boundaries_param(self):
        """P1: renderTaskDetailWithTabs signature accepts debugBoundaries parameter."""
        fn_start = _HTML.index("function renderTaskDetailWithTabs(task")
        snippet = _HTML[fn_start:fn_start + 60]
        self.assertIn("debugBoundaries", snippet)

    def test_select_task_triggers_render_task_segments(self):
        """P1: selectTaskSegment calls renderTaskSegments, which passes debugBoundaries internally."""
        fn_start = _HTML.index("function selectTaskSegment")
        fn_end = _HTML.index("function renderTaskDetailWithTabs", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("renderTaskSegments(cached, sessionId)", snippet)

    def test_current_loaded_session_id_declared(self):
        """P2: currentLoadedSessionId state variable exists."""
        self.assertIn("let currentLoadedSessionId = null", _HTML)

    def test_button_guards_on_loaded_session_id(self):
        """P2: button only enabled when currentLoadedSessionId matches."""
        fn_start = _HTML.index("function updateTaskSegmentsButton")
        fn_end = fn_start + 400
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("currentLoadedSessionId", snippet)

    def test_load_session_sets_loaded_id_on_success(self):
        """P2: loadSession sets currentLoadedSessionId on success."""
        fn_start = _HTML.index("async function loadSession")
        fn_end = _HTML.index("function resetAnalysisState", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("currentLoadedSessionId = sessionId", snippet)

    def test_reset_clears_loaded_session_id(self):
        """P2: resetAnalysisState clears currentLoadedSessionId."""
        fn_start = _HTML.index("function resetAnalysisState")
        snippet = _HTML[fn_start:fn_start + 700]
        self.assertIn("currentLoadedSessionId = null", snippet)


class TestNavigationImprovements(unittest.TestCase):
    """5.1-5.4 — regression tests for improve-task-segmentation-navigation."""

    # 5.1: task cards use data-task-id, not inline onclick
    def test_task_cards_use_data_task_id(self):
        self.assertIn('data-task-id=', _HTML)

    def test_task_cards_no_inline_onclick_with_select(self):
        # Task cards must NOT use onclick="selectTaskSegment(...)" inline
        # The delegated listener approach is used instead
        fn_start = _HTML.index("function renderTaskSegments")
        fn_end = _HTML.index("function selectTaskSegment", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertNotIn("onclick=\"selectTaskSegment(", snippet)

    def test_delegated_event_listener_on_cards(self):
        self.assertIn("addEventListener('click'", _HTML)
        self.assertIn("closest('[data-task-id]')", _HTML)

    # 5.2: task click triggers state-driven re-render
    def test_select_calls_render_task_segments(self):
        fn_start = _HTML.index("function selectTaskSegment")
        fn_end = fn_start + 500
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("renderTaskSegments(cached, sessionId)", snippet)

    def test_select_guards_invalid_task_id(self):
        fn_start = _HTML.index("function selectTaskSegment")
        snippet = _HTML[fn_start:fn_start + 400]
        self.assertIn("if (!task) return", snippet)

    # 5.3: final claim label + disclaimer + collapse
    def test_final_claim_label_is_agent_declaration(self):
        self.assertIn("Agent 最终声明", _HTML)

    def test_final_claim_disclaimer_exists(self):
        self.assertIn("不代表任务成功", _HTML)

    def test_final_claim_has_expand_collapse(self):
        self.assertIn("展开全文", _HTML)

    def test_error_summary_function_exists(self):
        self.assertIn("function errorSummary", _HTML)

    def test_error_summary_uses_keywords(self):
        fn_start = _HTML.index("function errorSummary")
        snippet = _HTML[fn_start:fn_start + 400]
        self.assertIn("Traceback", snippet)

    def test_errors_have_collapse_full_text(self):
        self.assertIn("展开原文", _HTML)

    # 5.4: stable turn index, focusEntryInNav, scrollIntoView, filter-hidden hint
    def test_stable_turn_root_idx_set(self):
        fn_start = _HTML.index("function buildTurns")
        snippet = _HTML[fn_start:fn_start + 800]
        self.assertIn("_turnRootIdx", snippet)

    def test_render_list_uses_full_group_entries(self):
        fn_start = _HTML.index("function renderList")
        snippet = _HTML[fn_start:fn_start + 2000]
        self.assertIn("buildTurns(group.entries", snippet)

    def test_is_entry_hidden_by_filter_exists(self):
        self.assertIn("function isEntryHiddenByFilter", _HTML)

    def test_focus_entry_in_nav_exists(self):
        self.assertIn("function focusEntryInNav", _HTML)

    def test_navigate_calls_focus_not_select_entry(self):
        fn_start = _HTML.index("function navigateToEventId")
        snippet = _HTML[fn_start:fn_start + 200]
        self.assertIn("focusEntryInNav", snippet)
        self.assertNotIn("selectEntry", snippet)

    def test_scroll_into_view_used(self):
        self.assertIn("scrollIntoView", _HTML)

    def test_turn_hdr_has_data_tkey(self):
        self.assertIn("turnHdr.dataset.tkey = turnKey", _HTML)

    def test_filter_hidden_hint_shown(self):
        fn_start = _HTML.index("function focusEntryInNav")
        snippet = _HTML[fn_start:fn_start + 2300]
        self.assertIn("目标事件被当前筛选隐藏", snippet)

    def test_nav_flash_css_exists(self):
        self.assertIn(".nav-flash", _HTML)


class TestWorkbenchReviewFixes(unittest.TestCase):
    """Review Fix 8 — static coverage for second-review regressions."""

    def test_style_tag_closes_before_mermaid_script(self):
        style_close = _HTML.index("</style>")
        mermaid_script = _HTML.index("mermaid.min.js")
        self.assertLess(style_close, mermaid_script)

    def test_events_to_entries_assigns_event_id_on_each_pushed_entry(self):
        fn_start = _HTML.index("function eventsToEntries")
        fn_end = _HTML.index("// ── Load session entries", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertGreaterEqual(snippet.count("_eventId,"), 6)
        self.assertIn("if (!pushed && _eventId && entries.length > 0)", snippet)

    def test_overview_turn_count_uses_entry_turn_keys(self):
        fn_start = _HTML.index("function renderOverviewPage")
        fn_end = _HTML.index("function renderTimelinePage", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("new Set(allEntries.map(e => e._turnKey).filter(Boolean))", snippet)
        self.assertNotIn("Object.keys(turnCollapsed).length", snippet)

    def test_analysis_cache_writes_by_cache_key_and_session_id(self):
        fn_start = _HTML.index("async function runAnalysisForCurrentSession")
        fn_end = _HTML.index("function analyzeCurrentSession", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("analysisReports[cacheKey] = cached", snippet)
        self.assertIn("analysisReports[sessionId] = cached", snippet)
        self.assertIn("analysisReports[preserveKey] = previous", snippet)

    def test_session_analysis_button_is_visible_in_session_toolbar(self):
        self.assertIn('id="sessionAnalyzeBtn"', _HTML)
        self.assertIn('onclick="analyzeCurrentSession()"', _HTML)
        self.assertIn("报告分析", _HTML)

    def test_analysis_no_longer_navigates_to_missing_evidence_page(self):
        self.assertNotIn("navigateToPage('evidence')", _HTML)
        self.assertIn("function ensureSessionAnalysisPanel", _HTML)
        self.assertIn("navigateToPage('sessions')", _HTML)


if __name__ == "__main__":
    unittest.main()


class TestViewerWorkbenchBugFixes(unittest.TestCase):
    """Regression tests for viewer workbench bug fixes."""

    def test_show_view_no_early_return_on_same_view(self):
        """showView must not early-return when viewId == activeView."""
        fn_start = _HTML.index("function showView(viewId)")
        fn_end = _HTML.index("function _renderView(viewId)", fn_start)
        snippet = _HTML[fn_start:fn_end]
        # The early return based on same view must be gone
        self.assertNotIn("if (activeView === viewId) return;", snippet)
        # _renderView must always be called
        self.assertIn("_renderView(viewId)", snippet)

    def test_render_view_helper_exists(self):
        """_renderView helper must exist and handle all views."""
        self.assertIn("function _renderView(viewId)", _HTML)
        fn_start = _HTML.index("function _renderView(viewId)")
        snippet = _HTML[fn_start:fn_start + 600]
        self.assertIn("'tasks'", snippet)
        self.assertIn("'overview'", snippet)
        self.assertIn("'sessions'", snippet)

    def test_load_session_calls_render_view_after_success(self):
        """loadSession must call _renderView(activeView) after successfully loading."""
        fn_start = _HTML.index("async function loadSession()")
        fn_end = _HTML.index("} catch(e) {", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("_renderView(activeView)", snippet)

    def test_agent_badge_no_hardcoded_claude_fallback(self):
        """agentBadge must not fall back to hardcoded 'claude' string."""
        fn_start = _HTML.index("async function init()")
        fn_end = fn_start + 1500
        snippet = _HTML[fn_start:fn_end]
        # Must not assign hardcoded 'claude'
        self.assertNotIn("agentBadge.textContent = 'claude'", snippet)

    def test_session_agent_updates_badge(self):
        """loadSession must update agentBadge from actual session data."""
        fn_start = _HTML.index("async function loadSession()")
        fn_end = _HTML.index("} catch(e) {", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("agentBadgeEl", snippet)
        self.assertIn("sessionAgent", snippet)

    def test_agent_badge_default_is_neutral(self):
        """agentBadge initial HTML value must not be hardcoded 'claude'."""
        # Find the span element itself
        idx = _HTML.index('id="agentBadge"')
        snippet = _HTML[max(0, idx - 50):idx + 80]
        self.assertNotIn(">claude<", snippet)

    def test_dom_content_loaded_calls_init(self):
        """DOMContentLoaded must trigger init so page auto-initializes on open."""
        self.assertIn("DOMContentLoaded", _HTML)
        self.assertIn("addEventListener('DOMContentLoaded', init)", _HTML)
