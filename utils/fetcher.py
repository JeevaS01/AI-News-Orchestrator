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
