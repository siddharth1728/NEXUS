# Contributing to NEXUS

First off, thank you for considering contributing to NEXUS! 

## Philosophy

NEXUS is built on a few core principles:
- **Action Graph First:** Relations are first-class citizens.
- **Provider-Agnostic AI:** Unified LLM adapter interface.
- **Never Invent Facts:** Missing evidence is `UNKNOWN`, conflicting information is `CONFLICT`.
- **Human-in-the-Loop:** Consequential actions require explicit human authorization.

Please ensure your contributions align with these principles and our [Engineering Constitution](docs/03_ENGINEERING_CONSTITUTION.md).

## Getting Started

1. **Fork the repository** and create your branch from `main`.
2. **Setup your environment:**
   - Python 3.11+
   - Node.js 20+
   - See the `README.md` for quickstart commands.
3. **Run tests:**
   - Backend: `uv run pytest tests/ --cov=app`
   - Frontend: `npm run lint` and `npm run build`

## Pull Request Process

1. Ensure the test suite passes and coverage remains >= 85%.
2. Update documentation if you are changing functionality.
3. Your code must pass all quality gates (Ruff, Mypy, ESLint).
4. A maintainer will review your PR.
