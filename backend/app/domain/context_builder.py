"""RAG Context Builder."""
import uuid
from typing import Any

from pydantic import BaseModel

from app.schemas.retrieval import RetrievalResult


class SourcePacket(BaseModel):
    """A structured representation of a context source sent to the LLM."""

    document_id: str
    chunk_id: str
    location: dict[str, Any]
    content: str

    def format_for_prompt(self, index: int) -> str:
        """Format the source packet into a distinct, boundary-marked string."""
        return (
            f"--- SOURCE {index} ---\n"
            f"document_id: {self.document_id}\n"
            f"chunk_id: {self.chunk_id}\n"
            f"location: {self.location}\n"
            f"CONTENT:\n{self.content}\n"
            f"--- END SOURCE {index} ---\n"
        )


class ContextBuilder:
    """Assembles retrieved chunks into LLM-ready context packets."""

    def __init__(self, max_tokens: int = 8000) -> None:
        self.max_tokens = max_tokens

    def build_context(self, results: list[RetrievalResult]) -> tuple[str, list[SourcePacket]]:
        """
        Deduplicate, order, and assemble retrieval results into a single context string
        and a list of source packets.
        """
        # Deduplicate while preserving order (assuming results are pre-sorted by rank)
        seen: set[uuid.UUID] = set()
        unique_results = []
        for r in results:
            if r.chunk_id not in seen:
                seen.add(r.chunk_id)
                unique_results.append(r)

        # Build packets
        packets = []
        # Simplistic token estimation: ~4 chars per token
        current_tokens = 0

        for r in unique_results:
            estimated_tokens = len(r.content) // 4
            if current_tokens + estimated_tokens > self.max_tokens:
                # We reached budget.
                # (We could truncate the string here, but full chunk integrity is preferred)
                break

            packet = SourcePacket(
                document_id=str(r.document_id),
                chunk_id=str(r.chunk_id),
                location=r.source_location,
                content=r.content
            )
            packets.append(packet)
            current_tokens += estimated_tokens

        # Assemble string
        context_string = "\n".join([p.format_for_prompt(i + 1) for i, p in enumerate(packets)])
        return context_string, packets
