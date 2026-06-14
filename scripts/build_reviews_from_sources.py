"""Build BiteRadar review/media snippets from real-data sources.

Inputs, when present:
- data/manual_reviews_raw.csv: user survey, restaurant-submitted notes, or manually licensed excerpts
- data/google_reviews_raw.csv: optional Google Places reviews, if collected and allowed
- data/articles_raw.csv: user-provided web article excerpts
- data/youtube_videos_raw.csv: YouTube Data API metadata
- data/restaurants_raw.csv: restaurant names for entity matching

Output:
- data/reviews_raw.csv, the format used by scripts/process_data.py

This script does simple restaurant name matching. It is transparent and easy to
explain in the report, but you can replace it with embeddings later.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def norm(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def short_name_candidates(name: str) -> list[str]:
    base = norm(name)
    parts = re.split(r"[\s\-–—_｜|()（）]+", base)
    candidates = {base}
    for p in parts:
        if len(p) >= 3:
            candidates.add(p)
    return sorted(candidates, key=len, reverse=True)


def load_optional(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def match_restaurant(text: str, restaurants: pd.DataFrame, hint: str = "") -> str | None:
    text_n = norm(" ".join([text, hint]))
    for _, r in restaurants.iterrows():
        for cand in short_name_candidates(r["name"]):
            if cand and cand in text_n:
                return r["restaurant_id"]
    # If hint exactly matches name fragment.
    hint_n = norm(hint)
    if hint_n:
        for _, r in restaurants.iterrows():
            if hint_n in norm(r["name"]) or norm(r["name"]) in hint_n:
                return r["restaurant_id"]
    return None


def main() -> None:
    restaurants = pd.read_csv(DATA_DIR / "restaurants_raw.csv")
    rows: list[dict] = []

    # 1) Manual/source-owned reviews are safest and should be preferred.
    manual = load_optional(DATA_DIR / "manual_reviews_raw.csv")
    if not manual.empty:
        for _, x in manual.iterrows():
            rid = x.get("restaurant_id") or match_restaurant(str(x.get("review_text", "")), restaurants, str(x.get("restaurant_hint", "")))
            if rid:
                rows.append({
                    "review_id": x.get("review_id", f"M{len(rows)+1:05d}"),
                    "restaurant_id": rid,
                    "source": x.get("source", "manual_or_survey"),
                    "rating": x.get("rating", ""),
                    "review_text": str(x.get("review_text", ""))[:1200],
                    "created_at": x.get("created_at", ""),
                })

    # 2) Optional Google review rows, only if user collected them intentionally.
    google_reviews = load_optional(DATA_DIR / "google_reviews_raw.csv")
    if not google_reviews.empty:
        for _, x in google_reviews.iterrows():
            if str(x.get("review_text", "")).strip():
                rows.append({
                    "review_id": x.get("review_id", f"GREV{len(rows)+1:05d}"),
                    "restaurant_id": x.get("restaurant_id"),
                    "source": x.get("source", "google_places_api_optional_review"),
                    "rating": x.get("rating", ""),
                    "review_text": str(x.get("review_text", ""))[:1200],
                    "created_at": x.get("created_at", ""),
                })

    # 3) Articles: convert article text into media snippets associated with restaurants.
    articles = load_optional(DATA_DIR / "articles_raw.csv")
    if not articles.empty:
        for _, a in articles.iterrows():
            full = f"{a.get('title', '')}. {a.get('text', '')}"
            rid = match_restaurant(full, restaurants, str(a.get("restaurant_hint", "")))
            if rid:
                rows.append({
                    "review_id": f"ART{len(rows)+1:05d}",
                    "restaurant_id": rid,
                    "source": "food_article_excerpt",
                    "rating": "",
                    "review_text": full[:1200],
                    "created_at": a.get("fetched_at", ""),
                })

    # 4) YouTube metadata: weak media signal, not a full review transcript.
    videos = load_optional(DATA_DIR / "youtube_videos_raw.csv")
    if not videos.empty:
        for _, v in videos.iterrows():
            full = f"{v.get('title', '')}. {v.get('description', '')}"
            rid = match_restaurant(full, restaurants, "")
            if rid:
                rows.append({
                    "review_id": f"YT{len(rows)+1:05d}",
                    "restaurant_id": rid,
                    "source": "youtube_metadata",
                    "rating": "",
                    "review_text": full[:1000],
                    "created_at": v.get("published_at", ""),
                })

    # Fallback: create one neutral snippet per restaurant so the pipeline never breaks.
    existing = {r["restaurant_id"] for r in rows if r.get("restaurant_id")}
    stamp = datetime.now(timezone.utc).date().isoformat()
    for _, r in restaurants.iterrows():
        if r["restaurant_id"] not in existing:
            rows.append({
                "review_id": f"AUTO{len(rows)+1:05d}",
                "restaurant_id": r["restaurant_id"],
                "source": "auto_metadata_summary",
                "rating": r.get("rating", ""),
                "review_text": (
                    f"{r['name']} is a {r.get('primary_cuisine', 'restaurant')} near {r.get('area', '')}. "
                    f"It has a public rating around {r.get('rating', '')} and estimated price range "
                    f"NT${r.get('price_min', '')}-{r.get('price_max', '')}."
                ),
                "created_at": stamp,
            })

    out = DATA_DIR / "reviews_raw.csv"
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["restaurant_id", "review_text"])
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
