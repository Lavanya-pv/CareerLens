"""Privacy-conscious SQLite history API for completed analyses."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from careerlens.config import DB_PATH


class AnalysisDatabaseError(RuntimeError):
    """Database operation failed; chained exception retains the SQLite cause."""


def _path(db_path: str | Path | None) -> Path:
    return Path(db_path) if db_path is not None else DB_PATH


@contextmanager
def _connection(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    path = _path(db_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as exc:
        raise AnalysisDatabaseError(f"Could not open the analysis database at {path}.") from exc
    try:
        yield connection
        connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise AnalysisDatabaseError("The analysis database operation failed.") from exc
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path: str | Path | None = None) -> None:
    """Create local history tables if they do not already exist."""
    with _connection(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                overall_score REAL NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
                component_scores_json TEXT NOT NULL,
                matched_skills_json TEXT NOT NULL,
                missing_skills_json TEXT NOT NULL,
                partial_skills_json TEXT NOT NULL,
                recommendations_json TEXT NOT NULL,
                candidate_summary_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(analysis_history)")}
        if "candidate_summary_json" not in columns:
            connection.execute("ALTER TABLE analysis_history ADD COLUMN candidate_summary_json TEXT NOT NULL DEFAULT '{}' ")


def _gap_lists(analysis: dict) -> tuple[list, list, list]:
    gaps = analysis.get("gap_analysis", {})
    matched = gaps.get("matched_skills", analysis.get("matched_skills", []))
    missing = gaps.get("missing_skills", analysis.get("missing_skills", []))
    partial = gaps.get("partially_matched_skills", analysis.get("partially_matched_skills", []))
    if not gaps and analysis.get("skills"):
        for item in analysis["skills"]:
            status = item.get("status")
            if status == "matched":
                matched.append(item)
            elif status == "partial":
                partial.append(item)
            elif status == "missing":
                missing.append(item)
    return list(matched), list(missing), list(partial)


def save_analysis(analysis: dict, db_path: str | Path | None = None) -> int:
    """Persist scores, job title, skill statuses, and roadmap, never resume text."""
    initialize_database(db_path)
    score_payload = analysis.get("score", analysis.get("scoring", {}))
    if isinstance(score_payload, dict):
        overall = score_payload.get("overall_score", analysis.get("overall_score", 0))
        components = score_payload.get("component_scores", analysis.get("component_scores", {}))
    else:
        overall = score_payload if score_payload is not None else analysis.get("overall_score", 0)
        components = analysis.get("component_scores", analysis.get("breakdown", {}))
    overall = max(0.0, min(100.0, float(overall)))
    matched, missing, partial = _gap_lists(analysis)
    recommendations = analysis.get("recommendations", {})
    with _connection(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO analysis_history (job_title, overall_score, component_scores_json, matched_skills_json, missing_skills_json, partial_skills_json, recommendations_json, candidate_summary_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(analysis.get("job_title", analysis.get("target_name", "Untitled role")))[:200],
                overall,
                json.dumps(components, ensure_ascii=True),
                json.dumps(matched, ensure_ascii=True),
                json.dumps(missing, ensure_ascii=True),
                json.dumps(partial, ensure_ascii=True),
                json.dumps(recommendations, ensure_ascii=True),
                json.dumps(analysis.get("candidate_summary", {}), ensure_ascii=True),
            ),
        )
        return int(cursor.lastrowid)


def _decode(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["target_name"] = data["job_title"]
    data["breakdown"] = json.loads(data.pop("component_scores_json"))
    data["component_scores"] = data["breakdown"]
    matched = json.loads(data.pop("matched_skills_json"))
    missing = json.loads(data.pop("missing_skills_json"))
    partial = json.loads(data.pop("partial_skills_json"))
    data["recommendations"] = json.loads(data.pop("recommendations_json"))
    data["candidate_summary"] = json.loads(data.pop("candidate_summary_json", "{}"))
    data["skill_gaps"] = {"matched_skills": matched, "missing_skills": missing, "partially_matched_skills": partial}
    data["skills"] = [
        {**item, "status": status, "name": item.get("skill", "")}
        for status, items in (("matched", matched), ("missing", missing), ("partial", partial))
        for item in items
    ]
    data["missing_count"] = len(missing)
    data["overall_score"] = data["overall_score"]
    data["filename"] = "Resume (private)"
    return data


def get_analyses(limit: int = 25, db_path: str | Path | None = None) -> list[dict]:
    """Return recent history, newest first; limits are clamped for safety."""
    initialize_database(db_path)
    limit = max(1, min(int(limit), 500))
    with _connection(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM analysis_history ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_decode(row) for row in rows]


def get_analysis(analysis_id: int, db_path: str | Path | None = None) -> dict | None:
    """Fetch one analysis by integer ID, or return None when it does not exist."""
    initialize_database(db_path)
    with _connection(db_path) as connection:
        row = connection.execute("SELECT * FROM analysis_history WHERE id = ?", (int(analysis_id),)).fetchone()
    return _decode(row) if row else None


def delete_analysis(analysis_id: int, db_path: str | Path | None = None) -> bool:
    """Delete one history record; return False for a missing record."""
    initialize_database(db_path)
    with _connection(db_path) as connection:
        cursor = connection.execute("DELETE FROM analysis_history WHERE id = ?", (int(analysis_id),))
        return cursor.rowcount > 0


def get_recent_analyses(limit: int = 25, db_path: str | Path | None = None) -> list[dict]:
    """Compatibility alias for the current Streamlit history UI."""
    return get_analyses(limit=limit, db_path=db_path)
