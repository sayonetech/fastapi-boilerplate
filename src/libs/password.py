"""Password utilities for secure password handling with salt."""

import base64
import hashlib
import secrets


def generate_salt() -> str:
    """
    Generate a random salt for password hashing.

    Returns:
        str: Base64-encoded salt
    """
    # Generate 32 bytes of random data
    salt_bytes = secrets.token_bytes(32)
    # Encode to base64 string
    return base64.b64encode(salt_bytes).decode("utf-8")


def hash_password(password: str, salt: str) -> str:
    """
    Hash password with salt using SHA-256.

    This provides secure password hashing using SHA-256 with salt.

    Args:
        password: Plain text password
        salt: Base64-encoded salt

    Returns:
        str: Hashed password
    """
    # Decode salt from base64
    salt_bytes = base64.b64decode(salt.encode("utf-8"))

    # Combine password and salt
    password_bytes = password.encode("utf-8")
    combined = password_bytes + salt_bytes

    # Hash with SHA-256
    hash_obj = hashlib.sha256(combined)

    # Return hex digest
    return hash_obj.hexdigest()


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify password against hashed password and salt.

    Args:
        password: Plain text password to verify
        hashed_password: Stored hashed password
        salt: Base64-encoded salt

    Returns:
        bool: True if password is valid, False otherwise
    """
    try:
        # Hash the provided password with the same salt
        computed_hash = hash_password(password, salt)

        # Compare with stored hash
        return computed_hash == hashed_password

    except Exception:
        # If any error occurs during verification, return False
        return False


def create_password_hash(password: str) -> tuple[str, str]:
    """
    Create password hash and salt for new password.

    Args:
        password: Plain text password

    Returns:
        Tuple[str, str]: (hashed_password, salt)
    """
    # Generate new salt
    salt = generate_salt()

    # Hash password with salt
    hashed_password = hash_password(password, salt)

    return hashed_password, salt


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength according to security requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters long"

    # Check for at least one letter
    has_letter = any(c.isalpha() for c in password)
    if not has_letter:
        return False, "Password must contain at least one letter"

    # Check for at least one digit
    has_digit = any(c.isdigit() for c in password)
    if not has_digit:
        return False, "Password must contain at least one digit"

    return True, ""


def is_password_compromised(password: str) -> bool:
    """
    Check if password is in common password lists (basic implementation).

    In production, this could check against known compromised password databases.

    Args:
        password: Password to check

    Returns:
        bool: True if password is compromised/weak
    """
    # Common weak passwords
    weak_passwords = {
        "password",
        "123456",
        "123456789",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "1234567890",
        "password1",
        "123123",
        "admin123",
    }

    return password.lower() in weak_passwords


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure random password.

    Args:
        length: Length of password to generate (default: 16)

    Returns:
        str: Generated secure password
    """
    if length < 8:
        length = 8
    if length > 128:
        length = 128

    # Character sets
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Ensure at least one character from each set
    password = [secrets.choice(lowercase), secrets.choice(uppercase), secrets.choice(digits), secrets.choice(special)]

    # Fill remaining length with random characters from all sets
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Shuffle the password
    secrets.SystemRandom().shuffle(password)

    return "".join(password)
