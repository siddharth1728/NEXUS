# NEXUS: Technology Decisions & Architecture Decision Records (ADRs)

**Document Version:** 1.0.0  
**Status:** Canonical Source of Truth  

---

## 1. Technology Selection Matrix

| Subsystem | Selected Technology | Alternative Considered | Core Rationale |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** (Python 3.12+) | Django, Go / Gin, Node.js | Native async support, high performance, tight integration with Pydantic v2 for AI schema validation, rich ecosystem for AI/data libraries (Docling, Langfuse). |
| **Data Validation** | **Pydantic v2** | Marshmallow, attrs | Industry-standard for FastAPI, Rust-backed high performance, native JSON Schema export for LLM structured output. |
| **Database & Vector** | **PostgreSQL 16+ with pgvector** | Neo4j, Qdrant, Milvus, MongoDB | Eliminates distributed database complexity; relational tables model nodes/edges with ACID guarantees while pgvector handles semantic similarity search in a single engine. |
| **ORM & Migrations** | **SQLAlchemy 2.0 (Async) + Alembic** | Tortoise-ORM, Prisma | Robust async query building, declarative mapping, mature migration tooling, deep ecosystem support. |
| **Frontend Framework** | **Next.js 15+ (App Router, React 19, TypeScript)** | Vite + React SPA, Remix | Superior full-stack capabilities, server-side rendering, streaming UI, ecosystem maturity for dashboard graphs. |
| **Styling & UI** | **Tailwind CSS + Radix UI / Lucide** | Material UI, Ant Design, Chakra UI | Lightweight, zero-runtime CSS, highly customizable design tokens for high-density workflow visualization. |
| **Document Processing** | **Docling** (IBM) | PyPDF, Unstructured.io, PDFMiner | Superior layout analysis, table extraction, chunking intelligence, and Markdown export for LLM ingestion. |
| **AI LLM Abstraction** | **Custom Provider Adapter (Gemini, Ollama, HF)** | LangChain, LlamaIndex | Complete architectural control, zero third-party dependency lock-in or breaking changes, tailored retry/fallback logic. |
| **Observability** | **Langfuse + OpenTelemetry** | Arize Phoenix, Weights & Biases | Open-source, self-hostable, dedicated LLM evaluation and trace analytics with OpenTelemetry standards. |
| **Testing** | **pytest + pytest-asyncio + Playwright** | unittest, Cypress | Industry-standard async testing for Python; fast, reliable headless browser E2E testing for the Next.js frontend. |

---

## 2. Architectural Decision Records Index

1. [ADR-001: Relational Action Graph with pgvector over Native Graph DB](file:///c:/NEXUS/docs/adr/ADR-001-action-graph-data-model.md)
2. [ADR-002: FastAPI, Pydantic v2 & SQLAlchemy 2.0 for Backend Foundation](file:///c:/NEXUS/docs/adr/ADR-002-backend-fastapi-pydantic-sqlalchemy.md)
3. [ADR-003: Next.js with TypeScript and Tailwind CSS for Action Graph Frontend](file:///c:/NEXUS/docs/adr/ADR-003-frontend-nextjs-tailwind.md)
4. [ADR-004: Provider-Agnostic AI Layer with Native Structured Output](file:///c:/NEXUS/docs/adr/ADR-004-provider-agnostic-ai-layer.md)
5. [ADR-005: Deferred Infrastructure Policy (No Kafka, Kubernetes, Neo4j)](file:///c:/NEXUS/docs/adr/ADR-005-deferred-infrastructure-policy.md)
