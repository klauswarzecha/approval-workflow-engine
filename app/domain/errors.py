class WorkflowError(Exception):
    """Base exception for workflow domain errors."""


class UnauthorizedWorkflowAction(WorkflowError):
    """Raised when a user is not allowed to perform a workflow action."""


class InvalidWorkflowState(WorkflowError):
    """Raised when the workflow state does not allow the requested action."""


class RejectCommentRequired(WorkflowError):
    """Raised when a rejection is attempted without a comment."""


class StepNotFound(WorkflowError):
    """Raised when the requested approval step does not exist."""