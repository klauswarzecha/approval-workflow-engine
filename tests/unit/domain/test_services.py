from datetime import datetime

import pytest

from app.domain.errors import (
    RejectCommentRequired,
    StepNotFound,
    UnauthorizedWorkflowAction,
)
from app.domain.models import ApprovalRequest, ApprovalStep, RequestStatus, StepStatus
from app.domain.services import approve_step, reject_step


def make_request(steps, current_step_index=0):
    now = datetime(2026, 5, 28, 12, 0, 0)
    return ApprovalRequest(
        request_od="req-1",
        requester_id="user-1",
        title="Approve expense",
        payload={"amount": 100},
        status=RequestStatus.PENDING,
        current_step_index=current_step_index,
        steps=steps,
        version=1,
        created_at=now,
        updated_at=now,
    )


def test_approve_first_step_moves_to_next_step():
    request = make_request(
        [
            ApprovalStep(step_id="step-1", order=1, approver_id=1),
            ApprovalStep(step_id="step-2", order=2, approver_id=2),
        ]
    )
    decided_at = datetime(2026, 5, 28, 12, 30, 0)

    result = approve_step(request, "step-1", "1", decided_at)

    assert result.current_step_index == 1
    assert result.status == RequestStatus.PENDING
    assert result.steps[0].status == StepStatus.APPROVED
    assert result.steps[0].decided_at == decided_at
    assert result.version == 2
    assert result.updated_at == decided_at
    assert request.current_step_index == 0
    assert request.steps[0].status == StepStatus.PENDING


def test_approve_final_step_approves_whole_request():
    request = make_request(
        [ApprovalStep(step_id="step-1", order=1, approver_id=1)]
    )
    decided_at = datetime(2026, 5, 28, 13, 0, 0)

    result = approve_step(request, "step-1", "1", decided_at)

    assert result.status == RequestStatus.APPROVED
    assert result.current_step_index == 0
    assert result.steps[0].status == StepStatus.APPROVED
    assert result.version == 2
    assert request.status == RequestStatus.PENDING


def test_wrong_approver_cannot_approve():
    request = make_request([ApprovalStep(step_id="step-1", order=1, approver_id=1)])

    with pytest.raises(UnauthorizedWorkflowAction):
        approve_step(request, "step-1", "2", datetime(2026, 5, 28, 13, 0, 0))


def test_approving_non_current_step_fails():
    request = make_request(
        [
            ApprovalStep(step_id="step-1", order=1, approver_id=1),
            ApprovalStep(step_id="step-2", order=2, approver_id=2),
        ]
    )

    with pytest.raises(StepNotFound):
        approve_step(request, "step-2", "2", datetime(2026, 5, 28, 13, 0, 0))


def test_rejecting_requires_non_empty_comment():
    request = make_request([ApprovalStep(step_id="step-1", order=1, approver_id=1)])

    with pytest.raises(RejectCommentRequired):
        reject_step(request, "step-1", "1", "   ", datetime(2026, 5, 28, 13, 0, 0))


def test_rejection_marks_request_as_rejected():
    request = make_request([ApprovalStep(step_id="step-1", order=1, approver_id=1)])
    decided_at = datetime(2026, 5, 28, 13, 30, 0)

    result = reject_step(request, "step-1", "1", "Not acceptable", decided_at)

    assert result.status == RequestStatus.REJECTED
    assert result.steps[0].status == StepStatus.REJECTED
    assert result.steps[0].comment == "Not acceptable"
    assert result.version == 2
    assert result.updated_at == decided_at
    assert request.status == RequestStatus.PENDING
    assert request.steps[0].status == StepStatus.PENDING
