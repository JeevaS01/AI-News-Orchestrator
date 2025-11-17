import streamlit as st
import pandas as pd
import os
from utils.fetcher import aggregate_articles
from utils.nlp import extract_entities, find_dates, openai_summarize, lightweight_summary

st.set_page_config(page_title="AI News Orchestrator", layout="wide")

# --------------------------------------------------------
# HEADER
# --------------------------------------------------------
st.title("📰 AI News Orchestrator")
st.write("Search news, extract insights, generate summaries & build event timelines.")


# --------------------------------------------------------
# SIDEBAR SETTINGS
# --------------------------------------------------------
st.sidebar.header("⚙ Configuration")

query = st.sidebar.text_input("Search topic:", value="AI")
llm_option = st.sidebar.selectbox(
    "Summarization Mode",
    ["LLM (OpenAI)", "Lightweight (Offline)"]
)
btn_fetch = st.sidebar.button("Fetch & Analyze News")


# --------------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------------
if btn_fetch:

    st.info(f"Fetching latest articles for **{query}** ...")

    articles = aggregate_articles(query=query)

    if not articles:
        st.error("No articles found or API error. Check NEWSAPI_KEY in secrets.")
        st.stop()

    st.success(f"Fetched {len(articles)} articles.")

    # -----------------------------------------------
    # SHOW ARTICLE LIST
    # -----------------------------------------------
    st.subheader("📄 Articles Fetched")

    df = pd.DataFrame([
        {
            "Title": a["title"],
            "Source": a["source"],
            "Published": a["published"],
            "URL": a["url"]
        }
        for a in articles
    ])

    st.dataframe(df, use_container_width=True)

    # -----------------------------------------------
    # PROCESS CONTENT
    # -----------------------------------------------
    texts = [a["content"] for a in articles]

    # Extract entities
    st.subheader("🔍 Named Entities (Lightweight)")

    all_ents = {}
    for a in articles:
        ents = extract_entities(a["content"])
        for k, v in ents.items():
            all_ents.setdefault(k, []).extend(v)

    # Deduplicate
    for k in all_ents:
        all_ents[k] = list(dict.fromkeys(all_ents[k]))

    st.json(all_ents)

    # Extract dates
    st.subheader("📅 Dates Detected (Heuristic)")
    collected_dates = []
    for a in texts:
        collected_dates.extend(find_dates(a))

    collected_dates = sorted(list(dict.fromkeys(collected_dates)))
    st.write(collected_dates)

    # -----------------------------------------------
    # SUMMARIZATION
    # -----------------------------------------------
    st.subheader("📝 Summary & Timeline")

    if llm_option == "LLM (OpenAI)":
        st.info("Using OpenAI model for summarization...")
        output = openai_summarize(texts)
    else:
        st.info("Using local lightweight summarizer...")
        output = lightweight_summary(texts)

    st.write(output)

    # -----------------------------------------------
    # RAW ARTICLE TEXT
    # -----------------------------------------------
    st.subheader("📚 Raw Article Texts")

    for idx, art in enumerate(articles):
        with st.expander(f"{idx+1}. {art['title']}"):
            st.write(f"**Source:** {art['source']}")
            st.write(f"**Published:** {art['published']}")
            st.write("---")
            st.write(art["content"])
            st.markdown(f"[Read Original Article]({art['url']})")


else:
    st.info("Enter a topic and click **Fetch & Analyze News** to begin.")
