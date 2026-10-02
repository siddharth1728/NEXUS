# NEXUS — Verification and Workflow Intelligence

## 1. Domain Models
- **EvidenceRequirement**: Deterministic requirements defining what evidence must be gathered to verify an Action's completion. Includes the expected tool/connector, required parameters, and the expected state (JSON object).
- **Evidence**: The cryptographically or deterministically sourced proof payload obtained from an external system that evaluates the EvidenceRequirement. Tracks provenance and the execution record.

## 2. Status Transitions
`ActionStatus` has been extended with the following verification states:
- `VERIFIED`: The Evidence successfully matched the EvidenceRequirement's assertions.
- `NOT_VERIFIED`: The Evidence failed to match the assertions.
- `REQUIRES_REVIEW`: The system requires human intervention due to ambiguity or a failed verification that should not automatically revert an action state to `FAILED`.

## 3. Workflow Progression
The `WorkflowEngine` observes state changes across the Action Graph.
When an Action is marked as `VERIFIED`:
1. It is considered a terminal success state for dependency evaluation.
2. The engine evaluates all dependent Actions (edges where the verified action is the target).
3. If all dependencies of a dependent action are `VERIFIED` or `COMPLETED`, the dependent action is unblocked and transitions to `READY`.

## 4. Verification Engine
The `VerificationService` orchestrates the deterministic checks. It executes read-only tools through the Tool Registry (e.g. `github_tools.py` reading an issue status), and asserts that the `result_payload` matches the expected state.
