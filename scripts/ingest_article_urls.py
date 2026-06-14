"""Ingest user-provided restaurant article URLs into a local CSV.

This is intentionally URL-driven rather than broad web crawling. Put URLs in
`data/article_urls.csv` with columns:
    url,restaurant_hint

Then run:
    python scripts/ingest_article_urls.py

Respect each site's robots.txt, terms, copyright, and privacy rules. For a safer
course prototype, you may also paste article excerpts manually into
`data/articles_raw.csv` instead of fetching pages automatically.
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def clean_text(text: str, max_chars: int = 4000) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:max_chars]


def fetch_article(url: str) -> dict:
    headers = {"User-Agent": "BiteRadarCoursePrototype/0.1 (+educational project)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    body = clean_text("\n".join([p for p in paragraphs if len(p) >= 20]))
    return {
        "title": title,
        "text": body,
        "domain": urlparse(url).netloc,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA_DIR / "article_urls.csv"))
    parser.add_argument("--output", default=str(DATA_DIR / "articles_raw.csv"))
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sample = pd.DataFrame([{"url": "https://example.com", "restaurant_hint": "Example Restaurant"}])
        sample.to_csv(input_path, index=False)
        raise FileNotFoundError(
            f"Created sample {input_path}. Replace it with real URLs, then rerun."
        )

    urls = pd.read_csv(input_path)
    rows = []
    for idx, row in urls.iterrows():
        url = str(row.get("url", "")).strip()
        if not url or url == "nan":
            continue
        try:
            article = fetch_article(url)
            rows.append({
                "article_id": f"A{idx+1:04d}",
                "source": "user_provided_url",
                "url": url,
                "restaurant_hint": row.get("restaurant_hint", ""),
                **article,
            })
            print(f"Fetched {url}")
        except Exception as exc:
            print(f"Failed {url}: {exc}")

    out = Path(args.output)
    df = pd.DataFrame(rows)
    if args.append and out.exists():
        df = pd.concat([pd.read_csv(out), df], ignore_index=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
