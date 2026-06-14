"""Optional Google Places API collection template.

This file is intentionally a template, not a default data source.
For the course project, use official APIs and respect the provider's terms.
Avoid unauthorized scraping and avoid redistributing raw third-party reviews.

Usage idea:
1. Put GOOGLE_PLACES_API_KEY in a .env file.
2. Search nearby restaurants.
3. Store only fields you are allowed to store and derived metadata needed for the demo.

This script is not required for the MVP demo, which runs on synthetic sample data.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def search_places(query: str, location: str = "25.0145,121.5340", radius: int = 1200) -> list[dict]:
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_PLACES_API_KEY in environment or .env")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "type": "restaurant",
        "key": api_key,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("results", [])


def main() -> None:
    results = search_places("restaurants near National Taiwan University")
    rows = []
    for item in results:
        rows.append({
            "place_id": item.get("place_id"),
            "name": item.get("name"),
            "rating": item.get("rating"),
            "user_ratings_total": item.get("user_ratings_total"),
            "address": item.get("formatted_address"),
            "lat": item.get("geometry", {}).get("location", {}).get("lat"),
            "lng": item.get("geometry", {}).get("location", {}).get("lng"),
        })
    out = DATA_DIR / "google_places_sample.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
