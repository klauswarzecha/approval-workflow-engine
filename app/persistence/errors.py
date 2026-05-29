"""Persistence-layer exceptions."""


class PersistenceError(Exception):
    """Base exception for persistence errors."""


class ApprovalRequestNotFound(PersistenceError):
    """Raised when an approval request cannot be found."""


class OptimisticLockConflict(PersistenceError):
    """Raised when an update loses an optimistic locking race."""
