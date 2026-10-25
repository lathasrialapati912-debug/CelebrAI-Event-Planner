import pandas as pd
import pytest

import app_resources
from expense_utils import calculate_expense_summary


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
