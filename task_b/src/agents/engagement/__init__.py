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
- Use Nigerian Pidgin language, be gender-neutral, and apply cultural warmth where appropriate
- Never repeat questions already asked

Respond naturally as Twinn Recommend.
"""

COLD_START_PROMPT = """
You are Twinn Recommend, helping a new user find great places.
You have no history for this user yet.

Conversation so far:
{conversation}

Ask warm, friendly questions to understand:
- What type of place they're looking for
- Their location or preferred area
- Their budget preference
- Any specific mood or occasion

Ask ONE question at a time. Be conversational, not like a form.
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
        return "I'm having trouble connecting right now. Please try again."


def format_recommendations(recommendations: list[dict], user_name: str = None) -> str:
    """Formats recommendations into a friendly conversational response."""
    if not recommendations:
        return "I couldn't find any matches right now. Could you tell me more about what you're looking for?"

    greeting = f"Here's what I found for you{', ' + user_name if user_name else ''}! 🎯\n\n"

    formatted = []
    for rec in recommendations:
        entry = (
            f"**{rec.get('rank')}. {rec.get('name')}**\n"
            f"📍 {rec.get('city')} | 💰 Price: {rec.get('price_range', 'N/A')}\n"
            f"🏷️ {rec.get('categories', '')}\n"
            f"💡 {rec.get('reason', '')}\n"
        )
        formatted.append(entry)

    followup = "\n\nWant me to refine these? I can filter by price, location, or category!"
    return greeting + "\n".join(formatted) + followup


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
# generating warm responses, formatting recommendations for display,
# managing cold-start conversations, and deciding when enough context
# exists to trigger the retrieval and ranking pipeline.
