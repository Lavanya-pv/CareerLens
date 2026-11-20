"""QA scenarios exercising the real parser, service, recommender, and SQLite."""
from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

import pymupdf

from modules.analysis_service import analyze_resume
from modules.database import get_analyses
from modules.recommendation_engine import recommend_learning_path
from modules.resume_parser import parse_resume


def pdf_for_text(text: str) -> bytes:
    """Create a real, in-memory text PDF with all supplied content selectable."""
    doc = pymupdf.open()
    words = text.split()
    for start in range(0, max(1, len(words)), 250):
        page = doc.new_page()
        chunk = " ".join(words[start:start + 250])
        page.insert_textbox(pymupdf.Rect(40, 40, 560, 740), chunk, fontsize=9)
    data = doc.tobytes()
    doc.close()
    return data


class Upload(io.BytesIO):
    name = "qa_resume.pdf"


class CareerLensQAScenarios(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "qa.sqlite"

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self, resume: str, jd: str, title: str = "QA Target"):
        return analyze_resume(Upload(pdf_for_text(resume)), title, jd, db_path=self.db)

    def test_01_valid_resume_and_complete_job_description(self):
        result = self.analyze(
            "SUMMARY Backend developer. EXPERIENCE Built Python APIs with FastAPI, PostgreSQL and Docker. "
            "SKILLS Python FastAPI PostgreSQL Docker Git. EDUCATION BSc Computer Science.",
            "Backend engineer: Python, FastAPI, PostgreSQL, Docker, Git, 3 years experience; bachelor's degree preferred.",
        )
        self.assertGreaterEqual(result["overall_score"], 0)
        self.assertLessEqual(result["overall_score"], 100)
        self.assertTrue(result["gap_analysis"]["matched_skills"])
        self.assertEqual(set(result["component_scores"]), {"required_skill_coverage", "semantic_relevance", "experience_qualifications"})
        self.assertGreater(result["analysis_id"], 0)

    def test_02_resume_with_no_technical_skills_is_analyzed_as_gaps(self):
        result = self.analyze(
            "Experienced office coordinator who organized schedules, supported teams, and prepared meeting notes.",
            "Developer requires Python, SQL, and Docker.",
        )
        self.assertEqual(result["gap_analysis"]["matched_skills"], [])
        self.assertEqual({x["skill"] for x in result["gap_analysis"]["missing_skills"]}, {"Python", "SQL", "Docker"})
        self.assertEqual({x["skill"] for x in result["recommendations"]["recommendations"]}, {"Python", "SQL", "Docker"})

    def test_03_empty_job_description_is_rejected_before_analysis(self):
        with self.assertRaisesRegex(ValueError, "job description"):
            self.analyze("Python developer", "")

    def test_04_invalid_or_corrupted_pdf_returns_readable_error(self):
        upload = Upload(b"not a valid PDF")
        with self.assertRaisesRegex(ValueError, "could not read"):
            analyze_resume(upload, "Backend Engineer", "Python and SQL required", db_path=self.db)

    def test_05_duplicate_resume_skills_are_deduplicated(self):
        parsed = parse_resume(Upload(pdf_for_text("Python PYTHON python; SQL sql.")))
        names = [skill["name"] for skill in parsed.skills]
        self.assertEqual(names.count("Python"), 1)
        self.assertEqual(names.count("SQL"), 1)

    def test_06_uncommon_curated_skill_is_extracted_and_matched(self):
        result = self.analyze("ML engineer. Used XGBoost for model training and evaluation.", "Need XGBoost experience.")
        self.assertIn("XGBoost", {x["skill"] for x in result["gap_analysis"]["matched_skills"]})

    def test_07_abbreviations_and_synonyms_match_canonical_skills(self):
        result = self.analyze("Used ML and NLP models; delivered UI work with JS.", "Machine Learning, Natural Language Processing, and JavaScript required.")
        self.assertEqual(
            {x["skill"] for x in result["gap_analysis"]["matched_skills"]},
            {"Machine Learning", "Natural Language Processing", "JavaScript"},
        )

    def test_08_very_short_resume_is_processed_without_inventing_skills(self):
        result = self.analyze("Python.", "Python required.")
        self.assertIn("Python", {x["skill"] for x in result["gap_analysis"]["matched_skills"]})
        self.assertTrue(result["warnings"], "Short selectable text should carry the parser's low-text warning.")

    def test_09_very_long_resume_is_extracted_across_pages(self):
        resume = ("Experience building Python services, testing APIs, and supporting SQL data workflows. " * 1200)
        parsed = parse_resume(Upload(pdf_for_text(resume)))
        self.assertGreater(parsed.page_count, 1)
        self.assertGreater(len(parsed.text), 20_000)
        result = self.analyze(resume, "Python and SQL engineer.")
        self.assertTrue(result["gap_analysis"]["matched_skills"])

    def test_10_missing_learning_resource_is_reported_without_unrelated_course(self):
        plan = recommend_learning_path(
            {"missing_skills": ["XGBoost"], "partially_matched_skills": []},
            required_skills=["XGBoost"],
        )
        item = plan["recommendations"][0]
        self.assertEqual(item["skill"], "XGBoost")
        self.assertIsNone(item["resource_url"])
        self.assertIn("No curated resource", item["explanation"])

    def test_11_new_analysis_history_starts_empty(self):
        self.assertEqual(get_analyses(db_path=self.db), [])

    def test_12_repeated_analysis_is_saved_as_distinct_history_entries(self):
        resume = "Python developer with SQL and Docker project experience."
        jd = "Python, SQL, and Docker required."
        first = self.analyze(resume, jd)
        second = self.analyze(resume, jd)
        records = get_analyses(db_path=self.db)
        self.assertNotEqual(first["analysis_id"], second["analysis_id"])
        self.assertEqual(len(records), 2)
        self.assertEqual(first["overall_score"], second["overall_score"])


if __name__ == "__main__":
    unittest.main()
