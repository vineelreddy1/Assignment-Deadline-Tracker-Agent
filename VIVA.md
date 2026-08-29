# 🎯 Viva Examination Guide — Day 2: Assignment Deadline Tracker Agent

This document provides simple, clear, and beginner-friendly answers to the 16 standard viva questions for this project.

---

### 1. What is an AI agent?
An AI agent is an autonomous software program that takes user input, formulates a step-by-step plan, uses external tools (like databases or Python calculators) to perform actions, observes tool results, and makes decisions to accomplish a specific goal.

---

### 2. Why is this not just a chatbot?
A normal chatbot simply takes text input and generates direct text response using probabilistic next-word prediction (LLM hallucination risk). 
In contrast, this **AI Agent**:
- Maintains persistent session memory.
- Calls actual Python tools (`add_assignment`, `get_upcoming`).
- Computes exact dates and urgency deterministically using Python code.
- Exhibits a visible **Plan → Act → Observe → Decide** execution trace before delivering the final answer.

---

### 3. What are the two required tools?
1. **`add_assignment(name, due)`**: Parses dates, calculates priority status, generates 1-click Google Calendar links, and stores assignments in memory.
2. **`get_upcoming()`**: Retrieves stored assignments, recalculates days remaining dynamically relative to today, and returns them sorted by priority urgency.

---

### 4. Where are the tools implemented?
All tool functions are explicitly implemented in [`tools.py`](file:///C:/Users/hp/.gemini/antigravity-ide/scratch/assignment-deadline-agent/tools.py). They wrap state management from [`memory.py`](file:///C:/Users/hp/.gemini/antigravity-ide/scratch/assignment-deadline-agent/memory.py) and calculation logic from [`priority.py`](file:///C:/Users/hp/.gemini/antigravity-ide/scratch/assignment-deadline-agent/priority.py).

---

### 5. Where does the agent call the tools?
The agent calls tools inside the `_run_plan_act_loop()` method in [`agent.py`](file:///C:/Users/hp/.gemini/antigravity-ide/scratch/assignment-deadline-agent/agent.py). Based on the analyzed intent, the agent invokes `tools.add_assignment()` or `tools.get_upcoming()`, logs the execution trace, and observes the JSON results.

---

### 6. How does the plan-act loop work?
The agent follows a 6-stage workflow:
1. **User Request**: Accepts natural language input.
2. **Understand Goal**: Identifies user intent (adding task, prioritizing, or listing).
3. **Plan Next Action**: Logs `[AGENT PLAN]`.
4. **Call Tool**: Invokes explicit tool function and logs `[TOOL CALL]`.
5. **Observe Tool Result**: Evaluates tool output JSON and logs `[TOOL RESULT]`.
6. **Decide & Respond**: Logs `[AGENT DECISION]` and generates `[FINAL ANSWER]`.

---

### 7. How does memory work?
Session memory is managed by the `AssignmentMemory` class in `memory.py`. It stores assignment objects in a dictionary keyed by normalized assignment name. This persists assignments across conversation turns. If an assignment with the same name is re-added, memory updates the existing assignment deadline instead of creating duplicates.

---

### 8. How is priority calculated?
Priority is calculated deterministically in `priority.py` based on `days_remaining = (due_date - current_date).days`:
- **OVERDUE**: `< 0` days
- **URGENT**: `0 – 2` days
- **HIGH**: `3 – 5` days
- **MEDIUM**: `6 – 10` days
- **LOW**: `> 10` days

---

### 9. How are overdue assignments handled?
When `days_remaining < 0`, `calculate_priority()` returns the status `"OVERDUE"`. Overdue assignments are assigned highest priority and placed at the top of the upcoming list with a warning label (`abs(days) day(s) overdue`).

---

### 10. What happens with an invalid date?
When a user inputs an invalid date (e.g., `"September 35"`), `parse_date_string()` catches the `ValueError` and returns `None`. The tool `add_assignment()` returns `{"success": false, "error": "invalid_date"}`. The agent observes this tool failure and asks the user to provide a valid date format.

---

### 11. What happens if information is missing?
If the user specifies an assignment name without a deadline (e.g., *"I have a DBMS assignment"*), the agent detects `due_str = None`, halts tool execution, and directly asks the user for the missing due date.

---

### 12. Explain the execution flow of one request.
For *"Which assignment should I complete first?"*:
1. Agent logs `[USER]`.
2. Agent identifies priority query and logs `[AGENT PLAN]`: *"Execute get_upcoming() to evaluate urgency."*
3. Agent invokes `tools.get_upcoming()` and logs `[TOOL CALL]`.
4. Tool returns list of assignments sorted by earliest deadline and logs `[TOOL RESULT]`.
5. Agent compares deadlines and logs `[AGENT DECISION]`: *"DBMS has nearest deadline (4 days)."*
6. Agent formats Markdown response with Google Calendar link and logs `[FINAL ANSWER]`.

---

### 13. Why do we use `datetime`?
LLMs are notoriously inaccurate at mental calendar math and leap year / month length calculations. Python's standard `datetime` module ensures exact, error-free subtraction between dates: `(due_date - date.today()).days`.

---

### 14. What is the role of the LLM?
The LLM handles **Natural Language Understanding (NLU)** — extracting assignment names, natural language dates ("tomorrow", "September 2"), and identifying whether the user wants to add, list, or prioritize tasks.

---

### 15. What part of the application is deterministic?
- Date string parsing (`parse_date_string`)
- Days remaining math (`calculate_days_remaining`)
- Priority threshold mapping (`calculate_priority`)
- Memory storage and sorting (`AssignmentMemory`)
- Google Calendar URL construction (`generate_gcal_link`)

---

### 16. How would you improve this agent in the future?
1. **Google Calendar API Integration**: Direct OAuth 2.0 automatic calendar creation instead of URL links.
2. **Subtask Breakdown**: Break large assignments into smaller daily milestones.
3. **Notification Push**: Send desktop/mobile alerts when an assignment status shifts from `HIGH` to `URGENT`.
