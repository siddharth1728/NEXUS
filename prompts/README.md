# NEXUS: Prompt Engineering Architecture

This directory contains the canonical specifications, templates, and guidelines for all AI prompts utilized by the NEXUS platform and engineering agents.

---

## Directory Structure

```
/prompts
  ├── README.md                               # Prompt architecture index
  ├── /00-master                              # Master system prompts and constitution
  │   └── SYSTEM_PROMPT_CONSTITUTION.md
  ├── /01-architecture                        # Agent architectural design prompts
  │   └── ARCHITECT_GUIDELINES.md
  ├── /02-ai                                  # Pipeline stage prompts (Production AI engine)
  │   ├── EXTRACTION_SCHEMA_PROMPT.md         # Stage 3: Grounded Fact Extraction
  │   ├── ACTION_SYNTHESIS_PROMPT.md          # Stage 5: Action & Task Synthesis
  │   └── DEPENDENCY_ANALYSIS_PROMPT.md       # Stage 7: Dependency & Prerequisite Resolution
  ├── /03-build                               # Agent implementation task prompt templates
  │   └── TASK_PROMPT_TEMPLATE.md
  ├── /04-review                              # Quality & code review guidelines
  │   └── CODE_REVIEW_CHECKLIST.md
  └── /05-evaluation                          # Red-team & benchmark evaluation prompts
      └── RED_TEAM_EVALUATION_PROMPT.md
```

---

## Standard Prompt Specification Schema

Every production prompt template in NEXUS must define:
1. **Role & Identity:** Precise agent role and boundaries.
2. **Context Ingestion:** Explicit XML-delimited inputs (`<context>`, `<document_metadata>`, `<user_profile>`).
3. **Objective:** Clear, singular transformation goal.
4. **Constraints & Rules:** Strict negative and positive constraints (e.g., zero hallucination, verbatim citations).
5. **Output Schema:** JSON Schema definition matching the target Pydantic model.
6. **Error / Edge Case Handling:** What to output when data is ambiguous (`UNKNOWN`, `CONFLICT`).
7. **Stop Conditions & Max Retries:** Controlled termination logic.
