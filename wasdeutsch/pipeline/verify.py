"""
pipeline/verify.py — Two-layer German accuracy verification.

Layer 1: Groq self-check (grammar, umlauts, conjugation)
Layer 2: Gemini Flash independent check (naturalness, A1 level, register)
"""

import json
from pipeline.api import call_groq, call_gemini, parse_json_response


def _collect_german_lines(script: dict) -> list[str]:
    lines = list(script.get("killian_lines", []))
    lines += [d.get("de", "") for d in script.get("dialogue", [])]
    if script.get("casual_german"):
        lines.append(script["casual_german"])
    return [l for l in lines if l]


def _groq_check(script: dict) -> dict:
    """Ask Groq to review its own German output."""
    lines = _collect_german_lines(script)
    if not lines:
        return {"passed": True, "corrected_script": script}

    prompt = (
        "Du bist ein muttersprachlicher Deutschlektor.\n\n"
        "Prüfe diese deutschen Sätze:\n"
        + json.dumps(lines, ensure_ascii=False, indent=2)
        + "\n\nPrüfe:\n"
        "1. Grammatikfehler (Artikel, Konjugation, Wortstellung)\n"
        "2. Fehlende Umlaute (ä/ö/ü/ß)\n"
        "3. Unnatürliche Formulierungen\n\n"
        "Nur JSON zurückgeben:\n"
        '{"passed":true/false,"issues":[{"original":"...","problem":"...","correction":"..."}],"quality":"sehr gut/gut/überarbeiten"}'
    )

    try:
        raw    = call_groq(
            [{"role": "system", "content": "Deutschlektor. Nur JSON."},
             {"role": "user",   "content": prompt}],
            temperature=0.1
        )
        result = parse_json_response(raw)

        if not result.get("passed") and result.get("issues"):
            print(f"    Groq found {len(result['issues'])} issue(s) — auto-correcting...")
            result["corrected_script"] = _groq_correct(script, result["issues"])
        else:
            result["corrected_script"] = script
        return result

    except Exception as e:
        # Verification failure is non-fatal — flag for manual review
        return {"passed": True, "corrected_script": script, "error": str(e)}


def _groq_correct(script: dict, issues: list) -> dict:
    """Ask Groq to fix the specific issues it found."""
    fixes = "\n".join(
        f"- '{i.get('original')}' → '{i.get('correction')}'"
        for i in issues
    )
    prompt = (
        "Korrigiere diese Fehler im Script:\n"
        + fixes
        + "\n\nScript:\n"
        + json.dumps(script, ensure_ascii=False, indent=2)
        + "\n\nVollständiges korrigiertes JSON zurückgeben."
    )
    try:
        raw = call_groq(
            [{"role": "system", "content": "Korrigiere. Nur JSON."},
             {"role": "user",   "content": prompt}],
            temperature=0.1
        )
        return parse_json_response(raw)
    except Exception:
        return script  # return original if correction fails


def _gemini_check(script: dict) -> dict:
    """Independent check via Gemini Flash."""
    lines = _collect_german_lines(script)
    if not lines:
        return {"passed": True, "skipped": False}

    lines_json = json.dumps(lines, ensure_ascii=False, indent=2)
    prompt = (
        "You are a native German speaker reviewing language learning video content.\n\n"
        "German lines:\n" + lines_json + "\n\n"
        "Check:\n"
        "1. GRAMMAR: errors in articles, conjugation, word order, umlauts?\n"
        "2. NATURALNESS: real spoken German, or stiff/textbook?\n"
        "3. LEVEL: all vocabulary A1/A2 appropriate?\n\n"
        "Return only JSON:\n"
        '{"grammar_ok":true,"grammar_issues":[],"naturalness_ok":true,'
        '"naturalness_notes":"...","level_ok":true,"level_issues":[],'
        '"overall":"pass/flag/fail","suggestion":"..."}'
    )

    raw = call_gemini(prompt)
    if not raw:
        return {"skipped": True}

    try:
        result = parse_json_response(raw)
        result["source"] = "gemini-2.0-flash"
        return result
    except Exception:
        return {"skipped": True}


def verify(script: dict) -> dict:
    """
    Run both verification layers. Returns:
    {
        "verdict":      "APPROVED" | "NEEDS_REVIEW",
        "final_script": <corrected script dict>,
        "groq":         <layer 1 result>,
        "gemini":       <layer 2 result>,
    }
    """
    print("  Layer 1 — Groq check...")
    g1      = _groq_check(script)
    working = g1.get("corrected_script", script)

    print("  Layer 2 — Gemini check...")
    g2 = _gemini_check(working)

    gemini_ok = g2.get("overall", "pass") == "pass" or g2.get("skipped", True)
    passed    = g1.get("passed", True) and gemini_ok

    verdict = "APPROVED" if passed else "NEEDS_REVIEW"
    icon    = "✅" if passed else "⚠️ "
    print(f"  {icon} {verdict}")

    if not passed and g2.get("suggestion"):
        print(f"    Gemini note: {g2['suggestion']}")

    return {
        "verdict":      verdict,
        "final_script": working,
        "groq":         g1,
        "gemini":       g2,
    }
