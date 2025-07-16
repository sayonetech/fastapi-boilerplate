#!/usr/bin/env python3
"""Debug script to test password verification."""

from sqlmodel import Session, create_engine, select

from src.configs import madcrow_config
from src.entities.account import Account
from src.libs.password import hash_password, verify_password


def debug_password_verification():
    """Debug password verification for a specific user."""
    engine = create_engine(
        madcrow_config.sqlalchemy_database_uri,  # type: ignore
        **madcrow_config.sqlalchemy_engine_options,  # type: ignore
    )

    with Session(engine) as session:
        # Get the user
        statement = select(Account).where(Account.email == "renjith@sayonetech.com")
        user = session.exec(statement).first()

        if not user:
            print("❌ User not found!")
            return

        print(f"✅ Found user: {user.name} ({user.email})")
        print(f"   Status: {user.status.value}")
        print(f"   Password Set: {user.is_password_set}")
        print(f"   Can Login: {user.can_login}")
        print(f"   Password Hash: {user.password[:20]}..." if user.password else "None")
        print(f"   Salt: {user.password_salt[:20]}..." if user.password_salt else "None")

        # Test password verification
        test_password = input("\nEnter password to test: ")

        if not user.password or not user.password_salt:
            print("❌ User has no password or salt set!")
            return

        print("\nTesting password verification...")
        print(f"   Test password: '{test_password}'")
        print(f"   Stored hash: {user.password}")
        print(f"   Stored salt: {user.password_salt}")

        # Manually compute hash
        computed_hash = hash_password(test_password, user.password_salt)
        print(f"   Computed hash: {computed_hash}")
        print(f"   Hashes match: {computed_hash == user.password}")

        # Use verify_password function
        is_valid = verify_password(test_password, user.password, user.password_salt)
        print(f"   verify_password result: {is_valid}")

        if is_valid:
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")


if __name__ == "__main__":
    debug_password_verification()
