from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel
from typing import Any


class RequestStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StepStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalStep(BaseModel):
    step_id: str
    order: int
    approver_id: str
    status: StepStatus = StepStatus.PENDING
    decided_at: datetime | None = None
    comment: str | None = None


class ApprovalRequest(BaseModel):
    request_od: str
    requester_id: str
    title: str
    payload: dict[str, Any]
    status: RequestStatus = RequestStatus.PENDING
    current_step_index: int = 0
    steps: list[ApprovalStep]
    version: int = 1
    created_at: datetime
    updated_at: datetime
