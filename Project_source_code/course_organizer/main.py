import os
import hmac
import hashlib
import secrets
import re
import sqlite3

from html import escape
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field

from course_organizer.database.db_service import DatabaseService
from course_organizer.agents.orchestrator import CourseOrganizerOrchestrator
from course_organizer.agents.integrated_lab_agent import IntegratedLabAgent
from course_organizer.agents.unified_agent import UnifiedAcademicAgent

app = FastAPI(
    title="Agentic AI Course Organizer",
    description="Agent-based academic workflow management",
    version="2.0.0",
)

db = DatabaseService()
orchestrator = CourseOrganizerOrchestrator(db)
integrated_lab_agent = IntegratedLabAgent(db)
unified_academic_agent = UnifiedAcademicAgent(db)
# ---------- AUTHENTICATION SETUP ----------

from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware

# Use a stable secret from an environment variable in production.
SESSION_SECRET = os.environ.get(
    "COURSE_ORGANIZER_SECRET",
    "local-demo-secret-change-before-deployment"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,  # Local development only; use HTTPS in production.
)

DB_PATH = (
    Path(__file__).resolve().parent
    / "database"
    / "course_organizer.db"
)


def hash_password(password: str, salt: bytes | None = None):
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = salt or secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )

    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password without comparing hashes directly."""
    try:
        salt_hex, expected_hex = stored_hash.split("$", 1)

        actual = hash_password(
            password,
            salt=bytes.fromhex(salt_hex),
        ).split("$", 1)[1]

        return hmac.compare_digest(actual, expected_hex)

    except (ValueError, TypeError):
        return False


def initialize_auth():
    """Add password storage without deleting existing users."""
    with sqlite3.connect(DB_PATH) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)")
        }

        if not columns:
            raise RuntimeError(
                f"Users table not found in database: {DB_PATH}"
            )

        if "password_hash" not in columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN password_hash TEXT"
            )

        # Demo credentials are assigned only to accounts
        # that do not already have a password.
        demo_accounts = [
            (1, "student123"),
            (2, "professor123"),
        ]

        for user_id, password in demo_accounts:
            user = conn.execute(
                "SELECT role, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

            if user is None:
                continue

            role, existing_hash = user

            expected_role = (
                "student" if user_id == 1 else "professor"
            )

            if role != expected_role:
                continue

            if not existing_hash:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hash_password(password), user_id),
                )


initialize_auth()


def current_user(request: Request):
    """Return the authenticated user stored in the session."""
    user_id = request.session.get("user_id")

    if user_id is None:
        return None

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def require_role(request: Request, *allowed_roles):
    """Reject unauthenticated users and disallowed roles."""
    user = current_user(request)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in first.",
        )

    if user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission for this action.",
        )

    return user


# ---------- LOGIN AND LOGOUT ----------

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Course Organizer Login</title>
      <style>
        body {
          margin:0; min-height:100vh; display:grid; place-items:center;
          background:#0b1020; color:#edf3ff;
          font:16px Segoe UI,Arial,sans-serif;
        }
        form {
          width:min(360px,85vw); padding:28px;
          background:#121d32; border:1px solid #293753;
          border-radius:14px;
        }
        h1 {font-size:25px}
        p {color:#9baecc;font-size:13px}
        label {display:block;margin-top:16px}
        input {
          box-sizing:border-box;width:100%;padding:12px;margin-top:6px;
          border-radius:7px;border:1px solid #30415f;
          background:#0b1324;color:white;
        }
        button {
          width:100%;padding:12px;margin-top:20px;border:0;
          border-radius:7px;background:#7d8cff;font-weight:bold;
          cursor:pointer;
        }
      </style>
    </head>
    <body>
      <form method="post" action="/login">
        <h1>Course Organizer</h1>
        <p>Sign in using your assigned account.</p>
        <label>Email</label>
        <input type="email" name="email" required>
        <label>Password</label>
        <input type="password" name="password" required>
        <button type="submit">Sign in</button>
      </form>
    </body>
    </html>
    """


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            """
            SELECT id, name, email, role, password_hash
            FROM users
            WHERE lower(email) = lower(?)
            """,
            (email.strip(),),
        ).fetchone()

    if (
        user is None
        or not user["password_hash"]
        or not verify_password(password, user["password_hash"])
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if user["role"] not in {"student", "professor"}:
        raise HTTPException(
            status_code=403,
            detail="Unsupported account role.",
        )

    request.session.clear()
    request.session["user_id"] = user["id"]

    return RedirectResponse("/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

def safe(value):
    return escape(str(value if value is not None else ""))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = current_user(request)

    if user is None:
        return RedirectResponse("/login", status_code=303)

    courses = db.list_courses()
    notes = db.list_notes()
    assignments = db.list_assignments()
    submissions = db.list_submissions()
    milestones = db.list_milestones()
    grades = db.list_grades()
    reports = db.list_similarity_reports() if hasattr(
        db, "list_similarity_reports"
    ) else []

    # Scope dashboard records to the signed-in user's academic context.
    if user["role"] == "student":
        courses = db._fetch_all(
            """SELECT c.* FROM courses c
               JOIN course_enrollments e ON e.course_id = c.id
               WHERE e.student_id = ? ORDER BY c.id""",
            (user["id"],),
        )
        visible_course_ids = {c["id"] for c in courses}
        notes = [n for n in notes if n.get("course_id") in visible_course_ids]
        assignments = [a for a in assignments if a.get("course_id") in visible_course_ids]
        submissions = db.list_submissions(student_id=user["id"])
        milestones = [x for x in milestones if x.get("course_id") in visible_course_ids]
        grades = db.list_grades(status="published", student_id=user["id"])
        reports = []
    elif user["role"] == "professor":
        courses = [c for c in courses if c.get("created_by") in (None, user["id"])]
        visible_course_ids = {c["id"] for c in courses}
        notes = [n for n in notes if n.get("course_id") in visible_course_ids]
        assignments = [a for a in assignments if a.get("course_id") in visible_course_ids]
        visible_assignment_ids = {a["id"] for a in assignments}
        submissions = [s for s in submissions if s.get("assignment_id") in visible_assignment_ids]
        visible_submission_ids = {s["id"] for s in submissions}
        milestones = [x for x in milestones if x.get("course_id") in visible_course_ids]
        grades = [g for g in grades if g.get("submission_id") in visible_submission_ids]
        reports = [r for r in reports if r.get("submission_id") in visible_submission_ids]

    def make_table(title, items, columns):
        headings = "".join(
            f"<th>{safe(c.replace('_', ' ').title())}</th>"
            for c in columns
        )

        if not items:
            rows = (
                f"<tr><td colspan='{len(columns)}' class='empty'>"
                "No records found</td></tr>"
            )
        else:
            rows = "".join(
                "<tr>"
                + "".join(
                    f"<td>{safe(item.get(c, ''))}</td>"
                    for c in columns
                )
                + "</tr>"
                for item in items
            )

        return f"""
        <section class="panel"
            id="{safe(title.lower().replace(' ', '-'))}">
          <div class="panel-head">
            <div>
              <small>DATABASE RECORDS</small>
              <h2>{safe(title)}</h2>
            </div>
            <span class="count">{len(items)}</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr>{headings}</tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
        </section>
        """

    tables = [
        make_table(
            "Courses",
            courses,
            ["id", "course_code", "name", "semester"],
        ),
        make_table(
            "Notes",
            notes,
            ["id", "title", "current_version"],
        ),
        make_table(
            "Assignments",
            assignments,
            ["id", "title", "deadline", "max_marks"],
        ),
        make_table(
            "Submissions",
            submissions,
            ["id", "assignment_title", "student_name", "status"],
        ),
        make_table(
            "Similarity Reports",
            reports,
            ["id", "submission_id", "similarity_score", "reviewed_by"],
        ),
        make_table(
            "Milestones",
            milestones,
            ["id", "title", "deadline", "status", "progress"],
        ),
        make_table(
            "Grades",
            grades,
            ["id", "student_name", "marks", "status"],
        ),
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentic AI Course Organizer</title>

<style>
:root {{
    --bg: #0b1020;
    --panel: #121d32;
    --line: #293753;
    --text: #edf3ff;
    --muted: #9baecc;
    --accent: #7d8cff;
    --cyan: #52d6c7;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: radial-gradient(
        ellipse at top left,
        #1b2a50,
        transparent 38%
    ), var(--bg);
    color: var(--text);
    font: 14px/1.5 Segoe UI, Arial, sans-serif;
}}

header {{
    padding: 30px clamp(18px, 4vw, 55px);
    border-bottom: 1px solid var(--line);
    background: #0c1426dd;
}}

header small,
.panel-head small {{
    color: var(--cyan);
    font-weight: bold;
    letter-spacing: 1.5px;
    font-size: 10px;
}}

h1 {{
    margin: 5px 0;
    font-size: clamp(26px, 3vw, 38px);
}}

header p {{
    color: var(--muted);
    margin: 0;
}}

main {{
    max-width: 1450px;
    margin: auto;
    padding: 24px clamp(14px, 3vw, 40px);
}}

.top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}}

.btn {{
    background: linear-gradient(
        100deg,
        var(--accent),
        var(--cyan)
    );
    border: 0;
    border-radius: 8px;
    padding: 10px 14px;
    font-weight: bold;
    color: #081020;
    cursor: pointer;
}}

.btn:disabled {{
    opacity: 0.6;
    cursor: wait;
}}

.stats {{
    display: grid;
    grid-template-columns: repeat(6, minmax(110px, 1fr));
    gap: 12px;
    margin: 22px 0;
}}

.stat,
.panel,
.action {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 13px;
}}

.stat {{
    padding: 16px;
}}

.stat span {{
    display: block;
    color: var(--muted);
    font-size: 12px;
}}

.stat strong {{
    font-size: 29px;
    display: block;
    margin-top: 6px;
}}

h2 {{
    font-size: 17px;
    margin: 2px 0;
}}

h3 {{
    margin: 0 0 4px;
}}

.section-title {{
    margin: 30px 0 13px;
}}

.section-title p,
.action p {{
    margin: 4px 0 14px;
    color: var(--muted);
    font-size: 12px;
}}

.workbench {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 13px;
}}

.action {{
    padding: 18px;
    min-width: 0;
}}

.fields {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}}

.field {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 0;
}}

.full {{
    grid-column: 1 / -1;
}}

label {{
    font-size: 11px;
    color: #b8c8e0;
}}

input,
select,
textarea {{
    width: 100%;
    background: #0b1324;
    color: var(--text);
    border: 1px solid #30415f;
    border-radius: 7px;
    padding: 10px;
    font: inherit;
}}

textarea {{
    min-height: 70px;
    resize: vertical;
}}

.form-end {{
    display: flex;
    justify-content: flex-end;
    margin-top: 12px;
}}

.panel {{
    overflow: hidden;
    margin: 14px 0;
}}

.panel-head {{
    padding: 15px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--line);
}}

.lab-demo-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 12px;
    margin-top: 14px;
}}
.lab-demo-card {{
    border: 1px solid var(--line);
    border-radius: 12px;
    background: rgba(255,255,255,.025);
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 9px;
}}
.lab-demo-card p {{ color: var(--muted); font-size: 13px; margin: 0; flex: 1; }}
.lab-demo-card .btn {{ align-self: flex-start; }}
.lab-demo-card h3 {{ margin: 0; font-size: 15px; }}

.count {{
    background: #253451;
    border-radius: 8px;
    padding: 4px 9px;
    color: #c8d7ff;
}}

.table-wrap {{
    overflow: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 470px;
}}

th,
td {{
    padding: 11px 14px;
    text-align: left;
    border-bottom: 1px solid #24314a;
    white-space: nowrap;
}}

th {{
    background: #16233a;
    color: #91a6c9;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    font-size: 10px;
}}

td {{
    font-size: 12px;
}}

tr:last-child td {{
    border: 0;
}}

.empty {{
    text-align: center;
    color: var(--muted);
    padding: 22px;
}}

#toast {{
    display: none;
    position: fixed;
    right: 20px;
    bottom: 20px;
    max-width: 420px;
    background: #1b2b48;
    border: 1px solid #476184;
    border-radius: 10px;
    padding: 14px;
    box-shadow: 0 8px 30px #0008;
    z-index: 1000;
}}

footer {{
    text-align: center;
    color: #7285a6;
    padding: 24px;
    font-size: 11px;
}}

@media (max-width: 1050px) {{
    .stats {{
        grid-template-columns: repeat(3, 1fr);
    }}
}}

@media (max-width: 680px) {{
    .top {{
        align-items: flex-start;
        flex-direction: column;
    }}

    .stats {{
        grid-template-columns: repeat(2, 1fr);
    }}

    .workbench,
    .fields {{
        grid-template-columns: 1fr;
    }}

    .full {{
        grid-column: auto;
    }}
}}
</style>
</head>

<body>
<header>
    <div class="top">
        <div>
            <small>ACADEMIC OPERATIONS / CONTROL CENTER</small>
            <h1>Agentic AI Course Organizer</h1>
            <p>Logged in as: {safe(user["name"])} ({safe(user["role"])})</p>

            <form method="post" action="/logout">
            <button class="btn" type="submit">Log out</button>
            </form>
            <p>
                Welcome, {safe(user["name"])}!
    You are logged in as a {safe(user["role"])}.
            </p>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
            <a class="btn" href="#integrated-assistant" style="text-decoration:none;background:#10a58f;color:#fff;">
                ✨ Open Academic AI Assistant
            </a>
            <button class="btn" onclick="location.reload()">
                ↻ Refresh dashboard
            </button>
        </div>
    </div>
</header>

<main>
{f"""<section class=\"panel\" style=\"padding:20px;margin-bottom:22px;\">
  <div class=\"panel-head\"><div><small>PROFESSOR CONTROLS</small><h2>Manage students and courses</h2></div></div>
  <p style=\"color:var(--muted);\">Create student accounts, add multiple courses/subjects, and enrol students into the relevant courses.</p>
  <div class=\"workbench\">
    <section class=\"action\" style=\"padding:16px;\"><h3>➕ Add student</h3>
      <form id=\"createStudentForm\"><div class=\"fields\">
        <div class=\"field\"><label>Full name</label><input name=\"name\" required></div>
        <div class=\"field\"><label>Email</label><input name=\"email\" type=\"email\" required></div>
        <div class=\"field\"><label>Temporary password</label><input name=\"password\" type=\"password\" minlength=\"8\" required></div>
      </div><button class=\"btn\">Create student</button></form>
    </section>
    <section class=\"action\" style=\"padding:16px;\"><h3>📚 Add course / subject</h3>
      <form id=\"createCourseForm\"><div class=\"fields\">
        <div class=\"field\"><label>Course code</label><input name=\"course_code\" placeholder=\"CS201\" required></div>
        <div class=\"field\"><label>Course name</label><input name=\"name\" placeholder=\"Database Management Systems\" required></div>
        <div class=\"field\"><label>Semester (1–12)</label><input name=\"semester\" type=\"number\" min=\"1\" max=\"12\" required></div>
        <div class=\"field full\"><label>Description</label><textarea name=\"description\"></textarea></div>
      </div><button class=\"btn\">Create course</button></form>
    </section>
    <section class=\"action\" style=\"padding:16px;\"><h3>🧑‍🎓 Enrol students into a course</h3>
      <form id=\"enrolStudentsForm\"><div class=\"fields\">
        <div class=\"field\"><label>Course ID</label><input name=\"course_id\" type=\"number\" min=\"1\" required></div>
        <div class=\"field full\"><label>Student IDs (comma-separated)</label><input name=\"student_ids\" placeholder=\"3, 4, 5\" required></div>
      </div><button class=\"btn\">Enrol selected students</button></form>
    </section>
  </div>
  <div id=\"managementResult\" role=\"status\" style=\"margin-top:12px;color:var(--cyan);white-space:pre-wrap;\"></div>
  <div class=\"workbench\" style=\"margin-top:16px;\">
    <section class=\"action\" style=\"padding:16px;\"><h3>Student accounts</h3><div class=\"table-wrap\"><table><thead><tr><th>ID</th><th>Name</th><th>Email</th></tr></thead><tbody id=\"managedStudents\"><tr><td colspan=3>Loading…</td></tr></tbody></table></div></section>
    <section class=\"action\" style=\"padding:16px;\"><h3>Available courses</h3><div class=\"table-wrap\"><table><thead><tr><th>ID</th><th>Code</th><th>Course</th><th>Semester</th></tr></thead><tbody id=\"managedCourses\"><tr><td colspan=4>Loading…</td></tr></tbody></table></div></section>
  </div>
</section>""" if user['role'] == 'professor' else ''}
<section class="panel" id="integrated-assistant" style="padding:22px;margin:0 0 24px;">
  <div class="panel-head"><div><small>ONE ENTRY POINT · FOURTEEN INTEGRATED CAPABILITIES</small><h2>Academic AI Assistant</h2></div></div>
  <p style="color:var(--muted);">Use this single assistant entry point for academic requests and all 14 independently executable lab capabilities. Enter a lab-specific request; each result shows the capability, actual components invoked, structured output and persisted execution history.</p>
  <form id="assistantForm">
    <div class="field"><label for="assistantQuestion">What would you like the assistant to do?</label><textarea id="assistantQuestion" name="question" rows="3" maxlength="1000" placeholder="Example: Analyse my pending assignments and suggest what I should complete first…" required></textarea></div>
    <div class="form-end"><button class="btn">Run integrated assistant</button></div>
  </form>
  <div id="assistant-result" aria-live="polite" style="margin-top:16px;white-space:pre-wrap;overflow-wrap:anywhere;color:#c8d7ff;"></div>
  <div id="assistant-history" style="margin-top:14px;"></div>
</section>
<div class="stats">
    <div class="stat">
        <span>Courses</span>
        <strong>{len(courses)}</strong>
    </div>
    <div class="stat">
        <span>Notes</span>
        <strong>{len(notes)}</strong>
    </div>
    <div class="stat">
        <span>Assignments</span>
        <strong>{len(assignments)}</strong>
    </div>
    <div class="stat">
        <span>Submissions</span>
        <strong>{len(submissions)}</strong>
    </div>
    <div class="stat">
        <span>Milestones</span>
        <strong>{len(milestones)}</strong>
    </div>
    <div class="stat">
        <span>Grades</span>
        <strong>{len(grades)}</strong>
    </div>
</div>

<div class="section-title">
    <h2>Agent Workbench</h2>
    <p>
        Create and manage academic records through the existing
        FastAPI endpoints.
    </p>
</div>

<div class="workbench">

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>📚 Create a note</h3>
<p>Notes Repository Agent · A note is stored with its initial version.</p>
<form data-endpoint="/api/notes">
<div class="fields">
    <div class="field">
        <label>Course ID</label>
        <input name="course_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Created by (user ID)</label>
        <input name="created_by" type="number" min="1" value="2" required>
    </div>
    <div class="field full">
        <label>Title</label>
        <input name="title" required>
    </div>
    <div class="field full">
        <label>Content</label>
        <textarea name="content" required></textarea>
    </div>
</div>
<div class="form-end">
    <button class="btn">Create note</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>📝 Create assignment</h3>
<p>Assignment Distribution Agent · Define deadline and maximum marks.</p>
<form data-endpoint="/api/assignments">
<div class="fields">
    <div class="field">
        <label>Course ID</label>
        <input name="course_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Created by (user ID)</label>
        <input name="created_by" type="number" min="1" value="2" required>
    </div>
    <div class="field full">
        <label>Title</label>
        <input name="title" required>
    </div>
    <div class="field">
        <label>Deadline</label>
        <input name="deadline" type="datetime-local" required>
    </div>
    <div class="field">
        <label>Maximum marks</label>
        <input name="max_marks" type="number" min=".1"
               step=".1" value="100" required>
    </div>
    <div class="field full">
        <label>Description</label>
        <textarea name="description"></textarea>
    </div>
</div>
<div class="form-end">
    <button class="btn">Create assignment</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'student' else 'none'};">
<h3>📤 Record a submission</h3>
<p>Submission Collection Agent · Save student work against an assignment.</p>
<form data-endpoint="/api/submissions">
<div class="fields">
    <div class="field">
        <label>Assignment ID</label>
        <input name="assignment_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Student ID</label>
        <input name="student_id" type="number" min="1" value="1" required>
    </div>
    <div class="field full">
        <label>Submission content</label>
        <textarea name="content"></textarea>
    </div>
    <div class="field full">
        <label>File path (optional)</label>
        <input name="file_path">
    </div>
</div>
<div class="form-end">
    <button class="btn">Record submission</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>🔍 Compare two student submissions</h3>
<p>Automatically compares submitted text and creates a similarity report for professor review. The score is a screening signal, not an automatic plagiarism decision.</p>
<form id="similarityCompareForm">
<div class="fields">
  <div class="field"><label>First submission ID</label><input name="submission_id" type="number" min="1" required></div>
  <div class="field"><label>Second submission ID</label><input name="compared_submission_id" type="number" min="1" required></div>
</div>
<div class="form-end"><button class="btn" type="submit">Compare submissions</button></div>
</form>
<pre id="similarity-compare-result" class="result-box" aria-live="polite"></pre>
<h3>🔍 Save similarity report manually</h3>
<p>
Optional manual entry for externally calculated similarity scores.
</p>
<form data-endpoint="/api/similarity/reports">
<div class="fields">
    <div class="field">
        <label>Submission ID</label>
        <input name="submission_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Compared submission ID (optional)</label>
        <input name="compared_submission_id" type="number" min="1">
    </div>
    <div class="field">
        <label>Similarity score (%)</label>
        <input name="similarity_score" type="number"
               min="0" max="100" step=".1" required>
    </div>
    <div class="field">
        <label>Details</label>
        <input name="details">
    </div>
</div>
<div class="form-end">
    <button class="btn">Save report</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>🎓 Prepare a grade</h3>
<p>Grading Assistance Agent · Creates or updates a grade for review.</p>
<form data-endpoint="/api/grades">
<div class="fields">
    <div class="field">
        <label>Submission ID</label>
        <input name="submission_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Graded by (user ID)</label>
        <input name="graded_by" type="number" min="1" value="2" required>
    </div>
    <div class="field">
        <label>Marks</label>
        <input name="marks" type="number" min="0" step=".1" required>
    </div>
    <div class="field">
        <label>Feedback</label>
        <input name="feedback">
    </div>
</div>
<div class="form-end">
    <button class="btn">Save grade</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>🎯 Create milestone</h3>
<p>Milestone Tracking Agent · Track course project deliverables.</p>
<form data-endpoint="/api/milestones">
<div class="fields">
    <div class="field">
        <label>Course ID</label>
        <input name="course_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Created by (user ID)</label>
        <input name="created_by" type="number" min="1" value="2" required>
    </div>
    <div class="field full">
        <label>Title</label>
        <input name="title" required>
    </div>
    <div class="field">
        <label>Deadline</label>
        <input name="deadline" type="datetime-local" required>
    </div>
    <div class="field">
        <label>Description</label>
        <input name="description">
    </div>
</div>
<div class="form-end">
    <button class="btn">Create milestone</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>🛡️ Review similarity report</h3>
<p>Human review step · Records who reviewed a report.</p>
<form id="reviewForm">
<div class="fields">
    <div class="field">
        <label>Report ID</label>
        <input name="report_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Reviewer user ID</label>
        <input name="reviewer_id" type="number" min="1" value="2" required>
    </div>
</div>
<div class="form-end">
    <button class="btn">Mark reviewed</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>✓ Approve grade</h3>
<p>Grade Publishing Agent · Approval remains separate from publication.</p>
<form data-endpoint="/api/grades/approve">
<div class="fields">
    <div class="field">
        <label>Grade ID</label>
        <input name="grade_id" type="number" min="1" required>
    </div>
    <div class="field">
        <label>Approver user ID</label>
        <input name="approved_by" type="number" min="1" value="2" required>
    </div>
</div>
<div class="form-end">
    <button class="btn">Approve grade</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>📣 Publish approved grade</h3>
<p>Backend should reject grades that have not been approved.</p>
<form id="publishForm">
<div class="fields">
    <div class="field full">
        <label>Grade ID</label>
        <input name="grade_id" type="number" min="1" required>
    </div>
</div>
<div class="form-end">
    <button class="btn">Publish grade</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>◷ Update milestone progress</h3>
<p>Milestone Tracking Agent · Update progress and status.</p>
<form id="milestoneForm">
<div class="fields">
    <div class="field">
        <label>Milestone ID</label>
        <input name="milestone_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Progress (%)</label>
        <input name="progress" type="number" min="0" max="100" required>
    </div>
    <div class="field full">
        <label>Status</label>
        <select name="status">
            <option value="">Keep current status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Completed</option>
            <option value="overdue">Overdue</option>
        </select>
    </div>
</div>
<div class="form-end">
    <button class="btn">Update milestone</button>
</div>
</form>
</section>

<section class="action" style="display: {'block' if user['role'] == 'professor' else 'none'};">
<h3>⇧ Update submission status</h3>
<p>Submission Collection Agent · Change a submission's workflow status.</p>
<form id="statusForm">
<div class="fields">
    <div class="field">
        <label>Submission ID</label>
        <input name="submission_id" type="number" min="1" value="1" required>
    </div>
    <div class="field">
        <label>Status</label>
        <select name="status">
            <option>submitted</option>
            <option>draft</option>
            <option>late</option>
            <option>reviewed</option>
        </select>
    </div>
</div>
<div class="form-end">
    <button class="btn">Update status</button>
</div>
</form>
</section>

</div>

<section class="panel" id="student-academic-tools" style="display: {'block' if user['role'] == 'student' else 'none'};">
  <div class="panel-head"><div><small>PERSONALISED ACADEMIC VIEW</small><h2>My notes and deadlines</h2></div></div>
  <div style="padding:18px;">
    <h3>Downloadable course notes</h3>
    <p>Notes are filtered to courses in which your account is enrolled.</p>
    <div id="my-notes">Loading your notes…</div>
    <h3 style="margin-top:22px;">Assignment tracker</h3>
    <p>Statuses are calculated from your own submission records and assignment deadlines.</p>
    <div id="my-assignments">Loading your assignments…</div>
  </div>
</section>

<div class="section-title">
    <h2>Live database records</h2>
    <p>After a successful operation, the page refreshes to show saved data.</p>
</div>

{''.join(tables)}

<footer>
    Agentic AI Course Organizer · FastAPI · SQLite · Integrated agents · Tools · Skills · Connectors
</footer>
</main>

<div id="toast" role="status"></div>

<script>
const toastEl = document.getElementById('toast');

function toast(msg, ok = true) {{
    toastEl.textContent = (ok ? '✓ ' : '⚠ ') + msg;
    toastEl.style.display = 'block';
    toastEl.style.borderColor = ok ? '#3b9488' : '#b05b5b';
    setTimeout(() => toastEl.style.display = 'none', 5500);
}}

function obj(form) {{
    const result = {{}};

    for (const [k, v] of new FormData(form).entries()) {{
        if (v === '') continue;

        const el = form.elements.namedItem(k);
        result[k] = el && el.type === 'number' ? Number(v) : v;
    }}

    return result;
}}

async function api(url, method, body) {{
    const opts = {{
        method,
        headers: {{'Content-Type': 'application/json'}}
    }};

    if (body !== undefined) {{
        opts.body = JSON.stringify(body);
    }}

    const r = await fetch(url, opts);
    const data = await r.json();

    if (!r.ok) {{
        throw new Error(data.detail || JSON.stringify(data));
    }}

    if (data && data.success === false) {{
        throw new Error(data.message || 'Agent operation failed');
    }}

    return data;
}}

async function refreshManagementLists() {{
  const result = document.getElementById('managementResult');
  try {{
    const [students, courses] = await Promise.all([
      api('/api/professor/students', 'GET'),
      api('/api/professor/courses', 'GET')
    ]);
    document.getElementById('managedStudents').innerHTML = students.map(s =>
      `<tr><td>${{s.id}}</td><td>${{escapeHtml(s.name)}}</td><td>${{escapeHtml(s.email)}}</td></tr>`
    ).join('') || '<tr><td colspan="3">No students yet</td></tr>';
    document.getElementById('managedCourses').innerHTML = courses.map(c =>
      `<tr><td>${{c.id}}</td><td>${{escapeHtml(c.course_code)}}</td><td>${{escapeHtml(c.name)}}</td><td>${{c.semester}}</td></tr>`
    ).join('') || '<tr><td colspan="4">No courses yet</td></tr>';
  }} catch (e) {{ if (result) result.textContent = e.message; }}
}}
function escapeHtml(value) {{
  return String(value ?? '').replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
}}
const studentForm = document.getElementById('createStudentForm');
if (studentForm) {{
  studentForm.addEventListener('submit', async e => {{
    e.preventDefault(); const d = obj(studentForm);
    try {{ const r = await api('/api/professor/students', 'POST', d);
      document.getElementById('managementResult').textContent = `Created student ${{r.name}} (ID ${{r.id}}). Share the temporary login securely.`;
      studentForm.reset(); await refreshManagementLists();
    }} catch (err) {{ document.getElementById('managementResult').textContent = err.message; }}
  }});
  document.getElementById('createCourseForm').addEventListener('submit', async e => {{
    e.preventDefault(); const d = obj(e.currentTarget);
    try {{ const r = await api('/api/professor/courses', 'POST', d);
      document.getElementById('managementResult').textContent = `Created ${{r.course_code}} — ${{r.name}} (Course ID ${{r.id}}).`;
      e.currentTarget.reset(); await refreshManagementLists();
    }} catch (err) {{ document.getElementById('managementResult').textContent = err.message; }}
  }});
  document.getElementById('enrolStudentsForm').addEventListener('submit', async e => {{
    e.preventDefault(); const d = obj(e.currentTarget);
    const student_ids = String(d.student_ids).split(',').map(x => Number(x.trim())).filter(Number.isInteger);
    try {{ const r = await api(`/api/professor/courses/${{d.course_id}}/enrol`, 'POST', {{student_ids}});
      document.getElementById('managementResult').textContent = `Enrolled ${{r.enrolled.length}} student(s).` + (r.errors.length ? '\\nNot enrolled: ' + r.errors.join('; ') : '');
      e.currentTarget.reset(); await refreshManagementLists();
    }} catch (err) {{ document.getElementById('managementResult').textContent = err.message; }}
  }});
  refreshManagementLists();
}}

document.querySelectorAll('form[data-endpoint]').forEach(form => {{
    form.addEventListener('submit', async e => {{
        e.preventDefault();

        const button = form.querySelector('button');
        const label = button.textContent;

        button.disabled = true;
        button.textContent = 'Working…';

        try {{
            const data = obj(form);

            if (data.deadline && data.deadline.length === 16) {{
                data.deadline = data.deadline.replace('T', ' ') + ':00';
            }}

            const result = await api(
                form.dataset.endpoint,
                'POST',
                data
            );

            toast(result.message || 'Operation successful');
            setTimeout(() => location.reload(), 900);
        }} catch (err) {{
            toast(err.message || 'Request failed', false);
        }} finally {{
            button.disabled = false;
            button.textContent = label;
        }}
    }});
}});

document.getElementById('reviewForm').addEventListener(
    'submit',
    async e => {{
        e.preventDefault();
        const d = obj(e.currentTarget);

        try {{
            const r = await api(
                '/api/similarity/reports/' + d.report_id + '/review',
                'POST',
                {{reviewer_id: d.reviewer_id}}
            );

            toast(r.message || 'Report reviewed');
            setTimeout(() => location.reload(), 900);
        }} catch (err) {{
            toast(err.message, false);
        }}
    }}
);

document.getElementById('publishForm').addEventListener(
    'submit',
    async e => {{
        e.preventDefault();
        const d = obj(e.currentTarget);

        if (!confirm(
            'Publish grade ' + d.grade_id +
            '? Confirm that it has already been approved.'
        )) return;

        try {{
            const r = await api(
                '/api/grades/' + d.grade_id + '/publish',
                'POST',
                {{}}
            );

            toast(r.message || 'Grade published');
            setTimeout(() => location.reload(), 900);
        }} catch (err) {{
            toast(err.message, false);
        }}
    }}
);

document.getElementById('milestoneForm').addEventListener(
    'submit',
    async e => {{
        e.preventDefault();
        const d = obj(e.currentTarget);

        const body = {{progress: d.progress}};
        if (d.status) body.status = d.status;

        try {{
            const r = await api(
                '/api/milestones/' + d.milestone_id,
                'PATCH',
                body
            );

            toast(r.message || 'Milestone updated');
            setTimeout(() => location.reload(), 900);
        }} catch (err) {{
            toast(err.message, false);
        }}
    }}
);

document.getElementById('statusForm').addEventListener(
    'submit',
    async e => {{
        e.preventDefault();
        const d = obj(e.currentTarget);

        try {{
            const r = await api(
                '/api/submissions/' + d.submission_id +
                '/status?status=' + encodeURIComponent(d.status),
                'PATCH'
            );

            toast(r.message || 'Status updated');
            setTimeout(() => location.reload(), 900);
        }} catch (err) {{
            toast(err.message, false);
        }}
    }}
);


async function loadStudentAcademicTools() {{
    const notesEl = document.getElementById('my-notes');
    const assignmentsEl = document.getElementById('my-assignments');
    if (!notesEl || !assignmentsEl) return;
    try {{
        const [nr, ar] = await Promise.all([
            fetch('/api/student/notes'), fetch('/api/student/assignments')
        ]);
        const notes = await nr.json();
        const assignments = await ar.json();
        if (!nr.ok) throw new Error(notes.detail || 'Could not load notes');
        if (!ar.ok) throw new Error(assignments.detail || 'Could not load assignments');
        notesEl.innerHTML = notes.length
          ? '<ul>' + notes.map(n => '<li>' + n.course_code + ' — ' + n.title +
              ' (v' + n.current_version + ') <a href="/api/notes/' + n.id +
              '/download">Download</a></li>').join('') + '</ul>'
          : '<p>No notes found for your enrolled courses yet.</p>';
        assignmentsEl.innerHTML = assignments.length
          ? '<div class="table-wrap"><table><thead><tr><th>Course</th><th>Assignment</th><th>Deadline</th><th>Status</th></tr></thead><tbody>' +
              assignments.map(a => '<tr><td>' + a.course_code + '</td><td>' +
              a.title + '</td><td>' + a.deadline + '</td><td>' +
              a.work_status + '</td></tr>').join('') + '</tbody></table></div>'
          : '<p>No assignments found for your enrolled courses.</p>';
    }} catch (err) {{
        notesEl.textContent = err.message;
        assignmentsEl.textContent = err.message;
    }}
}}
loadStudentAcademicTools();

const assistantForm = document.getElementById('assistantForm');
if (assistantForm) {{
  assistantForm.addEventListener('submit', async e => {{
    e.preventDefault();
    const output = document.getElementById('assistant-result');
    output.textContent = 'Working on your academic question…';
    try {{
      const result = await api('/api/assistant/query', 'POST',
        {{question: new FormData(assistantForm).get('question')}});
      const payload = result || {{}};
      const esc = value => String(value ?? '').replace(/[&<>\"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch]));
      const answer = payload.answer || payload.message || 'No answer was returned.';
      const trace = Array.isArray(payload.trace) ? payload.trace : [];
      const data = payload.data || {{}};
      let html = '<div class=\"assistant-answer\"><h3>Answer</h3><p>' + esc(answer).split(String.fromCharCode(10)).join('<br>') + '</p></div>';
      const entries = Object.entries(data);
      if (entries.length) {{
        html += '<h3>Relevant records</h3>';
        for (const [key, rows] of entries) {{
          html += '<h4>' + esc(key.replace(/_/g,' ')) + '</h4>';
          if (Array.isArray(rows) && rows.length) {{
            const cols = Object.keys(rows[0]).filter(k => !['content','file_path'].includes(k)).slice(0,6);
            html += '<div class=\"table-wrap\"><table><thead><tr>' + cols.map(c => '<th>'+esc(c.replace(/_/g,' '))+'</th>').join('') + '</tr></thead><tbody>' + rows.map(row => '<tr>' + cols.map(c => '<td>'+esc(row[c])+'</td>').join('') + '</tr>').join('') + '</tbody></table></div>';
          }} else html += '<p>No matching records found.</p>';
        }}
      }}
      html += '<details open><summary>Execution trace — components actually invoked</summary><ol>' + trace.map(t => '<li><b>Lab '+esc(t.lab ?? '-')+' — '+esc(t.component ?? 'Component')+'</b>: '+esc(t.status ?? 'completed')+(t.tool ? ' · tool: '+esc(t.tool) : '')+(t.intents ? ' ('+esc(t.intents.join(', '))+')' : '')+(t.error ? ' · '+esc(t.error) : '')+'</li>').join('') + '</ol></details>';
      if (payload.result) html += '<details><summary>Detailed execution output (JSON)</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere;">' + esc(JSON.stringify(payload.result, null, 2)) + '</pre></details>';
      output.innerHTML = html;
      try {{
        const history = await api('/api/assistant/history', 'GET');
        const hist = document.getElementById('assistant-history');
        const rows = Array.isArray(history.executions) ? history.executions : [];
        hist.innerHTML = '<details><summary>Recent persisted lab executions (' + rows.length + ')</summary><div class="table-wrap"><table><thead><tr><th>Lab</th><th>Status</th><th>Input</th><th>Duration</th><th>Run ID</th></tr></thead><tbody>' + rows.map(r => '<tr><td>' + esc(r.lab_id) + '</td><td>' + esc(r.status) + '</td><td>' + esc(r.input) + '</td><td>' + esc(r.duration) + 's</td><td>' + esc(r.id) + '</td></tr>').join('') + '</tbody></table></div></details>';
      }} catch (historyError) {{ /* history panel is supplementary */ }}
    }} catch (err) {{
      output.textContent = 'Assistant error: ' + err.message;
    }}
  }});
}}
const compareForm = document.getElementById('similarityCompareForm');
if (compareForm) {{
  compareForm.addEventListener('submit', async e => {{
    e.preventDefault();
    const out = document.getElementById('similarity-compare-result');
    out.textContent = 'Comparing submissions…';
    try {{
      const form = new FormData(compareForm);
      const result = await api('/api/similarity/compare', 'POST', {{
        submission_id: Number(form.get('submission_id')),
        compared_submission_id: Number(form.get('compared_submission_id'))
      }});
      const d = result.data || result;
      const a = d.submission_a || {{}};
      const b = d.submission_b || {{}};
      const nl = String.fromCharCode(10);
      out.textContent = 'COMPARISON COMPLETE' + nl +
        'Similarity score: ' + Number(d.similarity_score).toFixed(2) + '%' + nl +
        'Submission ' + a.id + ' (' + (a.student || 'Student') + ' — ' + (a.assignment || 'Assignment') + ') compared with submission ' + b.id + ' (' + (b.student || 'Student') + ' — ' + (b.assignment || 'Assignment') + ').' + nl +
        (d.requires_human_review ? 'Flagged for professor review.' : 'Below the configured review threshold.') + nl +
        'Method: ' + (d.metrics && d.metrics.method ? d.metrics.method : '') + nl +
        (d.metrics && d.metrics.disclaimer ? d.metrics.disclaimer : '');
    }} catch (err) {{ out.textContent = 'Comparison error: ' + err.message; }}
  }});
}}
</script>
</body>
</html>
"""
@app.get("/health")
def health():
    return {"status": "ok"}


class StudentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class CourseCreateRequest(BaseModel):
    course_code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=160)
    semester: int = Field(ge=1, le=12)
    description: str = ""


class EnrolStudentsRequest(BaseModel):
    student_ids: list[int] = Field(min_length=1, max_length=200)


class NoteRequest(BaseModel):
    course_id: int
    title: str = Field(min_length=1)
    content: str
    created_by: int


class NoteVersionRequest(BaseModel):
    content: str
    created_by: int


class AssignmentRequest(BaseModel):
    course_id: int
    title: str = Field(min_length=1)
    description: str = ""
    deadline: str
    max_marks: float = Field(default=100, gt=0)
    created_by: int


class SubmissionRequest(BaseModel):
    assignment_id: int
    student_id: int
    content: str = ""
    file_path: str | None = None


class SimilarityReportRequest(BaseModel):
    submission_id: int
    compared_submission_id: int | None = None
    similarity_score: float = Field(ge=0, le=100)
    details: str = ""


class SimilarityReviewRequest(BaseModel):
    reviewer_id: int


class SimilarityCompareRequest(BaseModel):
    submission_id: int = Field(gt=0)
    compared_submission_id: int = Field(gt=0)


class GradeRequest(BaseModel):
    submission_id: int
    marks: float | None = Field(default=None, ge=0)
    feedback: str = ""
    graded_by: int


class GradeApprovalRequest(BaseModel):
    grade_id: int
    approved_by: int


class MilestoneRequest(BaseModel):
    course_id: int
    title: str = Field(min_length=1)
    description: str = ""
    deadline: str
    created_by: int


class MilestoneProgressRequest(BaseModel):
    progress: int = Field(ge=0, le=100)
    status: str | None = None


class AssistantQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)



@app.get("/api/notes")
def list_notes(course_id: int | None = None):
    return orchestrator.execute(
        "notes",
        "list_notes",
        course_id=course_id,
    )


@app.get("/api/notes/{note_id}")
def get_note(note_id: int):
    return orchestrator.execute(
        "notes",
        "get_note",
        note_id=note_id,
    )


@app.get("/api/professor/students")
def professor_list_students(request: Request):
    require_role(request, "professor")
    return [
        {"id": u["id"], "name": u["name"], "email": u["email"]}
        for u in db.list_users("student")
    ]


@app.post("/api/professor/students")
def professor_create_student(payload: StudentCreateRequest, request: Request):
    require_role(request, "professor")
    try:
        student = db.create_user(payload.name, payload.email, "student")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(payload.password), student["id"]),
            )
        return {"id": student["id"], "name": student["name"], "email": student["email"], "role": "student"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/professor/courses")
def professor_list_courses(request: Request):
    user = require_role(request, "professor")
    return [c for c in db.list_courses() if c.get("created_by") in (None, user["id"])]


@app.post("/api/professor/courses")
def professor_create_course(payload: CourseCreateRequest, request: Request):
    user = require_role(request, "professor")
    try:
        return db.create_course(
            payload.course_code, payload.name, payload.semester,
            payload.description, created_by=user["id"]
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="That course code already exists.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/professor/courses/{course_id}/enrol")
def professor_enrol_students(course_id: int, payload: EnrolStudentsRequest, request: Request):
    user = require_role(request, "professor")
    course = db.get_course(course_id)
    if not course or course.get("created_by") not in (None, user["id"]):
        raise HTTPException(status_code=404, detail="Course not found in your teaching list.")
    enrolled, errors = [], []
    for student_id in dict.fromkeys(payload.student_ids):
        try:
            db.enroll_student(course_id, student_id)
            enrolled.append(student_id)
        except sqlite3.IntegrityError:
            errors.append(f"Student {student_id} is already enrolled")
        except ValueError as exc:
            errors.append(f"Student {student_id}: {exc}")
    return {"course_id": course_id, "enrolled": enrolled, "errors": errors}



@app.post("/api/notes/{note_id}/versions")
def add_note_version(note_id: int, request: NoteVersionRequest):
    return orchestrator.execute(
        "notes",
        "add_version",
        note_id=note_id,
        content=request.content,
        created_by=request.created_by,
    )


@app.post("/api/assignments")
def create_assignment(
    request: Request,
    assignment: AssignmentRequest,
):
    user = require_role(request, "professor")

    return orchestrator.execute(
        "assignments",
        "create_assignment",
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        deadline=assignment.deadline,
        max_marks=assignment.max_marks,
        created_by=user["id"],
    )


@app.get("/api/assignments")
def list_assignments(course_id: int | None = None):
    return orchestrator.execute(
        "assignments",
        "list_assignments",
        course_id=course_id,
    )


@app.post("/api/notes")
def create_note(
    request: Request,
    note: NoteRequest,
):
    user = require_role(request, "professor")

    return orchestrator.execute(
        "notes",
        "create_note",
        course_id=note.course_id,
        title=note.title,
        content=note.content,
        created_by=user["id"],
    )

@app.post("/api/submissions")
def create_submission(
    request: Request,
    submission: SubmissionRequest,
):
    user = require_role(request, "student")
    enrolled_assignment_ids = {
        item["assignment_id"] for item in db.list_student_assignments(user["id"])
    }
    if submission.assignment_id not in enrolled_assignment_ids:
        raise HTTPException(
            status_code=403,
            detail="You can submit only assignments from your enrolled courses.",
        )

    return orchestrator.execute(
        "submissions",
        "submit_assignment",
        assignment_id=submission.assignment_id,
        student_id=user["id"],
        content=submission.content,
        file_path=submission.file_path,
    )

@app.get("/api/submissions")
def list_submissions(assignment_id: int | None = None):
    return orchestrator.execute(
        "submissions",
        "list_submissions",
        assignment_id=assignment_id,
    )


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: int):
    return orchestrator.execute(
        "submissions",
        "get_submission",
        submission_id=submission_id,
    )


@app.patch("/api/submissions/{submission_id}/status")
def update_submission_status(submission_id: int, status: str):
    allowed = {"draft", "submitted", "late", "reviewed"}

    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {sorted(allowed)}",
        )

    return orchestrator.execute(
        "submissions",
        "update_status",
        submission_id=submission_id,
        status=status,
    )


@app.post("/api/similarity/compare")
def compare_submissions(request: Request, body: SimilarityCompareRequest):
    user = require_role(request, "professor")
    result = orchestrator.execute(
        "similarity", "compare_submissions",
        submission_id=body.submission_id,
        compared_submission_id=body.compared_submission_id,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Comparison failed."))
    return result


@app.post("/api/similarity/reports")
def create_similarity_report(
    request: Request,
    report: SimilarityReportRequest,
):
    user = require_role(request, "professor")

    return orchestrator.execute(
        "similarity",
        "create_report",
        submission_id=report.submission_id,
        compared_submission_id=report.compared_submission_id,
        similarity_score=report.similarity_score,
        details=report.details,
    )



@app.get("/api/similarity/reports")
def list_similarity_reports(request: Request, submission_id: int | None = None):
    require_role(request, "professor")
    return orchestrator.execute(
        "similarity",
        "list_reports",
        submission_id=submission_id,
    )


@app.post("/api/similarity/reports/{report_id}/review")
def review_similarity_report(
report_id: int,
request: Request,
review: SimilarityReviewRequest,
):
 user = require_role(request, "professor")
 return orchestrator.execute(
    "similarity",
    "review_report",
    report_id=report_id,
    reviewer_id=user["id"],
)



@app.post("/api/grades")
def create_or_update_grade(
    request: Request,
    grade: GradeRequest,
):
    user = require_role(request, "professor")

    return orchestrator.execute(
        "grading",
        "create_or_update_grade",
        submission_id=grade.submission_id,
        marks=grade.marks,
        feedback=grade.feedback,
        graded_by=user["id"],
    )


@app.get("/api/grades")
def list_grades(status: str | None = None):
    return orchestrator.execute(
        "grading",
        "list_grades",
        status=status,
    )


@app.get("/api/grades/submission/{submission_id}")
def get_grade_for_submission(submission_id: int):
    return orchestrator.execute(
        "grading",
        "get_grade",
        submission_id=submission_id,
    )


@app.post("/api/grades/approve")
def approve_grade(
    request: Request,
    approval: GradeApprovalRequest,
):
    user = require_role(request, "professor")

    return orchestrator.execute(
        "grade_publishing",
        "approve_grade",
        grade_id=approval.grade_id,
        approved_by=user["id"],
    )


@app.post("/api/grades/{grade_id}/publish")
def publish_grade(
grade_id: int,
request: Request,
):
 user = require_role(request, "professor")


 return orchestrator.execute(
    "grade_publishing",
    "publish_grade",
    grade_id=grade_id,
)




@app.post("/api/milestones")
def create_milestone(
request: Request,
milestone: MilestoneRequest,
):
 user = require_role(request, "professor")


 return orchestrator.execute(
    "milestones",
    "create_milestone",
    course_id=milestone.course_id,
    title=milestone.title,
    description=milestone.description,
    deadline=milestone.deadline,
    created_by=user["id"],
)



@app.get("/api/milestones")
def list_milestones(course_id: int | None = None):
    return orchestrator.execute(
        "milestones",
        "list_milestones",
        course_id=course_id,
    )


@app.patch("/api/milestones/{milestone_id}")
def update_milestone(
    milestone_id: int,
    request: MilestoneProgressRequest,
):
    allowed = {
        "pending",
        "in_progress",
        "completed",
        "overdue",
    }

    if request.status is not None and request.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Invalid milestone status.",
        )

    return orchestrator.execute(
        "milestones",
        "update_progress",
        milestone_id=milestone_id,
        progress=request.progress,
        status=request.status,
    )

# ---------- STUDENT-SCOPED NOTES, DEADLINES, AND TOOL-USING ASSISTANT ----------

@app.get("/api/student/notes")
def student_notes(request: Request):
    user = require_role(request, "student")
    return db.list_student_notes(user["id"])


@app.get("/api/student/assignments")
def student_assignments(request: Request):
    user = require_role(request, "student")
    return db.list_student_assignments(user["id"])


@app.get("/api/notes/{note_id}/download")
def download_note(note_id: int, request: Request):
    user = require_role(request, "student", "professor", "admin")
    note = db.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")

    if user["role"] == "student":
        allowed = any(n["id"] == note_id for n in db.list_student_notes(user["id"]))
        if not allowed:
            raise HTTPException(status_code=403, detail="This note is not in one of your enrolled courses.")
    elif user["role"] == "professor":
        course = db.get_course(note["course_id"])
        if not course or course.get("created_by") != user["id"]:
            raise HTTPException(status_code=403, detail="You can only access notes for courses you own.")

    latest = note.get("latest_version") or {}
    stored_path = latest.get("file_path")
    if stored_path:
        path = Path(stored_path).expanduser().resolve()
        if path.is_file():
            return FileResponse(path, filename=path.name)

    content = latest.get("content") or ""
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", note["title"]).strip("._") or f"note_{note_id}"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}.txt"'},
    )


@app.post("/api/assistant/query")
def ask_academic_assistant(request: Request, body: AssistantQuestionRequest):
    """Single assistant entry point for all fourteen integrated capabilities."""
    user = require_role(request, "student", "professor")
    return unified_academic_agent.run(
        user_id=user["id"],
        question=body.question,
        role=user["role"],
    )


@app.post("/api/labs/{lab_id}/run")
def run_individual_lab(lab_id: int, request: Request, body: AssistantQuestionRequest):
    """Run one lab independently through the same audited runtime."""
    user = require_role(request, "student", "professor")
    if lab_id < 1 or lab_id > 14:
        raise HTTPException(status_code=404, detail="Lab ID must be between 1 and 14.")
    from agentic_core.runtime import run_lab
    try:
        payload = unified_academic_agent._lab_input(lab_id, body.question, user["id"])
        recorded = run_lab(lab_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": recorded["success"],
        "lab_id": lab_id,
        "status": recorded["status"],
        "run_id": recorded["run_id"],
        "duration_seconds": recorded["duration_seconds"],
        "input": recorded["input"],
        "output": recorded["output"],
    }


@app.get("/api/assistant/history")
def assistant_execution_history(request: Request, limit: int = 50):
    """Return recent persisted lab execution metadata for the signed-in user."""
    require_role(request, "student", "professor")
    from agentic_core.runtime import list_traces
    rows = list_traces(max(1, min(int(limit), 100)))
    # Do not expose raw stored outputs in the history table; detailed output is
    # available immediately in the authenticated assistant response.
    return {"executions": [{k: row.get(k) for k in ("id", "lab_id", "input", "status", "started_at", "duration")} for row in rows]}

# ---------- AGENTIC ACADEMIC WORKFLOWS: PLANNING, MEMORY, MONITORING ----------
from course_organizer.agents.academic_workflows import AcademicWorkflowService
from typing import Literal

academic_workflows = AcademicWorkflowService(db)

class StudyPlanRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=1000)
    days: int = Field(default=5, ge=1, le=60)
    hours_per_day: float = Field(default=2.0, ge=0.5, le=16)

class PlanDecisionRequest(BaseModel):
    status: Literal["approved", "rejected", "completed"]

class MemoryRequest(BaseModel):
    key: str = Field(min_length=2, max_length=100)
    value: str = Field(min_length=1, max_length=1000)

class DeadlineMonitorRequest(BaseModel):
    within_hours: int = Field(default=48, ge=1, le=720)

@app.post("/api/agentic/study-plans")
def create_agentic_study_plan(body: StudyPlanRequest, request: Request):
    user = require_role(request, "student")
    try:
        return academic_workflows.create_study_plan(user["id"], body.goal, body.days, body.hours_per_day)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/agentic/study-plans")
def get_agentic_study_plans(request: Request):
    user = require_role(request, "student")
    return {"plans": academic_workflows.list_study_plans(user["id"])}

@app.patch("/api/agentic/study-plans/{plan_id}")
def decide_agentic_study_plan(plan_id: int, body: PlanDecisionRequest, request: Request):
    user = require_role(request, "student")
    row = academic_workflows.update_plan_status(user["id"], plan_id, body.status)
    if not row:
        raise HTTPException(status_code=404, detail="Study plan not found for your account.")
    return {"success": True, "plan": row}

@app.put("/api/agentic/memory")
def save_academic_memory(body: MemoryRequest, request: Request):
    user = require_role(request, "student")
    try:
        return academic_workflows.remember(user["id"], body.key, body.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/agentic/memory")
def get_academic_memory(request: Request):
    user = require_role(request, "student")
    return {"memories": academic_workflows.memories(user["id"])}

@app.post("/api/agentic/deadline-monitor")
def run_deadline_monitor(body: DeadlineMonitorRequest, request: Request):
    user = require_role(request, "student")
    try:
        return academic_workflows.run_deadline_monitor(user["id"], body.within_hours)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/agentic/notifications")
def get_agentic_notifications(request: Request):
    user = require_role(request, "student")
    return {"notifications": academic_workflows.list_notifications(user["id"])}

@app.get("/api/agentic/execution-history")
def get_agent_execution_history(request: Request):
    user = require_role(request, "student", "professor", "admin")
    return {"runs": academic_workflows.recent_runs(user["id"])}

@app.get("/api/agentic/professor/missing-submissions")
def professor_missing_submissions(request: Request, course_id: int | None = None):
    user = require_role(request, "professor", "admin")
    return academic_workflows.professor_missing_submissions(user["id"], course_id)


