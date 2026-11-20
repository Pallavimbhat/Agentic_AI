import sqlite3
import jwt

from datetime import datetime, timedelta, timezone

from app.database.connection import get_connection
from app.security.passwords import hash_password, verify_password
from app.core.config import SECRET_KEY, ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = 60

VALID_ROLES = {"professor", "student"}


def create_user(full_name, email, password, role):
    """Create a new professor or student account."""

    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        raise ValueError("Full name is required.")

    if "@" not in email:
        raise ValueError("Enter a valid email address.")

    if role not in VALID_ROLES:
        raise ValueError("Invalid user role.")

    password_hash = hash_password(password)

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, email, password_hash, role)
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "full_name": full_name,
            "email": email,
            "role": role
        }

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError("An account with this email already exists.")

    finally:
        connection.close()


def authenticate_user(email, password):
    """Verify login credentials."""

    email = email.strip().lower()

    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, full_name, email, password_hash, role, is_active
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if user is None:
            return None

        if not user["is_active"]:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"]
        }

    finally:
        connection.close()


def create_access_token(user):
    """Generate a signed JWT access token."""

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def verify_access_token(token):
    """Verify a JWT and confirm that the user is still active."""

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "email", "role", "exp"]}
        )

        user_id = int(payload["sub"])

        if payload["role"] not in VALID_ROLES:
            return None

        connection = get_connection()

        try:
            user = connection.execute(
                """
                SELECT id, full_name, email, role, is_active
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            ).fetchone()

            if user is None or not user["is_active"]:
                return None

            if user["role"] != payload["role"]:
                return None

            if user["email"] != payload["email"]:
                return None

            return {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }

        finally:
            connection.close()

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        return None


def check_permission(user, allowed_roles):
    """Check whether a user has permission to perform an operation."""

    if user is None:
        raise PermissionError("Authentication required.")

    if user["role"] not in allowed_roles:
        raise PermissionError("You do not have permission to perform this action.")

    return True


def require_professor(user):
    """Allow access only to professors."""

    return check_permission(user, {"professor"})


def require_student(user):
    """Allow access only to students."""

    return check_permission(user, {"student"})