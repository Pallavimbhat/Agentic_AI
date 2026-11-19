# Agentic AI Course, Notes and Assignment Organiser

A FastAPI + SQLite academic management application with student/professor login, role-aware academic workflows, a single Unified Academic AI Assistant, and 14 independently executable agent capabilities.

## What is included

### Academic application
- Student and professor authentication with PBKDF2 password hashing and session cookies.
- Role-specific dashboards and course enrolment.
- Course and student management.
- Course notes, note versions and downloads.
- Assignment creation, deadlines and assignment retrieval.
- Student submissions with submitted/late status.
- Similarity analysis from actual submission text using word-trigram Jaccard and token-frequency cosine similarity; submissions must belong to the same assignment. A score is a screening signal, not proof of plagiarism.
- Grade creation, maximum-mark validation, approval and publication workflow.
- Milestones, study-plan generation, memory, deadline notifications and execution history.
- Professor missing-submission reporting.

### 14 integrated and independently executable labs
1. Agent vs Chatbot
2. Tool-Using Agent
3. Reusable Skills and Skill Registry
4. Persistent Memory and Retrieval
5. Connectors (internal connector registry; MCP-style abstraction, not a claim of official MCP SDK compliance)
6. Agent Runtime and Execution Logging
7. Dependency-Aware Agentic Node Graph
8. Parallel Specialist Workers (concurrent Python functions, not autonomous LLM agents)
9. Deep Research (bundled local evidence corpus and clearly labelled user-supplied evidence; not live web search)
10. Cloud Operations Log Analysis (no infrastructure mutation)
11. SDLC Requirements and Test Artifact Factory
12. Safety, Validation, Audit and Human Approval Records (no production deployment)
13. Mechanical, Civil and Electrical Engineering Sensor Analysis (illustrative thresholds only)
14. Academic Helpdesk Ticket Lifecycle

Each lab can be run through the assistant or independently through the authenticated endpoint `POST /api/labs/{lab_id}/run`. Every run is persisted with input, output, status, run ID and duration.

## Important distinction: AI model vs agent runtime

The local application works without an external model: it uses a deterministic intent router, validated Python tools, database services, reusable skills and execution traces. An optional OpenAI-compatible LLM adapter can classify ambiguous natural-language requests when configured. No API key is bundled. To enable model-assisted routing, copy `.env.example` to `.env` and set:

```env
AI_API_BASE_URL=https://api.openai.com/v1
AI_API_KEY=your_provider_key
AI_MODEL=your_model_name
AI_API_TIMEOUT=12
```

A compatible local model server can also be used by changing `AI_API_BASE_URL` and `AI_MODEL`. The model proposes a capability and input only; local code still validates and executes tools. If no model is configured or the provider fails, deterministic local routing remains available. Do not describe the default offline configuration as an LLM-powered autonomous assistant.

## Windows setup

1. Extract the ZIP.
2. Open the **inner project folder** that contains `course_organizer`, `agentic_core`, `lab1` ... `lab14`, and `requirements.txt`.
3. Open Terminal in that folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002
```

4. Open `http://127.0.0.1:8002/`.
5. Keep the terminal running while demonstrating.

Alternatively double-click `START_APPLICATION.bat` from the project root.

## Demo accounts
- Student: `test.student@example.com` / `student123`
- Professor: `test.professor@example.com` / `professor123`

These are local demonstration accounts. Change passwords and set a strong `COURSE_ORGANIZER_SECRET` before exposing the app beyond localhost.

## Demonstrate all 14 labs
Use the **Academic AI Assistant** as the single user-facing entry point. For the requested VS Code terminal demonstration, run `python DEMO_ALL_14_LABS.py`. It executes 29 different inputs across all 14 labs, prints the actual JSON outputs and records run IDs. Run a single lab with `python DEMO_ALL_14_LABS.py --lab 8`. See `RUN_LAB_DEMOS_IN_VSCODE.md` for the presentation workflow. Keep the web interface for academic application features and the single Academic AI Assistant; there is no separate lab showcase in the interface.

For an independent lab run, authenticate first and call:

```http
POST /api/labs/1/run
Content-Type: application/json
{"question":"Compare a chatbot and an AI agent for finding Introduction to Artificial Intelligence."}
```

Replace `1` with any lab ID from 1 through 14. The endpoint uses the same shared runtime and persists the execution.

## Run tests

```powershell
python -m pytest -q
```

The project also includes lab-specific unittest modules and `RUN_TESTS.bat`.

## Technical boundaries
- Connector registry is internal and MCP-style; no official MCP SDK compliance is claimed.
- Parallel specialist work uses `ThreadPoolExecutor` and deterministic Python functions.
- Research uses a local evidence corpus unless a separate external research provider is configured.
- Cloud operations analyses logs and recommends actions; it does not control cloud resources.
- Governance records approval decisions; it does not deploy or mutate production systems.
- Engineering limits are illustrative, not certified safety thresholds.
- Similarity is lexical screening and requires human review.
