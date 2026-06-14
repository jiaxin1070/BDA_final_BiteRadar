from __future__ import annotations

import re
from collections import Counter


KEYWORD_TAGS: dict[str, list[str]] = {
    "quiet": ["quiet", "calm", "study", "read", "laptop", "work", "peaceful"],
    "cozy": ["cozy", "warm", "comfortable", "relax", "wood", "small"],
    "crowded": ["crowded", "packed", "busy", "full", "long line", "queue", "waiting"],
    "large portion": ["large portion", "big portion", "filling", "huge", "full"],
    "cheap": ["cheap", "affordable", "student", "value", "budget", "cp"],
    "expensive": ["expensive", "pricey", "overpriced", "costly"],
    "photogenic": ["photo", "photogenic", "instagram", "beautiful", "pretty", "aesthetic"],
    "date-friendly": ["date", "romantic", "anniversary", "atmosphere", "vibe"],
    "group-friendly": ["group", "friends", "gathering", "large table", "party"],
    "fast meal": ["fast", "quick", "lunch", "takeout", "efficient"],
    "good service": ["friendly", "service", "staff", "polite"],
    "slow service": ["slow", "waited", "forgot", "delay"],
    "dessert": ["cake", "dessert", "tiramisu", "pudding", "sweet"],
    "coffee": ["coffee", "latte", "espresso", "americano", "cappuccino"],
    "spicy": ["spicy", "chili", "mala", "pepper"],
    "vegetarian options": ["vegetarian", "vegan", "tofu", "plant"],
}

DISH_HINTS = [
    "ramen", "curry", "fried chicken", "beef noodle", "dumpling", "hot pot",
    "bibimbap", "pasta", "pizza", "risotto", "burger", "coffee", "latte",
    "tiramisu", "cheesecake", "toast", "brunch plate", "sushi", "bento",
    "noodle", "rice bowl", "sandwich", "steak", "salad", "dessert",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def extract_tags_from_texts(texts: list[str], min_count: int = 1, max_tags: int = 8) -> list[str]:
    """Simple transparent rule-based tag extraction for the MVP.

    This is intentionally lightweight and reproducible for course submission.
    You can replace it with an LLM or embedding-based tagger later.
    """
    counter: Counter[str] = Counter()
    joined_texts = [normalize_text(t) for t in texts]
    for tag, keywords in KEYWORD_TAGS.items():
        for text in joined_texts:
            if any(k in text for k in keywords):
                counter[tag] += 1
    return [tag for tag, count in counter.most_common(max_tags) if count >= min_count]


def extract_dishes(texts: list[str], max_dishes: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    joined_texts = [normalize_text(t) for t in texts]
    for dish in DISH_HINTS:
        for text in joined_texts:
            if dish in text:
                counter[dish.title()] += 1
    return [dish for dish, _ in counter.most_common(max_dishes)]


def infer_personality(row: dict) -> str:
    """Infer a restaurant personality from scores and tags."""
    positive = set(row.get("positive_tags", []))
    negative = set(row.get("negative_tags", []))
    occasion = set(row.get("occasion_tags", []))
    price_max = float(row.get("price_max", 999))
    food_score = float(row.get("food_score", 0))
    vibe_score = float(row.get("vibe_score", 0))
    value_score = float(row.get("value_score", 0))
    photo_score = float(row.get("photo_score", 0))
    waiting_risk = float(row.get("waiting_risk", 0))
    group_score = float(row.get("group_score", 0))
    quiet_score = float(row.get("quiet_score", 0))

    if price_max <= 250 and value_score >= 4.1:
        return "Hungry Student Saver"
    if quiet_score >= 4.0 and ("study" in occasion or "quiet" in positive or "coffee" in positive):
        return "Cozy Scholar"
    if vibe_score >= 4.2 and ("date" in occasion or "date-friendly" in positive):
        return "Date Night Pick"
    if photo_score >= 4.2 and ("photogenic" in positive or "photo" in occasion):
        return "Photo-First Cafe"
    if group_score >= 4.2 or "group-friendly" in positive:
        return "Group Gathering Place"
    if waiting_risk >= 3.8 or "crowded" in negative:
        return "Risky but Popular"
    if food_score >= 4.4 and vibe_score < 4.0:
        return "Serious Foodie Spot"
    return "Balanced Local Pick"


def infer_occasions(tags: list[str], cuisine: str, quiet_score: float, group_score: float, photo_score: float) -> list[str]:
    result: list[str] = []
    tag_set = set(tags)
    if quiet_score >= 4.0 or "quiet" in tag_set or "coffee" in tag_set:
        result.append("study")
    if "date-friendly" in tag_set or photo_score >= 4.0:
        result.append("date")
    if group_score >= 4.0 or "group-friendly" in tag_set:
        result.append("group gathering")
    if "fast meal" in tag_set or cuisine.lower() in {"bento", "noodles", "taiwanese"}:
        result.append("quick meal")
    if "photogenic" in tag_set or photo_score >= 4.2:
        result.append("social sharing")
    if "cheap" in tag_set:
        result.append("student budget")
    if not result:
        result.append("casual meal")
    return result[:5]
