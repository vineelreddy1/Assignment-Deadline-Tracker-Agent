"""
Priority and Date Handling Module for Assignment Deadline Tracker Agent.
Provides deterministic Python functions for date parsing, urgency calculation, priority levels,
and Google Calendar event link generation.
"""

import re
from datetime import date, datetime, timedelta
from urllib.parse import quote
from typing import Optional, Tuple


def parse_date_string(date_str: str, ref_date: Optional[date] = None) -> Optional[date]:
    """
    Parses a user-provided date string into a datetime.date object.
    Supports formats:
    - ISO format: '2026-09-02', '2026/09/02'
    - Relative dates: 'today', 'tomorrow'
    - Natural dates: 'September 2', 'Sep 5', 'September 2, 2026', '9/2'

    Returns None if date string is invalid (e.g. 'September 35').
    """
    if ref_date is None:
        ref_date = date.today()

    clean_str = date_str.strip().lower()

    if not clean_str:
        return None

    # Handle relative keywords
    if clean_str == "today":
        return ref_date
    if clean_str == "tomorrow":
        return ref_date + timedelta(days=1)

    # 1. Try ISO YYYY-MM-DD or YYYY/MM/DD
    match_iso = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", clean_str)
    if match_iso:
        y, m, d = int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            return None

    # 2. Try 'Month Day, Year' or 'Month Day' (e.g. 'September 2', 'Sep 5', 'September 2 2026')
    month_names = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12
    }

    pattern_month_first = r"^([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:[,\s]+(\d{4}))?$"
    match_mf = re.match(pattern_month_first, clean_str)
    if match_mf:
        m_str, d_str, y_str = match_mf.group(1), match_mf.group(2), match_mf.group(3)
        if m_str in month_names:
            m = month_names[m_str]
            d = int(d_str)
            y = int(y_str) if y_str else ref_date.year
            try:
                dt = date(y, m, d)
                # If year omitted and date has passed significantly (>30 days ago), consider next year
                if y_str is None and (ref_date - dt).days > 30:
                    dt = date(y + 1, m, d)
                return dt
            except ValueError:
                return None

    # 3. Try 'Day Month' (e.g. '2 September', '5 Sep')
    pattern_day_first = r"^(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)(?:[,\s]+(\d{4}))?$"
    match_df = re.match(pattern_day_first, clean_str)
    if match_df:
        d_str, m_str, y_str = match_df.group(1), match_df.group(2), match_df.group(3)
        if m_str in month_names:
            m = month_names[m_str]
            d = int(d_str)
            y = int(y_str) if y_str else ref_date.year
            try:
                dt = date(y, m, d)
                if y_str is None and (ref_date - dt).days > 30:
                    dt = date(y + 1, m, d)
                return dt
            except ValueError:
                return None

    # 4. Try M/D or M/D/Y (e.g. '9/2' or '9/2/2026')
    match_slash = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", clean_str)
    if match_slash:
        m, d = int(match_slash.group(1)), int(match_slash.group(2))
        y_raw = match_slash.group(3)
        if y_raw:
            y = int(y_raw) if len(y_raw) == 4 else 2000 + int(y_raw)
        else:
            y = ref_date.year
        try:
            return date(y, m, d)
        except ValueError:
            return None

    return None


def calculate_days_remaining(due_date: date, ref_date: Optional[date] = None) -> int:
    """Calculates number of days between ref_date and due_date."""
    if ref_date is None:
        ref_date = date.today()
    return (due_date - ref_date).days


def calculate_priority(days_remaining: int) -> str:
    """
    Determines assignment priority status based on days remaining:
    - OVERDUE: < 0 days remaining
    - URGENT: 0 to 2 days remaining
    - HIGH: 3 to 5 days remaining
    - MEDIUM: 6 to 10 days remaining
    - LOW: > 10 days remaining
    """
    if days_remaining < 0:
        return "OVERDUE"
    elif days_remaining <= 2:
        return "URGENT"
    elif days_remaining <= 5:
        return "HIGH"
    elif days_remaining <= 10:
        return "MEDIUM"
    else:
        return "LOW"


def generate_gcal_link(name: str, due_date: date, details: str = "") -> str:
    """
    Generates a 1-click Google Calendar Event Link for any device.
    Pre-fills title, date, and details.
    """
    date_formatted = due_date.strftime("%Y%m%d")
    # For an all-day event on Google Calendar, end date is next day YYYYMMDD
    next_day = (due_date + timedelta(days=1)).strftime("%Y%m%d")
    
    title_encoded = quote(name)
    details_text = details if details else f"Assignment Deadline for {name}"
    details_encoded = quote(details_text)

    link = (
        f"https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={title_encoded}"
        f"&dates={date_formatted}/{next_day}"
        f"&details={details_encoded}"
    )
    return link
