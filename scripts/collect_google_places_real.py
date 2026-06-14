"""Collect real restaurant metadata from Google Places API (New).

This script is optional. The app can run on demo CSV data, but this script lets
BiteRadar ingest real restaurant metadata for a selected area.

Important data ethics note:
- Use official APIs and follow Google Maps Platform Terms.
- By default, this script collects place metadata only.
- Reviews are optional via --include-reviews. If you use them, be careful about
  storage, redistribution, attribution, and caching restrictions. For course demos,
  prefer storing derived summaries/tags instead of raw third-party review text.
- Photos are not downloaded by default. The script stores photo resource names
  and uses placeholder display images unless you provide your own licensed or
  restaurant-submitted images.

Example:
    python scripts/collect_google_places_real.py \
      --query "restaurants near National Taiwan University" \
      --area Gongguan --limit 20

With reviews, only if you understand the provider terms:
    python scripts/collect_google_places_real.py --query "台大 公館 餐廳" --include-reviews
"""
from __future__ import annotations

import argparse
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
RAW_DIR = DATA_DIR / "raw_api"
RAW_DIR.mkdir(exist_ok=True)

NTU_LAT = 25.0145
NTU_LNG = 121.5340

CUISINE_HINTS = {
    "cafe": ["cafe", "coffee", "bakery"],
    "ramen": ["ramen", "noodle"],
    "japanese": ["japanese", "sushi", "izakaya", "japan"],
    "korean": ["korean", "bbq"],
    "italian": ["italian", "pizza", "pasta"],
    "hot pot": ["hot pot", "shabu", "mala"],
    "taiwanese": ["taiwanese", "bento", "breakfast", "restaurant"],
    "dessert": ["dessert", "ice", "cake"],
    "thai": ["thai"],
    "burger": ["burger", "american"],
}

PRICE_MAP = {
    "PRICE_LEVEL_FREE": (0, 0),
    "PRICE_LEVEL_INEXPENSIVE": (100, 250),
    "PRICE_LEVEL_MODERATE": (250, 500),
    "PRICE_LEVEL_EXPENSIVE": (500, 900),
    "PRICE_LEVEL_VERY_EXPENSIVE": (900, 1500),
}


def require_key() -> str:
    load_dotenv(ROOT / ".env")
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing GOOGLE_PLACES_API_KEY. Copy .env.example to .env and fill your key, "
            "or keep using the sample CSV demo."
        )
    return key


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def infer_cuisine(name: str, types: list[str]) -> str:
    text = " ".join([name] + types).lower()
    for cuisine, keys in CUISINE_HINTS.items():
        if any(k in text for k in keys):
            return cuisine.title()
    return "Restaurant"


def score_from_rating(rating: float, default: float = 3.8) -> float:
    if pd.isna(rating) or rating <= 0:
        return default
    # Translate rating into a mild 1-5 score, avoiding all dimensions being identical.
    return max(2.5, min(5.0, 0.55 * float(rating) + 1.75))


def place_text_search(query: str, limit: int, area_lat: float, area_lng: float, radius_m: int) -> list[dict[str, Any]]:
    key = require_key()
    url = "https://places.googleapis.com/v1/places:searchText"
    field_mask = ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "places.primaryType",
        "places.types",
        "places.googleMapsUri",
        "places.websiteUri",
        "places.photos.name",
    ])
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": field_mask,
    }
    body = {
        "textQuery": query,
        "includedType": "restaurant",
        "maxResultCount": min(max(limit, 1), 20),
        "locationBias": {
            "circle": {
                "center": {"latitude": area_lat, "longitude": area_lng},
                "radius": radius_m,
            }
        },
        "languageCode": "en",
    }
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    (RAW_DIR / f"google_places_textsearch_{stamp}.json").write_text(resp.text, encoding="utf-8")
    return payload.get("places", [])[:limit]


def place_details(place_id: str, include_reviews: bool = False) -> dict[str, Any]:
    key = require_key()
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    fields = [
        "id", "displayName", "formattedAddress", "location", "rating", "userRatingCount",
        "priceLevel", "primaryType", "types", "googleMapsUri", "websiteUri", "photos.name"
    ]
    if include_reviews:
        fields.extend([
            "reviews.name", "reviews.rating", "reviews.text", "reviews.publishTime",
            "reviews.relativePublishTimeDescription", "reviews.authorAttribution.displayName",
            "reviews.authorAttribution.uri",
        ])
    headers = {
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": ",".join(fields),
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def convert_places_to_rows(places: list[dict[str, Any]], area: str, center_lat: float, center_lng: float) -> tuple[list[dict], list[dict]]:
    restaurants: list[dict] = []
    photos: list[dict] = []
    for idx, p in enumerate(places, start=1):
        place_id = p.get("id") or f"G{idx:03d}"
        display = p.get("displayName", {}) or {}
        name = display.get("text") or p.get("name") or f"Restaurant {idx}"
        loc = p.get("location", {}) or {}
        lat = float(loc.get("latitude") or center_lat)
        lng = float(loc.get("longitude") or center_lng)
        km = haversine_km(center_lat, center_lng, lat, lng)
        distance_min = max(1, round(km / 4.8 * 60))  # rough walking time
        rating = float(p.get("rating") or 4.0)
        types = p.get("types") or []
        cuisine = infer_cuisine(name, types)
        price_min, price_max = PRICE_MAP.get(str(p.get("priceLevel")), (180, 500))
        user_count = int(p.get("userRatingCount") or 0)
        base_score = score_from_rating(rating)
        vibe = min(5.0, base_score + (0.2 if any(t in types for t in ["cafe", "bakery"]) else 0.0))
        value = max(2.5, min(5.0, 5.1 - price_max / 450 + rating / 5))
        waiting_risk = min(5.0, 2.0 + math.log10(user_count + 1) * 0.55)
        restaurant_id = f"G{idx:03d}"
        restaurants.append({
            "restaurant_id": restaurant_id,
            "name": name,
            "area": area,
            "primary_cuisine": cuisine,
            "price_min": price_min,
            "price_max": price_max,
            "rating": rating,
            "distance_min": distance_min,
            "food_score": base_score,
            "vibe_score": vibe,
            "value_score": value,
            "quiet_score": 3.2 if cuisine.lower() != "cafe" else 4.1,
            "group_score": 3.6,
            "photo_score": 3.8,
            "waiting_risk": waiting_risk,
            "address": p.get("formattedAddress", ""),
            "google_place_id": place_id,
            "google_maps_uri": p.get("googleMapsUri", ""),
            "website_uri": p.get("websiteUri", ""),
            "source": "google_places_api",
        })
        for j, photo in enumerate(p.get("photos", [])[:3], start=1):
            photo_name = photo.get("name", "")
            photos.append({
                "photo_id": f"{restaurant_id}_GP{j}",
                "restaurant_id": restaurant_id,
                "photo_url": f"https://placehold.co/600x400?text={name.replace(' ', '+')}",
                "photo_type": "api_reference",
                "photo_tags": "external_reference|not_downloaded",
                "provider_photo_name": photo_name,
            })
        if not p.get("photos"):
            photos.append({
                "photo_id": f"{restaurant_id}_P1",
                "restaurant_id": restaurant_id,
                "photo_url": f"https://placehold.co/600x400?text={name.replace(' ', '+')}",
                "photo_type": "placeholder",
                "photo_tags": "placeholder|demo",
                "provider_photo_name": "",
            })
    return restaurants, photos


def extract_google_reviews(details: list[dict[str, Any]], id_map: dict[str, str]) -> list[dict]:
    rows: list[dict] = []
    for detail in details:
        place_id = detail.get("id")
        rid = id_map.get(place_id)
        if not rid:
            continue
        for i, rev in enumerate(detail.get("reviews", []) or [], start=1):
            text_obj = rev.get("text") or {}
            if isinstance(text_obj, dict):
                text = text_obj.get("text") or ""
            else:
                text = str(text_obj)
            if not text.strip():
                continue
            rows.append({
                "review_id": f"{rid}_GREV{i}",
                "restaurant_id": rid,
                "source": "google_places_api_optional_review",
                "rating": rev.get("rating", ""),
                "review_text": text.strip(),
                "created_at": rev.get("publishTime", ""),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="restaurants near National Taiwan University")
    parser.add_argument("--area", default="Gongguan")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--lat", type=float, default=NTU_LAT)
    parser.add_argument("--lng", type=float, default=NTU_LNG)
    parser.add_argument("--radius-m", type=int, default=1200)
    parser.add_argument("--include-reviews", action="store_true")
    parser.add_argument("--append", action="store_true", help="Append to existing raw CSV files instead of overwriting")
    args = parser.parse_args()

    places = place_text_search(args.query, args.limit, args.lat, args.lng, args.radius_m)

    details: list[dict[str, Any]] = []
    if args.include_reviews:
        for p in places:
            if p.get("id"):
                details.append(place_details(p["id"], include_reviews=True))
        # Prefer detailed payload if available.
        places_for_convert = details or places
    else:
        places_for_convert = places

    restaurant_rows, photo_rows = convert_places_to_rows(places_for_convert, args.area, args.lat, args.lng)
    id_map = {r.get("google_place_id"): r["restaurant_id"] for r in restaurant_rows}
    review_rows = extract_google_reviews(details, id_map) if args.include_reviews else []

    def write_csv(path: Path, rows: list[dict]) -> None:
        new_df = pd.DataFrame(rows)
        if args.append and path.exists():
            old_df = pd.read_csv(path)
            new_df = pd.concat([old_df, new_df], ignore_index=True)
        new_df.to_csv(path, index=False)
        print(f"Wrote {len(new_df)} rows to {path}")

    write_csv(DATA_DIR / "restaurants_raw.csv", restaurant_rows)
    write_csv(DATA_DIR / "photos_raw.csv", photo_rows)
    if review_rows:
        write_csv(DATA_DIR / "google_reviews_raw.csv", review_rows)
        print("Raw Google review text was saved because --include-reviews was used. Review provider terms before redistribution.")
    else:
        # Keep an empty file so downstream merge scripts are predictable.
        path = DATA_DIR / "google_reviews_raw.csv"
        if not path.exists():
            pd.DataFrame(columns=["review_id", "restaurant_id", "source", "rating", "review_text", "created_at"]).to_csv(path, index=False)
        print("No raw reviews collected. Use user surveys, manual notes, articles, or --include-reviews if allowed.")


if __name__ == "__main__":
    main()
