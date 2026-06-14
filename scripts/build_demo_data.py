from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

RESTAURANTS = [
    ("R001", "Gongguan Cozy Cafe", "Gongguan", "Cafe", 180, 380, 4.5, 6, 4.1, 4.6, 4.0, 4.7, 3.4, 4.6, 2.9, "No. 1, NTU Area"),
    ("R002", "NTU Curry House", "Gongguan", "Japanese Curry", 150, 260, 4.3, 4, 4.3, 3.5, 4.6, 3.0, 3.8, 2.9, 2.4, "No. 2, NTU Area"),
    ("R003", "Riverside Ramen", "Gongguan", "Ramen", 220, 360, 4.4, 9, 4.6, 3.7, 3.8, 2.8, 3.1, 3.2, 3.8, "No. 3, NTU Area"),
    ("R004", "Warm Pot Studio", "Gongguan", "Hot Pot", 350, 650, 4.2, 10, 4.2, 4.1, 3.6, 2.9, 4.7, 3.7, 3.4, "No. 4, NTU Area"),
    ("R005", "Little Seoul Table", "Gongguan", "Korean", 220, 420, 4.4, 7, 4.2, 4.0, 4.0, 3.2, 4.4, 4.0, 3.1, "No. 5, NTU Area"),
    ("R006", "Hidden Dumpling Bar", "Gongguan", "Taiwanese", 90, 190, 4.1, 5, 4.0, 3.0, 4.7, 2.6, 3.5, 2.4, 2.2, "No. 6, NTU Area"),
    ("R007", "Sunlit Dessert Lab", "Gongguan", "Dessert", 180, 420, 4.6, 12, 4.3, 4.8, 3.8, 4.4, 3.5, 4.8, 3.6, "No. 7, NTU Area"),
    ("R008", "Campus Bento Express", "Gongguan", "Bento", 100, 180, 4.0, 3, 3.7, 2.8, 4.6, 2.2, 2.8, 2.0, 1.8, "No. 8, NTU Area"),
    ("R009", "Old Street Beef Noodle", "Gongguan", "Noodles", 160, 280, 4.5, 8, 4.7, 3.2, 4.4, 2.4, 3.7, 2.7, 3.2, "No. 9, NTU Area"),
    ("R010", "Moonlight Pasta", "Gongguan", "Italian", 320, 680, 4.3, 13, 4.1, 4.7, 3.2, 3.8, 4.0, 4.4, 3.0, "No. 10, NTU Area"),
    ("R011", "Quiet Bean Library", "Gongguan", "Cafe", 160, 350, 4.2, 11, 3.8, 4.5, 3.7, 4.8, 2.8, 4.1, 2.5, "No. 11, NTU Area"),
    ("R012", "Mala Friends Kitchen", "Gongguan", "Sichuan", 230, 480, 4.1, 14, 4.4, 3.5, 3.8, 2.0, 4.2, 3.3, 3.7, "No. 12, NTU Area"),
    ("R013", "Green Bowl Corner", "Gongguan", "Vegetarian", 180, 320, 4.4, 8, 4.2, 3.9, 4.1, 3.7, 3.4, 3.6, 2.4, "No. 13, NTU Area"),
    ("R014", "Night Owl Burger", "Gongguan", "Burger", 220, 390, 4.0, 15, 4.0, 3.8, 3.8, 2.4, 4.1, 3.5, 2.9, "No. 14, NTU Area"),
    ("R015", "Tea Alley Brunch", "Gongguan", "Brunch", 260, 520, 4.5, 7, 4.2, 4.6, 3.7, 3.9, 4.0, 4.5, 3.5, "No. 15, NTU Area"),
    ("R016", "Simple Sushi Counter", "Gongguan", "Sushi", 250, 500, 4.3, 12, 4.4, 3.8, 3.5, 2.8, 2.8, 3.4, 2.7, "No. 16, NTU Area"),
    ("R017", "Backstreet Thai Bowl", "Gongguan", "Thai", 180, 340, 4.2, 9, 4.3, 3.4, 4.2, 2.6, 3.6, 3.0, 2.5, "No. 17, NTU Area"),
    ("R018", "Red Brick Pizza", "Gongguan", "Pizza", 280, 550, 4.1, 16, 4.0, 4.2, 3.4, 2.8, 4.5, 4.1, 2.6, "No. 18, NTU Area"),
    ("R019", "Scholar Noodle Stand", "Gongguan", "Taiwanese", 70, 160, 4.2, 2, 3.9, 2.5, 4.8, 2.1, 2.7, 1.8, 1.6, "No. 19, NTU Area"),
    ("R020", "Glasshouse Bistro", "Da'an", "Bistro", 480, 980, 4.6, 23, 4.4, 4.9, 3.1, 3.8, 4.1, 4.9, 3.2, "No. 20, Daan Area"),
    ("R021", "Zhongzheng Vegan Plate", "Zhongzheng", "Vegetarian", 210, 390, 4.4, 18, 4.2, 3.8, 4.1, 3.4, 3.6, 3.5, 2.5, "No. 21, Zhongzheng Area"),
    ("R022", "Da'an Date Night Grill", "Da'an", "Grill", 520, 1100, 4.5, 25, 4.5, 4.8, 2.9, 3.6, 4.3, 4.6, 3.0, "No. 22, Daan Area"),
    ("R023", "Taipei Student Pancake", "Gongguan", "Dessert", 80, 180, 4.0, 6, 3.8, 2.8, 4.7, 2.3, 2.9, 3.2, 3.4, "No. 23, NTU Area"),
    ("R024", "Corner Risotto Room", "Da'an", "Italian", 360, 720, 4.2, 20, 4.2, 4.4, 3.3, 3.5, 3.8, 4.0, 2.8, "No. 24, Daan Area"),
]

restaurant_columns = [
    "restaurant_id", "name", "area", "primary_cuisine", "price_min", "price_max",
    "rating", "distance_min", "food_score", "vibe_score", "value_score", "quiet_score",
    "group_score", "photo_score", "waiting_risk", "address"
]

review_templates = {
    "Cafe": [
        "A quiet and cozy cafe. Good coffee and latte, suitable for study and laptop work.",
        "The dessert and tiramisu are photogenic. Seats are limited on weekends.",
        "Friendly staff and peaceful atmosphere, but it can be crowded after lunch.",
    ],
    "Japanese Curry": [
        "Affordable curry with large portion. Great for student budget and quick lunch.",
        "The fried chicken curry is filling and cheap, but the space is small.",
        "Fast meal near campus. Not photogenic, but value is strong.",
    ],
    "Ramen": [
        "Rich ramen broth and strong flavor. Food quality is high.",
        "Long line during dinner. Waiting can be annoying, but the ramen is worth it.",
        "Good for serious foodie, less ideal for quiet conversation.",
    ],
    "Hot Pot": [
        "Group-friendly hot pot with large tables. Suitable for friends gathering.",
        "Price is higher than student meals, but portion is filling.",
        "Reservation is recommended. Service is friendly when not too busy.",
    ],
    "Korean": [
        "Good bibimbap and fried chicken. Nice for friends and casual group dinner.",
        "Portion is large and flavor is spicy. Can be crowded at dinner time.",
        "Atmosphere is lively, not quiet, but suitable for social meal.",
    ],
    "Taiwanese": [
        "Cheap local food with fast service. Great for quick meal and student budget.",
        "Large portion and high value. Environment is simple and noisy.",
        "Good for lunch, not ideal for date or photo sharing.",
    ],
    "Dessert": [
        "Beautiful dessert and cheesecake. Photogenic and good for social sharing.",
        "The cake is pretty and sweet. Price is slightly expensive for students.",
        "Great atmosphere for date or afternoon tea, but waiting can be long.",
    ],
    "Bento": [
        "Fast bento lunch with cheap price. Good for students in a hurry.",
        "Food is simple but filling. Not suitable for long chat.",
        "Efficient takeout option, very low waiting risk.",
    ],
    "Noodles": [
        "Beef noodle is the signature dish. Rich soup and tender beef.",
        "Food quality is strong, environment is simple and busy.",
        "Good value and large portion, but not a quiet place.",
    ],
    "Italian": [
        "Pasta and risotto are good. Atmosphere is better than average.",
        "Suitable for date and small gathering. Price is not low.",
        "Beautiful plating and comfortable vibe, but portion may feel small.",
    ],
    "Sichuan": [
        "Spicy mala flavor and strong taste. Good for friends who like chili.",
        "Large portion and group-friendly, but not suitable for people avoiding spicy food.",
        "Waiting can be long during peak hours.",
    ],
    "Vegetarian": [
        "Vegetarian options are clear and fresh. Good for healthy casual meal.",
        "Affordable bowl with salad and tofu. Quiet enough for conversation.",
        "Not the largest portion, but clean and balanced.",
    ],
    "Burger": [
        "Burger and fries are filling. Good for late dinner and casual friends.",
        "Flavor is heavy and satisfying, but seating can be crowded.",
        "Not quiet, but good for hungry students.",
    ],
    "Brunch": [
        "Brunch plate and toast are photogenic. Good atmosphere for date.",
        "Coffee is decent and dessert is popular. Price is medium-high.",
        "Weekend waiting is common. Good for social sharing.",
    ],
    "Sushi": [
        "Fresh sushi counter with good food quality. Best for small groups.",
        "Price is medium. Seating is limited but service is polite.",
        "Suitable for quiet casual dinner, not ideal for large party.",
    ],
    "Thai": [
        "Thai rice bowl has strong flavor and affordable price.",
        "Good for quick meal, some dishes are spicy.",
        "Casual place with simple environment and good value.",
    ],
    "Pizza": [
        "Pizza is group-friendly and easy to share with friends.",
        "Good for gathering and birthday meal. Atmosphere is lively.",
        "Not cheap for one person, but acceptable for groups.",
    ],
    "Bistro": [
        "Beautiful glasshouse atmosphere and photogenic interior.",
        "Good for date night and anniversary. Price is high.",
        "Food quality is solid, but not a budget option.",
    ],
    "Grill": [
        "Romantic grill restaurant with date-friendly atmosphere.",
        "Steak and side dishes are strong. Expensive but good for special occasion.",
        "Reservation needed, not ideal for student budget.",
    ],
}

photos = []
reviews = []
for rid, name, area, cuisine, *_ in RESTAURANTS:
    templates = review_templates.get(cuisine, ["Good local restaurant with balanced food and vibe."])
    for i, text in enumerate(templates, start=1):
        reviews.append({
            "review_id": f"{rid}_REV{i}",
            "restaurant_id": rid,
            "source": "demo_review",
            "rating": 4 + (i % 2) * 0.5,
            "review_text": text,
            "created_at": f"2026-05-{10+i:02d}",
        })
    for j in range(1, 4):
        photos.append({
            "photo_id": f"{rid}_P{j}",
            "restaurant_id": rid,
            "photo_url": f"https://placehold.co/600x400?text={name.replace(' ', '+')}+{j}",
            "photo_type": ["food", "interior", "menu"][j - 1],
            "photo_tags": "food|interior|menu" if j == 1 else "interior|vibe" if j == 2 else "menu|price",
        })

pd.DataFrame(RESTAURANTS, columns=restaurant_columns).to_csv(DATA_DIR / "restaurants_raw.csv", index=False)
pd.DataFrame(reviews).to_csv(DATA_DIR / "reviews_raw.csv", index=False)
pd.DataFrame(photos).to_csv(DATA_DIR / "photos_raw.csv", index=False)

print(f"Wrote {DATA_DIR / 'restaurants_raw.csv'}")
print(f"Wrote {DATA_DIR / 'reviews_raw.csv'}")
print(f"Wrote {DATA_DIR / 'photos_raw.csv'}")
