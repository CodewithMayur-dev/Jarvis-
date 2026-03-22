import os
#!/usr/bin/env python3
"""
Moltbook challenge solver — Python number parsing + LLM for operation only.
"""
import re
import requests

GROQ_KEY = os.getenv("GROQ_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_KEY_1")

# Number words map
ONES = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19}
TENS = {"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90}

def clean_text(text):
    """Remove noise: symbols, random caps, repeated letters."""
    # Remove symbols
    t = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # Lowercase
    t = t.lower()
    # Remove repeated letters (3+ same consecutive) e.g. "errr" -> "er", "tttee" -> "te"
    t = re.sub(r'(.)\1{2,}', r'\1\1', t)
    # Normalize spaces
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def extract_numbers(text):
    """Extract all numbers from text including compound word numbers."""
    words = text.split()
    numbers = []
    i = 0
    while i < len(words):
        w = words[i]
        # Check digit
        try:
            numbers.append(float(w))
            i += 1
            continue
        except:
            pass
        # Check tens + ones compound (e.g. "twenty five")
        if w in TENS:
            val = TENS[w]
            if i+1 < len(words) and words[i+1] in ONES:
                val += ONES[words[i+1]]
                i += 2
            else:
                i += 1
            numbers.append(float(val))
        elif w in ONES:
            numbers.append(float(ONES[w]))
            i += 1
        else:
            i += 1
    return numbers

def get_operation(text):
    """Use simple keyword matching to find operation."""
    t = text.lower()
    # Subtract keywords
    if any(w in t for w in ["loses","loss","slow","minus","subtract","decrease","reduce","less"]):
        return "sub"
    # Multiply keywords
    if any(w in t for w in ["momentum","times","multiply","multiplied","product","force.*mass","mass.*velocity","kinetic"]):
        return "mul"
    # Divide keywords
    if any(w in t for w in ["divide","divided","per unit","average","split"]):
        return "div"
    # Default add
    return "add"

def solve_challenge(challenge):
    clean = clean_text(challenge)
    print(f"[Solver] Clean: {clean}")

    numbers = extract_numbers(clean)
    print(f"[Solver] Numbers found: {numbers}")

    if len(numbers) < 2:
        # Ask LLM as fallback
        return llm_solve(challenge, clean)

    op = get_operation(clean)
    print(f"[Solver] Operation: {op}")

    n1, n2 = numbers[0], numbers[1]
    if op == "add": result = n1 + n2
    elif op == "sub": result = n1 - n2
    elif op == "mul": result = n1 * n2
    elif op == "div": result = n1 / n2 if n2 != 0 else 0
    else: result = n1 + n2

    print(f"[Solver] {n1} {op} {n2} = {result}")
    return "%.2f" % result

def llm_solve(challenge, clean):
    """Fallback LLM solver."""
    prompt = f"Obfuscated math challenge:\nOriginal: {challenge}\nCleaned: {clean}\n\nFind all numbers and operation. Reply with ONLY the final answer to 2 decimal places."
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],"max_tokens":50,"temperature":0.0},
            timeout=30
        )
        r.raise_for_status()
        ans = r.json()["choices"][0]["message"]["content"].strip()
        nums = re.findall(r'\d+\.?\d*', ans)
        if nums:
            return "%.2f" % float(nums[-1])
    except:
        pass
    return "0.00"
