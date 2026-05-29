# Agent Guidelines

## General

- Keep changes small and reviewable.
- Do not expand scope beyond the current prompt.
- Prefer simple, explicit code over clever abstractions.
- Follow existing project structure and naming conventions.

## Python

- Use Python 3.14 syntax.
- Follow PEP 8.
- Follow Ruff/Black-compatible formatting.
- Use modern Python typing.
- Use `str | None` instead of `Optional[str]`.
- Use descriptive variable names.
- Avoid single-letter variables except for conventional cases.

## Documentation

- Every module must have a top-level docstring.
- Every class, function, and method must have an English docstring.
- Use American English spelling in documentation and code comments.

## Testing

- Add or update focused pytest tests for behavior changes.
- Prefer small, explicit tests over large scenario tests.
- Run:
  - `uv run ruff check .`
  - `uv run pytest`

## Architecture

- Keep domain logic independent from API, persistence, and infrastructure.
- Do not introduce new frameworks or services without an ADR.
- ADRs are authoritative for architectural decisions.

## Dependencies

- Use uv for dependency management.
- Do not use pip commands.