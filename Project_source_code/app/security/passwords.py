import hashlib
import secrets
import hmac


# =====================================================
# PASSWORD CONFIGURATION
# =====================================================

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 310000
SALT_LENGTH = 16


# =====================================================
# PASSWORD HASHING
# =====================================================

def hash_password(password: str) -> str:
    """
    Securely hashes a password using PBKDF2.
    """

    if not isinstance(password, str) or len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    salt = secrets.token_bytes(SALT_LENGTH)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    return (
        f"{ALGORITHM}$"
        f"{ITERATIONS}$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


# =====================================================
# PASSWORD VERIFICATION
# =====================================================

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a password against its stored hash.
    """

    try:
        algorithm, iterations, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != ALGORITHM:
            return False

        iterations = int(iterations)

        if not 100000 <= iterations <= 1000000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        if len(salt) != SALT_LENGTH or len(expected_hash) != 32:
            return False

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (ValueError, TypeError, AttributeError):
        return False