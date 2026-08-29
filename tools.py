"""
Tools Module for Assignment Deadline Tracker Agent.
Defines explicit Python tool implementations:
- TOOL 1: add_assignment(name, due)
- TOOL 2: get_upcoming()
- TOOL 3: generate_calendar_event(name, due) [Google Calendar Integration]
"""

from typing import Dict, Any, List, Optional
from datetime import date
from memory import AssignmentMemory


def add_assignment(name: str, due: str, memory: AssignmentMemory, ref_date: Optional[date] = None) -> Dict[str, Any]:
    """
    TOOL 1: add_assignment
    Adds an assignment and its deadline to the agent's memory/state.
    Calculates priority and generates a Google Calendar sync link.

    Returns structured dict response.
    """
    if not name or not name.strip():
        return {
            "success": False,
            "error": "missing_name",
            "message": "Assignment name is missing. Please provide the assignment name."
        }

    if not due or not due.strip():
        return {
            "success": False,
            "error": "missing_deadline",
            "message": f"Deadline is missing for '{name}'. Please provide a due date."
        }

    # Delegate to memory state manager
    res = memory.add_or_update_assignment(name=name, due_str=due, ref_date=ref_date)
    return res


def get_upcoming(memory: AssignmentMemory, ref_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    TOOL 2: get_upcoming
    Returns all stored assignments that are upcoming or currently relevant.
    Returns structured list of assignment dicts sorted by days remaining.
    """
    return memory.get_upcoming_assignments(ref_date=ref_date)


def generate_calendar_event(name: str, due: str, memory: AssignmentMemory, ref_date: Optional[date] = None) -> Dict[str, Any]:
    """
    TOOL 3: generate_calendar_event (Google Calendar Device Sync)
    Generates a 1-click Google Calendar URL to directly add the assignment to any device calendar.
    """
    result = memory.add_or_update_assignment(name=name, due_str=due, ref_date=ref_date)
    if not result["success"]:
        return result
    
    return {
        "success": True,
        "assignment": result["assignment"],
        "due": result["due"],
        "gcal_link": result["gcal_link"],
        "message": f"Google Calendar link created for '{result['assignment']}' on {result['due']}."
    }
