"""Independent parser tests; PDFs are generated in memory and contain no personal data."""
import unittest

import pymupdf

from careerlens.ingestion.pdf_reader import PDFReadError, read_pdf
from careerlens.ingestion.resume_parser import parse_resume_pdf
from modules.resume_parser import extract_resume_text, parse_resume


def make_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    result = document.tobytes()
    document.close()
    return result


class ResumeParserTests(unittest.TestCase):
    class Upload:
        name = "resume.pdf"
        def __init__(self, data): self._data = data
        def getvalue(self): return self._data

    def test_streamlit_upload_like_object_is_accepted(self):
        result = parse_resume(self.Upload(make_pdf("SKILLS\\nPython")))
        self.assertIn("Python", result.text)
        self.assertEqual(result.page_count, 1)

    def test_extract_text_helper_returns_clean_string(self):
        text = extract_resume_text(self.Upload(make_pdf("EXPERIENCE\\nBuilt services")))
        self.assertIn("Built services", text)

    def test_multipage_pdf_combines_all_pages(self):
        document = pymupdf.open()
        for content in ("PAGE ONE SKILLS Python", "PAGE TWO EXPERIENCE SQL"):
            page = document.new_page()
            page.insert_text((72, 72), content)
        data = document.tobytes()
        document.close()
        result = parse_resume(self.Upload(data))
        self.assertEqual(result.page_count, 2)
        self.assertIn("PAGE ONE", result.text)
        self.assertIn("PAGE TWO", result.text)

    def test_invalid_upload_has_clear_pdf_error(self):
        with self.assertRaisesRegex(PDFReadError, "could not read"):
            parse_resume(self.Upload(b"not a pdf"))

    def test_scanned_or_blank_pdf_returns_extraction_warning(self):
        result = parse_resume(self.Upload(make_pdf("")))
        self.assertEqual(result.text, "")
        self.assertTrue(result.warning)

    def test_three_resume_shapes_return_clean_sections_and_skills(self):
        samples = [
            "Alex Example\nSUMMARY\nBackend engineer\nWORK EXPERIENCE\nBuilt Python APIs\nSKILLS\nPython, FastAPI, SQL\nEDUCATION\nBSc Computer Science",
            "Jamie Example\nPROFILE\nData analyst\nEMPLOYMENT HISTORY\nCreated Tableau reports\nTECHNICAL PROFICIENCIES\nSQL, Excel, Tableau\nACADEMIC BACKGROUND\nBA Economics",
            "Taylor Example\nOBJECTIVE\nFrontend developer\nPROFESSIONAL EXPERIENCE\nBuilt React interfaces\nCORE SKILLS\nJavaScript, React, CSS\nPROJECTS\nPortfolio website",
        ]
        for sample in samples:
            with self.subTest(sample=sample[:20]):
                parsed = parse_resume_pdf(make_pdf(sample))
                self.assertEqual(parsed.page_count, 1)
                self.assertTrue(parsed.text)
                self.assertTrue(parsed.sections)
                self.assertTrue(parsed.skills)
        first = parse_resume_pdf(make_pdf(samples[0]))
        self.assertIn("Experience", first.sections)
        self.assertIn("Skills", first.sections)
        self.assertIn("Python", {skill["name"] for skill in first.skills})

    def test_empty_upload_and_invalid_pdf_are_reported(self):
        with self.assertRaisesRegex(PDFReadError, "empty"):
            read_pdf(b"")
        with self.assertRaisesRegex(PDFReadError, "could not read"):
            read_pdf(b"this is not a PDF")

    def test_blank_pdf_returns_warning_instead_of_crashing(self):
        result = parse_resume_pdf(make_pdf(""))
        self.assertEqual(result.text, "")
        self.assertEqual(result.page_count, 1)
        self.assertIsNotNone(result.warning)

    def test_cleaner_normalizes_ligatures_bullets_and_hyphenation(self):
        result = parse_resume_pdf(make_pdf("SKILLS\n• Python\nExperi-\nence"))
        self.assertIn("Python", result.text)
        self.assertIn("Experience", result.text)


if __name__ == "__main__":
    unittest.main()
