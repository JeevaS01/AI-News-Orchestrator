# utils/timeline.py
from typing import List, Dict
import pandas as pd
import plotly.express as px
from dateutil import parser as du_parser
import dateparser
import numpy as np

from typing import List, Dict
import dateparser

# def build_milestones_from_entities(articles: List[Dict]) -> List[Dict]:
#     items = []

#     for a in articles:
#         # Try publishedAt first
#         raw_date = a.get("publishedAt")
#         dt = dateparser.parse(raw_date) if raw_date else None

#         # Fallback: use first extracted date from content/title
#         if not dt and a.get("dates_found"):
#             dt = dateparser.parse(a["dates_found"][0])

#         iso = dt.date().isoformat() if dt else None

#         title = a.get("title") or ""
#         text = a.get("content") or ""

#         items.append({
#             "date": iso,
#             "headline": title[:120],
#             "description": (text[:400] + "...") if text else "",
#             "url": a.get("url"),
#             "source": a.get("source")
#         })

#     # Sort by date (None values go to the end)
#     items_sorted = sorted(items, key=lambda x: x["date"] if x["date"] else "9999-12-31")
#     return items_sorted
def build_milestones_from_entities(articles: List[Dict]) -> List[Dict]:
    items = []

    for a in articles:
        raw_date = a.get("publishedAt")

        # Try publishedAt first
        dt = dateparser.parse(raw_date) if raw_date else None

        # Fallback: use first extracted date from content/title
        if not dt and a.get("dates_found"):
            dt = dateparser.parse(a["dates_found"][0])

        # Final fallback: use today's date (optional)
        if not dt:
            continue  # or dt = datetime.now()

        iso = dt.date().isoformat()

        items.append({
            "date": iso,
            "headline": a.get("title", "")[:120],
            "description": (a.get("content", "")[:400] + "...") if a.get("content") else "",
            "url": a.get("url"),
            "source": a.get("source")
        })

    items_sorted = sorted(items, key=lambda x: x["date"])
    return items_sorted

def plot_timeline(milestones: List[Dict]):
    df = []

    for m in milestones:
        if not m.get("date"):
            continue
        try:
            parsed_date = pd.to_datetime(m["date"])
            df.append({
                "date": parsed_date,
                "label": m["headline"],
                "source": m["source"]
            })
        except Exception as e:
            print("Date parsing failed:", m["date"], e)

    if not df:
        return None

    df = pd.DataFrame(df)
    df['y'] = np.linspace(1, 1.8, len(df))

    fig = px.scatter(df, x='date', y='y', text='label', hover_data=['source'])
    fig.update_traces(marker=dict(size=18, symbol="diamond"))
    fig.update_yaxes(visible=False)
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=260,
        xaxis_title="Date",
        showlegend=False
    )
    return fig


