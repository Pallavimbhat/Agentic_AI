"""Run independently testable, input-varying terminal demonstrations for Labs 1-14.

Usage:
  python DEMO_ALL_14_LABS.py              # run two scenarios per lab
  python DEMO_ALL_14_LABS.py --lab 8       # run only Lab 8
  python DEMO_ALL_14_LABS.py --lab 1 --case 2

All scenarios invoke the real lab handler through agentic_core.runtime.run_lab.
Results and execution IDs are persisted in the agentic execution database.
"""
from __future__ import annotations
import argparse, json, sys
from agentic_core.runtime import run_lab

SCENARIOS = {
 1: [
  "Compare a chatbot and an AI agent for finding Introduction to Artificial Intelligence",
  "Compare a chatbot and an AI agent for finding Agentic AI",
  ],
 2: ["calculate (18 + 6) * 3", "calculate 144 / 12"],
 3: [
   '{"action":"create","name":"terminal_uppercase","description":"Convert supplied text to uppercase","operation":"uppercase"}',
   '{"action":"run","name":"terminal_uppercase","input":"My first reusable skill"}',
  ],
 4: [
   '{"action":"remember","user_id":"demo-student-101","text":"I prefer visual explanations and short revision plans."}',
   '{"action":"recall","user_id":"demo-student-101","query":"revision plans"}',
  ],
 5: [
   '{"action":"list"}',
   '{"action":"call","connector":"workspace_files","arguments":{"action":"write","path":"lab5_demo.txt","content":"Connector write-read demonstration."}}',
   '{"action":"call","connector":"workspace_files","arguments":{"action":"read","path":"lab5_demo.txt"}}',
  ],
 6: ["calculate 25 + 17", "calculate 19 * 8"],
 7: [
   '{"nodes":[{"id":"count","operation":"word_count","input":"Students need help planning revision."},{"id":"upper","operation":"uppercase","input":"agentic ai"},{"id":"summary","operation":"top_terms","input":"Students need help planning revision and agentic ai","depends_on":["count","upper"]}]}',
   '{"nodes":[{"id":"emails","operation":"extract_emails","input":"Contact team@example.org and mam@college.edu"},{"id":"stats","operation":"character_count","input":"Second workflow input"}]}',
  ],
 8: [
   "Student scores have improved, but assignment completion is declining.",
   "ERROR: payment service failed; contact support at help@example.org. 3 retries were attempted.",
  ],
 9: [
   '{"topic":"Artificial intelligence applications in education","sources":[{"title":"Supplied class note","text":"Adaptive learning systems can personalise practice and provide feedback."}]}',
   '{"topic":"AI governance, transparency and accountability","sources":[{"title":"Governance note","text":"Accountability requires transparent review and clear responsibility."}]}',
  ],
 10: [
   '{"service":"academic-api","environment":"development","logs":"INFO service started\nWARNING high memory usage\nERROR database connection timeout"}',
   '{"service":"submission-worker","environment":"test","logs":"INFO worker ready\nCRITICAL disk full\nERROR upload failed"}',
  ],
 11: [
   '{"requirement":"Build a student attendance management application with login, attendance recording and monthly reports."}',
   '{"requirement":"Create a library book reservation portal with search, reservations, due-date reminders and librarian management."}',
  ],
 12: [
   '{"diagnosis":"Unverified change request","proposed_change":"Increase the worker pool","rollback_plan":"Restore the previous worker pool value","privacy_scrubbed":false,"estimated_cost":10,"budget":100}',
   '{"diagnosis":"Worker queue saturation","proposed_change":"Increase worker pool after staging validation","rollback_plan":"Restore the previous pool configuration","privacy_scrubbed":true,"estimated_cost":10,"budget":100}',
  ],
 13: [
   '{"domain":"mechanical","readings":[{"vibration_mm_s":8.5,"temp_c":92}],"thresholds":{"vibration_mm_s":7,"temp_c":90}}',
   '{"domain":"civil","readings":[{"crack_width_mm":0.5,"displacement_mm":12}],"thresholds":{"crack_width_mm":0.3,"displacement_mm":10}}',
  ],
 14: [
   '{"action":"create","user_id":"demo-student-101","issue":"I cannot access my Agentic AI course notes."}',
   '{"action":"list","user_id":"demo-student-101"}',
  ],
}


def main():
    parser=argparse.ArgumentParser(description="Independent terminal demos for all 14 labs")
    parser.add_argument("--lab",type=int,choices=range(1,15),help="Run one lab only")
    parser.add_argument("--case",type=int,help="Run one scenario number for the selected lab")
    args=parser.parse_args()
    labs=[args.lab] if args.lab else list(range(1,15))
    failures=0
    print("\nAGENTIC AI COURSE ORGANISER — 14 LAB TERMINAL DEMONSTRATIONS")
    print("Each case invokes the real handler and persists an execution record.\n")
    for lab in labs:
        cases=SCENARIOS[lab]
        if args.case:
            if args.case<1 or args.case>len(cases):
                parser.error(f"Lab {lab} has {len(cases)} cases; choose 1..{len(cases)}")
            cases=[cases[args.case-1]]
        print("="*88+f"\nLAB {lab:02d} — {len(cases)} scenario(s)\n"+"="*88)
        for index,prompt in enumerate(cases,1):
            result=run_lab(lab,prompt)
            ok=result.get("success") and result.get("status")=="completed"
            failures += 0 if ok else 1
            print(f"\nCASE {index} | {'PASS' if ok else 'FAIL'} | run_id={result.get('run_id')}")
            print("INPUT:",prompt)
            print("OUTPUT:")
            print(json.dumps(result.get("output",{}),indent=2,ensure_ascii=False,default=str))
            print(f"STATUS: {result.get('status')} | duration={result.get('duration_seconds')}s")
    print("\n"+"="*88)
    print(f"SUMMARY: {len(labs)} lab(s) executed; {failures} failed scenario(s).")
    print("Execution records are persisted in course_organizer/database/agentic_core.sqlite3")
    return 1 if failures else 0

if __name__=="__main__":
    sys.exit(main())
