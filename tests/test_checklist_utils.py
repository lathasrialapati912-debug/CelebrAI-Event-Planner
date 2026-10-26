from datetime import date

import pytest

from checklist_utils import (
    checklist_progress,
    filter_checklist_tasks,
    is_task_overdue,
)


def tasks():
    return [
        {
            "id": "one",
            "task": "Book the venue",
            "completed": True,
            "due_date": "2026-10-20",
        },
        {
            "id": "two",
            "task": "Confirm catering",
            "completed": False,
            "due_date": "2026-10-20",
        },
        {
            "id": "three",
            "task": "Send invitations",
            "completed": False,
            "due_date": None,
        },
    ]


def test_checklist_progress_and_empty_checklist():
    assert checklist_progress(tasks()) == (1, 3, pytest.approx(1 / 3))
    assert checklist_progress([]) == (0, 0, 0.0)


def test_checklist_rejects_invalid_completion_state():
    with pytest.raises(ValueError, match="boolean"):
        checklist_progress([{"completed": "false"}])


@pytest.mark.parametrize(
    "status, expected",
    [
        ("all", 3),
        ("completed", 1),
        ("pending", 2),
    ],
)
def test_checklist_filters_tasks(status, expected):
    assert len(filter_checklist_tasks(tasks(), status)) == expected


def test_checklist_filter_rejects_unknown_status():
    with pytest.raises(ValueError, match="status"):
        filter_checklist_tasks(tasks(), "overdue")


def test_overdue_requires_pending_task_and_due_date():
    today = date(2026, 10, 26)
    assert is_task_overdue(tasks()[1], today)
    assert not is_task_overdue(tasks()[0], today)
    assert not is_task_overdue(tasks()[2], today)
    assert not is_task_overdue(
        {"completed": False, "due_date": "2026-10-26"},
        today,
    )


def test_invalid_due_date_is_reported():
    with pytest.raises(ValueError, match="ISO date"):
        is_task_overdue({"completed": False, "due_date": "soon"}, date.today())
