"""Offline text demonstration: python -m voice_agents.demo routing"""
import argparse
from .workflows import Workflow, Session

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", choices=["routing", "appointments", "outreach", "survey"])
    args = parser.parse_args()
    workflow, session = Workflow(args.workflow), Session()
    reply = workflow.start(session)
    print("Agent:", reply.text)
    while not reply.done:
        try:
            utterance = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        reply = workflow.step(session, utterance)
        print("Agent:", reply.text)
    if reply.transfer:
        print("Demo transfer target:", reply.transfer)

if __name__ == "__main__":
    main()
