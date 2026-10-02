# NEXUS: Testing Strategy & Quality Assurance

**Document Version:** 1.0.0  
**Status:** Canonical Source of Truth  

---

## 1. Testing Philosophy

Testing in NEXUS is structured to guarantee deterministic behavior across both traditional relational code and stochastic AI pipeline stages.

```
       ▲
      / \     E2E Tests (Playwright: UI Graph, Ingestion Flow, Evidence Upload)
     /   \
    /-----\   Integration Tests (FastAPI Routers, Async DB, pgvector, Provider Adapters)
   /       \
  /---------\ Unit Tests (DAG Topological Sort, Cycle Detection, Pydantic Schemas, Parsers)
```

---

## 2. Testing Layers

### 2.1 Unit Testing (`tests/unit/`)
- **Action Graph Algorithms:**
  - Cycle detection (Tarjan's / DFS algorithm)
  - Topological sorting of executable tasks
  - Critical path computation
  - State machine transition guards
- **Pydantic Validation & Serialization:**
  - Strict parsing of valid LLM JSON responses
  - Error recovery handlers on malformed or truncated inputs
- **Docling / Document Parsers:**
  - Structural chunking and metadata extraction from sample documents

### 2.2 Integration Testing (`tests/integration/`)
- **API Endpoints:**
  - FastAPI `httpx.AsyncClient` testing of all `/api/v1` routes
  - Authorization & tenant isolation validation
- **Database & Persistence:**
  - Testcontainers / local PostgreSQL + pgvector fixtures
  - HNSW similarity search accuracy
  - Transaction rollbacks on edge creation failures
- **Mock AI Provider Tests:**
  - Deterministic `MockLLMProvider` fixture simulating responses, network timeouts, rate limits, and repair retries

### 2.3 End-to-End Testing (`tests/e2e/`)
- **Playwright Suite:**
  - Document upload → Visualizing extracted Action Graph
  - Editing task properties and adding dependency links
  - Submitting evidence and verifying completion badge

---

## 3. Mock AI Testing Fixtures

Unit and CI integration tests must **never** make live billable API calls to external providers.

```python
class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for unit and CI testing."""
    def __init__(self, canned_responses: dict[str, Any]):
        self.canned_responses = canned_responses

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        response_dict = self.canned_responses.get(schema.__name__, {})
        return schema.model_validate(response_dict)
```

---

## 4. Test Execution Commands

```bash
# Run backend unit and integration tests
pytest tests/ -v --cov=nexus --cov-report=term-missing

# Run with fast fail
pytest tests/ -x

# Run frontend E2E tests
npx playwright test
```
