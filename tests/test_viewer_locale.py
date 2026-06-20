"""Static regression checks for the shared Viewer language switch."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_HTML = (ROOT / "viewer" / "claude-log.html").read_text(encoding="utf-8")
REQ_RESP_HTML = (ROOT / "viewer" / "req-resp.html").read_text(encoding="utf-8")


class ViewerLocaleTests(unittest.TestCase):
    def test_both_viewers_use_the_same_persisted_locale_key(self) -> None:
        for html in (MAIN_HTML, REQ_RESP_HTML):
            self.assertIn("const CCWHAT_LOCALE_KEY = 'ccwhat-locale'", html)
            self.assertIn('function applyLocale()', html)
            self.assertIn('function toggleLocale()', html)
            self.assertIn('id="languageBtn"', html)

    def test_locale_layer_does_not_translate_raw_evidence(self) -> None:
        for html in (MAIN_HTML, REQ_RESP_HTML):
            self.assertIn('only marked ui copy is localized', html.lower())

    def test_main_viewer_localizes_event_type_display_names(self) -> None:
        self.assertIn('data-i18n="filter_user">用户', MAIN_HTML)
        self.assertIn("kind_user_message: '用户'", MAIN_HTML)
        self.assertIn("kind_user_message: 'User'", MAIN_HTML)
        self.assertIn('function kindLabel(kind)', MAIN_HTML)

    def test_dynamic_project_and_session_selectors_use_localized_placeholders(self) -> None:
        self.assertIn("t('project_placeholder')", MAIN_HTML)
        self.assertIn("t('session_placeholder')", MAIN_HTML)
        self.assertIn('data-i18n-title="project"', MAIN_HTML)
        self.assertIn('data-i18n-title="session"', MAIN_HTML)

    def test_session_count_summary_uses_localized_labels(self) -> None:
        self.assertIn("t('steps')", MAIN_HTML)
        self.assertIn("t('total_turns')", MAIN_HTML)
        self.assertIn("t('entries')", MAIN_HTML)
        self.assertIn("updateSessionCountBadge();", MAIN_HTML)

    def test_trace_toolbar_and_overlay_status_use_localized_copy(self) -> None:
        for key in [
            'default_view', 'debug_view', 'expand_all', 'collapse_all',
            'edit_task_trace', 'create_task', 'no_overlay',
        ]:
            self.assertIn(f'data-i18n="{key}"', MAIN_HTML)
        self.assertIn("status.textContent = t('no_overlay')", MAIN_HTML)

    def test_project_and_session_empty_states_use_localized_copy(self) -> None:
        self.assertIn('data-i18n="select_project_and_session"', MAIN_HTML)
        self.assertIn("t('select_project_and_session')", MAIN_HTML)
        self.assertIn("t('select_project_and_session_for_tasks')", MAIN_HTML)
        self.assertIn("t('no_matching_projects')", MAIN_HTML)
        self.assertIn("t('select_project_to_view_sessions')", MAIN_HTML)
