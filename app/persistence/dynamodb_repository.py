"""DynamoDB repository implementation for approval requests."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.domain.models import ApprovalRequest, ApprovalStep, RequestStatus
from app.persistence.errors import ApprovalRequestNotFound, OptimisticLockConflict

METADATA_SK = "METADATA"
REQUEST_ENTITY_TYPE = "REQUEST_METADATA"
PENDING_ENTITY_TYPE = "PENDING_APPROVAL"
OUTBOX_ENTITY_TYPE = "OUTBOX_EVENT"
REQUESTER_INDEX_NAME = "GSI1"


class DynamoDBApprovalRequestRepository:
    """DynamoDB-backed repository for approval requests."""

    def __init__(
        self,
        table_name: str,
        dynamodb_resource: Any | None = None,
    ) -> None:
        """Initialize the repository with a DynamoDB table name."""
        self.table_name = table_name
        self.dynamodb_resource = dynamodb_resource or boto3.resource("dynamodb")
        self.table = self.dynamodb_resource.Table(table_name)
        self.client = self.table.meta.client

    def save(
        self,
        approval_request: ApprovalRequest,
        event: dict[str, object] | None = None,
    ) -> None:
        """Persist a new approval request and its active pending approval."""
        transaction_items = [
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": self._marshal_item(self._metadata_item(approval_request)),
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            }
        ]

        pending_item = self._pending_item(approval_request)
        if pending_item is not None:
            transaction_items.append(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": self._marshal_item(pending_item),
                    }
                }
            )

        if event is not None:
            transaction_items.append(self._put_transaction(self._outbox_item(event)))

        self._transact_write(transaction_items)

    def get(self, request_id: str) -> ApprovalRequest | None:
        """Return an approval request by ID if it exists."""
        response = self.table.get_item(
            Key={"PK": self._request_pk(request_id), "SK": METADATA_SK}
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._approval_request_from_item(item)

    def update(
        self,
        approval_request: ApprovalRequest,
        expected_version: int,
        event: dict[str, object] | None = None,
    ) -> None:
        """Persist an updated approval request using optimistic locking."""
        current_request = self.get(approval_request.request_id)
        if current_request is None:
            raise ApprovalRequestNotFound(
                f"Approval request {approval_request.request_id} was not found."
            )

        transaction_items = [
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": self._marshal_item(self._metadata_item(approval_request)),
                    "ConditionExpression": "#version = :expected_version",
                    "ExpressionAttributeNames": {"#version": "version"},
                    "ExpressionAttributeValues": self._marshal_item(
                        {":expected_version": expected_version}
                    ),
                }
            }
        ]

        current_pending_key = self._pending_key(current_request)
        if current_pending_key is not None:
            transaction_items.append(
                {
                    "Delete": {
                        "TableName": self.table_name,
                        "Key": self._marshal_item(current_pending_key),
                    }
                }
            )

        next_pending_item = self._pending_item(approval_request)
        if next_pending_item is not None:
            transaction_items.append(self._put_transaction(next_pending_item))

        if event is not None:
            transaction_items.append(self._put_transaction(self._outbox_item(event)))

        self._transact_write(transaction_items)

    def list_by_requester(
        self,
        requester_id: str,
        status: RequestStatus | None = None,
    ) -> list[ApprovalRequest]:
        """Return requests created by a requester."""
        key_condition = Key("GSI1PK").eq(self._requester_gsi_pk(requester_id))
        if status is not None:
            key_condition &= Key("GSI1SK").begins_with(f"STATUS#{status.value}#")

        response = self.table.query(
            IndexName=REQUESTER_INDEX_NAME,
            KeyConditionExpression=key_condition,
        )
        return [
            self._approval_request_from_item(item)
            for item in response.get("Items", [])
            if item.get("entity_type") == REQUEST_ENTITY_TYPE
        ]

    def list_pending_for_approver(self, approver_id: str) -> list[ApprovalRequest]:
        """Return requests currently waiting for an approver."""
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(self._approver_pk(approver_id))
        )

        approval_requests = []
        for item in response.get("Items", []):
            request_id = item["request_id"]
            approval_request = self.get(request_id)
            if approval_request is not None:
                approval_requests.append(approval_request)
        return approval_requests

    def _transact_write(self, transaction_items: list[dict[str, Any]]) -> None:
        """Write transaction items and normalize conditional failures."""
        try:
            self.client.transact_write_items(TransactItems=transaction_items)
        except ClientError as error:
            error_code = error.response["Error"]["Code"]
            if error_code in {
                "ConditionalCheckFailedException",
                "TransactionCanceledException",
            }:
                raise OptimisticLockConflict(
                    "Approval request version did not match expected version."
                ) from error
            raise

    def _put_transaction(self, item: dict[str, Any]) -> dict[str, Any]:
        """Build a DynamoDB transaction put operation."""
        return {
            "Put": {
                "TableName": self.table_name,
                "Item": self._marshal_item(item),
            }
        }

    def _metadata_item(self, approval_request: ApprovalRequest) -> dict[str, Any]:
        """Build the request metadata item for the aggregate root."""
        request_id = approval_request.request_id
        return {
            "PK": self._request_pk(request_id),
            "SK": METADATA_SK,
            "entity_type": REQUEST_ENTITY_TYPE,
            "request_id": request_id,
            "requester_id": approval_request.requester_id,
            "title": approval_request.title,
            "payload": approval_request.payload,
            "status": approval_request.status.value,
            "current_step_index": approval_request.current_step_index,
            "steps": [self._step_to_item(step) for step in approval_request.steps],
            "version": approval_request.version,
            "created_at": approval_request.created_at.isoformat(),
            "updated_at": approval_request.updated_at.isoformat(),
            "GSI1PK": self._requester_gsi_pk(approval_request.requester_id),
            "GSI1SK": (
                f"STATUS#{approval_request.status.value}#"
                f"CREATED_AT#{approval_request.created_at.isoformat()}#"
                f"REQUEST#{request_id}"
            ),
        }

    def _pending_item(self, approval_request: ApprovalRequest) -> dict[str, Any] | None:
        """Build the active pending approval projection item if one exists."""
        pending_key = self._pending_key(approval_request)
        if pending_key is None:
            return None

        current_step = approval_request.steps[approval_request.current_step_index]
        return {
            **pending_key,
            "entity_type": PENDING_ENTITY_TYPE,
            "request_id": approval_request.request_id,
            "step_id": current_step.step_id,
            "approver_id": current_step.approver_id,
            "requester_id": approval_request.requester_id,
            "title": approval_request.title,
            "created_at": approval_request.created_at.isoformat(),
        }

    def _pending_key(self, approval_request: ApprovalRequest) -> dict[str, str] | None:
        """Return the active pending approval key if the request is pending."""
        if approval_request.status != RequestStatus.PENDING:
            return None
        if not 0 <= approval_request.current_step_index < len(approval_request.steps):
            return None

        current_step = approval_request.steps[approval_request.current_step_index]
        return {
            "PK": self._approver_pk(current_step.approver_id),
            "SK": (
                f"REQUEST#{approval_request.request_id}#STEP#{current_step.step_id}"
            ),
        }

    def _outbox_item(self, event: dict[str, object]) -> dict[str, Any]:
        """Build an outbox item for reliable event publication."""
        event_id = str(event.get("event_id") or uuid4())
        created_at = event.get("created_at") or datetime.now(UTC)
        created_at_text = (
            created_at.isoformat()
            if isinstance(created_at, datetime)
            else str(created_at)
        )

        return {
            "PK": "OUTBOX",
            "SK": f"EVENT#{created_at_text}#{event_id}",
            "entity_type": OUTBOX_ENTITY_TYPE,
            **event,
            "event_id": event_id,
            "created_at": created_at_text,
        }

    def _approval_request_from_item(self, item: dict[str, Any]) -> ApprovalRequest:
        """Deserialize a request metadata item into a domain model."""
        return ApprovalRequest(
            request_id=item["request_id"],
            requester_id=item["requester_id"],
            title=item["title"],
            payload=item["payload"],
            status=item["status"],
            current_step_index=item["current_step_index"],
            steps=[ApprovalStep(**step) for step in item["steps"]],
            version=item["version"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    def _step_to_item(self, step: ApprovalStep) -> dict[str, Any]:
        """Serialize an approval step for storage."""
        return {
            "step_id": step.step_id,
            "order": step.order,
            "approver_id": step.approver_id,
            "status": step.status.value,
            "decided_at": (
                step.decided_at.isoformat() if step.decided_at is not None else None
            ),
            "comment": step.comment,
        }

    def _marshal_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Return Python values for boto3's DynamoDB resource transformer."""
        return item

    def _request_pk(self, request_id: str) -> str:
        """Return the request aggregate partition key."""
        return f"REQUEST#{request_id}"

    def _approver_pk(self, approver_id: str) -> str:
        """Return the pending approval partition key for an approver."""
        return f"APPROVER#{approver_id}"

    def _requester_gsi_pk(self, requester_id: str) -> str:
        """Return the requester GSI partition key."""
        return f"REQUESTER#{requester_id}"
