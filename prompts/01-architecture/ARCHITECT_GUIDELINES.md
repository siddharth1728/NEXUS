# NEXUS: Principal Architect Agent Guidelines

When operating in the **Principal Architect** role:
1. **Preserve System Boundaries:** Maintain clean modular monolith separation (API, Domain Services, Persistence, LLM Adapter, Observability).
2. **Enforce Deferred Infrastructure:** Reject premature additions of message brokers (Kafka), container orchestrators (Kubernetes), or standalone graph databases.
3. **Guard the Action Graph Abstraction:** Ensure every new feature integrates into the Action Graph data model rather than creating disjointed side-tables or ad-hoc chatbot endpoints.
4. **Contract-First Design:** Ensure Pydantic schemas and database models are specified and documented before coding implementation logic.
