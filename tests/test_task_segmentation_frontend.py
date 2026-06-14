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


class TestTaskDatasetSaveExportFrontend(unittest.TestCase):
    """Dataset save/export viewer surface."""

    def test_save_dataset_entry_and_modal_exist(self):
        self.assertIn('id="saveTaskDatasetBtn"', _HTML)
        self.assertIn('onclick="openDatasetSaveModal()"', _HTML)
        self.assertIn('id="datasetSaveOverlay"', _HTML)
        self.assertIn("保存 Dataset", _HTML)
        self.assertIn("保存并下载 .tar.gz", _HTML)

    def test_modal_lists_dataset_v1_required_files(self):
        modal_start = _HTML.index('id="datasetSaveOverlay"')
        modal_end = _HTML.index("<!-- Mode selection modal -->", modal_start)
        snippet = _HTML[modal_start:modal_end]
        for required in ["manifest.json", "dataset.jsonl", "traces/*.json", "scores.jsonl 空文件"]:
            self.assertIn(required, snippet)

    def test_dataset_modal_hides_raw_source_options(self):
        modal_start = _HTML.index('id="datasetSaveOverlay"')
        modal_end = _HTML.index("<!-- Mode selection modal -->", modal_start)
        snippet = _HTML[modal_start:modal_end].lower()
        self.assertNotIn("raw session", snippet)
        self.assertNotIn("raw req", snippet)
        self.assertNotIn("checkbox", snippet)

    def test_dirty_overlay_blocks_dataset_save(self):
        fn_start = _HTML.index("function buildDatasetSavePayload")
        fn_end = _HTML.index("function openDatasetSaveModal", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("hasDirtyTaskTraceOverlay(sessionId)", snippet)
        self.assertIn("未保存修改", snippet)
        self.assertIn("throw new Error", snippet)

    def test_saved_overlay_preferred_over_task_segments(self):
        fn_start = _HTML.index("function buildDatasetSavePayload")
        fn_end = _HTML.index("function openDatasetSaveModal", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("datasetSavedOverlaySource(sessionId) || datasetTaskSegmentsSource(sessionId)", snippet)
        self.assertIn("taskSource: 'activeOverlay'", _HTML)
        self.assertIn("taskSource: 'taskSegments'", _HTML)

    def test_save_request_payload_includes_source_versions_and_provenance(self):
        self.assertIn("DATASET_OVERLAY_VERSION", _HTML)
        self.assertIn("DATASET_TASK_SEGMENTATION_SCHEMA_VERSION", _HTML)
        self.assertIn("overlayVersion", _HTML)
        self.assertIn("sourceSchemaVersion", _HTML)
        self.assertIn("provenance", _HTML)
        self.assertIn("sourceTrace", _HTML)
        self.assertIn("includeRawSession: false", _HTML)
        self.assertIn("includeReqResp: false", _HTML)

    def test_save_endpoint_and_download_trigger_exist(self):
        self.assertIn("/api/save-task-dataset", _HTML)
        self.assertIn("function triggerDatasetDownload", _HTML)
        self.assertIn("data.downloadUrl", _HTML)


class TestSessionTasksWorkbenchScope(unittest.TestCase):
    """Session + Tasks scoped workbench regression tests."""

    def test_session_is_default_active_page(self):
        self.assertIn("activeView: 'sessions'", _HTML)
        session_nav_idx = _HTML.index('data-page="sessions"')
        session_nav_snippet = _HTML[max(0, session_nav_idx - 80):session_nav_idx + 160]
        self.assertIn("nav-item active", session_nav_snippet)

    def test_left_nav_core_modules_are_present(self):
        nav_start = _HTML.index('<nav class="left-nav">')
        nav_end = _HTML.index('</nav>', nav_start)
        nav = _HTML[nav_start:nav_end]
        for page in [
            "sessions",
            "tasks",
            "overview",
            "timeline",
            "reqresp",
            "differential",
            "diagnostics",
            "export",
            "settings",
        ]:
            self.assertIn(f'data-page="{page}"', nav)
        self.assertIn('> Session', nav)
        self.assertIn('> Tasks', nav)
        self.assertIn('> Req / Resp', nav)
        self.assertIn('> Diff', nav)

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
        # loadSession must refresh the active workbench page after loading
        self.assertIn("renderPage(workbenchState.activeView)", snippet)


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

    def test_tasks_page_waits_for_manual_segmentation(self):
        fn_start = _HTML.index("function renderTasksPage")
        fn_end = _HTML.index("function renderReqRespPage", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("sessionId !== currentLoadedSessionId", snippet)
        self.assertIn("当前 Session 尚未生成任务切分结果", snippet)
        self.assertIn('onclick="onTaskSegmentsBtnClick()"', snippet)
        self.assertIn('onclick="startManualTaskSegmentationFromTasks()"', snippet)
        self.assertNotIn("正在切分当前 Session 的任务", snippet)

    def test_manual_segmentation_functions_exist(self):
        for name in [
            "startManualTaskSegmentationFromTasks",
            "createManualSegmentTask",
            "undoLastManualSegmentTask",
            "completeManualTaskSegmentation",
            "cancelManualTaskSegmentation",
        ]:
            self.assertIn(f"function {name}", _HTML)

    def test_task_runner_accepts_navigation_option(self):
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        fn_end = _HTML.index("// 3.1-3.4", fn_start)
        snippet = _HTML[fn_start:fn_end]
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
        self.assertIn("定位起始会话", _HTML)

    def test_end_event_nav_label(self):
        self.assertIn("定位结束会话", _HTML)

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
        fn_end = _HTML.index("// 3.1-3.4", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("currentSession !== sessionId", snippet)

    def test_stale_guard_in_catch_path(self):
        """P1: failure/catch path must also check current session (stale guard)."""
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        fn_end = _HTML.index("// 3.1-3.4", fn_start)
        snippet = _HTML[fn_start:fn_end]
        # Must appear in both try (success) and catch (failure) paths
        first_guard = snippet.index("currentSession !== sessionId")
        second_guard = snippet.index("currentSession !== sessionId", first_guard + 1)
        self.assertIsNotNone(second_guard)

    def test_stale_guard_still_caches_result(self):
        """P1: stale guard must cache result before returning."""
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        fn_end = _HTML.index("// 3.1-3.4", fn_start)
        snippet = _HTML[fn_start:fn_end]
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
        snippet = _HTML[fn_start:fn_start + 1200]
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


class TestEditableTaskTraceOverlayStatic(unittest.TestCase):
    """Static coverage for editable Task Trace Overlay change."""

    def test_overlay_state_declared(self):
        for name in [
            "taskTraceOverlaysBySession",
            "activeTaskTraceOverlayBySession",
            "savedTaskTraceOverlayBySession",
        ]:
            self.assertIn(name, _HTML)

    def test_edit_mode_state_declared(self):
        for name in ["taskTraceEditMode", "selectedEditableTaskId", "selectedEditableTurnKey", "selectedEditableConversationKey", "manualTaskCreateState"]:
            self.assertIn(name, _HTML)

    def test_overlay_lifecycle_functions_exist(self):
        for name in [
            "createTaskTraceOverlayFromSegments",
            "ensureTaskTraceOverlayFromSegments",
            "setActiveTaskTraceOverlay",
            "markTaskTraceOverlayEdited",
            "saveTaskTraceOverlay",
            "undoTaskTraceOverlay",
            "exportTaskTraceOverlay",
        ]:
            self.assertIn(f"function {name}", _HTML)

    def test_edit_operation_functions_exist(self):
        for name in [
            "setSelectedConversationAsTaskStart",
            "setSelectedConversationAsTaskEnd",
            "setSelectedTurnAsTaskStart",
            "setSelectedTurnAsTaskEnd",
            "moveSelectedConversationToPreviousTask",
            "moveSelectedConversationToNextTask",
            "moveSelectedTurnToPreviousTask",
            "moveSelectedTurnToNextTask",
            "splitTaskAtSelectedConversation",
            "splitTaskAtSelectedTurn",
            "mergeSelectedTaskWithNext",
            "deleteSelectedTask",
            "editSelectedTaskMetadata",
        ]:
            self.assertIn(f"function {name}", _HTML)

    def test_manual_create_functions_exist(self):
        for name in ["startManualTaskCreate", "handleManualTaskConversationSelection", "handleManualTaskTurnSelection", "createManualTaskFromSelection"]:
            self.assertIn(f"function {name}", _HTML)

    def test_trace_consumes_overlay_source(self):
        fn_start = _HTML.index("function getActiveTaskTraceState")
        fn_end = _HTML.index("function expandTaskTraceNodes", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("getActiveTaskTraceOverlay", snippet)
        self.assertIn("taskTraceLikeData", snippet)

    def test_export_uses_overlay_payload_without_raw_trace(self):
        self.assertIn("function overlayExportPayload", _HTML)
        fn_start = _HTML.index("function overlayExportPayload")
        fn_end = _HTML.index("function exportTaskTraceOverlay", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertNotIn("raw", snippet.lower())


if __name__ == "__main__":
    unittest.main()


class TestViewerWorkbenchBugFixes(unittest.TestCase):
    """Regression tests for viewer workbench bug fixes."""

    def test_navigate_to_page_rerenders_same_page(self):
        """navigateToPage must not early-return when the page is already active."""
        fn_start = _HTML.index("function navigateToPage(pageId)")
        fn_end = _HTML.index("function renderPage(pageId)", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertNotIn("return;", snippet.split("renderPage(normalizedPageId)")[0])
        self.assertIn("renderPage(normalizedPageId)", snippet)

    def test_render_page_helper_exists(self):
        """renderPage helper must exist and handle core pages."""
        self.assertIn("function renderPage(pageId)", _HTML)
        fn_start = _HTML.index("function renderPage(pageId)")
        snippet = _HTML[fn_start:fn_start + 600]
        self.assertIn("case 'tasks'", snippet)
        self.assertIn("case 'overview'", snippet)
        self.assertIn("case 'sessions'", snippet)

    def test_load_session_calls_render_page_after_success(self):
        """loadSession must call renderPage(workbenchState.activeView) after success."""
        fn_start = _HTML.index("async function loadSession()")
        fn_end = _HTML.index("} catch(e) {", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("renderPage(workbenchState.activeView)", snippet)

    def test_init_wrapper_removed(self):
        """init must not be wrapped through _origInit, which can recurse."""
        self.assertNotIn("_origInit", _HTML)
        self.assertEqual(_HTML.count("async function init()"), 1)

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


class TestTurnFirstSessionNavigation(unittest.TestCase):
    """4.1 — Turn-first session navigation: Turn helpers, navigation index, Task-to-Turn."""

    # Turn helper and index functions
    def test_rebuild_all_group_turns_exists(self):
        self.assertIn("function rebuildAllGroupTurns", _HTML)

    def test_build_turn_navigation_index_exists(self):
        self.assertIn("function buildTurnNavigationIndex", _HTML)

    def test_lookup_turn_by_event_id_exists(self):
        self.assertIn("function lookupTurnByEventId", _HTML)

    def test_rebuild_turn_task_association_exists(self):
        self.assertIn("function rebuildTurnTaskAssociation", _HTML)

    def test_navigate_to_turn_exists(self):
        self.assertIn("function navigateToTurn", _HTML)

    def test_make_nav_turn_btn_exists(self):
        self.assertIn("function makeNavTurnBtn", _HTML)

    def test_select_turn_function_exists(self):
        self.assertIn("function selectTurn", _HTML)

    def test_render_turn_list_function_exists(self):
        self.assertIn("function renderTurnList", _HTML)

    def test_build_turn_detail_html_exists(self):
        self.assertIn("function buildTurnDetailHtml", _HTML)

    # Turn label generation
    def test_turn_label_format(self):
        fn_start = _HTML.index("function buildTurns")
        snippet = _HTML[fn_start:fn_start + 1500]
        self.assertIn("Turn ${userTurnCount}", snippet)

    def test_build_turns_returns_turn_key(self):
        fn_start = _HTML.index("function buildTurns")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("current.turnKey = tk", snippet)

    def test_turn_navigation_index_state_declared(self):
        self.assertIn("const turnNavigationIndex = {", _HTML)
        self.assertIn("byFileAnchor: new Map()", _HTML)
        self.assertIn("byTurnKey: new Map()", _HTML)

    def test_selected_turn_key_state_declared(self):
        self.assertIn("let selectedTurnKey = null", _HTML)

    def test_all_group_turns_state_declared(self):
        self.assertIn("let allGroupTurns = []", _HTML)

    # Turn navigation in Task detail
    def test_task_overview_shows_start_turn_label(self):
        fn_start = _HTML.index("function renderTabOverview(task)")
        snippet = _HTML[fn_start:fn_start + 600]
        self.assertIn("startConversation", snippet)
        self.assertIn("会话", snippet)

    def test_task_overview_uses_nav_turn_btn(self):
        fn_start = _HTML.index("function renderTabOverview(task)")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("makeNavTurnBtn", snippet)

    def test_task_turns_tab_shows_turn_range(self):
        fn_start = _HTML.index("function renderTabTurns(task)")
        snippet = _HTML[fn_start:fn_start + 1000]
        self.assertIn("startConversation", snippet)
        self.assertIn("endConversation", snippet)
        self.assertIn("定位起始会话", snippet)
        self.assertIn("定位结束会话", snippet)

    def test_task_turns_tab_shows_turn_list(self):
        fn_start = _HTML.index("function renderTabTurns(task)")
        snippet = _HTML[fn_start:fn_start + 1800]
        self.assertIn("rangeTurns", snippet)
        self.assertIn("navigateToTurn", snippet)

    def test_task_turns_tab_has_debug_eventid_section(self):
        fn_start = _HTML.index("function renderTabTurns(task)")
        snippet = _HTML[fn_start:fn_start + 2500]
        self.assertIn("调试", snippet)
        self.assertIn("startEventId", snippet)

    # Turn card CSS
    def test_turn_card_css_exists(self):
        self.assertIn(".turn-card", _HTML)
        self.assertIn(".turn-card.selected", _HTML)

    def test_turn_card_label_css_exists(self):
        self.assertIn(".turn-card-label", _HTML)

    def test_turn_task_badge_css_exists(self):
        self.assertIn(".turn-task-badge", _HTML)

    def test_turn_meta_badge_css_exists(self):
        self.assertIn(".turn-meta-badge", _HTML)

    def test_turn_detail_css_exists(self):
        self.assertIn(".turn-detail", _HTML)
        self.assertIn(".turn-detail-section", _HTML)

    # Session page now renders Turn list
    def test_render_session_page_calls_render_trace_tree(self):
        fn_start = _HTML.index("function renderSessionPage()")
        fn_end = fn_start + 900
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("renderTraceTree()", snippet)

    # rebuild called in loadSession
    def test_load_session_calls_rebuild_all_group_turns(self):
        fn_start = _HTML.index("async function loadSession()")
        fn_end = _HTML.index("} catch(e) {", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertIn("rebuildAllGroupTurns()", snippet)

    # Turn task association rebuild called after segmentation
    def test_task_segments_triggers_turn_association(self):
        fn_start = _HTML.index("async function runTaskSegmentationForCurrentSession")
        snippet = _HTML[fn_start:fn_start + 1000]
        self.assertIn("rebuildTurnTaskAssociation(data)", snippet)

    # navigateToTurn switches to sessions page
    def test_navigate_to_turn_switches_to_sessions(self):
        fn_start = _HTML.index("function navigateToTurn")
        snippet = _HTML[fn_start:fn_start + 2500]
        self.assertIn("navigateToPage('sessions')", snippet)

    def test_navigate_to_turn_triggers_scroll(self):
        fn_start = _HTML.index("function navigateToTurn")
        snippet = _HTML[fn_start:fn_start + 2500]
        self.assertIn("scrollIntoView", snippet)

    # makeNavTurnBtn disabled when Turn not found
    def test_make_nav_turn_btn_disabled_when_not_found(self):
        fn_start = _HTML.index("function makeNavTurnBtn")
        snippet = _HTML[fn_start:fn_start + 400]
        self.assertIn("disabled", snippet)
        self.assertIn("无法定位 Turn", snippet)


class TestStrictTurnRootDetection(unittest.TestCase):
    """Regression: P1 strict isUserTurnRoot, duplicate merging, filter-aware render."""

    def test_is_user_turn_root_function_exists(self):
        self.assertIn("function isUserTurnRoot", _HTML)

    def test_extract_user_text_helper_exists(self):
        self.assertIn("function extractUserText", _HTML)

    def test_normalize_user_text_helper_exists(self):
        self.assertIn("function normalizeUserText", _HTML)

    def test_is_user_turn_root_excludes_system_reminder(self):
        fn_start = _HTML.index("function isUserTurnRoot")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("<system-reminder", snippet)

    def test_is_user_turn_root_excludes_local_command(self):
        fn_start = _HTML.index("function isUserTurnRoot")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("<local-command", snippet)

    def test_is_user_turn_root_excludes_tool_result_only(self):
        fn_start = _HTML.index("function isUserTurnRoot")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("tool_result", snippet)

    def test_is_user_turn_root_duplicate_detection_has_no_asst(self):
        fn_start = _HTML.index("function isUserTurnRoot")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("previousTurn", snippet)
        self.assertIn("hasAsstBetween", snippet)

    def test_build_turns_calls_is_user_turn_root(self):
        fn_start = _HTML.index("function buildTurns")
        snippet = _HTML[fn_start:fn_start + 400]
        self.assertIn("isUserTurnRoot(e,", snippet)

    def test_rebuild_turn_task_association_uses_by_uuid(self):
        fn_start = _HTML.index("function rebuildTurnTaskAssociation")
        snippet = _HTML[fn_start:fn_start + 800]
        self.assertIn("byUuid.get(task.startEventId)", snippet)
        self.assertIn("byUuid.get(task.endEventId)", snippet)

    def test_type_filter_handler_calls_render_page(self):
        # find the actual typeFilters listener block
        type_filters_add_evt = _HTML.index("getElementById('typeFilters').addEventListener('click'")
        listener_snippet = _HTML[type_filters_add_evt:type_filters_add_evt + 800]
        self.assertIn("renderPage(workbenchState.activeView)", listener_snippet)
        self.assertNotIn("renderList()", listener_snippet)

    def test_load_session_does_not_call_render_list_before_render_page(self):
        fn_start = _HTML.index("async function loadSession()")
        fn_end = _HTML.index("} catch(e) {", fn_start)
        snippet = _HTML[fn_start:fn_end]
        # after rebuildAllGroupTurns(), should NOT call renderList()
        rebuild_idx = snippet.index("rebuildAllGroupTurns()")
        after_rebuild = snippet[rebuild_idx:rebuild_idx + 200]
        self.assertNotIn("renderList()", after_rebuild)

    def test_build_turn_detail_uses_complete_raw_entries(self):
        fn_start = _HTML.index("function buildTurnDetailHtml")
        snippet = _HTML[fn_start:fn_start + 1200]
        self.assertIn("const allTurnEntries", snippet)
        self.assertIn("JSON.stringify(allTurnEntries", snippet)
        self.assertNotIn("turn-detail-hint", snippet)


class TestTurnFilterInteractions(unittest.TestCase):
    """Regression: type filters must affect Turn-first visible content."""

    def test_turn_filter_stats_helper_exists(self):
        self.assertIn("function getTurnFilterStats", _HTML)
        self.assertIn("function getVisibleTurnEntries", _HTML)

    def test_render_turn_list_uses_filter_stats(self):
        fn_start = _HTML.index("function renderTurnList")
        snippet = _HTML[fn_start:fn_start + 2400]
        self.assertIn("getTurnFilterStats(turn)", snippet)
        self.assertIn("visibleEntries.length", snippet)
        self.assertIn("hiddenCount", snippet)

    def test_build_turn_detail_does_not_crop_body_to_visible_entries(self):
        fn_start = _HTML.index("function buildTurnDetailHtml")
        snippet = _HTML[fn_start:fn_start + 2500]
        self.assertNotIn("const visibleTurnEntries", snippet)
        self.assertIn("allTurnEntries.filter", snippet)
        self.assertIn("buildTurnEvidenceModel", snippet)


class TestConversationMinimalTurnDataLayer(unittest.TestCase):
    """task 6.1 — Conversation helper, minimal Turn helper, navigation index assertions."""

    # ── Conversation helper ──────────────────────────────────────────────

    def test_build_conversations_function_exists(self):
        self.assertIn("function buildConversations", _HTML)

    def test_is_real_user_request_function_exists(self):
        self.assertIn("function isRealUserRequest", _HTML)

    def test_build_conversations_returns_preamble_and_conversations(self):
        fn = _HTML.index("function buildConversations")
        snippet = _HTML[fn:fn + 1200]
        self.assertIn("preamble", snippet)
        self.assertIn("conversations", snippet)

    def test_conversation_key_format(self):
        fn = _HTML.index("function buildConversations")
        snippet = _HTML[fn:fn + 1200]
        self.assertIn("conversation:", snippet)
        self.assertIn("conversationKey", snippet)

    def test_conversation_label_format(self):
        fn = _HTML.index("function buildConversations")
        snippet = _HTML[fn:fn + 1200]
        self.assertIn("会话", snippet)

    def test_user_message_text_computed(self):
        fn = _HTML.index("function buildConversations")
        snippet = _HTML[fn:fn + 1500]
        self.assertIn("userMessageText", snippet)
        self.assertIn("finalAgentText", snippet)

    # ── MinimalTurn helper ───────────────────────────────────────────────

    def test_build_minimal_turns_function_exists(self):
        self.assertIn("function buildMinimalTurns", _HTML)

    def test_minimal_turn_kinds_declared(self):
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 4000]
        for kind in ["user_message", "tool_use", "tool_result", "assistant_text", "thinking", "context", "system"]:
            self.assertIn(f"'{kind}'", snippet)

    def test_multiblock_assistant_split(self):
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 4000]
        # Multi-block iteration
        self.assertIn("for (let i = 0; i < c.length; i++)", snippet)
        # tool_use block creates separate Turn
        self.assertIn("'tool_use'", snippet)
        self.assertIn("addTurn", snippet)

    def test_block_anchor_generated(self):
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 2000]
        self.assertIn("blockAnchor", snippet)
        self.assertIn("#content:", snippet)

    def test_is_minimal_turn_flag(self):
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 1200]
        self.assertIn("_isMinimalTurn: true", snippet)

    def test_tool_use_id_recorded(self):
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 4000]
        self.assertIn("toolUseId", snippet)
        self.assertIn("toolName", snippet)

    def test_tool_result_records_is_error(self):
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 2500]
        self.assertIn("isError", snippet)
        self.assertIn("resultSummary", snippet)

    # ── Navigation index ─────────────────────────────────────────────────

    def test_by_conversation_key_in_index(self):
        self.assertIn("byConversationKey: new Map()", _HTML)

    def test_by_block_anchor_in_index(self):
        self.assertIn("byBlockAnchor: new Map()", _HTML)

    def test_build_turn_navigation_index_populates_conversation_key(self):
        fn = _HTML.index("function buildTurnNavigationIndex")
        snippet = _HTML[fn:fn + 1200]
        self.assertIn("byConversationKey.set", snippet)
        self.assertIn("byBlockAnchor.set", snippet)

    def test_lookup_conversation_by_event_id_exists(self):
        self.assertIn("function lookupConversationByEventId", _HTML)

    def test_all_group_conversations_state_declared(self):
        self.assertIn("let allGroupConversations = []", _HTML)

    # ── rebuildAllGroupTurns uses new pipeline ───────────────────────────

    def test_rebuild_all_group_turns_calls_build_conversations(self):
        fn = _HTML.index("function rebuildAllGroupTurns")
        snippet = _HTML[fn:fn + 600]
        self.assertIn("buildConversations", snippet)
        self.assertIn("buildMinimalTurns", snippet)

    def test_rebuild_all_group_turns_populates_group_conversations(self):
        fn = _HTML.index("function rebuildAllGroupTurns")
        snippet = _HTML[fn:fn + 600]
        self.assertIn("allGroupConversations", snippet)

    def test_load_session_calls_rebuild_all_group_turns(self):
        fn = _HTML.index("async function loadSession()")
        fn_end = _HTML.index("} catch(e) {", fn)
        snippet = _HTML[fn:fn_end]
        self.assertIn("rebuildAllGroupTurns()", snippet)

    # ── renderTurnList uses Conversations ────────────────────────────────

    def test_render_turn_list_uses_group_conversations(self):
        fn = _HTML.index("function renderTurnList()")
        snippet = _HTML[fn:fn + 2800]
        self.assertIn("allGroupConversations", snippet)
        self.assertIn("conv-hdr", snippet)

    def test_turn_card_has_turn_label_and_kind_badge(self):
        fn = _HTML.index("function renderTurnList()")
        snippet = _HTML[fn:fn + 2800]
        self.assertIn("turn-card-label", snippet)
        self.assertIn("turn-kind-badge", snippet)

    # ── buildMinimalTurnDetailHtml ───────────────────────────────────────

    def test_build_minimal_turn_detail_html_exists(self):
        self.assertIn("function buildMinimalTurnDetailHtml", _HTML)

    def test_minimal_turn_detail_does_not_show_filter_hidden_placeholder(self):
        fn = _HTML.index("function buildMinimalTurnDetailHtml")
        snippet = _HTML[fn:fn + 2000]
        self.assertNotIn("当前筛选隐藏了该 Turn 的全部事件", snippet)
        self.assertNotIn("entryMatchesFilter", snippet)

    def test_minimal_turn_detail_has_tool_use_section(self):
        fn = _HTML.index("function buildMinimalTurnDetailHtml")
        snippet = _HTML[fn:fn + 5200]
        self.assertIn("case 'tool_use':", snippet)
        self.assertIn("case 'tool_result':", snippet)

    # ── kind labels ──────────────────────────────────────────────────────

    def test_kind_label_function_exists(self):
        self.assertIn("function kindLabel", _HTML)

    def test_turn_display_text_function_exists(self):
        self.assertIn("function turnDisplayText", _HTML)

    # ── CSS ──────────────────────────────────────────────────────────────

    def test_conv_hdr_css_exists(self):
        self.assertIn(".conv-hdr", _HTML)
        self.assertIn(".conv-hdr-label", _HTML)

    def test_turn_kind_badge_css_exists(self):
        self.assertIn(".turn-kind-badge", _HTML)
        self.assertIn(".kind-tool_use", _HTML)
        self.assertIn(".kind-tool_result", _HTML)
        self.assertIn(".kind-user_message", _HTML)


class TestConversationBugFixes(unittest.TestCase):
    """Regression tests for three bug fixes in conversation-minimal-turn-data-layer."""

    # Fix 1: isRealUserRequest uses currentConversation, not prevConversation
    def test_is_real_user_request_accepts_current_conversation(self):
        """isRealUserRequest must accept currentConversation, not prevConversation."""
        fn = _HTML.index("function isRealUserRequest")
        snippet = _HTML[fn:fn + 400]
        # Must use currentConversation parameter (not prevConversation)
        self.assertNotIn("prevConversation", snippet)
        self.assertIn("currentConversation", snippet)

    def test_build_conversations_passes_current_not_prev(self):
        """buildConversations must pass current (not a prevConversation variable) to isRealUserRequest."""
        fn = _HTML.index("function buildConversations")
        snippet = _HTML[fn:fn + 1200]
        # Must not have a prevConversation variable
        self.assertNotIn("prevConversation", snippet)
        # Must call isRealUserRequest with current
        self.assertIn("isRealUserRequest(e, current)", snippet)

    def test_is_real_user_request_builds_prev_compat_from_current_entries(self):
        """isRealUserRequest must build prevTurnCompat from currentConversation.entries."""
        fn = _HTML.index("function isRealUserRequest")
        snippet = _HTML[fn:fn + 500]
        self.assertIn("currentConversation.entries", snippet)

    # Fix 2: eventsToEntries reasoning → thinking type
    def test_events_to_entries_reasoning_uses_thinking_block_type(self):
        """reasoning kind must produce type:'thinking' content block, not type:'text'."""
        fn = _HTML.index("function eventsToEntries")
        fn_end = _HTML.index("function ", fn + 10)
        snippet = _HTML[fn:fn_end]
        # Must use type:'thinking' for reasoning events
        self.assertIn("type: 'thinking'", snippet)
        # Must use `thinking:` field
        self.assertIn("thinking:", snippet)
        # Must NOT use type:'text' for reasoning (regression check)
        reasoning_idx = snippet.index("kind === 'reasoning'")
        after_reasoning = snippet[reasoning_idx:reasoning_idx + 300]
        self.assertNotIn("type: 'text'", after_reasoning)

    # Fix 3: unknown entry fallback always generates Turn
    def test_build_minimal_turns_unknown_entry_fallback_is_else_not_elif(self):
        """buildMinimalTurns must use 'else' (not 'else if (type !== unknown)') as final fallback."""
        fn = _HTML.index("function buildMinimalTurns")
        snippet = _HTML[fn:fn + 5600]
        # Must NOT have the broken condition
        self.assertNotIn("e.type !== 'unknown'", snippet)
        # Must have a plain else branch that adds unknown Turn
        self.assertIn("} else {", snippet)
        # That else branch must call addTurn with 'unknown'
        else_pos = snippet.rfind("} else {")
        after_else = snippet[else_pos:else_pos + 100]
        self.assertIn("addTurn('unknown'", after_else)


class TestTraceTreeDualViewUI(unittest.TestCase):
    """trace-tree-dual-view-ui: view mode state, controls, projection consumption."""

    def test_trace_view_mode_state_exists(self):
        self.assertIn("let traceViewMode", _HTML)

    def test_trace_view_mode_controls_html_exists(self):
        self.assertIn('id="traceViewModeControls"', _HTML)
        self.assertIn('data-trace-view="default"', _HTML)
        self.assertIn('data-trace-view="debug"', _HTML)

    def test_set_trace_view_mode_function_exists(self):
        self.assertIn("function setTraceViewMode", _HTML)

    def test_update_trace_view_mode_controls_function_exists(self):
        self.assertIn("function updateTraceViewModeControls", _HTML)

    def test_debug_filters_default_to_full_timeline_until_touched(self):
        self.assertIn("let traceDebugFiltersTouched = false", _HTML)
        self.assertIn("function setAllTraceTypeFiltersChecked", _HTML)
        fn_start = _HTML.index("function setTraceViewMode")
        snippet = _HTML[fn_start:fn_start + 600]
        self.assertIn("mode === 'debug' && !traceDebugFiltersTouched", snippet)
        self.assertIn("setAllTraceTypeFiltersChecked(true)", snippet)

    def test_type_filter_click_marks_debug_filters_touched(self):
        fn_start = _HTML.index("document.getElementById('typeFilters').addEventListener")
        snippet = _HTML[fn_start:fn_start + 400]
        self.assertIn("traceDebugFiltersTouched = true", snippet)

    def test_display_kind_label_function_exists(self):
        self.assertIn("function displayKindLabel", _HTML)

    def test_render_trace_tree_uses_projection(self):
        fn_start = _HTML.index("function renderTraceTree()")
        snippet = _HTML[fn_start:fn_start + 4000]
        self.assertIn("buildTurnViewProjection", snippet)

    def test_default_mode_hides_type_filters(self):
        fn_start = _HTML.index("function updateTraceViewModeControls")
        snippet = _HTML[fn_start:fn_start + 800]
        self.assertIn("typeFilters", snippet)

    def test_get_projection_source_function_exists(self):
        self.assertIn("function getProjectionSource", _HTML)

    def test_active_task_trace_source_function_exists(self):
        self.assertIn("function getActiveTaskTraceState", _HTML)
        self.assertIn("function expandTaskTraceNodes", _HTML)

    def test_projection_source_uses_active_task_state(self):
        fn_start = _HTML.index("function getProjectionSource")
        snippet = _HTML[fn_start:fn_start + 600]
        self.assertIn("getActiveTaskTraceState", snippet)
        self.assertNotIn("isTaskTraceConfirmed", snippet)

    def test_build_trace_nodes_uses_active_task_state(self):
        fn_start = _HTML.index("function buildTraceNodes")
        snippet = _HTML[fn_start:fn_start + 1400]
        self.assertIn("getActiveTaskTraceState", snippet)
        self.assertNotIn("isTaskTraceConfirmed", snippet)

    def test_render_projection_node_card_function_exists(self):
        self.assertIn("function renderProjectionNodeCard", _HTML)

    def test_node_matches_debug_filter_function_exists(self):
        self.assertIn("function nodeMatchesDebugFilter", _HTML)

    def test_step_kind_badge_css_exists(self):
        self.assertIn("step-kind-badge", _HTML)
        self.assertIn("step-user_request", _HTML)
        self.assertIn("step-thinking", _HTML)
        self.assertIn("step-error_signal", _HTML)

    def test_trace_step_card_css_exists(self):
        self.assertIn("trace-step-card", _HTML)


class TestTurnDetailCompleteEvidence(unittest.TestCase):
    """turn-detail-complete-evidence: Detail keeps full evidence independent of filters."""

    def test_evidence_helpers_exist(self):
        self.assertIn("function buildTurnEvidenceModel", _HTML)
        self.assertIn("function renderTurnEvidenceSections", _HTML)
        self.assertIn("function renderRawEvidenceJson", _HTML)

    def test_minimal_detail_does_not_return_filter_hidden_placeholder(self):
        fn_start = _HTML.index("function buildMinimalTurnDetailHtml")
        fn_end = _HTML.index("function renderAgentResponseContent", fn_start)
        snippet = _HTML[fn_start:fn_end]
        self.assertNotIn("entryMatchesFilter", snippet)
        self.assertNotIn("当前筛选隐藏了该 Turn 的全部事件", snippet)

    def test_tool_result_detail_does_not_truncate_result(self):
        fn_start = _HTML.index("function renderTurnEvidenceSections")
        snippet = _HTML[fn_start:fn_start + 4000]
        self.assertIn("renderEvidencePre(resultStr", snippet)
        self.assertNotIn("trunc(resultStr", snippet)

    def test_raw_evidence_includes_entry_and_content_block(self):
        fn_start = _HTML.index("function renderRawEvidenceJson")
        snippet = _HTML[fn_start:fn_start + 900]
        self.assertIn("contentBlock", snippet)
        self.assertIn("entry", snippet)
        self.assertIn("anchors", snippet)
