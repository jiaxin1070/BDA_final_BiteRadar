from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_photos, load_restaurants, load_reviews
from src.recommender import category_picks, recommend_restaurants
from src.scoring import MemberPreference
from src.ui_components import inject_global_css, render_personality_card, render_social_preview

st.set_page_config(
    page_title="BiteRadar",
    page_icon="🍽️",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
inject_global_css()


@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_restaurants(processed=True), load_reviews(), load_photos()


def restaurant_card(row: pd.Series, photos: pd.DataFrame, show_button: bool = True, key_prefix: str = "card") -> None:
    render_personality_card(row, photos=photos, show_generate_button=show_button, key_prefix=key_prefix)


def home_page(restaurants: pd.DataFrame, photos: pd.DataFrame) -> None:
    st.title("🍽️ BiteRadar")
    st.subheader("A social restaurant intelligence app with Personality Cards and Group Decision Mode")
    st.write(
        "BiteRadar turns fragmented restaurant reviews, food photos, and online food media "
        "into structured restaurant profiles. The upgraded MVP emphasizes two product surfaces: "
        "a polished in-app Restaurant Personality Card and a downloadable social sharing card."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Restaurants", len(restaurants))
    c2.metric("Areas", restaurants["area"].nunique())
    c3.metric("Personality Types", restaurants["personality_type"].nunique())
    c4.metric("Avg Rating", f"{restaurants['rating'].mean():.2f}")

    st.markdown("### What makes this different")
    st.markdown(
        """
        1. **Restaurant Personality Card**: not just stars; it explains the restaurant's vibe, strengths, risks, and suitable occasions.  
        2. **Group Decision Mode**: aggregates budgets, cuisine preferences, social contexts, and constraints from multiple people.  
        3. **Shareable Social Card**: creates an image card for LINE / Instagram-style sharing.  
        4. **Restaurant-side Insights**: turns review signals into merchant-facing analytics.  
        """
    )

    st.markdown("### Preview")
    preview = restaurants.iloc[0]
    restaurant_card(preview, photos, show_button=True, key_prefix="home")

    st.markdown("### Data note")
    st.info(
        "For course safety, the default MVP can use placeholder, self-owned, restaurant-submitted, or licensed images. "
        "If Google imagery is used, prefer official Google APIs and show required attribution instead of manually downloading and rehosting images."
    )


def explorer_page(restaurants: pd.DataFrame, photos: pd.DataFrame) -> None:
    st.title("🔎 Restaurant Explorer")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        area = st.selectbox("Area", ["Any"] + sorted(restaurants["area"].unique().tolist()))
    with col2:
        cuisine = st.selectbox("Cuisine", ["Any"] + sorted(restaurants["primary_cuisine"].unique().tolist()))
    with col3:
        personality = st.selectbox("Personality", ["Any"] + sorted(restaurants["personality_type"].unique().tolist()))
    with col4:
        max_price = st.slider("Max price", 100, 1200, 500, step=50)

    df = restaurants.copy()
    if area != "Any":
        df = df[df["area"] == area]
    if cuisine != "Any":
        df = df[df["primary_cuisine"] == cuisine]
    if personality != "Any":
        df = df[df["personality_type"] == personality]
    df = df[df["price_min"] <= max_price]
    df = df.sort_values(by=["rating", "food_score"], ascending=False)

    st.write(f"Found **{len(df)}** restaurants.")
    for _, row in df.iterrows():
        restaurant_card(row, photos, key_prefix="explore")
        st.divider()


def group_decision_page(restaurants: pd.DataFrame, photos: pd.DataFrame) -> None:
    st.title("👥 Group Decision Mode")
    st.write(
        "Create a group dining task, enter each person's preference, and BiteRadar returns "
        "a group match score with explainable recommendation categories."
    )

    with st.sidebar:
        st.header("Group setup")
        area = st.selectbox("Search area", ["Any"] + sorted(restaurants["area"].unique().tolist()), key="group_area")
        n_members = st.slider("Number of people", 1, 6, 3)
        top_k = st.slider("Number of results", 3, 15, 8)

    cuisine_options = ["Any"] + sorted(restaurants["primary_cuisine"].unique().tolist())
    occasion_options = [
        "Any", "study", "date", "group gathering", "quick meal", "student budget", "social sharing", "casual meal"
    ]
    priority_options = ["Balanced", "Price", "Food", "Vibe", "Distance", "No Queue", "Photo"]

    st.markdown("### Member preferences")
    preferences: list[MemberPreference] = []
    for i in range(n_members):
        with st.expander(f"Person {i + 1}", expanded=(i < 3)):
            c1, c2, c3, c4 = st.columns(4)
            name = c1.text_input("Name", value=f"P{i + 1}", key=f"name_{i}")
            budget = c2.slider("Budget", 100, 1200, 350, step=50, key=f"budget_{i}")
            cuisine = c3.selectbox("Cuisine", cuisine_options, key=f"cuisine_{i}")
            occasion = c4.selectbox("Occasion", occasion_options, key=f"occasion_{i}")
            c5, c6, c7, c8 = st.columns(4)
            priority = c5.selectbox("Priority", priority_options, key=f"priority_{i}")
            avoid_crowded = c6.checkbox("Avoid crowded", key=f"crowded_{i}")
            needs_quiet = c7.checkbox("Needs quiet", key=f"quiet_{i}")
            wants_photo = c8.checkbox("Wants photo spot", key=f"photo_{i}")
            vegetarian = st.checkbox("Vegetarian-friendly needed", key=f"veg_{i}")
            preferences.append(
                MemberPreference(
                    name=name,
                    budget=budget,
                    cuisine=cuisine,
                    occasion=occasion,
                    priority=priority,
                    avoid_crowded=avoid_crowded,
                    needs_quiet=needs_quiet,
                    wants_photo_spot=wants_photo,
                    vegetarian_friendly=vegetarian,
                )
            )

    if st.button("Find group recommendations", type="primary"):
        scored = recommend_restaurants(restaurants, preferences, area=area, top_k=top_k)
        if scored.empty:
            st.warning("No restaurants found. Try another area or preference setting.")
            return
        st.session_state["last_scored"] = scored
        st.session_state["last_preferences"] = preferences

    scored = st.session_state.get("last_scored")
    if isinstance(scored, pd.DataFrame) and not scored.empty:
        st.markdown("### Recommendation categories")
        picks = category_picks(scored)
        cols = st.columns(len(picks))
        for col, (label, row) in zip(cols, picks.items()):
            with col:
                st.metric(label, f"{row['group_match_score']:.0f}%")
                st.caption(row["name"])

        st.markdown("### Ranked restaurants")
        for _, row in scored.iterrows():
            restaurant_card(row, photos, key_prefix="group")
            st.divider()


def social_card_page(restaurants: pd.DataFrame, photos: pd.DataFrame) -> None:
    st.title("📲 Social Sharing Card")
    st.write(
        "This page demonstrates the outward-facing growth loop: a restaurant can be compressed into a beautiful, shareable card. "
        "It is designed for screenshots, LINE group chats, and Instagram-style sharing."
    )
    selected = st.selectbox("Choose a restaurant", restaurants["name"].tolist(), key="social_select")
    row = restaurants[restaurants["name"] == selected].iloc[0]
    render_social_preview(row, photos)


def real_data_page() -> None:
    st.title("🛰️ Real Data Pipeline")
    st.write(
        "The repository can run as a synthetic MVP, but it also includes optional collectors "
        "for official/API-based real data. Run these commands in VSCode Terminal, not inside this page."
    )
    st.warning(
        "Avoid unauthorized scraping. Prefer official APIs, user surveys, restaurant-submitted photos, "
        "self-taken photos, and licensed data. Do not publish raw third-party reviews unless the provider terms allow it."
    )
    st.markdown("### 1. Prepare API keys")
    st.code("copy .env.example .env\n# then fill GOOGLE_PLACES_API_KEY and/or YOUTUBE_API_KEY", language="bash")
    st.markdown("### 2. Collect restaurant metadata")
    st.code('python scripts/collect_google_places_real.py --query "台大 公館 餐廳" --area Gongguan --limit 20', language="bash")
    st.markdown("### 3. Collect media metadata")
    st.code('python scripts/collect_youtube_real.py --query "公館 美食 台大" --max-results 25', language="bash")
    st.markdown("### 4. Build review/media snippets and processed profiles")
    st.code("python scripts/build_reviews_from_sources.py\npython scripts/process_data.py\nstreamlit run app.py", language="bash")


def analytics_page(restaurants: pd.DataFrame, reviews: pd.DataFrame, photos: pd.DataFrame) -> None:
    st.title("📊 Restaurant-side Insights")
    st.write(
        "This page demonstrates the B2B monetization angle: restaurants can see how customers "
        "perceive them, what positive/negative tags dominate, and which dining occasions they fit."
    )

    selected = st.selectbox("Choose a restaurant", restaurants["name"].tolist())
    row = restaurants[restaurants["name"] == selected].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rating", f"{row['rating']:.1f}")
    c2.metric("Food", f"{row['food_score']:.1f}")
    c3.metric("Vibe", f"{row['vibe_score']:.1f}")
    c4.metric("Waiting risk", f"{row['waiting_risk']:.1f}")

    restaurant_card(row, photos, show_button=False, key_prefix="insight")

    radar_df = pd.DataFrame({
        "dimension": ["food", "vibe", "value", "quiet", "group", "photo", "low waiting risk"],
        "score": [
            row["food_score"], row["vibe_score"], row["value_score"], row["quiet_score"],
            row["group_score"], row["photo_score"], 5 - row["waiting_risk"],
        ]
    })
    fig = px.bar(radar_df, x="dimension", y="score", range_y=[0, 5], title="Perception dimensions")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Demo review snippets")
    subset = reviews[reviews["restaurant_id"] == row["restaurant_id"]]
    if subset.empty:
        st.info("No review snippets for this restaurant yet.")
    else:
        for _, review in subset.iterrows():
            st.write(f"- {review['review_text']}")


def data_page(restaurants: pd.DataFrame, reviews: pd.DataFrame, photos: pd.DataFrame) -> None:
    st.title("🧱 Data Tables")
    st.write("Use this page to inspect the data currently used by the MVP. It may be demo data or real API/survey data after you run the pipeline.")
    st.markdown("### Processed restaurant profiles")
    st.dataframe(restaurants, use_container_width=True)
    st.markdown("### Raw review snippets")
    st.dataframe(reviews, use_container_width=True)
    st.markdown("### Photo metadata")
    st.dataframe(photos, use_container_width=True)


def main() -> None:
    try:
        restaurants, reviews, photos = get_data()
    except Exception as e:
        st.error(str(e))
        st.stop()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Home",
            "Restaurant Explorer",
            "Group Decision Mode",
            "Social Sharing Card",
            "Real Data Pipeline",
            "Restaurant Insights",
            "Data Tables",
        ],
    )

    if page == "Home":
        home_page(restaurants, photos)
    elif page == "Restaurant Explorer":
        explorer_page(restaurants, photos)
    elif page == "Group Decision Mode":
        group_decision_page(restaurants, photos)
    elif page == "Social Sharing Card":
        social_card_page(restaurants, photos)
    elif page == "Real Data Pipeline":
        real_data_page()
    elif page == "Restaurant Insights":
        analytics_page(restaurants, reviews, photos)
    elif page == "Data Tables":
        data_page(restaurants, reviews, photos)


if __name__ == "__main__":
    main()
