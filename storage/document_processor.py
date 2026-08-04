"""
RAGTUNE - Document Processing & Chunking Engine
Parses multi-format enterprise documents and creates semantic chunk embeddings.
"""

import json
import os
import re
from typing import Any

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_index: int
    token_count: int


class DocumentProcessor:
    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process_text(
        self,
        text: str,
        doc_id: str,
        title: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """
        Splits raw text into overlapping semantic chunks with metadata tracking.
        """
        if not text or not text.strip():
            return []

        # Split into paragraph / sentence chunks
        raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: list[DocumentChunk] = []
        chunk_idx = 0

        current_words: list[str] = []

        def commit_chunk(words_list: list[str]):
            nonlocal chunk_idx
            chunk_str = " ".join(words_list)
            c_id = f"{doc_id}_chunk_{chunk_idx}"
            chunks.append(
                DocumentChunk(
                    chunk_id=c_id,
                    doc_id=doc_id,
                    title=title,
                    content=chunk_str,
                    metadata=metadata or {},
                    chunk_index=chunk_idx,
                    token_count=len(words_list),
                )
            )
            chunk_idx += 1

        for para in raw_paragraphs:
            words = para.split()
            if len(current_words) + len(words) <= self.chunk_size:
                current_words.extend(words)
            else:
                if current_words:
                    commit_chunk(current_words)
                    # Keep overlap
                    current_words = (
                        current_words[-self.overlap :]
                        if self.overlap < len(current_words)
                        else []
                    )
                current_words.extend(words)

        if current_words:
            commit_chunk(current_words)

        return chunks

    def process_file(
        self, file_path: str, doc_id: str | None = None
    ) -> list[DocumentChunk]:
        """
        Processes a file on disk (txt, md, json, csv).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        filename = os.path.basename(file_path)
        d_id = doc_id or f"doc_{hash(filename) & 0xFFFFFFFF}"
        title = os.path.splitext(filename)[0].replace("_", " ").title()

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if ext == ".json":
            try:
                data = json.loads(content)
                content = json.dumps(data, indent=2)
            except Exception:
                pass

        return self.process_text(
            text=content,
            doc_id=d_id,
            title=title,
            metadata={"source_path": file_path, "file_type": ext},
        )
