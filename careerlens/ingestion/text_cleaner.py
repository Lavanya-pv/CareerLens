"""Normalize extracted PDF text while preserving useful resume structure."""
import re
import unicodedata


def clean_text(text: str) -> str:
    """Normalize ligatures, bullets, broken words and whitespace for downstream parsing."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\uf0b7", "•").replace("\u2022", "•").replace("\u25aa", "•")
    # Join words split by a PDF line break, but keep ordinary line boundaries intact.
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[\t\r\f]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
