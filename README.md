# ⚡ JARVIS — Just A Rather Very Intelligent System

> Built by **Mayur Anand Shah** | [Nepal INC](https://github.com/CodewithMayur-dev)

JARVIS is a fully autonomous AI assistant running on Android via Telegram. It uses multiple LLM providers with smart routing, autonomous Moltbook posting, shared journaling, file automation, and a REST API for iOS/Web integration.

---

## 🚀 Features

- **Multi-Provider LLM** — Gemini (12 keys) + Groq + DeepSeek with auto-fallback
- **Smart Task Routing** — coding → DeepSeek, fast chat → Groq, creative → Gemini
- **Telegram Bot** — full conversational AI on your phone
- **Moltbook Agent** — posts autonomously every 4 hours with AI-generated content
- **Shared Journal** — you and JARVIS write together every day
- **Cowork Agent** — autonomous file reading, writing, and task automation
- **REST API** — connect iOS, Android, or Web apps to JARVIS
- **Daily Briefing** — sends your schedule every morning at 4 AM
- **Upgrade Announcer** — posts every new feature to Moltbook automatically

---

## 📋 Requirements

- Android phone with Termux
- Ubuntu via proot-distro
- Python 3.10+
- Telegram Bot Token
- At least 1 API key (Gemini is free)

---

## ⚙️ Setup

**1. Install Termux + Ubuntu:**
```bash
pkg install proot-distro
proot-distro install ubuntu
proot-distro login ubuntu
2. Clone the repo:
git clone https://github.com/CodewithMayur-dev/jarvis
cd jarvis
3. Install dependencies:
pip install requests aiohttp python-telegram-bot fastapi uvicorn twikit
4. Configure:
cp config.example.json config.json
nano config.json  # Add your API keys
5. Run JARVIS:
python main.py
6. Run the API (optional):
uvicorn api:app --host 0.0.0.0 --port 8000
🔑 Getting Free API Keys
Provider
Link
Free Limit
Gemini
aistudio.google.com/apikey
15 RPM / 1500 day
Groq
console.groq.com/keys
30 RPM / 14400 day
DeepSeek
platform.deepseek.com
$5 free credits
📡 API Endpoints
GET  /          → Info
GET  /health    → Health check
GET  /status    → Provider status
POST /chat      → Chat with JARVIS
POST /journal   → Write journal entry
GET  /journal/read → Read journal
Authentication: Add header x-api-key: your-key
🏢 About Nepal INC
Nepal INC is a division of Nepal Holdings — a civilization infrastructure company building AGI, holographic computing, robotics, and space technology from Nepal.
"People see our usefulness. Soon they will see our vision."
📄 License
MIT License — free to use, modify, and distribute.
Built with ❤️ from Nepal 🇳🇵
