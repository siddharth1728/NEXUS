# ADR-002: FastAPI, Pydantic v2 & SQLAlchemy 2.0 for Backend Foundation

**Status:** Accepted  
**Deciders:** Principal Architect  
**Date:** 2026-10-01  

---

## Context
The NEXUS backend must support high-performance asynchronous I/O, strict data validation, seamless integration with Python AI/ML libraries (Docling, Langfuse, NumPy), and structured contract generation (OpenAPI & JSON Schema).

## Decision
We select **FastAPI (Python 3.12+)** paired with **Pydantic v2** and **SQLAlchemy 2.0 (Async)**.

## Rationale
- **Pydantic v2:** Rust-backed validation ensures extreme throughput. Its `model_json_schema()` generation directly supplies schemas to LLMs for structured JSON decoding.
- **SQLAlchemy 2.0 Async:** Provides robust async ORM and Core query generation with `asyncpg`, handling concurrency and transaction isolation cleanly.
- **FastAPI:** Delivers automatic OpenAPI documentation, dependency injection for auth/sessions, and native async endpoint execution.

## Consequences & Trade-offs
- **Positive:** Uniform Python ecosystem for both backend business logic and AI/data pipelines; seamless typing and contract enforcement.
- **Negative:** Async Python requires discipline (avoiding blocking I/O calls in event loops). Heavy CPU-bound tasks (Docling parsing) must run in thread pools or background processes.
