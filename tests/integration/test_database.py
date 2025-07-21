"""Integration tests for database operations."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from src.entities.account import Account
from src.entities.status import AccountStatus


class TestAccountDatabaseOperations:
    """Test cases for Account database operations."""

    def _create_account(self, session, **kwargs):
        """Helper method to create and save an account."""
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        defaults = {
            "name": "Test User",
            "email": f"test-{unique_id}@example.com",
            "password": "hashed_password",  # pragma: allowlist secret
            "password_salt": "random_salt",  # pragma: allowlist secret
            "status": AccountStatus.ACTIVE,
            "is_admin": False,
        }
        defaults.update(kwargs)

        account = Account(**defaults)
        session.add(account)
        session.commit()
        session.refresh(account)
        return account

    def test_create_account(self, test_db_session):
        """Test creating a new account in the database."""
        account = Account(
            name="Test User",
            email="test@example.com",
            password="hashed_password",  # pragma: allowlist secret
            password_salt="random_salt",  # pragma: allowlist secret
            status=AccountStatus.ACTIVE,
            is_admin=False,
        )

        test_db_session.add(account)
        test_db_session.commit()
        test_db_session.refresh(account)

        assert account is not None
        assert account.id is not None
        assert account.name == "Test User"
        assert account.email == "test@example.com"
        assert account.status == AccountStatus.ACTIVE
        assert account.is_admin is False
        assert account.created_at is not None

    def test_get_account_by_email(self, test_db_session):
        """Test retrieving account by email."""
        # Create account first
        created_account = self._create_account(test_db_session, email="unique@example.com")

        # Retrieve by email
        retrieved_account = Account.get_by_email(test_db_session, "unique@example.com")

        assert retrieved_account is not None
        assert retrieved_account.id == created_account.id
        assert retrieved_account.email == "unique@example.com"

    def test_get_account_by_email_case_insensitive(self, test_db_session):
        """Test retrieving account by email is case insensitive."""
        # Create account with lowercase email
        self._create_account(test_db_session, email="casetest@example.com")
        test_db_session.commit()

        # Retrieve with different case
        retrieved_account = Account.get_by_email(test_db_session, "CASETEST@EXAMPLE.COM")

        assert retrieved_account is not None
        assert retrieved_account.email == "casetest@example.com"

    def test_get_account_by_email_not_found(self, test_db_session):
        """Test retrieving non-existent account by email."""
        retrieved_account = Account.get_by_email(test_db_session, "nonexistent@example.com")

        assert retrieved_account is None

    def test_get_account_by_id(self, test_db_session):
        """Test retrieving account by ID."""
        # Create account first
        created_account = self._create_account(test_db_session)

        # Retrieve by ID
        retrieved_account = Account.get_by_id(test_db_session, created_account.id)

        assert retrieved_account is not None
        assert retrieved_account.id == created_account.id
        assert retrieved_account.email == created_account.email

    def test_get_account_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent account by ID."""
        non_existent_id = uuid4()
        retrieved_account = Account.get_by_id(test_db_session, non_existent_id)

        assert retrieved_account is None

    def test_update_account(self, test_db_session):
        """Test updating account information."""
        # Create account first
        account = self._create_account(test_db_session)

        # Update account
        account.name = "Updated User"
        account.timezone = "UTC"
        account.last_login_at = datetime.now(UTC)

        test_db_session.commit()

        # Retrieve and verify update
        updated_account = Account.get_by_id(test_db_session, account.id)
        assert updated_account.name == "Updated User"
        assert updated_account.timezone == "UTC"
        assert updated_account.last_login_at is not None

    def test_update_account_status(self, test_db_session):
        """Test updating account status."""
        # Create account first
        account = self._create_account(test_db_session, status=AccountStatus.PENDING)

        # Update status
        account.status = AccountStatus.ACTIVE
        test_db_session.commit()

        # Verify update
        updated_account = Account.get_by_id(test_db_session, account.id)
        assert updated_account.status == AccountStatus.ACTIVE

    def test_delete_account(self, test_db_session):
        """Test deleting an account."""
        # Create account first
        account = self._create_account(test_db_session)
        account_id = account.id

        # Delete account
        test_db_session.delete(account)
        test_db_session.commit()

        # Verify deletion
        deleted_account = Account.get_by_id(test_db_session, account_id)
        assert deleted_account is None

    def test_unique_email_constraint(self, test_db_session):
        """Test that email uniqueness is enforced."""
        # Create first account
        self._create_account(test_db_session, name="User One", email="duplicate@example.com")

        # Try to create second account with same email
        duplicate_account = Account(
            name="User Two",
            email="duplicate@example.com",
            password="hashed_password2",  # pragma: allowlist secret
            password_salt="salt2",  # pragma: allowlist secret
            status=AccountStatus.ACTIVE,  # pragma: allowlist secret
            is_admin=False,
        )
        test_db_session.add(duplicate_account)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_account_timestamps(self, test_db_session):
        """Test that account timestamps are set correctly."""
        from datetime import datetime

        before_creation = datetime.now(UTC)

        account = self._create_account(test_db_session)

        after_creation = datetime.now(UTC)

        # Check created_at timestamp
        assert account.created_at is not None

        # Convert to timezone-aware if needed
        created_at = account.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        assert before_creation <= created_at <= after_creation

        # Check updated_at timestamp (if exists)
        if hasattr(account, "updated_at"):
            assert account.updated_at is not None
            updated_at = account.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=UTC)
            assert before_creation <= updated_at <= after_creation

    def test_account_default_values(self, test_db_session):
        """Test that account default values are set correctly."""
        import uuid

        unique_email = f"defaults-{str(uuid.uuid4())[:8]}@example.com"

        account = Account(name="Test User", email=unique_email, password="hashed_password", password_salt="random_salt")

        test_db_session.add(account)
        test_db_session.commit()
        test_db_session.refresh(account)

        # Check default values
        assert account.status == AccountStatus.PENDING  # Default status is PENDING
        assert account.is_admin is False
        assert account.timezone is None
        assert account.avatar is None
        assert account.last_login_at is None
        assert account.initialized_at is None

    def test_list_accounts(self, test_db_session):
        """Test listing multiple accounts."""
        # Create multiple accounts
        accounts_data = [
            {
                "name": "User One",
                "email": "user1@example.com",  # pragma: allowlist secret
                "password": "password1",  # pragma: allowlist secret
                "password_salt": "salt1",  # pragma: allowlist secret
                "status": AccountStatus.ACTIVE,
                "is_admin": False,
            },
            {
                "name": "User Two",
                "email": "user2@example.com",  # pragma: allowlist secret
                "password": "password2",  # pragma: allowlist secret
                "password_salt": "salt2",  # pragma: allowlist secret
                "status": AccountStatus.PENDING,
                "is_admin": True,
            },
            {
                "name": "User Three",
                "email": "user3@example.com",  # pragma: allowlist secret
                "password": "password3",  # pragma: allowlist secret
                "password_salt": "salt3",  # pragma: allowlist secret
                "status": AccountStatus.BANNED,
                "is_admin": False,
            },
        ]

        created_accounts = []
        for data in accounts_data:
            account = Account(**data)
            test_db_session.add(account)
            created_accounts.append(account)

        test_db_session.commit()
        for account in created_accounts:
            test_db_session.refresh(account)

        # List all accounts
        statement = select(Account)
        all_accounts = test_db_session.exec(statement).all()

        assert len(all_accounts) >= 3

        # Check that our created accounts are in the list
        created_emails = {acc.email for acc in created_accounts}
        retrieved_emails = {acc.email for acc in all_accounts}

        assert created_emails.issubset(retrieved_emails)

    def test_filter_accounts_by_status(self, test_db_session):
        """Test filtering accounts by status."""
        # Create accounts with different statuses
        accounts = [
            Account(
                name="Active User",
                email="active@example.com",  # pragma: allowlist secret
                password="pass",  # pragma: allowlist secret
                password_salt="salt",  # pragma: allowlist secret
                status=AccountStatus.ACTIVE,
            ),
            Account(
                name="Pending User",
                email="pending@example.com",
                password="pass",  # pragma: allowlist secret
                password_salt="salt",  # pragma: allowlist secret
                status=AccountStatus.PENDING,
            ),
            Account(
                name="Banned User",
                email="banned@example.com",
                password="pass",  # pragma: allowlist secret
                password_salt="salt",  # pragma: allowlist secret
                status=AccountStatus.BANNED,
            ),
        ]

        for account in accounts:
            test_db_session.add(account)
        test_db_session.commit()

        # Filter by status
        active_statement = select(Account).where(Account.status == AccountStatus.ACTIVE)
        active_accounts = test_db_session.exec(active_statement).all()

        pending_statement = select(Account).where(Account.status == AccountStatus.PENDING)
        pending_accounts = test_db_session.exec(pending_statement).all()

        banned_statement = select(Account).where(Account.status == AccountStatus.BANNED)
        banned_accounts = test_db_session.exec(banned_statement).all()

        # Verify filtering
        assert len(active_accounts) >= 1
        assert len(pending_accounts) >= 1
        assert len(banned_accounts) >= 1

        assert all(acc.status == AccountStatus.ACTIVE for acc in active_accounts)
        assert all(acc.status == AccountStatus.PENDING for acc in pending_accounts)
        assert all(acc.status == AccountStatus.BANNED for acc in banned_accounts)
