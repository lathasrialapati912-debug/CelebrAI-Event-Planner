from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import app_resources
from expense_utils import calculate_expense_summary
from translations import (
    ENGLISH,
    TRANSLATIONS,
    missing_translation_keys,
    translate,
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


def test_language_preference_is_available_and_preserves_event_input():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run(
        timeout=30
    )

    assert not app.exception
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
