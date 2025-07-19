"""Unit tests for validation utilities."""

import pytest

from src.utils.validation import (
    ValidationUtils,
    create_pydantic_validators,
    validate_password_strength,
)


@pytest.mark.unit
class TestValidationUtils:
    """Test ValidationUtils class."""

    @pytest.fixture
    def validator(self):
        """Create ValidationUtils instance."""
        return ValidationUtils()

    def test_validate_email_valid_emails(self, validator):
        """Test email validation with valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "firstname.lastname@company.com",
            "user123@test-domain.com",
            "a@b.co",
            "test.email.with+symbol@example.com",
        ]

        for email in valid_emails:
            # Should not raise exception for valid emails
            result = validator.validate_email(email)
            assert result == email, f"Email '{email}' should be valid"

    def test_validate_email_invalid_emails(self, validator):
        """Test email validation with invalid email addresses."""
        from src.exceptions.validation import EmailValidationError

        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "",
            "user name@example.com",  # Space in email
        ]

        for email in invalid_emails:
            with pytest.raises(EmailValidationError):
                validator.validate_email(email)

    def test_validate_password_strength(self, validator):
        """Test password strength validation."""
        # Strong password should pass
        strong_password = "StrongPass123!"  # pragma: allowlist secret
        result = validator.validate_password(strong_password)
        assert result == strong_password

        # Weak password should raise exception
        from src.exceptions.validation import PasswordValidationError

        weak_password = "weak"  # pragma: allowlist secret
        with pytest.raises(PasswordValidationError):
            validator.validate_password(weak_password)

    def test_validate_password_strength_function(self):
        """Test standalone password strength validation function."""
        # Strong password should return (True, "")
        strong_password = "StrongPass123!"  # pragma: allowlist secret
        is_valid, error_msg = validate_password_strength(strong_password)
        assert is_valid is True
        assert error_msg == ""

        # Weak password should return (False, error_message)
        weak_password = "weak"  # pragma: allowlist secret
        is_valid, error_msg = validate_password_strength(weak_password)
        assert is_valid is False
        assert error_msg != ""

    def test_create_pydantic_validators(self):
        """Test Pydantic validators creation."""
        validators = create_pydantic_validators()
        assert isinstance(validators, dict)
        assert len(validators) > 0
