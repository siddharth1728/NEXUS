# ADR-004: Provider-Agnostic AI Layer with Native Structured Output

**Status:** Accepted  
**Deciders:** Principal Architect  
**Date:** 2026-10-01  

---

## Context
NEXUS requires LLM capabilities across multiple stages: document classification, fact extraction, action synthesis, and dependency analysis. We must avoid vendor lock-in to any single AI provider (e.g. Gemini, OpenAI, Anthropic, or local open-source models like LLaMA via Ollama).

## Decision
We implement a lightweight, custom **`LLMProvider` abstraction interface** in the backend core rather than adopting heavyweight framework wrappers (e.g., LangChain).

```
LLMProvider (Base Abstract Class)
 ├── GeminiProvider (Google Generative AI)
 ├── OllamaProvider (Local LLaMA 3, Mistral, Qwen)
 ├── HuggingFaceProvider (Inference API / Local TGI)
 └── OpenAICompatibleProvider (vLLM, OpenAI, Groq)
```

## Rationale
- **Direct Control:** Guarantees strict adherence to our structured output validation (Pydantic v2 schemas) and error handling.
- **No Dependency Churn:** Eliminates external framework breaking changes and unnecessary abstractions.
- **Multi-Environment Flexibility:** Developers can run entirely offline using Ollama, or deploy in cloud using Gemini 1.5 Pro/Flash.

## Consequences & Trade-offs
- **Positive:** Clean architecture, unified telemetry hooks (Langfuse), zero proprietary lock-in.
- **Negative:** Provider-specific edge features (e.g., specific caching or tools APIs) must be normalized across our adapter methods.
