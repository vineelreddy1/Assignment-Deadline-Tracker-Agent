"""
Web UI Application for Assignment Deadline Tracker Agent using Gradio 6.x.
Provides a modern visual interface with chat, execution trace logging,
and live Google Calendar device sync buttons.
"""

import sys
import os
from datetime import date
import gradio as gr

# Ensure local modules are accessible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import AssignmentTrackerAgent
from memory import AssignmentMemory
import tools

# Initialize shared global agent instance
agent = AssignmentTrackerAgent(verbose=True)


def process_agent_chat(user_message, chat_history):
    """
    Processes user input through the Plan-Act-Observe-Decide loop
    and updates chatbot history and execution trace.
    """
    if not user_message or not user_message.strip():
        return "", chat_history, "No query submitted.", get_memory_table()

    res = agent.process_turn(user_message)
    user_msg = res["user_message"]
    final_ans = res["final_answer"]
    trace_log = res["trace_log"]

    # Format for Gradio 6.x messages schema: list of dicts with 'role' and 'content'
    if chat_history is None:
        chat_history = []
    
    chat_history.append({"role": "user", "content": user_msg})
    chat_history.append({"role": "assistant", "content": final_ans})

    memory_table = get_memory_table()

    return "", chat_history, trace_log, memory_table


def direct_add_assignment(name, due_date):
    """Adds assignment directly from the UI form."""
    if not name or not due_date:
        return "❌ Please enter both assignment name and due date.", get_memory_table()
    
    res = agent.process_turn(f"I have a {name} assignment due {due_date}.")
    return res["final_answer"], get_memory_table()


def clear_agent_memory():
    """Clears all session memory."""
    agent.memory.clear()
    return [], "Session memory cleared.", get_memory_table()


def get_memory_table():
    """Formats current stored assignments into a Markdown table for UI rendering."""
    upcoming = agent.memory.get_upcoming_assignments()
    if not upcoming:
        return "*No assignments currently stored in memory.*"

    headers = "| # | Assignment Name | Due Date | Days Remaining | Priority Status | Google Calendar Sync |\n|---|---|---|---|---|---|\n"
    rows = []
    for idx, item in enumerate(upcoming, 1):
        status = item["status"]
        if status in ["OVERDUE", "URGENT"]:
            badge = f"🔴 **{status}**"
        elif status == "HIGH":
            badge = f"🟠 **{status}**"
        elif status == "MEDIUM":
            badge = f"🟡 **{status}**"
        else:
            badge = f"🟢 **{status}**"

        gcal_btn = f"[🗓️ Sync to Calendar]({item['gcal_link']})"
        rows.append(f"| {idx} | **{item['name']}** | {item['due']} | {item['days_remaining']} days | {badge} | {gcal_btn} |")

    return headers + "\n".join(rows)


# Custom CSS styling for premium dark theme with vibrant accents
custom_css = """
body {
    background-color: #0f172a;
    font-family: 'Inter', sans-serif;
}
.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
}
.header-box {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #1e1b4b 0%, #311b92 50%, #4a148c 100%);
    border-radius: 16px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
}
.header-box h1 {
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 8px;
}
.header-box p {
    font-size: 1.05rem;
    opacity: 0.9;
}
.trace-box {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-family: 'Fira Code', 'Courier New', monospace !important;
    color: #58a6ff !important;
}
"""

with gr.Blocks(title="Assignment Deadline Tracker Agent") as demo:

    with gr.Column(elem_classes=["header-box"]):
        gr.Markdown(
            """
            # 📚 Assignment Deadline Tracker Agent
            ### Multi-Step Agentic Planning • Deterministic Urgency Priority • 1-Click Google Calendar Sync
            """
        )

    with gr.Tabs():
        # TAB 1: Chatbot & Plan-Act Loop
        with gr.Tab("💬 Agent Chat & Plan-Act Loop"):
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        height=420
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="e.g. 'I have a DBMS assignment due September 2' or 'Which should I complete first?'",
                            show_label=False,
                            scale=4
                        )
                        submit_btn = gr.Button("Send 🚀", variant="primary", scale=1)
                        clear_btn = gr.Button("Clear Memory 🗑️", variant="secondary", scale=1)

                    gr.Examples(
                        examples=[
                            "I have a DBMS assignment due September 2.",
                            "I also have a Computer Networks assignment due September 5.",
                            "Which assignment should I complete first?",
                            "What assignments do I currently have?"
                        ],
                        inputs=msg_input,
                        label="💡 Sample Prompts (Click to test)"
                    )

                with gr.Column(scale=2):
                    gr.Markdown("### 🔍 Visible Execution Trace Log")
                    trace_output = gr.Code(
                        label="Plan -> Act -> Observe -> Decide Trace",
                        language="markdown",
                        lines=18,
                        elem_classes=["trace-box"]
                    )

        # TAB 2: Live Memory & Priority Matrix
        with gr.Tab("📋 Active Assignments & Priority Matrix"):
            gr.Markdown("### 📊 Stored Assignments Sorted by Urgency")
            memory_table_output = gr.Markdown(get_memory_table)
            refresh_btn = gr.Button("🔄 Refresh Table", variant="secondary")

        # TAB 3: Quick Add Form
        with gr.Tab("➕ Quick Form Input"):
            gr.Markdown("### Add Assignment via Structured Form")
            with gr.Row():
                form_name = gr.Textbox(label="Assignment Name", placeholder="e.g. Java Project")
                form_due = gr.Textbox(label="Due Date", placeholder="e.g. 2026-09-12 or September 12")
            form_submit = gr.Button("Add to Agent Memory ➕", variant="primary")
            form_status = gr.Markdown()

    # Event handlers
    submit_btn.click(
        process_agent_chat,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot, trace_output, memory_table_output]
    )
    
    msg_input.submit(
        process_agent_chat,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot, trace_output, memory_table_output]
    )

    clear_btn.click(
        clear_agent_memory,
        inputs=[],
        outputs=[chatbot, trace_output, memory_table_output]
    )

    refresh_btn.click(
        get_memory_table,
        inputs=[],
        outputs=[memory_table_output]
    )

    form_submit.click(
        direct_add_assignment,
        inputs=[form_name, form_due],
        outputs=[form_status, memory_table_output]
    )


if __name__ == "__main__":
    print("Launching Assignment Deadline Tracker Agent Web UI on http://127.0.0.1:7860...")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
