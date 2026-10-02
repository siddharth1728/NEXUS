# NEXUS: AI Provider Gateway Architecture

**Document Version:** 1.0.0  
**Status:** Canonical Source of Truth  

---

## 1. Provider Architecture

NEXUS relies on a **Provider-Agnostic AI Gateway** located at `app/core/ai/gateway.py`. This ensures that business logic inside the application never interacts directly with provider-specific SDKs (e.g., `google-generativeai`, `huggingface_hub`, `ollama`).

Instead, the application depends on a unified interface:

```python
from app.core.ai import AIGateway, AIRequest

gateway = AIGateway()
response = await gateway.generate(AIRequest(
    provider="gemini", # Or "mock", "huggingface", "ollama"
    model="gemini-1.5-pro",
    prompt="Synthesize this task...",
))
print(response.content)
```

### Supported Providers
1. **Gemini**: REST API integration for `gemini-*` models.
2. **Hugging Face**: Serverless Inference API for open-source models.
3. **Ollama**: Local inference for models like `llama3` and `mistral`.
4. **Mock**: Deterministic memory-backed provider used exclusively for CI and unit testing.

---

## 2. Provider Configuration

Providers are configured via environment variables mapped to `app.core.config.AISettings`.

| Environment Variable | Description |
|---|---|
| `DEFAULT_LLM_PROVIDER` | Fallback provider if not specified in the request (default: `mock` or `gemini`). |
| `GEMINI_API_KEY` | Secret key for Google Gemini API. |
| `HUGGINGFACE_API_TOKEN` | Secret token for Hugging Face Inference API. |
| `OLLAMA_BASE_URL` | Host URL for local Ollama instance (default: `http://localhost:11434`). |

**Important Security Rule:** Never hardcode these credentials into the application. Use a `.env` file (see `.env.example`) and ensure `.env` remains in `.gitignore`.

---

## 3. Local Ollama Usage

To use local models via Ollama:
1. Ensure Ollama is installed and running (`ollama serve`).
2. Pull the desired model: `ollama pull llama3:8b`.
3. Set `OLLAMA_BASE_URL=http://localhost:11434` in your `.env`.
4. Submit requests with `provider="ollama"` and `model="llama3:8b"`.

---

## 4. Mock Provider Usage

The Mock Provider is mandatory for deterministic unit tests. It prevents network latency and hidden dependencies on live external services.

By default, tests should override the gateway request to use `provider="mock"`.
The mock provider can simulate errors, latency, and specific canned responses:

```python
provider = MockAIProvider()
provider.should_fail = True
provider.canned_response = "Controlled output for test"
```

---

## 5. Adding a New Provider

To add a new AI provider:
1. Create a new file in `app/core/ai/providers/myprovider.py`.
2. Implement the `app.core.ai.interfaces.AIProviderInterface`.
3. Use raw `httpx` to manage network calls with strict timeouts (e.g., `timeout=30.0`).
4. Catch `httpx.RequestError` and `httpx.TimeoutException`.
5. Raise normalized errors from `app.core.ai.errors` (e.g., `AITimeoutError`, `AIAuthenticationError`, `AIBadResponseError`).
6. Register the provider in `app.core.ai.gateway.AIGateway._providers`.

---

## 6. Running Tests

The test suite is fully isolated from live networks.

```bash
# Run unit and integration tests (mock providers only)
python -m pytest tests/unit/test_ai_providers.py tests/integration/test_ai_gateway.py -v

# Ensure full AI gateway coverage
python -m pytest --cov=app.core.ai --cov-report=term-missing
```

Do not write unit tests that require valid API keys. Real network requests belong strictly to separate E2E testing phases not executed during standard CI.
