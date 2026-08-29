# 📚 Day 2: Assignment Deadline Tracker Agent

An AI Agent built for students to track upcoming assignment deadlines, determine urgency levels, prioritize workload, generate **1-click Google Calendar sync links**, and maintain session memory across multi-turn conversations with both a CLI and a visual **Gradio Web UI**.

---

## 1. What It Does

The **Assignment Deadline Tracker Agent** is an agentic AI assistant designed to solve student task overload. Instead of simple chatbot responses, this agent executes a structured **Plan → Act → Observe → Decide** workflow. It parses assignment names and due dates, stores them in persistent session memory, computes exact days remaining using Python's `datetime` library, assigns deterministic urgency levels (`OVERDUE`, `URGENT`, `HIGH`, `MEDIUM`, `LOW`), and creates instant 1-click Google Calendar event links for device synchronization.

---

## 2. Tools

The agent uses explicit, deterministic Python tools rather than guessing dates or math:

1. **`add_assignment(name, due)`**:
   - **Purpose**: Parses raw natural date inputs ("September 2", "2026-09-02", "tomorrow"), calculates days remaining, determines priority status, attaches a 1-click Google Calendar link, and stores or updates the assignment in session memory.
   - **Return Format**:
     ```json
     {
       "success": true,
       "action": "added",
       "assignment": "DBMS Assignment",
       "due": "2026-09-02",
       "days_remaining": 4,
       "status": "HIGH",
       "gcal_link": "https://calendar.google.com/calendar/render?action=TEMPLATE&text=DBMS%20Assignment..."
     }
     ```

2. **`get_upcoming()`**:
   - **Purpose**: Retrieves all stored assignments from memory, dynamically recalculates days remaining relative to today, and returns them sorted by earliest deadline first.
   - **Return Format**:
     ```json
     [
       {
         "name": "DBMS Assignment",
         "due": "2026-09-02",
         "days_remaining": 4,
         "status": "HIGH",
         "gcal_link": "..."
       },
       {
         "name": "DSA Assignment",
         "due": "2026-09-05",
         "days_remaining": 7,
         "status": "MEDIUM",
         "gcal_link": "..."
       }
     ]
     ```

---

## 3. Memory Architecture

The project cleanly separates responsibilities into three distinct layers:
- **Agent State**: Tracks the multi-step execution loop, plan rationale, tool calls, and decisions.
- **Conversation History**: Retains the sequence of user and agent messages across conversation turns.
- **Assignment Memory (`AssignmentMemory`)**: Stores assignment objects keyed by normalized name. If a duplicate assignment is added, it updates the existing record with the new deadline instead of creating redundant clutter.

---

## 4. Agentic Behavior (Plan → Act → Observe → Decide)

The agent does NOT simply generate a direct LLM string response. Instead, it follows a transparent loop:

```
USER REQUEST
    ↓
UNDERSTAND GOAL
    ↓
AGENT PLAN (Formulate plan based on NLU intent)
    ↓
TOOL CALL (Execute add_assignment or get_upcoming)
    ↓
TOOL RESULT (Observe JSON return data from Python)
    ↓
AGENT DECISION (Evaluate priority order / check for errors)
    ↓
FINAL ANSWER (Synthesize structured Markdown answer for user)
```

---

## 5. Priority Logic

Priority is calculated deterministically in `priority.py` based on `days_remaining = (due_date - current_date).days`:

| Urgency Level | Days Remaining | Action / Meaning |
|---|---|---|
| **OVERDUE** | `< 0` | Deadline has passed! Needs immediate attention. |
| **URGENT** | `0 – 2` | Due today, tomorrow, or in 2 days. Critical focus! |
| **HIGH** | `3 – 5` | Due in 3 to 5 days. High priority. |
| **MEDIUM** | `6 – 10` | Due in 6 to 10 days. Normal workflow. |
| **LOW** | `> 10` | Due in more than 10 days. Low priority. |

---

## 6. Complete Example Trace

```text
[USER]
Which assignment should I complete first?

[MEMORY]
Stored Assignments (Total: 2):
1. DBMS Assignment | Due: 2026-09-02 | Days Left: 4 | Priority: HIGH
2. DSA Assignment  | Due: 2026-09-05 | Days Left: 7 | Priority: MEDIUM

[AGENT PLAN]
Detected priority request. Plan: Execute get_upcoming() tool to fetch all stored assignments, compare deadlines & urgency levels, and recommend highest priority task.

[TOOL CALL]
get_upcoming()

[TOOL RESULT]
[
  {
    "name": "DBMS Assignment",
    "due": "2026-09-02",
    "days_remaining": 4,
    "status": "HIGH",
    "gcal_link": "https://calendar.google.com/calendar/render?action=TEMPLATE&text=DBMS%20Assignment..."
  },
  {
    "name": "DSA Assignment",
    "due": "2026-09-05",
    "days_remaining": 7,
    "status": "MEDIUM",
    "gcal_link": "..."
  }
]

[AGENT DECISION]
Evaluated upcoming list sorted by days remaining. 'DBMS Assignment' has nearest deadline (4 days left). Formulating recommendation.

[FINAL ANSWER]
### 🎯 Priority Recommendation

You should complete **DBMS Assignment** first!

- **Why:** It has the nearest deadline on **2026-09-02** (4 days remaining, **HIGH** priority).
- **Google Sync:** [Sync to Calendar](https://calendar.google.com/calendar/render?action=TEMPLATE&text=DBMS%20Assignment...)

---
#### 📋 Full Assignment Ranking by Urgency:
1. **DBMS Assignment** — Due **2026-09-02** (4 days left) [HIGH]
2. **DSA Assignment** — Due **2026-09-05** (7 days left) [MEDIUM]
```

---

## 7. Honest Failure & Resolution

**Real Problem Encountered During Development**:
- *Issue 1 (Date String & Prefix Noise)*: When the user said *"I have a DBMS assignment due September 2"*, the initial regex extracted the name as `"a DBMS Assignment"`. The leading article `"a "` was improperly capitalized into the assignment title.
  - *Fix*: Improved the intent parsing regex with non-capturing noise cleaning (`re.sub(r'^(?:i have|a|an|the|my)\s+', '')`) and added acronym protection (`_clean_name`) so names like `DBMS` and `DSA` retain proper uppercase formatting.
- *Issue 2 (Invalid Date Input)*: Passing `"September 35"` previously caused Python's `datetime.date(y, m, d)` to throw an uncaught `ValueError`.
  - *Fix*: Wrapped date instantiation in explicit try/except blocks inside `priority.py`. When an invalid date is detected, `parse_date_string()` cleanly returns `None`, allowing `add_assignment()` to return `{"success": false, "error": "invalid_date"}` and triggering the agent to politely ask the user for a valid date.

---

## 8. Installation

```bash
# Clone the repository
git clone https://github.com/vineelreddy1/Assignment-Deadline-Tracker-Agent.git
cd Assignment-Deadline-Tracker-Agent

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate    # On Windows

# Install requirements
pip install -r requirements.txt
```

---

## 9. Running the Application

### 🌐 Web UI Interface (Gradio)
Launch the visual web interface with real-time Plan-Act execution trace logger and interactive priority matrix:
```bash
python app.py
```
> Open browser at: **`http://127.0.0.1:7860`**

### 💻 Command Line Interface (CLI)
```bash
python main.py
```

---

## 10. Running the Tests & Notebook

Run unit and integration test suite (14 tests):
```bash
pytest tests/ -v
```

Launch the Jupyter Notebook demo:
```bash
jupyter notebook notebook/deadline_tracker_demo.ipynb
```
