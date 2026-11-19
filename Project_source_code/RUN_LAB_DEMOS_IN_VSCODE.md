# Run the 14 labs independently in VS Code Terminal

The web interface is reserved for the academic application: login, courses, students, enrolment, notes, assignments, submissions, similarity reports, grading, study plans and the Unified Academic AI Assistant. Do not use the interface as a 14-lab showcase.

## One command: run two or more real inputs for every lab

Open VS Code Terminal in the project root (the folder containing `agentic_core`, `course_organizer`, `lab1` ... `lab14`) and run:

```powershell
python DEMO_ALL_14_LABS.py
```

This executes 29 input cases across all 14 lab handlers, prints the supplied input and actual JSON output, shows PASS/FAIL, run ID and duration, and persists each execution in the agentic runtime database.

## Run one lab independently

```powershell
python DEMO_ALL_14_LABS.py --lab 1
python DEMO_ALL_14_LABS.py --lab 2
# ...
python DEMO_ALL_14_LABS.py --lab 14
```

Run a single case of a lab:

```powershell
python DEMO_ALL_14_LABS.py --lab 1 --case 2
```

## Run each lab's interactive CLI instead

```powershell
python -m lab1
python -m lab2
# ...
python -m lab14
```

Each CLI accepts a fresh text or JSON payload. Type `:example` for its sample and `:quit` to exit. The batch runner is recommended for a repeatable viva because it contains multiple distinct inputs per lab.

## Important: what the terminal output proves

- Every case calls `agentic_core.runtime.run_lab()` and the actual registered handler for that lab.
- `completed` means the local handler returned without an execution exception; inspect the returned payload to understand the operation's business result. For example, Lab 12 can correctly complete a validation run whose payload says `rejected` or `pending`.
- Lab 3 and Lab 4 use persistent state, Lab 5 writes and reads a sandboxed workspace file, Lab 12 records approval state, and Lab 14 persists helpdesk tickets.
- Lab 9 uses the bundled offline evidence corpus and supplied evidence. It is not live web research.
- Lab 5 is an internal MCP-style connector abstraction, not a claim of official MCP SDK protocol compliance.
- Lab 8 uses concurrent Python specialist workers, not autonomous LLM agents.
- Lab 10 analyses logs and recommends actions; it does not change cloud infrastructure.
- Lab 12 records governance and human approval decisions; it does not deploy changes.

## Web application demo

Start the application with `START_APPLICATION.bat` or:

```powershell
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002
```

Open `http://127.0.0.1:8002/` and demonstrate only the academic application functions and the single Academic AI Assistant. The 14 individual lab demonstrations stay in the VS Code terminal.
