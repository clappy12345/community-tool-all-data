from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "saved"

DATASET_KEYS = ["post_performance", "profile_performance", "affogata", "inbox", "looker_sentiment"]


def _dataset_dir(title_key: str, label: str) -> Path:
    safe_label = label.replace("/", "-").replace("\\", "-").strip()
    return DATA_DIR / title_key / safe_label


def save_dataset(
    label: str,
    title_key: str,
    campaign_start: str | None = None,
    campaign_phases: list | None = None,
    campaign_events: list | None = None,
    game_version: str | None = None,
    campaign_type: str | None = None,
) -> str:
    dest = _dataset_dir(title_key, label)
    dest.mkdir(parents=True, exist_ok=True)

    row_counts = {}
    for key in DATASET_KEYS:
        df = st.session_state.get(key)
        if df is not None and len(df) > 0:
            df.to_parquet(dest / f"{key}.parquet", index=False)
            row_counts[key] = len(df)

    pp = st.session_state.get("post_performance")
    date_range = None
    if pp is not None and len(pp) > 0:
        date_range = [
            pp["Date"].min().strftime("%Y-%m-%d"),
            pp["Date"].max().strftime("%Y-%m-%d"),
        ]

    manifest = {
        "title": title_key,
        "label": label,
        "date_range": date_range,
        "campaign_start": campaign_start,
        "campaign_phases": campaign_phases or [],
        "campaign_events": campaign_events or [],
        "game_version": game_version,
        "campaign_type": campaign_type,
        "saved_at": datetime.now().isoformat(),
        "row_counts": row_counts,
    }
    with open(dest / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return label


def update_dataset_phases(title_key: str, label: str, phases: list) -> None:
    """Update campaign_phases on an existing saved dataset manifest."""
    manifest_path = _dataset_dir(title_key, label) / "manifest.json"
    if not manifest_path.exists():
        return
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest["campaign_phases"] = phases
    if phases and not manifest.get("campaign_start"):
        manifest["campaign_start"] = phases[0]["start"]
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def update_dataset_events(title_key: str, label: str, events: list) -> None:
    """Update campaign_events on an existing saved dataset manifest."""
    manifest_path = _dataset_dir(title_key, label) / "manifest.json"
    if not manifest_path.exists():
        return
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest["campaign_events"] = events
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def update_dataset_metadata(title_key: str, label: str, **fields) -> None:
    """Update arbitrary manifest fields on an existing saved dataset."""
    manifest_path = _dataset_dir(title_key, label) / "manifest.json"
    if not manifest_path.exists():
        return
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest.update(fields)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def get_dataset_manifest(title_key: str, label: str) -> dict | None:
    manifest_path = _dataset_dir(title_key, label) / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def list_saved_datasets(title_key: str) -> list[dict]:
    title_dir = DATA_DIR / title_key
    if not title_dir.exists():
        return []

    datasets = []
    for entry in sorted(title_dir.iterdir()):
        manifest_path = entry / "manifest.json"
        if entry.is_dir() and manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            datasets.append(manifest)

    datasets.sort(key=lambda d: d.get("saved_at", ""), reverse=True)
    return datasets


def load_saved_dataset(title_key: str, label: str) -> dict:
    src = _dataset_dir(title_key, label)
    results = {}
    for key in DATASET_KEYS:
        parquet_path = src / f"{key}.parquet"
        if parquet_path.exists():
            results[key] = pd.read_parquet(parquet_path)
    return results


def delete_saved_dataset(title_key: str, label: str) -> None:
    target = _dataset_dir(title_key, label)
    if target.exists():
        shutil.rmtree(target)


def get_default_label() -> str:
    pp = st.session_state.get("post_performance")
    if pp is not None and len(pp) > 0:
        d_min = pp["Date"].min().strftime("%b %d, %Y")
        d_max = pp["Date"].max().strftime("%b %d, %Y")
        return f"{d_min} — {d_max}"
    return datetime.now().strftime("%b %d, %Y")
