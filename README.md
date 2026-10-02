# NEXUS

> **Open-Source Context-to-Action Engine**  
> *Transforming fragmented unstructured context into personalized, source-grounded, dependency-aware actions with verified completion.*

---

## 🧭 Mission

In modern work environments, critical information arrives across fragmented channels: documents, emails, chat messages, meetings, announcements, technical specifications, and ticketing systems. People spend immense cognitive effort manually parsing:
- **Relevance:** Does this information apply to me, my team, or my project?
- **Implications:** What does this mean in practical terms?
- **Action Items:** What concrete tasks are required?
- **Timelines:** What are the strict deadlines and milestones?
- **Dependencies:** What must happen before this action can start, and who is blocked?
- **Execution:** What tools, approvals, or materials are needed?
- **Verification:** Has the required action actually been completed with auditable evidence?

**NEXUS is NOT a generic chatbot or conversational wrapper.**  
It is a deterministic, auditable **Action Graph engine** that ingests multi-source data, extracts verifiable facts and structured actions, resolves cross-entity dependencies, and tracks progress to verified completion.

---

## 🏛️ Core Architecture Principles

1. **Context → Understanding → Actions → Dependencies → Execution → Verification**
2. **Action Graph First:** Relations (`applies_to`, `creates`, `depends_on`, `requires`, `due_on`, `completed_by`) are first-class citizens.
3. **Provider-Agnostic AI:** Unified LLM adapter interface supporting Gemini, Ollama, Hugging Face, and OpenAI-compatible models.
4. **Never Invent Facts:** Missing evidence is `UNKNOWN`, conflicting information is `CONFLICT`, low confidence is `REQUIRES_REVIEW`.
5. **Human-in-the-Loop:** Consequential actions require explicit human authorization.
6. **No Premature Infrastructure:** Built on clean, composable foundations (PostgreSQL + pgvector, FastAPI, Next.js) without operational bloat.

---

## 📚 Source of Truth Documentation

Explore the comprehensive engineering documentation:

- [Product Definition & Vision](file:///c:/NEXUS/docs/01_PRODUCT_DEFINITION.md)
- [System Architecture](file:///c:/NEXUS/docs/02_SYSTEM_ARCHITECTURE.md)
- [Engineering Constitution & Principles](file:///c:/NEXUS/docs/03_ENGINEERING_CONSTITUTION.md)
- [Technology Decisions & ADRs](file:///c:/NEXUS/docs/04_TECHNOLOGY_DECISIONS.md)
- [AI Architecture & Staged Pipeline](file:///c:/NEXUS/docs/05_AI_ARCHITECTURE_PIPELINE.md)
- [Security & Authorization Framework](file:///c:/NEXUS/docs/06_SECURITY_AND_AUTHORIZATION.md)
- [Data Model & Action Graph Specification](file:///c:/NEXUS/docs/07_DATA_MODEL_SPECIFICATION.md)
- [API Design Specification](file:///c:/NEXUS/docs/08_API_DESIGN_SPECIFICATION.md)
- [Testing Strategy](file:///c:/NEXUS/docs/09_TESTING_STRATEGY.md)
- [Evaluation & Observability](file:///c:/NEXUS/docs/10_EVALUATION_AND_OBSERVABILITY.md)
- [Development Phases & Roadmap](file:///c:/NEXUS/docs/11_DEVELOPMENT_PHASES_AND_ROADMAP.md)
- [Definition of Done](file:///c:/NEXUS/docs/12_DEFINITION_OF_DONE.md)
- [Prompt Engineering Architecture](file:///c:/NEXUS/prompts/README.md)

---

## 🗺️ Implementation Roadmap Summary

| Phase | Focus | Status |
| :--- | :--- | :--- |
| **Phase 00** | System Initialization, Specifications & Engineering Constitution | **Completed** |
| **Phase 01** | Core Domain Models, LLM Provider Abstraction & Document Ingestion Baseline | Planned |
| **Phase 02** | Staged AI Extraction Pipeline & Action Graph Construction | Planned |
| **Phase 03** | Personalization, Relevance Scoring & Dependency Resolution Engine | Planned |
| **Phase 04** | Execution Verification & Evidence Collection Engine | Planned |
| **Phase 05** | Next.js Action Graph UI, Human-in-the-Loop Workbench & Observability | Planned |

---

## ⚖️ License

NEXUS is open-source software licensed under the Apache 2.0 License.
