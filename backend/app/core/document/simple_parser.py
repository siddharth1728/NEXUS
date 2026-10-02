"""Simple Structural Parser for NEXUS."""

import re
from pathlib import Path

from app.core.document.parser import (
    DocumentLocation,
    DocumentParserInterface,
    NormalizedChunk,
    ParsedDocument,
    compute_file_hash,
)


class SimpleTextParser(DocumentParserInterface):
    """Deterministic structural parser for TXT and Markdown files."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".txt", ".md"}

    @property
    def parser_version(self) -> str:
        return "nexus-simple-text-v1"

    async def parse(self, file_path: Path, mime_type: str | None = None) -> ParsedDocument:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        file_hash = compute_file_hash(file_path)

        chunks: list[NormalizedChunk] = []

        # Simple deterministic structural chunking: split by double newlines (paragraphs/blocks)
        blocks = re.split(r"\n\s*\n", content.strip())

        current_section = "Root"

        for idx, block in enumerate(blocks):
            block = block.strip()
            if not block:
                continue

            # Naive heading detection (Markdown style)
            if block.startswith("#"):
                current_section = block.lstrip("#").strip()
                structural_type = "heading"
            elif block.startswith("- ") or block.startswith("* ") or re.match(r"^\d+\.", block):
                structural_type = "list"
            elif "|" in block and "-|-" in block:
                structural_type = "table"
            else:
                structural_type = "paragraph"

            # If a block is too large, we would perform secondary splitting here,
            # but for this simple parser we just assume blocks are reasonably sized.

            chunk = NormalizedChunk(
                chunk_index=len(chunks),
                content=block,
                structural_type=structural_type,
                source_location=DocumentLocation(section=current_section, block_index=idx),
                metadata={
                    "parser": self.parser_version,
                },
            )
            chunks.append(chunk)

        return ParsedDocument(
            chunks=chunks, sha256_hash=file_hash, metadata={"total_blocks": len(blocks)}
        )
