from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ExpenseSummary:
    estimated_total: float
    actual_total: float
    remaining_budget: float
    category_totals: pd.Series
    comparison: pd.DataFrame


def calculate_expense_summary(
    expenses: pd.DataFrame,
    budget: float,
) -> ExpenseSummary:
    estimated_costs = expenses["Estimated Cost (₹)"].fillna(0)
    actual_costs = expenses["Actual Cost (₹)"].fillna(0)

    category_totals = actual_costs.groupby(expenses["Category"]).sum()
    comparison = pd.concat(
        [
            estimated_costs.rename("Estimated Cost (₹)"),
            actual_costs.rename("Actual Cost (₹)"),
        ],
        axis=1,
    )
    comparison.index = expenses["Expense"]

    actual_total = float(actual_costs.sum())
    return ExpenseSummary(
        estimated_total=float(estimated_costs.sum()),
        actual_total=actual_total,
        remaining_budget=float(budget - actual_total),
        category_totals=category_totals,
        comparison=comparison,
    )
