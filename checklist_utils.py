"""Pure checklist operations shared by the UI and tests."""

from __future__ import annotations

from datetime import date
from typing import Any


def checklist_progress(tasks: list[dict[str, Any]]) -> tuple[int, int, float]:
    """Return completed count, task count, and completion fraction."""
    if not isinstance(tasks, list):
        raise ValueError("Checklist tasks must be a list.")
    completed_count = 0
    for task in tasks:
        if not isinstance(task, dict) or type(task.get("completed")) is not bool:
            raise ValueError("Each checklist task needs a boolean completion status.")
        completed_count += task["completed"]
    total = len(tasks)
    return completed_count, total, completed_count / total if total else 0.0


def filter_checklist_tasks(
    tasks: list[dict[str, Any]],
    status: str,
) -> list[dict[str, Any]]:
    """Filter tasks by all, completed, or pending status."""
    if status == "all":
        return list(tasks)
    if status == "completed":
        return [task for task in tasks if task.get("completed") is True]
    if status == "pending":
        return [task for task in tasks if task.get("completed") is False]
    raise ValueError("Checklist status must be all, completed, or pending.")


def is_task_overdue(task: dict[str, Any], today: date) -> bool:
    """A task is overdue only when it is pending and has a past due date."""
    due_date = task.get("due_date")
    if task.get("completed") or due_date is None:
        return False
    try:
        parsed_due_date = due_date if isinstance(due_date, date) else date.fromisoformat(
            due_date
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Checklist due date must be an ISO date.") from error
    return parsed_due_date < today
