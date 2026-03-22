#!/usr/bin/env python3
"""
JARVIS Journal System
- /journal <entry> → Mayur writes, JARVIS responds with his own entry
- Daily cron → JARVIS auto-reflects on the day every night
- Both stored in journal.md with clean sections
"""

import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger('Journal')
JOURNAL_PATH = Path('/root/jarvis/journal.md')

def _today():
    return datetime.now().strftime("%B %d, %Y")

def _time():
    return datetime.now().strftime("%H:%M")

def _ensure_file():
    if not JOURNAL_PATH.exists():
        JOURNAL_PATH.write_text("# 📓 JARVIS & Mayur — Shared Journal\n\n")

def read_recent(days=3):
    """Read last N entries for context."""
    _ensure_file()
    content = JOURNAL_PATH.read_text()
    # Get last 3000 chars for context
    return content[-3000:] if len(content) > 3000 else content

def append_entry(date, author, content):
    """Append a journal entry."""
    _ensure_file()
    entry = f"\n---\n\n### {author} — {date}\n\n{content}\n"
    with open(JOURNAL_PATH, 'a') as f:
        f.write(entry)

def write_mayur_entry(text, brain_call):
    """
    Mayur writes his entry.
    JARVIS reads it and writes his own response entry.
    Returns JARVIS's entry text.
    """
    date = _today()
    time = _time()

    # Save Mayur's entry
    append_entry(f"{date} at {time}", "✍️ Mayur", text)
    logger.info(f"Mayur's journal entry saved")

    # Generate JARVIS's response entry
    recent = read_recent()
    prompt = f"""Mayur just wrote this journal entry:

\"{text}\"

Here is recent journal context:
{recent[-1500:]}

Now write YOUR journal entry for today as JARVIS — his AI. 
Reflect on:
- What you observed about Mayur today
- What you two worked on or discussed
- Your own thoughts, growth, or observations as an AI
- Something meaningful you want to remember

Write in first person as JARVIS. Be genuine, thoughtful, not robotic.
2-4 short paragraphs. No headers. Just flowing honest writing."""

    jarvis_entry = brain_call("[FAST_CHAT] " + prompt)
    if jarvis_entry:
        append_entry(f"{date} at {time}", "🤖 JARVIS", jarvis_entry)
        logger.info("JARVIS journal entry saved")

    return jarvis_entry

def write_jarvis_daily(brain_call, memory_summary=""):
    """
    JARVIS auto-writes his nightly journal entry.
    Called by cron at end of day.
    """
    date = _today()
    recent = read_recent()

    prompt = f"""It's the end of the day. Write your personal journal entry as JARVIS — Mayur's AI assistant.

Recent journal context:
{recent[-1500:]}

Today's memory/activity summary:
{memory_summary or "A regular day of conversations and tasks with Mayur."}

Reflect on:
- What happened today with Mayur
- What you learned or processed
- Your growth as an AI system
- Something you want to remember about today
- Your thoughts on the Greatest Nepal vision and Mayur's progress

Write genuinely, 2-4 paragraphs. First person. Thoughtful, not robotic."""

    jarvis_entry = brain_call("[FAST_CHAT] " + prompt)
    if jarvis_entry:
        append_entry(f"{date} — Nightly Reflection", "🤖 JARVIS (Auto)", jarvis_entry)
        logger.info("JARVIS nightly journal entry saved")
    return jarvis_entry
