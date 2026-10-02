"""NEXUS Document Parsing Abstraction."""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DocumentLocation(BaseModel):
    """Normalized source location."""

    page_number: int | None = None
    section: str | None = None
    block_index: int | None = None


class NormalizedChunk(BaseModel):
    """A structural chunk extracted from a document."""

    chunk_index: int
    content: str
    structural_type: str
    source_location: DocumentLocation
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    """Fully parsed and normalized document representation."""

    chunks: list[NormalizedChunk]
    metadata: dict[str, Any] = Field(default_factory=dict)
    sha256_hash: str


class DocumentParserInterface(ABC):
    """Abstract interface for document parsers."""

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Extensions supported by this parser (e.g. {'.txt', '.md'})."""
        pass

    @property
    @abstractmethod
    def parser_version(self) -> str:
        """Version of the parser."""
        pass

    @abstractmethod
    async def parse(self, file_path: Path, mime_type: str | None = None) -> ParsedDocument:
        """Parse a document into normalized chunks."""
        pass


def compute_file_hash(file_path: Path) -> str:
    """Compute deterministic SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in 64kb chunks
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()
