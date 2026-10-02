# NEXUS: REST & Event API Specification

**Document Version:** 1.0.0  
**Status:** Canonical Source of Truth  
**Base URL:** `/api/v1`  

---

## 1. API Design Principles

1. **RESTful Resource Structure:** Clear hierarchical endpoints for documents, facts, tasks, graph edges, and evidence.
2. **Deterministic Status Codes:** Strict usage of standard HTTP status codes (`200 OK`, `201 Created`, `202 Accepted` for async jobs, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`).
3. **Real-Time Streaming:** Server-Sent Events (SSE) for tracking asynchronous document extraction, graph construction, and evidence verification.
4. **Structured Error Envelope:** All non-2xx responses return a consistent error schema.

---

## 2. Global Error Envelope

```json
{
  "error": {
    "code": "DEPENDENCY_CYCLE_DETECTED",
    "message": "The proposed dependency creates a cycle between Task A and Task B.",
    "details": {
      "cycle_path": ["f47ac10b-58cc-4372-a567-0e02b2c3d479", "c9bf9e57-1685-4c89-bafb-ff5af830be8a"]
    },
    "request_id": "req_01h7vbn..."
  }
}
```

---

## 3. Core API Endpoints Index

### 3.1 Ingestion & Documents
- `POST /api/v1/documents/upload`
  - Multipart form upload of files (PDF, DOCX, TXT, MD, Images).
  - Returns: `202 Accepted` with `document_id` and background processing task ID.
- `GET /api/v1/documents/{document_id}`
  - Retrieves document metadata, parsing status, and chunk count.
- `GET /api/v1/documents/{document_id}/stream`
  - SSE stream of extraction events (`chunking`, `classifying`, `extracting_facts`, `synthesizing_tasks`, `complete`).

### 3.2 Action Graph & Tasks
- `GET /api/v1/graph/view`
  - Query parameters: `project_id`, `assignee_id`, `status`, `depth`.
  - Returns DAG node list and edge list for interactive rendering.
- `GET /api/v1/tasks`
  - Filter by `status`, `priority`, `assignee_id`, `is_blocked`.
- `GET /api/v1/tasks/{task_id}`
  - Retrieves full task details, upstream prerequisites, downstream blockers, grounded source facts, and required approvals.
- `PATCH /api/v1/tasks/{task_id}/status`
  - Manually transition task status (e.g. `CANDIDATE` → `READY`, `IN_PROGRESS`).
- `POST /api/v1/tasks/{task_id}/authorize`
  - Human review approval gate authorization.

### 3.3 Dependencies & Graph Edges
- `POST /api/v1/graph/edges`
  - Add explicit edge (e.g. `source_id: Task A, target_id: Task B, relation: depends_on`).
  - Validates DAG cycle freedom; returns `400` if a cycle is created.
- `DELETE /api/v1/graph/edges/{edge_id}`
  - Remove relationship.

### 3.4 Verification & Evidence
- `POST /api/v1/tasks/{task_id}/evidence`
  - Submit completion evidence (`evidence_type`, `payload`, `notes`).
  - Automatically transitions task to `PENDING_VERIFICATION` and triggers verification evaluation.
- `GET /api/v1/tasks/{task_id}/evidence`
  - Retrieve evidence audit log with verification verdicts.
