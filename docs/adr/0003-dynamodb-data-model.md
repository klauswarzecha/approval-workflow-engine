# ADR 0003: DynamoDB Data Model and Access Pattern Design

## Status
Accepted

## Context

DynamoDB requires a data model that is driven by application access patterns rather than normalized relational design.

The system must efficiently support the following core access patterns:

- Fetch a request by ID
- List requests created by a user
- List requests waiting for approval by a specific user
- Perform safe, concurrent updates on the active workflow step

Additionally, the system must emit events reliably after state changes.

---

## Decision

A single-table design is used with multiple item types:

1. **Request Metadata Item (Aggregate Root)**
2. **Pending Approval Items (Projection)**
3. **Outbox Event Items**

An `entity_type` attribute is included in all items to simplify debugging, deserialization, and future extensibility. It is not used for querying or indexing.

---

### Request Metadata Item

Each request is stored as a single aggregate item:

```text
PK = REQUEST#<request_id>
SK = METADATA
```

The item contains:

- full request data
- embedded approval steps
- workflow state (status, current_step_index)
- version for optimistic locking
- timestamps

Steps are embedded to allow atomic updates and consistent state transitions.

---

### Pending Approval Items

To efficiently query "requests waiting for a specific approver", a projection item is created:

```
PK = APPROVER#<approver_id>
SK = REQUEST#<request_id>#STEP#<step_id>
```

Only the currently active step is represented as a pending approval item.

When a step is approved or rejected:

- the current pending item is deleted
- a new pending item is created for the next step (if any)

This ensures that each approver sees only the tasks they are currently responsible for.

---

### Requester Index (GSI)

To list requests created by a user:

```
GSI1PK = REQUESTER#<requester_id>
GSI1SK = STATUS#<status>#CREATED_AT#<timestamp>#REQUEST#<request_id>
```

This allows efficient querying of:

- all requests of a user
- filtered subsets (e.g. only PENDING requests)

without scanning the table.

---

### Outbox Event Items

To ensure reliable event publication, an outbox pattern is used:

```
PK = OUTBOX
SK = EVENT#<timestamp>#<event_id>
```

Events are written within the same transaction as the workflow update.

Outbox items are queried via PK = OUTBOX, not via entity_type`.

A separate process is responsible for publishing events to SQS.

---

### Concurrency Control

Optimistic locking is implemented using a version attribute:

- each update requires version == expected_version
- the version is incremented on each successful update

This prevents concurrent modifications of the same workflow instance.

---

### Workflow Execution Model

The workflow is strictly sequential:

- only one step is active at a time
- only the assigned approver can act on the current step

This simplifies consistency and concurrency handling.

---

## Rationale

This design ensures:

- efficient access for core application use cases
- atomic updates on workflow state
- clear ownership of workflow state (aggregate model)
- reliable event publication via the outbox pattern

Embedding steps avoids cross-item transactions for most operations.

---

## Consequences

- Additional projection items (pending approvals) must be maintained
- Reporting queries (e.g. by status or step) are not fully optimized
- DynamoDB item size limits may constrain very large workflows (acceptable for MVP)
- Event publication is eventually consistent due to the outbox pattern


## Alternatives Considered

### Separate Step Items

Each step stored as its own item.

Rejected because:

- increases complexity of updates
- requires multi-item transactions for each approval decision
- complicates consistency guarantees

---

### Direct Event Publishing Without Outbox

Publishing events immediately after DB writes.

Rejected because:

- risk of lost events if publishing fails
- no retry mechanism tied to state changes

---

## Conclusion

The chosen design prioritizes:

- correctness of workflow state transitions
- efficiency of primary access patterns
- clarity of the data model

It provides a solid foundation for incremental extension.


---