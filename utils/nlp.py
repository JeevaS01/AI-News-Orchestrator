# utils/nlp.py
import os
import spacy
from dateutil import parser as du_parser
import dateparser
import openai
from typing import List, Dict
import re

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# load spaCy small english
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    # instruct user to download model in README
    nlp = None

def extract_entities(text: str) -> Dict:
    ents = {"PERSON":[], "ORG":[], "GPE":[], "DATE":[], "EVENT":[], "MISC":[]}
    if not nlp or not text:
        return ents
    doc = nlp(text[:50000])
    for e in doc.ents:
        if e.label_ in ents:
            ents[e.label_].append(e.text)
        else:
            ents["MISC"].append(e.text)
    # dedupe
    for k in ents:
        ents[k] = list(dict.fromkeys(ents[k]))[:20]
    return ents

def find_dates(text: str) -> List[str]:
    # look for date-like substrings; use dateparser to normalize
    res = set()
    # quick regex for YYYY or Month words
    patterns = [
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{0,4}",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{4}\b"
    ]
    for pat in patterns:
        for m in re.findall(pat, text, flags=re.IGNORECASE):
            parsed = dateparser.parse(m)
            if parsed:
                res.add(parsed.date().isoformat())
    # fallback: try sentence-level parse
    for sent in text.split("."):
        dt = dateparser.parse(sent)
        if dt:
            res.add(dt.date().isoformat())
    return sorted(res)

def openai_summarize(texts: List[str], prompt_extra: str="") -> str:
    if not OPENAI_KEY:
        return "OpenAI API key not provided; cannot run LLM summarization. Set OPENAI_API_KEY in environment."
    combined = "\n\n---\n\n".join([t[:4000] for t in texts])
    system_prompt = (
        "You are an assistant that reads multiple news articles and writes a concise timeline of events, "
        "listing chronological milestones with short descriptions (date → event). Also produce a short summary and note any conflicting claims among the sources."
    )
    user_prompt = f"{prompt_extra}\n\nArticles:\n{combined}\n\nProduce: (1) timeline bullets with ISO dates, (2) 2-paragraph summary, (3) 'Conflicts:' short notes"
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini", # use available model or gpt-4 if user prefers
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM summarization failed: {e}"

def lightweight_summary(texts: List[str]) -> str:
    # simple heuristics fallback: join first sentences
    bullets = []
    for t in texts:
        s = t.strip().split("\n")
        if s:
            intro = s[0][:250]
            bullets.append(intro)
    summary = " ".join(bullets[:5])
    if len(summary) > 1000:
        summary = summary[:1000] + "..."
    return summary
