"""
pipeline/api.py — Groq and Gemini API calls.
Single module for all external calls — easy to swap models later.
"""

import json
import re
import urllib.request
import urllib.error
from config import GROQ_API_KEY, GEMINI_API_KEY, GROQ_MODEL

# Cloudflare on Groq's CDN blocks Python's default user-agent string.
_HEADERS_BASE = {
    "Content-Type": "application/json",
    "Accept":       "application/json",
    "User-Agent":   (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _read_error(e: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(e.read().decode())
        if isinstance(body, dict):
            return body.get("error", {}).get("message", str(body))
        return str(body)
    except Exception:
        return e.reason


def call_groq(messages: list, temperature: float = 0.85) -> str:
    """
    Send messages to Groq. Returns raw text response.
    Raises ValueError with actionable message on any failure.
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set.\n"
            "  Get a free key: https://console.groq.com\n"
            "  Then: export GROQ_API_KEY=gsk_..."
        )

    payload = json.dumps({
        "model":       GROQ_MODEL,
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data    = payload,
        headers = {**_HEADERS_BASE, "Authorization": f"Bearer {GROQ_API_KEY}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()

    except urllib.error.HTTPError as e:
        msg = _read_error(e)
        if e.code in (401, 403):
            raise ValueError(
                f"HTTP {e.code} from Groq: {msg}\n"
                f"  Check/renew key at https://console.groq.com/keys"
            )
        if e.code == 429:
            raise ValueError("Groq rate limit hit. Wait 30s and retry.")
        raise ValueError(f"Groq HTTP {e.code}: {msg}")

    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot reach Groq: {e.reason}\nCheck internet connection.")


def call_gemini(prompt: str, max_tokens: int = 600) -> str:
    """
    Send a single prompt to Gemini Flash. Returns raw text response.
    Returns empty string if GEMINI_API_KEY not set (caller handles gracefully).
    """
    if not GEMINI_API_KEY:
        return ""

    url = (
        "https://generativelanguage.googleapis.com/v1beta"
        f"/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": max_tokens},
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json", **_HEADERS_BASE},
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return ""


def parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$",     "", raw)
    return json.loads(raw)


def test_connection() -> bool:
    """Quick smoke test — prints result, returns True if working."""
    print("Testing Groq connection...")
    try:
        result = call_groq(
            [{"role": "user", "content": "Reply with exactly: OK"}],
            temperature=0.0
        )
        print(f"  ✅ Groq: {result}")
        return True
    except Exception as e:
        print(f"  ❌ {e}")
        return False
