# ADR-005: Deferred Infrastructure Policy (No Kafka, Kubernetes, Neo4j, or Microservice Sprawl)

**Status:** Accepted  
**Deciders:** Principal Architect  
**Date:** 2026-10-01  

---

## Context
Complex distributed infrastructure (Kafka, Kubernetes, Ray, distributed vector engines, Neo4j) is often introduced prematurely in AI applications, dramatically raising operational overhead and hindering developer velocity.

## Decision
We enforce a strict **Deferred Infrastructure Policy**:
- **No Kafka / RabbitMQ:** Use PostgreSQL transactional queues or Redis Streams / Celery.
- **No Kubernetes in Phase 0-4:** Use Docker Compose for local orchestration and containerized deployment.
- **No Dedicated Graph DB:** Use PostgreSQL 16+ relational tables with recursive CTEs.
- **No Dedicated Vector DB:** Use PostgreSQL with pgvector.
- **Modular Monolith over Microservices:** All backend domain services reside in a single well-structured FastAPI codebase with distinct modules.

## Rationale
- Maximizes development velocity, local developer ease, and testability.
- Simplifies operational footprint (runs easily on a single standard server or local machine).
- Any future infrastructure expansion must be justified by concrete scale bottlenecks measured in production.

## Consequences & Trade-offs
- **Positive:** Immediate setup, low resource consumption, zero distributed failure modes.
- **Negative:** If ingestion spikes to millions of concurrent documents per hour in future phases, a dedicated message broker can be integrated cleanly behind the established service interfaces.
