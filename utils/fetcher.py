# # utils/fetcher.py
# import requests
# from bs4 import BeautifulSoup
# import dateparser
# from typing import List, Dict
# import re
# import os

# NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")


# # -------------------------------------------------------------
# # 1. Fetch headlines from NewsAPI
# # -------------------------------------------------------------
# def fetch_news(query: str = "technology", limit: int = 10) -> List[Dict]:
#     """
#     Fetch news articles from NewsAPI.
#     """
#     if not NEWSAPI_KEY:
#         return []

#     url = (
#         f"https://newsapi.org/v2/everything?"
#         f"q={query}&language=en&sortBy=publishedAt&pageSize={limit}&apiKey={NEWSAPI_KEY}"
#     )

#     try:
#         response = requests.get(url, timeout=10)
#         data = response.json()

#         if data.get("status") != "ok":
#             return []

#         return data.get("articles", [])

#     except Exception:
#         return []


# # -------------------------------------------------------------
# # 2. Extract clean text from article webpage (no newspaper3k)
# # -------------------------------------------------------------
# def extract_full_text(url: str) -> str:
#     """
#     Extract readable text from a URL using BeautifulSoup.
#     Works on Streamlit Cloud (no lxml required).
#     """

#     try:
#         html = requests.get(url, timeout=10).text
#         soup = BeautifulSoup(html, "html.parser")

#         # Prefer meta description
#         meta_desc = soup.find("meta", {"name": "description"})
#         if meta_desc and meta_desc.get("content"):
#             return meta_desc["content"]

#         # Collect paragraph text
#         paragraphs = soup.find_all("p")
#         text = " ".join(p.get_text(strip=True) for p in paragraphs)

#         # Fallback
#         return text[:5000] if text.strip() else "Content not available."

#     except Exception:
#         return "Failed to fetch article."


# # -------------------------------------------------------------
# # 3. Clean text (remove scripts, ads, unrelated garbage)
# # -------------------------------------------------------------
# def clean_text(text: str) -> str:
#     if not text:
#         return ""

#     # remove URLs
#     text = re.sub(r"http\S+", "", text)

#     # remove multiple spaces
#     text = re.sub(r"\s+", " ", text)

#     return text.strip()


# # -------------------------------------------------------------
# # 4. Build a unified list of processed articles
# # -------------------------------------------------------------
# def aggregate_articles(query: str) -> List[Dict]:
#     """
#     Fetch articles → extract full text → clean → return structured list.
#     """
#     raw_articles = fetch_news(query=query, limit=10)
#     processed = []

#     if not raw_articles:
#         return []

#     for art in raw_articles:
#         url = art.get("url")
#         title = art.get("title", "")
#         source = art.get("source", {}).get("name", "")
#         published_at = art.get("publishedAt", "")

#         full_text = extract_full_text(url)
#         full_text = clean_text(full_text)

#         processed.append({
#             "title": title,
#             "source": source,
#             "url": url,
#             "published": published_at,
#             "content": full_text
#         })

#     return processed
# utils/fetcher.py
import os
import requests
from newspaper import Article
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlencode
import time

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")  # set in env

def fetch_from_newsapi(query: str, page_size: int = 8) -> List[Dict]:
    if not NEWSAPI_KEY:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "apiKey": NEWSAPI_KEY
    }
    r = requests.get(url, params=params, timeout=12)
    out = []
    if r.ok:
        data = r.json()
        for art in data.get("articles", []):
            out.append({
                "title": art.get("title"),
                "publishedAt": art.get("publishedAt"),
                "url": art.get("url"),
                "source": art.get("source", {}).get("name"),
                "raw": art
            })
    return out

def fetch_from_gnews(query: str, page_size: int = 8) -> List[Dict]:
    # lightweight fallback using Google News RSS search
    q = urlencode({"q": query})
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    r = requests.get(rss_url, timeout=10)
    out = []
    if r.ok:
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")[:page_size]
        for it in items:
            link = it.link.text
            out.append({
                "title": it.title.text,
                "publishedAt": it.pubDate.text if it.pubDate else None,
                "url": link,
                "source": it.source.text if it.source else None,
                "raw": None
            })
    return out

def extract_full_text(url: str) -> str:
    try:
        art = Article(url)
        art.download()
        art.parse()
        if art.text and len(art.text) > 50:
            return art.text
    except Exception:
        pass
    # fallback simple scrape:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.content, "html.parser")
        paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
        joined = "\n\n".join([p for p in paragraphs if len(p) > 30])
        return joined[:20000]
    except Exception:
        return ""

def aggregate_articles(query: str, max_articles: int = 8) -> List[Dict]:
    articles = fetch_from_newsapi(query, page_size=max_articles)
    if len(articles) < max_articles:
        g = fetch_from_gnews(query, page_size=max_articles - len(articles))
        articles.extend(g)
    # Deduplicate by URL or title
    seen = set()
    dedup = []
    for a in articles:
        key = (a.get("url") or a.get("title")).strip()
        if key in seen: continue
        seen.add(key)
        # get full text
        a["content"] = extract_full_text(a.get("url", "")) or ""
        dedup.append(a)
    return dedup[:max_articles]


