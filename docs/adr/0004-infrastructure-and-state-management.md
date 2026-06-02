# ADR 0004: Infrastructure Foundation and State Management

## Status

Accepted

## Context

The approval workflow engine must be deployed using Infrastructure as Code (IaC) and run as a cloud-native application on AWS.

The infrastructure should remain simple, explainable, and aligned with the MVP scope. The goal is to demonstrate a complete end-to-end workflow while avoiding unnecessary operational complexity.

The project requires:

* Persistent storage for workflow state
* Public API access
* Event-driven processing
* Repeatable infrastructure provisioning

---

## Decision

The infrastructure is provisioned using OpenTofu.

A modern OpenTofu version is assumed, supporting native S3 state locking via `use_lockfile = true`.

The OpenTofu state is stored in a dedicated S3 bucket.

No DynamoDB table is created for OpenTofu state locking.

The initial infrastructure deployment consists of:

* DynamoDB table for workflow persistence
* API Gateway HTTP API
* Lambda function for API request handling
* SQS queue for workflow events
* Lambda function for asynchronous event processing
* IAM roles and policies required by the application
* CloudWatch Logs created by AWS Lambda

---

## State Management

OpenTofu remote state is stored in a dedicated S3 bucket.

State locking is performed using native S3 locking:

```hcl
use_lockfile = true
```

A separate DynamoDB table for state locking is intentionally not used.

The DynamoDB service is reserved exclusively for application data and must not be shared with infrastructure state management.

---

## Explicitly Out of Scope

The following infrastructure concerns are intentionally excluded from the MVP:

* Multi-environment deployments
* CI/CD pipelines
* Custom domains
* AWS WAF
* Cognito integration
* CloudWatch dashboards and alarms
* Cross-account deployments
* Disaster recovery automation

---

## Rationale

This approach provides:

* A fully reproducible deployment process
* Minimal operational complexity
* Clear separation between infrastructure state and application data
* Reduced AWS resource footprint
* Infrastructure that remains easy to explain and review

By limiting the deployment to the components required for the workflow engine, the infrastructure remains aligned with the MVP philosophy established in ADR 0001.

---

## Consequences

* Infrastructure can be provisioned with a small OpenTofu codebase
* No additional DynamoDB resources are required for state locking
* Future operational features can be added incrementally
* The deployment remains easy to understand during code reviews and follow-up discussions
