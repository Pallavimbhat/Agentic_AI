> Historical development note. The current implementation and run instructions are in `README.md`, `INTEGRATED_ARCHITECTURE.md`, and `VERIFICATION_REPORT.md`.

# Integrated Labs 1–8 Workflow

The main dashboard's **Academic AI Assistant** is the single entry point for the integrated demonstration. A student submits one natural-language query to `POST /api/assistant/query`; the integrated agent selects relevant academic records, invokes the corresponding specialists and returns a readable answer, selected records and an execution trace.

| Lab | What executes in the integrated application |
|---|---|
| L1 | Natural-language intent interpretation and grounded response synthesis. |
| L2 | Read-only academic database tools scoped to the authenticated student. |
| L3 | Reusable retrieval skills that wrap the academic connector operations. |
| L4 | Persistent JSON memory stored separately for each student; explicit preferences can be saved and recalled. |
| L5 | Connector registry plus authenticated academic database connector adapter. |
| L6 | Runtime lifecycle wraps specialist execution and graph aggregation, recording start/completion/failure events. |
| L7 | Dependency-aware graph combines outputs from the selected specialists. |
| L8 | Five specialist workers (assignments, notes, courses, grades and milestones) are dispatched concurrently; only relevant workers retrieve records for the current question. |

## Run

From the project root (the folder containing `course_organizer`, `lab1` through `lab8`, and `requirements.txt`):

```powershell
python -m pip install -r requirements.txt
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002 --reload
```

Or double-click `START_APPLICATION.bat` on Windows.

## Demonstration prompts

- `Show my pending assignments with deadlines.`
- `Show my enrolled courses.`
- `Find my AI notes.`
- `Show my published grades.`
- `Give me a complete academic overview.`
- `Remember that I prefer short study sessions.`
- `What do you remember about my study preferences?`

Each supported query displays only relevant records. Expand the trace to inspect all eight lab components. Out-of-scope questions receive a clarification rather than fabricated student data.

## Implementation boundaries

- The integrated workflow uses deterministic intent classification and grounded answer templates. It is not presented as an open-ended LLM.
- Memory is persistent and user-scoped JSON, not a vector database.
- Lab 5 includes a connector registry and an authenticated adapter to the application's live database; the academic adapter is not a separate remote MCP server transport.
- Lab 8 is a Python parallel specialist-agent swarm, not five independent LLMs.
