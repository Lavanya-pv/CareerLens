"""Independent report generation tests; output is kept in memory."""
import unittest
from unittest.mock import patch

from modules.report_generator import generate_report


class ReportGeneratorTests(unittest.TestCase):
    def test_history_record_skill_gaps_are_forwarded_to_pdf_builder(self):
        history_record = {
            "job_title": "Backend Engineer", "overall_score": 72,
            "component_scores": {"required_skill_coverage": 70},
            "skill_gaps": {"matched_skills": [{"skill": "Python"}], "missing_skills": [{"skill": "Docker"}], "partially_matched_skills": []},
            "recommendations": {"recommendations": []},
        }
        with patch("modules.report_generator.generate_analysis_pdf", return_value=b"%PDF") as builder:
            self.assertEqual(generate_report(history_record), b"%PDF")
        self.assertEqual(builder.call_args.args[0]["gap_analysis"], history_record["skill_gaps"])

    def test_complete_analysis_returns_pdf_bytes(self):
        report = generate_report({
            "job_title": "Backend Engineer", "score": {"overall_score": 73, "component_scores": {"required_skill_coverage": 70, "semantic_relevance": 80, "experience_qualifications": 65}},
            "gap_analysis": {"matched_skills": [{"skill": "Python", "category": "Programming", "evidence": "Direct match"}], "missing_skills": [{"skill": "Docker", "category": "DevOps", "explanation": "No evidence"}], "partially_matched_skills": []},
            "recommendations": {"recommendations": [{"skill": "Docker", "priority": "High", "level": "Beginner", "resource_name": "Docker Docs", "resource_url": "https://docs.docker.com/", "estimated_hours": 6, "project_idea": "Containerize a service"}], "roadmap_by_level": {"Beginner": [], "Intermediate": [], "Advanced": []}},
        })
        self.assertTrue(report.startswith(b"%PDF"))
        self.assertGreater(len(report), 500)

    def test_empty_sections_still_generate_pdf(self):
        report = generate_report({"job_title": "Analyst", "score": {"overall_score": 0, "component_scores": {}}, "gap_analysis": {}, "recommendations": {}})
        self.assertTrue(report.startswith(b"%PDF"))

    def test_long_skill_lists_generate_without_layout_failure(self):
        gaps = {"matched_skills": [{"skill": f"Skill {i}", "category": "Tools"} for i in range(150)], "missing_skills": [], "partially_matched_skills": []}
        report = generate_report({"job_title": "Engineer", "score": 50, "gap_analysis": gaps, "recommendations": {}})
        self.assertTrue(report.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
