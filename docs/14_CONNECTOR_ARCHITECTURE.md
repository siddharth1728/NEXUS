# NEXUS — Connector Architecture

## Overview

This document describes the Connector SDK introduced in Phase 02C, which provides the first real external integration for NEXUS — the GitHub connector.

The architecture enforces the canonical execution path:

```
ACTION
↓ EXECUTION REQUEST
↓ AUTHENTICATION (JWT → tenant_id)
↓ TENANT CONTEXT
↓ CAPABILITY (enum-typed, strict)
↓ POLICY ENGINE (deterministic, no LLM)
↓ APPROVAL (if REQUIRE_APPROVAL)
↓ CONNECTOR (external boundary)
↓ EXTERNAL API
↓ NORMALIZED RESULT
↓ VERIFICATION HOOK
```

No connector may bypass any layer.

---

## Concepts

### Connector

A `Connector` represents an external system integration. It owns:

- Provider identity
- Authentication (credential retrieval from SecretStore)
- HTTP client lifecycle (timeouts, headers)
- Error normalization
- Health checks

A connector does **not** own the NEXUS policy decision or tenant authorization. Those remain in the application control plane.

### Tool

A `Tool` represents a specific executable capability exposed through a connector. It owns:

- Strict Pydantic input schema
- Capability declaration
- NEXUS execution wiring

Tools call connectors. Connectors call external APIs.

**One connector** may expose **multiple tools**.

### Connection

A `Connection` binds a **tenant** (and optionally a user) to an external provider. It tracks:

- `provider` — the system identifier (e.g., `"github"`)
- `tenant_id` — strict tenant ownership
- `status` — `AVAILABLE | UNAVAILABLE | AUTHENTICATION_REQUIRED`
- `connection_metadata` — non-secret routing info

Credentials are **never stored in Connection** records. They are stored in the `SecretStore`.

---

## ConnectorRegistry

```python
from app.core.execution.connectors import connector_registry

connector_registry.register(GitHubConnector())
connector = connector_registry.get("github")
```

- Explicit registration only. No dynamic imports from user input.
- `list_all()` returns all registered connectors.
- `clear()` for test isolation.

---

## SecretStore

The `SecretStore` is the explicit credential boundary:

```python
from app.core.secrets import secret_store

token = secret_store.get_secret(f"GITHUB_{tenant_id}_TOKEN")
```

### Rules

| Prohibited | Required |
|-----------|---------|
| Tokens in Action records | Tokens in SecretStore only |
| Tokens in ExecutionRecord parameters | Credentials retrieved by connector, not tools |
| Tokens in prompts or logs | Secret key encodes tenant_id |
| Tokens in API responses | Credential not returned to caller |

In Phase 02C, the SecretStore reads from in-memory mock (tests) or environment variables (local dev). A cloud secret manager (e.g., GCP Secret Manager) will replace this in a later phase.

---

## GitHub Connector

### Supported Capabilities

| Capability | Type | Policy |
|-----------|------|--------|
| `GITHUB_REPOSITORY_READ` | Read | `ALLOW` |
| `GITHUB_ISSUE_READ` | Read | `ALLOW` |
| `GITHUB_ISSUE_CREATE` | Mutation | `REQUIRE_APPROVAL` |
| `GITHUB_ISSUE_COMMENT_CREATE` | Mutation | `REQUIRE_APPROVAL` |

### Credential Key Format

```
GITHUB_{tenant_id}_TOKEN
```

This means Tenant A's token cannot resolve to Tenant B's connection.

### HTTP Client

- Bounded timeout: `10s` total, `5s` connect
- Safe error normalization
- No raw GitHub response bodies exposed
- B904-compliant exception chaining

### Error Normalization

| GitHub HTTP Status | NEXUS Error |
|-------------------|-------------|
| 401 | `UnauthorizedError` |
| 403 (rate limit) | `GitHubError` |
| 403 (forbidden) | `ForbiddenError` |
| 404 | `NotFoundError` |
| 422 | `ValidationError` |
| 5xx | `GitHubError` (upstream failure) |
| `ConnectError` | `GitHubError` (connection failure) |

---

## Tools

### `GitHubRepositoryReadTool` (`github_repository_read_v1`)

**Input schema:** `GitHubRepositoryInput`

| Field | Type | Required |
|-------|------|---------|
| `owner` | str | ✓ |
| `repository` | str | ✓ |

**Returns:** Normalized repository info (id, url, visibility, default_branch).

### `GitHubIssueReadTool` (`github_issue_read_v1`)

**Input schema:** `GitHubIssueReadInput`

| Field | Type | Required |
|-------|------|---------|
| `owner` | str | ✓ |
| `repository` | str | ✓ |
| `issue_number` | int | ✓ |

**Returns:** Normalized issue info (number, title, state, url, author).

### `GitHubIssueCreateTool` (`github_issue_create_v1`)

**Input schema:** `GitHubIssueCreateInput`

| Field | Type | Required |
|-------|------|---------|
| `owner` | str | ✓ |
| `repository` | str | ✓ |
| `title` | str | ✓ |
| `body` | str | ✓ |

**Policy:** `REQUIRE_APPROVAL` — No GitHub request is made until approval.

**Returns:** Normalized issue creation result (resource_id, issue_number, url).

### `GitHubCommentCreateTool` (`github_comment_create_v1`)

**Input schema:** `GitHubCommentCreateInput`

| Field | Type | Required |
|-------|------|---------|
| `owner` | str | ✓ |
| `repository` | str | ✓ |
| `issue_number` | int | ✓ |
| `body` | str | ✓ |

**Policy:** `REQUIRE_APPROVAL` — No GitHub request is made until approval.

---

## NEXUS Authorization vs. GitHub Authorization

Both layers are required before execution:

```
NEXUS policy: ALLOW
AND
GitHub credential: authorized for this repository
↓
EXECUTE
```

NEXUS authorization is controlled by the `PolicyEngine`. GitHub authorization is enforced by the GitHub API (401/403 responses) which are normalized and surfaced as NEXUS errors.

---

## Idempotency

Duplicate execution requests for the same `(action_id, tool_id)` in a non-terminal state are rejected:

```
PENDING | AWAITING_APPROVAL | AUTHORIZED | RUNNING | SUCCEEDED
→ ValueError("Idempotency violation")
```

This prevents duplicate GitHub issue creation from:
- Double-clicks
- Retry storms
- Concurrent agent calls

---

## Dry Run

All GitHub mutation tools support dry-run evaluation:

```json
{
  "status": "dry_run",
  "provider": "github",
  "capability": "GITHUB_ISSUE_CREATE",
  "target": {"owner": "...", "repository": "...", "title": "...", "body": "..."},
  "approval_required": true,
  "message": "Dry run succeeded. No external request made."
}
```

No GitHub API request is made during dry run.

---

## Audit Trail

Every `ExecutionRecord` stores:

| Field | Content |
|-------|---------|
| `tenant_id` | Authenticated tenant |
| `requester_id` | Requesting user |
| `agent_id` | Agent that initiated |
| `capability` | e.g., `GITHUB_ISSUE_CREATE` |
| `tool_id` | e.g., `github_issue_create_v1` |
| `parameters` | Validated, normalized inputs (no secrets) |
| `state` | Full lifecycle |
| `policy_decision` | `ALLOW / DENY / REQUIRE_APPROVAL` |
| `approval_decision` | `APPROVED / REJECTED` |
| `approver_id` | Who approved |
| `result_payload` | Normalized result (no secrets) |

---

## Verification Hook

The `result_payload` from GitHub tools contains enough metadata to wire into a future `VerificationEngine`:

```json
{
  "resource_type": "issue",
  "resource_id": "12345",
  "owner": "acme",
  "repository": "my-repo",
  "issue_number": 42,
  "url": "https://github.com/acme/my-repo/issues/42"
}
```

A verifier can later confirm: issue exists, title matches, body matches expected content.

---

## Security Boundaries

| Threat | Mitigation |
|-------|-----------|
| Cross-tenant credential access | Credential key includes `tenant_id`; Tenant A's key cannot resolve Tenant B's token |
| Token in execution result | Tokens retrieved by connector only; never stored in `result_payload` |
| Token in logs | `SecretStore.get_secret()` is the only retrieval point; logging must not capture return value |
| Parameter injection | Strict Pydantic schemas reject extra fields and type mismatches |
| Prompt injection → execution | Full control plane still required: Action → Request → Policy → Approval → Connector |
| Tool output injection | GitHub responses treated as untrusted external data; not re-interpreted as commands |
| Approval bypass | `ExecutionService.execute()` checks `state == AUTHORIZED` before proceeding |
| Duplicate mutation | Idempotency check rejects duplicate `(action_id, tool_id)` in non-terminal states |
| Replay attack | `ExecutionRecord.id` is UUID; stale record IDs return 404 |
