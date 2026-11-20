from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
    Request
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from pathlib import Path
from uuid import uuid4

from app.services.course_service import CourseService
from app.services.notes_service import NotesService
from app.services.assignment_service import AssignmentService
from app.services.submission_service import SubmissionService
from app.services.grading_service import GradingService
from app.services.similarity_review_service import SimilarityReviewService
from app.services.project_service import ProjectService

from app.security.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_access_token
)

from app.core.config import (
    APP_NAME,
    APP_VERSION,
    NOTES_DIR,
    SUBMISSIONS_DIR
)
from app.services.academic_assistant_service import AcademicAssistantService
from app.services.conversation_service import ConversationService
from app.services.assistant_context_service import AssistantContextService
from app.agents.tool_using_agent import ToolUsingAgent

# =====================================================
# APPLICATION INITIALIZATION
# =====================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Agentic AI-based Course, Notes and Assignment Organizer API"
)


# =====================================================
# FRONTEND CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

# Create required folders before mounting StaticFiles (prevents startup failure).
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Serve CSS, JavaScript and image assets from /static.
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# Load Jinja2 HTML templates from frontend/templates.
templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)

security = HTTPBearer()




# =====================================================
# FRONTEND PAGE ROUTES
# =====================================================

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"app_name": APP_NAME}
    )


@app.get("/professor", response_class=HTMLResponse, include_in_schema=False)
def professor_dashboard_page(request: Request):
    """Serve the professor dashboard shell; its data is fetched via protected APIs."""
    return templates.TemplateResponse(
        request=request,
        name="professor_dashboard.html",
        context={"app_name": APP_NAME}
    )


@app.get("/student", response_class=HTMLResponse, include_in_schema=False)
def student_dashboard_page(request: Request):
    """Serve the student dashboard shell; its data is fetched via protected APIs."""
    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={"app_name": APP_NAME}
    )

# =====================================================
# REQUEST MODELS
# =====================================================

class StudentRegistration(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: int | None = Field(default=None, gt=0)


class CourseCreateRequest(BaseModel):
    course_code: str = Field(min_length=2, max_length=20)
    course_name: str = Field(min_length=2, max_length=150)
    description: str = ""
    semester: int = Field(gt=0)


class EnrollmentRequest(BaseModel):
    course_id: int = Field(gt=0)


class AssignmentCreateRequest(BaseModel):
    course_id: int
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    instructions: str | None = None
    maximum_marks: float = Field(..., gt=0)
    deadline: str
    status: str = "published"


class GradeSubmissionRequest(BaseModel):
    final_marks: float = Field(..., ge=0)
    professor_feedback: str = Field(..., min_length=1)
    suggested_marks: float | None = Field(default=None, ge=0)
    ai_feedback: str | None = None


class SimilarityReviewRequest(BaseModel):
    review_decision: str = Field(
        ...,
        pattern="^(confirmed|not_confirmed)$"
    )
    reason: str = Field(min_length=5, max_length=1000)


class ProjectCreateRequest(BaseModel):
    course_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None


class MilestoneCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    deadline: str | None = None


class MilestoneStatusUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(pending|in_progress|completed)$"
    )


# =====================================================
# AUTHENTICATION DEPENDENCIES
# =====================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    user = verify_access_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token."
        )

    return user


def require_professor_api(user=Depends(get_current_user)):

    if user["role"] != "professor":
        raise HTTPException(
            status_code=403,
            detail="Professor access required."
        )

    return user


def require_student_api(user=Depends(get_current_user)):

    if user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access required."
        )

    return user


# =====================================================
# AI ASSISTANT API
# =====================================================

@app.post("/assistant/conversations", status_code=201)
def create_assistant_conversation(user=Depends(get_current_user)):
    """Create a private conversation for the authenticated user."""
    conversation = ConversationService.create_conversation(
        user_id=user["id"]
    )
    return {
        "success": True,
        "conversation": conversation
    }


@app.get("/assistant/conversations")
def list_assistant_conversations(user=Depends(get_current_user)):
    """List only the authenticated user's conversations."""
    conversations = ConversationService.get_user_conversations(
        user["id"]
    )
    return {
        "success": True,
        "count": len(conversations),
        "conversations": conversations
    }


@app.get("/assistant/conversations/{conversation_id}/messages")
def get_assistant_conversation_messages(
    conversation_id: int,
    user=Depends(get_current_user)
):
    """Retrieve messages after ConversationService verifies ownership."""
    try:
        messages = ConversationService.get_conversation_history(
            user_id=user["id"],
            conversation_id=conversation_id
        )
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": messages
        }
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/assistant/chat")
def assistant_chat(
    request: AssistantChatRequest,
    user=Depends(get_current_user)
):
    """
    Send a message to AcademicFlow AI through the ToolUsingAgent.

    Authentication identity comes only from the verified access token.
    Academic context remains role-scoped through AssistantContextService.
    """

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty."
        )

    try:
        # 1. Create a new conversation or verify ownership of an existing one.
        if request.conversation_id is None:
            conversation = ConversationService.create_conversation(
                user_id=user["id"],
                title=message[:60]
            )
            conversation_id = conversation["conversation_id"]
        else:
            conversation_id = request.conversation_id
            ConversationService.get_conversation_history(
                user_id=user["id"],
                conversation_id=conversation_id
            )

        # 2. Persist the user's message.
        ConversationService.add_message(
            user_id=user["id"],
            conversation_id=conversation_id,
            sender="user",
            content=message
        )

        # 3. Build role-scoped academic context and conversation history.
        assistant_context = AssistantContextService.build_context(
            user_id=user["id"],
            role=user["role"],
            conversation_id=conversation_id
        )

        history = assistant_context.get("conversation_history", [])
        ollama_messages = []

        for item in history:
            sender = item.get("sender")
            content = item.get("content", "")

            if not content:
                continue

            if sender == "user":
                ollama_role = "user"
            elif sender in ("assistant", "agent"):
                ollama_role = "assistant"
            else:
                continue

            ollama_messages.append({
                "role": ollama_role,
                "content": content
            })

        # History is passed as chat messages, not duplicated in context.
        model_context = {
            key: value
            for key, value in assistant_context.items()
            if key != "conversation_history"
        }

        # 4. Let the agent choose between tool execution, conversation,
        #    or clarification.
        agent_execution = ToolUsingAgent().run({
            "request": message,
            "user_id": user["id"],
            "role": user["role"],
            "messages": ollama_messages,
            "context": model_context
        })

        if not agent_execution.get("success"):
            raise HTTPException(
                status_code=503,
                detail=agent_execution.get(
                    "error",
                    "Academic AI agent execution failed."
                )
            )

        # 5. Extract the response from the agent's output.
        agent_output = agent_execution.get("output") or {}

        answer = (
            agent_output.get("final_response")
            or agent_output.get("message")
            or "I couldn't generate a response."
        )

        # 6. Persist the assistant response.
        ConversationService.add_message(
            user_id=user["id"],
            conversation_id=conversation_id,
            sender="assistant",
            content=answer,
            agent_name="Academic Tool Using Agent"
        )

        # 7. Return the reply and useful execution metadata.
        return {
            "success": True,
            "conversation_id": conversation_id,
            "reply": answer,
            "role": user["role"],
            "agent": agent_execution.get("agent"),
            "execution_id": agent_execution.get("execution_id"),
            "database_execution_id": agent_execution.get(
                "database_execution_id"
            ),
            "execution_status": agent_output.get("status"),
            "selected_tool": agent_output.get("selected_tool"),
            "execution_trace": agent_execution.get(
                "execution_trace",
                []
            )
        }

    except HTTPException:
        raise

    except ValueError as error:
        # Preserve the existing not-found behavior for invalid conversation IDs.
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


# =====================================================
# GENERAL ENDPOINTS
# =====================================================

@app.get("/")
def home():

    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "message": "Welcome to the Academic Organizer API"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# =====================================================
# STUDENT REGISTRATION
# =====================================================

@app.post("/auth/register", status_code=201)
def register_student(data: StudentRegistration):

    try:

        user = create_user(
            full_name=data.full_name,
            email=data.email,
            password=data.password,
            role="student"
        )

        return {
            "message": "Student account created successfully.",
            "user": user
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =====================================================
# LOGIN
# =====================================================

@app.post("/auth/login")
def login(data: LoginRequest):

    user = authenticate_user(
        email=data.email,
        password=data.password
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(user)

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


# =====================================================
# CURRENT USER PROFILE
# =====================================================

@app.get("/auth/me")
def get_profile(user=Depends(get_current_user)):

    return {
        "message": "Authenticated successfully.",
        "user": user
    }


# =====================================================
# ROLE-BASED DASHBOARDS
# =====================================================

@app.get("/professor/dashboard")
def professor_dashboard(user=Depends(require_professor_api)):

    return {
        "message": "Professor dashboard access granted.",
        "user": user
    }


@app.get("/student/dashboard")
def student_dashboard(user=Depends(require_student_api)):

    return {
        "message": "Student dashboard access granted.",
        "user": user
    }


# =====================================================
# COURSE MANAGEMENT
# =====================================================

@app.post("/courses", status_code=201)
def create_course(
    data: CourseCreateRequest,
    user=Depends(require_professor_api)
):

    try:

        return CourseService.create_course(
            course_code=data.course_code,
            course_name=data.course_name,
            description=data.description,
            semester=data.semester,
            professor_id=user["id"]
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.get("/courses")
def list_courses(user=Depends(get_current_user)):

    if user["role"] == "professor":
        return CourseService.list_professor_courses(user["id"])

    # Students should only see courses they are enrolled in.
    return CourseService.list_student_courses(user["id"])


@app.get("/courses/my")
def my_courses(user=Depends(get_current_user)):

    if user["role"] == "professor":
        return CourseService.list_professor_courses(user["id"])

    return CourseService.list_student_courses(user["id"])


@app.get("/notes/my")
def get_my_notes(user=Depends(get_current_user)):
    """Return notes from courses the current user is allowed to access."""
    courses = (
        CourseService.list_professor_courses(user["id"])
        if user["role"] == "professor"
        else CourseService.list_student_courses(user["id"])
    )

    notes = []
    for course in courses:
        course_id = course.get("id", course.get("course_id"))
        if course_id is not None:
            notes.extend(NotesService.get_course_notes(course_id=course_id, user=user))

    return {"success": True, "count": len(notes), "notes": notes}


@app.get("/assignments/my")
def get_my_assignments(user=Depends(get_current_user)):
    """Return assignments from courses the current user is allowed to access."""
    courses = (
        CourseService.list_professor_courses(user["id"])
        if user["role"] == "professor"
        else CourseService.list_student_courses(user["id"])
    )

    assignments = []
    for course in courses:
        course_id = course.get("id", course.get("course_id"))
        if course_id is not None:
            assignments.extend(
                AssignmentService.list_course_assignments(course_id=course_id, user=user)
            )

    return {"success": True, "count": len(assignments), "assignments": assignments}


@app.post("/courses/enroll")
def enroll_in_course(
    data: EnrollmentRequest,
    user=Depends(require_student_api)
):

    try:

        return CourseService.enroll_student(
            course_id=data.course_id,
            student_id=user["id"]
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =====================================================
# NOTES MANAGEMENT
# =====================================================

ALLOWED_NOTE_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".md"
}

MAX_NOTE_SIZE = 20 * 1024 * 1024


async def save_note_upload(file: UploadFile):

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_NOTE_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )

    content = await file.read(MAX_NOTE_SIZE + 1)

    if len(content) > MAX_NOTE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="File size cannot exceed 20 MB."
        )

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{extension}"
    file_path = NOTES_DIR / stored_filename

    file_path.write_bytes(content)

    return file_path


@app.post("/courses/{course_id}/notes", status_code=201)
async def upload_course_notes(
    course_id: int,
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user=Depends(require_professor_api)
):

    file_path = await save_note_upload(file)

    try:

        return NotesService.upload_note(
            course_id=course_id,
            title=title,
            description=description,
            uploaded_by=user["id"],
            file_path=str(file_path)
        )

    except ValueError as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:

        file_path.unlink(missing_ok=True)
        raise


@app.get("/courses/{course_id}/notes")
def get_course_notes(
    course_id: int,
    user=Depends(get_current_user)
):

    try:

        return NotesService.get_course_notes(
            course_id=course_id,
            user=user
        )

    except ValueError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error)
        )


@app.get("/notes/{note_id}/download")
def download_note(
    note_id: int,
    user=Depends(get_current_user)
):

    try:

        note = NotesService.get_note_file(
            note_id=note_id,
            user=user
        )

        file_path = Path(note["file_path"])

        if not file_path.is_file():

            raise HTTPException(
                status_code=404,
                detail="Note file is unavailable."
            )

        return FileResponse(
            path=file_path,
            filename=f"{note['title']}{file_path.suffix}",
            media_type="application/octet-stream"
        )

    except ValueError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error)
        )


# -----------------------------------------------------
# UPDATE NOTES - CREATE A NEW VERSION
# -----------------------------------------------------

@app.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user=Depends(require_professor_api)
):

    file_path = await save_note_upload(file)

    try:

        result = NotesService.update_note(
            note_id=note_id,
            title=title,
            description=description,
            uploaded_by=user["id"],
            file_path=str(file_path)
        )

        return result

    except ValueError as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:

        file_path.unlink(missing_ok=True)
        raise


# -----------------------------------------------------
# GET NOTE VERSION HISTORY
# -----------------------------------------------------

@app.get("/notes/{note_id}/versions")
def get_note_versions(
    note_id: int,
    user=Depends(get_current_user)
):

    try:

        return NotesService.get_note_versions(
            note_id=note_id,
            user=user
        )

    except ValueError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error)
        )


# -----------------------------------------------------
# DOWNLOAD A PARTICULAR NOTE VERSION
# -----------------------------------------------------

@app.get("/notes/{note_id}/versions/{version_number}/download")
def download_note_version(
    note_id: int,
    version_number: int,
    user=Depends(get_current_user)
):

    try:

        note = NotesService.get_note_version_file(
            note_id=note_id,
            version_number=version_number,
            user=user
        )

        file_path = Path(note["file_path"])

        if not file_path.is_file():

            raise HTTPException(
                status_code=404,
                detail="Requested note version is unavailable."
            )

        return FileResponse(
            path=file_path,
            filename=f"{note['title']}_v{version_number}{file_path.suffix}",
            media_type="application/octet-stream"
        )

    except ValueError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error)
        )


# =====================================================
# ASSIGNMENT MANAGEMENT
# =====================================================

@app.post("/assignments")
def create_assignment(
    request: AssignmentCreateRequest,
    current_user=Depends(require_professor_api)
):

    try:

        assignment = AssignmentService.create_assignment(
            course_id=request.course_id,
            title=request.title,
            description=request.description,
            instructions=request.instructions,
            maximum_marks=request.maximum_marks,
            deadline=request.deadline,
            created_by=current_user["id"],
            status=request.status
        )

        return {
            "success": True,
            "message": "Assignment created successfully.",
            "assignment": assignment
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.get("/courses/{course_id}/assignments")
def get_course_assignments(
    course_id: int,
    current_user=Depends(get_current_user)
):

    try:

        assignments = AssignmentService.list_course_assignments(
            course_id=course_id,
            user=current_user
        )

        return {
            "success": True,
            "count": len(assignments),
            "assignments": assignments
        }

    except ValueError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error)
        )


# =====================================================
# ASSIGNMENT SUBMISSION MANAGEMENT
# =====================================================

ALLOWED_SUBMISSION_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".zip"
}

MAX_SUBMISSION_SIZE = 20 * 1024 * 1024


@app.post("/assignments/{assignment_id}/submit", status_code=201)
async def submit_assignment(
    assignment_id: int,
    file: UploadFile = File(...),
    user=Depends(require_student_api)
):

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_SUBMISSION_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Unsupported submission file type."
        )

    content = await file.read(MAX_SUBMISSION_SIZE + 1)

    if len(content) > MAX_SUBMISSION_SIZE:

        raise HTTPException(
            status_code=413,
            detail="Submission cannot exceed 20 MB."
        )

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{extension}"
    file_path = SUBMISSIONS_DIR / stored_filename

    try:

        file_path.write_bytes(content)

        result = SubmissionService.submit_assignment(
            assignment_id=assignment_id,
            student_id=user["id"],
            file_path=str(file_path)
        )

        return {
            "success": True,
            "message": "Submission processed successfully.",
            "submission": result
        }

    except ValueError as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:

        file_path.unlink(missing_ok=True)
        raise


@app.get("/assignments/{assignment_id}/submissions")
def get_assignment_submissions(
    assignment_id: int,
    user=Depends(require_professor_api)
):

    try:

        submissions = SubmissionService.get_assignment_submissions(
            assignment_id=assignment_id,
            professor_id=user["id"]
        )

        return {
            "success": True,
            "count": len(submissions),
            "submissions": submissions
        }

    except ValueError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error)
        )


# =====================================================
# SIMILARITY REVIEW MANAGEMENT
# =====================================================

@app.get("/submissions/{submission_id}/similarity-reports")
def get_similarity_reports(
    submission_id: int,
    user=Depends(require_professor_api)
):

    try:

        return SimilarityReviewService.get_submission_reports(
            submission_id=submission_id,
            professor_id=user["id"]
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.post("/similarity-reports/{report_id}/review")
def review_similarity_report(
    report_id: int,
    request: SimilarityReviewRequest,
    user=Depends(require_professor_api)
):

    try:

        return SimilarityReviewService.review_report(
            report_id=report_id,
            professor_id=user["id"],
            review_decision=request.review_decision,
            reason=request.reason
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =====================================================
# PROJECT AND MILESTONE MANAGEMENT
# =====================================================

@app.post("/projects", status_code=201)
def create_project(
    request: ProjectCreateRequest,
    user=Depends(require_professor_api)
):
    try:
        return ProjectService.create_project(
            professor_id=user["id"],
            course_id=request.course_id,
            student_id=request.student_id,
            title=request.title,
            description=request.description
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/projects/my")
def get_my_projects(user=Depends(get_current_user)):
    if user["role"] == "professor":
        return ProjectService.get_professor_projects(user["id"])

    if user["role"] == "student":
        return ProjectService.get_student_projects(user["id"])

    raise HTTPException(status_code=403, detail="Access denied.")


@app.post("/projects/{project_id}/milestones", status_code=201)
def create_project_milestone(
    project_id: int,
    request: MilestoneCreateRequest,
    user=Depends(require_professor_api)
):
    try:
        return ProjectService.create_milestone(
            professor_id=user["id"],
            project_id=project_id,
            title=request.title,
            description=request.description,
            deadline=request.deadline
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/projects/{project_id}/milestones")
def get_project_milestones(
    project_id: int,
    user=Depends(get_current_user)
):
    try:
        return ProjectService.get_project_milestones(
            project_id=project_id,
            user_id=user["id"],
            role=user["role"]
        )
    except ValueError as error:
        raise HTTPException(status_code=403, detail=str(error))


@app.patch("/milestones/{milestone_id}/status")
def update_milestone_status(
    milestone_id: int,
    request: MilestoneStatusUpdateRequest,
    user=Depends(require_student_api)
):
    try:
        return ProjectService.update_milestone(
            student_id=user["id"],
            milestone_id=milestone_id,
            status=request.status
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# =====================================================
# GRADING MANAGEMENT
# =====================================================

@app.post("/submissions/{submission_id}/grade")
def grade_submission(
    submission_id: int,
    request: GradeSubmissionRequest,
    user=Depends(require_professor_api)
):

    try:

        return GradingService.grade_submission(
            submission_id=submission_id,
            professor_id=user["id"],
            final_marks=request.final_marks,
            professor_feedback=request.professor_feedback,
            suggested_marks=request.suggested_marks,
            ai_feedback=request.ai_feedback
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.post("/grades/{grade_id}/approve")
def approve_grade(
    grade_id: int,
    user=Depends(require_professor_api)
):

    try:

        return GradingService.approve_grade(
            grade_id=grade_id,
            professor_id=user["id"]
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.post("/grades/{grade_id}/publish")
def publish_grade(
    grade_id: int,
    user=Depends(require_professor_api)
):

    try:

        return GradingService.publish_grade(
            grade_id=grade_id,
            professor_id=user["id"]
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.get("/students/me/grades")
def get_my_grades(
    user=Depends(require_student_api)
):

    grades = GradingService.get_student_grades(user["id"])

    return {
        "success": True,
        "count": len(grades),
        "grades": grades
    }