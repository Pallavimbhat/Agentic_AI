"""Interactive, input-driven terminal demonstrations for all 14 labs.

Examples:
  python DYNAMIC_LAB_DEMO.py                 # choose labs interactively
  python DYNAMIC_LAB_DEMO.py --lab 8          # run Lab 8 with your own inputs
  python DYNAMIC_LAB_DEMO.py --all            # visit all labs, enter live inputs

Each entered input is sent to the real lab handler through run_lab(); outputs
and execution metadata are persisted in the Agentic Core SQLite database.
"""
from __future__ import annotations
import argparse
import json
import sys
from textwrap import dedent

from agentic_core.runtime import run_lab
from course_organizer.database.db_service import DatabaseService
from course_organizer.agents.unified_agent import UnifiedAcademicAgent

LABS = {
 1: ("Agent vs Chatbot", "Compare text-only chatbot behaviour with an agent that selects and executes a tool.", [
     "Compare a chatbot and an AI agent for finding Introduction to Artificial Intelligence",
     "Compare a chatbot and an AI agent for finding Agentic AI"], "Enter a natural-language comparison or course lookup."),
 2: ("Tool-Using Agent", "Select and execute calculator, course lookup or text-analysis tools.", [
     "calculate (18 + 6) * 3", "find course Database Management Systems", "analyse Retrieval augmented generation uses retrieved evidence"], "Try: calculate 35 * 12 | find course <name> | analyse <your text>"),
 3: ("Reusable Skills", "Register, version, list and execute reusable skills.", [
     '{"action":"create","name":"my_uppercase","description":"Convert text to uppercase","operation":"uppercase"}',
     '{"action":"run","name":"my_uppercase","input":"my own text"}'], "Enter JSON: action=create (name, description, operation) or action=run (name, input). Operations: uppercase, lowercase, word_count, character_count, extract_emails, calculate, course_lookup."),
 4: ("Memory and Retrieval", "Store and recall user-scoped persistent memory.", [
     "remember I prefer examples and concise explanations", "recall examples"], "Try: remember <fact> | recall <keyword>."),
 5: ("Connectors", "Discover and invoke registered database and workspace connectors.", [
     "list connectors", "find course Artificial Intelligence", "list files"], "Try: list connectors | find course <name> | list files | read file <name> | write file <name> <content>. JSON connector calls are also accepted."),
 6: ("Agent Runtime", "Show accepted, planning, running and completed/failed lifecycle events.", [
     "calculate 25 + 17", "calculate 19 * 8"], "Try: calculate <expression> or find course <name>."),
 7: ("Agentic Node Graph", "Build a dependency-aware graph and show execution order and node outputs.", [
     "Students need a revision plan for the database examination.", "Contact faculty@example.edu about the AI assignment."], "Enter arbitrary text for the generated graph, or JSON with a nodes array to define your own DAG."),
 8: ("Parallel Specialist Workers", "Run keyword, sentiment, entity and statistics specialists concurrently.", [
     "Student scores improved, but assignment completion is declining.", "The campus portal failed with timeout; contact support@example.edu"], "Enter any text to analyse; JSON {\"text\": \"...\"} is also accepted."),
 9: ("Deep Research", "Build a research brief from the bundled evidence corpus and any supplied evidence.", [
     "Artificial intelligence applications in higher education", "Responsible AI governance in student assessment"], "Enter a research topic, or JSON {\"topic\": \"...\", \"sources\": [{\"title\": \"...\", \"text\": \"...\"}]} . Evidence is offline/bundled unless external search is configured."),
 10: ("Cloud Operations", "Parse operational logs, classify severity and suggest diagnostic actions.", [
     "INFO service started\nWARNING memory usage high\nERROR database connection timeout", "INFO worker ready\nCRITICAL disk full\nERROR upload failed"], "Paste your own log lines. Multi-line input ends with a blank line."),
 11: ("SDLC Factory", "Convert a software requirement into architecture, modules, criteria and test artifacts.", [
     "Build a student attendance portal with login, attendance recording and monthly reports.", "Create a library reservation system with search and due-date reminders."], "Enter any software requirement, or JSON {\"requirement\": \"...\"}."),
 12: ("Safety and Governance", "Validate proposals, privacy handling, rollback plans, budgets and approval workflow.", [
     '{"diagnosis":"Unverified database change","proposed_change":"Increase connection pool after staging test","rollback_plan":"Restore previous pool size","privacy_scrubbed":true,"estimated_cost":10,"budget":100}',
     '{"diagnosis":"Sensitive request","proposed_change":"Export student records","rollback_plan":"Revoke export and restore backup","privacy_scrubbed":false,"estimated_cost":0,"budget":100}'], "Enter JSON with diagnosis, proposed_change, rollback_plan, privacy_scrubbed, estimated_cost and budget. No production action is executed."),
 13: ("Engineering Specialist", "Analyse domain-specific sensor readings against configured/illustrative thresholds.", [
     "Analyse mechanical sensor readings: vibration 8.5, temperature 92", "civil crack width 0.5, displacement 12"], "Enter domain and measurements, e.g. mechanical vibration 8.5 temperature 92; or JSON with domain and readings."),
 14: ("Academic Helpdesk", "Triage issues and create, list, retrieve or update persistent tickets.", [
     "create ticket I cannot access my Agentic AI course notes", "list tickets"], "Try: create ticket <issue> | triage <issue> | list tickets | check ticket <id> | close ticket <id>. JSON is also accepted."),
}


def read_multiline(prompt: str) -> str:
    print(prompt)
    print("Paste/type input. Press Enter on an empty line to execute (single-line input works too):")
    lines=[]
    while True:
        try: line=input("  ")
        except EOFError: break
        if not line:
            if lines: break
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def normalize(lab_id: int, raw: str, adapter: UnifiedAcademicAgent) -> str:
    # Reuse the application's tested natural-language argument normaliser for
    # the labs that need authenticated user context or canonical input syntax.
    if lab_id in {2,4,5,6,13,14}:
        return adapter._lab_input(lab_id, raw, user_id=1)
    if lab_id == 2 and raw and not raw.lower().startswith(("calculate ","find course ","search course ","course ","analyse ","analyze ","list tools","tools","help")):
        return "analyse " + raw
    return raw


def run_one(lab_id: int, adapter: UnifiedAcademicAgent, case_no: int):
    name, concept, examples, hint = LABS[lab_id]
    print("\n" + "="*88)
    print(f"LAB {lab_id:02d} — {name}")
    print(concept)
    print("="*88)
    print("Input guidance:", hint)
    print("Example inputs (for guidance only; you will enter your own):")
    for ex in examples:
        print("  • " + ex.replace("\n", " | "))
    raw = read_multiline(f"\n[Lab {lab_id}] Enter your dynamic test input #{case_no}:")
    if not raw:
        print("Skipped: no input supplied.")
        return True
    try:
        payload = normalize(lab_id, raw, adapter)
        result = run_lab(lab_id, payload)
        print("\nACTUAL INPUT SENT TO LAB:")
        print(payload)
        print("\nACTUAL LAB OUTPUT:")
        print(json.dumps(result.get("output"), indent=2, ensure_ascii=False, default=str))
        print(f"\nEXECUTION: {result.get('status')} | run_id={result.get('run_id')} | duration={result.get('duration_seconds')}s")
        return result.get("success", False)
    except Exception as exc:
        print(f"INPUT/EXECUTION ERROR: {type(exc).__name__}: {exc}")
        return False


def main():
    parser=argparse.ArgumentParser(description="Dynamic live-input terminal demo for Labs 1-14")
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--lab", type=int, choices=range(1,15), help="Demonstrate one lab")
    group.add_argument("--all", action="store_true", help="Visit all 14 labs")
    parser.add_argument("--runs", type=int, default=3, choices=range(1,6), help="Number of dynamic inputs per lab (default: 3)")
    args=parser.parse_args()
    adapter=UnifiedAcademicAgent(DatabaseService())
    labs=[args.lab] if args.lab else list(range(1,15)) if args.all else None
    print("\nAGENTIC AI COURSE ORGANIZER — DYNAMIC LAB DEMONSTRATION")
    print("Every query is entered live and passed to the actual lab handler.")
    if labs is None:
        print("Available labs:")
        for i,(name,desc,_,_) in LABS.items(): print(f"  {i:02d}. {name} — {desc}")
        choice=input("\nEnter lab number (1-14), or 'all': ").strip().lower()
        labs=list(range(1,15)) if choice=="all" else [int(choice)]
        if labs[0] not in LABS: parser.error("Lab number must be 1-14")
    passed=failed=0
    for lab in labs:
        print(f"\nYou can enter up to {args.runs} different inputs for this lab.")
        for case in range(1,args.runs+1):
            ok=run_one(lab,adapter,case)
            if ok: passed+=1
            else: failed+=1
            if case < args.runs:
                more=input("Run another different input for this same lab? [Y/n]: ").strip().lower()
                if more in {"n","no"}: break
        if lab != labs[-1]:
            nxt=input("Move to next lab? [Y/n]: ").strip().lower()
            if nxt in {"n","no"}: break
    print("\nDEMO SESSION SUMMARY")
    print(f"Completed scenarios: {passed} | failed/skipped scenarios: {failed}")
    print("Execution history is persisted in course_organizer/database/agentic_core.sqlite3")
    print("Note: Lab 9 uses bundled/offline evidence; Lab 8 uses concurrent Python specialist workers.")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
