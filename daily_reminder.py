import os
#!/usr/bin/env python3
"""
JARVIS Daily Reminder System
Sends Mayur his schedule and motivational push every morning at 4 AM
"""
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "8319501573"
GROQ_KEY = os.getenv("GROQ_KEY_1")

SCHEDULE = """⚡ *JARVIS MORNING BRIEFING*
📅 {date} | Day {day}/20 to Send-up

*TODAY'S WAR PLAN:*

🌅 *4:00-4:50 AM* → Math (close book, recall only)
📐 *4:50-5:40 AM* → Physics (derivations + past papers)
⚗️ *5:40-6:00 AM* → Chemistry (fast read → 3 questions)
🏫 *6:10 AM* → Leave for school

🌆 *4:30-5:00 PM* → Rest + eat
📝 *5:00-6:00 PM* → Homework done fast
🏢 *6:00-7:30 PM* → Nepal Holdings ({company_focus})
🤖 *7:30-8:00 PM* → JARVIS upgrade
🧠 *8:00-8:30 PM* → Theory work
📚 *8:30-9:00 PM* → Past papers ({subject_focus})
😴 *9:00 PM* → SLEEP

*Remember:*
❌ No copying from books
✅ Close book recall only
💪 Nepal is watching. Build."""

COMPANY_FOCUS = {
    0: "Nepal INC + JARVIS upgrades",  # Monday
    1: "Nepal Energy research",
    2: "Nepal Secure + cybersecurity",
    3: "Nepal Space + ARYA station",
    4: "Nepal Motors",
    5: "Full company review",
    6: "Rest + planning",
}

SUBJECT_FOCUS = {
    0: "English + Nepali",
    1: "Computer",
    2: "English + Nepali",
    3: "Computer",
    4: "Full mock test",
    5: "Full mock test",
    6: "Review weak areas",
}

def get_motivation():
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{
                    "role": "user",
                    "content": "Write a 2-sentence brutal honest motivational message for Mayur — a 17-year-old building Nepal's first AI company while preparing for NEB board exams. Make it raw and real, not cliche."
                }],
                "max_tokens": 120,
                "temperature": 0.9
            },
            timeout=20
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return "Every hour you waste today is an hour your competition uses. Move."

def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"},
        timeout=15
    )

def main():
    now = datetime.now()
    weekday = now.weekday()

    # Calculate days since March 21
    start = datetime(2026, 3, 21)
    day_num = min((now - start).days + 1, 20)

    message = SCHEDULE.format(
        date=now.strftime("%B %d, %Y"),
        day=day_num,
        company_focus=COMPANY_FOCUS.get(weekday, "Planning"),
        subject_focus=SUBJECT_FOCUS.get(weekday, "Past papers")
    )

    motivation = get_motivation()
    message += f"\n\n💬 *JARVIS says:*\n_{motivation}_"

    send_telegram(message)
    print(f"✅ Morning briefing sent for {now.strftime('%A %B %d')}")

if __name__ == "__main__":
    main()
