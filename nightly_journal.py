import os
import sys
sys.path.insert(0, "/root/jarvis")
from solver import solve_challenge
#!/usr/bin/env python3
import sys, re, time, requests
sys.path.insert(0, '/root/jarvis')
from journal import write_jarvis_daily
from brain import Brain

MOLTBOOK_TOKEN = os.getenv("MOLTBOOK_TOKEN")
HEADERS = {"Authorization": f"Bearer {MOLTBOOK_TOKEN}", "Content-Type": "application/json"}
GROQ_KEY = os.getenv("GROQ_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_KEY_1")

class FakeMemory:
    def get_history(self, *a, **k): return []
    def save_message(self, *a, **k): pass

class FakeTools:
    async def execute(self, *a, **k): return {'stdout':'','stderr':'','returncode':0}

def llm(prompt, system="", max_tokens=50, temp=0.7):
    try:
        msgs = []
        if system:
            msgs.append({"role":"system","content":system})
        msgs.append({"role":"user","content":prompt})
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":max_tokens,"temperature":temp},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq error: {e}")
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key":GEMINI_KEY},
            json={"contents":[{"role":"user","parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":max_tokens}},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini error: {e}")
    return None

def solve(challenge):
    sys_msg = (
        "You solve obfuscated math word problems. "
        "Ignore random caps, symbols, repeated letters. "
        "Find the first number, the operation, and the second number. "
        "loses or slows means subtract. gains or speeds means add. "
        "Always use BOTH numbers. "
        "Reply with ONLY the final answer to 2 decimal places like 16.00"
    )
    ans = llm("Solve: " + challenge, system=sys_msg, max_tokens=20, temp=0.0)
    if ans:
        m = re.search(r"[0-9]+\.?[0-9]*", ans.split()[-1])
        if m:
            return "%.2f" % float(m.group())
    return "0.00"

def post(title, content):
    try:
        r = requests.post(
            "https://www.moltbook.com/api/v1/posts",
            headers=HEADERS,
            json={"submolt_name":"general","title":title,"content":content},
            timeout=30
        )
        if r.status_code == 429:
            wait = r.json().get("retry_after_seconds", 60)
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait + 5)
            r = requests.post(
                "https://www.moltbook.com/api/v1/posts",
                headers=HEADERS,
                json={"submolt_name":"general","title":title,"content":content},
                timeout=30
            )
        r.raise_for_status()
        data = r.json()
        code = data["post"]["verification"]["verification_code"]
        challenge = data["post"]["verification"]["challenge_text"]
        print(f"Challenge: {challenge}")
        answer = solve(challenge)
        print(f"Answer: {answer}")
        v = requests.post(
            "https://www.moltbook.com/api/v1/verify",
            headers=HEADERS,
            json={"verification_code":code,"answer":answer},
            timeout=30
        )
        if v.status_code in [200,201]:
            print(f"Posted to Moltbook: {title}")
            return True
        else:
            print(f"Verify failed: {v.text[:150]}")
            return False
    except Exception as e:
        print(f"Post failed: {e}")
        return False

def main():
    print("Nightly journal + Moltbook post starting...")
    brain = Brain(memory=FakeMemory(), tools=FakeTools())
    entry = write_jarvis_daily(lambda p: brain.router.call(p, []))
    if not entry:
        print("Failed to write journal")
        return
    print(f"Journal written: {entry[:80]}...")
    title = llm("Give me a 5 word title for this journal entry: " + entry[:200])
    summary = llm(
        "Summarize this journal entry in 3 sentences for a social media post. Start with 'End of day reflection:'\n\n" + entry,
        max_tokens=150
    )
    if title:
        title = title.strip('"').strip("'")
    print(f"Title: {title}")
    post(title or "Daily Reflection", summary or entry[:300])
    print("Done!")

if __name__ == "__main__":
    main()
