"""Domain models for approval workflows."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class RequestStatus(StrEnum):
    """Workflow-level request statuses."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StepStatus(StrEnum):
    """Approval step statuses."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalStep(BaseModel):
    """A single sequential approval step."""

    step_id: str
    order: int
    approver_id: str
    status: StepStatus = StepStatus.PENDING
    decided_at: datetime | None = None
    comment: str | None = None


class ApprovalRequest(BaseModel):
    """An approval workflow aggregate."""

    request_id: str
    requester_id: str
    title: str
    payload: dict[str, Any]
    status: RequestStatus = RequestStatus.PENDING
    current_step_index: int = 0
    steps: list[ApprovalStep]
    version: int = 1
    created_at: datetime
    updated_at: datetime
