import json
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


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


def discover_themes(messages_df, text_col="Text", n_sample=500):
    client = get_gemini_client()
    if client is None:
        st.error("No Google API key found. Set GOOGLE_API_KEY in your .env file.")
        return None

    from utils.titles import get_title_config
    from google.genai import types

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

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are an expert at analyzing gaming community conversations. "
                    "Return valid JSON only."
                ),
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None

    result = json.loads(response.text)
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


def _gemini_call(prompt, system_instruction, temperature=0.3, max_tokens=8000, json_mode=False):
    """Shared helper for Gemini API calls."""
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

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None
    return response.text


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


def generate_pos_neg_themes(messages_df, n_sample=1200):
    """AI-generated positive and negative coverage themes with notable quotes."""
    from utils.titles import get_title_config
    cfg = get_title_config()

    texts = messages_df["Text"].dropna()
    texts = texts[texts.str.strip() != ""]
    texts = texts[texts.str.len() > 20]
    if len(texts) == 0:
        return None

    sample = texts.sample(min(n_sample, len(texts)), random_state=42)
    message_block = "\n---\n".join(t[:350] for t in sample.tolist())

    prompt = f"""Analyze these community messages about {cfg['ai_context']} and identify coverage themes.

Return a JSON object with two keys:

"positive_themes": An array of 3-5 objects, each with:
  - "theme": A concise theme name (e.g. "Skating Engine Improvements")
  - "summary": One sentence summarizing the positive reception
  - "quotes": Array of 3-5 verbatim quotes from the messages below that best represent this theme. Pick quotes that are specific and articulate. Include the quote text only.

"negative_themes": Same structure, 3-5 objects for critical/negative themes.

Select quotes that are real, representative, and specific — not generic praise or complaints.

COMMUNITY MESSAGES:
{message_block}"""

    result = _gemini_call(
        prompt,
        "You are an expert community analyst. Return valid JSON only. "
        "Pull quotes verbatim from the provided messages.",
        temperature=0.3,
        max_tokens=6000,
        json_mode=True,
    )
    if result is None:
        return None
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None


def generate_conversation_drivers(messages_df, n_sample=1500):
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

    message_block = "\n---\n".join(t[:400] for t in sample.tolist())

    prompt = f"""You are a senior community intelligence analyst writing a formal Community Conversation Drivers report for {cfg['publisher']} {cfg['full_name']} ({cfg['ai_context']}).

TOTAL MESSAGES ANALYZED: {total_messages:,}

Platform breakdown:
{net_counts}

Below is a representative sample of {len(sample):,} community messages. Write a Community Conversation Drivers report.

REQUIREMENTS:
1. Identify the top 5-8 conversation drivers, ranked by estimated share of total conversation volume.
2. For each driver, provide:
   - A clear driver name as a heading
   - An estimated comment count and percentage of total conversation (should sum roughly to the total)
   - A "Key Takeaways" section with 4-6 bullet points — concise, insight-driven observations
   - An "Expanded Summary" section with 2-4 paragraphs of analytical prose — go deep on what the data reveals, why it matters, and what patterns emerge. Professional, analytical tone. No marketing language. Be specific and grounded.
3. End with a "Closing Synthesis" section that ties all drivers together.

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
[2-3 paragraphs tying everything together]

COMMUNITY MESSAGES:
{message_block}"""

    return _gemini_call(
        prompt,
        "You are a senior community intelligence analyst who writes detailed, "
        "data-grounded reports for game publishers. Your writing is precise, analytical, "
        "and avoids marketing fluff. Professional reports suitable for executive stakeholders.",
        temperature=0.4,
        max_tokens=16000,
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

Identify the 8-10 most prominent conversation topics.

Return a JSON object where each key is a short topic name (2-4 words) and each value is an array of 5-8 lowercase keywords that identify messages belonging to that topic.

Keep it concise — short topic names, short keyword lists.

Example:
{{"Skating": ["skating", "skate", "speed", "momentum", "agility"], "Servers": ["server", "lag", "disconnect", "crash"]}}

MESSAGES:
{message_block}"""

    result = _gemini_call(
        prompt,
        "Return valid compact JSON only — a single object mapping topic names to keyword arrays. No extra text.",
        temperature=0.3,
        max_tokens=2000,
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
    retry_prompt = f"""Identify 8 conversation topics from these messages about {ai_context}.
Return compact JSON: {{"Topic Name": ["keyword1", "keyword2", ...], ...}}

MESSAGES:
{message_block_small}"""

    result2 = _gemini_call(
        retry_prompt,
        "Return valid compact JSON only. No markdown, no extra text.",
        temperature=0.2,
        max_tokens=1500,
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
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and all(isinstance(v, list) for v in parsed.values()):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try to salvage truncated JSON by closing open brackets
    patched = text.rstrip()
    for closer in ('"', "]", "}"):
        try:
            parsed = json.loads(patched + closer)
            if isinstance(parsed, dict):
                return {k: v for k, v in parsed.items() if isinstance(v, list)}
        except json.JSONDecodeError:
            patched += closer

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
