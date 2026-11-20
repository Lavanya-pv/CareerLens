"""Application service that wires parsing, matching, scoring, and persistence."""
import json

from careerlens.analysis.gap_analyzer import analyze_gaps
from careerlens.analysis.scorer import score_analysis
from careerlens.config import DATA_DIR
from careerlens.db.repository import save_analysis
from careerlens.embeddings.similarity import similarity_matrix
from careerlens.ingestion.pdf_reader import read_pdf
from careerlens.ingestion.text_cleaner import clean_text
from careerlens.matching.tfidf_keywords import keyword_coverage
from careerlens.parsing.entity_extractor import extract_profile
from careerlens.parsing.section_parser import parse_sections
from careerlens.recommendations.learning_paths import get_learning_plan
from careerlens.recommendations.resume_tips import get_resume_tips
from careerlens.skills.extractor import extract_skills


def analyze(upload, target_type: str, target_name: str, jd_text: str = "") -> dict:
    """Analyze an uploaded PDF against a role profile or pasted job description."""
    pdf = read_pdf(upload.getvalue())
    text = clean_text(pdf.text)
    if not text:
        raise ValueError("No selectable text was found in this PDF. It may be blank or scanned; OCR is not included.")

    sections = parse_sections(text)
    found = extract_skills(text)
    if target_type == "role":
        profiles = json.loads((DATA_DIR / "role_profiles.json").read_text(encoding="utf-8"))
        role = next((item for item in profiles if item["name"] == target_name), None)
        if role is None:
            raise ValueError(f"Unknown role profile: {target_name}")
        required, preferred = role["required"], role.get("preferred", [])
        jd_text = role["description"]
    elif target_type in {"jd", "job_description"}:
        if not jd_text.strip():
            raise ValueError("Paste a job description before running the analysis.")
        required = [item["name"] for item in extract_skills(jd_text)]
        preferred = []
        if not required:
            raise ValueError("No recognized skills were found in this job description. Add role-specific skill terms or choose a role profile.")
    else:
        raise ValueError("Choose a supported target type: role or job description.")

    resume_skill_names = [item["name"] for item in found]
    comparison, semantic_method = similarity_matrix(
        [text, *resume_skill_names],
        [jd_text, *required],
    )
    semantic_score = float(comparison[0, 0])
    nearest_skills = {}
    if resume_skill_names:
        per_skill = comparison[1:, 1:]
        for target_index, skill_name in enumerate(required):
            best_index = int(per_skill[:, target_index].argmax())
            nearest_skills[skill_name] = (resume_skill_names[best_index], float(per_skill[best_index, target_index]))

    gaps = analyze_gaps(found, required, preferred, similarities=nearest_skills)
    keyword_score, keywords = keyword_coverage(jd_text, text)
    profile = extract_profile(text)
    score, breakdown = score_analysis(gaps, keyword_score, profile, len(sections), semantic_score)
    next_skills = [item["name"] for item in gaps if item["status"] in {"missing", "partial"}]
    recommendations = get_learning_plan(next_skills[:5])
    recommendations += [{"skill": "Resume polish", "resource": tip, "project": ""} for tip in get_resume_tips(text, sections)]
    analysis_id = save_analysis(
        upload.name, text, target_name, target_type, jd_text, score,
        breakdown, profile, recommendations, gaps,
    )
    return {
        "id": analysis_id,
        "filename": upload.name,
        "target_name": target_name,
        "score": score,
        "breakdown": breakdown,
        "semantic_method": semantic_method,
        "semantic_similarity": round(semantic_score, 4),
        "keyword_score": round(keyword_score, 4),
        "keywords": keywords,
        "profile": profile,
        "skills": gaps,
        "recommendations": recommendations,
        "sections": sections,
        "pages": pdf.page_count,
        "warning": pdf.warning,
    }
