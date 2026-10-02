# NEXUS: Engineering Task Prompt Template

When formulating tasks for autonomous coding subagents or engineers, structure the prompt with this template:

```markdown
# TASK: [Short Imperative Task Title]

## Role
You are operating as [Backend Engineer | Frontend Engineer | AI Engineer | Security Engineer | QA Engineer].

## Phase
Target Implementation Phase: [e.g. Phase 01: Core Domain Engine]

## Objective
[Clear 1-2 sentence description of the exact deliverable.]

## Allowed Scope & Files
- Target files to create/modify: `[path/to/file.py]`
- Out of scope: [Explicitly forbidden files or systems]

## Input Contracts & Schemas
[Reference to Pydantic schemas, database models, or API endpoints]

## Constraints
1. Adhere to the Engineering Constitution ([docs/03_ENGINEERING_CONSTITUTION.md](file:///c:/NEXUS/docs/03_ENGINEERING_CONSTITUTION.md)).
2. Fully typed with zero implicit types.
3. Include unit tests in `tests/unit/`.
4. Do not invent or stub unapproved future-phase features.

## Acceptance Criteria
- [ ] AC 1: ...
- [ ] AC 2: ...
- [ ] AC 3: Unit test suite passes with 100% success.
```
