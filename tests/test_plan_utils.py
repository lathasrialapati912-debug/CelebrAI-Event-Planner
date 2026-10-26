import pytest

from plan_utils import (
    MAX_BACKUP_BYTES,
    decode_event_plan,
    encode_event_plan,
    validate_event_plan,
)


def valid_plan():
    return {
        "version": 1,
        "event": {
            "type": "Birthday",
            "name": "Maya's celebration",
            "location": "Chennai",
            "budget": 125000,
            "guests": 75,
            "theme": "Colorful & Fun",
            "date": "2027-05-12",
        },
        "preferences": {
            "language": "English",
            "visual_theme": "Ocean Dream",
            "font": "Modern",
        },
        "expense_budget": 100000,
        "expenses": [
            {
                "Expense": "Catering",
                "Category": "Food",
                "Estimated Cost (₹)": 25000.5,
                "Actual Cost (₹)": None,
            }
        ],
        "checklist": [
            {
                "id": "task-1",
                "stage": "two_weeks",
                "task": "Confirm the guest list",
                "completed": False,
                "due_date": "2027-04-28",
            }
        ],
        "invitation": {
            "title": "மாயாவின் பிறந்தநாள்",
            "date": "2027-05-12",
            "location": "Chennai",
            "message": "Join us to celebrate!",
            "style": "Royal Gold",
        },
    }


def test_plan_round_trip_preserves_unicode_and_expense_values():
    encoded = encode_event_plan(valid_plan())

    assert decode_event_plan(encoded) == validate_event_plan(valid_plan())
    assert "மாயாவின் பிறந்தநாள்".encode("utf-8") in encoded


@pytest.mark.parametrize(
    "mutate",
    [
        lambda plan: plan.update(version=2),
        lambda plan: plan["event"].update(guests=True),
        lambda plan: plan["event"].update(guests=0),
        lambda plan: plan["event"].update(name=object()),
        lambda plan: plan["event"].update(date="not-a-date"),
        lambda plan: plan["expenses"][0].update(
            **{"Actual Cost (₹)": float("inf")}
        ),
        lambda plan: plan["expenses"][0].update(Category="Untrusted"),
        lambda plan: plan["checklist"][0].update(completed="no"),
        lambda plan: plan["preferences"].update(api_key="secret"),
        lambda plan: plan.update(unexpected="data"),
    ],
)
def test_invalid_plan_data_is_rejected(mutate):
    plan = valid_plan()
    mutate(plan)

    with pytest.raises(ValueError):
        validate_event_plan(plan)


def test_missing_fields_and_too_many_expenses_are_rejected():
    plan = valid_plan()
    del plan["event"]["name"]
    with pytest.raises(ValueError, match="missing or unsupported"):
        validate_event_plan(plan)

    plan = valid_plan()
    plan["expenses"] *= 501
    with pytest.raises(ValueError, match="at most"):
        validate_event_plan(plan)


@pytest.mark.parametrize(
    "contents, message",
    [
        (b"\xff", "UTF-8"),
        (b"{bad json", "valid JSON"),
        (b'{"version":1,"version":1}', "duplicate"),
        (b'{"value":NaN}', "Unsupported numeric"),
    ],
)
def test_invalid_upload_content_is_rejected(contents, message):
    with pytest.raises(ValueError, match=message):
        decode_event_plan(contents)


def test_oversized_upload_is_rejected_before_json_parsing():
    with pytest.raises(ValueError, match="cannot exceed"):
        decode_event_plan(b" " * (MAX_BACKUP_BYTES + 1))


def test_deep_array_backup_with_invalid_root_is_rejected():
    nested_json = b"[" * 10000 + b"]" * 10000

    with pytest.raises(ValueError, match="Plan must be an object"):
        decode_event_plan(nested_json)


def test_export_rejects_non_json_values():
    plan = valid_plan()
    plan["event"]["budget"] = float("nan")

    with pytest.raises(ValueError, match="finite"):
        encode_event_plan(plan)


def test_decoder_does_not_execute_uploaded_content():
    with pytest.raises(ValueError):
        decode_event_plan(b'{"__import__": "os"}')
