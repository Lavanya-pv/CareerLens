"""Independent skill gap classification tests."""
import unittest
from unittest.mock import patch

from modules.gap_analyzer import analyze_skill_gaps


class GapAnalyzerTests(unittest.TestCase):
    def test_exact_skill_is_directly_matched(self):
        result = analyze_skill_gaps(["Python"], ["Python"])
        self.assertEqual([x["skill"] for x in result["matched_skills"]], ["Python"])

    def test_missing_skill_is_reported(self):
        result = analyze_skill_gaps([], ["Python"])
        self.assertEqual(result["missing_skills"][0]["skill"], "Python")

    def test_partial_uses_configured_threshold_and_explanation(self):
        values = {"resume_statement": ["Data analyst"], "job_requirement": ["Data scientist"], "similarity": [0.8]}
        with patch("modules.gap_analyzer.batch_similarity") as similarity:
            import pandas as pd
            similarity.return_value = pd.DataFrame(values)
            result = analyze_skill_gaps(["Data analyst"], ["Data scientist"], similarity_threshold=0.7)
        self.assertEqual(len(result["partially_matched_skills"]), 1)
        self.assertIn("similarity", result["partially_matched_skills"][0]["explanation"])

    def test_duplicates_are_collapsed_and_denominator_is_unique_required(self):
        result = analyze_skill_gaps(["Python", "python"], ["Python", "PYTHON", "SQL"])
        self.assertEqual(result["required_skill_count"], 2)
        self.assertEqual(result["coverage_denominator"], "unique required skills")
        self.assertEqual(result["skill_coverage"], 50.0)

    def test_empty_required_skills_have_zero_coverage(self):
        result = analyze_skill_gaps(["Python"], [])
        self.assertEqual(result["skill_coverage"], 0.0)

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            analyze_skill_gaps([], [], 1.1)

    def test_skill_dicts_preserve_category(self):
        result = analyze_skill_gaps([], [{"name": "Python", "category": "Programming"}])
        self.assertEqual(result["missing_skills"][0]["category"], "Programming")


if __name__ == "__main__":
    unittest.main()
