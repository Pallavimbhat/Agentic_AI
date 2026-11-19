> Historical development note. The current implementation and run instructions are in `README.md`, `INTEGRATED_ARCHITECTURE.md`, and `VERIFICATION_REPORT.md`.

# Course Organizer upgrade notes

## Added in this build
- Student dashboard panel for enrolled-course notes and assignments.
- Notes can be downloaded. If a note version has an existing file path, that file is returned; otherwise, the stored note content is downloaded as a `.txt` file.
- Student deadline statuses are calculated from the current time, assignment deadline, and that student's submission: Pending, Overdue, Submitted, or Submitted late.
- New Academic Planning Assistant Agent. It classifies common questions, selects a database tool, returns the records, and exposes a plan/execution trace.
- The orchestrator registers the Academic Planning Assistant Agent.
- Dashboard tables are scoped to the student's enrolled courses and own submissions/grades. Professor view is scoped to courses they created plus legacy unassigned courses.
- Submission API rejects submissions for assignments outside the student's enrolled courses.

## Run locally (Windows)
From the project root:
```bash
python -m py_compile course_organizer\main.py
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002 --reload
```
Open `http://127.0.0.1:8002/`.

## Demo credentials in the included sample database
- Student: `test.student@example.com` / `student123`
- Professor: `test.professor@example.com` / `professor123`

If you already have a working local database, back it up before copying source files. Do not replace your existing `course_organizer/database/course_organizer.db` with the sample database unless you intentionally want the sample data.

## Agentic AI explanation for demonstration
The Academic Planning Assistant currently uses deterministic intent rules, not an LLM. It is still a transparent tool-using agent workflow: classify intent -> select a database tool -> execute it -> verify returned records -> show trace. Explain this honestly in the presentation. An LLM-based planner can be added as a separate enhancement, but would require an API key/model configuration and guardrails.

## Important limitations
- Notes created through the existing dashboard are stored as text, so the download is a `.txt` file. File-backed note versions can download their existing file when a valid path is recorded.
- Professor course ownership uses the existing `courses.created_by` field. Existing unassigned courses (`created_by` is NULL) remain visible to professors for backwards compatibility. For a production multi-professor deployment, add an explicit course-instructor assignment workflow and tighten all remaining legacy endpoints.
- This is a local demo configuration. Set a strong `COURSE_ORGANIZER_SECRET` and use HTTPS before deployment.
