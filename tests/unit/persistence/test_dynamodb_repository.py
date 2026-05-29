"""Tests for the DynamoDB approval request repository."""

from datetime import datetime

import boto3
import pytest
from moto import mock_aws

from app.domain.models import ApprovalRequest, ApprovalStep, RequestStatus
from app.domain.services import approve_step
from app.persistence.dynamodb_repository import DynamoDBApprovalRequestRepository
from app.persistence.errors import OptimisticLockConflict


TABLE_NAME = "approval-workflows"


@pytest.fixture
def dynamodb_table():
    """Create a DynamoDB table with the MVP single-table key schema."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield dynamodb, table


@pytest.fixture
def repository(dynamodb_table):
    """Create a repository bound to the test table."""
    dynamodb, _table = dynamodb_table
    return DynamoDBApprovalRequestRepository(TABLE_NAME, dynamodb)


def make_request() -> ApprovalRequest:
    """Build a two-step approval request."""
    now = datetime(2026, 5, 29, 10, 0, 0)
    return ApprovalRequest(
        request_id="request-1",
        requester_id="requester-1",
        title="Approve purchase",
        payload={"amount": 100},
        status=RequestStatus.PENDING,
        current_step_index=0,
        steps=[
            ApprovalStep(step_id="step-1", order=1, approver_id="approver-1"),
            ApprovalStep(step_id="step-2", order=2, approver_id="approver-2"),
        ],
        version=1,
        created_at=now,
        updated_at=now,
    )


def test_save_stores_metadata_and_active_pending_projection(
    repository,
    dynamodb_table,
):
    """Save writes the aggregate and only the current pending approval."""
    _dynamodb, table = dynamodb_table
    approval_request = make_request()

    repository.save(approval_request)

    stored_request = repository.get("request-1")
    assert stored_request == approval_request

    pending_response = table.get_item(
        Key={
            "PK": "APPROVER#approver-1",
            "SK": "REQUEST#request-1#STEP#step-1",
        }
    )
    assert pending_response["Item"]["entity_type"] == "PENDING_APPROVAL"

    assert repository.list_by_requester("requester-1") == [approval_request]
    assert repository.list_pending_for_approver("approver-1") == [approval_request]
    assert repository.list_pending_for_approver("approver-2") == []


def test_update_moves_pending_projection_and_writes_outbox(
    repository,
    dynamodb_table,
):
    """Update replaces the active pending projection and writes an outbox event."""
    _dynamodb, table = dynamodb_table
    approval_request = make_request()
    repository.save(approval_request)

    updated_request = approve_step(
        approval_request,
        "step-1",
        "approver-1",
        datetime(2026, 5, 29, 10, 30, 0),
    )

    repository.update(
        updated_request,
        expected_version=1,
        event={
            "event_id": "event-1",
            "event_type": "approval_step_approved",
            "created_at": "2026-05-29T10:30:00",
            "payload": {"request_id": "request-1", "step_id": "step-1"},
        },
    )

    assert repository.get("request-1") == updated_request
    assert repository.list_pending_for_approver("approver-1") == []
    assert repository.list_pending_for_approver("approver-2") == [updated_request]

    old_pending_response = table.get_item(
        Key={
            "PK": "APPROVER#approver-1",
            "SK": "REQUEST#request-1#STEP#step-1",
        }
    )
    assert "Item" not in old_pending_response

    outbox_response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": "OUTBOX"},
    )
    assert outbox_response["Items"][0]["entity_type"] == "OUTBOX_EVENT"
    assert outbox_response["Items"][0]["event_id"] == "event-1"


def test_update_rejects_stale_expected_version(repository):
    """Update raises an optimistic lock conflict for a stale version."""
    approval_request = make_request()
    repository.save(approval_request)

    updated_request = approve_step(
        approval_request,
        "step-1",
        "approver-1",
        datetime(2026, 5, 29, 10, 15, 0),
    )

    with pytest.raises(OptimisticLockConflict):
        repository.update(updated_request, expected_version=0)
