from dataclasses import dataclass
from typing import Optional


# =====================================================
# 1. USER
# =====================================================

@dataclass
class User:
    id: Optional[int]
    full_name: str
    email: str
    role: str


# =====================================================
# 2. COURSE
# =====================================================

@dataclass
class Course:
    id: Optional[int]
    course_code: str
    course_name: str
    description: Optional[str]
    semester: Optional[int]
    professor_id: int


# =====================================================
# 3. ENROLLMENT
# =====================================================

@dataclass
class Enrollment:
    id: Optional[int]
    student_id: int
    course_id: int
    status: str = "active"


# =====================================================
# 4. NOTES
# =====================================================

@dataclass
class Note:
    id: Optional[int]
    course_id: int
    title: str
    description: Optional[str]
    uploaded_by: int
    current_version: int = 1


# =====================================================
# 5. ASSIGNMENT
# =====================================================

@dataclass
class Assignment:
    id: Optional[int]
    course_id: int
    title: str
    description: str
    maximum_marks: float
    deadline: str
    created_by: int
    status: str = "published"


# =====================================================
# 6. SUBMISSION
# =====================================================

@dataclass
class Submission:
    id: Optional[int]
    assignment_id: int
    student_id: int
    file_path: str
    file_hash: str
    status: str = "pending_similarity"


# =====================================================
# 7. SIMILARITY REPORT
# =====================================================

@dataclass
class SimilarityReport:
    id: Optional[int]
    submission_id: int
    compared_submission_id: int
    similarity_score: float
    comparison_method: str
    decision: str


# =====================================================
# 8. GRADE
# =====================================================

@dataclass
class Grade:
    id: Optional[int]
    submission_id: int
    maximum_marks: float
    suggested_marks: Optional[float] = None
    final_marks: Optional[float] = None
    status: str = "pending"


# =====================================================
# 9. STUDENT PROJECT
# =====================================================

@dataclass
class Project:
    id: Optional[int]
    course_id: int
    student_id: int
    title: str
    description: Optional[str]
    status: str = "ongoing"


# =====================================================
# 10. PROJECT MILESTONE
# =====================================================

@dataclass
class ProjectMilestone:
    id: Optional[int]
    project_id: int
    title: str
    description: Optional[str]
    deadline: Optional[str]
    status: str = "pending"


# =====================================================
# 11. AGENT EXECUTION
# =====================================================

@dataclass
class AgentExecution:
    id: Optional[int]
    agent_name: str
    task: str
    status: str
    user_id: Optional[int] = None
    duration: Optional[float] = None


# =====================================================
# 12. WORKFLOW EXECUTION
# =====================================================

@dataclass
class WorkflowExecution:
    id: Optional[int]
    workflow_name: str
    status: str
    triggered_by: Optional[int] = None


# =====================================================
# 13. WORKFLOW NODE
# =====================================================

@dataclass
class WorkflowNode:
    id: Optional[int]
    execution_id: int
    node_name: str
    operation: str
    status: str
    agent_name: Optional[str] = None


# =====================================================
# 14. NOTIFICATION
# =====================================================

@dataclass
class Notification:
    id: Optional[int]
    user_id: int
    title: str
    message: str
    is_read: bool = False