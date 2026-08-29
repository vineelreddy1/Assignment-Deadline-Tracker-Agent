"""
Memory Module for Assignment Deadline Tracker Agent.
Manages persistent session memory across conversation turns:
- Stored assignment objects with computed deadlines and priority
- Conversation message history
- Assignment list retrieval sorted by priority/days remaining
"""

from datetime import date
from typing import Dict, Any, List, Optional
from priority import parse_date_string, calculate_days_remaining, calculate_priority, generate_gcal_link
from config import DEFAULT_REFERENCE_DATE


class AssignmentMemory:
    """
    Session memory class that stores assignments and conversation history.
    Enforces deterministic sorting and duplicate updating.
    """

    def __init__(self, ref_date: Optional[date] = None):
        # Dict of assignments keyed by normalized assignment name
        self.assignments: Dict[str, Dict[str, Any]] = {}
        self.conversation_history: List[Dict[str, str]] = []
        self.ref_date = ref_date if ref_date is not None else DEFAULT_REFERENCE_DATE

    def add_or_update_assignment(self, name: str, due_str: str, ref_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Adds a new assignment or updates an existing one if the name already exists.
        Parses date string, calculates days remaining and priority status, and attaches Google Calendar link.
        """
        active_ref_date = ref_date if ref_date is not None else self.ref_date
        parsed_due = parse_date_string(due_str, ref_date=active_ref_date)

        if parsed_due is None:
            return {
                "success": False,
                "error": "invalid_date",
                "message": f"Unable to parse date string '{due_str}'. Please provide a valid date format (e.g. '2026-09-02' or 'September 2')."
            }

        # Clean name while preserving acronyms like DBMS, DSA
        words = name.strip().split()
        cleaned_words = [w if (w.isupper() and len(w) <= 5) else w.capitalize() for w in words]
        norm_name = " ".join(cleaned_words)
        key = norm_name.lower()
        is_update = key in self.assignments

        days_rem = calculate_days_remaining(parsed_due, ref_date=active_ref_date)
        status = calculate_priority(days_rem)
        gcal_link = generate_gcal_link(norm_name, parsed_due, f"Due on {parsed_due.isoformat()} ({status} priority)")

        assignment_data = {
            "name": norm_name,
            "due": parsed_due.isoformat(),
            "due_date_obj": parsed_due,
            "days_remaining": days_rem,
            "status": status,
            "gcal_link": gcal_link
        }

        self.assignments[key] = assignment_data

        return {
            "success": True,
            "action": "updated" if is_update else "added",
            "assignment": norm_name,
            "due": parsed_due.isoformat(),
            "days_remaining": days_rem,
            "status": status,
            "gcal_link": gcal_link,
            "message": f"Assignment '{norm_name}' {'updated with new deadline' if is_update else 'added successfully'} ({parsed_due.isoformat()})."
        }

    def get_upcoming_assignments(self, ref_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Returns all stored assignments, recalculated relative to ref_date,
        sorted by days remaining ascending (earliest deadline first).
        """
        active_ref_date = ref_date if ref_date is not None else self.ref_date
        upcoming = []

        for key, item in self.assignments.items():
            due_obj = item["due_date_obj"]
            days_rem = calculate_days_remaining(due_obj, ref_date=active_ref_date)
            status = calculate_priority(days_rem)
            gcal_link = generate_gcal_link(item["name"], due_obj, f"Due on {due_obj.isoformat()} ({status} priority)")

            upcoming.append({
                "name": item["name"],
                "due": item["due"],
                "days_remaining": days_rem,
                "status": status,
                "gcal_link": gcal_link
            })

        # Sort by days remaining ascending (earliest/overdue deadlines first)
        upcoming.sort(key=lambda x: x["days_remaining"])
        return upcoming

    def add_history(self, role: str, content: str) -> None:
        """Stores message in conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def get_memory_summary(self, ref_date: Optional[date] = None) -> str:
        """Generates human-readable string summary of currently stored assignments."""
        upcoming = self.get_upcoming_assignments(ref_date=ref_date)
        if not upcoming:
            return "No assignments currently stored in memory."

        lines = [f"Stored Assignments (Total: {len(upcoming)}):"]
        for idx, item in enumerate(upcoming, 1):
            lines.append(f"{idx}. {item['name']} | Due: {item['due']} | Days Left: {item['days_remaining']} | Priority: {item['status']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clears all stored assignments and conversation history."""
        self.assignments.clear()
        self.conversation_history.clear()
