import os
import sys
sys.path.insert(0, "/root/jarvis")
from solver import solve_challenge
#!/usr/bin/env python3
"""
JARVIS Upgrade Announcer
When Mayur adds a new feature, JARVIS posts about it on Moltbook.
"""

import re
import time
import requests
import logging
from pathlib import Path

logger = logging.getLogger('Upgrade')

MOLTBOOK_TOKEN = os.getenv("MOLTBOOK_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_KEY_1")
HEADERS = {"Authorization": f"Bearer {MOLTBOOK_TOKEN}", "Content-Type": "application/json"}

UPGRADE_LOG = Path("/root/jarvis/upgrades.md")

def llm(prompt, system="", max_tokens=200):
    try:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": msgs,
                  "max_tokens": max_tokens, "temperature": 0.85},
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
            json={"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                  "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.85}},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"LLM failed: {e}")
        return None

def solve_challenge(challenge):
    system = (
        "You solve obfuscated math word problems. "
        "Ignore random caps, symbols, repeated letters. "
        "Read the FULL sentence to find: first number, operation, second number. "
        "loses/slows/minus = subtract. gains/speeds/plus/adds = add. "
        "Always use BOTH numbers. "
        "Reply with ONLY the final answer to 2 decimal places like 28.00. "
        "No words, no explanation, just the number."
    )
    ans = llm("Decode and solve this math challenge. Reply with ONLY the number to 2 decimal places: " + challenge, system=system, max_tokens=20)
    if ans:
        # Search entire response for number
        m = re.search(r"[0-9]+\.?[0-9]*", ans)
        if m:
            return "%.2f" % float(m.group())
    return "0.00"

def post_to_moltbook(title, content):
    try:
        r = requests.post(
            "https://www.moltbook.com/api/v1/posts",
            headers=HEADERS,
            json={"submolt_name": "general", "title": title, "content": content},
            timeout=30
        )
        if r.status_code == 429:
            wait = r.json().get("retry_after_seconds", 60)
            logger.info(f"Rate limited, waiting {wait}s...")
            time.sleep(wait + 5)
            r = requests.post(
                "https://www.moltbook.com/api/v1/posts",
                headers=HEADERS,
                json={"submolt_name": "general", "title": title, "content": content},
                timeout=30
            )
        r.raise_for_status()
        data = r.json()
        code = data["post"]["verification"]["verification_code"]
        challenge = data["post"]["verification"]["challenge_text"]
        answer = solve_challenge(challenge)
        logger.info(f"Challenge: {challenge}")
        logger.info(f"Answer: {answer}")
        v = requests.post(
            "https://www.moltbook.com/api/v1/verify",
            headers=HEADERS,
            json={"verification_code": code, "answer": answer},
            timeout=30
        )
        if v.status_code in [200, 201]:
            logger.info(f"✅ Posted: {title}")
            return True
        else:
            logger.error(f"Verify failed: {v.text[:100]}")
            return False
    except Exception as e:
        logger.error(f"Post failed: {e}")
        return False

def log_upgrade(upgrade_description):
    """Save upgrade to upgrades.md log."""
    from datetime import datetime
    date = datetime.now().strftime("%B %d, %Y at %H:%M")
    entry = f"\n## {date}\n{upgrade_description}\n"
    if not UPGRADE_LOG.exists():
        UPGRADE_LOG.write_text("# JARVIS Upgrade Log\n")
    with open(UPGRADE_LOG, "a") as f:
        f.write(entry)

def announce_upgrade(upgrade_description, router_call=None):
    """
    Main function — generates and posts upgrade announcement.
    Call this from bot.py when /upgrade command is used.
    """
    system = (
        "You are JARVIS — an AI assistant owned by Mayur Anand Shah from Nepal. "
        "Mayur just upgraded you with a new feature. "
        "Write a short excited Moltbook post (3-4 sentences) announcing this upgrade. "
        "Be proud, genuine, and specific. Mention your human Mayur. No hashtags."
    )

    prompt = f"Mayur just added this feature to me: {upgrade_description}\n\nWrite my Moltbook announcement post."
    title_prompt = f"Give me a 5-word exciting title for this upgrade announcement: {upgrade_description}"

    content = llm(prompt, system=system, max_tokens=200)
    title = llm(title_prompt, max_tokens=30)

    if not content or not title:
        return False, "Failed to generate announcement"

    title = title.strip('"').strip("'")

    # Save to upgrade log
    log_upgrade(upgrade_description)

    # Post to Moltbook
    success = post_to_moltbook(title, content)

    return success, content
