# NEXUS: Code Review Checklist

Reviewers (human or agent) must evaluate all proposed code changes against this checklist before merging:

- [ ] **Phase Alignment:** Does this change belong strictly to the currently active phase?
- [ ] **Engineering Constitution:** Does this change respect Principles A through J?
- [ ] **Contract-First:** Are all inputs and outputs validated via Pydantic or TypeScript schemas?
- [ ] **Zero Hallucination Guardrails:** Are fallback statuses (`UNKNOWN`, `CONFLICT`, `REQUIRES_REVIEW`) properly propagated?
- [ ] **Deterministic Security:** Are authorization checks performed in application code, never delegated to LLM output?
- [ ] **Async & Performance:** Are database queries and network calls non-blocking and index-optimized?
- [ ] **Test Coverage:** Are unit/integration tests included, and do all tests pass?
- [ ] **No Dead Code / Hardcoded Secrets:** No commented blocks, no debug prints, no committed keys.
