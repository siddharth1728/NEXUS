"""Tests for Document Ingestion and Chunking."""

from pathlib import Path

import pytest

from app.core.document.parser import compute_file_hash
from app.core.document.simple_parser import SimpleTextParser


@pytest.mark.asyncio
@pytest.mark.unit
async def test_simple_text_parser_structural_chunking(tmp_path: Path) -> None:
    # 1. Create a sample markdown file
    md_content = """# Title

This is a paragraph.

- Item 1
- Item 2

## Subheading

Another paragraph.
"""
    test_file = tmp_path / "test.md"
    test_file.write_text(md_content, encoding="utf-8")

    # 2. Parse
    parser = SimpleTextParser()
    assert ".md" in parser.supported_extensions

    parsed = await parser.parse(test_file)

    # 3. Assertions
    assert parsed.sha256_hash == compute_file_hash(test_file)
    assert len(parsed.chunks) == 5

    chunk_0 = parsed.chunks[0]
    assert chunk_0.chunk_index == 0
    assert chunk_0.content == "# Title"
    assert chunk_0.structural_type == "heading"
    assert chunk_0.source_location.section == "Title"
    assert chunk_0.source_location.block_index == 0

    chunk_1 = parsed.chunks[1]
    assert chunk_1.content == "This is a paragraph."
    assert chunk_1.structural_type == "paragraph"
    assert chunk_1.source_location.section == "Title"  # Parent section is retained

    chunk_2 = parsed.chunks[2]
    assert "Item 1" in chunk_2.content
    assert chunk_2.structural_type == "list"

    chunk_3 = parsed.chunks[3]
    assert chunk_3.content == "## Subheading\n\nAnother paragraph." or chunk_3.content.startswith(
        "## Subheading"
    )

    # Wait, simple parser actually splits by double newline, so:
    # chunk_0: # Title
    # chunk_1: This is a paragraph.
    # chunk_2: - Item 1\n- Item 2
    # chunk_3: ## Subheading
    # chunk_4: Another paragraph.
    assert len(parsed.chunks) == 5
    assert parsed.chunks[3].structural_type == "heading"
    assert parsed.chunks[4].source_location.section == "Subheading"


@pytest.mark.unit
def test_compute_file_hash(tmp_path: Path) -> None:
    file_path = tmp_path / "hash_test.txt"
    file_path.write_bytes(b"deterministic content")

    hash1 = compute_file_hash(file_path)
    hash2 = compute_file_hash(file_path)

    assert hash1 == hash2
    assert len(hash1) == 64
