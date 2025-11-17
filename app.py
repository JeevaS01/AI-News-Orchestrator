import streamlit as st
import pandas as pd
from datetime import datetime
from utils.fetcher import aggregate_articles
from utils.nlp import extract_entities, find_dates, openai_summarize, lightweight_summary

st.set_page_config(page_title="AI News Orchestrator", layout="wide")

# ---------------------------------------------------------
# CUSTOM CSS (same as old UI)
# ---------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        color: #2E86C1;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 28px;
        font-weight: 700;
        color: #1A5276;
        margin-top: 40px;
    }
    .card {
        padding: 18px;
        border-radius: 12px;
        background-color: #F8F9F9;
        border: 1px solid #D5D8DC;
        margin-bottom: 16px;
    }
    .article-card {
        background: white;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #E5E7E9;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown("<h1 class='main-title'>📰 AI News Orchestrator</h1>", unsafe_allow_html=True)
st.write("Search global news → extract insights → build AI-generated timelines.")

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("🔍 Search Settings")

query = st.sidebar.text_input("Enter a topic:", value="AI")
mode = st.sidebar.radio("Summarization Mode:", ["LLM", "Lightweight"])
btn = st.sidebar.button("Run Analysis")

# ---------------------------------------------------------
# MAIN ACTION
# ---------------------------------------------------------
if btn:
    st.markdown("<h2 class='section-title'>1️⃣ Fetching News</h2>", unsafe_allow_html=True)

    with st.spinner(f"Fetching latest news for '{query}' ..."):
        articles = aggregate_articles(query=query)

    if not articles:
        st.error("No news found. Check API key or try different keywords.")
        st.stop()

    st.success(f"Fetched {len(articles)} articles.")

    # ---------------------------------------------------------
    # ARTICLE LIST VIEW (old UI style)
    # ---------------------------------------------------------
    st.markdown("<h2 class='section-title'>2️⃣ Articles Found</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    for i, art in enumerate(articles):
        target_col = [col1, col2, col3][i % 3]
        with target_col:
            st.markdown(f"""
            <div class='article-card'>
                <h4>{art['title']}</h4>
                <p><b>Source:</b> {art['source']}</p>
                <p><b>Date:</b> {art['published']}</p>
                <a href='{art['url']}' target='_blank'>Read full article</a>
            </div>
            """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # ENTITY EXTRACTION
    # ---------------------------------------------------------
    st.markdown("<h2 class='section-title'>3️⃣ Extracted Entities</h2>", unsafe_allow_html=True)

    all_ents = {"PERSON":[], "ORG":[], "GPE":[], "EVENT":[], "MISC":[]}

    for a in articles:
        ents = extract_entities(a["content"])
        for k, v in ents.items():
            all_ents[k].extend(v)

    # Dedupe
    for k in all_ents:
        all_ents[k] = list(dict.fromkeys(all_ents[k]))

    st.json(all_ents)

    # ---------------------------------------------------------
    # DATE TIMELINE
    # ---------------------------------------------------------
    st.markdown("<h2 class='section-title'>4️⃣ Timeline (Auto-Extracted Dates)</h2>", unsafe_allow_html=True)

    date_list = []
    for a in articles:
        date_list += find_dates(a["content"])

    date_list = sorted(list(dict.fromkeys(date_list)))

    if date_list:
        for d in date_list:
            st.markdown(f"- **{d}**")
    else:
        st.info("No dates detected.")

    # ---------------------------------------------------------
    # SUMMARIZATION OUTPUT BOX
    # ---------------------------------------------------------
    st.markdown("<h2 class='section-title'>5️⃣ AI Summary</h2>", unsafe_allow_html=True)

    texts = [a["content"] for a in articles]

    with st.spinner("Generating summary..."):
        if mode == "LLM":
            summary = openai_summarize(texts)
        else:
            summary = lightweight_summary(texts)

    st.markdown(f"""
    <div class='card'>
        <h4>Summary</h4>
        <p>{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # RAW TEXT EXPANDERS
    # ---------------------------------------------------------
    st.markdown("<h2 class='section-title'>6️⃣ Full Article Text</h2>", unsafe_allow_html=True)

    for i, art in enumerate(articles):
        with st.expander(f"{i+1}. {art['title']}"):
            st.write(art["content"])

else:
    st.info("Enter a topic → click **Run Analysis** to begin.")
