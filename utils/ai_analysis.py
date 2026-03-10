from __future__ import annotations

import json
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

EADP_BASE_URL = "https://corp-prod-eadp-ai-genai-gateway.data.ea.com/v1"
EADP_MODELS = [
    "vertex_ai/gemini-2.5-flash",
    "azure_ai/gpt-4.1",
    "bedrock/anthropic.claude-sonnet-4-20250514-v1:0",
    "azure_ai/gpt-4o",
    "eadp/openai/gpt-oss-20b",
]
EADP_MODEL = EADP_MODELS[0]


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
    from openai import OpenAI
    api_key = os.getenv("EADP_GATEWAY_API_KEY", "").strip()
    if not api_key:
        try:
            api_key = st.secrets.get("EADP_GATEWAY_API_KEY", "").strip()
        except Exception:
            pass
    if not api_key:
        return None
    return OpenAI(base_url=EADP_BASE_URL, api_key=api_key)


def discover_themes(messages_df, text_col="Text", n_sample=500):
    if get_ai_provider() == "gemini":
        client = get_gemini_client()
        if client is None:
            st.error("No Google API key found. Set GOOGLE_API_KEY in your .env file.")
            return None

    from utils.titles import get_title_config

    ai_context = get_title_config()["ai_context"]

    texts = messages_df[text_col].dropna()
    texts = texts[texts.str.strip() != ""]
    texts = texts[texts.str.len() > 20]

    if len(texts) > n_sample:
        sample = texts.sample(n_sample, random_state=42)
    else:
        sample = texts

    message_block = "\n---\n".join(t[:300] for t in sample.tolist())

    prompt = f"""Analyze these community messages about {ai_context}.
Identify the top 12-15 distinct themes or topics people are discussing.

For each theme, return a JSON object with:
- "name": Short theme name (2-4 words, e.g. "Gameplay Physics", "Be A Pro Mode")
- "description": One sentence summarizing what people are saying
- "sentiment_lean": "positive", "mixed", or "negative"
- "keywords": Array of 10-15 lowercase keywords/phrases that identify this theme

Return a JSON object with a single key "themes" containing an array of theme objects.

Community Messages:
{message_block}"""

    raw = _gemini_call(
        prompt,
        "You are an expert at analyzing gaming community conversations. Return valid JSON only.",
        temperature=0.3,
        max_tokens=8000,
        json_mode=True,
    )
    if raw is None:
        return None

    result = json.loads(raw)
    themes = result.get("themes", [])

    if isinstance(themes, dict):
        themes = list(themes.values())

    return themes


def classify_messages(messages_df, themes, text_col="Text"):
    if not themes:
        messages_df = messages_df.copy()
        messages_df["Theme"] = "Uncategorized"
        return messages_df

    theme_keywords = {}
    for theme in themes:
        name = theme["name"]
        keywords = [k.lower() for k in theme.get("keywords", [])]
        theme_keywords[name] = keywords

    def classify_text(text):
        if not isinstance(text, str) or text.strip() == "":
            return "Uncategorized"
        text_lower = text.lower()
        scores = {}
        for theme_name, keywords in theme_keywords.items():
            score = sum(1 for k in keywords if k in text_lower)
            if score > 0:
                scores[theme_name] = score
        if scores:
            return max(scores, key=scores.get)
        return "Uncategorized"

    messages_df = messages_df.copy()
    messages_df["Theme"] = messages_df[text_col].apply(classify_text)
    return messages_df


def get_theme_summary(classified_df):
    if "Theme" not in classified_df.columns:
        return None

    summary = (
        classified_df.groupby("Theme")
        .agg(
            Count=("Theme", "size"),
            Positive=("Sentiment", lambda x: (x == "positive").sum()),
            Negative=("Sentiment", lambda x: (x == "negative").sum()),
            Neutral=("Sentiment", lambda x: (x == "neutral").sum()),
        )
        .reset_index()
    )
    summary["Pct Positive"] = (summary["Positive"] / summary["Count"] * 100).round(1)
    summary["Pct Negative"] = (summary["Negative"] / summary["Count"] * 100).round(1)
    return summary.sort_values("Count", ascending=False)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

import pandas as pd


def build_report_context():
    """Build a comprehensive statistical context string from all session data.

    Uses only Looker for sentiment — Affogata/Inbox are volume-only.
    """
    from utils.titles import get_title_config
    from utils.processors import get_kpis_safe

    cfg = get_title_config()
    sections = [f"TITLE: {cfg['full_name']} by {cfg['publisher']}"]

    pp = st.session_state.get("post_performance")
    prof = st.session_state.get("profile_performance")
    aff = st.session_state.get("affogata")
    inbox = st.session_state.get("inbox")
    looker = st.session_state.get("looker_sentiment")

    if pp is not None and len(pp) > 0:
        date_min = pp["Date"].min().strftime("%B %d, %Y")
        date_max = pp["Date"].max().strftime("%B %d, %Y")
        sections.append(f"REPORTING PERIOD: {date_min} — {date_max}")

        kpis = get_kpis_safe(pp, prof)

        sections.append(
            f"PERFORMANCE KPIs:\n"
            f"  Total Posts: {int(kpis['total_posts']):,}\n"
            f"  Total Impressions: {int(kpis['total_impressions']):,}\n"
            f"  Total Engagements: {int(kpis['total_engagements']):,}\n"
            f"  Total Reach: {int(kpis['total_reach']):,}\n"
            f"  Avg Engagement Rate: {kpis['avg_engagement_rate']:.2f}%\n"
            f"  Total Comments: {int(kpis['total_comments']):,}\n"
            f"  Total Shares: {int(kpis['total_shares']):,}\n"
            f"  Total Video Views: {int(kpis['total_video_views']):,}\n"
            f"  Total Audience: {int(kpis['total_audience']):,}\n"
            f"  Net Audience Growth: {int(kpis['audience_growth']):,}"
        )

        plat_stats = (
            pp.groupby("Network")
            .agg(
                Posts=("Engagements", "size"),
                Impressions=("Impressions", "sum"),
                Engagements=("Engagements", "sum"),
                Comments=("Comments", "sum"),
                Shares=("Shares", "sum"),
                VideoViews=("Video Views", "sum"),
            )
            .sort_values("Engagements", ascending=False)
        )
        plat_lines = "\n".join(
            f"  - {r.Index}: {int(r.Posts)} posts, {int(r.Impressions):,} imp, "
            f"{int(r.Engagements):,} eng, {int(r.Comments):,} comments, "
            f"{int(r.Shares):,} shares, {int(r.VideoViews):,} video views"
            for r in plat_stats.itertuples()
        )
        sections.append(f"POST PERFORMANCE BY PLATFORM:\n{plat_lines}")

        ct_stats = (
            pp.groupby("Content Type")
            .agg(Posts=("Engagements", "size"), Engagements=("Engagements", "sum"), Impressions=("Impressions", "sum"))
            .sort_values("Engagements", ascending=False)
        )
        ct_lines = "\n".join(
            f"  - {r.Index}: {int(r.Posts)} posts, {int(r.Engagements):,} eng, {int(r.Impressions):,} imp"
            for r in ct_stats.itertuples()
        )
        sections.append(f"BY CONTENT TYPE:\n{ct_lines}")

        exclude = ["Story", "@Reply", "'@Reply"]
        top = pp[~pp["Post Type"].isin(exclude)].nlargest(10, "Engagements")
        top_lines = "\n".join(
            f"  {i+1}. [{row['Network']}] {str(row.get('Post', ''))[:120]} — "
            f"{int(row['Engagements']):,} eng, {int(row['Impressions']):,} imp"
            for i, (_, row) in enumerate(top.iterrows())
        )
        sections.append(f"TOP 10 POSTS BY ENGAGEMENT:\n{top_lines}")

    if prof is not None and len(prof) > 0:
        latest = prof["Date"].max()
        aud_by_net = prof[prof["Date"] == latest].groupby("Network")["Audience"].max()
        growth_by_net = prof.groupby("Network")["Net Audience Growth"].sum()
        aud_lines = "\n".join(
            f"  - {net}: audience {int(aud_by_net.get(net, 0)):,}, "
            f"growth {int(growth_by_net.get(net, 0)):,}"
            for net in sorted(set(aud_by_net.index) | set(growth_by_net.index))
        )
        sections.append(f"AUDIENCE BY PLATFORM:\n{aud_lines}")

    if aff is not None and len(aff) > 0:
        net_vol = aff["Network Name"].value_counts()
        net_str = "\n".join(f"  - {k}: {v:,} messages" for k, v in net_vol.items())
        sections.append(
            f"COMMUNITY CONVERSATIONS (Affogata): {len(aff):,} total\n"
            f"  By platform:\n{net_str}"
        )

    if inbox is not None and len(inbox) > 0:
        sections.append(f"INBOX MESSAGES (Sprout): {len(inbox):,} total")

    if looker is not None and len(looker) > 0:
        avg_score = looker["Impact Score"].mean()
        max_score = looker["Impact Score"].max()
        min_score = looker["Impact Score"].min()
        sections.append(
            f"LOOKER SENTIMENT:\n"
            f"  Days of data: {len(looker)}\n"
            f"  Avg Impact Score: {avg_score:.1f}\n"
            f"  Highest: {max_score:.1f}, Lowest: {min_score:.1f}"
        )

    return "\n\n".join(sections)


def combine_community_messages(aff_df=None, inbox_df=None):
    """Delegate to the canonical implementation in processors."""
    from utils.processors import combine_community_messages as _impl
    return _impl(aff_df, inbox_df)


# Keep backward-compatible alias for any existing imports
_combine_community_messages = combine_community_messages


_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]
_MAX_RETRIES = 4
_BASE_DELAY = 5


def _eadp_call(prompt, system_instruction, temperature=0.3, max_tokens=8000, json_mode=False):
    """Call the EA GenAI Gateway via the OpenAI SDK, trying multiple models."""
    client = get_eadp_client()
    if client is None:
        st.error("No EADP Gateway API key found. Set EADP_GATEWAY_API_KEY in your .env file.")
        return None
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt},
    ]
    last_error = None
    for model in EADP_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            err = str(e)
            if "not found" in err.lower():
                continue
            st.error(f"EA EADP API error ({model}): {e}")
            return None

    st.error(
        f"No EADP models are currently available. "
        f"The shared service may be temporarily down. Last error: {last_error}"
    )
    return None


def _gemini_call_impl(prompt, system_instruction, temperature=0.3, max_tokens=8000, json_mode=False):
    """Gemini API call with retry + model fallback."""
    import time
    import re

    client = get_gemini_client()
    if client is None:
        st.error("No Google API key found. Set GOOGLE_API_KEY in your .env file.")
        return None
    from google.genai import types

    config_kwargs = dict(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    config = types.GenerateContentConfig(**config_kwargs)

    for model in _GEMINI_MODELS:
        for attempt in range(_MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt, config=config,
                )
                return response.text
            except Exception as e:
                err = str(e)
                is_rate_limit = "429" in err or "RESOURCE_EXHAUSTED" in err

                if not is_rate_limit:
                    st.error(f"Gemini API error: {e}")
                    return None

                retry_match = re.search(r"retry\s*in\s*([\d.]+)", err, re.IGNORECASE)
                wait = float(retry_match.group(1)) + 1 if retry_match else _BASE_DELAY * (2 ** attempt)

                if "per_day" in err.lower() or "PerDay" in err:
                    break

                if attempt < _MAX_RETRIES - 1:
                    st.toast(f"Rate limited on {model} — retrying in {wait:.0f}s…")
                    time.sleep(wait)

        st.toast(f"Quota exhausted on {model}, trying next model…")

    st.error(
        "All Gemini models are rate-limited. The free tier allows ~20 requests/day "
        "for gemini-2.5-flash. Wait a minute and try again, or upgrade to a paid "
        "Google AI plan for higher limits."
    )
    return None


def _gemini_call(prompt, system_instruction, temperature=0.3, max_tokens=8000, json_mode=False):
    """Provider-aware AI call — dispatches to EADP or Gemini based on session state."""
    if get_ai_provider() == "eadp":
        return _eadp_call(prompt, system_instruction, temperature, max_tokens, json_mode)
    return _gemini_call_impl(prompt, system_instruction, temperature, max_tokens, json_mode)


def generate_executive_summary(context):
    """AI-generated 3-5 sentence executive summary."""
    from utils.titles import get_title_config
    cfg = get_title_config()

    prompt = f"""Write a 3-5 sentence executive summary for {cfg['publisher']} {cfg['full_name']}.

DATA CONTEXT:
{context}

Requirements:
- Open with the reporting period and the single most important headline number.
- Hit the 2-3 most critical KPIs (bold the numbers).
- End with one sentence on the dominant community narrative or sentiment trend.
- Keep it concise enough to paste into an email. No headers or bullets — just a paragraph.
- Only use Looker Impact Score data for sentiment. Do NOT reference Affogata or Inbox sentiment.
- Do NOT invent numbers."""

    return _gemini_call(
        prompt,
        "You are a concise executive communications writer for a game publisher. "
        "Write tight, data-grounded summaries suitable for senior leadership.",
        temperature=0.3,
        max_tokens=1500,
    )


def generate_performance_report(context):
    """AI-generated performance highlights narrative."""
    from utils.titles import get_title_config
    cfg = get_title_config()

    prompt = f"""Using the data context below, write a Performance Highlights report for {cfg['publisher']} {cfg['full_name']}.

DATA CONTEXT:
{context}

Write the report in markdown with these sections:

1. **Social / Owned Performance** — Start with a bold at-a-glance block listing headline KPIs as bullet points with numbers in bold, like:
   - **Total Impressions:** **X,XXX,XXX**
   - **Total Engagements:** **X,XXX**
   - etc.
   Then provide 1-2 paragraphs interpreting what these numbers mean.

2. **Platform Highlights** — For each platform, highlight key metrics and standout observations. Use bold for key numbers. Note which platform leads in which category.

3. **Top Content Moments** — Discuss the highest-performing posts, what made them resonate, and any patterns in content type or timing. Bold the engagement/impression numbers.

4. **Audience Growth** — Summarize audience trajectory and growth by platform. Bold the growth figures.

5. **Sentiment Snapshot** — ONLY use Looker Sentiment / Impact Score data for sentiment analysis. Do NOT reference Affogata or Inbox sentiment. If Looker data is available, summarize the average, high, and low impact scores.

Use a professional, analytical tone. Reference specific numbers from the data — always **bold** the key figures. Do not invent numbers. Keep each section concise (2-3 paragraphs max).

Start with:
# {cfg['publisher']} {cfg['full_name']} — Performance Highlights
"""

    return _gemini_call(
        prompt,
        "You are a social media analytics expert who writes clear, data-driven "
        "performance reports for game publishers. Be precise with numbers.",
        temperature=0.3,
        max_tokens=8000,
    )


def generate_pos_neg_themes(messages_df, n_sample=1800):
    """AI-generated positive and negative coverage themes with notable quotes."""
    from utils.titles import get_title_config
    cfg = get_title_config()

    texts = messages_df["Text"].dropna()
    texts = texts[texts.str.strip() != ""]
    texts = texts[texts.str.len() > 20]
    if len(texts) == 0:
        return None

    sample = texts.sample(min(n_sample, len(texts)), random_state=42)
    message_block = "\n---\n".join(t[:400] for t in sample.tolist())

    prompt = f"""Analyze these community messages about {cfg['ai_context']} and identify coverage themes.

Return a JSON object with two keys:

"positive_themes": An array of 5-7 objects, each with:
  - "theme": A concise theme name (e.g. "Skating Engine Improvements")
  - "summary": 2-3 sentences summarizing the positive reception — what specifically are people praising, why it matters, and how widespread the sentiment appears.
  - "quotes": Array of 5-7 verbatim quotes from the messages below that best represent this theme. Pick quotes that are specific, articulate, and varied (not all saying the same thing). Include the quote text only.
  - "estimated_pct": Estimated percentage of positive conversation this theme represents (should sum roughly to 100 across positive themes).

"negative_themes": Same structure, 5-7 objects for critical/negative themes. Summaries should explain what the core complaint is, how it impacts the player experience, and any nuance in the feedback.

Selection criteria:
- Quotes must be real, representative, and specific — not generic praise or complaints.
- Themes should be distinct with minimal overlap.
- Order themes from most prevalent to least prevalent.

COMMUNITY MESSAGES:
{message_block}"""

    result = _gemini_call(
        prompt,
        "You are an expert community analyst. Return valid JSON only. "
        "Pull quotes verbatim from the provided messages.",
        temperature=0.3,
        max_tokens=12000,
        json_mode=True,
    )
    if result is None:
        return None
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None


def generate_conversation_drivers(messages_df, n_sample=2000):
    """AI-generated Community Conversation Drivers report."""
    from utils.titles import get_title_config
    cfg = get_title_config()

    texts = messages_df["Text"].dropna()
    texts = texts[texts.str.strip() != ""]
    texts = texts[texts.str.len() > 20]
    total_messages = len(texts)
    if total_messages == 0:
        return None

    sample = texts.sample(min(n_sample, len(texts)), random_state=42)

    net_counts = ""
    if "Network" in messages_df.columns:
        vc = messages_df["Network"].value_counts()
        net_counts = "\n".join(f"  {k}: {v:,}" for k, v in vc.items())

    message_block = "\n---\n".join(t[:500] for t in sample.tolist())

    prompt = f"""You are a senior community intelligence analyst writing a formal Community Conversation Drivers report for {cfg['publisher']} {cfg['full_name']} ({cfg['ai_context']}).

TOTAL MESSAGES ANALYZED: {total_messages:,}

Platform breakdown:
{net_counts}

Below is a representative sample of {len(sample):,} community messages. Write a comprehensive Community Conversation Drivers report.

REQUIREMENTS:
1. Identify the top 8-12 conversation drivers, ranked by estimated share of total conversation volume. Be granular — split large topics into distinct sub-drivers rather than lumping them together (e.g. separate "Goalie AI Issues" from "CPU Teammate AI" rather than combining into one "AI Issues" driver).
2. For each driver, provide:
   - A clear, specific driver name as a heading
   - An estimated comment count and percentage of total conversation (should sum roughly to the total)
   - A "Key Takeaways" section with 5-8 bullet points — concise, insight-driven observations. Each bullet should surface a specific finding, not just restate the theme.
   - An "Expanded Summary" section with 3-5 paragraphs of analytical prose — go deep on what the data reveals, why it matters, and what patterns emerge. Reference specific examples from the messages. Discuss the nuance — where does the community agree vs. disagree? What is the intensity of sentiment? Are there sub-groups with different views? Professional, analytical tone. No marketing language. Be specific and grounded.
3. End with a "Closing Synthesis" section (3-4 paragraphs) that:
   - Identifies the 2-3 biggest risks / issues the team should prioritize
   - Highlights the 2-3 strongest positives to protect and amplify
   - Notes any emerging trends or under-the-radar topics that could grow
   - Provides a clear "bottom line" takeaway

FORMAT (use this exact markdown structure):

# {cfg['publisher']} {cfg['full_name']} — Community Conversation Drivers Report
**Beat Window:** [date range if inferrable, otherwise "Analysis Period"]
**Total Messages Analyzed:** {total_messages:,}

---

## [Driver Name]
**X,XXX comments (XX.X% of total conversation)**

### Key Takeaways
- Bullet 1
- Bullet 2
- ...

### Expanded Summary
Paragraph 1...

Paragraph 2...

---

(repeat for each driver)

---

## Closing Synthesis
[3-4 paragraphs tying everything together]

COMMUNITY MESSAGES:
{message_block}"""

    return _gemini_call(
        prompt,
        "You are a senior community intelligence analyst who writes detailed, "
        "data-grounded reports for game publishers. Your writing is precise, analytical, "
        "and avoids marketing fluff. Professional reports suitable for executive stakeholders. "
        "Be thorough — more detail and more drivers is always better than fewer.",
        temperature=0.4,
        max_tokens=24000,
    )


def discover_topic_buckets(messages_df, text_col="Text", n_sample=400):
    """Ask Gemini to discover topic buckets from community messages.

    Returns a dict[str, list[str]] mapping topic names to keyword lists,
    suitable for passing to get_top_conversation_topics(buckets=...).
    Returns None on failure.
    """
    from utils.titles import get_title_config

    cfg = get_title_config()
    ai_context = cfg["ai_context"]

    texts = messages_df[text_col].dropna()
    texts = texts[texts.str.strip() != ""]
    texts = texts[texts.str.len() > 15]
    if len(texts) == 0:
        return None

    sample = texts.sample(min(n_sample, len(texts)), random_state=42)
    message_block = "\n---\n".join(t[:200] for t in sample.tolist())

    prompt = f"""Analyze these community messages about {ai_context}.

Identify exactly 10 prominent conversation topics. You MUST return all 10.

Return a JSON object where each key is a short topic name (2-4 words) and each value is an array of 4-6 lowercase keywords that identify messages belonging to that topic.

Rules:
- Exactly 10 topics, no fewer.
- Topic names: 2-4 words max.
- Keywords: 4-6 per topic, all lowercase, single words or short phrases.
- No overlap between topic keywords.

Example format:
{{"Skating": ["skating", "skate", "speed", "momentum"], "Servers": ["server", "lag", "disconnect", "crash"]}}

MESSAGES:
{message_block}"""

    result = _gemini_call(
        prompt,
        "Return valid compact JSON only — a single object mapping topic names to keyword arrays. Exactly 10 topics. No extra text.",
        temperature=0.3,
        max_tokens=4000,
        json_mode=True,
    )
    if result is None:
        return None

    parsed = _parse_bucket_json(result)
    if parsed:
        _save_topic_buckets(parsed)
        return parsed

    st.warning("Gemini returned an incomplete response. Retrying with a smaller sample...")
    smaller_sample = sample.head(200)
    message_block_small = "\n---\n".join(t[:150] for t in smaller_sample.tolist())
    retry_prompt = f"""Identify exactly 10 conversation topics from these messages about {ai_context}.
Return compact JSON with exactly 10 keys: {{"Topic Name": ["keyword1", "keyword2", ...], ...}}

MESSAGES:
{message_block_small}"""

    result2 = _gemini_call(
        retry_prompt,
        "Return valid compact JSON only. Exactly 10 topics. No markdown, no extra text.",
        temperature=0.2,
        max_tokens=4000,
        json_mode=True,
    )
    if result2 is None:
        return None
    parsed2 = _parse_bucket_json(result2)
    if parsed2:
        _save_topic_buckets(parsed2)
        return parsed2

    st.warning("Could not get valid topic buckets from Gemini after retry.")
    return None


def _parse_bucket_json(text):
    """Try to parse bucket JSON, handling truncated responses."""
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and all(isinstance(v, list) for v in parsed.values()):
            if len(parsed) >= 5:
                return parsed
    except json.JSONDecodeError:
        pass

    # Truncated JSON recovery: find the last complete key-value pair
    last_good = cleaned.rfind("]")
    if last_good > 0:
        candidate = cleaned[:last_good + 1].rstrip().rstrip(",") + "}"
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                result = {k: v for k, v in parsed.items() if isinstance(v, list)}
                if len(result) >= 5:
                    return result
        except json.JSONDecodeError:
            pass

    return None


def _topic_buckets_path():
    """Path for persisting AI-discovered topic buckets per title."""
    from utils.titles import get_title_config
    from pathlib import Path
    cfg = get_title_config()
    data_dir = Path(__file__).resolve().parent.parent / "data" / "topic_buckets"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / f"{cfg['name'].lower()}.json"


def _save_topic_buckets(buckets):
    """Persist AI-discovered buckets to a JSON file."""
    try:
        path = _topic_buckets_path()
        with open(path, "w") as f:
            json.dump(buckets, f, indent=2)
    except Exception:
        pass


def load_saved_topic_buckets():
    """Load previously saved AI-discovered topic buckets, or return None."""
    try:
        path = _topic_buckets_path()
        if path.exists():
            with open(path) as f:
                buckets = json.load(f)
            if isinstance(buckets, dict) and buckets:
                return buckets
    except Exception:
        pass
    return None


def detect_campaign_phases(post_df, profile_df=None, title_config=None):
    """Use CSV spike analysis + AI to detect campaign phases.

    When Gemini is the active provider, also uses Google Search grounding.
    Returns a list of dicts: [{"name": str, "start": str, "end": str, "confidence": str, "evidence": str}, ...]
    or None on failure.
    """
    import numpy as np
    from utils.titles import get_title_config

    cfg = title_config or get_title_config()
    provider = get_ai_provider()

    if provider == "gemini":
        client = get_gemini_client()
        if client is None:
            st.error("No Google API key found. Set GOOGLE_API_KEY in your .env file.")
            return None

    date_min = post_df["Date"].min().strftime("%Y-%m-%d")
    date_max = post_df["Date"].max().strftime("%Y-%m-%d")

    # --- Phase 1: CSV spike analysis ---
    daily = post_df.groupby(post_df["Date"].dt.normalize()).agg(
        Posts=("Impressions", "size"),
        Impressions=("Impressions", "sum"),
        Engagements=("Engagements", "sum"),
        VideoViews=("Video Views", "sum"),
    ).reset_index()
    daily.columns = ["Date", "Posts", "Impressions", "Engagements", "VideoViews"]

    median_imp = daily["Impressions"].median()
    daily["Spike"] = daily["Impressions"] / median_imp if median_imp > 0 else 1.0
    spike_days = daily[daily["Spike"] >= 2.5].sort_values("Spike", ascending=False)

    spike_summary = []
    for _, row in spike_days.head(15).iterrows():
        d = row["Date"].strftime("%Y-%m-%d")
        day_posts = post_df[post_df["Date"].dt.normalize() == row["Date"]]
        post_texts = day_posts["Post"].dropna().str[:100].tolist()[:5]
        texts_str = " | ".join(post_texts) if post_texts else "(no post text)"
        spike_summary.append(
            f"  {d}: {row['Spike']:.1f}x normal impressions, "
            f"{int(row['Posts'])} posts, {int(row['Engagements']):,} eng. "
            f"Post excerpts: {texts_str}"
        )

    spike_block = "\n".join(spike_summary) if spike_summary else "  No significant spikes detected."

    campaign_keywords = [
        "reveal", "announce", "launch", "trailer", "gameplay",
        "available now", "out now", "first look", "deep dive",
        "cover athlete", "pre-order", "beta", "early access",
        "official", "introducing", "unveiled",
    ]
    keyword_days = []
    for kw in campaign_keywords:
        matches = post_df[post_df["Post"].fillna("").str.lower().str.contains(kw, na=False)]
        if len(matches) > 0:
            dates = matches["Date"].dt.normalize().unique()
            for d in dates:
                keyword_days.append({"date": d, "keyword": kw})

    kw_summary = []
    if keyword_days:
        kw_df = pd.DataFrame(keyword_days)
        kw_by_date = kw_df.groupby("date")["keyword"].apply(list).reset_index()
        kw_by_date = kw_by_date.sort_values("date")
        for _, row in kw_by_date.iterrows():
            kw_summary.append(f"  {row['date'].strftime('%Y-%m-%d')}: keywords found: {', '.join(row['keyword'])}")
    kw_block = "\n".join(kw_summary[:20]) if kw_summary else "  No campaign keywords found in post text."

    # --- Phase 2: Google Search grounding (Gemini only) ---
    game_name = cfg["full_name"]
    publisher = cfg["publisher"]

    web_results = None
    if provider == "gemini":
        from google.genai import types

        search_prompt = (
            f"Search the web for key marketing campaign dates for the video game "
            f"{game_name} by {publisher}. I need the specific dates (month and day) for events like: "
            f"cover reveal, gameplay trailer, announcement/reveal, beta or early access, "
            f"launch/release date, and any other major marketing beats. "
            f"The data I have spans {date_min} to {date_max}. "
            f"Return the dates you find with sources."
        )
        try:
            search_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=search_prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.1,
                ),
            )
            web_results = search_response.text
        except Exception as e:
            web_results = f"(Web search unavailable: {e})"
    else:
        web_results = "(Web search not available with EA EADP provider — using CSV signals only)"

    # --- Phase 3: Gemini combines all signals to propose phases ---
    combined_prompt = f"""You are analyzing social media data for {game_name} by {publisher}.
Data spans {date_min} to {date_max}.

SIGNAL 1 — IMPRESSIONS SPIKES (days with 2.5x+ normal volume):
{spike_block}

SIGNAL 2 — CAMPAIGN KEYWORDS IN POST TEXT:
{kw_block}

SIGNAL 3 — WEB SEARCH RESULTS FOR KNOWN CAMPAIGN DATES:
{web_results or "(no web results)"}

Using all three signals, identify the major marketing campaign phases within this data period.
For each phase, provide:
- "name": Short descriptive name (e.g. "Cover Reveal", "Gameplay Trailer", "Launch Week")
- "start": Start date (YYYY-MM-DD) — the first day of this campaign beat
- "end": End date (YYYY-MM-DD) — the last high-activity day of this beat (usually 1-5 days)
- "confidence": "high" if web + CSV both confirm, "medium" if only one signal, "low" if uncertain
- "evidence": One sentence explaining what signals support this detection

Return a JSON object with a single key "phases" containing an array of phase objects.
Order by date. Only include phases that fall within the data period {date_min} to {date_max}.
If you cannot confidently identify any phases, return {{"phases": []}}.
"""

    result = _gemini_call(
        combined_prompt,
        "You are an expert at identifying marketing campaign timelines from social data. "
        "Return valid JSON only. Be conservative — only flag phases you have evidence for.",
        temperature=0.2,
        max_tokens=3000,
        json_mode=True,
    )
    if result is None:
        return None

    try:
        parsed = json.loads(result)
        phases = parsed.get("phases", [])
        if isinstance(phases, list) and all(
            isinstance(p, dict) and "name" in p and "start" in p
            for p in phases
        ):
            for p in phases:
                if "end" not in p:
                    p["end"] = p["start"]
            return phases
    except (json.JSONDecodeError, TypeError):
        pass

    return None


def generate_comparison_narrative(label_a, label_b, kpis_a, kpis_b, looker_a=None, looker_b=None):
    """AI-generated narrative explaining what changed between two periods and why it matters."""
    from utils.titles import get_title_config
    from utils.processors import format_number

    cfg = get_title_config()

    def _fmt(v):
        if isinstance(v, float) and v < 100:
            return f"{v:.2f}%"
        return format_number(int(v))

    comparison_lines = []
    for key in kpis_a:
        va, vb = kpis_a.get(key, 0), kpis_b.get(key, 0)
        if va == 0 and vb == 0:
            continue
        delta = ((va - vb) / vb * 100) if vb != 0 else 0
        comparison_lines.append(f"  {key}: Period A = {_fmt(va)}, Period B = {_fmt(vb)}, change = {delta:+.1f}%")

    comparison_block = "\n".join(comparison_lines)

    sentiment_block = ""
    if looker_a is not None and len(looker_a) > 0:
        sentiment_block += f"\n  Period A sentiment: avg {looker_a['Impact Score'].mean():.1f}, high {looker_a['Impact Score'].max():.1f}, low {looker_a['Impact Score'].min():.1f}"
    if looker_b is not None and len(looker_b) > 0:
        sentiment_block += f"\n  Period B sentiment: avg {looker_b['Impact Score'].mean():.1f}, high {looker_b['Impact Score'].max():.1f}, low {looker_b['Impact Score'].min():.1f}"

    prompt = f"""You are analyzing two reporting periods for {cfg['publisher']} {cfg['full_name']} ({cfg['ai_context']}).

Period A: "{label_a}"
Period B: "{label_b}"

METRICS COMPARISON:
{comparison_block}
{sentiment_block}

Write a 3-5 paragraph analysis that:
1. Opens with the single most important change between the two periods
2. Highlights which metrics improved and which declined, using bold for key numbers
3. Identifies likely causes or patterns (e.g. if engagement dropped but posts increased, that suggests lower-quality content or audience fatigue)
4. Notes any sentiment shifts if Looker data is available
5. Ends with a one-sentence takeaway for the team

Professional, analytical tone. Reference specific numbers. Do NOT invent data."""

    return _gemini_call(
        prompt,
        "You are a social media analytics expert who writes clear, data-driven "
        "period-over-period analyses for game publishers.",
        temperature=0.3,
        max_tokens=3000,
    )


def parse_comparison_request(user_query: str, saved_datasets: list, current_label: str | None = None):
    """Parse a natural-language campaign comparison request using Gemini.

    *saved_datasets* is the list of manifest dicts from ``list_saved_datasets``.
    Returns a dict with keys: dataset_a, dataset_b, phase_a, phase_b,
    day_range_a, day_range_b, explanation  — or None on failure.
    """
    from utils.titles import get_title_config

    cfg = get_title_config()

    catalog_lines = []
    for ds in saved_datasets:
        dr = ds.get("date_range") or ["?", "?"]
        cs = ds.get("campaign_start", "")
        phases = ds.get("campaign_phases", [])
        phase_strs = []
        for p in phases:
            phase_strs.append(f'{p["name"]} ({p["start"]} to {p.get("end", p["start"])})')
        phase_block = "; ".join(phase_strs) if phase_strs else "none detected"
        catalog_lines.append(
            f'- "{ds["label"]}"  date range: {dr[0]} to {dr[1]}  '
            f'campaign_start: {cs or "not set"}  phases: {phase_block}'
        )

    if current_label:
        catalog_lines.insert(0, f'- "__current__" (currently loaded data, label: "{current_label}")')

    catalog_block = "\n".join(catalog_lines) if catalog_lines else "(no saved datasets)"

    prompt = f"""You are resolving a campaign comparison request for {cfg['full_name']} by {cfg['publisher']}.

AVAILABLE DATASETS:
{catalog_block}

USER REQUEST: "{user_query}"

Your job: figure out which two datasets and which date slices the user wants to compare.

Rules:
- If the user says "current" or "this campaign" or references the loaded data, use "__current__" as the dataset identifier.
- Match fuzzy references ("NHL 26", "last year", "the reveal") to the best dataset label.
- If the user references a phase name (e.g. "cover reveal", "launch"), match it to a detected phase.
- day_range is [start_day, end_day] relative to the phase start date (or campaign_start, or dataset start if neither exists). Day 0 = the anchor date, Day 2 = two days later, etc.
- "First 3 days" = [0, 2]. "Week 1" = [0, 6]. "Day 1" = [0, 0]. "First 5 days" = [0, 4].
- If no specific day range is mentioned, use the full dataset range: [0, 9999] (sentinel for "all data").
- dataset_a is always the "newer" or "current" period, dataset_b is the older/comparison period.

Return a JSON object with these keys:
{{
  "dataset_a": "<label or __current__>",
  "dataset_b": "<label>",
  "phase_a": "<phase name or null>",
  "phase_b": "<phase name or null>",
  "day_range_a": [start, end],
  "day_range_b": [start, end],
  "explanation": "One sentence describing what is being compared and the actual dates"
}}

If you cannot resolve the request, return:
{{"error": "reason the request could not be resolved"}}
"""

    result = _gemini_call(
        prompt,
        "You are a precise data operations assistant. Return valid JSON only. "
        "Match user intent to datasets as accurately as possible.",
        temperature=0.1,
        max_tokens=1000,
        json_mode=True,
    )
    if result is None:
        return {"error": "Gemini API returned no response. Check your API key and quota."}

    def _try_parse(text):
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None

    parsed = _try_parse(result)

    if parsed is None:
        trimmed = result.rstrip()
        for closer in ('"', "]", "}", '"}', '"]}', '"]}'):
            attempt = _try_parse(trimmed + closer)
            if attempt is not None:
                parsed = attempt
                break
            trimmed += closer

    if parsed is None:
        return {"error": "Could not parse AI response. Try rephrasing your request."}

    if "error" in parsed:
        return parsed
    required = ("dataset_a", "dataset_b", "day_range_a", "day_range_b")
    if all(k in parsed for k in required):
        return parsed
    missing = [k for k in required if k not in parsed]
    return {"error": f"AI response missing required fields: {', '.join(missing)}. Try rephrasing."}


def generate_yoy_narrative(explanation: str, kpis_a: dict, kpis_b: dict):
    """Short AI narrative summarising a YoY comparison for the dashboard."""
    from utils.titles import get_title_config
    from utils.processors import format_number

    cfg = get_title_config()

    def _fmt(v):
        if isinstance(v, float) and v < 100:
            return f"{v:.2f}%"
        return format_number(int(v))

    lines = []
    for key in kpis_a:
        va, vb = kpis_a.get(key, 0), kpis_b.get(key, 0)
        if va == 0 and vb == 0:
            continue
        delta = ((va - vb) / vb * 100) if vb != 0 else 0
        lines.append(f"  {key}: Current = {_fmt(va)}, Comparison = {_fmt(vb)}, change = {delta:+.1f}%")

    metrics_block = "\n".join(lines)

    prompt = f"""You are writing a 2-3 sentence dashboard summary for {cfg['publisher']} {cfg['full_name']}.

Context: {explanation}

METRICS:
{metrics_block}

Write a concise, insight-driven summary. Bold the most important numbers. Professional tone.
Open with the single biggest change, then note 1-2 other key shifts. Do NOT invent data."""

    return _gemini_call(
        prompt,
        "You are a social media analytics expert writing a concise dashboard annotation.",
        temperature=0.3,
        max_tokens=800,
    )
