import os
from pathlib import Path

from dotenv import load_dotenv


# =====================================================
# PROJECT PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables from project root
load_dotenv(BASE_DIR / ".env")


# =====================================================
# APPLICATION SETTINGS
# =====================================================

APP_NAME = "Course Project, Notes & Assignment Organizer"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"


# =====================================================
# DATABASE
# =====================================================

DATABASE_PATH = BASE_DIR / "data" / "course_organizer.db"


# =====================================================
# STORAGE
# =====================================================

STORAGE_DIR = BASE_DIR / "storage"

NOTES_DIR = STORAGE_DIR / "notes"
ASSIGNMENTS_DIR = STORAGE_DIR / "assignments"
SUBMISSIONS_DIR = STORAGE_DIR / "submissions"
PROJECTS_DIR = STORAGE_DIR / "projects"
RESEARCH_DIR = STORAGE_DIR / "research"


# =====================================================
# LOGGING
# =====================================================

LOG_DIR = BASE_DIR / "logs"


# =====================================================
# AUTHENTICATION
# =====================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "A secure SECRET_KEY must be configured in the .env file."
    )

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


# =====================================================
# SIMILARITY POLICY
# =====================================================

SIMILARITY_ACCEPT_THRESHOLD = 50.0
SIMILARITY_REVIEW_THRESHOLD = 75.0
SIMILARITY_REJECTION_THRESHOLD = 90.0