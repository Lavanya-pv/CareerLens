"""Five PDF-resume/JD pipeline combinations, including sparse resume details."""
import unittest
from unittest.mock import patch

import pymupdf

from careerlens.services.pipeline import analyze
from careerlens.services.report_generator import generate_analysis_pdf


class FakeUpload:
    def __init__(self, name: str, body: bytes):
        self.name = name
        self._body = body

    def getvalue(self) -> bytes:
        return self._body


def pdf_bytes(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((50, 55), text, fontsize=9)
    contents = document.tobytes()
    document.close()
    return contents


CASES = [
    (
        "analyst.pdf",
        "Morgan Chen\nSUMMARY\nData analyst with business reporting experience.\nEXPERIENCE\nUsed Python and SQL to analyze weekly sales. Built Power BI dashboards and data visualizations.\nEDUCATION\nBSc Statistics",
        "Data Analyst",
        "Data Analyst needs SQL, Python, Power BI, Data Analysis, and Data Visualization skills.",
    ),
    (
        "frontend.pdf",
        "Riley Jones\nEXPERIENCE\nBuilt React and JavaScript interfaces. Used HTML and CSS for responsive layouts.\nSKILLS\nReact, JavaScript, HTML, CSS",
        "Frontend Developer",
        "Frontend developer with JavaScript, React, HTML, CSS, and TypeScript experience.",
    ),
    (
        "backend.pdf",
        "Sam Patel\nEXPERIENCE\nCreated Python REST APIs using FastAPI. Deployed Docker services backed by PostgreSQL.\nSKILLS\nPython, FastAPI, Docker, PostgreSQL",
        "Backend Developer",
        "Backend engineer. Required: Python, SQL, REST APIs, Git, Docker, AWS, FastAPI.",
    ),
    (
        "scientist.pdf",
        "Taylor Kim\nSUMMARY\nMachine learning researcher working on text classification.\nSKILLS\nPython, Pandas, NLP, scikit-learn, SQL",
        "Data Scientist",
        "Data Scientist: Python, SQL, Machine Learning, Pandas, NLP, scikit-learn.",
    ),
    (
        "sparse_resume.pdf",
        "Jordan\nPython and Excel. Assisted on a small project.",
        "Product Analyst",
        "Seeking someone with Python, SQL, Excel, Data Analysis, Communication, and Project Management.",
    ),
]


class AnalysisCombinationTests(unittest.TestCase):
    def test_five_resume_and_job_description_combinations(self):
        with patch("careerlens.services.pipeline.save_analysis", return_value=123):
            for filename, resume_text, title, jd in CASES:
                with self.subTest(target=title):
                    result = analyze(FakeUpload(filename, pdf_bytes(resume_text)), "jd", title, jd)
                    self.assertEqual(result["target_name"], title)
                    self.assertGreaterEqual(result["score"], 0)
                    self.assertLessEqual(result["score"], 100)
                    self.assertEqual(result["id"], 123)
                    self.assertTrue(result["skills"])
                    self.assertTrue(result["breakdown"])
                    self.assertIn(result["semantic_method"], {"all-MiniLM-L6-v2", "tfidf-fallback"})
                    self.assertTrue({"matched", "partial", "missing"}.intersection(s["status"] for s in result["skills"]))

    def test_sparse_resume_with_missing_contact_and_dates_is_still_analyzed(self):
        name, resume_text, title, jd = CASES[-1]
        with patch("careerlens.services.pipeline.save_analysis", return_value=5):
            result = analyze(FakeUpload(name, pdf_bytes(resume_text)), "jd", title, jd)
        self.assertIsNone(result["profile"]["email"])
        self.assertIsNone(result["profile"]["phone"])
        self.assertEqual(result["profile"]["estimated_experience"], 0)
        self.assertTrue(any(skill["status"] == "missing" for skill in result["skills"]))

    def test_analysis_result_can_be_exported_as_a_pdf(self):
        report = generate_analysis_pdf({
            "id": 1,
            "filename": "resume.pdf",
            "target_name": "Data Analyst",
            "overall_score": 74,
            "breakdown": {"skills": 80, "semantic": 65},
            "skills": [{"skill": "SQL", "status": "matched", "category": "Database"}],
            "recommendations": [{"skill": "Python", "resource": "Free course", "project": "Build a small analysis."}],
        })
        self.assertTrue(report.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
