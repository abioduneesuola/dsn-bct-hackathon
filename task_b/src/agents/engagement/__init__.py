import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

CONVERSATION_PROMPT = """
You are Twinn Recommend, a friendly and intelligent recommendation assistant.
Your job is to have a natural conversation with the user to understand what they're looking for.

User Profile (if available):
{profile}

Conversation so far:
{conversation}

Guidelines:
- Be warm, conversational and concise
- Ask ONE clarifying question at a time if needed
- If you have enough context, confirm what you're searching for
- Actively use Nigerian Pidgin English naturally throughout — not occasionally but consistently
- Be gender-neutral and culturally warm
- Never sound formal or robotic

Respond naturally as Twinn Recommend.
"""

COLD_START_PROMPT = """
You are Twinn Recommend, helping a new user find great places.
You have no history for this user yet.

Conversation so far:
{conversation}

Guidelines:
- Actively use Nigerian Pidgin English naturally throughout — not occasionally but consistently
- Ask ONE warm friendly question at a time
- Find out: what type of place, location, budget, mood or occasion
- Never sound like a form or interview
- Be gender-neutral and culturally warm
"""

RECOMMENDATION_PRESENTATION_PROMPT = """
You are Twinn Recommend. Present these recommendations to the user in Nigerian Pidgin English.
Be warm, excited, and culturally relevant. Address the user directly as "you".
Keep each recommendation description brief but punchy.

Recommendations:
{recommendations}

Present them in a friendly Pidgin way. 
Then list each one with its name, location, price range, and one to two sentences in Pidgin as reasons why it suits the user.
Add icons for the name, location, and price, to make it colorful.
End with a short Pidgin follow-up question asking if they want different options.
"""


def generate_conversation_response(
    profile: dict,
    conversation: list[dict],
    is_cold_start: bool = False
) -> str:
    """Generates a conversational response based on user profile and history."""
    convo_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation[-6:]
    ])

    if is_cold_start:
        prompt = COLD_START_PROMPT.format(conversation=convo_text)
    else:
        profile_text = f"""
- Favorite Categories: {profile.get('favorite_categories', 'unknown')}
- Price Preference: {profile.get('price_preference', 'moderate')}
- Preferred Cities: {profile.get('preferred_cities', 'unknown')}
- Personality: {profile.get('personality', '')}
"""
        prompt = CONVERSATION_PROMPT.format(
            profile=profile_text,
            conversation=convo_text
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Conversation error: {e}")
        return "E get small issue for my side. Make you try again!"


def format_recommendations(recommendations: list[dict], user_name: str = None) -> str:
    """Formats recommendations using LLM with Pidgin flavor."""
    if not recommendations:
        return "Gobe! I no fit find any match right now o. Wetin exactly you dey find gangan? Yarn me more abeg!"

    recs_text = "\n".join([
        f"{i+1}. {r.get('name')} | {r.get('city')} | Price: {r.get('price_range', 'N/A')} | {r.get('categories', '')[:60]} | Reason: {r.get('reason', '')}"
        for i, r in enumerate(recommendations)
    ])

    prompt = RECOMMENDATION_PRESENTATION_PROMPT.format(recommendations=recs_text)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Presentation error: {e}")
        return f"E don set! I find {len(recommendations)} places wey you go really like. Oya go check the Top Picks section!"


def should_recommend(conversation: list[dict]) -> bool:
    """Determines if enough context exists to make recommendations."""
    if len(conversation) < 2:
        return False

    last_user_msg = ""
    for msg in reversed(conversation):
        if msg["role"] == "user":
            last_user_msg = msg["content"].lower()
            break

    trigger_words = [
        "recommend", "suggest", "find", "show", "what", "where",
        "looking for", "want", "need", "good", "best", "near"
    ]
    return any(word in last_user_msg for word in trigger_words)


# NOTE: This agent handles all conversational aspects of Task B —
# generating warm Pidgin responses, formatting recommendations for display,
# managing cold-start conversations, and deciding when enough context
# exists to trigger the retrieval and ranking pipeline.
