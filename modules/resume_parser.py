"""Streamlit-upload-compatible, local PDF parsing interface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Protocol

from careerlens.ingestion.pdf_reader import PDFReadError
from careerlens.ingestion.resume_parser import parse_resume_pdf as _parse_bytes


class UploadedFileLike(Protocol):
    name: str
    def getvalue(self) -> bytes: ...


@dataclass(frozen=True)
class ResumeParseResult:
    text: str
    page_count: int
    sections: dict[str, str]
    skills: list[dict]
    warning: str | None = None


def _read_upload(uploaded_file: UploadedFileLike | BinaryIO | bytes | bytearray) -> bytes:
    """Read bytes from Streamlit UploadedFile, a binary file, or raw bytes."""
    if isinstance(uploaded_file, (bytes, bytearray)):
        return bytes(uploaded_file)
    getvalue = getattr(uploaded_file, "getvalue", None)
    if callable(getvalue):
        return getvalue()
    read = getattr(uploaded_file, "read", None)
    if callable(read):
        return read()
    raise TypeError("Expected a Streamlit UploadedFile, binary file, or PDF bytes.")


def parse_resume(uploaded_file: UploadedFileLike | BinaryIO | bytes | bytearray) -> ResumeParseResult:
    """Extract and clean all pages, retaining detected sections and skills.

    Empty/invalid/encrypted PDFs raise ``PDFReadError`` with a user-facing message.
    Scanned PDFs return an empty text value and an OCR warning.
    """
    parsed = _parse_bytes(_read_upload(uploaded_file))
    return ResumeParseResult(
        text=parsed.text,
        page_count=parsed.page_count,
        sections=parsed.sections,
        skills=parsed.skills,
        warning=parsed.warning,
    )


def extract_resume_text(uploaded_file: UploadedFileLike | BinaryIO | bytes | bytearray) -> str:
    """Convenience API returning only the clean extracted text."""
    return parse_resume(uploaded_file).text
