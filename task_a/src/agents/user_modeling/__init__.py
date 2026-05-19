import json
import gzip
from groq import Groq
from supabase import create_client
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATASET_PATH

client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_user_reviews(user_id: str, min_review_length: int = 50) -> list[dict]:
    """Loads a user's quality review history from the Amazon dataset."""
    reviews = []
    try:
        with gzip.open(DATASET_PATH, 'rt', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                if record.get("reviewerID") == user_id:
                    text = record.get("reviewText", "")
                    if len(text) >= min_review_length:
                        reviews.append({
                            "product_id": record.get("asin"),
                            "rating": record.get("overall"),
                            "review_text": text,
                            "summary": record.get("summary", ""),
                            "style": record.get("style", {})
                        })
    except Exception as e:
        print(f"❌ Error loading reviews: {e}")

    if len(reviews) < 3:
        print(f"⚠️ User {user_id} has insufficient quality reviews ({len(reviews)})")
        return []

    return reviews


def get_sample_users(n: int = 5) -> list[str]:
    """Gets a random sample of quality user IDs from the dataset."""
    import random
    user_review_counts = {}

    try:
        with gzip.open(DATASET_PATH, 'rt', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                uid = record.get("reviewerID")
                text = record.get("reviewText", "")
                if len(text) >= 50:
                    user_review_counts[uid] = user_review_counts.get(uid, 0) + 1

        quality_users = [uid for uid, count in user_review_counts.items() if count >= 5]
        sample = random.sample(quality_users, min(n, len(quality_users)))
        print(f"✅ {len(quality_users)} quality users available, returning {len(sample)}")
        return sample

    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return []


def build_user_profile(user_id: str, reviews: list[dict]) -> dict:
    """Uses LLM to analyze user reviews and build behavioral profile."""
    if not reviews:
        return {}

    reviews_text = "\n".join([
        f"Rating: {r['rating']}/5 | Summary: {r['summary']} | Review: {r['review_text'][:200]}"
        for r in reviews
    ])

    avg_rating = sum(r['rating'] for r in reviews) / len(reviews)

    prompt = f"""
Analyze these product reviews written by the same user and extract their behavioral profile.

Reviews:
{reviews_text}

Respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.
All string values must use only single sentences with no special characters or inner quotes.

{{
    "tone": "one of: enthusiastic, critical, balanced, casual, formal",
    "vocabulary_level": "one of: simple, moderate, sophisticated",
    "rating_pattern": "one of: generous, harsh, balanced",
    "topics": "comma separated topics",
    "writing_style": "one sentence description only",
    "common_phrases": "3 to 5 words or short phrases only"
}}
"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON generator. You only output valid JSON. Never include markdown, code blocks, or explanations. Never use double quotes inside string values."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip().replace("```", "").strip()
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                content = content[start:end]
            profile = json.loads(content)
            profile["user_id"] = user_id
            profile["review_count"] = len(reviews)
            profile["avg_rating"] = round(avg_rating, 2)
            return profile
        except Exception as e:
            print(f"❌ Profile building error (attempt {attempt+1}): {e}")
            if attempt == 2:
                return {}


def save_user_profile(profile: dict) -> bool:
    """Saves user profile to Supabase."""
    try:
        supabase.table("task_a_users").upsert({
            "id": profile.get("user_id"),
            "review_count": profile.get("review_count", 0),
            "avg_rating": profile.get("avg_rating", 0),
            "topics": profile.get("topics", ""),
            "tone": profile.get("tone", ""),
            "vocabulary_level": profile.get("vocabulary_level", ""),
            "rating_pattern": profile.get("rating_pattern", "")
        }).execute()
        print(f"✅ Profile saved for user: {profile.get('user_id')}")
        return True
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False


def get_or_build_profile(user_id: str) -> dict:
    """Gets existing profile or builds new one from dataset."""
    result = supabase.table("task_a_users").select("*").eq("id", user_id).execute()
    if result.data:
        print(f"✅ Found existing profile for: {user_id}")
        return result.data[0]

    print(f"🔍 Building profile for: {user_id}")
    reviews = load_user_reviews(user_id)
    if not reviews:
        print(f"❌ No reviews found for user: {user_id}")
        return {}

    profile = build_user_profile(user_id, reviews)
    if profile:
        save_user_profile(profile)
    return profile
