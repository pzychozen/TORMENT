# torment_service/chunking.py
"""
Smart text chunking for TORMENT archive memory.

Splits long documents into semantically meaningful segments while preserving
section structure. Chunks go into the archive lane — never into core identity.

Design rules:
  - Target 250–450 tokens per chunk
  - Overlap 40–80 tokens when cutting mid-paragraph
  - Preserve section headers as metadata (section_path)
  - Never blindly cut every N tokens
  - Attach document and section context to each chunk
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------
def _estimate_tokens(text: str) -> int:
    """Rough token count (≈ words * 1.3 for English text)."""
    words = len(text.split())
    return max(1, int(words * 1.3))


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------
_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_UNDERLINE_H1 = re.compile(r"^(.+)\n={3,}$", re.MULTILINE)
_UNDERLINE_H2 = re.compile(r"^(.+)\n-{3,}$", re.MULTILINE)


@dataclass
class _Section:
    """A section of text with heading hierarchy."""
    level: int          # 1-6, 0 = root
    title: str          # section heading text
    content: str        # text content (excluding sub-section headings)
    path: List[str]     # full path: ["Chapter 1", "Setup", "Environment"]
    start_pos: int      # character position in original text


def _parse_sections(text: str) -> List[_Section]:
    """Parse markdown-style sections from text.

    Returns flat list of sections with their heading paths.
    If no headings found, returns the whole text as a single root section.
    """
    # Find all headings with positions
    headings: List[Tuple[int, int, str]] = []  # (pos, level, title)

    for m in _MD_HEADING.finditer(text):
        headings.append((m.start(), len(m.group(1)), m.group(2).strip()))

    for m in _UNDERLINE_H1.finditer(text):
        headings.append((m.start(), 1, m.group(1).strip()))

    for m in _UNDERLINE_H2.finditer(text):
        headings.append((m.start(), 2, m.group(1).strip()))

    headings.sort(key=lambda h: h[0])

    if not headings:
        return [_Section(level=0, title="", content=text.strip(),
                         path=[], start_pos=0)]

    sections: List[_Section] = []
    path_stack: List[Tuple[int, str]] = []  # (level, title)

    # Text before first heading
    pre = text[:headings[0][0]].strip()
    if pre:
        sections.append(_Section(level=0, title="", content=pre,
                                 path=[], start_pos=0))

    for i, (pos, level, title) in enumerate(headings):
        # Update path stack
        while path_stack and path_stack[-1][0] >= level:
            path_stack.pop()
        path_stack.append((level, title))
        path = [t for _, t in path_stack]

        # Extract content until next heading
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        # Skip the heading line itself
        heading_end = text.find("\n", pos)
        if heading_end == -1:
            heading_end = len(text)
        content = text[heading_end:end].strip()

        if content:
            sections.append(_Section(
                level=level, title=title, content=content,
                path=path, start_pos=pos,
            ))

    return sections


# ---------------------------------------------------------------------------
# Chunk dataclass
# ---------------------------------------------------------------------------
@dataclass
class TextChunk:
    """A single chunk from a document, ready for archive ingestion."""
    chunk_index: int
    text: str
    token_count: int
    section_path: List[str]
    section_title: str
    overlap_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core chunking logic
# ---------------------------------------------------------------------------
def _split_text_into_chunks(
    text: str,
    section_path: List[str],
    section_title: str,
    target_tokens: int = 350,
    min_tokens: int = 100,
    max_tokens: int = 500,
    overlap_tokens: int = 60,
    start_index: int = 0,
) -> List[TextChunk]:
    """Split a section's text into chunks at natural boundaries.

    Tries to split at paragraph breaks first, then sentence breaks,
    then word boundaries as a last resort.
    """
    text = text.strip()
    if not text:
        return []

    total = _estimate_tokens(text)
    if total <= max_tokens:
        return [TextChunk(
            chunk_index=start_index,
            text=text,
            token_count=total,
            section_path=list(section_path),
            section_title=section_title,
        )]

    # Split into paragraphs
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return [TextChunk(
            chunk_index=start_index,
            text=text,
            token_count=total,
            section_path=list(section_path),
            section_title=section_title,
        )]

    chunks: List[TextChunk] = []
    current_parts: List[str] = []
    current_tokens = 0
    idx = start_index

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)

        # If single paragraph exceeds max, split it by sentences
        if para_tokens > max_tokens:
            # Flush current buffer first
            if current_parts:
                chunk_text = "\n\n".join(current_parts)
                chunks.append(TextChunk(
                    chunk_index=idx,
                    text=chunk_text,
                    token_count=_estimate_tokens(chunk_text),
                    section_path=list(section_path),
                    section_title=section_title,
                ))
                idx += 1
                current_parts = []
                current_tokens = 0

            # Split long paragraph by sentences
            sentence_chunks = _split_by_sentences(
                para, section_path, section_title, target_tokens,
                min_tokens, max_tokens, overlap_tokens, idx,
            )
            chunks.extend(sentence_chunks)
            idx += len(sentence_chunks)
            continue

        # Would adding this paragraph exceed target?
        if current_tokens + para_tokens > target_tokens and current_parts:
            chunk_text = "\n\n".join(current_parts)
            chunks.append(TextChunk(
                chunk_index=idx,
                text=chunk_text,
                token_count=_estimate_tokens(chunk_text),
                section_path=list(section_path),
                section_title=section_title,
            ))
            idx += 1

            # Overlap: carry last paragraph into next chunk if it's short enough
            if overlap_tokens > 0 and current_parts:
                last_para = current_parts[-1]
                if _estimate_tokens(last_para) <= overlap_tokens:
                    current_parts = [last_para]
                    current_tokens = _estimate_tokens(last_para)
                else:
                    current_parts = []
                    current_tokens = 0
            else:
                current_parts = []
                current_tokens = 0

        current_parts.append(para)
        current_tokens += para_tokens

    # Flush remaining
    if current_parts:
        chunk_text = "\n\n".join(current_parts)
        ct = _estimate_tokens(chunk_text)
        # If too small and we have previous chunks, merge with last
        if ct < min_tokens and chunks:
            last = chunks[-1]
            merged = last.text + "\n\n" + chunk_text
            chunks[-1] = TextChunk(
                chunk_index=last.chunk_index,
                text=merged,
                token_count=_estimate_tokens(merged),
                section_path=list(section_path),
                section_title=section_title,
            )
        else:
            chunks.append(TextChunk(
                chunk_index=idx,
                text=chunk_text,
                token_count=ct,
                section_path=list(section_path),
                section_title=section_title,
            ))

    return chunks


def _split_by_sentences(
    text: str,
    section_path: List[str],
    section_title: str,
    target_tokens: int,
    min_tokens: int,
    max_tokens: int,
    overlap_tokens: int,
    start_index: int,
) -> List[TextChunk]:
    """Split text by sentence boundaries."""
    # Simple sentence splitting
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    chunks: List[TextChunk] = []
    current: List[str] = []
    current_tokens = 0
    idx = start_index

    for sent in sentences:
        sent_tokens = _estimate_tokens(sent)

        if current_tokens + sent_tokens > target_tokens and current:
            chunk_text = " ".join(current)
            chunks.append(TextChunk(
                chunk_index=idx,
                text=chunk_text,
                token_count=_estimate_tokens(chunk_text),
                section_path=list(section_path),
                section_title=section_title,
            ))
            idx += 1
            current = []
            current_tokens = 0

        current.append(sent)
        current_tokens += sent_tokens

    if current:
        chunk_text = " ".join(current)
        chunks.append(TextChunk(
            chunk_index=idx,
            text=chunk_text,
            token_count=_estimate_tokens(chunk_text),
            section_path=list(section_path),
            section_title=section_title,
        ))

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def chunk_text(
    text: str,
    *,
    target_tokens: int = 350,
    min_tokens: int = 100,
    max_tokens: int = 500,
    overlap_tokens: int = 60,
) -> List[TextChunk]:
    """Chunk a document into semantically meaningful segments.

    Preserves section structure from markdown headings.
    Each chunk carries its section_path for context.

    Args:
        text: Full document text
        target_tokens: Ideal chunk size (default 350)
        min_tokens: Minimum chunk size before merging (default 100)
        max_tokens: Maximum chunk size before splitting (default 500)
        overlap_tokens: Token overlap between adjacent chunks (default 60)

    Returns:
        List of TextChunk objects, each with text, section_path, and metadata.
    """
    if not text or not text.strip():
        return []

    sections = _parse_sections(text)
    all_chunks: List[TextChunk] = []
    idx = 0

    for section in sections:
        section_chunks = _split_text_into_chunks(
            section.content,
            section_path=section.path,
            section_title=section.title,
            target_tokens=target_tokens,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            start_index=idx,
        )
        all_chunks.extend(section_chunks)
        idx += len(section_chunks)

    # Re-index sequentially
    for i, chunk in enumerate(all_chunks):
        chunk.chunk_index = i

    return all_chunks


def chunk_text_plain(
    text: str,
    *,
    target_tokens: int = 350,
    max_tokens: int = 500,
    overlap_tokens: int = 60,
) -> List[TextChunk]:
    """Chunk plain text without section awareness.

    Use for non-structured text (raw transcripts, chat logs, etc.).
    """
    return _split_text_into_chunks(
        text,
        section_path=[],
        section_title="",
        target_tokens=target_tokens,
        min_tokens=50,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
    )
