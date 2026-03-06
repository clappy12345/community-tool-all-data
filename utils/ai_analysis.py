import json
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            pass
    if not api_key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def discover_themes(messages_df, text_col="Text", n_sample=500):
    client = get_openai_client()
    if client is None:
        st.error("No OpenAI API key found. Set OPENAI_API_KEY in your .env file.")
        return None

    texts = messages_df[text_col].dropna()
    texts = texts[texts.str.strip() != ""]
    texts = texts[texts.str.len() > 20]

    if len(texts) > n_sample:
        sample = texts.sample(n_sample, random_state=42)
    else:
        sample = texts

    message_block = "\n---\n".join(t[:300] for t in sample.tolist())

    from openai import APIError, RateLimitError, AuthenticationError

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at analyzing gaming community conversations. "
                        "Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""Analyze these community messages about the video game NHL 26 by EA Sports.
Identify the top 12-15 distinct themes or topics people are discussing.

For each theme, return a JSON object with:
- "name": Short theme name (2-4 words, e.g. "Gameplay Physics", "Be A Pro Mode")
- "description": One sentence summarizing what people are saying
- "sentiment_lean": "positive", "mixed", or "negative"
- "keywords": Array of 10-15 lowercase keywords/phrases that identify this theme

Return a JSON object with a single key "themes" containing an array of theme objects.

Community Messages:
{message_block}""",
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
    except RateLimitError:
        st.error(
            "OpenAI quota exceeded — your API key has run out of credits. "
            "Add billing at https://platform.openai.com/account/billing and try again."
        )
        return None
    except AuthenticationError:
        st.error("Invalid OpenAI API key. Check the key in your .env file.")
        return None
    except APIError as e:
        st.error(f"OpenAI API error: {e}")
        return None

    result = json.loads(response.choices[0].message.content)
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
