# NEXUS — Frontend Architecture

## 1. Overview
The NEXUS frontend is a Next.js 15+ (App Router) application written in TypeScript and styled with Tailwind CSS v4. It serves as the primary visual interface for the NEXUS Context-to-Action Engine.

## 2. Design Philosophy
- **Context over decoration:** We do not use arbitrary colors or gradients. UI elements are dense, functional, and focus on the provenance of actions.
- **Backend as Authoritative:** The frontend does not make authorization decisions, synthesize actions, or verify results. It faithfully renders the state returned by the `/api/v1` backend endpoints.
- **Status Consistency:** We map `ActionStatus` and `ExecutionState` to semantic colors (`success`, `warning`, `danger`, `info`, `accent`) across the entire application to ensure cognitive consistency.

## 3. Key Experiences
- **Dashboard:** High-level metrics showing what needs attention.
- **Action Center:** Searchable, filterable list of all proposed, running, or verified actions.
- **Action Detail:** Visualizes the relationship between Source -> Context -> Action -> Execution -> Verification. Includes upstream dependencies and downstream blockers.
- **Execution Center & Approval:** Lists execution requests. Displays critical `AWAITING_APPROVAL` states where humans must intervene before connector mutation.
- **Documents:** Source of truth vault showing ingested knowledge.

## 4. Technology Stack
- Next.js (App Router, Turbopack)
- React Server Components / Client Components
- Tailwind CSS v4
- Lucide React (Icons)
- TypeScript

## 5. Security & Isolation
- **Tenant Context:** Hardcoded to `dev-tenant` for Phase 02, but architecturally designed to pass `x-tenant-id` securely to the backend on every request.
- **Approvals:** Does not execute mutations directly. Submits `APPROVED` or `REJECTED` state transitions back to the Execution Service for processing.

## 6. Real Data
All views are wired up directly to the backend Pydantic schemas via the generic API wrapper. We do not use mock payloads or fabricate metrics.
