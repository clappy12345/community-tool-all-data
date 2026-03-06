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


@st.cache_data(show_spinner=False)
def load_profile_performance(file_bytes, filename=""):
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


@st.cache_data(show_spinner=False)
def load_affogata(file_bytes, filename=""):
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


@st.cache_data(show_spinner=False)
def load_inbox_export(file_bytes, filename=""):
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


def read_file_bytes(path):
    with open(path, "rb") as f:
        return f.read()


DEFAULT_PATHS = {
    "post_performance": os.path.expanduser(
        "~/Desktop/Post Performance Sprout August 21, 2025 - September 17, 2025.csv"
    ),
    "profile_performance": os.path.expanduser(
        "~/Desktop/Profile Performance Sprout August 21, 2025 - September 17, 2025.csv"
    ),
    "affogata": os.path.expanduser(
        "~/Desktop/ AFFOGATA Aug 21st - Sept 17th NHL 26.csv"
    ),
    "inbox": os.path.expanduser(
        "~/Desktop/Inbox Export Sprout Aug 21, 2025 - Sep 17, 2025_46268d38-65ae-4911-bec8-eca54ad6ecf3.zip"
    ),
}


def check_default_data():
    return {k: v for k, v in DEFAULT_PATHS.items() if os.path.exists(v)}


def load_all_defaults():
    available = check_default_data()
    results = {}

    if "post_performance" in available:
        b = read_file_bytes(available["post_performance"])
        results["post_performance"] = load_post_performance(b, "data.csv")

    if "profile_performance" in available:
        b = read_file_bytes(available["profile_performance"])
        results["profile_performance"] = load_profile_performance(b, "data.csv")

    if "affogata" in available:
        b = read_file_bytes(available["affogata"])
        results["affogata"] = load_affogata(b, "data.csv")

    if "inbox" in available:
        path = available["inbox"]
        b = read_file_bytes(path)
        fname = os.path.basename(path)
        results["inbox"] = load_inbox_export(b, fname)

    return results
