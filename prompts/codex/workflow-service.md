
# Workflow Service Implementation Prompt

## Context

You are working in the repository `approval-workflow-engine`.

Current branch: `feature/workflow-service`

Implement the domain workflow service layer for the approval workflow engine.

## Scope

- Only modify files under:
  - app/domain/
  - tests/unit/domain/
- Do not add API, persistence, AWS, FastAPI routes, or infrastructure.
- Keep the implementation small and reviewable.


## Constraints

- Use Python 3.14 syntax.
- Use Pydantic v2 models already present in app/domain/models.py.
- Follow Ruff formatting and linting.
- Every module and function must have an English docstring.
- Do not mutate ApprovalRequest in-place. Return a modified copy using Pydantic model_copy(deep=True).
- Do not modify domain models unless required for correctness.
- Keep the implementation small and reviewable.
- Prefer small, focused pytest test cases.


## Tasks

1. approve_step(...)
2. reject_step(...)



## Business Rules

- Workflow is strictly sequential.
- Only the current step can be approved or rejected.
- Only the assigned approver can act on the current step.
- The request must be PENDING.
- The current step must be PENDING.
- approve_step marks the current step as APPROVED.
- If the approved step is the final step, set request.status to APPROVED.
- Otherwise increment current_step_index by 1.
- reject_step requires a non-empty comment.
- reject_step marks the current step as REJECTED and request.status as REJECTED.
- Both actions set decided_at and updated_at.
- Both actions increment version by 1.

## Errors

Use the existing domain exceptions in app/domain/errors.py:
- UnauthorizedWorkflowAction
- InvalidWorkflowState
- RejectCommentRequired
- StepNotFound

## Tests

Add tests under tests/unit/domain/test_services.py.


Cover at least:
- approving the first step moves to the next step
- approving the final step approves the whole request
- wrong approver cannot approve
- approving a non-current step fails
- rejecting requires a non-empty comment
- rejection marks request as REJECTED
- service functions do not mutate the original request

## After implementation

- run `uv run ruff check .`
- run `uv run pytest`
- report what changed and any assumptions made.
