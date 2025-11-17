# utils/nlp.py
import os
from typing import List, Dict
import re
import dateparser
import openai

# Load API key from environment (Streamlit secrets)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY


# -----------------------------------------
# Lightweight ENTITY extraction (no spaCy)
# -----------------------------------------
def extract_entities(text: str) -> Dict:
    """
    Simple regex-based entity extraction suitable for Streamlit Cloud.
    Extracts:
    - Names (capitalized phrases)
    - Organizations
    - Places
    """

    if not text:
        return {"PERSON": [], "ORG": [], "GPE": [], "MISC": []}

    # Capture capitalized words or sequences (e.g. "Joe Biden", "OpenAI", "New York")
    pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    matches = re.findall(pattern, text)

    # Remove common false positives
    blacklist = {"The", "A", "In", "On", "At", "Of", "And", "For", "With", "To"}

    cleaned = [m for m in matches if m not in blacklist]

    # Deduplicate
    cleaned = list(dict.fromkeys(cleaned))[:30]

    # Split heuristically into categories
    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],
        "MISC": []
    }

    for e in cleaned:
        if len(e.split()) == 2:  # likely a person (2-word names)
            entities["PERSON"].append(e)
        elif "University" in e or "Corp" in e or "Inc" in e or "AI" in e or "Company" in e:
            entities["ORG"].append(e)
        elif e in ["India", "USA", "China", "Russia", "Germany", "UK"]:
            entities["GPE"].append(e)
        else:
            entities["MISC"].append(e)

    return entities


# -----------------------------------------
# Date extraction
# -----------------------------------------

def find_dates(text: str):
    matches = re.findall(r'\b(?:\d{1,2}[\s/-])?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s/-]?\d{2,4}\b', text, re.IGNORECASE)
    parsed_dates = [dateparser.parse(m).date().isoformat() for m in matches if dateparser.parse(m)]
    return parsed_dates

    found_dates = set()

    # Date-like patterns
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{0,4}",
        r"\b\d{4}\b"
    ]

    for pat in patterns:
        for m in re.findall(pat, text, flags=re.IGNORECASE):
            dt = dateparser.parse(m)
            if dt:
                found_dates.add(dt.date().isoformat())

    return sorted(found_dates)


# -----------------------------------------
# OpenAI summarization
# -----------------------------------------
def openai_summarize(texts: List[str], prompt_extra: str = "") -> str:
    if not OPENAI_KEY:
        return "OpenAI API key missing. Set OPENAI_API_KEY in environment."

    combined = "\n\n---\n\n".join([t[:4000] for t in texts])

    system_prompt = (
        "You are an AI that summarizes multiple news articles. "
        "Output: (1) Timeline with ISO dates → events, "
        "(2) 2-paragraph summary, "
        "(3) Conflicts between sources."
    )

    user_prompt = f"{prompt_extra}\n\nArticles:\n{combined}"

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"AI summarization failed: {e}"


# -----------------------------------------
# Lightweight fallback summary
# -----------------------------------------
def lightweight_summary(texts: List[str]) -> str:
    bullets = []
    for t in texts:
        first_line = t.strip().split("\n")[0][:250]
        bullets.append(first_line)

    summary = " ".join(bullets[:5])
    return summary[:1000] + ("..." if len(summary) > 1000 else "")



