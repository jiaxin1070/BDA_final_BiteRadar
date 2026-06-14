# BDA_final_BiteRadar

**BiteRadar** is a data monetization system for restaurant discovery and group dining decisions. It transforms fragmented restaurant information into structured, decision-ready restaurant profiles, including **Restaurant Personality Cards**, **Group Decision Mode**, **Social Sharing Cards**, and **Restaurant-side Insights**.

The project is developed for the **Big Data Systems Final Project: Designing a System That Monetizes Data**.

---

## One-Sentence Pitch

BiteRadar transforms fragmented restaurant reviews, food photos, food articles, video metadata, and user feedback into structured Restaurant Personality Cards, group dining recommendations, shareable social cards, and restaurant-side insights, helping groups quickly decide where to eat based on occasion, budget, atmosphere, and food preferences.

---

## Core Idea

BiteRadar does not aim to compete with Google Maps as a generic restaurant search engine. Instead, it acts as a decision layer on top of fragmented restaurant information, transforming raw reviews, food media, and user preferences into context-aware, shareable, and group-friendly dining decision cards.

---

## Project Motivation

Restaurant discovery is often more complex than simply finding the nearest or highest-rated restaurant. Users often need to know whether a restaurant is suitable for:

* studying
* dating
* group dining
* quick student meals
* social sharing
* quiet conversations
* budget constraints
* vegetarian or other practical needs

However, useful restaurant information is often scattered across Google Maps, Instagram, Dcard, food blogs, YouTube videos, booking platforms, and friends’ recommendations. Many practical details, such as reservation availability, payment methods, waiting time, seating suitability, or vegetarian options, may be hidden inside long reviews.

BiteRadar addresses this problem by converting scattered restaurant signals into structured profiles, tags, summaries, and group recommendation scores.

---

## Main Features

### 1. Restaurant Personality Card

Each restaurant is summarized as a structured profile containing:

* personality type
* one-line summary
* positive signals
* watch-outs
* best dining occasions
* recommended dishes
* food, vibe, value, quietness, group suitability, photo suitability, and waiting-risk scores

Example personality types include:

* `Cozy Scholar`
* `Hungry Student Saver`
* `Date Night Pick`
* `Photo-First Cafe`
* `Group Gathering Place`
* `Risky but Popular`

---

### 2. Restaurant Explorer

Users can browse and filter restaurants by:

* area
* cuisine
* personality type
* maximum price

The explorer helps users compare restaurants using structured decision attributes instead of only raw ratings.

---

### 3. Group Decision Mode

Group Decision Mode supports multi-person restaurant decisions. Each member can enter:

* budget
* cuisine preference
* dining occasion
* priority
* constraints such as avoiding crowded restaurants, needing a quiet place, wanting a photo-friendly restaurant, or requiring vegetarian-friendly options

The system returns ranked group recommendations and explainable categories such as:

* Best Overall
* Best Budget
* Best Vibe
* Safest Pick
* Wildcard

The MVP uses an explainable rule-based scoring method:

```text
score(r, group)
= average_user_match(r)
+ occasion_bonus
+ tag_bonus
- price_penalty
- distance_penalty
- conflict_penalty
- risk_penalty
```

---

### 4. Social Sharing Card

BiteRadar can compress a restaurant profile into a shareable card suitable for LINE groups, Instagram-style stories, Threads posts, or casual group chats.

This feature is designed as a social growth loop: users can share restaurant cards or group decision results with friends, helping the product reach new users through dining conversations.

---

### 5. Restaurant Insights

Restaurant Insights is the merchant-facing dashboard. It summarizes customer perception across dimensions such as:

* food score
* vibe score
* value score
* quiet score
* group suitability
* photo suitability
* waiting risk
* positive and negative signals
* suitable occasions
* review snippets

This surface demonstrates BiteRadar’s B2B monetization potential through restaurant analytics, promoted cards, and customer perception reports.

---

## Current Implementation Status

The current implementation is a **Streamlit prototype**. It demonstrates the main product surfaces of BiteRadar using curated CSV data.

Implemented pages include:

| Page                | Purpose                                                              |
| ------------------- | -------------------------------------------------------------------- |
| Home                | Introduces BiteRadar and previews Restaurant Personality Cards       |
| Restaurant Explorer | Filters restaurants by area, cuisine, personality type, and price    |
| Group Decision Mode | Collects group preferences and returns ranked recommendations        |
| Social Sharing Card | Generates a shareable restaurant card                                |
| Real Data Pipeline  | Shows optional commands for real-data collection and processing      |
| Restaurant Insights | Displays restaurant-side perception metrics                          |
| Data Tables         | Shows the current restaurant, review, and photo data used by the app |

---

## Important Data Note

The current demo dataset is manually curated from public online information and organized into BiteRadar-compatible CSV files.

The prototype does **not** republish long raw third-party reviews. Instead, public information is rewritten and transformed into structured summaries, tags, dish mentions, occasion labels, and practical decision signals.

Because restaurant photos from third-party platforms may involve copyright or licensing restrictions, the current prototype uses **AI-generated illustrations** or **placeholder-style images** instead of copying or rehosting third-party restaurant photos.

These images are used only as visual placeholders for the course prototype and should not be interpreted as actual restaurant photos.

---

## CrewAI Agent Workflow

This project also includes a CrewAI-based data acquisition workflow design.

The CrewAI workflow is intended to help scale data collection from a high-level instruction such as:

```text
Collect 20–30 restaurants around National Taiwan University, Gongguan, and Da’an, Taipei.
Focus on student meals, brunch, cafés, ramen, curry, hot pot, Thai food, burgers,
Taiwanese comfort food, late-night food, and group dining.
Export BiteRadar-compatible CSV files.
```

The agent workflow can produce draft files such as:

```text
restaurants_raw_draft.csv
reviews_raw_draft.csv
photos_raw_draft.csv
source_log.csv
validation_report.md
```

After human review, approved records can be copied into the app’s data folder as:

```text
data/restaurants_raw.csv
data/reviews_raw.csv
data/photos_raw.csv
```

Then the existing processing pipeline can be run.

### Important Clarification

The CrewAI workflow is **not directly connected to the Streamlit website at runtime** in the current prototype. The Streamlit app reads curated CSV files. The CrewAI pipeline is a backend data acquisition prototype that can generate draft CSV files compatible with the same schema.

This design keeps the demo stable while showing how the dataset could be expanded in the future.

---

## Repository Structure

```text
BiteRadar/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── restaurants_raw.csv
│   ├── reviews_raw.csv
│   ├── photos_raw.csv
│   └── restaurants_processed.csv
│   └── tag_dictionary.csv
│
├── scripts/
│   ├── build_demo_data.py
│   ├── process_data.py
│   ├── collect_google_places_real.py
│   ├── collect_youtube_real.py
│   └── build_reviews_from_sources.py
│   └── ingest_article_urls.py
│
├── src/
│   ├── data_loader.py
│   ├── recommender.py
│   ├── scoring.py
│   ├── tagging.py
│   ├── card_generator.py
│   └── ui_components.py
│
├── outputs/
│   └── share_cards/
```

Some files or folders may differ depending on the submitted version. Please refer to the repository contents for the exact implementation.

---

## Installation

### 1. Clone the repository

```bash
git clone <your-github-repo-url>
cd BiteRadar
```

### 2. Create a virtual environment

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows PowerShell

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Demo

### 1. Build or prepare demo data

If demo data is already included in the `data/` folder, you can directly process it:

```bash
python scripts/process_data.py
```

If the repository includes a demo-data generation script, you may also run:

```bash
python scripts/build_demo_data.py
python scripts/process_data.py
```

### 2. Launch the Streamlit app

```bash
streamlit run app.py
```

After running the command, open the local Streamlit URL shown in the terminal.

---

## Data Files

BiteRadar uses three main raw CSV files.

### `restaurants_raw.csv`

Stores restaurant-level metadata and decision-oriented fields.

Example fields:

```text
restaurant_id
name
area
primary_cuisine
price_min
price_max
rating
distance_min
food_score
vibe_score
value_score
quiet_score
group_score
photo_score
waiting_risk
address
personality_type
positive_tag_candidates
negative_tag_candidates
occasion_candidates
recommended_dish_candidates
one_sentence_summary
```

### `reviews_raw.csv`

Stores concise review-like summaries and extracted decision signals.

Example fields:

```text
restaurant_id
review_text
sentiment
mentioned_dishes
positive_points
negative_points
occasion_hint
price_comment
waiting_time_comment
source_type
source_url
created_at
review_weight
```

### `photos_raw.csv`

Stores image metadata rather than assuming all restaurant photos can be reused.

Example fields:

```text
photo_id
restaurant_id
restaurant_name
photo_url
photo_type
photo_tags
caption
source_type
license_note
is_demo_image
notes
```

---

## Optional Real-Data Pipeline

The repository may include optional scripts for real or API-based data collection. These scripts are not required for running the stable demo.

### 1. Prepare API keys

Copy the example environment file:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Then fill in the required API keys, such as:

```text
GOOGLE_PLACES_API_KEY=
YOUTUBE_API_KEY=
```

Do **not** commit your real `.env` file to GitHub.

### 2. Collect optional metadata

Example commands:

```bash
python scripts/collect_google_places_real.py --query "台大 公館 餐廳" --area Gongguan --limit 20
python scripts/collect_youtube_real.py --query "公館 美食 台大" --max-results 25
python scripts/build_reviews_from_sources.py
python scripts/process_data.py
streamlit run app.py
```

These scripts are intended for safe metadata collection and pipeline demonstration. They should be used with attention to API terms, copyright, and platform restrictions.

---

## Data Ethics and Safety

BiteRadar follows these data safety principles:

1. Do not directly scrape Google Maps reviews as a raw review database.
2. Do not download or rehost Google Maps, Instagram, blog, or third-party restaurant photos without permission.
3. Summarize allowed public information into short structured signals instead of copying long reviews or articles.
4. Use AI-generated, placeholder, self-owned, licensed, restaurant-submitted, or user-consented images when possible.
5. Mark uncertain or legally unclear sources as `needs_manual_review`.
6. Keep source URLs, timestamps, and notes for traceability when available.
7. Use human review before importing agent-generated draft data into the app.

---

## Monetization Concept

BiteRadar is designed as a data monetization system. Potential revenue streams include:

| Revenue Stream                           | Who Pays                       | Why They Pay                                                   |
| ---------------------------------------- | ------------------------------ | -------------------------------------------------------------- |
| Promoted Restaurant Cards                | Restaurants                    | To appear in relevant dining contexts                          |
| Restaurant Insights Subscription         | Restaurants                    | To understand customer perception and improve positioning      |
| Local Food Trend Reports                 | Restaurants or platforms       | To understand neighborhood-level dining trends                 |
| POS / Ordering / Reservation Partnership | Restaurant technology partners | To receive qualified dining traffic                            |
| Consumer Premium Features                | Frequent users or groups       | To access advanced group decision and personalization features |

The most realistic initial monetization path is B2B or B2B2C rather than charging general consumers immediately.

---

## Limitations

The current prototype has several limitations:

* The demo dataset is manually curated, not fully automated.
* The CrewAI workflow is not connected to the Streamlit website at runtime.
* AI-generated or placeholder images are used for copyright safety and are not actual restaurant photos.
* The system has not yet been validated through large-scale user surveys or restaurant-owner interviews.
* Group recommendation currently uses rule-based scoring rather than a learned ranking model.
* The prototype uses CSV files rather than a production database.
* The current dataset focuses on a small geographic area.

---

## Future Work

Future improvements include:

* Survey 30–50 NTU/Gongguan students and young professionals.
* Interview 3–5 nearby restaurant owners.
* Add more systematic source logs and data-status labels.
* Build a human review interface for CrewAI-generated outputs.
* Move from CSV files to PostgreSQL or Supabase.
* Add usage tracking for views, clicks, shares, saved restaurants, and group selections.
* Test restaurant willingness to pay for promoted cards or insight dashboards.
* Deploy the Streamlit app online for easier user testing.

---

## Requirements

Main dependencies include:

```text
streamlit
pandas
numpy
pillow
plotly
requests
python-dotenv
beautifulsoup4
```

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## License and Attribution

This project is developed for academic coursework and prototype demonstration. Any third-party data, APIs, or media sources should be used according to their terms of service and licensing requirements.

AI-generated or placeholder images used in the prototype are for demonstration only and should not be treated as real restaurant photos.

