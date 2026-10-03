# 17. AUTONOMOUS EXECUTION & RELEASE SPECIFICATION

## 1. Executive Summary

NEXUS achieves controlled, trustworthy autonomy by adhering to the core principle:
> **AI Proposes. Application Validates. Domain Decides. Database Persists.**

The autonomous loop does not give generative models arbitrary execution privileges. Instead, actions are driven through deterministic risk tiers, capability boundaries, strict schema validation, policy engines, execution audit trails, and post-execution evidence verification.

---

## 2. Autonomy Architecture & Bounded Loop

The progression engine executes through a closed feedback loop:

```text
[ Action Graph: READY Actions ]
               │
               ▼
[ Risk Tier & Capability Resolution ]
               │
               ▼
[ Policy Engine Evaluation ] ─── DENY ───► [ Halt / Review ]
               │
          ALLOW / APPROVAL_REQUIRED
               │
               ▼
[ Execution Control Plane ] ─── REQUIRES_APPROVAL ───► [ Human Review Gate ]
               │
           AUTHORIZED
               │
               ▼
[ Tool Registry & Sandboxed Execution ]
               │
               ▼
[ Verification Engine: Evidence Gathering ]
               │
               ▼
[ Workflow Progress: Downstream Unlock ]
```

### Risk Tiers

| Risk Tier | Definition | Default Autonomous Policy |
| :--- | :--- | :--- |
| `READ_ONLY` | Read data, query repositories, calendar search, simulations | `ALLOW` |
| `LOW_RISK_MUTATION` | Create issues, draft emails, append comments | `ALLOW` in `AUTONOMOUS_WITHIN_POLICY` |
| `HIGH_RISK_MUTATION` | Send emails, mutate critical records, delete data | `REQUIRE_APPROVAL` |
| `SENSITIVE` | Financial, credential, or authorization mutations | `REQUIRE_APPROVAL` (Mandatory Human Gate) |

### Autonomy Modes

1. `MANUAL`: Every single execution request requires explicit human approval.
2. `ASSISTED`: Generates proposed execution requests with dry-run evaluation.
3. `APPROVAL_REQUIRED`: High/medium mutations require human signoff.
4. `AUTONOMOUS_WITHIN_POLICY`: Executes `READ_ONLY` and `LOW_RISK_MUTATION` automatically; gates `HIGH_RISK_MUTATION` and `SENSITIVE` for human approval.

---

## 3. Agent & Tool Delegation Bounds

1. **Explicit Capabilities**: Agents are assigned a strict, non-escalatable set of `Capability` enums.
2. **Tool Scope Enforcement**: An agent cannot invoke a tool whose capability exceeds the agent's registration.
3. **Pydantic Validation**: All tool parameters must strictly validate against the tool's schema before execution request generation.
4. **Idempotency**: Duplicate pending or active execution requests for the same action and tool are rejected.

---

## 4. Multi-Tenant & Credential Security Posture

1. **Tenant Isolation**:
   - Every database query and repository access is partitioned by `tenant_id`.
   - Client headers (`x-tenant-id`) cannot override server-verified JWT identities.
2. **Credential Boundary**:
   - Connector secrets and API tokens are never persisted in the primary database, Action records, Execution records, or logs.
   - Credentials reside solely in memory or secured secret stores and are injected only at the connector execution boundary.
3. **Prompt Injection Defense**:
   - Extracted document text is treated as untrusted input.
   - Domain models, entities, and actions are validated through strict JSON schema parsers before database ingestion.

---

## 5. Verification & Workflow Progress

Before an action transitions to `COMPLETED`:
1. The `VerificationEngine` gathers evidence using read-only inspection tools.
2. Assertions are matched deterministically against the expected outcome state.
3. Upon verified evidence, the `WorkflowEngine` unlocks dependent actions in the `ActionGraph`.
