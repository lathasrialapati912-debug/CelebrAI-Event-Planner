import pytest


def calculate_budget(budget, expenses):
    """Calculate total expenses and remaining budget."""
    total_expenses = sum(expenses)
    remaining_budget = budget - total_expenses

    return total_expenses, remaining_budget


def test_budget_calculation():
    total, remaining = calculate_budget(10000, [1500, 2000, 500])

    assert total == 4000
    assert remaining == 6000


def test_budget_with_no_expenses():
    total, remaining = calculate_budget(5000, [])

    assert total == 0
    assert remaining == 5000


def test_budget_exceeded():
    total, remaining = calculate_budget(3000, [2000, 1500])

    assert total == 3500
    assert remaining == -500


def test_budget_exactly_used():
    total, remaining = calculate_budget(3000, [1000, 2000])

    assert total == 3000
    assert remaining == 0


def test_budget_with_decimal_expenses():
    total, remaining = calculate_budget(1000, [100.50, 200.25])

    assert total == pytest.approx(300.75)
    assert remaining == pytest.approx(699.25)


@pytest.mark.parametrize(
    "budget, expenses, expected_total, expected_remaining",
    [
        (1000, [100, 200], 300, 700),
        (5000, [500], 500, 4500),
        (2000, [], 0, 2000),
        (100, [150], 150, -50),
    ],
)
def test_budget_scenarios(
    budget, expenses, expected_total, expected_remaining
):
    total, remaining = calculate_budget(budget, expenses)

    assert total == expected_total
    assert remaining == expected_remaining