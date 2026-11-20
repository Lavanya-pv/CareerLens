"""Independent tests for transparent compatibility scoring."""
import unittest

from modules.scoring_engine import calculate_compatibility_score


class ScoringEngineTests(unittest.TestCase):
    def test_default_weights_compute_expected_score(self):
        result = calculate_compatibility_score(80, 60, {}, "")
        self.assertEqual(result["overall_score"], 68.0)  # 40 + 18 + 10 (neutral 50 × 20%)

    def test_fraction_inputs_are_normalized(self):
        result = calculate_compatibility_score(.5, .5, {}, "")
        self.assertEqual(result["component_scores"]["required_skill_coverage"], 50.0)

    def test_explicit_experience_missing_from_resume_is_not_perfect(self):
        result = calculate_compatibility_score(100, 100, {}, "Requires 5 years of experience")
        self.assertLess(result["component_scores"]["experience_qualifications"], 50)

    def test_degree_and_experience_evidence_are_explained(self):
        result = calculate_compatibility_score(70, 80, {"estimated_experience": 4, "degrees": ["BSc Computer Science"]}, "Requires 3 years experience and a bachelor's degree")
        explanations = " ".join(result["explanations"]["experience_qualifications"])
        self.assertIn("Experience", explanations)
        self.assertIn("degree", explanations)

    def test_custom_weights_are_normalized(self):
        result = calculate_compatibility_score(100, 0, {}, "", {"required_skill_coverage": 1, "semantic_relevance": 0, "experience_qualifications": 0})
        self.assertEqual(result["overall_score"], 100.0)

    def test_out_of_range_component_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_compatibility_score(101, 50)

    def test_result_is_not_a_hiring_probability(self):
        result = calculate_compatibility_score(50, 50)
        self.assertIn("not a probability", result["disclaimer"])


if __name__ == "__main__":
    unittest.main()
