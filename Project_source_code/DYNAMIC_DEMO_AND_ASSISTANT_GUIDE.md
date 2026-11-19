# Dynamic 14-Lab Terminal Demo + Academic AI Assistant

## What changed

- Preserved the existing 14 lab implementations, FastAPI application, database, authentication, academic workflows, similarity checking, submission and grading flows.
- Added `DYNAMIC_LAB_DEMO.py`: the presenter chooses a lab and enters their own live inputs. It does not replay a fixed list of canned scenarios.
- Added `RUN_DYNAMIC_LAB_DEMO.bat` for Windows.
- Expanded academic assistant note retrieval to include the latest note-version text, scoped to the authenticated student's enrolled courses. Topic questions return matching passages from saved notes; the optional configured LLM can compose a grounded explanation.
- Expanded professor assistant retrieval across teaching-scope courses, students, notes, assignments, submissions and grades.
- Unified assistant model configuration now accepts the documented `AI_API_*` variables as well as `AI_ASSISTANT_*` aliases.

## Dynamic terminal demonstration

From the project root:

```powershell
python DYNAMIC_LAB_DEMO.py
```

Choose a lab number (1-14) or `all`. The runner asks for up to three inputs per lab by default. Inputs are entered live, converted only where a lab requires a structured format, and passed to the real handler via `agentic_core.runtime.run_lab`. The actual payload, JSON output, status, execution ID and duration are displayed and persisted.

Run a particular lab:

```powershell
python DYNAMIC_LAB_DEMO.py --lab 8 --runs 3
```

Run all labs interactively:

```powershell
python DYNAMIC_LAB_DEMO.py --all --runs 3
```

For structured labs (especially 3 and 12), enter the JSON format shown by the on-screen guidance. For Lab 10, paste multiple log lines and finish with a blank line. Lab 7 accepts free text for an automatically constructed graph or JSON containing a custom `nodes` list.

## Start the academic web application

```powershell
python -m pip install -r requirements.txt
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002
```

Open `http://127.0.0.1:8002/` and sign in with a provisioned student or professor account. The assistant is the single natural-language entry point. It can retrieve course, note, assignment, deadline, submission, published-grade and milestone information permitted to the signed-in role. It shows a trace of the tools and records used.

## Optional model-backed conversational answers

The app has a deterministic, database-grounded fallback. For more flexible natural-language interpretation and fluent note explanations, configure an OpenAI-compatible model endpoint:

1. Copy `.env.example` to `.env`.
2. Set `AI_ASSISTANT_BASE_URL`, `AI_ASSISTANT_API_KEY`, and `AI_ASSISTANT_MODEL` (or use `AI_API_BASE_URL`, `AI_API_KEY`, `AI_MODEL`).
3. Restart the server.

The model is only given records retrieved for the authenticated user's permitted academic scope. It must not invent missing grades, deadlines, submissions or note content. If no model is configured or the endpoint is unavailable, the local grounded fallback remains available.

## Important implementation boundaries

- Lab 8 is implemented as concurrent Python specialist workers, not a set of independently reasoning LLM agents.
- Lab 9 uses its bundled/offline research evidence corpus and any explicitly supplied evidence; it is not live web research by default.
- Lab 5 exposes an internal connector registry and is not claimed to be full official MCP SDK/protocol compliance.
- The assistant answers from academic records and note content available to the logged-in role; it cannot truthfully answer about records or note files that are not stored in the application.
