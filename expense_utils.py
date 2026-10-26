from dataclasses import dataclass
import math

import pandas as pd


EXPENSE_COLUMNS = (
    "Expense",
    "Category",
    "Estimated Cost (₹)",
    "Actual Cost (₹)",
)

DEFAULT_BUDGET_WARNING_THRESHOLD = 0.8


@dataclass(frozen=True)
class ExpenseSummary:
    estimated_total: float
    actual_total: float
    remaining_budget: float
    category_totals: pd.Series
    comparison: pd.DataFrame


def budget_status(
    actual_spending: float,
    budget: float,
    warning_threshold: float = DEFAULT_BUDGET_WARNING_THRESHOLD,
) -> str:
    """Classify spending as within budget, approaching, or exceeded."""
    values = (actual_spending, budget, warning_threshold)
    try:
        spending_value, budget_value, threshold_value = map(float, values)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("Spending, budget, and threshold must be numeric.") from error
    if not all(map(math.isfinite, (spending_value, budget_value, threshold_value))):
        raise ValueError("Spending, budget, and threshold must be finite.")
    if spending_value < 0 or budget_value < 0:
        raise ValueError("Spending and budget cannot be negative.")
    if not 0 < threshold_value <= 1:
        raise ValueError("Warning threshold must be greater than zero and at most one.")
    if spending_value > budget_value:
        return "exceeded"
    if budget_value > 0 and spending_value / budget_value >= threshold_value:
        return "approaching"
    return "within"


def calculate_expense_summary(
    expenses: pd.DataFrame,
    budget: float,
) -> ExpenseSummary:
    """Validate and summarize expense data without mutating the input."""
    missing_columns = set(EXPENSE_COLUMNS).difference(expenses.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Expense data is missing required columns: {missing}.")

    try:
        budget_value = float(budget)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Budget must be a finite, non-negative number."
        ) from error

    if not math.isfinite(budget_value) or budget_value < 0:
        raise ValueError("Budget must be a finite, non-negative number.")

    def get_costs(column: str) -> pd.Series:
        raw_costs = expenses[column]
        costs = pd.to_numeric(raw_costs, errors="coerce")
        malformed = raw_costs.notna() & costs.isna()
        if malformed.any():
            raise ValueError(f"{column} must contain only numeric values.")
        if not costs.map(lambda value: pd.isna(value) or math.isfinite(value)).all():
            raise ValueError(f"{column} must contain only finite values.")
        if costs.lt(0).any():
            raise ValueError(f"{column} cannot contain negative values.")
        return costs.fillna(0).astype(float)

    estimated_costs = get_costs("Estimated Cost (₹)")
    actual_costs = get_costs("Actual Cost (₹)")
    categories = expenses["Category"].fillna("Uncategorized").replace(
        r"^\s*$", "Uncategorized", regex=True
    )
    expense_names = expenses["Expense"].fillna("Unnamed expense").replace(
        r"^\s*$", "Unnamed expense", regex=True
    )

    category_totals = actual_costs.groupby(categories).sum()
    comparison = pd.concat(
        [
            estimated_costs.rename("Estimated Cost (₹)"),
            actual_costs.rename("Actual Cost (₹)"),
        ],
        axis=1,
    )
    comparison.index = expense_names

    actual_total = float(actual_costs.sum())
    return ExpenseSummary(
        estimated_total=float(estimated_costs.sum()),
        actual_total=actual_total,
        remaining_budget=float(budget_value - actual_total),
        category_totals=category_totals,
        comparison=comparison,
    )
