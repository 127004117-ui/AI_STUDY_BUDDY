"""
In-memory document store with text extraction helpers.
Supports PDF (built-in fallback), TXT, and Markdown uploads.
No external dependencies required for basic operation.
"""

import uuid
import io
import re
import struct
import zlib
from typing import Dict, Optional

# ── Optional heavy deps (used if installed, gracefully skipped otherwise) ─────

try:
    import pdfplumber
    _PDFPLUMBER = True
except ImportError:
    _PDFPLUMBER = False

try:
    import markdown as _md
    _MARKDOWN = True
except ImportError:
    _MARKDOWN = False


# ── In-memory store ───────────────────────────────────────────────────────────
_STORE: Dict[str, dict] = {}


# ── PDF text extraction (pure-Python fallback) ────────────────────────────────

def _extract_pdf_builtin(data: bytes) -> str:
    """
    Minimal pure-Python PDF text extractor.
    Handles most text-based PDFs without any external library.
    Extracts raw text from PDF stream objects.
    """
    text_parts = []

    try:
        content = data.decode("latin-1", errors="replace")

        # Try to find BT...ET blocks (PDF text blocks)
        bt_blocks = re.findall(r'BT(.*?)ET', content, re.DOTALL)
        for block in bt_blocks:
            # Extract text from Tj, TJ, ' and " operators
            strings = re.findall(r'\(((?:[^()\\]|\\.)*)\)\s*(?:Tj|\'|")', block)
            strings += re.findall(r'\[((?:[^\[\]]|\\.)*)\]\s*TJ', block)
            for s in strings:
                # Unescape PDF string escapes
                s = re.sub(r'\\n', '\n', s)
                s = re.sub(r'\\r', '\r', s)
                s = re.sub(r'\\t', '\t', s)
                s = re.sub(r'\\(.)', r'\1', s)
                # Filter out non-printable garbage
                clean = ''.join(c for c in s if c.isprintable() or c in '\n\r\t ')
                if clean.strip():
                    text_parts.append(clean)

        # Also try to decompress FlateDecode streams
        stream_pattern = re.compile(
            r'<<[^>]*?/Filter\s*/FlateDecode[^>]*?>>\s*stream\r?\n(.*?)\r?\nendstream',
            re.DOTALL
        )
        for match in stream_pattern.finditer(content):
            raw = match.group(1).encode("latin-1", errors="replace")
            try:
                decompressed = zlib.decompress(raw).decode("latin-1", errors="replace")
                # Pull text from decompressed stream
                sub_strings = re.findall(r'\(((?:[^()\\]|\\.)*)\)\s*(?:Tj|\'|")', decompressed)
                for s in sub_strings:
                    s = re.sub(r'\\(.)', r'\1', s)
                    clean = ''.join(c for c in s if c.isprintable() or c in '\n\r\t ')
                    if clean.strip():
                        text_parts.append(clean)
            except Exception:
                pass

    except Exception:
        pass

    result = " ".join(text_parts)
    # Collapse excessive whitespace
    result = re.sub(r'[ \t]{3,}', '  ', result)
    result = re.sub(r'\n{4,}', '\n\n', result)
    return result.strip()


# ── Main extraction function ──────────────────────────────────────────────────

def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Extract plain text from uploaded bytes based on filename extension.
    Always succeeds — falls back gracefully for every format.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    # ── PDF ──────────────────────────────────────────────────────────────────
    if ext == "pdf":
        # Try pdfplumber first (best quality)
        if _PDFPLUMBER:
            try:
                text_parts = []
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                result = "\n".join(text_parts)
                if result.strip():
                    return result
            except Exception:
                pass

        # Pure-Python fallback
        result = _extract_pdf_builtin(file_bytes)
        if result.strip():
            return result

        # Last resort: raw byte scan for readable ASCII
        raw = file_bytes.decode("latin-1", errors="replace")
        words = re.findall(r'[A-Za-z][A-Za-z0-9 ,.\-:;\'\"!?]{3,}', raw)
        return " ".join(words[:2000]) or "Could not extract text from this PDF."

    # ── Markdown ─────────────────────────────────────────────────────────────
    if ext in ("md", "markdown"):
        raw = file_bytes.decode("utf-8", errors="replace")
        if _MARKDOWN:
            try:
                html = _md.markdown(raw)
                return re.sub(r"<[^>]+>", " ", html)
            except Exception:
                pass
        # Fallback: strip markdown syntax manually
        text = re.sub(r'#{1,6}\s*', '', raw)       # headings
        text = re.sub(r'\*\*?|__?', '', text)       # bold/italic
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
        text = re.sub(r'`+', '', text)               # code
        return text.strip()

    # ── Plain text (TXT or anything else) ────────────────────────────────────
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_bytes.decode("utf-8", errors="replace")


# ── Store operations ──────────────────────────────────────────────────────────

def store_document(filename: str, text: str) -> str:
    """Save extracted text and return a new doc_id."""
    doc_id = str(uuid.uuid4())[:8]
    _STORE[doc_id] = {"filename": filename, "text": text}
    return doc_id


def get_document(doc_id: str) -> Optional[dict]:
    """Return stored document dict or None."""
    return _STORE.get(doc_id)


def list_documents() -> list:
    """Return metadata list for all stored documents."""
    result = []
    for doc_id, doc in _STORE.items():
        text = doc["text"]
        result.append({
            "doc_id": doc_id,
            "filename": doc["filename"],
            "content_preview": text[:200].replace("\n", " "),
            "word_count": len(text.split()),
        })
    return result


def delete_document(doc_id: str) -> bool:
    """Remove document from store. Returns True if found."""
    if doc_id in _STORE:
        del _STORE[doc_id]
        return True
    return False
