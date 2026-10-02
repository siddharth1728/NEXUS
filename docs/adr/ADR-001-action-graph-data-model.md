# ADR-001: Relational Action Graph with pgvector over Native Graph Database

**Status:** Accepted  
**Deciders:** Principal Architect  
**Date:** 2026-10-01  

---

## Context
NEXUS requires an Action Graph representation to link Documents, Users, Facts, Tasks, Deadlines, Approvals, and Evidence. We must decide how to persist this graph and perform semantic similarity search on extracted chunks.

## Alternatives Considered
1. **Dedicated Graph Database (Neo4j, Amazon Neptune) + Vector Database (Qdrant, Pinecone):**
   - *Pros:* Native graph traversal syntax (Cypher), high performance on deep recursive traversals (>10 hops).
   - *Cons:* Operational complexity of managing two separate distributed databases, dual writes, transaction synchronization issues, high deployment cost.
2. **PostgreSQL with pgvector (Relational Node/Edge modeling + Dense Embeddings):**
   - *Pros:* Single production-grade engine, full ACID transactions across graph edges and vector embeddings, simple operational footprint, recursive CTEs handle DAG path traversals (1-5 hops) effortlessly, broad cloud compatibility (Supabase, RDS, self-hosted).
   - *Cons:* Deep arbitrary-depth graph traversals are less optimized than in specialized native graph engines.

## Decision
We choose **PostgreSQL 16+ with the pgvector extension**.  
The Action Graph entities (Users, Documents, Tasks, Approvals, Evidence) are modeled as typed relational tables, with explicit `graph_edges` tables tracking relationships (`source_id`, `target_id`, `relation_type`, `metadata`). Semantic chunk search is handled within the same database via pgvector `HNSW` indexes.

## Consequences & Trade-offs
- **Positive:** Zero operational synchronization overhead, unified backup/restore, relational consistency guarantees, simple local development.
- **Negative:** If graph traversals exceed 10+ hops across millions of nodes in future phases, recursive query performance will need caching or optimization. Action graphs in NEXUS are typically shallow DAGs (2-4 hops), making PostgreSQL an ideal fit.
