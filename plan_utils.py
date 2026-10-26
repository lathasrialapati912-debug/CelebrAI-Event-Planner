"""Validation and JSON encoding for downloadable CelebrAI plan backups."""

from __future__ import annotations

from datetime import date
import json
import math
from numbers import Real
from typing import Any

from translations import LANGUAGES


MAX_BACKUP_BYTES = 1_048_576
MAX_EXPENSES = 500
MAX_CHECKLIST_ITEMS = 500
PLAN_VERSION = 1

_EVENT_TYPES = {
    "Wedding",
    "Birthday",
    "College Fest",
    "Anniversary",
    "Community Celebration",
}
_EVENT_THEMES = {
    "Royal & Luxurious",
    "Traditional Indian",
    "Elegant & Minimal",
    "Colorful & Fun",
    "Modern & Futuristic",
}
_VISUAL_THEMES = {
    "Royal Purple",
    "Rose Gold",
    "Ocean Dream",
    "Emerald Elegance",
    "Midnight Galaxy",
}
_FONTS = {"Modern", "Elegant", "Playful", "Futuristic"}
_INVITATION_STYLES = {
    "Royal Gold",
    "Rose Romance",
    "Midnight Purple",
    "Emerald Elegance",
}
_EXPENSE_CATEGORIES = {
    "Venue",
    "Food",
    "Decoration",
    "Photography",
    "Entertainment",
    "Transport",
    "Gifts",
    "Other",
}
_CHECKLIST_STAGES = {
    "four_weeks",
    "three_weeks",
    "two_weeks",
    "one_week",
    "two_days",
    "event_day",
    "custom",
}


def _require_object(value: Any, expected_keys: set[str], field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    if set(value) != expected_keys:
        raise ValueError(f"{field} has missing or unsupported fields.")
    return value


def _require_text(
    value: Any,
    field: str,
    *,
    max_length: int,
    choices: set[str] | None = None,
) -> str:
    if not isinstance(value, str) or len(value) > max_length or "\x00" in value:
        raise ValueError(f"{field} must be text of at most {max_length} characters.")
    if choices is not None and value not in choices:
        raise ValueError(f"{field} has an unsupported value.")
    return value


def _require_number(
    value: Any,
    field: str,
    *,
    minimum: float,
    maximum: float,
) -> int | float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a number.")
    try:
        is_finite = math.isfinite(value)
    except OverflowError:
        is_finite = False
    if not is_finite:
        raise ValueError(f"{field} must be finite.")
    if value < minimum or value > maximum:
        raise ValueError(f"{field} must be between {minimum:g} and {maximum:g}.")
    return value


def _require_date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO date.") from error
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be an ISO date.")
    return value


def validate_event_plan(data: Any) -> dict[str, Any]:
    """Validate a versioned backup and return a normalized copy."""
    top_level = _require_object(
        data,
        {"version", "event", "preferences", "expense_budget", "expenses",
         "checklist", "invitation"},
        "Plan",
    )
    if type(top_level["version"]) is not int or top_level["version"] != PLAN_VERSION:
        raise ValueError("This event-plan backup version is not supported.")

    event = _require_object(
        top_level["event"],
        {"type", "name", "location", "budget", "guests", "theme", "date"},
        "Event",
    )
    normalized_event = {
        "type": _require_text(event["type"], "Event type", max_length=40,
                              choices=_EVENT_TYPES),
        "name": _require_text(event["name"], "Event name", max_length=120),
        "location": _require_text(event["location"], "Event location",
                                  max_length=200),
        "budget": _require_number(event["budget"], "Event budget",
                                  minimum=5000, maximum=500000),
        "guests": _require_number(event["guests"], "Guest count",
                                  minimum=1, maximum=10000),
        "theme": _require_text(event["theme"], "Event theme", max_length=40,
                               choices=_EVENT_THEMES),
        "date": _require_date(event["date"], "Event date"),
    }
    if type(normalized_event["guests"]) is not int:
        raise ValueError("Guest count must be a whole number.")

    preferences = _require_object(
        top_level["preferences"],
        {"language", "visual_theme", "font"},
        "Preferences",
    )
    normalized_preferences = {
        "language": _require_text(preferences["language"], "Language",
                                  max_length=40, choices=set(LANGUAGES)),
        "visual_theme": _require_text(
            preferences["visual_theme"], "Visual theme", max_length=40,
            choices=_VISUAL_THEMES,
        ),
        "font": _require_text(preferences["font"], "Font", max_length=20,
                              choices=_FONTS),
    }

    expense_budget = _require_number(
        top_level["expense_budget"], "Expense budget",
        minimum=1000, maximum=10000000,
    )
    expenses = top_level["expenses"]
    if not isinstance(expenses, list) or len(expenses) > MAX_EXPENSES:
        raise ValueError(f"Expenses must be a list of at most {MAX_EXPENSES} items.")
    normalized_expenses = []
    expense_keys = {
        "Expense", "Category", "Estimated Cost (₹)", "Actual Cost (₹)"
    }
    for index, raw_expense in enumerate(expenses):
        item = _require_object(raw_expense, expense_keys, f"Expense {index + 1}")
        row = {
            "Expense": _require_text(item["Expense"], "Expense name",
                                     max_length=200),
            "Category": _require_text(
                item["Category"], "Expense category", max_length=40,
                choices=_EXPENSE_CATEGORIES,
            ),
        }
        for key in ("Estimated Cost (₹)", "Actual Cost (₹)"):
            amount = item[key]
            row[key] = None if amount is None else _require_number(
                amount, key, minimum=0, maximum=1000000000
            )
        normalized_expenses.append(row)

    checklist = top_level["checklist"]
    if not isinstance(checklist, list) or len(checklist) > MAX_CHECKLIST_ITEMS:
        raise ValueError(
            f"Checklist must be a list of at most {MAX_CHECKLIST_ITEMS} items."
        )
    normalized_checklist = []
    checklist_keys = {"id", "stage", "task", "completed", "due_date"}
    for index, raw_task in enumerate(checklist):
        task = _require_object(raw_task, checklist_keys, f"Checklist item {index + 1}")
        task_id = _require_text(task["id"], "Checklist ID", max_length=80)
        if not task_id:
            raise ValueError("Checklist IDs cannot be empty.")
        stage = _require_text(task["stage"], "Checklist stage", max_length=20,
                              choices=_CHECKLIST_STAGES)
        description = _require_text(task["task"], "Checklist task",
                                    max_length=300)
        if not description.strip():
            raise ValueError("Checklist tasks cannot be empty.")
        if type(task["completed"]) is not bool:
            raise ValueError("Checklist completion status must be true or false.")
        due_date = task["due_date"]
        if due_date is not None:
            due_date = _require_date(due_date, "Checklist due date")
        normalized_checklist.append({
            "id": task_id,
            "stage": stage,
            "task": description,
            "completed": task["completed"],
            "due_date": due_date,
        })

    invitation = _require_object(
        top_level["invitation"],
        {"title", "date", "location", "message", "style"},
        "Invitation",
    )
    normalized_invitation = {
        "title": _require_text(invitation["title"], "Invitation title",
                               max_length=120),
        "date": _require_date(invitation["date"], "Invitation date"),
        "location": _require_text(invitation["location"], "Invitation location",
                                  max_length=200),
        "message": _require_text(invitation["message"], "Invitation message",
                                 max_length=1000),
        "style": _require_text(invitation["style"], "Invitation style",
                               max_length=40, choices=_INVITATION_STYLES),
    }

    return {
        "version": PLAN_VERSION,
        "event": normalized_event,
        "preferences": normalized_preferences,
        "expense_budget": expense_budget,
        "expenses": normalized_expenses,
        "checklist": normalized_checklist,
        "invitation": normalized_invitation,
    }


def encode_event_plan(data: Any) -> bytes:
    """Validate and encode a plan as bounded UTF-8 JSON."""
    validated = validate_event_plan(data)
    try:
        encoded = json.dumps(
            validated,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("The event plan could not be encoded.") from error
    if len(encoded) > MAX_BACKUP_BYTES:
        raise ValueError(f"Event-plan backups cannot exceed {MAX_BACKUP_BYTES} bytes.")
    return encoded


def decode_event_plan(contents: bytes) -> dict[str, Any]:
    """Decode and validate an uploaded UTF-8 JSON backup without executing it."""
    if not isinstance(contents, bytes):
        raise ValueError("The backup must be uploaded as a file.")
    if len(contents) > MAX_BACKUP_BYTES:
        raise ValueError(f"Event-plan backups cannot exceed {MAX_BACKUP_BYTES} bytes.")
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The backup must use UTF-8 encoding.") from error

    def reject_constant(value: str) -> None:
        raise ValueError(f"Unsupported numeric value: {value}.")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("The backup contains duplicate object keys.")
            result[key] = value
        return result

    try:
        data = json.loads(
            text,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_keys,
        )
    except json.JSONDecodeError as error:
        raise ValueError("The backup is not valid JSON.") from error
    except RecursionError as error:
        raise ValueError("The backup structure is too deeply nested.") from error
    except ValueError:
        raise
    return validate_event_plan(data)
