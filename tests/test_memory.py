"""
Unit tests for memory.py module.
Tests assignment memory persistence across turns, duplicate updating,
dynamic recalculation of priority, and upcoming list sorting.
"""

import sys
import os
from datetime import date
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory import AssignmentMemory


def test_add_and_retrieve_assignment():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)
    
    res = mem.add_or_update_assignment("DBMS Assignment", "2026-09-02", ref_date=ref)
    assert res["success"] is True
    assert res["action"] == "added"
    assert res["assignment"] == "DBMS Assignment"
    assert res["days_remaining"] == 4
    assert res["status"] == "HIGH"

    upcoming = mem.get_upcoming_assignments(ref_date=ref)
    assert len(upcoming) == 1
    assert upcoming[0]["name"] == "DBMS Assignment"


def test_duplicate_assignment_update():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    mem.add_or_update_assignment("DBMS Assignment", "2026-09-02", ref_date=ref)
    res_update = mem.add_or_update_assignment("DBMS Assignment", "2026-09-10", ref_date=ref)

    assert res_update["success"] is True
    assert res_update["action"] == "updated"
    assert res_update["days_remaining"] == 12
    assert res_update["status"] == "LOW"

    upcoming = mem.get_upcoming_assignments(ref_date=ref)
    assert len(upcoming) == 1
    assert upcoming[0]["due"] == "2026-09-10"


def test_memory_sorting_by_urgency():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    mem.add_or_update_assignment("DSA Assignment", "2026-09-05", ref_date=ref)
    mem.add_or_update_assignment("DBMS Assignment", "2026-09-02", ref_date=ref)
    mem.add_or_update_assignment("Java Assignment", "2026-09-12", ref_date=ref)

    upcoming = mem.get_upcoming_assignments(ref_date=ref)
    assert len(upcoming) == 3
    # Earliest deadline first
    assert upcoming[0]["name"] == "DBMS Assignment"  # Sep 2
    assert upcoming[1]["name"] == "DSA Assignment"   # Sep 5
    assert upcoming[2]["name"] == "Java Assignment"  # Sep 12


def test_memory_persistence_across_turns():
    ref = date(2026, 8, 29)
    mem = AssignmentMemory(ref_date=ref)

    # Turn 1
    mem.add_or_update_assignment("DSA Assignment", "2026-09-05", ref_date=ref)
    
    # Turn 2
    mem.add_or_update_assignment("DBMS Assignment", "2026-09-02", ref_date=ref)

    # Turn 3 query
    upcoming = mem.get_upcoming_assignments(ref_date=ref)
    assert len(upcoming) == 2
    names = [u["name"] for u in upcoming]
    assert "DBMS Assignment" in names
    assert "DSA Assignment" in names
