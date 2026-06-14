from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return float(max(low, min(high, value)))


def price_fit(price_min: float, price_max: float, budget: float) -> float:
    if budget <= 0:
        return 0.5
    if price_max <= budget:
        return 1.0
    if price_min > budget:
        return clamp(1 - ((price_min - budget) / max(budget, 1)), 0, 0.45)
    return 0.75


def list_match_score(options: list[str], desired: str | list[str] | None) -> float:
    if desired is None or desired == "Any" or desired == []:
        return 0.7
    if isinstance(desired, str):
        desired_set = {desired.lower()}
    else:
        desired_set = {str(x).lower() for x in desired}
    option_set = {str(x).lower() for x in options}
    if desired_set & option_set:
        return 1.0
    return 0.35


@dataclass
class MemberPreference:
    name: str
    budget: float
    cuisine: str = "Any"
    occasion: str = "Any"
    priority: str = "Balanced"
    avoid_crowded: bool = False
    needs_quiet: bool = False
    wants_photo_spot: bool = False
    vegetarian_friendly: bool = False


def score_for_member(row: pd.Series, pref: MemberPreference) -> dict[str, float]:
    cuisine_tags = row.get("cuisine_tags", [])
    occasion_tags = row.get("occasion_tags", [])
    positive_tags = row.get("positive_tags", [])

    price_component = price_fit(row["price_min"], row["price_max"], pref.budget)
    cuisine_component = list_match_score(cuisine_tags, pref.cuisine)
    occasion_component = list_match_score(occasion_tags, pref.occasion)
    rating_component = clamp(row["rating"] / 5)
    food_component = clamp(row["food_score"] / 5)
    vibe_component = clamp(row["vibe_score"] / 5)
    value_component = clamp(row["value_score"] / 5)
    distance_component = clamp(1 - (row["distance_min"] / 30), 0.1, 1.0)
    quiet_component = clamp(row["quiet_score"] / 5)
    group_component = clamp(row["group_score"] / 5)
    photo_component = clamp(row["photo_score"] / 5)
    risk_component = clamp(1 - (row["waiting_risk"] / 5), 0.05, 1.0)

    weights = {
        "rating": 0.12,
        "food": 0.15,
        "vibe": 0.10,
        "value": 0.12,
        "price": 0.13,
        "distance": 0.10,
        "cuisine": 0.10,
        "occasion": 0.10,
        "risk": 0.08,
    }

    if pref.priority == "Price":
        weights.update({"price": 0.22, "value": 0.18, "vibe": 0.06})
    elif pref.priority == "Food":
        weights.update({"food": 0.25, "rating": 0.15, "vibe": 0.06})
    elif pref.priority == "Vibe":
        weights.update({"vibe": 0.23, "occasion": 0.16, "photo": 0.08})
    elif pref.priority == "Distance":
        weights.update({"distance": 0.23, "price": 0.14})
    elif pref.priority == "No Queue":
        weights.update({"risk": 0.22, "distance": 0.13})
    elif pref.priority == "Photo":
        weights.update({"photo": 0.23, "vibe": 0.16, "occasion": 0.14})

    # Optional weights default to zero if not explicitly set above.
    components = {
        "rating": rating_component,
        "food": food_component,
        "vibe": vibe_component,
        "value": value_component,
        "price": price_component,
        "distance": distance_component,
        "cuisine": cuisine_component,
        "occasion": occasion_component,
        "risk": risk_component,
        "quiet": quiet_component,
        "group": group_component,
        "photo": photo_component,
    }

    if pref.needs_quiet:
        weights["quiet"] = weights.get("quiet", 0) + 0.16
    if pref.wants_photo_spot:
        weights["photo"] = weights.get("photo", 0) + 0.16
    if pref.avoid_crowded:
        weights["risk"] = weights.get("risk", 0) + 0.16
    if pref.vegetarian_friendly:
        veggie_fit = 1.0 if "vegetarian options" in [str(x).lower() for x in positive_tags] else 0.35
        components["vegetarian"] = veggie_fit
        weights["vegetarian"] = 0.16

    total_weight = sum(weights.values())
    final_score = sum(components[k] * w for k, w in weights.items()) / total_weight
    return {
        "member_score": clamp(final_score) * 100,
        "price_fit": price_component * 100,
        "cuisine_fit": cuisine_component * 100,
        "occasion_fit": occasion_component * 100,
        "risk_fit": risk_component * 100,
    }


def group_score(row: pd.Series, preferences: list[MemberPreference]) -> dict[str, Any]:
    if not preferences:
        preferences = [MemberPreference(name="Default", budget=350)]
    member_scores = [score_for_member(row, pref)["member_score"] for pref in preferences]
    avg_score = float(np.mean(member_scores))
    disagreement = float(np.std(member_scores)) if len(member_scores) > 1 else 0.0
    final_score = clamp((avg_score - disagreement * 0.35) / 100) * 100
    return {
        "group_match_score": round(final_score, 1),
        "avg_member_score": round(avg_score, 1),
        "disagreement_penalty": round(disagreement * 0.35, 1),
        "member_scores": [round(s, 1) for s in member_scores],
    }


def explain_match(row: pd.Series, preferences: list[MemberPreference]) -> list[str]:
    reasons: list[str] = []
    max_budget = max([p.budget for p in preferences], default=350)
    desired_cuisines = {p.cuisine for p in preferences if p.cuisine != "Any"}
    desired_occasions = {p.occasion for p in preferences if p.occasion != "Any"}
    cuisine_tags = {str(x) for x in row.get("cuisine_tags", [])}
    occasion_tags = {str(x) for x in row.get("occasion_tags", [])}

    if row["price_max"] <= max_budget:
        reasons.append(f"Fits the group budget: about NT${int(row['price_min'])}–{int(row['price_max'])} per person.")
    if desired_cuisines and (desired_cuisines & cuisine_tags):
        reasons.append("Matches at least one requested cuisine preference.")
    if desired_occasions and (desired_occasions & occasion_tags):
        reasons.append("Matches the planned dining occasion.")
    if row["rating"] >= 4.3:
        reasons.append(f"Strong public rating signal ({row['rating']:.1f}/5).")
    if row["group_score"] >= 4.2:
        reasons.append("Good for group dining or small gatherings.")
    if row["waiting_risk"] <= 2.7:
        reasons.append("Relatively low waiting-time risk in the demo data.")
    if not reasons:
        reasons.append("Balanced match across price, distance, rating, and dining context.")
    return reasons[:4]
