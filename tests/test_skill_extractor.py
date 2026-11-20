"""Independent tests for CSV-driven skill extraction."""
import csv
import tempfile
import unittest
from pathlib import Path

from careerlens.skills.extractor import (
    extract_job_description_skills,
    extract_resume_skills,
    extract_skills,
)


class SkillExtractorTests(unittest.TestCase):
    def names(self, text):
        return {skill["name"] for skill in extract_skills(text)}

    def test_case_insensitive_matching(self):
        self.assertEqual(self.names("PYTHON, sql, and JaVaScRiPt"), {"Python", "SQL", "JavaScript"})

    def test_abbreviations_and_synonyms_return_canonical_names(self):
        found = self.names("ML and NLP are useful; JS is used in the UI.")
        self.assertTrue({"Machine Learning", "Natural Language Processing", "JavaScript"}.issubset(found))

    def test_short_c_does_not_match_inside_unrelated_words_or_c_plus_plus(self):
        found = self.names("Career coaching and cloud computing. C++ and C# are listed separately.")
        self.assertNotIn("C", found)
        self.assertIn("C++", found)
        self.assertIn("C#", found)

    def test_ml_does_not_match_as_a_substring_of_html(self):
        found = self.names("HTML and CSS are used for page layout.")
        self.assertNotIn("Machine Learning", found)
        self.assertIn("HTML", found)

    def test_case_and_alias_duplicates_collapse_to_one_canonical_skill(self):
        found = extract_skills("Python, PYTHON, and py scripting")
        python_hits = [skill for skill in found if skill["name"] == "Python"]
        self.assertEqual(len(python_hits), 1)
        self.assertEqual(python_hits[0]["evidence"].casefold(), "python")

    def test_resume_and_job_description_helpers_accept_text(self):
        self.assertIn("React", {x["name"] for x in extract_resume_skills("Built a React interface")})
        self.assertIn("Docker", {x["name"] for x in extract_job_description_skills("Experience with Docker preferred")})

    def test_structured_output_has_category_confidence_and_evidence(self):
        skill = next(x for x in extract_skills("Developed a Python app") if x["name"] == "Python")
        self.assertEqual(set(skill), {"name", "category", "confidence", "evidence"})
        self.assertEqual(skill["category"], "Programming")
        self.assertEqual(skill["confidence"], 1.0)
        self.assertEqual(skill["evidence"], "Python")

    def test_custom_csv_can_add_skills_without_changing_extractor_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "skills.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["canonical_name", "category", "aliases"])
                writer.writerow(["Prompt Ops", "Tools", "PO|prompt operations"])
            found = extract_skills("We use PO practices", dictionary_path=path)
        self.assertEqual(found[0]["name"], "Prompt Ops")


if __name__ == "__main__":
    unittest.main()
