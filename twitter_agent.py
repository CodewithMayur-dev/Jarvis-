import os
#!/usr/bin/env python3
"""
JARVIS Twitter Agent — uses Twitter internal API (no payment needed)
Same method used by many Twitter bots and tools like twikit
"""
import asyncio
import random
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [Twitter] %(message)s')
log = logging.getLogger()

GROQ_KEY   = os.getenv("GROQ_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_KEY_1")

SYSTEM = """You are a Twitter content creator for @shah_mayur22381 — a 17-year-old AI builder from Nepal.
Topics: AI, coding, Nepal tech, building JARVIS (autonomous AI on Android).
Style: Short, punchy, authentic, opinionated. Under 250 chars. Max 2 hashtags."""

CATEGORIES = [
    "ai_news","ai_news","ai_news",
    "coding_tip","coding_tip",
    "nepal_tech","nepal_tech",
    "motivational","motivational",
    "jarvis_update",
]

def llm(prompt):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.9
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_KEY},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 100, "temperature": 0.9}
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return None

def generate_tweet():
    category = random.choice(CATEGORIES)
    prompts = {
        "ai_news":      "Write a punchy tweet with a hot take on a recent AI development.",
        "coding_tip":   "Write a tweet with a practical Python or AI coding tip.",
        "nepal_tech":   "Write a tweet about Nepal's potential in AI and tech.",
        "motivational": "Write a raw real tweet about building something as a young developer.",
        "jarvis_update":"Write a tweet about building JARVIS — autonomous AI on Android.",
    }
    tweet = llm(prompts.get(category, prompts["ai_news"]))
    if tweet and len(tweet) > 275:
        tweet = tweet[:272] + "..."
    log.info(f"Category: {category}")
    return tweet

async def main():
    log.info("🐦 Twitter agent starting...")

    # Install twikit if not installed
    try:
        import twikit
    except ImportError:
        import subprocess
        subprocess.run(["pip", "install", "twikit", "--break-system-packages", "-q"])
        import twikit

    from twikit import Client

    tweet = generate_tweet()
    if not tweet:
        log.error("Failed to generate tweet")
        return

    log.info(f"Tweet: {tweet}")

    client = Client("en-US")

    try:
        # Login
        await client.login(
            auth_info_1="shah_mayur22381",
            auth_info_2="mayurshah.dev@gmail.com",
            password="ZTgM1Yz9x0_Dcmr"
        )
        # Save cookies
        client.save_cookies("/root/jarvis/twitter_cookies.json")
        log.info("Logged in!")
    except Exception as e:
        log.warning(f"Fresh login failed, trying cookies: {e}")
        try:
            client.load_cookies("/root/jarvis/twitter_cookies.json")
        except:
            log.error("No saved cookies either")
            return

    try:
        await client.create_tweet(text=tweet)
        log.info(f"✅ Tweet posted: {tweet[:60]}...")
    except Exception as e:
        log.error(f"❌ Tweet failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
