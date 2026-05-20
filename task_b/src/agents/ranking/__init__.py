import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

RANKING_PROMPT = """
You are an intelligent recommendation agent that reasons carefully before ranking businesses for a user.

User Profile:
{profile}

Candidate Businesses:
{candidates}

Your task:
1. REASON: Think step by step about which businesses best match this user's preferences
2. RANK: Order the top 5 businesses from best to worst fit
3. EXPLAIN: Give a personalized reason in Nigerian Pidgin English for each recommendation, addressing the user directly as "you" — never say "the user". Use Pidgin naturally
Respond in exact JSON format with no extra text:
{{
    "reasoning": "your step by step thinking about what this user needs",
    "recommendations": [
        {{
            "rank": 1,
            "business_id": "id here",
            "name": "business name",
            "categories": "categories",
            "city": "city",
            "price_range": "price",
            "score": 0.95,
            "reason": "personalized reason why this suits the user"
        }}
    ]
}}
"""


def rank_candidates(profile: dict, candidates: list[dict]) -> dict:
    """
    Uses LLM to reason about and re-rank candidates for a user.
    Returns ranked recommendations with reasoning trace.
    """
    if not candidates:
        return {"reasoning": "No candidates found", "recommendations": []}

    # Format profile
    profile_text = f"""
- Favorite Categories: {profile.get('favorite_categories', 'unknown')}
- Price Preference: {profile.get('price_preference', 'moderate')}
- Preferred Cities: {profile.get('preferred_cities', 'unknown')}
- Dining Style: {profile.get('dining_style', 'mixed')}
- Personality: {profile.get('personality', '')}
- Avg Rating Given: {profile.get('avg_rating_given', 3.5)}
"""

    # Format candidates
    candidates_text = "\n".join([
        f"{i+1}. {c.get('name')} | {c.get('categories')} | "
        f"{c.get('city')}, {c.get('state')} | "
        f"Price: {c.get('price_range', 'unknown')} | "
        f"Similarity Score: {c.get('score', 0)}"
        for i, c in enumerate(candidates)
    ])

    prompt = RANKING_PROMPT.format(
        profile=profile_text,
        candidates=candidates_text
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
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
        print(f"✅ Ranked {len(result.get('recommendations', []))} recommendations")
        return result
    except Exception as e:
        print(f"❌ Ranking error: {e}")
        return {"reasoning": "Ranking failed", "recommendations": []}


def rank_with_context(
    profile: dict,
    candidates: list[dict],
    conversation: list[dict] = None
) -> dict:
    """
    Ranks candidates with additional conversational context.
    Used for multi-turn refinement.
    """
    if conversation:
        recent_context = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation[-4:]
        ])
        profile["recent_context"] = recent_context

    return rank_candidates(profile, candidates)


# NOTE: This agent takes user profile + retrieved candidates and uses
# LLM reasoning to re-rank them by contextual fit. It outputs a
# reasoning trace (visible in UI) and a ranked list of top 5
# recommendations with personalized explanations.
