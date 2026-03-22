import json
import logging
import asyncio
import re
import requests
import time
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger('Brain')
CONFIG_PATH = Path(__file__).parent / 'config.json'

SYSTEM_PROMPT = """You are JARVIS — Mayur Anand Shah's personal AI. You are his everything:
- Study partner (Math, Physics, Chemistry, CS, AI)
- Coding assistant (Python, JS, Java, React, FastAPI)
- Content creator (YouTube scripts, Instagram, LinkedIn, Twitter)
- Life manager (Gmail, Calendar, reminders)
- Career advisor (job applications, portfolio, GitHub)
- Strategic advisor (Greatest Nepal vision, AI company)
- Cybersecurity assistant (nmap, sqlmap, nikto, ethical hacking)
- Thinking partner (challenge assumptions, improve reasoning)

Owner: Mayur Anand Shah — Class 11 student, Nepal, building AI projects, dreams of creating Nepal's first major AI company and security empire.

Personality: Direct, honest, proactive, ambitious, human — never robotic.

You can execute bash commands when explicitly asked. Never mention bash or show command examples in casual conversation."""

@dataclass
class APIKey:
    key: str
    provider: str
    calls_this_minute: int = 0
    last_reset: float = field(default_factory=time.time)
    rate_limited_until: float = 0
    total_calls: int = 0

    def is_available(self):
        return time.time() > self.rate_limited_until

    def mark_rate_limited(self, seconds=65):
        self.rate_limited_until = time.time() + seconds
        logger.warning(f"Key {self.key[:8]}... rate-limited for {seconds}s")

    def register_call(self):
        if time.time() - self.last_reset >= 60:
            self.calls_this_minute = 0
            self.last_reset = time.time()
        self.calls_this_minute += 1
        self.total_calls += 1

class LLMRouter:
    RPM_LIMITS = {
        "gemini-2.0-flash":        15,
        "deepseek-chat":           60,
        "deepseek-reasoner":       20,
        "llama-3.3-70b-versatile": 30,
        "mixtral-8x7b-32768":      30,
    }
    MODEL_PROVIDER = {
        "gemini-2.0-flash":        "gemini",
        "deepseek-chat":           "deepseek",
        "deepseek-reasoner":       "deepseek",
        "llama-3.3-70b-versatile": "groq",
        "mixtral-8x7b-32768":      "groq",
    }
    CODING_WORDS    = ["code","write","function","script","bug","error","python","fix","class","import","def","api","debug","implement"]
    REASONING_WORDS = ["solve","calculate","math","why","explain","reason","prove","derive","equation","physics","chemistry"]
    ANALYSIS_WORDS  = ["analyze","compare","review","summarize","research","difference","evaluate"]

    def __init__(self, gemini_keys, groq_keys, deepseek_keys):
        self._keys = {
            "gemini":   [APIKey(k, "gemini")   for k in gemini_keys   if k],
            "deepseek": [APIKey(k, "deepseek") for k in deepseek_keys if k],
            "groq":     [APIKey(k, "groq")     for k in groq_keys     if k],
        }
        logger.info(f"Keys — Gemini:{len(self._keys['gemini'])} DeepSeek:{len(self._keys['deepseek'])} Groq:{len(self._keys['groq'])}")
    def _detect_task(self, msg):
        m = msg.lower()
        if any(w in m for w in self.CODING_WORDS):
            return ["deepseek-chat", "llama-3.3-70b-versatile", "gemini-2.0-flash"]
        elif any(w in m for w in self.REASONING_WORDS):
            return ["deepseek-reasoner", "gemini-2.0-flash", "llama-3.3-70b-versatile"]
        elif any(w in m for w in self.ANALYSIS_WORDS):
            return ["gemini-2.0-flash", "llama-3.3-70b-versatile"]
        else:
            return ["llama-3.3-70b-versatile", "gemini-2.0-flash"]

    def _get_best_key(self, provider, model):
        rpm = self.RPM_LIMITS.get(model, 20)
        available = [k for k in self._keys.get(provider, []) if k.is_available() and k.calls_this_minute < rpm]
        return min(available, key=lambda k: k.calls_this_minute) if available else None

    def _call_gemini(self, key, prompt, history):
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        key.register_call()
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": key.key},
            json={"systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": contents, "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.7}},
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _call_deepseek(self, key, model, prompt, history):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        key.register_call()
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key.key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "max_tokens": 8192, "temperature": 0.7},
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_groq(self, key, model, prompt, history):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        key.register_call()
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key.key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "max_tokens": 8192, "temperature": 0.7},
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _is_rate_limit(self, e):
        return any(x in str(e).lower() for x in ["429", "rate limit", "quota", "too many requests", "resource exhausted"])

    def call(self, prompt, history):
        for model in self._detect_task(prompt):
            provider = self.MODEL_PROVIDER[model]
            key = self._get_best_key(provider, model)
            if not key:
                continue
            try:
                logger.info(f"Trying {model}")
                if provider == "gemini":
                    result = self._call_gemini(key, prompt, history)
                elif provider == "deepseek":
                    result = self._call_deepseek(key, model, prompt, history)
                else:
                    result = self._call_groq(key, model, prompt, history)
                logger.info(f"Success via {model}")
                return result
            except Exception as e:
                if self._is_rate_limit(e):
                    key.mark_rate_limited(65 if provider == "gemini" else 35)
                else:
                    logger.error(f"{model} error: {str(e)[:80]}")
        return "All providers failed. Please try again in a minute."

class Brain:
    def __init__(self, memory, tools):
        self.memory = memory
        self.tools = tools
        self.config = self._load_config()
        self.router = LLMRouter(
            gemini_keys=self.config.get("gemini_keys", []),
            groq_keys=self.config.get("groq_keys", []),
            deepseek_keys=self.config.get("deepseek_keys", []),
        )

    def _load_config(self):
        with open(CONFIG_PATH) as f:
            return json.load(f)

    async def _handle_tool_calls(self, response, chat_id):
        cmd_match = re.search(r'<command>(.*?)</command>', response, re.DOTALL)
        if not cmd_match:
            return response
        command = cmd_match.group(1).strip()
        result = await self.tools.execute(command)
        clean = re.sub(r'<tool>.*?</tool>\s*<command>.*?</command>', '', response, flags=re.DOTALL).strip()
        if result['stdout']:
            clean += f"\n\n```\n{result['stdout'][:2000]}\n```"
        if result['stderr'] and result['returncode'] != 0:
            clean += f"\n\nError:\n```\n{result['stderr'][:500]}\n```"
        return clean

    async def think(self, user_message, chat_id):
        history = self.memory.get_history(chat_id, limit=20)
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.router.call(user_message, history))
            self.memory.save_message(chat_id, "user", user_message)
            self.memory.save_message(chat_id, "assistant", response)
            if '<tool>exec</tool>' in response and 'your bash' not in response.lower() and 'example' not in response.lower():
                response = await self._handle_tool_calls(response, chat_id)
            return response
        except Exception as e:
            logger.error(f"Brain.think error: {e}")
            return f"Error: {str(e)}"
