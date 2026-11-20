"""Independent offline-friendly tests for semantic similarity helpers."""
import unittest

from modules.semantic_matcher import (
    batch_similarity,
    calculate_semantic_similarity,
    compare_resume_to_job_description,
    semantic_comparison,
)


class SemanticMatcherTests(unittest.TestCase):
    def test_empty_text_has_zero_similarity(self):
        self.assertEqual(calculate_semantic_similarity("", "Python developer"), 0.0)

    def test_identical_text_has_bounded_score(self):
        score = calculate_semantic_similarity("Python data engineer", "Python data engineer")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_comparison_reports_local_method(self):
        result = semantic_comparison("Build APIs", "Develop REST services")
        self.assertIn("similarity", result)
        self.assertIn("method", result)

    def test_batch_returns_cartesian_comparisons(self):
        frame = batch_similarity(["Python", "SQL"], ["Python role", "database role"])
        self.assertEqual(len(frame), 4)
        self.assertEqual(set(frame.columns), {"resume_statement", "job_requirement", "similarity"})

    def test_empty_batch_has_stable_columns(self):
        frame = batch_similarity([], ["Python"])
        self.assertEqual(len(frame), 0)
        self.assertIn("similarity", frame.columns)

    def test_non_string_input_is_rejected(self):
        with self.assertRaises(TypeError):
            calculate_semantic_similarity(None, "Python")

    def test_document_wrapper_returns_numeric_score(self):
        score = compare_resume_to_job_description("Data analysis with pandas", "Data analyst")
        self.assertIsInstance(score, float)


if __name__ == "__main__":
    unittest.main()
