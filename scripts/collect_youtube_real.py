"""Collect YouTube video metadata for restaurant discovery.

This script uses the official YouTube Data API v3. It collects video metadata
(title, description, channel, view count) that can be used as a weak signal for
restaurant/media mentions. It does not download videos.

Example:
    python scripts/collect_youtube_real.py --query "公館 美食 台大" --max-results 25
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
RAW_DIR = DATA_DIR / "raw_api"
RAW_DIR.mkdir(exist_ok=True)


def require_key() -> str:
    load_dotenv(ROOT / ".env")
    key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Missing YOUTUBE_API_KEY in .env")
    return key


def search_videos(query: str, max_results: int = 25, region_code: str = "TW") -> list[dict]:
    key = require_key()
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(max_results, 50),
        "regionCode": region_code,
        "key": key,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    (RAW_DIR / f"youtube_search_{stamp}.json").write_text(resp.text, encoding="utf-8")
    return payload.get("items", [])


def get_video_stats(video_ids: list[str]) -> dict[str, dict]:
    if not video_ids:
        return {}
    key = require_key()
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "statistics,contentDetails",
        "id": ",".join(video_ids[:50]),
        "key": key,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return {item["id"]: item for item in payload.get("items", [])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="公館 美食 台大")
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--region-code", default="TW")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    items = search_videos(args.query, args.max_results, args.region_code)
    ids = [item.get("id", {}).get("videoId") for item in items if item.get("id", {}).get("videoId")]
    stats = get_video_stats(ids)

    rows = []
    for item in items:
        vid = item.get("id", {}).get("videoId")
        snip = item.get("snippet", {})
        stat = stats.get(vid, {}).get("statistics", {})
        rows.append({
            "video_id": vid,
            "source": "youtube_data_api",
            "query": args.query,
            "title": snip.get("title", ""),
            "description": snip.get("description", ""),
            "channel_title": snip.get("channelTitle", ""),
            "published_at": snip.get("publishedAt", ""),
            "thumbnail_url": snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={vid}" if vid else "",
            "view_count": stat.get("viewCount", ""),
            "like_count": stat.get("likeCount", ""),
        })

    out = DATA_DIR / "youtube_videos_raw.csv"
    df = pd.DataFrame(rows)
    if args.append and out.exists():
        df = pd.concat([pd.read_csv(out), df], ignore_index=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
