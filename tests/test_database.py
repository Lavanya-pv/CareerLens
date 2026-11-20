"""Independent SQLite persistence tests using isolated temporary databases."""
import tempfile
import unittest
from pathlib import Path

from modules.database import delete_analysis, get_analyses, get_analysis, save_analysis


class AnalysisDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "history.sqlite"
        self.analysis = {
            "job_title": "Data Engineer",
            "score": {"overall_score": 72.5, "component_scores": {"skills": 80}},
            "gap_analysis": {"matched_skills": [{"skill": "Python"}], "missing_skills": [{"skill": "Kafka"}], "partially_matched_skills": []},
            "recommendations": {"recommendations": []},
            "resume_text": "PRIVATE RESUME TEXT MUST NOT BE STORED",
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_save_creates_database_and_fetch_by_id(self):
        item_id = save_analysis(self.analysis, self.db)
        result = get_analysis(item_id, self.db)
        self.assertEqual(result["job_title"], "Data Engineer")
        self.assertEqual(result["overall_score"], 72.5)

    def test_list_returns_skill_statuses(self):
        save_analysis(self.analysis, self.db)
        rows = get_analyses(db_path=self.db)
        self.assertEqual(rows[0]["skill_gaps"]["missing_skills"][0]["skill"], "Kafka")

    def test_raw_resume_text_is_not_persisted(self):
        item_id = save_analysis(self.analysis, self.db)
        result = get_analysis(item_id, self.db)
        self.assertNotIn("resume_text", result)
        self.assertNotIn("PRIVATE RESUME TEXT MUST NOT BE STORED", repr(result))

    def test_missing_id_returns_none_and_delete_returns_false(self):
        self.assertIsNone(get_analysis(999, self.db))
        self.assertFalse(delete_analysis(999, self.db))

    def test_delete_removes_saved_record(self):
        item_id = save_analysis(self.analysis, self.db)
        self.assertTrue(delete_analysis(item_id, self.db))
        self.assertIsNone(get_analysis(item_id, self.db))

    def test_parameterized_job_title_is_saved_as_data(self):
        self.analysis["job_title"] = "x'); DROP TABLE analysis_history;--"
        item_id = save_analysis(self.analysis, self.db)
        self.assertEqual(get_analysis(item_id, self.db)["job_title"], self.analysis["job_title"])
        self.assertEqual(len(get_analyses(db_path=self.db)), 1)


if __name__ == "__main__":
    unittest.main()
