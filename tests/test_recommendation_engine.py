"""Independent CSV-backed learning recommendation tests."""
import csv
import tempfile
import unittest
from pathlib import Path

from modules.recommendation_engine import recommend_learning_path


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.skills_path = root / "skills.csv"
        self.resources_path = root / "resources.csv"
        with self.skills_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f); writer.writerow(["skill", "category", "aliases", "related_skills", "level"])
            writer.writerow(["Python", "Programming", "py", "SQL", "Beginner"])
            writer.writerow(["SQL", "Database", "", "Python", "Beginner"])
        with self.resources_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f); writer.writerow(["skill", "resource_name", "resource_url", "difficulty", "estimated_hours", "project_idea"])
            writer.writerow(["Python", "Python Tutorial", "https://docs.python.org/3/tutorial/", "Beginner", 8, "Build a parser"])
            writer.writerow(["SQL", "SQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html", "Intermediate", 10, "Build a report"])

    def tearDown(self):
        self.temp.cleanup()

    def recommend(self, gaps, required=None):
        return recommend_learning_path(gaps, required, self.resources_path, self.skills_path)

    def test_missing_skill_gets_resource_and_high_priority(self):
        result = self.recommend({"missing_skills": ["Python"]}, ["Python"])
        item = result["recommendations"][0]
        self.assertEqual(item["priority"], "High")
        self.assertEqual(item["resource_name"], "Python Tutorial")

    def test_alias_resolves_to_canonical_resource(self):
        result = self.recommend({"missing_skills": ["py"]})
        self.assertEqual(result["recommendations"][0]["skill"], "Python")

    def test_partial_skill_gets_medium_priority(self):
        result = self.recommend({"partially_matched_skills": ["SQL"]}, ["SQL"])
        self.assertEqual(result["recommendations"][0]["priority"], "Medium")

    def test_unavailable_resource_is_reported_without_unrelated_course(self):
        result = self.recommend({"missing_skills": ["Kubernetes"]})
        item = result["recommendations"][0]
        self.assertIsNone(item["resource_url"])
        self.assertIn("No curated resource", item["explanation"])

    def test_roadmap_groups_levels_and_sums_duration(self):
        result = self.recommend({"missing_skills": ["Python", "SQL"]})
        self.assertEqual(len(result["roadmap_by_level"]["Beginner"]), 1)
        self.assertEqual(len(result["roadmap_by_level"]["Intermediate"]), 1)
        self.assertEqual(result["total_estimated_hours"], 18)

    def test_duplicate_gaps_collapse(self):
        result = self.recommend({"missing_skills": ["Python", "python"]})
        self.assertEqual(len(result["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()
