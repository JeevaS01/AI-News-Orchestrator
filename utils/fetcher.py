# utils/fetcher.py
import requests
from bs4 import BeautifulSoup
import dateparser
from typing import List, Dict
import re
import os

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")


# -------------------------------------------------------------
# 1. Fetch headlines from NewsAPI
# -------------------------------------------------------------
def fetch_news(query: str = "technology", limit: int = 10) -> List[Dict]:
    """
    Fetch news articles from NewsAPI.
    """
    if not NEWSAPI_KEY:
        return []

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=publishedAt&pageSize={limit}&apiKey={NEWSAPI_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return []

        return data.get("articles", [])

    except Exception:
        return []


# -------------------------------------------------------------
# 2. Extract clean text from article webpage (no newspaper3k)
# -------------------------------------------------------------
def extract_full_text(url: str) -> str:
    """
    Extract readable text from a URL using BeautifulSoup.
    Works on Streamlit Cloud (no lxml required).
    """

    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        # Prefer meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"]

        # Collect paragraph text
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)

        # Fallback
        return text[:5000] if text.strip() else "Content not available."

    except Exception:
        return "Failed to fetch article."


# -------------------------------------------------------------
# 3. Clean text (remove scripts, ads, unrelated garbage)
# -------------------------------------------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""

    # remove URLs
    text = re.sub(r"http\S+", "", text)

    # remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -------------------------------------------------------------
# 4. Build a unified list of processed articles
# -------------------------------------------------------------
def aggregate_articles(query: str) -> List[Dict]:
    """
    Fetch articles → extract full text → clean → return structured list.
    """
    raw_articles = fetch_news(query=query, limit=10)
    processed = []

    if not raw_articles:
        return []

    for art in raw_articles:
        url = art.get("url")
        title = art.get("title", "")
        source = art.get("source", {}).get("name", "")
        published_at = art.get("publishedAt", "")

        full_text = extract_full_text(url)
        full_text = clean_text(full_text)

        processed.append({
            "title": title,
            "source": source,
            "url": url,
            "published": published_at,
            "content": full_text
        })

    return processed
