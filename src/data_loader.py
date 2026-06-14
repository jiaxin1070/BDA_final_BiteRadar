from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def _split_list(value: object) -> list[str]:
    """Convert pipe-separated strings into clean lists."""
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    return [x.strip() for x in str(value).split("|") if x.strip()]


def _list_to_pipe(values: Iterable[str]) -> str:
    return "|".join([str(v).strip() for v in values if str(v).strip()])


def load_restaurants(processed: bool = True) -> pd.DataFrame:
    """Load processed restaurant profiles. Falls back to raw data if needed."""
    path = DATA_DIR / ("restaurants_processed.csv" if processed else "restaurants_raw.csv")
    if not path.exists():
        fallback = DATA_DIR / "restaurants_raw.csv"
        if fallback.exists():
            path = fallback
        else:
            raise FileNotFoundError(
                f"Cannot find {path}. Run `python scripts/build_demo_data.py` and "
                "`python scripts/process_data.py` first."
            )
    df = pd.read_csv(path)

    for col in [
        "positive_tags",
        "negative_tags",
        "occasion_tags",
        "cuisine_tags",
        "recommended_dishes",
        "photo_tags",
    ]:
        if col in df.columns:
            df[col] = df[col].apply(_split_list)
    return df


def load_reviews() -> pd.DataFrame:
    path = DATA_DIR / "reviews_raw.csv"
    if not path.exists():
        raise FileNotFoundError("Cannot find data/reviews_raw.csv")
    return pd.read_csv(path)


def save_processed_restaurants(df: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or DATA_DIR / "restaurants_processed.csv"
    output = df.copy()
    for col in [
        "positive_tags",
        "negative_tags",
        "occasion_tags",
        "cuisine_tags",
        "recommended_dishes",
        "photo_tags",
    ]:
        if col in output.columns:
            output[col] = output[col].apply(lambda x: _list_to_pipe(x) if isinstance(x, list) else x)
    output.to_csv(path, index=False)
    return path


def load_photos() -> pd.DataFrame:
    path = DATA_DIR / "photos_raw.csv"
    if not path.exists():
        return pd.DataFrame(columns=["photo_id", "restaurant_id", "photo_url", "photo_type", "photo_tags"])
    df = pd.read_csv(path)
    if "photo_tags" in df.columns:
        df["photo_tags"] = df["photo_tags"].apply(_split_list)
    return df
