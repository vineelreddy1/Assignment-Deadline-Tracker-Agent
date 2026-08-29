"""
Agent Module for Assignment Deadline Tracker Agent.
Implements the real multi-step Plan -> Act -> Observe -> Decide loop,
session memory persistence, tool execution, Google Calendar linking, and visible trace logging.
"""

import json
import re
from datetime import date
from typing import Dict, Any, List, Optional, Tuple
from memory import AssignmentMemory
import tools
from config import DEFAULT_REFERENCE_DATE, VERBOSE_TRACE


class TraceLogger:
    """Helper class to record and format visible agent trace logs."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logs: List[str] = []

    def log(self, tag: str, content: str) -> None:
        formatted = f"[{tag}]\n{content.strip()}\n"
        self.logs.append(formatted)
        if self.verbose:
            try:
                print(formatted)
            except UnicodeEncodeError:
                safe_str = formatted.encode("ascii", errors="replace").decode("ascii")
                print(safe_str)

    def get_full_trace(self) -> str:
        return "\n".join(self.logs)


class AssignmentTrackerAgent:
    """
    AssignmentTrackerAgent:
    An agentic AI assistant that tracks assignments, determines urgency, orders priorities,
    creates 1-click Google Calendar links, and remembers state across conversation turns.
    """

    def __init__(self, memory: Optional[AssignmentMemory] = None, ref_date: Optional[date] = None, verbose: bool = True):
        self.ref_date = ref_date if ref_date is not None else DEFAULT_REFERENCE_DATE
        self.memory = memory if memory is not None else AssignmentMemory(ref_date=self.ref_date)
        self.verbose = verbose

    def process_turn(self, user_message: str) -> Dict[str, Any]:
        """
        Executes a complete multi-step Plan-Act-Observe-Decide turn for a user message.
        """
        logger = TraceLogger(verbose=self.verbose)
        logger.log("USER", user_message)

        # Record input in conversation history
        self.memory.add_history("user", user_message)

        # Log current memory state
        memory_summary = self.memory.get_memory_summary(ref_date=self.ref_date)
        logger.log("MEMORY", memory_summary)

        # Run multi-step agentic plan-act loop
        final_answer = self._run_plan_act_loop(user_message, logger)

        # Record agent output in conversation history
        self.memory.add_history("agent", final_answer)

        return {
            "user_message": user_message,
            "final_answer": final_answer,
            "trace_log": logger.get_full_trace(),
            "upcoming_assignments": self.memory.get_upcoming_assignments(ref_date=self.ref_date)
        }

    def _run_plan_act_loop(self, user_message: str, logger: TraceLogger) -> str:
        """
        Core Plan-Act-Observe-Decide workflow.
        Parses intent, invokes tools, evaluates tool outputs, and makes decisions.
        """
        clean_msg = user_message.strip()

        # Step 1: Intent Recognition & Planning
        plan_str, assignments_detected, is_priority_query, is_list_query = self._analyze_intent(clean_msg)
        logger.log("AGENT PLAN", plan_str)

        # Step 2: Act — Add Assignments tool calls if assignments detected
        if assignments_detected:
            results = []
            for name, due_str in assignments_detected:
                if not due_str:
                    logger.log("AGENT DECISION", f"Assignment '{name}' was mentioned without a deadline. Requesting deadline from user.")
                    final_ans = f"I see you mentioned the assignment **'{name}'**, but I couldn't find a deadline. What date is it due?"
                    logger.log("FINAL ANSWER", final_ans)
                    return final_ans

                logger.log("TOOL CALL", f"add_assignment(name='{name}', due='{due_str}')")
                
                # Execute Python Tool 1
                tool_res = tools.add_assignment(name=name, due=due_str, memory=self.memory, ref_date=self.ref_date)
                logger.log("TOOL RESULT", json.dumps(tool_res, indent=2))
                results.append(tool_res)

                # Observe tool result
                if not tool_res.get("success"):
                    logger.log("AGENT DECISION", f"Tool call add_assignment returned error: {tool_res.get('message')}. Asking user for correction.")
                    final_ans = f"I encountered an issue adding '{name}': {tool_res.get('message')}"
                    logger.log("FINAL ANSWER", final_ans)
                    return final_ans

            # Formulate response for added assignments
            logger.log("AGENT DECISION", "All assignments stored successfully in memory. Formulating confirmation with Google Calendar links.")
            return self._format_addition_response(results)

        # Step 3: Prioritization Query
        elif is_priority_query:
            logger.log("TOOL CALL", "get_upcoming()")
            upcoming = tools.get_upcoming(memory=self.memory, ref_date=self.ref_date)
            logger.log("TOOL RESULT", json.dumps(upcoming, indent=2))

            if not upcoming:
                logger.log("AGENT DECISION", "No assignments found in memory to prioritize.")
                final_ans = "You don't have any assignments saved in memory yet! Tell me what assignments you have and when they are due."
                logger.log("FINAL ANSWER", final_ans)
                return final_ans

            top_item = upcoming[0]
            logger.log("AGENT DECISION", f"Evaluated upcoming list sorted by days remaining. '{top_item['name']}' has nearest deadline ({top_item['days_remaining']} days left). Formulating recommendation.")

            final_ans = self._format_priority_response(upcoming)
            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Step 4: List / View Query
        elif is_list_query:
            logger.log("TOOL CALL", "get_upcoming()")
            upcoming = tools.get_upcoming(memory=self.memory, ref_date=self.ref_date)
            logger.log("TOOL RESULT", json.dumps(upcoming, indent=2))

            logger.log("AGENT DECISION", f"Retrieved {len(upcoming)} assignments from memory. Formatting structured list for user.")
            final_ans = self._format_list_response(upcoming)
            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Step 5: General query / Help fallback
        else:
            logger.log("AGENT DECISION", "Request is general conversational input. Informing user about available tools and memory state.")
            upcoming = self.memory.get_upcoming_assignments(ref_date=self.ref_date)
            if upcoming:
                final_ans = f"Hello! You currently have {len(upcoming)} assignment(s) stored in your memory.\n" + self.memory.get_memory_summary(ref_date=self.ref_date)
            else:
                final_ans = "Hello! I am your Assignment Deadline Tracker Agent. Tell me about your assignments and due dates (e.g. 'I have a DBMS assignment due September 2'), and I will help you track, sync to Google Calendar, and prioritize them!"
            logger.log("FINAL ANSWER", final_ans)
            return final_ans

    def _analyze_intent(self, msg: str) -> Tuple[str, List[Tuple[str, Optional[str]]], bool, bool]:
        """
        Parses intent from user message:
        Returns (plan_str, assignments_detected[(name, due)], is_priority_query, is_list_query)
        """
        clean = msg.strip()
        assignments = []
        is_priority_query = False
        is_list_query = False

        # Priority query keywords
        priority_keywords = [
            "which assignment should i do first",
            "which assignment should i complete first",
            "which one should i do first",
            "which one should i complete first",
            "which assignment to do first",
            "which assignment to complete first",
            "which assignment should i prioritize",
            "what should i do first",
            "what should i complete first",
            "what to do first",
            "prioritize",
            "priority",
            "do first",
            "complete first"
        ]
        if any(kw in clean.lower() for kw in priority_keywords):
            is_priority_query = True

        # List query keywords
        list_keywords = [
            "what assignments do i",
            "view upcoming",
            "list assignments",
            "show assignments",
            "which assignments do i have",
            "my assignments",
            "what assignments"
        ]
        if any(kw in clean.lower() for kw in list_keywords):
            is_list_query = True

        # Split multiple statements joined by 'and', 'also', ';'
        clauses = re.split(r'\band\b|\balso\b|;|\.', clean, flags=re.IGNORECASE)

        for clause in clauses:
            clause = clause.strip()
            if not clause or is_priority_query or is_list_query:
                continue

            # Pattern 1: 'X assignment due Y' or 'X due on Y' or 'X on Y'
            match1 = re.search(
                r'(?:have|added|got|need to do)?\s*([a-zA-Z0-9\s]+?)\s+(?:assignment|project|homework|task)?\s*(?:due|on|by)\s+([a-zA-Z0-9\s,/-]+)',
                clause,
                re.IGNORECASE
            )
            if match1:
                raw_name = match1.group(1).strip()
                raw_due = match1.group(2).strip()
                # Clean leading noise words (a, an, the, my, i have, got)
                raw_name = re.sub(r'^(?:i have|i also have|i got|i|have|got|a|an|the|my)\s+', '', raw_name, flags=re.IGNORECASE).strip()
                raw_name = re.sub(r'^(?:a|an|the|my)\s+', '', raw_name, flags=re.IGNORECASE).strip()
                if raw_name:
                    if not raw_name.lower().endswith("assignment") and "assignment" in clause.lower():
                        raw_name = f"{raw_name} Assignment"
                    assignments.append((raw_name, raw_due))
                continue

            # Pattern 2: Mention of assignment without explicit deadline keyword (missing deadline case)
            match2 = re.search(r'i have (?:a|an)?\s*([a-zA-Z0-9\s]+?\s+assignment)', clause, re.IGNORECASE)
            if match2:
                raw_name = match2.group(1).strip()
                assignments.append((raw_name, None))

        # Build transparent plan summary
        if assignments:
            item_strs = [f"'{a[0]}' (Due: {a[1] if a[1] else 'MISSING'})" for a in assignments]
            plan_str = f"Detected {len(assignments)} assignment addition(s): {', '.join(item_strs)}. Plan: Execute add_assignment() tool to store in memory and generate Google Calendar sync link."
        elif is_priority_query:
            plan_str = "Detected priority request. Plan: Execute get_upcoming() tool to fetch all stored assignments, compare deadlines & urgency levels, and recommend highest priority task."
        elif is_list_query:
            plan_str = "Detected list query. Plan: Execute get_upcoming() tool to retrieve stored assignments from memory and present upcoming schedule."
        else:
            plan_str = "General query detected. Plan: Check current session memory state and provide helpful summary."

        return plan_str, assignments, is_priority_query, is_list_query

    def _format_addition_response(self, results: List[Dict[str, Any]]) -> str:
        lines = []
        for r in results:
            action_word = "Updated" if r.get("action") == "updated" else "Added"
            status = r["status"]
            status_badge = f"**[{status}]**"
            days = r["days_remaining"]
            
            if days < 0:
                day_str = f"{abs(days)} day(s) overdue"
            elif days == 0:
                day_str = "due TODAY"
            elif days == 1:
                day_str = "due TOMORROW"
            else:
                day_str = f"{days} days remaining"

            lines.append(f"✅ **{action_word} Assignment:** **{r['assignment']}**")
            lines.append(f"- 📅 **Deadline:** {r['due']} ({day_str})")
            lines.append(f"- 🚨 **Priority Status:** {status_badge}")
            lines.append(f"- 🗓️ **Google Calendar:** [Add to Google Calendar]({r['gcal_link']})\n")

        return "\n".join(lines).strip()

    def _format_priority_response(self, upcoming: List[Dict[str, Any]]) -> str:
        top = upcoming[0]
        out = []
        out.append("### 🎯 Priority Recommendation\n")
        out.append(f"You should complete **{top['name']}** first!\n")
        out.append(f"- **Why:** It has the nearest deadline on **{top['due']}** ({top['days_remaining']} days remaining, **{top['status']}** priority).")
        out.append(f"- **Google Sync:** [Sync to Calendar]({top['gcal_link']})\n")

        if len(upcoming) > 1:
            out.append("---")
            out.append("#### 📋 Full Assignment Ranking by Urgency:\n")
            for idx, item in enumerate(upcoming, 1):
                out.append(f"{idx}. **{item['name']}** — Due **{item['due']}** ({item['days_remaining']} days left) [{item['status']}]")

        return "\n".join(out)

    def _format_list_response(self, upcoming: List[Dict[str, Any]]) -> str:
        if not upcoming:
            return "You have no upcoming assignments stored in memory."

        out = [f"### 📋 Stored Upcoming Assignments ({len(upcoming)})\n"]
        for idx, item in enumerate(upcoming, 1):
            out.append(f"{idx}. **{item['name']}**")
            out.append(f"   - Due: **{item['due']}** ({item['days_remaining']} days left)")
            out.append(f"   - Status: `{item['status']}`")
            out.append(f"   - Calendar: [Add to Google Calendar]({item['gcal_link']})\n")

        return "\n".join(out)
