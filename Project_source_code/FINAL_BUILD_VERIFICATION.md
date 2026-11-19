# Final build verification — 19 November 2026

## Verified in this build

- `python -m pytest -q`: **95 passed, 103 subtests passed, 0 failed**.
- `python DEMO_ALL_14_LABS.py`: **14 labs executed, 29 input scenarios, 0 failed scenarios**.
- Lab 1 regression checks include two different named course lookups and assert that the requested title is preserved in the tool arguments and returned matches.
- Application integration tests verify student and professor login, the single assistant interface, assistant invocation, and that the separate `/labs` showcase route is not mounted.
- The automated suite also covers academic database operations, notes, assignments, submissions, similarity comparisons, grading approval/publication, user-scoped memory, connector file round trips, node graph dependency validation, approval records, and persistent helpdesk tickets.

## What the demo runner does

`DEMO_ALL_14_LABS.py` calls the actual `run_lab()` runtime and registered handler for each lab. It does not print canned demonstration text. It displays the input, returned JSON output, execution status, run ID and duration. It runs 29 different scenarios across all 14 labs. You can run an individual lab with `python DEMO_ALL_14_LABS.py --lab N`.

## Academic application scope

The web app includes authenticated student/professor roles and API/UI workflows for courses, student management, enrolment, notes and note versions, assignments, submissions, similarity reports, grade review/approval/publication, milestones, student views, memory, deadline monitoring, notifications and execution history.

## Explicit technical limitations

- The application has a deterministic local assistant/router by default. An optional OpenAI-compatible model can be configured through `.env` for model-assisted classification of ambiguous requests. No API key is bundled, and the default local assistant must not be represented as a fully autonomous LLM.
- Lab 5 provides an internal MCP-style connector abstraction, not official MCP SDK compliance.
- Lab 8 uses concurrent Python specialist functions, not autonomous LLM agents.
- Lab 9 uses a local evidence corpus and user-supplied sources, not live web research by default.
- Lab 10 analyses logs and recommends actions; it does not operate cloud infrastructure.
- Lab 12 validates proposals and records human approval decisions; it does not deploy changes.
- Lab 13 uses configurable/illustrative thresholds; it is not a certified safety system.
- Similarity is a lexical screening measure and is not, by itself, proof of plagiarism.

## Run locally

From the extracted project root (the directory containing `course_organizer`, `agentic_core`, `lab1` through `lab14`):

```powershell
python -m pip install -r requirements.txt
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002
```

Open `http://127.0.0.1:8002/`. Use `RUN_LAB_DEMOS_IN_VSCODE.md` for the terminal demo sequence.
