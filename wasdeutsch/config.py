"""
config.py — Was?! Deutsch pipeline configuration
All constants in one place. Only file you need to edit before first run.
"""

import os
from pathlib import Path

# ── API KEYS ──────────────────────────────────────────────────────────────────
# Option A: set in shell before running
#   export GROQ_API_KEY=gsk_...
#   export GEMINI_API_KEY=AI...
#
# Option B: paste directly here (never commit to git)
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY",   "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY",  "")  # optional but recommended

GROQ_MODEL = "llama-3.3-70b-versatile"

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
CURRICULUM_DIR = BASE_DIR / "curriculum"
OUTPUT_DIR     = BASE_DIR / "output"
EPISODES_DIR   = OUTPUT_DIR / "episodes"
FRAMES_DIR     = OUTPUT_DIR / "frames"
AUDIO_DIR      = OUTPUT_DIR / "audio"
TRACKER_FILE   = CURRICULUM_DIR / "tracker.json"

for d in [CURRICULUM_DIR, EPISODES_DIR, FRAMES_DIR, AUDIO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── BRAND — German flag DNA palette ───────────────────────────────────────────
BLACK = (10,  10,  12)
RED   = (204, 20,  20)
GOLD  = (255, 200,  0)
WHITE = (252, 252, 250)
SMOKE = (28,  26,  28)
MIDG  = (160, 155, 148)
OFFW  = (240, 238, 230)

# ── VIDEO ─────────────────────────────────────────────────────────────────────
VIDEO_W = 1080
VIDEO_H = 1920
VIDEO_FPS = 30

# ── VOICE ─────────────────────────────────────────────────────────────────────
VOICE_KILLIAN = "de-DE-KillianNeural"   # formal German lines
VOICE_RATE_FORMAL = "-10%"              # slightly slower for clarity
VOICE_RATE_CASUAL  = "0%"              # natural speed for authentic layer

# ── PIPELINE ──────────────────────────────────────────────────────────────────
MAX_RETRIES    = 3   # Groq generation attempts before giving up
MAX_NEW_WORDS  = 3   # maximum new vocabulary per video
SR_INTERVALS   = [3, 8, 20, 50]  # spaced repetition gaps in episodes
