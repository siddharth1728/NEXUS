"""Mock Embedding Provider for isolated tests and deterministic retrieval."""
import hashlib

from app.core.ai.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Generates pseudo-random but deterministic vectors based on input text hash.
    Useful for testing retrieval engines without external calls.
    """

    def __init__(self, dimensions: int = 768) -> None:
        self._dimensions = dimensions

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return f"mock-embedding-{self._dimensions}"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _hash_to_vector(self, text: str) -> list[float]:
        """Convert text into a deterministic vector using repeated MD5 hashing."""
        base_hash = hashlib.md5(text.encode("utf-8")).digest()

        # We need `dimensions` floats. We can generate them by hashing the hash
        # repeatedly and taking bytes to floats.
        vector: list[float] = []
        current_hash = base_hash

        # Simplistic generation of a vector in range [-1.0, 1.0]
        # Just to ensure tests don't break with non-normalized vectors, we normalize it.
        while len(vector) < self._dimensions:
            current_hash = hashlib.md5(current_hash).digest()
            for b in current_hash:
                if len(vector) >= self._dimensions:
                    break
                # Convert byte to a float between -1.0 and 1.0
                val = (b / 127.5) - 1.0
                vector.append(val)

        # Normalize vector
        magnitude = sum(x*x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]
