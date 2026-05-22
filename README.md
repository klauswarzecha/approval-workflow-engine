# Approval Workflow Engine

A generic, cloud-native approval workflow engine built on AWS.

The system allows users to create arbitrary requests (e.g. vacation requests, purchase approvals, access requests) and route them through a configurable multi-step approval process.

---

## ✨ Features (MVP Scope)

- Create a request with multiple ordered approval steps
- Sequential approval flow
- Only the assigned approver can approve/reject a step
- Final approval when all steps are approved
- Immediate rejection if any step is rejected
- Optimistic locking to prevent race conditions
- Event emission on workflow state changes

---

## 🧠 Design Goals

This project focuses on:

- Clean domain modeling
- Explicit architecture decisions
- Production-relevant concerns (concurrency, consistency)
- Event-driven design
- Infrastructure as Code

It is intentionally scoped as an MVP that demonstrates the core workflow behavior end-to-end.

---

## 🏗️ Architecture Overview

- **API Layer**: FastAPI (deployed via AWS Lambda + API Gateway)
- **Compute**: AWS Lambda (Python 3.14 runtime)
- **Persistence**: DynamoDB (single-table design)
- **Events**: SQS (with Outbox pattern)
- **Infrastructure**: OpenTofu
- **Dependency Management**: uv

---

## 🔄 Core Workflow

1. A user creates a request with a list of approval steps
2. The first approver reviews the request
3. Each step is processed sequentially
4. If all steps are approved → request is `APPROVED`
5. If any step is rejected → request is `REJECTED`

---

## 🧪 Testing Strategy

- Unit tests for domain logic and persistence
- Integration test covering a full multi-step approval workflow
- Selected failure cases (authorization, concurrency)

---

## 🚧 Out of Scope (for MVP)

- Complex role-based access control
- Advanced filtering and pagination
- UI
- Full-fledged notification system

---

## 📦 Deployment

Infrastructure is defined using OpenTofu.

Detailed instructions will be added after implementation.

---

## 📚 Architecture Decision Records

See `docs/adr/` for detailed design decisions and trade-offs.

---

## 🤖 AI-Assisted Development

This project was developed using AI-assisted tooling (e.g. ChatGPT, Codex).  
All architectural decisions and critical logic were explicitly reviewed and validated.

---

## 📌 Status

Work in progress – focused on building a production-grade MVP.