# Infrastructure Foundation Implementation Prompt

## Context

This repository implements a cloud-native approval workflow engine on AWS.

The infrastructure is defined with OpenTofu.

## Reference Documents

- AGENTS.md
- docs/adr/0001-mvp-scope.md
- docs/adr/0003-dynamodb-data-model.md
- docs/adr/0004-infrastructure-and-state-management.md

The ADRs are authoritative for architecture decisions, including OpenTofu state management.

## Scope

Only modify files under:

- infra/

Do not modify:

- app/
- tests/
- docs/adr/
- prompts/
- pyproject.toml
- uv.lock

## Existing Infrastructure Foundation

The following files already exist and should not be modified unless required for correctness:

- infra/versions.tf
- infra/providers.tf
- infra/variables.tf

## Implement

Create the OpenTofu infrastructure foundation for:

- DynamoDB application table
- IAM role and policies for future Lambda functions
- relevant outputs

## DynamoDB Requirements

Create a DynamoDB table for workflow persistence.

Requirements:

- Use PAY_PER_REQUEST billing mode.
- Use a single-table design.
- Use string partition key `PK`.
- Use string sort key `SK`.
- Add a GSI for requests by requester:
  - `GSI1PK`
  - `GSI1SK`
- Use `var.project_name` for naming.

The table stores:

- Request metadata items
- Pending approval projection items
- Outbox event items

## IAM Requirements

Create IAM resources required by future Lambda functions.

Requirements:

- IAM role for workflow Lambda functions
- Basic CloudWatch Logs permissions
- Least-privilege DynamoDB permissions for the workflow table

Do not create Lambda functions yet.

## Explicitly Out of Scope

Do not implement:

- Lambda functions
- API Gateway
- SQS
- EventBridge
- Cognito
- CI/CD
- CloudWatch alarms
- WAF
- multi-environment deployment logic

## Validation

Run:

- `tofu fmt`
- `tofu validate`

Report:

- files created
- resources added
- assumptions made

Keep the implementation small and reviewable.