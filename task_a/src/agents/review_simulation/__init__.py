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


def get_product_context(product_id: str, max_reviews: int = 5) -> dict:
    """Fetches product details AND other users' reviews to understand the product."""
    other_reviews = []
    product_info = {}

    try:
        with gzip.open(DATASET_PATH, 'rt', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                if record.get("asin") == product_id:
                    if not product_info:
                        product_info = {
                            "product_id": product_id,
                            "style": record.get("style", {}),
                        }
                    if len(other_reviews) < max_reviews:
                        other_reviews.append({
                            "rating": record.get("overall"),
                            "review": record.get("reviewText", "")[:200],
                            "summary": record.get("summary", "")
                        })
                    if len(other_reviews) >= max_reviews:
                        break
    except Exception as e:
        print(f"❌ Error fetching product context: {e}")

    product_info["other_reviews"] = other_reviews
    product_info["avg_rating"] = (
        sum(r["rating"] for r in other_reviews) / len(other_reviews)
        if other_reviews else 0
    )
    return product_info


def find_product_by_description(description: str) -> dict:
    """
    Finds the closest matching product in the dataset based on a text description.
    Uses LLM to match description against product summaries.
    """
    print(f"🔍 Searching for product matching: {description}")

    sample_products = []
    try:
        with gzip.open(DATASET_PATH, 'rt', encoding='utf-8') as f:
            seen = set()
            for line in f:
                if len(sample_products) >= 100:
                    break
                record = json.loads(line)
                pid = record.get("asin")
                summary = record.get("summary", "")
                style = record.get("style", {})
                if pid and pid not in seen and summary:
                    seen.add(pid)
                    sample_products.append({
                        "product_id": pid,
                        "summary": summary,
                        "style": str(style),
                        "actual_rating": record.get("overall"),
                        "actual_review": record.get("reviewText", "")
                    })
    except Exception as e:
        print(f"❌ Error scanning dataset: {e}")
        return {}

    if not sample_products:
        return {}

    products_text = "\n".join([
        f"{i+1}. ID: {p['product_id']} | Summary: {p['summary']} | Style: {p['style']}"
        for i, p in enumerate(sample_products)
    ])

    prompt = f"""
A user is looking for a product matching this description: "{description}"

Here are available products:
{products_text}

Which product best matches the description? Respond with ONLY the product ID, nothing else.
If no product matches, respond with NONE.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        matched_id = response.choices[0].message.content.strip()

        if len(matched_id) > 20 or " " in matched_id or matched_id == "NONE":
            print(f"⚠️ No clean match found for: {description}")
            return {}

        print(f"✅ Matched product ID: {matched_id}")

        for p in sample_products:
            if p["product_id"] == matched_id:
                return p

        return get_product_context(matched_id)

    except Exception as e:
        print(f"❌ Product matching error: {e}")
        return {}


def get_unseen_products(user_id: str, n: int = 5) -> list[dict]:
    """Gets RANDOM products the user has NOT reviewed for evaluation."""
    import random
    reviewed = set()
    all_candidates = []

    try:
        with gzip.open(DATASET_PATH, 'rt', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                if record.get("reviewerID") == user_id:
                    reviewed.add(record.get("asin"))

        with gzip.open(DATASET_PATH, 'rt', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                pid = record.get("asin")
                text = record.get("reviewText", "")
                if (pid not in reviewed and
                    pid not in [p["product_id"] for p in all_candidates] and
                    len(text) >= 50):
                    all_candidates.append({
                        "product_id": pid,
                        "style": record.get("style", {}),
                        "summary": record.get("summary", ""),
                        "actual_rating": record.get("overall"),
                        "actual_review": text
                    })

        return random.sample(all_candidates, min(n, len(all_candidates)))

    except Exception as e:
        print(f"❌ Error getting unseen products: {e}")
        return []


SIMULATION_PROMPT = """
You are simulating a product review for a specific user based on their behavioral profile.
Your job is to write a review that sounds EXACTLY like this user would write it,
but also responds to what this specific product actually is.

User Profile:
- Tone: {tone}
- Vocabulary Level: {vocabulary_level}
- Rating Pattern: {rating_pattern}
- Topics they care about: {topics}
- Writing Style: {writing_style}
- Common Phrases: {common_phrases}
- Average Rating they give: {avg_rating}/5

Product Context:
- Product ID: {product_id}
- Format/Style: {style}
- Average rating from other users: {product_avg_rating}/5
- What others are saying about this product:
{other_reviews}

Based on this user's profile AND what the product actually is,
simulate what they would write. Make the review specific to this product.

Respond in exact JSON format with no extra text:
{{
    "simulated_rating": a float between 1.0 and 5.0,
    "simulated_review": "the review text in this user's voice, specific to this product",
    "confidence": "high/medium/low"
}}
"""


def simulate_review(user_profile: dict, product: dict) -> dict:
    """Simulates a review for a product based on user profile."""
    product_context = get_product_context(product.get("product_id"))

    other_reviews_text = "\n".join([
        f"- {r['rating']}/5: {r['review']}"
        for r in product_context.get("other_reviews", [])
    ])

    prompt = SIMULATION_PROMPT.format(
        tone=user_profile.get("tone", "balanced"),
        vocabulary_level=user_profile.get("vocabulary_level", "moderate"),
        rating_pattern=user_profile.get("rating_pattern", "balanced"),
        topics=user_profile.get("topics", "general"),
        writing_style=user_profile.get("writing_style", ""),
        common_phrases=user_profile.get("common_phrases", ""),
        avg_rating=user_profile.get("avg_rating", 3.0),
        product_id=product.get("product_id", ""),
        style=product_context.get("style", {}),
        product_avg_rating=round(product_context.get("avg_rating", 0), 2),
        other_reviews=other_reviews_text or "No other reviews available"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
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
        result = json.loads(content)
        result["user_id"] = user_profile.get("user_id") or user_profile.get("id")
        result["product_id"] = product.get("product_id")
        result["product_name"] = str(product.get("style", {}))
        result["actual_rating"] = product.get("actual_rating")
        result["actual_review"] = product.get("actual_review", "")
        return result
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return {}


def save_simulated_review(review: dict) -> bool:
    """Saves simulated review to Supabase."""
    try:
        supabase.table("task_a_reviews").insert({
            "user_id": review.get("user_id"),
            "product_id": review.get("product_id"),
            "product_name": review.get("product_name"),
            "simulated_rating": review.get("simulated_rating"),
            "simulated_review": review.get("simulated_review"),
            "actual_rating": review.get("actual_rating"),
            "actual_review": review.get("actual_review")
        }).execute()
        print(f"✅ Review saved for product: {review.get('product_id')}")
        return True
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False


def simulate_multiple_reviews(user_profile: dict, products: list[dict]) -> list[dict]:
    """Simulates reviews for multiple products."""
    results = []
    for i, product in enumerate(products):
        print(f"🔍 Simulating review {i+1}/{len(products)}...")
        result = simulate_review(user_profile, product)
        if result:
            save_simulated_review(result)
            results.append(result)
    print(f"\n✅ Simulated {len(results)}/{len(products)} reviews")
    return results
