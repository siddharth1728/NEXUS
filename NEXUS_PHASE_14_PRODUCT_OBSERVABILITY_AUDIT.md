# NEXUS PHASE 14 PRODUCT OBSERVABILITY AUDIT

## 1. Objective
Ensure NEXUS is observable to answer critical questions about what students actually use, where they get stuck, what creates real value, and what causes them to return. The tracking mechanism is strictly purpose-limited, private, and aggregate-oriented, avoiding collection of sensitive data (passwords, tokens, source code, private AI conversations, database credentials).

## 2. Completed Architecture
- **Data Models**: Created `ProductEvent` and `ProductFeedback` to store analytics and user sentiment in the core database safely.
- **Telemetry Engine**: Added `app/services/telemetry_service.py` to support `record_event` and `record_feedback` synchronously, ensuring no data loss for critical flow stages.
- **Internal API Boundaries**: Added internal health endpoints secured strictly with `get_internal_user` dependency, ensuring that telemetry aggregates and health views are not accessible to public users.
- **Feature Flags**: Exposed flags via `/api/config/flags` based on settings toggles (`ENABLE_BETA_MODE`, `ENABLE_AI_COPILOT`, etc.) to safely observe product variations.

## 3. Emitted Event Funnel (Instrumentation Points)

### A. Lifecycle & Authorization
- `ACCOUNT_CREATED` - Triggers in `auth.py` when an account is established.
- `ONBOARDING_COMPLETED` - Triggers in `profile_service.py` upon initial profile data setup.
- `GITHUB_CONNECTED` - Triggers in `profile_service.py` when OAuth links successfully.

### B. Core Engineering Loop (The Flywheel)
- `SYNC_STARTED` - Triggers in `project_service.py` indicating intent to pull evidence.
- `SYNC_COMPLETED` - Triggers in `project_service.py` on successful completion.
- `SYNC_FAILED` - Triggers in `project_service.py` capturing systemic sync failures.
- `FIRST_SYNC_COMPLETED` - Captures the vital "First Activation" milestone.

### C. Technical Cartography & Navigation
- `ATLAS_VIEWED` - Client-side telemetry captured via `/api/telemetry/event` API when the Engineering Atlas renders.
- `PROJECT_INTELLIGENCE_VIEWED` - Triggers on the `/projects/{project_id}/intelligence` endpoint.

### D. Skill Action & Engineering Lab
- `QUEST_STARTED` - Triggers in `nba.py` when a Proof Quest is accepted.
- `QUEST_MARKED_COMPLETE` - Triggers when the user clicks 'Mark Complete'.
- `QUEST_VERIFIED` - Triggers upon successful state gap closure via the `nba_engine.py` validation.
- `LAB_ACTIVITY_COMPLETED` - Triggers via backend detail retrieval for lab discovery exploration.

### E. Social / Ecosystem
- `NEXUS_ID_CREATED` - Logs adoption of stable identifiers.
- `PUBLIC_PROFILE_ENABLED` - Indicates willingness to expose skill vectors.
- `REVIEW_LINK_CREATED` - Observes usage of artifact sharing.
- `MENTOR_INVITED` / `MENTOR_ACCEPTED` - Tracks the growth of the learning mesh.

### F. AI Copilot Integration
- `COPILOT_STARTED` - Validates adoption of the contextual chat engine.
- `DEFEND_BUILD_STARTED` - Highlights initiation of active defense.
- `DEFEND_BUILD_COMPLETED` - Proves endurance through the interview session.
- `AI_FAILURE` - Pinpoints breakdown instances to safeguard reliability.

## 4. Privacy & Compliance Check
- **No Sensitive Exfiltration**: The instrumentation intercepts only routing edges and boolean state toggles. `context_data` only includes `project_id`, `concept_key`, or `session_id`, leaving out query texts, tokens, or PII.
- **No Third-Party Brokers**: Built directly into internal PostgreSQL models. Data does not leave the boundary.

## 5. Status
**STATUS**: PASS. Phase 14 Observability is safely integrated and recording accurately.
