"""
pipeline/script_gen.py — Generate episode scripts via Groq.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from config import MAX_RETRIES, BASE_DIR
from pipeline.api import call_groq, parse_json_response
from formats.prompts import FORMAT_BLUEPRINTS, SCRIPT_SCHEMA

_VOCAB_FILE = BASE_DIR / "curriculum" / "goethe_a1.json"
_VOCAB = json.loads(_VOCAB_FILE.read_text(encoding="utf-8"))


def _get_phase_words(phase: int) -> list[str]:
    """Flatten all vocab for phases 1..n."""
    words = []
    for p in range(1, phase + 1):
        key = f"phase_{p}_" + {
            1: "survival", 2: "food", 3: "transport",
            4: "social",   5: "daily"
        }.get(p, "survival")
        section = _VOCAB.get(key, {})
        for sublist in section.values():
            words.extend(w for w in sublist if isinstance(w, str))

    for sublist in _VOCAB.get("grammar_hooks", {}).values():
        words.extend(w for w in sublist if isinstance(w, str))

    return list(set(words))


def _get_target_words(phase: int, topic: str = None) -> list[str]:
    """Pick 1-3 target words for this episode."""
    if topic:
        return [topic]
    key = f"phase_{phase}_" + {
        1: "survival", 2: "food", 3: "transport",
        4: "social",   5: "daily"
    }.get(phase, "survival")
    pool = []
    for sublist in _VOCAB.get(key, {}).values():
        pool.extend(w for w in sublist if isinstance(w, str))
    return random.sample(pool, min(3, len(pool))) if pool else ["bitte"]


def generate_script(
    episode_num: int,
    phase: int,
    fmt: str,
    sr_words: list[str],
    topic: str = None,
) -> dict:
    """
    Generate a script via Groq. Retries up to MAX_RETRIES times.
    Returns parsed script dict.
    """
    blueprint    = FORMAT_BLUEPRINTS.get(fmt, FORMAT_BLUEPRINTS["grammar_hook"])
    vocab_pool   = _get_phase_words(phase)
    vocab_sample = random.sample(vocab_pool, min(60, len(vocab_pool)))
    target_words = _get_target_words(phase, topic)

    system_prompt = (
        "Du bist Experte für Deutsch als Fremdsprache und Viral-Video-Autor.\n\n"
        f"FORMAT:\n{blueprint}\n\n"
        "REGELN:\n"
        "- Alle Videos funktionieren OHNE Englischkenntnisse\n"
        f"- Nur Wörter aus der Goethe A1 Liste: {', '.join(vocab_sample[:40])}...\n"
        "- Maximal 3 neue Wörter pro Video\n"
        "- Deutsch muss 100% korrekt sein\n"
        "- KEIN Grammatik-Jargon (kein 'Akkusativ', 'Konjunktiv' etc.)\n"
        "- EIN echter Überraschungsmoment pro Video\n\n"
        f"SCHEMA:\n{SCRIPT_SCHEMA}"
    )

    user_prompt = (
        f"Episode {episode_num} | Phase {phase} | Format: {fmt}\n"
        f"Zielwörter: {target_words}\n"
        f"SR-Wörter einbauen: {sr_words}\n"
        + (f"Thema: {topic}\n" if topic else "")
        + "\nMach es überraschend und einprägsam. Deutsch muss perfekt sein."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  Generating... (attempt {attempt}/{MAX_RETRIES})")
        try:
            raw    = call_groq(messages, temperature=0.85)
            script = parse_json_response(raw)
            script.setdefault("target_word",  target_words[0] if target_words else "")
            script.setdefault("target_words", target_words)
            script.setdefault("generated",    datetime.now().isoformat())
            script["episode"] = episode_num
            script["phase"]   = phase
            script["format"]  = fmt
            print(f"  ✅ Script generated")
            return script
        except Exception as e:
            print(f"  ⚠️  Attempt {attempt} failed: {e}")

    raise RuntimeError(
        f"Script generation failed after {MAX_RETRIES} attempts. "
        "Check your GROQ_API_KEY and internet connection."
    )
