"""
Terminal loop for free conversation.

Orchestration (Session, ChatFocus, process_turn) lives in
backend.agent.process_turn — this file only reads lines and prints replies.

Run from app/ (this directory), with app/'s own venv:
    .venv/bin/python cli.py
"""

from backend.agent.process_turn import Session, process_turn


def main() -> None:
    print("USER -> Voice -> Describe -> LLM3 -> Planning experiment. Ctrl+C to quit.\n")
    session = Session()
    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        try:
            result = process_turn(session.chat_focus, user_text)
        except Exception as e:
            # Friendly fallback — llm_client.call_with_retry already
            # absorbs most model-shape hiccups; what reaches here is
            # persistent failure or something else. Printed alongside
            # for whoever is debugging this run.
            print(f"  (debug: {e})")
            print("Agent: That took longer than expected - try again in a moment.\n")
            continue
        print(f"Agent: {result['reply']}\n")


if __name__ == "__main__":
    main()
