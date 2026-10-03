from __future__ import annotations

import io
from dataclasses import dataclass, field

from pypdf import PdfReader


@dataclass
class ExtractedDocument:
    pages: list[dict] = field(default_factory=list)
    full_text: str = ""
    warning: str | None = None


class DocumentExtractionTool:
    """Reads a PDF and extracts text, preserving page boundaries where possible.

    Never raises on a bad PDF: extraction failures are captured as a warning so
    that one bad supplier document does not crash the whole evaluation batch.
    """

    def extract(self, file_bytes: bytes) -> ExtractedDocument:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
        except Exception as exc:  # noqa: BLE001 - any parser failure must be contained
            return ExtractedDocument(warning=f"Failed to open PDF: {exc}")

        pages: list[dict] = []
        text_parts: list[str] = []

        for i, page in enumerate(reader.pages, start=1):
            try:
                raw_text = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                pages.append({"page_number": i, "text": "", "warning": f"Extraction failed: {exc}"})
                continue
            cleaned = _clean_text(raw_text)
            pages.append({"page_number": i, "text": cleaned})
            if cleaned:
                text_parts.append(cleaned)

        full_text = "\n\n".join(text_parts).strip()
        warning = None
        if not full_text:
            warning = "No extractable text found in PDF (it may be empty, corrupt, or scanned/image-based)."

        return ExtractedDocument(pages=pages, full_text=full_text, warning=warning)


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
