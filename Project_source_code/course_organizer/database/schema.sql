PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
email TEXT NOT NULL UNIQUE,
role TEXT NOT NULL CHECK (role IN ('admin', 'professor', 'student')),
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
id INTEGER PRIMARY KEY AUTOINCREMENT,
course_code TEXT NOT NULL UNIQUE,
name TEXT NOT NULL,
semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 12),
description TEXT DEFAULT '',
created_by INTEGER,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS course_enrollments (
course_id INTEGER NOT NULL,
student_id INTEGER NOT NULL,
enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (course_id, student_id),
FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
course_id INTEGER NOT NULL,
title TEXT NOT NULL,
current_version INTEGER NOT NULL DEFAULT 1,
created_by INTEGER,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS note_versions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
note_id INTEGER NOT NULL,
version_number INTEGER NOT NULL,
content TEXT NOT NULL,
file_path TEXT,
created_by INTEGER,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
UNIQUE (note_id, version_number),
FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS assignments (
id INTEGER PRIMARY KEY AUTOINCREMENT,
course_id INTEGER NOT NULL,
title TEXT NOT NULL,
description TEXT NOT NULL DEFAULT '',
deadline TEXT NOT NULL,
max_marks REAL NOT NULL DEFAULT 100 CHECK (max_marks > 0),
created_by INTEGER,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS submissions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
assignment_id INTEGER NOT NULL,
student_id INTEGER NOT NULL,
content TEXT DEFAULT '',
file_path TEXT,
status TEXT NOT NULL DEFAULT 'submitted'
CHECK (status IN ('draft', 'submitted', 'late', 'reviewed')),
submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
UNIQUE (assignment_id, student_id),
FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS similarity_reports (
id INTEGER PRIMARY KEY AUTOINCREMENT,
submission_id INTEGER NOT NULL,
compared_submission_id INTEGER,
similarity_score REAL NOT NULL CHECK (similarity_score BETWEEN 0 AND 100),
details TEXT DEFAULT '',
reviewed_by INTEGER,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
FOREIGN KEY (compared_submission_id) REFERENCES submissions(id) ON DELETE SET NULL,
FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS grades (
id INTEGER PRIMARY KEY AUTOINCREMENT,
submission_id INTEGER NOT NULL UNIQUE,
marks REAL CHECK (marks >= 0),
feedback TEXT DEFAULT '',
status TEXT NOT NULL DEFAULT 'draft'
CHECK (status IN ('draft', 'approved', 'published')),
graded_by INTEGER,
approved_by INTEGER,
published_at TEXT,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
FOREIGN KEY (graded_by) REFERENCES users(id) ON DELETE SET NULL,
FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS project_milestones (
id INTEGER PRIMARY KEY AUTOINCREMENT,
course_id INTEGER NOT NULL,
title TEXT NOT NULL,
description TEXT DEFAULT '',
deadline TEXT NOT NULL,
status TEXT NOT NULL DEFAULT 'pending'
CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
created_by INTEGER,
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
id INTEGER PRIMARY KEY AUTOINCREMENT,
actor_type TEXT NOT NULL,
actor_id INTEGER,
agent_name TEXT,
action TEXT NOT NULL,
entity_type TEXT NOT NULL,
entity_id INTEGER,
outcome TEXT NOT NULL CHECK (outcome IN ('success', 'failure')),
details TEXT DEFAULT '',
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_course
ON notes(course_id);

CREATE INDEX IF NOT EXISTS idx_assignments_course
ON assignments(course_id);

CREATE INDEX IF NOT EXISTS idx_submissions_assignment
ON submissions(assignment_id);

CREATE INDEX IF NOT EXISTS idx_grades_status
ON grades(status);

CREATE INDEX IF NOT EXISTS idx_milestones_deadline
ON project_milestones(deadline);
