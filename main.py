"""
Main CLI Application for Assignment Deadline Tracker Agent.
Runs an interactive conversation loop in terminal with visible trace output.
"""

import sys
from agent import AssignmentTrackerAgent


def main():
    print("=" * 60)
    print(" 📚 ASSIGNMENT DEADLINE TRACKER AGENT (DAY 2)")
    print(" Powered by Plan-Act-Observe-Decide Loop & Google Calendar Sync")
    print("=" * 60)
    print("Type your message below (or type 'exit' or 'quit' to stop).\n")

    agent = AssignmentTrackerAgent(verbose=True)

    while True:
        try:
            user_input = input("\n[USER] > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting Assignment Deadline Tracker Agent. Goodbye!")
                break

            print("\n" + "-" * 50)
            res = agent.process_turn(user_input)
            print("-" * 50)
            print(f"\n[AGENT RESPONSE]\n{res['final_answer']}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


if __name__ == "__main__":
    main()
