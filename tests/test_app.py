from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import app_resources
from expense_utils import budget_status, calculate_expense_summary
from plan_utils import encode_event_plan
from translations import (
    ENGLISH,
    LANGUAGES,
    TRANSLATIONS,
    missing_translation_keys,
    translate,
    translation_key_diagnostics,
)


def make_expenses(actual, estimated=None, categories=None):
    estimated = actual if estimated is None else estimated
    categories = ["Other"] * len(actual) if categories is None else categories
    return pd.DataFrame({
        "Expense": [f"Expense {index}" for index in range(len(actual))],
        "Category": categories,
        "Estimated Cost (₹)": estimated,
        "Actual Cost (₹)": actual,
    })


def make_event_plan_backup():
    return encode_event_plan({
        "version": 1,
        "event": {
            "type": "Birthday",
            "name": "Imported celebration",
            "location": "Pune",
            "budget": 85000,
            "guests": 42,
            "theme": "Colorful & Fun",
            "date": "2027-05-12",
        },
        "preferences": {
            "language": "English",
            "visual_theme": "Ocean Dream",
            "font": "Elegant",
        },
        "expense_budget": 72000,
        "expenses": [{
            "Expense": "Catering",
            "Category": "Food",
            "Estimated Cost (₹)": 25000,
            "Actual Cost (₹)": 23000,
        }],
        "checklist": [{
            "id": "todo-1",
            "stage": "custom",
            "task": "Call venue",
            "completed": True,
            "due_date": "2027-04-01",
        }],
        "invitation": {
            "title": "Imported invitation",
            "date": "2027-05-12",
            "location": "Pune",
            "message": "Welcome!",
            "style": "Rose Romance",
        },
    })


def test_budget_calculation():
    summary = calculate_expense_summary(
        make_expenses([1500, 2000, 500]),
        10000,
    )

    assert summary.actual_total == 4000
    assert summary.remaining_budget == 6000


def test_budget_with_no_expenses():
    summary = calculate_expense_summary(make_expenses([]), 5000)

    assert summary.actual_total == 0
    assert summary.remaining_budget == 5000


def test_budget_exceeded():
    summary = calculate_expense_summary(make_expenses([2000, 1500]), 3000)

    assert summary.actual_total == 3500
    assert summary.remaining_budget == -500


def test_budget_exactly_used():
    summary = calculate_expense_summary(make_expenses([1000, 2000]), 3000)

    assert summary.actual_total == 3000
    assert summary.remaining_budget == 0


def test_budget_with_decimal_expenses():
    summary = calculate_expense_summary(
        make_expenses([100.50, 200.25]),
        1000,
    )

    assert summary.actual_total == pytest.approx(300.75)
    assert summary.remaining_budget == pytest.approx(699.25)


def test_empty_expenses_have_empty_chart_data():
    summary = calculate_expense_summary(make_expenses([]), 5000)

    assert summary.estimated_total == 0
    assert summary.actual_total == 0
    assert summary.remaining_budget == 5000
    assert summary.category_totals.empty
    assert summary.comparison.empty


@pytest.mark.parametrize(
    "budget, actual, expected_total, expected_remaining",
    [
        (1000, [100, 200], 300, 700),
        (5000, [500], 500, 4500),
        (2000, [], 0, 2000),
        (100, [150], 150, -50),
    ],
)
def test_budget_scenarios(
    budget, actual, expected_total, expected_remaining
):
    summary = calculate_expense_summary(make_expenses(actual), budget)

    assert summary.actual_total == expected_total
    assert summary.remaining_budget == expected_remaining


def test_missing_costs_are_zero_in_totals_and_chart_data():
    expenses = make_expenses(
        [100, None, 50],
        estimated=[80, 40, None],
        categories=["Venue", "Food", "Venue"],
    )

    summary = calculate_expense_summary(expenses, 500)

    assert summary.estimated_total == 120
    assert summary.actual_total == 150
    assert summary.remaining_budget == 350
    assert summary.category_totals.to_dict() == {"Food": 0, "Venue": 150}
    assert summary.comparison["Estimated Cost (₹)"].tolist() == [80, 40, 0]
    assert summary.comparison["Actual Cost (₹)"].tolist() == [100, 0, 50]


def test_empty_expense_dataframe_with_schema_is_supported():
    expenses = pd.DataFrame(columns=[
        "Expense",
        "Category",
        "Estimated Cost (₹)",
        "Actual Cost (₹)",
    ])

    summary = calculate_expense_summary(expenses, 5000)

    assert summary.estimated_total == 0
    assert summary.actual_total == 0
    assert summary.remaining_budget == 5000
    assert summary.category_totals.empty
    assert summary.comparison.empty


def test_missing_categories_and_names_are_included_in_chart_data():
    expenses = make_expenses(
        [125],
        estimated=[150],
        categories=[None],
    )
    expenses.loc[0, "Expense"] = None

    summary = calculate_expense_summary(expenses, 500)

    assert summary.category_totals.to_dict() == {"Uncategorized": 125}
    assert summary.comparison.index.tolist() == ["Unnamed expense"]


@pytest.mark.parametrize(
    "budget, costs, message",
    [
        (-1, [10], "Budget"),
        (float("inf"), [10], "Budget"),
        (100, ["not a cost"], "numeric"),
        (100, [-1], "negative"),
        (100, [float("inf")], "finite"),
    ],
)
def test_invalid_budget_and_costs_are_rejected(budget, costs, message):
    with pytest.raises(ValueError, match=message):
        calculate_expense_summary(make_expenses(costs), budget)


def test_missing_expense_columns_are_reported():
    with pytest.raises(ValueError, match="missing required columns"):
        calculate_expense_summary(pd.DataFrame(), 1000)


@pytest.mark.parametrize(
    "spending, budget, expected",
    [
        (0, 0, "within"),
        (799, 1000, "within"),
        (800, 1000, "approaching"),
        (1000, 1000, "approaching"),
        (1001, 1000, "exceeded"),
    ],
)
def test_budget_status_thresholds(spending, budget, expected):
    assert budget_status(spending, budget) == expected


@pytest.mark.parametrize(
    "spending, budget, threshold",
    [
        (-1, 100, 0.8),
        (10, float("inf"), 0.8),
        (10, 100, 0),
        (10, 100, 1.1),
    ],
)
def test_budget_status_rejects_invalid_inputs(spending, budget, threshold):
    with pytest.raises(ValueError):
        budget_status(spending, budget, threshold)


def test_language_preference_is_available_and_preserves_event_input():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run(
        timeout=30
    )

    assert not app.exception
    assert any(
        item.label == translate("download_backup", "English")
        for item in app.download_button
    )
    assert any(
        translate("checklist", "English") in item.value
        for item in app.header
    )
    language_selector = app.selectbox[0]
    assert language_selector.label == "Language"
    assert language_selector.value == "English"
    assert len(language_selector.options) == 12

    next(item for item in app.text_input if item.label == "Event name").set_value(
        "Latha's celebration"
    )
    for key, value in (
        ("theme_selector", "Ocean Dream"),
        ("font_selector", "Elegant"),
    ):
        next(item for item in app.selectbox if item.key == key).select(value)
        app.run(timeout=30)

    for language, heading, action in [
        (
            "తెలుగు (Telugu)",
            "మీ వేడుకల స్టూడియోను అన్వేషించండి",
            "నా వేడుకను రూపొందించండి",
        ),
        (
            "हिन्दी (Hindi)",
            "अपने उत्सव स्टूडियो को देखें",
            "मेरा कार्यक्रम बनाएँ",
        ),
        (
            "தமிழ் (Tamil)",
            "உங்கள் கொண்டாட்ட ஸ்டுடியோவைப் பாருங்கள்",
            "என் நிகழ்வை உருவாக்கு",
        ),
        (
            "ಕನ್ನಡ (Kannada)",
            "ನಿಮ್ಮ ಸಂಭ್ರಮ ಸ್ಟುಡಿಯೋವನ್ನು ಅನ್ವೇಷಿಸಿ",
            "ನನ್ನ ಕಾರ್ಯಕ್ರಮವನ್ನು ರೂಪಿಸಿ",
        ),
        (
            "Français (French)",
            "Découvrez votre studio de célébration",
            "Créer mon événement",
        ),
        (
            "Deutsch (German)",
            "Entdecken Sie Ihr Feier-Studio",
            "Meine Veranstaltung erstellen",
        ),
        (
            "Español (Spanish)",
            "Explora tu estudio de celebraciones",
            "Crear mi evento",
        ),
        (
            "日本語 (Japanese)",
            "お祝いプランニングスタジオ",
            "イベントを作成",
        ),
        (
            "한국어 (Korean)",
            "셀러브레이션 스튜디오 둘러보기",
            "행사 계획 만들기",
        ),
        (
            "中文 (Chinese)",
            "探索庆典规划工作室",
            "生成活动方案",
        ),
        (
            "العربية (Arabic)",
            "اكتشف استوديو التخطيط للاحتفالات",
            "أنشئ خطة المناسبة",
        ),
        (
            "English",
            "Explore Your Celebration Studio",
            "Generate My Dream Event",
        ),
    ]:
        app.selectbox[0].select(language)
        app.run(timeout=30)

        assert not app.exception
        assert app.session_state["celebrai_language"] == language
        assert app.session_state["theme_selector"] == "Ocean Dream"
        assert app.session_state["font_selector"] == "Elegant"
        assert app.session_state["event_expenses"]["Category"].tolist() == [
            "Venue",
            "Food",
            "Decoration",
        ]
        assert any(heading in item.value for item in app.header)
        assert any(action in item.label for item in app.button)
        for feature_key in (
            "feature_ai",
            "feature_budget",
            "feature_invitation",
        ):
            feature_text = translate(feature_key, language)
            assert any(
                feature_text in item.value for item in app.markdown
            )
        assert any(
            translate("expense_tracker", language) in item.value
            for item in app.header
        )
        assert any(
            item.label == translate("event_name", language)
            for item in app.text_input
        )
        event_name = next(
            item for item in app.text_input if item.value == "Latha's celebration"
        )
        assert event_name.value == "Latha's celebration"


def test_checklist_add_edit_and_completion_survive_reruns():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run(
        timeout=30
    )

    next(item for item in app.text_input if item.key == "new_checklist_task").set_value(
        "Book the venue"
    )
    next(item for item in app.button if item.label == "Add task").click()
    app.run(timeout=30)

    task_key = next(
        item.key for item in app.text_input
        if item.key.startswith("checklist_text_")
    )
    assert next(item for item in app.text_input if item.key == task_key).value == (
        "Book the venue"
    )
    assert any(
        "Completed 0 of 1 tasks" in item.value for item in app.markdown
    )

    next(item for item in app.text_input if item.key == task_key).set_value(
        "Book the garden venue"
    )
    app.run(timeout=30)
    task_checkbox = next(
        item for item in app.checkbox
        if item.key.startswith("checklist_completed_")
    )
    task_checkbox.set_value(True)
    app.run(timeout=30)

    assert any(
        "Completed 1 of 1 tasks" in item.value for item in app.markdown
    )
    assert next(item for item in app.text_input if item.key == task_key).value == (
        "Book the garden venue"
    )
    app.selectbox[0].select("Français (French)")
    app.run(timeout=30)
    assert app.session_state["checklist_tasks"][0]["task"] == (
        "Book the garden venue"
    )


def test_valid_backup_restores_event_expenses_checklist_and_preferences():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run(
        timeout=30
    )
    app.file_uploader[0].upload(
        "event-plan.json",
        make_event_plan_backup(),
        "application/json",
    )
    next(item for item in app.button if item.key == "restore_event_plan").click()
    app.run(timeout=30)

    assert not app.exception
    assert app.session_state["event_name"] == "Imported celebration"
    assert app.session_state["event_location"] == "Pune"
    assert app.session_state["event_budget"] == 85000
    assert app.session_state["event_guest_count"] == 42
    assert app.session_state["theme_selector"] == "Ocean Dream"
    assert app.session_state["font_selector"] == "Elegant"
    assert app.session_state["expense_tracker_budget"] == 72000
    assert app.session_state["event_expenses"].iloc[0]["Actual Cost (₹)"] == 23000
    assert app.session_state["checklist_tasks"][0]["task"] == "Call venue"
    assert app.session_state["checklist_tasks"][0]["completed"] is True
    assert app.session_state["invitation_title"] == "Imported invitation"
    assert any("restored" in item.value.lower() for item in app.success)


def test_invalid_backup_does_not_overwrite_current_event():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run(
        timeout=30
    )
    next(item for item in app.text_input if item.key == "event_name").set_value(
        "Keep this event"
    )
    app.file_uploader[0].upload(
        "invalid.json",
        b'{"version": 999}',
        "application/json",
    )
    next(item for item in app.button if item.key == "restore_event_plan").click()
    app.run(timeout=30)

    assert not app.exception
    assert app.session_state["event_name"] == "Keep this event"
    assert any("could not be restored" in item.value for item in app.error)


def test_translation_english_fallback_and_missing_key_diagnostics(monkeypatch):
    assert (
        translate("welcome_title", "Français (French)")
        == "Bienvenue sur CelebrAI"
    )
    assert translate("welcome_title", "unsupported") == ENGLISH["welcome_title"]
    assert translate("unknown_key", "English") == "unknown_key"
    assert missing_translation_keys() == {}

    monkeypatch.delitem(TRANSLATIONS["fr"], "welcome_title")
    assert translate("welcome_title", "Français (French)") == ENGLISH[
        "welcome_title"
    ]


def test_translation_catalog_is_complete_and_has_no_unused_keys():
    assert missing_translation_keys() == {}
    assert translation_key_diagnostics() == {}
    for language in LANGUAGES:
        assert translate("checklist", language)
        assert "{percent}" in TRANSLATIONS[LANGUAGES[language]][
            "budget_approaching"
        ]


def test_repaired_ai_busy_translations_preserve_unicode():
    assert "?" not in TRANSLATIONS["de"]["ai_busy"]
    assert "réessayer" in TRANSLATIONS["fr"]["ai_busy"]
    assert "مؤقتًا" in TRANSLATIONS["ar"]["ai_busy"]


def test_gemini_client_is_reused_per_key_and_separated_between_keys(
    monkeypatch,
):
    created_clients = []

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            created_clients.append(self)

    app_resources.get_gemini_client.clear()
    monkeypatch.setattr(app_resources.genai, "Client", FakeClient)
    try:
        first = app_resources.get_gemini_client("placeholder-key-one")
        repeated = app_resources.get_gemini_client("placeholder-key-one")
        separate = app_resources.get_gemini_client("placeholder-key-two")

        assert first is repeated
        assert first is not separate
        assert len(created_clients) == 2
    finally:
        app_resources.get_gemini_client.clear()
