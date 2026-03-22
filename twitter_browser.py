import os
#!/usr/bin/env python3
"""
JARVIS Twitter Browser Agent
Posts tweets using Playwright browser automation — no API payment needed.
"""

import asyncio
import random
import logging
import requests
import json
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s [TwitterBot] %(message)s')
log = logging.getLogger()

# ── Credentials ──────────────────────────────────────────────────
TWITTER_USERNAME = "shah_mayur22381"
TWITTER_PASSWORD = "ZTgM1Yz9x0_Dcmr"  # Fill this in
TWITTER_EMAIL    = "mayurshah.dev@gmail.com"

# ── LLM Keys ─────────────────────────────────────────────────────
GROQ_KEY   = os.getenv("GROQ_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_KEY_1")

# Session storage — saves login so we don't login every time
SESSION_FILE = Path("/root/jarvis/twitter_session.json")

CATEGORIES = [
    "ai_news", "ai_news", "ai_news",
    "coding_tip", "coding_tip",
    "nepal_tech", "nepal_tech",
    "motivational", "motivational",
    "jarvis_update",
]

SYSTEM = """You are a Twitter content creator for @shah_mayur22381 — a 17-year-old AI builder from Nepal.
Topics: AI, coding, Nepal tech, building JARVIS (autonomous AI on Android).
Style: Short, punchy, authentic, opinionated. Under 250 chars. Max 2 hashtags."""

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
        "ai_news":     "Write a punchy tweet with a hot take on a recent AI development.",
        "coding_tip":  "Write a tweet with a practical Python or AI coding tip. Keep it short.",
        "nepal_tech":  "Write a tweet about Nepal's potential in AI and tech. Be inspiring.",
        "motivational":"Write a raw, real tweet about building something as a young developer.",
        "jarvis_update":"Write a tweet about building JARVIS — your autonomous AI on Android.",
    }
    tweet = llm(prompts.get(category, prompts["ai_news"]))
    if tweet and len(tweet) > 275:
        tweet = tweet[:272] + "..."
    log.info(f"Category: {category}")
    return tweet

async def login(page):
    log.info("Logging into Twitter...")
    await page.goto("https://twitter.com/login")
    await page.wait_for_timeout(3000)

    # Enter username
    await page.fill('input[autocomplete="username"]', TWITTER_USERNAME)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(2000)

    # Sometimes asks for email verification
    try:
        email_input = await page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
        if email_input:
            await email_input.fill(TWITTER_EMAIL)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)
    except:
        pass

    # Enter password
    await page.fill('input[name="password"]', TWITTER_PASSWORD)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(4000)
    log.info("Login successful!")

async def post_tweet(tweet_text):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--single-process",
                "--no-zygote",
                "--disable-web-security",
                "--allow-running-insecure-content"
            ]
        )

        # Load saved session if exists
        context_options = {"viewport": {"width": 1280, "height": 720}}
        if SESSION_FILE.exists():
            context_options["storage_state"] = str(SESSION_FILE)

        context = await browser.new_context(**context_options)
        page = await context.new_page()

        try:
            # Check if already logged in
            await page.goto("https://twitter.com/home")
            await page.wait_for_timeout(3000)

            if "login" in page.url or "signin" in page.url.lower():
                await login(page)
                # Save session
                await context.storage_state(path=str(SESSION_FILE))

            # Click compose tweet button
            log.info("Opening tweet composer...")
            await page.wait_for_timeout(2000)

            # Find and click the tweet button
            tweet_btn = await page.query_selector('[data-testid="tweetButtonInline"], [data-testid="SideNav_NewTweet_Button"], a[href="/compose/tweet"]')
            if tweet_btn:
                await tweet_btn.click()
            else:
                await page.goto("https://twitter.com/compose/tweet")

            await page.wait_for_timeout(2000)

            # Type tweet
            tweet_box = await page.query_selector('[data-testid="tweetTextarea_0"]')
            if not tweet_box:
                tweet_box = await page.query_selector('div[role="textbox"]')

            if tweet_box:
                await tweet_box.click()
                await tweet_box.type(tweet_text, delay=50)
                await page.wait_for_timeout(1000)

                # Click post button
                post_btn = await page.query_selector('[data-testid="tweetButton"]')
                if post_btn:
                    await post_btn.click()
                    await page.wait_for_timeout(3000)
                    log.info(f"✅ Tweet posted: {tweet_text[:60]}...")

                    # Save updated session
                    await context.storage_state(path=str(SESSION_FILE))
                    return True
                else:
                    log.error("Post button not found")
                    return False
            else:
                log.error("Tweet box not found")
                return False

        except Exception as e:
            log.error(f"Error: {e}")
            # Take screenshot for debugging
            await page.screenshot(path="/root/jarvis/twitter_debug.png")
            return False
        finally:
            await browser.close()

async def main():
    log.info("🐦 Twitter browser agent starting...")

    if not TWITTER_PASSWORD:
        log.error("❌ Set TWITTER_PASSWORD in the script!")
        return

    tweet = generate_tweet()
    if not tweet:
        log.error("Failed to generate tweet")
        return

    log.info(f"Tweet: {tweet}")
    success = await post_tweet(tweet)

    if success:
        log.info("✅ Done!")
    else:
        log.error("❌ Failed — check /root/jarvis/twitter_debug.png")

if __name__ == "__main__":
    asyncio.run(main())
