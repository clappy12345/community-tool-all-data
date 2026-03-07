import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ask the Data", page_icon="💬", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.chatbot import get_gemini_client, build_data_context, stream_chat_response
from utils.processors import format_number


def _build_suggested_questions():
    """Generate context-aware suggested questions based on loaded data."""
    questions = []

    pp = st.session_state.get("post_performance")
    if pp is not None and len(pp) > 0:
        networks = sorted(pp["Network"].dropna().unique().tolist())
        if len(networks) >= 2:
            questions.append(f"Compare engagement between {networks[0]} and {networks[1]}")
        top = pp.nlargest(1, "Engagements")
        if len(top) > 0:
            questions.append("What was our best performing post and why?")
        if "Content Type" in pp.columns:
            questions.append("Which content type drives the most engagement?")

    aff = st.session_state.get("affogata")
    if aff is not None and len(aff) > 0:
        questions.append("What are the top community complaints?")
        questions.append("What topics are people most positive about?")

    looker = st.session_state.get("looker_sentiment")
    if looker is not None and len(looker) > 0:
        questions.append("How has sentiment trended over the period?")

    prof = st.session_state.get("profile_performance")
    if prof is not None and len(prof) > 0:
        questions.append("How did our audience grow over the period?")

    inbox = st.session_state.get("inbox")
    if inbox is not None and len(inbox) > 0:
        questions.append("What are the most common themes in inbox messages?")

    defaults = [
        "Which platform has the best engagement rate?",
        "What's the overall sentiment breakdown?",
        "Give me an executive summary of the data",
        "What should we focus on improving?",
        "What content resonated most with the community?",
        "What are people most negative about?",
    ]
    for d in defaults:
        if d not in questions:
            questions.append(d)

    return questions[:9]

filters = render_sidebar()
apply_theme()
require_data()

st.title("💬 Ask the Data")
st.markdown("*Ask natural-language questions about your social and community data*")
st.divider()

client = get_gemini_client()

if client is None:
    st.warning(
        "**Google API key not found.** To use the chatbot:\n\n"
        "1. Go to [aistudio.google.com](https://aistudio.google.com) and sign in with a Google account\n"
        "2. Click **Get API Key** and create a free key (no credit card required)\n"
        "3. Add `GOOGLE_API_KEY=your_key_here` to your `.env` file\n"
        "4. Restart the app"
    )
    st.stop()

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

col_header, col_clear = st.columns([5, 1])
with col_clear:
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["chat_messages"] = []
        st.rerun()

if not st.session_state["chat_messages"]:
    st.markdown("#### Ask anything about your loaded data")
    st.markdown(
        "The chatbot has access to summaries of all your uploaded datasets "
        "(post performance, profile metrics, community conversations, and inbox messages)."
    )

    suggested = _build_suggested_questions()

    cols = st.columns(3)
    for i, example in enumerate(suggested):
        with cols[i % 3]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state["chat_messages"].append(
                    {"role": "user", "content": example}
                )
                st.rerun()

for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state["chat_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

if (
    st.session_state["chat_messages"]
    and st.session_state["chat_messages"][-1]["role"] == "user"
):
    data_context = build_data_context()

    with st.chat_message("assistant"):
        try:
            response_text = st.write_stream(
                stream_chat_response(
                    client, st.session_state["chat_messages"], data_context
                )
            )
            st.session_state["chat_messages"].append(
                {"role": "assistant", "content": response_text}
            )
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg:
                st.error("Invalid Google API key. Check the key in your `.env` file (no extra spaces).")
            elif "RESOURCE_EXHAUSTED" in error_msg or "RATE_LIMIT" in error_msg:
                st.error(
                    "Gemini quota exhausted. The free tier allows 15 requests/min and "
                    "1,500/day. Wait a moment and try again, or check your quota at "
                    "[ai.dev/rate-limit](https://ai.dev/rate-limit)."
                )
            else:
                st.error(f"Gemini error: {error_msg}")
