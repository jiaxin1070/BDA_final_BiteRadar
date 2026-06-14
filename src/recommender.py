from __future__ import annotations

import pandas as pd

from .scoring import MemberPreference, explain_match, group_score


def recommend_restaurants(
    restaurants: pd.DataFrame,
    preferences: list[MemberPreference],
    area: str = "Any",
    top_k: int = 10,
) -> pd.DataFrame:
    df = restaurants.copy()
    if area != "Any":
        df = df[df["area"].str.lower() == area.lower()].copy()
    if df.empty:
        return df

    scored = []
    for _, row in df.iterrows():
        score_info = group_score(row, preferences)
        item = row.to_dict()
        item.update(score_info)
        item["match_reasons"] = explain_match(row, preferences)
        scored.append(item)

    out = pd.DataFrame(scored).sort_values(
        by=["group_match_score", "rating", "food_score"], ascending=False
    )
    return out.head(top_k).reset_index(drop=True)


def category_picks(scored_df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return named recommendations for the UI."""
    picks: dict[str, pd.Series] = {}
    if scored_df.empty:
        return picks
    picks["Best Overall"] = scored_df.iloc[0]
    picks["Best Budget"] = scored_df.sort_values(
        by=["value_score", "price_max", "group_match_score"], ascending=[False, True, False]
    ).iloc[0]
    picks["Best Vibe"] = scored_df.sort_values(
        by=["vibe_score", "photo_score", "group_match_score"], ascending=False
    ).iloc[0]
    picks["Safest Pick"] = scored_df.sort_values(
        by=["waiting_risk", "rating", "group_match_score"], ascending=[True, False, False]
    ).iloc[0]
    picks["Wildcard"] = scored_df.sort_values(
        by=["photo_score", "food_score", "waiting_risk"], ascending=[False, False, False]
    ).iloc[0]
    return picks
