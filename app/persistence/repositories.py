"""Repository interfaces."""

from typing import Protocol

from app.domain.models import ApprovalRequest, RequestStatus


class ApprovalRequestRepository(Protocol):
    """Repository interface for approval requests."""

    def save(
        self,
        approval_request: ApprovalRequest,
        event: dict[str, object] | None = None,
    ) -> None:
        """Persist a new approval request and its active pending approval."""

    def get(self, request_id: str) -> ApprovalRequest | None:
        """Return an approval request by ID if it exists."""

    def update(
        self,
        approval_request: ApprovalRequest,
        expected_version: int,
        event: dict[str, object] | None = None,
    ) -> None:
        """Persist an updated approval request using optimistic locking."""

    def list_by_requester(
        self,
        requester_id: str,
        status: RequestStatus | None = None,
    ) -> list[ApprovalRequest]:
        """Return requests created by a requester."""

    def list_pending_for_approver(self, approver_id: str) -> list[ApprovalRequest]:
        """Return requests currently waiting for an approver."""
