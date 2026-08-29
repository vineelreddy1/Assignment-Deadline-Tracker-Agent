"""
Unit tests for priority.py module.
Tests date parsing, priority levels (OVERDUE, URGENT, HIGH, MEDIUM, LOW),
and Google Calendar link generation.
"""

import sys
import os
from datetime import date
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from priority import (
    parse_date_string,
    calculate_days_remaining,
    calculate_priority,
    generate_gcal_link
)


def test_parse_date_string_iso():
    ref = date(2026, 8, 29)
    res = parse_date_string("2026-09-02", ref_date=ref)
    assert res == date(2026, 9, 2)


def test_parse_date_string_natural():
    ref = date(2026, 8, 29)
    assert parse_date_string("September 2", ref_date=ref) == date(2026, 9, 2)
    assert parse_date_string("Sep 5", ref_date=ref) == date(2026, 9, 5)
    assert parse_date_string("today", ref_date=ref) == date(2026, 8, 29)
    assert parse_date_string("tomorrow", ref_date=ref) == date(2026, 8, 30)


def test_parse_date_string_invalid():
    ref = date(2026, 8, 29)
    assert parse_date_string("September 35", ref_date=ref) is None
    assert parse_date_string("invalid-date", ref_date=ref) is None


def test_calculate_days_remaining():
    ref = date(2026, 8, 29)
    due = date(2026, 9, 2)
    assert calculate_days_remaining(due, ref_date=ref) == 4


def test_calculate_priority_levels():
    assert calculate_priority(-1) == "OVERDUE"
    assert calculate_priority(0) == "URGENT"   # Due today
    assert calculate_priority(1) == "URGENT"   # Due tomorrow
    assert calculate_priority(2) == "URGENT"
    assert calculate_priority(3) == "HIGH"
    assert calculate_priority(5) == "HIGH"
    assert calculate_priority(6) == "MEDIUM"
    assert calculate_priority(10) == "MEDIUM"
    assert calculate_priority(11) == "LOW"


def test_generate_gcal_link():
    due = date(2026, 9, 2)
    link = generate_gcal_link("DBMS Assignment", due)
    assert "https://calendar.google.com/calendar/render" in link
    assert "text=DBMS%20Assignment" in link
    assert "dates=20260902/20260903" in link
