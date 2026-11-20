"""ReportLab PDF export adapter for the structured analysis-engine result."""
from __future__ import annotations

from careerlens.services.report_generator import generate_analysis_pdf


def generate_report(analysis_result: dict) -> bytes:
    """Build downloadable PDF bytes from scoring, gap, and roadmap outputs."""
    score = analysis_result.get("score", {})
    if not isinstance(score, dict):
        score = {"overall_score": score, "component_scores": analysis_result.get("component_scores", {})}
    result = {
        "target_name": analysis_result.get("job_title", analysis_result.get("target_name", "Job role")),
        "filename": analysis_result.get("filename", "Uploaded resume"),
        "overall_score": score.get("overall_score", analysis_result.get("overall_score", 0)),
        "breakdown": score.get("component_scores", analysis_result.get("component_scores", {})),
        "candidate_summary": analysis_result.get("candidate_summary", {}),
        # Fresh service results use ``gap_analysis``; SQLite history decodes the
        # same stored fields as ``skill_gaps`` for the UI. Accept both contracts.
        "gap_analysis": analysis_result.get("gap_analysis", analysis_result.get("skill_gaps", {})),
        "recommendations": analysis_result.get("recommendations", {}),
    }
    return generate_analysis_pdf(result)


def generate_report_bytes(analysis_result: dict) -> bytes:
    """Explicitly named alias for Streamlit's download_button data argument."""
    return generate_report(analysis_result)
