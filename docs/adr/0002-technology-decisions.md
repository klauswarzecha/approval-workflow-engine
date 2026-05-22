# ADR 0002: Technology and Architecture Decisions

## Status
Accepted

## Context

The goal of this project is to build a cloud-native approval workflow engine that is:

- production-relevant
- explainable in design decisions
- deployable via Infrastructure as Code

The solution must balance simplicity (MVP scope) with realistic architectural considerations.

---

## Decision

The system is built using the following technology stack:

- **Language**: Python 3.14
- **Dependency Management**: uv
- **API Layer**: FastAPI (deployed via AWS Lambda)
- **Compute**: AWS Lambda (Python 3.14 runtime)
- **API Gateway**: AWS API Gateway (HTTP API)
- **Persistence**: DynamoDB (single-table design)
- **Events**: Amazon SQS
- **Infrastructure as Code**: OpenTofu

All documentation and code use American English spelling for consistency with AWS and the broader Python ecosystem.

---

## Rationale

### Python 3.14

Python 3.14 is chosen to use a modern and up-to-date runtime.

AWS Lambda provides native support for Python 3.14, allowing use of the managed runtime without container overhead.

---

### uv (Dependency Management)

`uv` is selected over traditional tools such as `pip` or `Poetry` because:

- fast dependency resolution and installation
- reproducible environments via `uv.lock`
- modern Python project structure using `pyproject.toml`

---

### FastAPI + Lambda

FastAPI is used as the API framework because:

- strong typing support via Pydantic
- automatic OpenAPI generation
- clear request/response modeling

It is deployed via AWS Lambda to maintain a fully serverless architecture.

This provides:

- low operational overhead
- scalability by default
- cost efficiency for low-to-medium workloads

---

### API Gateway (HTTP API)

API Gateway is used to expose the REST API:

- integrates natively with Lambda
- provides request routing and authentication integration
- simpler and cheaper than REST API variant for MVP use cases

---

### DynamoDB (Single-Table Design)

DynamoDB is selected because:

- it is fully managed and serverless
- predictable performance
- well-suited for access-pattern-driven design

A single-table design is used to support multiple access patterns efficiently.

Key access patterns:

- Fetch request by ID
- List requests created by a user
- List requests waiting for a specific approver

These patterns drive the key design and item structure.

---

### Sequential Workflow Model

The workflow is strictly sequential:

- only one step is active at a time
- only the assigned approver can act on the current step

This simplifies:

- state management
- concurrency control
- reasoning about system behavior

Parallel approvals are intentionally out of scope for the MVP.

---

### Concurrency Control (Optimistic Locking)

Optimistic locking is used to prevent race conditions:

- each request contains a `version` attribute
- updates use conditional writes in DynamoDB

This ensures:

- only one concurrent update succeeds
- conflicting updates are rejected with a clear error (409 Conflict)

---

### Event Handling (SQS)

Amazon SQS is used for asynchronous event handling:

- decouples workflow processing from notification handling
- ensures reliable delivery via retry mechanisms

---

### Consistency Between DB and Events (Outbox Pattern)

To avoid inconsistencies between database writes and event publication:

- events are written to an outbox within the same database transaction
- a separate process publishes events to SQS

This ensures:

- no lost events after successful state changes
- eventual consistency between system state and emitted events

Trade-off:
- increased implementation complexity
- but significantly improved reliability

---

### OpenTofu (Infrastructure as Code)

OpenTofu is used instead of AWS CDK because:

- declarative infrastructure definition
- strong ecosystem compatibility with Terraform
- easier to review in pull requests (plain HCL)
- no additional abstraction layer in application code

---

## Consequences

- The system is fully serverless and scalable
- The architecture prioritizes clarity and correctness over feature completeness
- Additional features can be added incrementally without changing core design decisions