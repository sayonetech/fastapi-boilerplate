"""Unit tests for password library."""

import pytest

from src.libs.password import (
    create_password_hash,
    generate_salt,
    generate_secure_password,
    hash_password,
    is_password_compromised,
    validate_password_strength,
    verify_password,
)


@pytest.mark.unit
class TestPasswordLibrary:
    """Test password library functionality."""

    def test_generate_salt(self):
        """Test salt generation."""
        salt1 = generate_salt()
        salt2 = generate_salt()

        assert salt1 is not None
        assert salt2 is not None
        assert isinstance(salt1, str)
        assert isinstance(salt2, str)
        assert salt1 != salt2  # Should generate different salts
        assert len(salt1) > 20  # Base64 encoded salt should be reasonably long

    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "test_password_123"  # pragma: allowlist secret
        salt = generate_salt()

        hashed = hash_password(password, salt)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password  # Should be hashed, not plain text
        assert len(hashed) == 64  # SHA-256 hex digest is 64 characters

    def test_hash_password_different_results(self):
        """Test that same password produces different hashes with different salts."""
        password = "test_password_123"  # pragma: allowlist secret
        salt1 = generate_salt()
        salt2 = generate_salt()

        hash1 = hash_password(password, salt1)
        hash2 = hash_password(password, salt2)

        assert hash1 != hash2  # Different salts should produce different hashes

    def test_hash_password_same_salt_same_result(self):
        """Test that same password and salt produce same hash."""
        password = "test_password_123"  # pragma: allowlist secret
        salt = generate_salt()

        hash1 = hash_password(password, salt)
        hash2 = hash_password(password, salt)

        assert hash1 == hash2  # Same salt should produce same hash

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"  # pragma: allowlist secret
        salt = generate_salt()
        hashed = hash_password(password, salt)

        result = verify_password(password, hashed, salt)

        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"  # pragma: allowlist secret
        wrong_password = "wrong_password"  # pragma: allowlist secret
        salt = generate_salt()
        hashed = hash_password(password, salt)

        result = verify_password(wrong_password, hashed, salt)

        assert result is False

    def test_create_password_hash(self):
        """Test password hash creation with salt."""
        password = "test_password_123"  # pragma: allowlist secret

        hashed, salt = create_password_hash(password)

        assert hashed is not None
        assert salt is not None
        assert isinstance(hashed, str)
        assert isinstance(salt, str)
        assert len(hashed) == 64  # SHA-256 hex digest

        # Verify the hash works
        assert verify_password(password, hashed, salt) is True

    def test_validate_password_strength_strong_password(self):
        """Test password strength validation with strong password."""
        strong_password = "StrongPass123!"  # pragma: allowlist secret

        is_valid, message = validate_password_strength(strong_password)

        assert is_valid is True
        assert message == ""

    def test_validate_password_strength_weak_passwords(self):
        """Test password strength validation with weak passwords."""
        weak_cases = [
            ("short", "Password must be at least 8 characters long"),
            ("12345678", "Password must contain at least one letter"),  # Only digits
            ("abcdefgh", "Password must contain at least one digit"),  # Only letters
            ("", "Password is required"),  # Empty password
        ]

        for password, expected_message in weak_cases:
            is_valid, message = validate_password_strength(password)
            assert is_valid is False
            assert expected_message in message

    def test_is_password_compromised(self):
        """Test password compromise checking."""
        # Test with known weak passwords
        weak_passwords = ["password", "123456", "admin", "qwerty"]

        for password in weak_passwords:
            result = is_password_compromised(password)
            assert result is True, f"Password '{password}' should be flagged as compromised"

        # Test with strong password
        strong_password = "MyVerySecureP@ssw0rd2024!"  # pragma: allowlist secret
        result = is_password_compromised(strong_password)
        assert result is False

    def test_generate_secure_password(self):
        """Test secure password generation."""
        # Test default length
        password1 = generate_secure_password()
        assert len(password1) == 16
        assert isinstance(password1, str)

        # Test custom length
        password2 = generate_secure_password(24)
        assert len(password2) == 24

        # Test that generated passwords are different
        password3 = generate_secure_password()
        assert password1 != password3

    def test_password_hashing_consistency(self):
        """Test that password hashing and verification work together consistently."""
        test_passwords = [
            "simple",
            "Complex@Password123",
            "unicode_测试_🔒",
            "a" * 100,  # Long password
            "!@#$%^&*()",  # Special characters only
        ]

        for password in test_passwords:
            hashed, salt = create_password_hash(password)

            # Correct password should verify
            assert verify_password(password, hashed, salt) is True

            # Wrong password should not verify
            assert verify_password(password + "wrong", hashed, salt) is False

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test empty password
        is_valid, message = validate_password_strength("")
        assert is_valid is False
        assert "Password is required" in message

        # Test very long password (over 128 chars)
        long_password = "a1" * 100  # 200 characters  # pragma: allowlist secret
        is_valid, message = validate_password_strength(long_password)
        assert is_valid is False
        assert "less than 128 characters" in message

        # Test unicode in password
        unicode_password = "Pássw0rd123"  # pragma: allowlist secret
        is_valid, message = validate_password_strength(unicode_password)
        assert is_valid is True
