# Academic Assistant Setup

The main dashboard's integrated Academic AI Assistant uses deterministic intent interpretation and database-grounded response templates. It supports natural-language queries about a student's enrolled courses, notes, assignments, submission status, deadlines, published grades, milestones, and saved study preferences.

## Run (Windows PowerShell)

From the project root (the directory containing `course_organizer`, `lab1` through `lab8`, and `requirements.txt`):

```powershell
python -m pip install -r requirements.txt
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002 --reload
```

Open `http://127.0.0.1:8002/`. You can also double-click `START_APPLICATION.bat`.

## Supported example queries

- `Show my pending assignments with deadlines.`
- `What is my next deadline?`
- `Show my enrolled courses.`
- `Find my AI notes.`
- `Show my published grades.`
- `Give me a complete academic overview.`
- `Remember that I prefer short study sessions.`
- `What do you remember about my study preferences?`

The assistant answers from the authenticated student's permitted database records. It does not invent facts or claim to answer arbitrary general-knowledge questions. For the exact integrated Lab 1–8 mapping and implementation boundaries, see `INTEGRATED_LABS_1_TO_8.md`.
