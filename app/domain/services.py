from datetime import datetime
from models import ApprovalRequest


def approve_step(
    approval_request: ApprovalRequest,
    step_id: str,
    actor_id: str,
    decided_at: datetime,
) -> ApprovalRequest:
    ...


def reject_step(
    approval_request: ApprovalRequest,
    step_id: str,
    actor_id: str,
    comment: str,
    decided_at: datetime,
) -> ApprovalRequest:
    ...

