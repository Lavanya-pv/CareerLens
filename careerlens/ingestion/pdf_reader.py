"""Reliable text extraction for uploaded PDF resume bytes using PyMuPDF."""
from dataclasses import dataclass


class PDFReadError(ValueError):
    """Raised when the uploaded bytes are not a readable PDF."""


@dataclass(frozen=True)
class PDFText:
    text: str
    page_count: int
    warning: str | None = None


def read_pdf(data: bytes) -> PDFText:
    """Extract page-ordered text; scanned/empty PDFs return a warning for OCR limits."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise PDFReadError("The uploaded PDF is empty. Choose a non-empty PDF file.")
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PDF support requires PyMuPDF. Install project requirements first.") from exc

    try:
        with pymupdf.open(stream=bytes(data), filetype="pdf") as document:
            if document.is_encrypted and not document.authenticate(""):
                raise PDFReadError("This PDF is password-protected. Upload an unlocked copy.")
            page_count = document.page_count
            if page_count == 0:
                raise PDFReadError("This PDF has no pages. Upload a PDF containing resume pages.")
            text = "\n\n".join(page.get_text("text", sort=True) for page in document)
    except PDFReadError:
        raise
    except Exception as exc:
        # PyMuPDF raises several exception types depending on the kind of corrupt input.
        raise PDFReadError("CareerLens could not read this PDF. Check that it is a valid, uncorrupted PDF and try again.") from exc

    warning = None
    if not text.strip():
        warning = "No selectable text was found. This PDF may be blank or scanned; OCR is not included."
    elif len(text.strip()) < 60:
        warning = "This PDF contains very little selectable text; it may be scanned. OCR is not included."
    return PDFText(text=text, page_count=page_count, warning=warning)
