"""Base interfaces for embedding providers."""
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for embedding generation."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the embedding model."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Number of dimensions the model outputs."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts.
        Returns a list of vectors corresponding to the input texts.
        """
        pass

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        results = await self.embed_texts([text])
        return results[0]
