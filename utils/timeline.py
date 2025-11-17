# utils/timeline.py
from typing import List, Dict
import pandas as pd
import plotly.express as px
from dateutil import parser as du_parser
import dateparser
import numpy as np

from typing import List, Dict
import dateparser

def build_milestones_from_entities(articles: List[Dict]) -> List[Dict]:
    items = []

    for a in articles:
        date = a.get("publishedAt")

        # Normalize using dateparser
        if date:
            dt = dateparser.parse(date)
            iso = dt.date().isoformat() if dt else None
        else:
            iso = None

        title = a.get("title") or ""
        text = a.get("content") or ""

        items.append({
            "date": iso,
            "headline": title[:120],
            "description": (text[:400] + "...") if text else "",
            "url": a.get("url"),
            "source": a.get("source")
        })

    # Sort by date (None values go to the end)
    items_sorted = sorted(items, key=lambda x: x["date"] if x["date"] else "9999-12-31")
    return items_sorted

def plot_timeline(milestones: List[Dict]):
    # create DataFrame for plotly scatter
    df = []
    for m in milestones:
        if not m.get("date"):
            continue
        df.append({"date": m["date"], "label": m["headline"], "source": m["source"]})
    if not df:
        return None
    df = pd.DataFrame(df)
    df['date'] = pd.to_datetime(df['date'])
    # place y jitter to avoid overlap
    n = len(df)
    df['y'] = np.linspace(1, 1.8, n)
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

