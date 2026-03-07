import pandas as pd
import zipfile
import io
import os
import streamlit as st


def clean_numeric(val):
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace("%", "")
    if s == "" or s == "-":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


@st.cache_data(show_spinner=False)
def load_post_performance(file_bytes, filename=""):
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        df["Date"] = pd.to_datetime(df["Date"], format="mixed")

        numeric_cols = [
            "Impressions",
            "Reach",
            "Potential Reach",
            "Engagements",
            "Reactions",
            "Comments",
            "Shares",
            "Saves",
            "Post Link Clicks",
            "Video Views",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        if "Engagement Rate (per Impression)" in df.columns:
            df["Engagement Rate (per Impression)"] = df[
                "Engagement Rate (per Impression)"
            ].apply(clean_numeric)

        return df
    except Exception as e:
        st.error(f"Failed to load Post Performance: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_profile_performance(file_bytes, filename=""):
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        df["Date"] = pd.to_datetime(df["Date"], format="%m-%d-%Y")

        numeric_cols = [
            "Audience",
            "Net Audience Growth",
            "Audience Gained",
            "Impressions",
            "Video Views",
            "Engagements",
            "Reactions",
            "Comments",
            "Shares",
            "Post Link Clicks",
            "Saves",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        if "Engagement Rate (per Impression)" in df.columns:
            df["Engagement Rate (per Impression)"] = df[
                "Engagement Rate (per Impression)"
            ].apply(clean_numeric)

        return df
    except Exception as e:
        st.error(f"Failed to load Profile Performance: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_affogata(file_bytes, filename=""):
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, low_memory=False)
        df["Created At"] = pd.to_datetime(df["Created At"], format="mixed", utc=True)
        df["Created At"] = df["Created At"].dt.tz_localize(None)

        numeric_cols = ["Likes", "Shares", "Comments", "Views", "Total Engagements", "Reach"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        if "Sentiment" in df.columns:
            df["Sentiment"] = df["Sentiment"].fillna("neutral").str.strip().str.lower()

        return df
    except Exception as e:
        st.error(f"Failed to load Affogata: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_inbox_export(file_bytes, filename=""):
    try:
        keep_cols = [
            "Timestamp (PT)",
            "Type",
            "Network",
            "Message Type",
            "Received From (Network Name)",
            "Message",
            "Sentiment",
            "Language",
            "In Response To: Message",
            "Parent Post ID",
            "Permalink",
            "Message Intent",
        ]

        if filename.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                csv_names = [n for n in z.namelist() if n.endswith(".csv")]
                if not csv_names:
                    raise ValueError("No CSV file found inside ZIP")
                with z.open(csv_names[0]) as f:
                    all_cols = pd.read_csv(f, nrows=0).columns.tolist()
                    usecols = [c for c in keep_cols if c in all_cols]
                with z.open(csv_names[0]) as f:
                    df = pd.read_csv(f, dtype=str, usecols=usecols, low_memory=False)
        else:
            buf = io.BytesIO(file_bytes)
            all_cols = pd.read_csv(buf, nrows=0).columns.tolist()
            usecols = [c for c in keep_cols if c in all_cols]
            buf.seek(0)
            df = pd.read_csv(buf, dtype=str, usecols=usecols, low_memory=False)

        if "Type" in df.columns:
            df = df[df["Type"] == "Incoming"].copy()

        if "Timestamp (PT)" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp (PT)"], format="mixed")
            df.drop(columns=["Timestamp (PT)"], inplace=True)

        if "Sentiment" in df.columns:
            df["Sentiment"] = df["Sentiment"].fillna("neutral").str.strip().str.lower()

        if "Message" in df.columns:
            df = df[df["Message"].notna() & (df["Message"].str.strip() != "")]

        return df
    except Exception as e:
        st.error(f"Failed to load Inbox Export: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_looker_sentiment(file_bytes, filename=""):
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), skiprows=1, dtype=str)
        df["Date"] = pd.to_datetime(df["Date"], format="mixed")
        df["Impact Score"] = df["Impact Score"].apply(clean_numeric)
        return df.sort_values("Date").reset_index(drop=True)
    except Exception as e:
        st.error(f"Failed to load Looker Sentiment: {e}")
        return None


def read_file_bytes(path):
    with open(path, "rb") as f:
        return f.read()


# Keyword patterns used to auto-detect CSV types inside a data directory
_FILE_PATTERNS = {
    "post_performance": ["post performance", "post_performance"],
    "profile_performance": ["profile performance", "profile_performance"],
    "affogata": ["affogata"],
    "inbox": ["inbox export", "inbox_export"],
    "looker_sentiment": ["looker", "sentiment score"],
}


def _get_data_dir():
    """Return the data directory from env, or fall back to well-known locations."""
    from dotenv import load_dotenv
    load_dotenv()

    explicit = os.getenv("DATA_DIR", "").strip()
    if explicit and os.path.isdir(explicit):
        return explicit

    candidates = [
        os.path.expanduser("~/Desktop/Template Data Set"),
        os.path.expanduser("~/Desktop"),
    ]
    for d in candidates:
        if os.path.isdir(d):
            return d
    return None


def _detect_files_in_dir(directory):
    """Scan a directory and match files to dataset types by filename keywords."""
    if not directory or not os.path.isdir(directory):
        return {}

    found = {}
    for fname in os.listdir(directory):
        lower = fname.lower()
        if not (lower.endswith(".csv") or lower.endswith(".zip")):
            continue
        for key, patterns in _FILE_PATTERNS.items():
            if key in found:
                continue
            if any(p in lower for p in patterns):
                found[key] = os.path.join(directory, fname)
                break
    return found


def check_default_data():
    data_dir = _get_data_dir()
    return _detect_files_in_dir(data_dir)


def load_all_defaults():
    available = check_default_data()
    results = {}

    loaders = {
        "post_performance": lambda p: load_post_performance(read_file_bytes(p), os.path.basename(p)),
        "profile_performance": lambda p: load_profile_performance(read_file_bytes(p), os.path.basename(p)),
        "affogata": lambda p: load_affogata(read_file_bytes(p), os.path.basename(p)),
        "inbox": lambda p: load_inbox_export(read_file_bytes(p), os.path.basename(p)),
        "looker_sentiment": lambda p: load_looker_sentiment(read_file_bytes(p), os.path.basename(p)),
    }

    for key, path in available.items():
        if key in loaders:
            results[key] = loaders[key](path)

    return results
