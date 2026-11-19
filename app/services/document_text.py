from __future__ import annotations

import io
import re
import zipfile

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def extract_text(raw_bytes: bytes, file_name: str | None, content_type: str | None) -> str:
    """Extract plain text from an uploaded PDF, DOCX, or text file."""
    name = (file_name or "").lower()
    ctype = (content_type or "").lower()

    if name.endswith(".pdf") or ctype == "application/pdf" or raw_bytes[:5] == b"%PDF-":
        return _extract_pdf(raw_bytes)
    if name.endswith(".docx") or "wordprocessingml" in ctype:
        return _extract_docx(raw_bytes)
    return raw_bytes.decode("utf-8", errors="replace")


def _extract_pdf(raw_bytes: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:  # pypdf raises several error types for malformed files
        raise ValueError("Could not read PDF file") from exc


def _extract_docx(raw_bytes: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError("Could not read DOCX file") from exc
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab/>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    return (
        text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
    )
