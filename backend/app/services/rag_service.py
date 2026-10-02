"""RAG Service for Grounded Generation."""
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest
from app.domain.context_builder import ContextBuilder, SourcePacket
from app.repositories.retrieval import BaseRetriever
from app.schemas.retrieval import RetrievalQuery


class CitationOutput(BaseModel):
    document_id: str
    chunk_id: str


class GroundedGenerationOutput(BaseModel):
    answer: str
    status: str
    citations: list[CitationOutput]
    conflict_description: str | None = None

    model_config = ConfigDict(extra="ignore")


class RAGService:
    """Orchestrates retrieval, context assembly, and grounded generation."""

    def __init__(self, ai_gateway: AIGateway, retriever: BaseRetriever) -> None:
        self.ai = ai_gateway
        self.retriever = retriever
        self.context_builder = ContextBuilder(max_tokens=8000)
        self.prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "02-ai" / "GROUNDED_GENERATION_PROMPT.md"

    async def answer_query(self, query: RetrievalQuery) -> GroundedGenerationOutput:
        """
        Retrieves context, builds the prompt, calls the AI Gateway,
        and validates citations.
        """
        # 1. Retrieve
        results = await self.retriever.retrieve(query)
        if not results:
            return GroundedGenerationOutput(
                answer="No relevant context found.",
                status="INSUFFICIENT_CONTEXT",
                citations=[]
            )

        # 2. Build Context
        context_string, packets = self.context_builder.build_context(results)

        # 3. Build AI Request
        system_instruction = self.prompt_path.read_text(encoding="utf-8")

        prompt = (
            f"User Query:\n{query.query}\n\n"
            f"Available Context:\n{context_string}"
        )

        request = AIRequest(
            provider="gemini",
            model="gemini-3.1-pro",
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.0,
            require_structured_output=True,
        )

        # 4. Generate
        response = await self.ai.generate(request)

        try:
            data = json.loads(response.content)
            output = GroundedGenerationOutput(**data)
        except (json.JSONDecodeError, ValueError):
            return GroundedGenerationOutput(
                answer="Failed to parse structured generation response.",
                status="ERROR",
                citations=[]
            )

        # 5. Citation Validation
        output = self._validate_citations(output, packets)

        return output

    def _validate_citations(
        self, output: GroundedGenerationOutput, packets: list[SourcePacket]
    ) -> GroundedGenerationOutput:
        """
        Validates that every citation returned by the model actually exists
        in the retrieved packets. Drops invalid citations.
        """
        valid_chunks = {p.chunk_id: p.document_id for p in packets}

        validated_citations = []
        for citation in output.citations:
            if citation.chunk_id in valid_chunks and valid_chunks[citation.chunk_id] == citation.document_id:
                validated_citations.append(citation)

        # Replace the citations with only the valid ones
        output.citations = validated_citations
        return output
