# ADR-003: Next.js with TypeScript & Tailwind CSS for Action Graph Frontend

**Status:** Accepted  
**Deciders:** Principal Architect  
**Date:** 2026-10-01  

---

## Context
NEXUS requires an interactive user interface to visualize DAG dependencies, review extracted actions side-by-side with source documents, manage approval gates, and inspect verification evidence.

## Decision
We select **Next.js 15+ (App Router)** with **TypeScript**, **React 19**, and **Tailwind CSS**.

## Rationale
- **Next.js & React 19:** Server components optimize initial load times and security, while client components provide rich stateful graph interactions.
- **TypeScript:** Strict type contracts aligned with backend OpenAPI schemas via automated client generation.
- **Tailwind CSS:** Enables a sleek, modern, dark-mode design system with responsive layouts and minimal bundle overhead.

## Consequences & Trade-offs
- **Positive:** Modern developer experience, robust ecosystem, rapid UI prototyping, support for streaming SSR.
- **Negative:** Full-stack Next.js deployment requires Node runtime or static export when decoupled from backend. In NEXUS, Next.js communicates with FastAPI via standard REST/SSE endpoints.
