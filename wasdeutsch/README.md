# 🇩🇪 Was?! Deutsch — Automated German Shorts Pipeline

> Because German keeps surprising you.

Generates complete German language learning short-form videos:
script → verified German → branded frames → Killian's voice.

---

## Setup (one time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys
export GROQ_API_KEY=gsk_...       # https://console.groq.com (free)
export GEMINI_API_KEY=AI...       # https://aistudio.google.com (free, optional)

# 3. Test connection
python run.py --test
```

---

## Usage

```bash
# Generate next episode (auto-picks phase, format, topic)
python run.py

# Force a specific format
python run.py --format trap
python run.py --format grammar_hook
python run.py --format a1_honest
python run.py --format eavesdrop
python run.py --format recap

# Force a specific word as topic
python run.py --topic "doch"
python run.py --topic "Gift"

# Preview script only — no files saved, no audio
python run.py --preview

# Skip voice generation (faster, for testing frames only)
python run.py --skip-audio

# Generate a full week (7 episodes)
python run.py --batch 7

# Show flagged episodes + vocabulary stats
python run.py --review
```

---

## Project Structure

```
wasdeutsch/
│
├── run.py                    ← ENTRY POINT — only file you run
├── config.py                 ← API keys, paths, brand colours
├── requirements.txt
│
├── curriculum/
│   ├── goethe_a1.json        ← ~650 Goethe A1 words by phase
│   ├── schedule.py           ← phase/format scheduling + SR tracker
│   └── tracker.json          ← auto-created, persists between runs
│
├── pipeline/
│   ├── api.py                ← Groq + Gemini calls (one place)
│   ├── script_gen.py         ← LLM script generation
│   ├── verify.py             ← 2-layer German verification
│   ├── renderer.py           ← PIL frame renderer (3 frames)
│   ├── audio.py              ← edge-tts voice generation
│   └── fonts.py              ← cross-platform font detection
│
├── formats/
│   └── prompts.py            ← prompt blueprints for all 5 formats
│
└── output/
    ├── episodes/             ← episode_0001_trap.json etc.
    ├── frames/               ← ep_0001/frame1_hook.png etc.
    └── audio/                ← ep_0001/killian_00.mp3 etc.
```

---

## Video Formats

| Format | Hook type | Phase | Automation |
|---|---|---|---|
| `trap` | False cognate reveal | All | 95% |
| `grammar_hook` | True/False or binary | All | 90% |
| `a1_honest` | Want vs Can gap | All | 90% |
| `eavesdrop` | Real dialogue | 2+ | 80% |
| `recap` | 5 words rapid-fire | Weekly | 95% |

---

## Curriculum (120 videos, 24 weeks)

| Phase | Topic | Videos |
|---|---|---|
| 0 | Trap & Hook (false cognates) | 10+ |
| 1 | Survival basics | 20 |
| 2 | Food & Drink | 20 |
| 3 | Getting Around | 20 |
| 4 | Social | 20 |
| 5 | Daily Life | 30 |

---

## Language Policy

**All video content works without knowing English.**

Hooks are in German. Emoji carry meaning. Visual contrast shows grammar.
A learner from Turkey, Brazil, or Korea can follow every video.

---

## Automation (GitHub Actions)

Add `.github/workflows/daily.yml`:

```yaml
name: Daily Episode
on:
  schedule:
    - cron: '0 9 * * *'   # 9am UTC every day
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: python run.py --skip-audio
        env:
          GROQ_API_KEY:   ${{ secrets.GROQ_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      - uses: actions/upload-artifact@v3
        with:
          name: episode
          path: output/
```
