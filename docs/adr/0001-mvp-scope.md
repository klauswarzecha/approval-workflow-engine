# ADR 0001: MVP Scope and Design Focus

## Status
Accepted

## Context

The challenge requires building a generic approval workflow engine with:

- Configurable multi-step approvals
- REST API
- Event-driven behavior
- Cloud-native deployment using Infrastructure as Code

Given the scope, it is not feasible to fully implement all features in production quality within limited time.

Therefore, a focused MVP approach is chosen.

---

## Decision

The MVP will focus on a **single, fully functional end-to-end workflow**, supported by selected failure scenarios.

### Golden Path

The system must correctly support:

1. A user creates a request with multiple approval steps
2. The first approver approves the request
3. The next approver approves the request
4. The request transitions to `APPROVED`

This flow must be fully implemented and tested.

---

### Failure Scenarios

The MVP will explicitly handle selected failure cases:

- Unauthorized approval attempt (wrong user)
- Missing rejection comment
- Concurrent updates (optimistic locking conflict)

These scenarios are chosen because they demonstrate:

- Authorization correctness
- Input validation
- Concurrency control

---

### Explicitly Out of Scope

The following features are intentionally excluded or simplified:

- Complex RBAC models
- Advanced querying (filtering, pagination)
- Full notification system
- Extensive error taxonomy
- UI layer

---

## Rationale

This approach ensures:

- The core domain behavior is correct and demonstrable
- Critical production concerns (concurrency, consistency) are addressed
- The solution remains explainable and reviewable

Instead of partially implementing many features, the focus is on **correctness and clarity of the core workflow**.

---

## Consequences

- The system is not feature-complete but demonstrates production-relevant design
- Additional features can be added incrementally on top of a solid foundation
- The design is easier to explain and defend in follow-up discussions