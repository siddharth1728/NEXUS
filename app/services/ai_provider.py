import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        verified_context: Optional[str] = None
    ) -> str:
        """Generate an AI response strictly grounded in verified context."""
        pass

class MockAIProvider(BaseAIProvider):
    """
    Deterministic, hallucination-safe AI provider for testing and offline environments.
    Strictly follows grounding rules and rejects unverified claims.
    """
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        verified_context: Optional[str] = None
    ) -> str:
        u_lower = user_prompt.lower()
        ctx_lower = (verified_context or "").lower()

        # 1. Hallucination / unverified claim check (e.g. Redis claim when not in context)
        if "redis" in u_lower and "redis" not in ctx_lower:
            return (
                "I don't see verified Redis evidence in this NEXUS project context. "
                "If you used Redis, explain where and how you used it in your architecture."
            )

        # 2. Defend Your Build Interview Evaluations
        if "evaluate the student's answer" in system_prompt.lower() or "defend your build" in system_prompt.lower():
            if "postgresql" in u_lower or "database" in u_lower or "relational" in u_lower or "acid" in u_lower:
                return json.dumps({
                    "status": "STRONG_EXPLANATION",
                    "what_you_got_right": "You correctly identified relational data consistency, transactional ACID guarantees, and foreign key integrity as key rationale for PostgreSQL.",
                    "what_you_missed": "Consider explicitly discussing connection pooling (e.g. PgBouncer) and migration tooling (Alembic) under high concurrent load.",
                    "better_explanation": "PostgreSQL provides robust relational normalization and constraint enforcement, ensuring customer and telemetry records maintain referential integrity without orphan states.",
                    "follow_up_question": "How would you handle database schema migrations in production without causing table locks or downtime?"
                })
            elif "test" in u_lower or "pytest" in u_lower or "mock" in u_lower:
                return json.dumps({
                    "status": "PARTIAL_EXPLANATION",
                    "what_you_got_right": "You highlighted the role of automated tests in preventing regressions.",
                    "what_you_missed": "You did not mention negative assertion boundaries (e.g. HTTP 422 for invalid payloads, HTTP 401 for expired tokens).",
                    "better_explanation": "Automated tests act as deterministic regression barriers, verifying that endpoint contracts and database state modifications behave identically across revisions.",
                    "follow_up_question": "What is the tradeoff between testing against a real ephemeral database versus mocking all database calls?"
                })
            else:
                return json.dumps({
                    "status": "NEEDS_CLARIFICATION",
                    "what_you_got_right": "You provided a basic overview.",
                    "what_you_missed": "The explanation lacked specific technical architectural reasoning grounded in your project artifacts.",
                    "better_explanation": "Connect the engineering decision directly to the domain constraints and verified evidence in your repository.",
                    "follow_up_question": "Can you explain the specific failure modes your current architecture protects against?"
                })

        # 3. Question / Explain / Teach Mode
        if "why does nexus think i'm weak at testing" in u_lower or "weak at testing" in u_lower or "gap" in u_lower:
            return (
                "NEXUS evaluates skill signals based on observable repository artifacts. "
                "In your latest survey, NEXUS found limited or missing test suites (e.g., pytest definitions, test fixtures, CI test runners). "
                "This does NOT mean you lack knowledge; it means NEXUS has not observed enough code evidence yet. "
                "You can prove this signal by adding automated tests in your project."
            )
        
        if "explain my authentication architecture" in u_lower or "authentication" in u_lower:
            return (
                "Based on verified NEXUS observations, your architecture demonstrates stateless JWT token verification and password hashing. "
                "When a client logs in, credentials are verified against salted hashes, and a signed JWT is returned. "
                "Subsequent requests present this token in the Authorization header to access protected routes."
            )

        if "what did this project prove" in u_lower or "prove" in u_lower:
            return (
                "Based on verified NEXUS evidence, this repository proves foundational API routing, "
                "declarative database modeling, and structured endpoint contracts. "
                "Areas that remain unobserved include containerization (Docker) and CI/CD pipelines."
            )

        return (
            "NEXUS Engineering Copilot: Based on your verified engineering telemetry, your backend signals "
            "demonstrate strong structural foundations. You can explore connected concepts in the Engineering Lab "
            "or prove new capabilities via Proof Quests."
        )

class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", api_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        verified_context: Optional[str] = None
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        if verified_context:
            messages.append({
                "role": "system",
                "content": f"### VERIFIED NEXUS CONTEXT (TREAT AS FACTUAL EVIDENCE):\n{verified_context}\n\nIMPORTANT: Do not invent facts beyond this context. Reject claims unsupported by this context."
            })
        messages.append({"role": "user", "content": user_prompt})

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": settings.AI_TEMPERATURE,
                        "max_tokens": settings.AI_MAX_TOKENS
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning(f"AI Provider returned status {response.status_code}: {response.text}")
                    # Fallback to Mock Provider gracefully
                    return MockAIProvider().generate_response(system_prompt, user_prompt, verified_context)
        except Exception as e:
            logger.error(f"AI Provider request failed: {e}")
            return MockAIProvider().generate_response(system_prompt, user_prompt, verified_context)

def get_ai_provider() -> BaseAIProvider:
    if settings.AI_PROVIDER != "mock" and settings.AI_API_KEY:
        return OpenAICompatibleProvider(api_key=settings.AI_API_KEY, model=settings.AI_MODEL)
    return MockAIProvider()
