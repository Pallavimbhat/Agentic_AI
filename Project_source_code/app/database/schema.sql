PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. USERS: PROFESSORS AND STUDENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('professor', 'student')),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- 2. COURSES
-- =====================================================

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    description TEXT,
    semester INTEGER,
    professor_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (professor_id) REFERENCES users(id)
);


-- =====================================================
-- 3. STUDENT ENROLLMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
        CHECK(status IN ('active', 'inactive')),

    UNIQUE(student_id, course_id),

    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);


-- =====================================================
-- 4. NOTES REPOSITORY
-- =====================================================

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    uploaded_by INTEGER NOT NULL,
    current_version INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);


-- =====================================================
-- 5. NOTE VERSIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS note_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_by INTEGER NOT NULL,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(note_id, version_number),

    FOREIGN KEY (note_id) REFERENCES notes(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);


-- =====================================================
-- 6. ASSIGNMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    instructions TEXT,
    maximum_marks REAL NOT NULL,
    deadline TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    status TEXT DEFAULT 'published'
        CHECK(status IN ('draft', 'published', 'closed')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);


-- =====================================================
-- 7. ASSIGNMENT RESOURCES
-- =====================================================

CREATE TABLE IF NOT EXISTS assignment_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);


-- =====================================================
-- 8. GRADING RUBRICS
-- =====================================================

CREATE TABLE IF NOT EXISTS grading_rubrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    total_marks REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);


CREATE TABLE IF NOT EXISTS rubric_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rubric_id INTEGER NOT NULL,
    criterion_name TEXT NOT NULL,
    description TEXT,
    maximum_marks REAL NOT NULL,

    FOREIGN KEY (rubric_id) REFERENCES grading_rubrics(id)
);


-- =====================================================
-- 9. STUDENT SUBMISSIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,

    status TEXT DEFAULT 'pending_similarity'
        CHECK(status IN (
            'pending_similarity',
            'accepted',
            'flagged_review',
            'rejected_similarity',
            'late',
            'withdrawn'
        )),

    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
);


-- =====================================================
-- 10. SIMILARITY REPORTS
-- =====================================================

CREATE TABLE IF NOT EXISTS similarity_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    compared_submission_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL
        CHECK(similarity_score >= 0 AND similarity_score <= 100),

    comparison_method TEXT NOT NULL,
    decision TEXT NOT NULL
        CHECK(decision IN (
            'accepted',
            'flagged_review',
            'rejected_similarity'
        )),

    matching_details TEXT,
    reviewed_by INTEGER,
    review_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (submission_id) REFERENCES submissions(id),
    FOREIGN KEY (compared_submission_id) REFERENCES submissions(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);


-- =====================================================
-- 11. GRADES
-- =====================================================

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL UNIQUE,
    suggested_marks REAL,
    final_marks REAL,
    maximum_marks REAL NOT NULL,
    ai_feedback TEXT,
    professor_feedback TEXT,

    status TEXT DEFAULT 'pending'
        CHECK(status IN ('pending', 'approved', 'published')),

    graded_by INTEGER,
    approved_at TEXT,
    published_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (submission_id) REFERENCES submissions(id),
    FOREIGN KEY (graded_by) REFERENCES users(id)
);


-- =====================================================
-- 12. FEEDBACK
-- =====================================================

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade_id INTEGER NOT NULL,
    professor_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    comments TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (grade_id) REFERENCES grades(id),
    FOREIGN KEY (professor_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
);


-- =====================================================
-- 13. STUDENT PROJECTS
-- =====================================================

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'ongoing'
        CHECK(status IN ('ongoing', 'completed', 'on_hold')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
);


-- =====================================================
-- 14. PROJECT MILESTONES
-- =====================================================

CREATE TABLE IF NOT EXISTS project_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    deadline TEXT,
    status TEXT DEFAULT 'pending'
        CHECK(status IN ('pending', 'in_progress', 'completed', 'overdue')),
    completed_at TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);


-- =====================================================
-- 15. AI ASSISTANT CONVERSATIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);


CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender TEXT NOT NULL
        CHECK(sender IN ('user', 'assistant', 'agent')),
    content TEXT NOT NULL,
    agent_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);


-- =====================================================
-- 16. STUDENT MEMORY
-- =====================================================

CREATE TABLE IF NOT EXISTS student_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    memory_type TEXT NOT NULL,
    memory_content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES users(id)
);


-- =====================================================
-- 17. AGENT EXECUTION HISTORY
-- =====================================================

CREATE TABLE IF NOT EXISTS agent_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    user_id INTEGER,
    task TEXT NOT NULL,
    status TEXT NOT NULL,
    input_data TEXT,
    output_data TEXT,
    error_message TEXT,
    duration REAL,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- =====================================================
-- 18. WORKFLOW EXECUTIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT NOT NULL,
    triggered_by INTEGER,
    status TEXT NOT NULL,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,

    FOREIGN KEY (triggered_by) REFERENCES users(id)
);


CREATE TABLE IF NOT EXISTS workflow_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL,
    node_name TEXT NOT NULL,
    agent_name TEXT,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    input_data TEXT,
    output_data TEXT,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,

    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
);


-- =====================================================
-- 19. AUDIT LOGS
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- =====================================================
-- 20. NOTIFICATIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- =====================================================
-- 21. INDEXES FOR FASTER QUERIES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_enrollments_student
ON enrollments(student_id);

CREATE INDEX IF NOT EXISTS idx_enrollments_course
ON enrollments(course_id);

CREATE INDEX IF NOT EXISTS idx_assignments_course
ON assignments(course_id);

CREATE INDEX IF NOT EXISTS idx_submissions_assignment
ON submissions(assignment_id);

CREATE INDEX IF NOT EXISTS idx_submissions_student
ON submissions(student_id);

CREATE INDEX IF NOT EXISTS idx_submissions_hash
ON submissions(file_hash);

CREATE INDEX IF NOT EXISTS idx_similarity_submission
ON similarity_reports(submission_id);

CREATE INDEX IF NOT EXISTS idx_agent_executions
ON agent_executions(agent_name);

CREATE INDEX IF NOT EXISTS idx_notifications_user
ON notifications(user_id);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
ON messages(conversation_id);