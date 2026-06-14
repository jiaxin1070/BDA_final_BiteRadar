from __future__ import annotations

import html
import math
from typing import Iterable

import pandas as pd
import streamlit as st

from src.card_generator import generate_restaurant_card


def _clean_items(value: object, limit: int | None = None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, list):
        items = [str(x).strip() for x in value if str(x).strip()]
    else:
        items = [x.strip() for x in str(value).split("|") if x.strip()]
    return items[:limit] if limit else items


def _badge_html(items: Iterable[str], kind: str = "neutral", limit: int = 6) -> str:
    tags = list(items)[:limit]
    if not tags:
        return '<span class="br-muted">No repeated signal yet</span>'
    return "".join(
        f'<span class="br-badge br-badge-{kind}">{html.escape(str(tag))}</span>'
        for tag in tags
    )


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        value_float = float(value)
        if math.isnan(value_float):
            return default
        return value_float
    except Exception:
        return default


def _safe_int(value: object, default: int = 0) -> int:
    return int(round(_safe_float(value, float(default))))


def _score_bar(label: str, value: object, max_value: float = 5.0) -> str:
    value_float = _safe_float(value, 0.0)
    pct = max(0, min(100, value_float / max_value * 100))
    # Keep this HTML on one line. Multi-line, indented raw HTML can be interpreted
    # by Markdown as a code block, causing stray </div> tags to appear in Streamlit.
    return (
        f'<div class="br-score-row">'
        f'<div class="br-score-head"><span>{html.escape(label)}</span><b>{value_float:.1f}</b></div>'
        f'<div class="br-score-track"><div class="br-score-fill" style="width:{pct:.0f}%"></div></div>'
        f'</div>'
    )


def inject_global_css() -> None:
    st.markdown(
        """
<style>
:root {
    --br-cream: #fff7ed;
    --br-paper: #fffaf2;
    --br-ink: #1f2937;
    --br-muted: #6b7280;
    --br-orange: #f97316;
    --br-amber: #f59e0b;
    --br-green: #059669;
    --br-red: #dc2626;
    --br-blue: #2563eb;
    --br-border: rgba(31, 41, 55, 0.10);
}
.main .block-container { padding-top: 2rem; }
.br-card {
    border: 1px solid var(--br-border);
    border-radius: 28px;
    padding: 24px;
    background: linear-gradient(145deg, #fffaf2 0%, #ffffff 56%, #fff7ed 100%);
    box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
    margin-bottom: 18px;
}
.br-mini-label {
    color: var(--br-muted);
    font-size: 0.85rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    font-weight: 800;
    margin-bottom: 4px;
}
.br-title {
    color: var(--br-ink);
    font-size: 1.7rem;
    font-weight: 900;
    line-height: 1.15;
    margin: 0 0 4px 0;
}
.br-meta { color: var(--br-muted); font-size: .95rem; margin-bottom: 12px; }
.br-personality {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #111827;
    color: white;
    padding: 9px 14px;
    border-radius: 999px;
    font-weight: 850;
    margin: 6px 0 12px 0;
    box-shadow: 0 8px 18px rgba(17,24,39,.18);
}
.br-summary {
    font-size: 1.02rem;
    line-height: 1.6;
    color: #374151;
    padding: 12px 0 6px 0;
}
.br-section-title {
    font-size: .9rem;
    font-weight: 850;
    color: #374151;
    margin: 12px 0 7px 0;
}
.br-badge {
    display: inline-block;
    margin: 4px 5px 4px 0;
    padding: 7px 10px;
    border-radius: 999px;
    font-size: .86rem;
    font-weight: 750;
    border: 1px solid transparent;
}
.br-badge-good { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.br-badge-risk { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
.br-badge-occasion { background: #dbeafe; color: #1e40af; border-color: #bfdbfe; }
.br-badge-dish { background: #ffedd5; color: #9a3412; border-color: #fed7aa; }
.br-badge-neutral { background: #f3f4f6; color: #374151; border-color: #e5e7eb; }
.br-muted { color: var(--br-muted); font-size: .9rem; }
.br-score-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 14px;
    margin-top: 12px;
}
.br-score-head {
    display: flex;
    justify-content: space-between;
    font-size: .82rem;
    color: #4b5563;
    margin-bottom: 4px;
}
.br-score-track {
    height: 8px;
    border-radius: 999px;
    background: #e5e7eb;
    overflow: hidden;
}
.br-score-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #f97316, #f59e0b, #10b981);
}
.br-rank-pill {
    float: right;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 8px 13px;
    border-radius: 999px;
    font-weight: 900;
}
.br-social-card {
    border: 1px solid var(--br-border);
    border-radius: 34px;
    padding: 22px;
    background: radial-gradient(circle at top left, #ffedd5, transparent 38%), linear-gradient(145deg, #111827, #1f2937 45%, #422006);
    color: white;
    box-shadow: 0 22px 60px rgba(15, 23, 42, 0.18);
    margin: 10px 0 18px 0;
}
.br-social-card .br-badge { background: rgba(255,255,255,.15); color: white; border-color: rgba(255,255,255,.2); }
.br-social-title { font-size: 2rem; font-weight: 950; line-height: 1.05; margin: 4px 0; }
.br-social-persona { color: #fbbf24; font-size: 1.15rem; font-weight: 900; }
.br-social-summary { color: #f9fafb; line-height: 1.55; margin: 12px 0; }
</style>
        """.strip(),
        unsafe_allow_html=True,
    )


def get_photo_url(photos: pd.DataFrame, restaurant_id: str) -> str | None:
    if photos is None or photos.empty or "restaurant_id" not in photos.columns:
        return None
    subset = photos[photos["restaurant_id"].astype(str) == str(restaurant_id)]
    if subset.empty:
        return None
    if "photo_type" in subset.columns:
        ordered = subset.copy()
        order_map = {"food": 0, "interior": 1, "exterior": 2, "menu": 3, "placeholder": 4}
        ordered["_rank"] = ordered["photo_type"].map(order_map).fillna(5)
        subset = ordered.sort_values("_rank")
    photo_url = str(subset.iloc[0].get("photo_url", "")).strip()
    return photo_url or None


def render_personality_card(
    row: pd.Series | dict,
    photos: pd.DataFrame | None = None,
    show_generate_button: bool = True,
    key_prefix: str = "card",
) -> None:
    data = row.to_dict() if isinstance(row, pd.Series) else dict(row)

    rid = str(data.get("restaurant_id", "restaurant"))
    photo_url = get_photo_url(photos, rid) if photos is not None else data.get("photo_url")
    score = data.get("group_match_score", _safe_float(data.get("rating", 0)) * 20)

    price_min = _safe_int(data.get("price_min", 0))
    price_max = _safe_int(data.get("price_max", 0))
    distance_min = _safe_int(data.get("distance_min", 0))

    score_grid = "".join(
        [
            _score_bar("Food", data.get("food_score", 0)),
            _score_bar("Vibe", data.get("vibe_score", 0)),
            _score_bar("Value", data.get("value_score", 0)),
            _score_bar("Group", data.get("group_score", 0)),
        ]
    )

    card_html = f"""
<div class="br-card">
  <span class="br-rank-pill">{_safe_float(score):.0f}%</span>
  <div class="br-mini-label">Restaurant Personality Card</div>
  <div class="br-title">{html.escape(str(data.get('name', 'Restaurant')))}</div>
  <div class="br-meta">{html.escape(str(data.get('area','Area')))} · {html.escape(str(data.get('primary_cuisine','Food')))} · NT${price_min}–{price_max} · {distance_min} min walk</div>
  <div class="br-personality">✨ {html.escape(str(data.get('personality_type', 'Restaurant Personality')))}</div>
  <div class="br-summary">{html.escape(str(data.get('one_line_summary', 'No summary yet.')))}</div>
  <div class="br-section-title">Best for</div>
  <div>{_badge_html(_clean_items(data.get('occasion_tags'), 5), 'occasion')}</div>
  <div class="br-section-title">Positive signals</div>
  <div>{_badge_html(_clean_items(data.get('positive_tags'), 6), 'good')}</div>
  <div class="br-section-title">Watch-outs</div>
  <div>{_badge_html(_clean_items(data.get('negative_tags'), 4), 'risk')}</div>
  <div class="br-section-title">Recommended dishes</div>
  <div>{_badge_html(_clean_items(data.get('recommended_dishes'), 5), 'dish')}</div>
  <div class="br-score-grid">{score_grid}</div>
</div>
""".strip()

    with st.container():
        col_img, col_info = st.columns([0.95, 1.45], gap="large")
        with col_img:
            if photo_url:
                st.image(photo_url, use_container_width=True)
            else:
                st.markdown(
                    '<div style="height:260px;border-radius:26px;background:linear-gradient(135deg,#fed7aa,#fde68a,#bbf7d0);display:flex;align-items:center;justify-content:center;font-weight:900;color:#374151;">BiteRadar Preview</div>',
                    unsafe_allow_html=True,
                )
        with col_info:
            st.markdown(card_html, unsafe_allow_html=True)

            if "match_reasons" in data and isinstance(data["match_reasons"], list):
                with st.expander("Why this matches this group"):
                    for reason in data["match_reasons"]:
                        st.write(f"- {reason}")

            if show_generate_button:
                if st.button("Generate polished social share card", key=f"{key_prefix}_{rid}"):
                    path = generate_restaurant_card(data, photo_url=photo_url)
                    st.success(f"Share card generated: {path.name}")
                    st.image(str(path), use_container_width=True)
                    with open(path, "rb") as f:
                        st.download_button(
                            "Download PNG share card",
                            f,
                            file_name=path.name,
                            mime="image/png",
                            key=f"download_{key_prefix}_{rid}",
                        )


def render_social_preview(row: pd.Series | dict, photos: pd.DataFrame | None = None) -> None:
    data = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    rid = str(data.get("restaurant_id", "restaurant"))
    photo_url = get_photo_url(photos, rid) if photos is not None else data.get("photo_url")

    price_min = _safe_int(data.get("price_min", 0))
    price_max = _safe_int(data.get("price_max", 0))

    social_html = f"""
<div class="br-social-card">
  <div class="br-mini-label" style="color:#fde68a;">Tonight's BiteRadar Pick</div>
  <div class="br-social-title">{html.escape(str(data.get('name', 'Restaurant')))}</div>
  <div class="br-social-persona">{html.escape(str(data.get('personality_type', 'Restaurant Personality')))}</div>
  <div class="br-social-summary">{html.escape(str(data.get('one_line_summary', 'No summary yet.')))}</div>
  <div>{_badge_html(_clean_items(data.get('occasion_tags'), 4), 'neutral')}</div>
  <br />
  <div style="color:#d1d5db;">{html.escape(str(data.get('area','Area')))} · {html.escape(str(data.get('primary_cuisine','Food')))} · NT${price_min}–{price_max}</div>
  <div style="margin-top:14px;font-weight:900;color:#fbbf24;">Generated by BiteRadar ✨</div>
</div>
""".strip()

    col1, col2 = st.columns([1, 1.1], gap="large")
    with col1:
        if photo_url:
            st.image(photo_url, use_container_width=True)
    with col2:
        st.markdown(social_html, unsafe_allow_html=True)
        if st.button("Create downloadable social card", key=f"social_{rid}"):
            path = generate_restaurant_card(data, photo_url=photo_url)
            st.image(str(path), use_container_width=True)
            with open(path, "rb") as f:
                st.download_button(
                    "Download PNG",
                    f,
                    file_name=path.name,
                    mime="image/png",
                    key=f"social_download_{rid}",
                )
