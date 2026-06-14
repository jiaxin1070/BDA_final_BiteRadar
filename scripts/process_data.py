from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import pandas as pd

from src.data_loader import save_processed_restaurants
from src.tagging import extract_dishes, extract_tags_from_texts, infer_occasions, infer_personality

DATA_DIR = ROOT / "data"


def make_summary(name: str, tags: list[str], dishes: list[str], negative: list[str]) -> str:
    tag_phrase = ", ".join(tags[:3]) if tags else "balanced dining signals"
    dish_phrase = ", ".join(dishes[:2]) if dishes else "its main dishes"
    neg_phrase = ", ".join(negative[:2]) if negative else "no major repeated warning in the demo reviews"
    return (
        f"{name} is mainly perceived as {tag_phrase}. Review snippets often mention {dish_phrase}. "
        f"Potential watch-outs include {neg_phrase}."
    )


def main() -> None:
    #restaurants = pd.read_csv(DATA_DIR / "restaurants_raw.csv")
    #reviews = pd.read_csv(DATA_DIR / "reviews_raw.csv")
    #photos = pd.read_csv(DATA_DIR / "photos_raw.csv")
    def read_csv_flexible(path):
        for encoding in ["utf-8-sig", "utf-8", "cp950", "big5"]:
            try:
                return pd.read_csv(path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"Cannot decode file: {path}")


    restaurants = read_csv_flexible(DATA_DIR / "restaurants_raw.csv")
    reviews = read_csv_flexible(DATA_DIR / "reviews_raw.csv")
    photos = read_csv_flexible(DATA_DIR / "photos_raw.csv")

    rows = []
    for _, r in restaurants.iterrows():
        rid = r["restaurant_id"]
        review_texts = reviews.loc[reviews["restaurant_id"] == rid, "review_text"].astype(str).tolist()
        photo_tags = []
        for value in photos.loc[photos["restaurant_id"] == rid, "photo_tags"].astype(str).tolist():
            photo_tags.extend([x.strip() for x in value.split("|") if x.strip()])
        extracted_tags = extract_tags_from_texts(review_texts, min_count=1, max_tags=10)
        positive_tags = [
            t for t in extracted_tags
            if t not in {"crowded", "expensive", "slow service"}
        ][:8]
        negative_tags = [
            t for t in extracted_tags
            if t in {"crowded", "expensive", "slow service"}
        ]
        if r["waiting_risk"] >= 3.5 and "crowded" not in negative_tags:
            negative_tags.append("crowded")
        if r["price_max"] >= 650 and "expensive" not in negative_tags:
            negative_tags.append("expensive")
        if r["vibe_score"] < 3.0 and "simple environment" not in negative_tags:
            negative_tags.append("simple environment")

        dishes = extract_dishes(review_texts, max_dishes=5)
        if not dishes:
            dishes = [r["primary_cuisine"]]
        occasion_tags = infer_occasions(
            positive_tags,
            r["primary_cuisine"],
            r["quiet_score"],
            r["group_score"],
            r["photo_score"],
        )
        cuisine_tags = [r["primary_cuisine"], "Any"]
        row = r.to_dict()
        row.update({
            "cuisine_tags": cuisine_tags,
            "positive_tags": positive_tags,
            "negative_tags": negative_tags[:6],
            "occasion_tags": occasion_tags,
            "recommended_dishes": dishes,
            "photo_tags": sorted(set(photo_tags)),
        })
        row["personality_type"] = infer_personality(row)
        row["one_line_summary"] = make_summary(
            r["name"], positive_tags, dishes, negative_tags
        )
        rows.append(row)

    processed = pd.DataFrame(rows)
    path = save_processed_restaurants(processed)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
