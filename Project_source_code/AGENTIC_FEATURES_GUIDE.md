# Agentic Course Organizer — Feature Guide

This update adds database-backed workflow endpoints for study planning, user-approved plans, explicit academic memory, deadline monitoring, notifications, execution history, and professor missing-submission reports.

## Start the app

From the project root (the folder containing `course_organizer`):

```powershell
python -m py_compile course_organizer\main.py course_organizer\agents\academic_workflows.py
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002 --reload
```

Sign in through the web interface first. API requests use the same session cookie. Open `http://127.0.0.1:8002/docs` to try the endpoints interactively.

## Student workflows

### Create a plan (plan is saved as pending approval)
`POST /api/agentic/study-plans`

```json
{"goal":"Prepare for my AI exam and finish pending assignments","days":5,"hours_per_day":2}
```

The service retrieves the authenticated student's assignments and notes, allocates tasks, verifies basic constraints, persists the plan, and returns an execution trace. This is a transparent deterministic planner, not a claim that an LLM autonomously reasoned.

### List plans
`GET /api/agentic/study-plans`

### Approve/reject/complete a plan
`PATCH /api/agentic/study-plans/{plan_id}`

```json
{"status":"approved"}
```

Allowed status values: `approved`, `rejected`, `completed`. A student can only update their own plan.

### Store explicit memory
`PUT /api/agentic/memory`

```json
{"key":"study_preference","value":"Prefer 45-minute study sessions with short breaks"}
```

Read it with `GET /api/agentic/memory`. This is explicit user-provided memory, not hidden inference. The user can edit a key by sending it again; database-level scoping is by authenticated user.

### Run deadline monitor
`POST /api/agentic/deadline-monitor`

```json
{"within_hours":48}
```

Creates deduplicated in-app notifications for pending/overdue assignments whose deadline falls within the selected window. It runs on demand; to make it automatic, configure a scheduler to call this service periodically. Notifications are listed at `GET /api/agentic/notifications`.

### Execution history
`GET /api/agentic/execution-history`

Returns stored workflow traces for the authenticated user.

## Professor workflow

`GET /api/agentic/professor/missing-submissions` lists enrolled students with no submission for courses owned by the authenticated professor. Optional query parameter: `course_id`. Courses without an owner are intentionally excluded from this professor report.

## Resource search and summaries

The existing student notes endpoint and Academic Assistant can retrieve notes. To add document-grounded summaries, store note contents or extract text from uploaded files, retrieve only authorized course materials, and pass those retrieved passages to a configured LLM. The LLM must cite the note titles/sections used and must not invent source content.

## Important implementation boundaries

- The LLM is optional and needs a separately running local model or configured compatible endpoint; this ZIP does not include a model or API key.
- Study plan creation is deterministic and saved as `pending_approval`; it does not silently alter the student's calendar.
- Deadline monitoring is currently run on demand, not by a background scheduler.
- Professor missing-submission reporting only returns courses whose `created_by` matches the professor's user ID. Confirm course ownership is populated in your database.
- Before deployment, set a strong `COURSE_ORGANIZER_SECRET`, use HTTPS, review all existing API authorization checks, and test role isolation with separate student/professor accounts.
