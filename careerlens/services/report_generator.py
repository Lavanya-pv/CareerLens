"""Build a downloadable analysis PDF in memory without temporary files."""
from io import BytesIO
from xml.sax.saxutils import escape


def generate_analysis_pdf(analysis: dict) -> bytes:
    """Create a concise PDF containing score, skill gaps, and learning actions."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF report export requires reportlab. Install project requirements.") from exc

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=.65 * inch, leftMargin=.65 * inch,
        topMargin=.6 * inch, bottomMargin=.6 * inch,
        title=f"CareerLens analysis - {analysis.get('target_name', 'Career fit')}",
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle("CLTitle", parent=base["Title"], textColor=colors.HexColor("#245c43"), alignment=TA_LEFT, spaceAfter=8)
    heading = ParagraphStyle("CLHeading", parent=base["Heading2"], textColor=colors.HexColor("#245c43"), spaceBefore=14, spaceAfter=7)
    body = ParagraphStyle("CLBody", parent=base["BodyText"], leading=14, spaceAfter=4)
    small = ParagraphStyle("CLSmall", parent=body, fontSize=8.5, textColor=colors.HexColor("#59645d"))

    def para(value, style=body):
        # Built-in Helvetica supports WinAnsi; replace unusual glyphs so uploaded
        # filenames or free-form target titles cannot make PDF export fail.
        safe_text = str(value or "").encode("cp1252", errors="replace").decode("cp1252")
        return Paragraph(escape(safe_text).replace("\n", "<br/>"), style)

    story = [para("CareerLens AI", title), para("Career analysis report", heading)]
    story += [para(f"Resume: {analysis.get('filename', 'Uploaded resume')}", body), para(f"Target: {analysis.get('target_name', analysis.get('job_title', 'Job description'))}", body)]
    summary = analysis.get("candidate_summary")
    if summary:
        story.append(para("Candidate summary", heading))
        if isinstance(summary, dict):
            story.extend(para(f"{key.replace('_', ' ').title()}: {value}") for key, value in summary.items() if value not in (None, "", [], {}))
        else:
            story.append(para(summary))
    overall = analysis.get("overall_score", analysis.get("score", 0))
    if isinstance(overall, dict):
        overall = overall.get("overall_score", 0)
    story += [para(f"Overall compatibility score: {round(float(overall))}%", heading)]

    breakdown = analysis.get("breakdown") or analysis.get("component_scores", {})
    if breakdown:
        table_data = [["Score component", "Score"]] + [[name.replace("_", " ").title(), f"{round(float(value))}%"] for name, value in breakdown.items()]
        table = Table(table_data, colWidths=[4.8 * inch, 1.2 * inch], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2ec")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#20362a")),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#dce4de")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        story.extend([table, Spacer(1, 8)])

    skills = analysis.get("skills", [])
    gaps = analysis.get("gap_analysis", {})
    if not skills and gaps:
        skills = []
        for status, key in (("matched", "matched_skills"), ("missing", "missing_skills"), ("partial", "partially_matched_skills")):
            skills.extend({**item, "status": status} for item in gaps.get(key, []))
    story.append(para("Skill alignment", heading))
    if skills:
        rows = [["Skill", "Status", "Category", "Evidence / explanation"]]
        rows += [[item.get("skill", item.get("name", "")), item.get("status", ""), item.get("category", ""), item.get("explanation", item.get("evidence", ""))] for item in skills]
        skill_table = Table([[para(cell, small) for cell in row] for row in rows], colWidths=[1.45 * inch, .8 * inch, 1.15 * inch, 2.7 * inch], repeatRows=1, splitByRow=1)
        skill_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2ec")),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#dce4de")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(skill_table)
    else:
        story.append(para("No skills were recorded for this analysis."))

    story.append(para("Recommended next steps", heading))
    recommendations = analysis.get("recommendations", [])
    if isinstance(recommendations, dict):
        roadmap = recommendations.get("roadmap_by_level", {})
        recommendations = [item for level in ("Beginner", "Intermediate", "Advanced") for item in roadmap.get(level, [])]
    for item in recommendations:
        name = item.get("skill", "Next step")
        resource = item.get("resource", item.get("resource_name", ""))
        url = item.get("resource_url", "")
        priority = item.get("priority", "")
        level = item.get("level", item.get("difficulty", ""))
        duration = item.get("estimated_hours", "")
        details = " · ".join(str(value) for value in (priority, level, f"{duration} hours" if duration else "") if value)
        story.append(para(f"{name}{' (' + details + ')' if details else ''}: {resource}"))
        if url:
            story.append(para(url, small))
        project = item.get("project", item.get("project_idea", ""))
        if project:
            story.append(para(f"Portfolio idea: {project}", small))
    story.append(Spacer(1, 12))
    story.append(para("This report is a planning aid and is not a hiring prediction.", small))
    document.build(story)
    return buffer.getvalue()
