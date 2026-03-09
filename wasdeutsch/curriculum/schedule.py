"""
curriculum/schedule.py — Episode scheduling and spaced repetition tracker.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from config import TRACKER_FILE, SR_INTERVALS, MAX_NEW_WORDS

# ── CURRICULUM MAP ─────────────────────────────────────────────────────────────
PHASES = {
    1: {"name": "Survival",       "vocab_key": "phase_1_survival",  "new_per_video": 2},
    2: {"name": "Food & Drink",   "vocab_key": "phase_2_food",      "new_per_video": 3},
    3: {"name": "Getting Around", "vocab_key": "phase_3_transport",  "new_per_video": 3},
    4: {"name": "Social",         "vocab_key": "phase_4_social",     "new_per_video": 3},
    5: {"name": "Daily Life",     "vocab_key": "phase_5_daily",      "new_per_video": 3},
}

# Format rotation per phase — trap every 7th, recap every 5th, rest rotate
FORMAT_ROTATION = {
    1: ["grammar_hook", "a1_honest", "grammar_hook", "a1_honest"],
    2: ["eavesdrop", "a1_honest", "grammar_hook", "eavesdrop"],
    3: ["eavesdrop", "grammar_hook", "a1_honest", "eavesdrop"],
    4: ["eavesdrop", "a1_honest", "grammar_hook", "eavesdrop"],
    5: ["eavesdrop", "a1_honest", "grammar_hook", "eavesdrop"],
}


# ── SCHEDULING ─────────────────────────────────────────────────────────────────
def determine_phase(episode_num: int) -> int:
    week = (episode_num - 1) // 5 + 1
    if week <= 4:  return 1
    if week <= 8:  return 2
    if week <= 12: return 3
    if week <= 16: return 4
    return 5


def determine_format(episode_num: int, phase: int, force: str = None) -> str:
    if force:
        return force
    if episode_num % 7 == 0:
        return "trap"
    if episode_num % 5 == 0:
        return "recap"
    rotation = FORMAT_ROTATION.get(phase, FORMAT_ROTATION[1])
    return rotation[episode_num % len(rotation)]


# ── TRACKER ────────────────────────────────────────────────────────────────────
def load_tracker() -> dict:
    if TRACKER_FILE.exists():
        return json.loads(TRACKER_FILE.read_text(encoding="utf-8"))
    return {"words": {}, "episode_count": 0, "last_run": ""}


def save_tracker(tracker: dict):
    tracker["last_run"] = datetime.now().isoformat()
    TRACKER_FILE.write_text(
        json.dumps(tracker, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_sr_words(tracker: dict, episode_num: int, max_words: int = 4) -> list:
    """Return words whose spaced repetition interval is due."""
    due = []
    for word, info in tracker["words"].items():
        if info["status"] == "consolidated":
            continue
        appearances = info["appearances"]
        n = len(appearances)
        last = appearances[-1] if appearances else 0
        interval = SR_INTERVALS[min(n - 1, len(SR_INTERVALS) - 1)]
        if episode_num >= last + interval:
            due.append(word)
    return due[:max_words]


def update_tracker(tracker: dict, script: dict, episode_num: int):
    """Record new words and SR appearances from a completed script."""
    for word in script.get("new_words", []):
        if word not in tracker["words"]:
            tracker["words"][word] = {
                "introduced_ep": episode_num,
                "appearances":   [episode_num],
                "status":        "active",
                "phase":         script.get("phase", 1),
            }

    for word in script.get("sr_words_used", []):
        if word in tracker["words"]:
            info = tracker["words"][word]
            if episode_num not in info["appearances"]:
                info["appearances"].append(episode_num)
            if len(info["appearances"]) >= 5:
                info["status"] = "consolidated"

    tracker["episode_count"] = episode_num
    save_tracker(tracker)


def get_next_episode(force_format: str = None, force_topic: str = None) -> dict:
    """Return a fully resolved episode spec ready for the pipeline."""
    tracker    = load_tracker()
    episode    = tracker["episode_count"] + 1
    phase      = determine_phase(episode)
    fmt        = determine_format(episode, phase, force_format)
    sr_words   = get_sr_words(tracker, episode)

    return {
        "episode":    episode,
        "phase":      phase,
        "phase_name": PHASES[phase]["name"],
        "format":     fmt,
        "sr_words":   sr_words,
        "topic":      force_topic,
        "tracker":    tracker,
    }


def print_tracker_stats():
    tracker = load_tracker()
    words   = tracker["words"]
    active  = [(w, i) for w, i in words.items() if i["status"] == "active"]
    consol  = [(w, i) for w, i in words.items() if i["status"] == "consolidated"]
    ep_now  = tracker["episode_count"] + 1

    print(f"\n📊 Vocabulary Tracker")
    print(f"   Total tracked:       {len(words)}")
    print(f"   Active (drilling):   {len(active)}")
    print(f"   Consolidated:        {len(consol)}")

    if active:
        print(f"\n   SR due next:")
        for w, info in sorted(active, key=lambda x: x[1]["appearances"][-1])[:8]:
            n        = len(info["appearances"])
            last     = info["appearances"][-1]
            interval = SR_INTERVALS[min(n - 1, len(SR_INTERVALS) - 1)]
            due_ep   = last + interval
            flag     = "⏰ DUE" if ep_now >= due_ep else f"ep {due_ep}"
            print(f"   {w:<25} seen {n}x  {flag}")
