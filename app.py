from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st

st.write("DEBUG: NEWSAPI_KEY loaded:", bool(os.getenv("NEWSAPI_KEY")))
st.write("DEBUG: OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))
# Optionally print the first 6 chars to confirm (do NOT reveal real key publicly)
if os.getenv("NEWSAPI_KEY"):
    st.write("NEWSAPI_KEY starts with:", os.getenv("NEWSAPI_KEY")[:6])


import streamlit as st
from utils.fetcher import aggregate_articles
from utils.nlp import extract_entities, find_dates, openai_summarize, lightweight_summary
from utils.timeline import build_milestones_from_entities, plot_timeline
import pandas as pd

# Page config
st.set_page_config(page_title="AI News Orchestrator", layout="wide")

# -----------------------------
# Inject custom CSS for dashboard
# -----------------------------
st.markdown("""
<style>
/* Global page style */
[data-testid="root"] .main {
    background: #ffffff;
    min-height: 100vh;
    padding: 3rem !important;
    font-family: 'Segoe UI', Tahoma, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Glass card panels */
.glass-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 2rem;
    max-width: 1000px;
    width: 100%;
    box-shadow: 0 12px 30px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.05);
}

/* Centered gradient title */
.header-title {
    font-size: 50px;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #5b4bff, #9b59d0, #ff6fb0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.header-sub {
    font-size: 20px;
    text-align: center;
    color: #666666;
    margin-bottom: 1.5rem;
}

/* Gradient buttons */
.stButton>button {
    background: linear-gradient(90deg, #5b4bff, #9b59d0);
    color: white;
    font-weight: bold;
    border-radius: 12px;
    padding: 0.8rem 1.8rem;
    transition: 0.3s ease;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #6c5dff, #ba6dff);
    transform: scale(1.05);
}

/* Inputs */
.stTextInput>div>div>input {
    background: rgba(245,245,245,0.95) !important;
    border-radius: 10px !important;
    border: 1px solid #ddd !important;
    padding: 0.6rem 1rem !important;
}

/* Timeline boxes */
.timeline-box {
    background: #ffffff;
    box-shadow: 0 6px 15px rgba(0,0,0,0.05);
    padding: 1rem;
    border-radius: 16px;
    border-left: 6px solid #9b59d0;
    margin-bottom: 1.2rem;
}
.timeline-item {
    background: linear-gradient(90deg, #5b4bff, #9b59d0);
    color: white;
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 8px;
}

/* Tabs style */
.stTabs [role="tablist"] {
    background: rgba(255,255,255,0.8);
    border-radius: 14px;
    padding: 0.6rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 6px 15px rgba(0,0,0,0.06);
}
.stTabs [role="tab"] {
    font-weight: 700;
    padding: 0.6rem 1.2rem;
    border-radius: 10px;
    margin-right: 0.6rem;
}

/* Footer */
.footer {
    text-align: center;
    font-size: 0.9rem;
    color: #999999;
    padding: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Centered Glass Card with Title and Inputs
# -----------------------------
#st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

st.markdown('<div class="header-title">AI News Orchestrator</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">🧠 Event Timeline Generator & Multi-Source News Analyzer</div>', unsafe_allow_html=True)

st.subheader("🔍 Enter An Event Or Topic")
query = st.text_input(
    "Event / Topic (e.g., 'Chandrayaan-3 mission', 'OpenAI GPT-5 launch')",
    value="Chandrayaan-3 mission"
)

cols = st.columns([1, 1, 1, 2])
with cols[0]:
    max_articles = st.number_input("Max articles", min_value=3, max_value=20, value=8, step=1)
with cols[1]:
    use_openai = st.checkbox("Use OpenAI summarization", value=True)
with cols[2]:
    run_button = st.button("🚀 Generate Timeline")
with cols[3]:
    st.write("")

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Main Logic
# -----------------------------
if run_button and query.strip():
    with st.spinner("Fetching articles and building timeline..."):
        articles = aggregate_articles(query, max_articles)
        if not articles:
            st.warning("No articles found. Check NEWSAPI_KEY or internet connection.")
        for a in articles:
            a['entities'] = extract_entities(a.get('content', '') or a.get('title', ''))
            a['dates_found'] = find_dates((a.get('content') or "") + " " + (a.get('title') or ""))
        milestones = build_milestones_from_entities(articles)
        texts = [a.get('content') or a.get('title') or "" for a in articles]
        summary_text = openai_summarize(texts) if use_openai else lightweight_summary(texts)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🕒 Timeline", "🧠 Summary", "📊 Sources"])

    with tab1:
        st.markdown("### Timeline")
        fig = plot_timeline(milestones)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No date-tagged milestones; showing articles below.")
        for m in milestones:
            date = m.get("date") or "Unknown date"
            st.markdown(f"""
            <div class='timeline-box'>
                <span class='timeline-item'>{date}</span>
                <h4>{m.get('headline')}</h4>
                <p>{m.get('description')}</p>
                <a href='{m.get('url')}' target='_blank'>🔗 Source</a>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### 🧠 Event Summary")
        st.write(summary_text)

    with tab3:
        st.markdown("### 📊 Sources & Authenticity")
        rows = []
        for a in articles:
            len_text = len((a.get('content') or "").strip())
            score = min(100, max(30, int(len_text / 50)))
            rows.append({
                "source": a.get("source") or "Unknown",
                "title": a.get("title") or "",
                "url": a.get("url"),
                "score": score
            })
        df = pd.DataFrame(rows)
        # Safe rendering of the source table (prevents KeyError if df is missing columns)
expected_cols = ['source','title','score']
available = [c for c in expected_cols if c in df.columns]
if available:
    st.dataframe(df[available])
else:
    st.warning("No article scoring data available.")



# Footer
st.markdown("""
<hr>
<div class='footer'>
  Built with ❤️ by Jeeva | Powered by Streamlit & OpenAI
</div>
""", unsafe_allow_html=True)


