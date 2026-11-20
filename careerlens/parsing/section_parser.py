"""Split resume text into common sections using heading names and synonyms."""
import re

HEADING_SYNONYMS = {
    "Summary": ("summary", "profile", "professional summary", "career summary", "objective", "about me"),
    "Experience": ("experience", "work experience", "professional experience", "work history", "employment", "employment history"),
    "Education": ("education", "academic background", "academic history", "qualifications"),
    "Skills": ("skills", "technical skills", "core skills", "technical expertise", "competencies", "technologies", "technical proficiencies"),
    "Projects": ("projects", "personal projects", "selected projects", "academic projects"),
    "Certifications": ("certifications", "certificates", "licenses", "licenses and certifications"),
    "Awards": ("awards", "honors", "honours", "achievements"),
    "Publications": ("publications", "papers", "presentations"),
    "Volunteer Experience": ("volunteer experience", "volunteering", "community involvement"),
}
_NORMALIZED_HEADINGS = {
    re.sub(r"[^a-z0-9 ]", "", alias.lower()).strip(): section
    for section, aliases in HEADING_SYNONYMS.items()
    for alias in aliases
}


def _heading_for(line: str) -> str | None:
    candidate = re.sub(r"[^a-z0-9 ]", "", line.lower()).strip()
    candidate = re.sub(r"\s+", " ", candidate)
    # A colon is common in inline section labels (e.g. "Skills:").
    candidate = candidate.removesuffix(":").strip()
    return _NORMALIZED_HEADINGS.get(candidate)


def parse_sections(text: str) -> dict[str, str]:
    """Return normalized section names mapped to their original cleaned text."""
    sections: dict[str, str] = {}
    current = "Other"
    buffer: list[str] = []

    def save() -> None:
        content = "\n".join(buffer).strip()
        if content:
            sections[current] = "\n".join(filter(None, (sections.get(current, ""), content)))

    for line in (text or "").splitlines():
        heading = _heading_for(line)
        if heading and len(line.strip()) < 60:
            save()
            current, buffer = heading, []
        else:
            buffer.append(line)
    save()
    return sections
