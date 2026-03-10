import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

SYSTEM_INSTRUCTION = """You are {chatbot_role}. You answer questions based ONLY on
the data summaries provided below. Follow these rules strictly:

- Use the exact numbers from the data context. Never invent or estimate figures.
- If the data context does not contain enough information to answer, say so clearly.
- Format responses with markdown for readability (bold key numbers, use tables when comparing).
- Keep answers concise and actionable — aim for 2-4 short paragraphs max.
- When discussing sentiment, always reference the actual counts or percentages.
- When ranking platforms or content types, show the numbers that support the ranking.

DATA CONTEXT:
{data_context}"""


def get_ai_provider() -> str:
    return st.session_state.get("ai_provider", "gemini")


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            api_key = (
                st.secrets.get("GOOGLE_API_KEY", "").strip()
                or st.secrets.get("GEMINI_API_KEY", "").strip()
            )
        except Exception:
            pass
    if not api_key:
        return None
    from google import genai

    return genai.Client(api_key=api_key)


def get_eadp_client():
    from utils.ai_analysis import get_eadp_client as _get_eadp
    return _get_eadp()


def get_ai_client():
    """Return the appropriate AI client based on the active provider."""
    if get_ai_provider() == "eadp":
        return get_eadp_client()
    return get_gemini_client()


def build_data_context():
    sections = []

    pp = st.session_state.get("post_performance")
    if pp is not None and len(pp) > 0:
        total_imp = pp["Impressions"].sum()
        total_eng = pp["Engagements"].sum()
        eng_rate = (total_eng / total_imp * 100) if total_imp > 0 else 0
        date_min = pp["Date"].min().strftime("%Y-%m-%d")
        date_max = pp["Date"].max().strftime("%Y-%m-%d")

        platform_stats = (
            pp.groupby("Network")
            .agg(Posts=("Engagements", "size"), Impressions=("Impressions", "sum"), Engagements=("Engagements", "sum"))
            .sort_values("Engagements", ascending=False)
        )
        platform_lines = "\n".join(
            f"  - {row.Index}: {int(row.Posts)} posts, {int(row.Impressions):,} impressions, {int(row.Engagements):,} engagements"
            for row in platform_stats.itertuples()
        )

        content_stats = (
            pp.groupby("Content Type")
            .agg(Posts=("Engagements", "size"), Engagements=("Engagements", "sum"), Impressions=("Impressions", "sum"))
            .sort_values("Engagements", ascending=False)
        )
        content_lines = "\n".join(
            f"  - {row.Index}: {int(row.Posts)} posts, {int(row.Engagements):,} engagements, {int(row.Impressions):,} impressions"
            for row in content_stats.itertuples()
        )

        top_posts = pp.nlargest(5, "Engagements")
        top_lines = "\n".join(
            f"  {i+1}. [{row['Network']}] {str(row.get('Post', ''))[:100]} — "
            f"{int(row['Engagements']):,} eng, {int(row['Impressions']):,} imp"
            for i, (_, row) in enumerate(top_posts.iterrows())
        )

        sections.append(
            f"""POST PERFORMANCE ({date_min} to {date_max}):
  Total posts: {len(pp):,}
  Total impressions: {int(total_imp):,}
  Total engagements: {int(total_eng):,}
  Overall engagement rate: {eng_rate:.2f}%
  Total comments: {int(pp['Comments'].sum()):,}
  Total shares: {int(pp['Shares'].sum()):,}
  Total video views: {int(pp['Video Views'].sum()):,}

  By platform:
{platform_lines}

  By content type:
{content_lines}

  Top 5 posts by engagement:
{top_lines}"""
        )

    prof = st.session_state.get("profile_performance")
    if prof is not None and len(prof) > 0:
        audience_by_net = (
            prof.sort_values("Date")
            .groupby("Network")
            .last()[["Audience", "Net Audience Growth"]]
        )
        audience_total = prof.groupby("Network")["Audience"].max().sum()
        net_growth = prof["Net Audience Growth"].sum()

        aud_lines = "\n".join(
            f"  - {net}: audience {int(row['Audience']):,}, net growth {int(row['Net Audience Growth']):,}"
            for net, row in audience_by_net.iterrows()
        )

        sections.append(
            f"""PROFILE / AUDIENCE:
  Total audience (latest): {int(audience_total):,}
  Net audience growth (period): {int(net_growth):,}

  By platform:
{aud_lines}"""
        )

    aff = st.session_state.get("affogata")
    if aff is not None and len(aff) > 0:
        sent_counts = aff["Sentiment"].value_counts()
        sent_lines = ", ".join(f"{k}: {v:,}" for k, v in sent_counts.items())
        aff_platforms = aff["Network Name"].value_counts()
        plat_lines = ", ".join(f"{k}: {v:,}" for k, v in aff_platforms.head(10).items())

        top_aff = aff.nlargest(3, "Total Engagements")
        top_aff_lines = "\n".join(
            f"  - [{row['Network Name']}] {str(row['Text'])[:120]} (engagements: {int(row['Total Engagements']):,})"
            for _, row in top_aff.iterrows()
        )

        sections.append(
            f"""COMMUNITY CONVERSATIONS (Affogata):
  Total conversations: {len(aff):,}
  Sentiment: {sent_lines}
  Platforms: {plat_lines}

  Top engaged messages:
{top_aff_lines}"""
        )

    inbox = st.session_state.get("inbox")
    if inbox is not None and len(inbox) > 0:
        inbox_sent = inbox["Sentiment"].value_counts() if "Sentiment" in inbox.columns else {}
        sent_str = ", ".join(f"{k}: {v:,}" for k, v in inbox_sent.items()) if len(inbox_sent) > 0 else "N/A"
        inbox_nets = inbox["Network"].value_counts() if "Network" in inbox.columns else {}
        net_str = ", ".join(f"{k}: {v:,}" for k, v in inbox_nets.items()) if len(inbox_nets) > 0 else "N/A"

        sections.append(
            f"""INBOX MESSAGES (Sprout):
  Total messages: {len(inbox):,}
  Sentiment: {sent_str}
  By network: {net_str}"""
        )

    looker = st.session_state.get("looker_sentiment")
    if looker is not None and len(looker) > 0:
        avg_score = looker["Impact Score"].mean()
        max_row = looker.loc[looker["Impact Score"].idxmax()]
        min_row = looker.loc[looker["Impact Score"].idxmin()]
        date_min_l = looker["Date"].min().strftime("%Y-%m-%d")
        date_max_l = looker["Date"].max().strftime("%Y-%m-%d")

        sections.append(
            f"""LOOKER SENTIMENT ({date_min_l} to {date_max_l}):
  Days tracked: {len(looker)}
  Average Impact Score: {avg_score:.1f}
  Highest: {max_row['Impact Score']:.1f} on {max_row['Date'].strftime('%b %d, %Y')}
  Lowest: {min_row['Impact Score']:.1f} on {min_row['Date'].strftime('%b %d, %Y')}"""
        )

    if not sections:
        return "No data is currently loaded."

    return "\n\n".join(sections)


def _stream_gemini(client, messages, system):
    from google.genai import types

    contents = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )

    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.3,
        ),
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text


def _stream_eadp(client, messages, system):
    from utils.ai_analysis import EADP_MODELS

    oai_messages = [{"role": "system", "content": system}]
    for msg in messages:
        oai_messages.append({"role": msg["role"], "content": msg["content"]})

    last_error = None
    for model in EADP_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=oai_messages,
                temperature=0.3,
                max_tokens=4000,
                stream=True,
            )
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return
        except Exception as e:
            last_error = e
            if "not found" in str(e).lower():
                continue
            raise

    raise RuntimeError(
        f"No EADP models are currently available. Last error: {last_error}"
    )


def stream_chat_response(client, messages, data_context):
    from utils.titles import get_title_config

    cfg = get_title_config()
    system = SYSTEM_INSTRUCTION.format(
        chatbot_role=cfg["chatbot_role"],
        data_context=data_context,
    )

    if get_ai_provider() == "eadp":
        yield from _stream_eadp(client, messages, system)
    else:
        yield from _stream_gemini(client, messages, system)
