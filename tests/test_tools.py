"""
Integration unit tests for tools.py module.
Tests add_assignment(), get_upcoming(), and error handling.
"""

import sys
import os
from datetime import date
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory import AssignmentMemory
from tools import add_assignment, get_upcoming


def test_add_assignment_tool_success():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    res = add_assignment(name="DBMS Assignment", due="2026-09-02", memory=mem, ref_date=ref)
    assert res["success"] is True
    assert res["assignment"] == "DBMS Assignment"
    assert res["due"] == "2026-09-02"
    assert res["days_remaining"] == 4
    assert res["status"] == "HIGH"
    assert "gcal_link" in res


def test_add_assignment_tool_invalid_date():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    res = add_assignment(name="DBMS Assignment", due="September 35", memory=mem, ref_date=ref)
    assert res["success"] is False
    assert res["error"] == "invalid_date"


def test_add_assignment_tool_missing_deadline():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    res = add_assignment(name="DBMS Assignment", due="", memory=mem, ref_date=ref)
    assert res["success"] is False
    assert res["error"] == "missing_deadline"


def test_get_upcoming_tool():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    add_assignment(name="DSA Assignment", due="2026-09-05", memory=mem, ref_date=ref)
    add_assignment(name="DBMS Assignment", due="2026-09-02", memory=mem, ref_date=ref)

    upcoming = get_upcoming(memory=mem, ref_date=ref)
    assert isinstance(upcoming, list)
    assert len(upcoming) == 2
    assert upcoming[0]["name"] == "DBMS Assignment"
    assert upcoming[1]["name"] == "DSA Assignment"
