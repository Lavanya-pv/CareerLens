"""Independent resume parsing entry point: PDF bytes to clean text, sections and skills."""
from dataclasses import dataclass

from careerlens.ingestion.pdf_reader import read_pdf
from careerlens.ingestion.text_cleaner import clean_text
from careerlens.parsing.section_parser import parse_sections
from careerlens.skills.extractor import extract_skills


@dataclass(frozen=True)
class ParsedResume:
    text: str
    page_count: int
    sections: dict[str, str]
    skills: list[dict]
    warning: str | None = None


def parse_resume_pdf(pdf_bytes: bytes) -> ParsedResume:
    """Parse a PDF in memory without Streamlit, database access or network requests."""
    pdf = read_pdf(pdf_bytes)
    text = clean_text(pdf.text)
    return ParsedResume(
        text=text,
        page_count=pdf.page_count,
        sections=parse_sections(text),
        skills=extract_skills(text),
        warning=pdf.warning,
    )
