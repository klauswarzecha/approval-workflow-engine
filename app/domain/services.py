from datetime import datetime

from .errors import (
    InvalidWorkflowState,
    RejectCommentRequired,
    StepNotFound,
    UnauthorizedWorkflowAction,
)
from .models import ApprovalRequest, RequestStatus, StepStatus


def _validate_current_step(
    approval_request: ApprovalRequest,
    step_id: str,
    actor_id: str,
) -> int:
    """Validate workflow request and return the current step index."""
    if approval_request.status != RequestStatus.PENDING:
        raise InvalidWorkflowState("Approval request is not pending.")

    if approval_request.current_step_index < 0 or approval_request.current_step_index >= len(
        approval_request.steps
    ):
        raise StepNotFound("Current approval step was not found.")

    current_step = approval_request.steps[approval_request.current_step_index]
    if current_step.step_id != step_id:
        raise StepNotFound("Only the current step can be acted on.")

    if current_step.status != StepStatus.PENDING:
        raise InvalidWorkflowState("Current approval step is not pending.")

    if actor_id != current_step.approver_id:
        raise UnauthorizedWorkflowAction("Actor is not assigned to approve this step.")

    return approval_request.current_step_index


def approve_step(
    approval_request: ApprovalRequest,
    step_id: str,
    actor_id: str,
    decided_at: datetime,
) -> ApprovalRequest:
    """Approve the current workflow step and advance the request if applicable."""
    current_step_index = _validate_current_step(approval_request, step_id, actor_id)

    updated_request = approval_request.model_copy(deep=True)
    current_step = updated_request.steps[current_step_index]
    current_step.status = StepStatus.APPROVED
    current_step.decided_at = decided_at
    updated_request.updated_at = decided_at
    updated_request.version += 1

    if current_step_index == len(updated_request.steps) - 1:
        updated_request.status = RequestStatus.APPROVED
    else:
        updated_request.current_step_index += 1

    return updated_request


def reject_step(
    approval_request: ApprovalRequest,
    step_id: str,
    actor_id: str,
    comment: str,
    decided_at: datetime,
) -> ApprovalRequest:
    """Reject the current workflow step and mark the request as rejected."""
    if not comment or not comment.strip():
        raise RejectCommentRequired("Rejection requires a non-empty comment.")

    current_step_index = _validate_current_step(approval_request, step_id, actor_id)

    updated_request = approval_request.model_copy(deep=True)
    current_step = updated_request.steps[current_step_index]
    current_step.status = StepStatus.REJECTED
    current_step.comment = comment
    current_step.decided_at = decided_at
    updated_request.status = RequestStatus.REJECTED
    updated_request.updated_at = decided_at
    updated_request.version += 1

    return updated_request
