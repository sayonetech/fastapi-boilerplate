# src/entities/status.py

from enum import StrEnum


class AccountStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    BANNED = "banned"
    CLOSED = "closed"


class WorkspaceRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


class WorkspaceStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    TRIAL = "trial"
