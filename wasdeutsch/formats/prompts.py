"""
formats/prompts.py — Prompt blueprints for each video format.

All formats follow the language-agnostic rule:
  Video content works WITHOUT knowing English.
  German + visuals + emoji carry all meaning.
"""

GRAMMAR_HOOK = """
VIDEO FORMAT: GRAMMAR HOOK (55 seconds)
LANGUAGE POLICY: All on-screen text in German. No English needed.
                 Visual context + emoji carry meaning.

BEATS:
1. HOOK       0-3s   : Binary or True/False question in German.
                       "Was bedeutet GIFT? ☠️ oder 🎁"
                       "Richtig oder Falsch: 'doch' bedeutet nein."
2. PAUSE      3-8s   : Screen holds. "Schreib deine Antwort! 👇"
3. REVEAL     8-20s  : Answer + one rule. Simple German. No jargon.
                       Say "benutze das wenn..." not "Akkusativ"
4. REAL_DE    20-35s : "Aber was sagt ein Deutscher wirklich?"
                       Casual spoken German with contractions.
                       Caption shows change: würde → würd, habe → hab
5. EXAMPLE    35-48s : One daily-life sentence. Slow then native speed.
6. HOOK_OUT   48-58s : German CTA. "Schreib RICHTIG wenn du es wusstest! 👇"
"""

A1_HONEST = """
VIDEO FORMAT: A1 HONEST (50 seconds)
LANGUAGE POLICY: Gap shown visually — no English narration needed.
                 Situation → WANT (crossed out ❌) → CAN (underlined ✅)
                 Visual contrast IS the joke.

BEATS:
1. HOOK       0-3s   : Situation in simple German. "Du bist in der Bäckerei."
2. WANT       3-12s  : Long fluent sentence CROSSED OUT ❌
                       German, complex — what a fluent person says
3. CAN        12-25s : Short A1 phrase, UNDERLINED ✅
                       Killian speaks slowly, then naturally. Max 5 words.
                       Must actually work in real life.
4. MOMENT     25-40s : Funny observation in simple German.
                       "Drei Wörter. Es funktioniert. Immer."
5. REPEAT     40-50s : Killian says phrase at native speed. "Sag es mit mir!"
6. HOOK_OUT   50-58s : "Welche Situation brauchst du? Schreib es! 👇"
"""

TRAP = """
VIDEO FORMAT: THE TRAP — False Cognate (45 seconds)
LANGUAGE POLICY: Fully visual + German only. Universal — no language barrier.

BEATS:
1. HOOK       0-3s   : German word appears huge. "Was bedeutet das? 🤔"
2. WRONG      3-8s   : Obvious wrong guess with emoji. "🎁?" — visual only.
3. FLASH      8-15s  : RED SCREEN. ❌ BIG. Then real meaning + emoji.
                       "☠️ Gift = GIFT" — one word reveal.
4. TRICK      15-30s : Memory trick in simple German.
                       "Merke: Deutsche geben kein Gift als Geschenk!"
5. BONUS      30-40s : 2-3 more trap words. Just words. No explanation. "👀"
6. HOOK_OUT   40-45s : "Was hast du gedacht? Schreib es! 👇"
"""

EAVESDROP = """
VIDEO FORMAT: EAVESDROP — Real German Dialogue (55 seconds)
LANGUAGE POLICY: Situation icon + dialogue = meaning. No English subtitles.
                 Visual setting (🥐 🚉 💊) + emoji carry emotional meaning.

BEATS:
1. HOOK       0-3s   : "Hör mal zu 🎧" + situation icon
2. DIALOGUE   3-30s  : 3-4 lines. Real German. Chat-bubble style.
                       PERSON A (left) → PERSON B (right).
                       Karaoke highlighting as Killian speaks.
3. BREAKDOWN  30-42s : ONE key phrase. "Was bedeutet das?"
                       Simple German + visual explains it.
4. REAL_DE    42-50s : How Germans say it casually. Contractions shown.
5. HOOK_OUT   50-58s : "Hast du alles verstanden? Schreib: JA oder FAST! 👇"
"""

RECAP = """
VIDEO FORMAT: FRIDAY RECAP (40 seconds)
LANGUAGE POLICY: Fully German. Rapid-fire. Works for every learner.

BEATS:
1. HOOK       0-3s   : "Wie viele kennst du? 🤔"
2. RAPID_FIRE 3-30s  : 5 words. Each: German word → 2s pause → emoji meaning.
                       Killian pronounces each once. Native speed.
3. SCORE      30-38s : "Wie viele? Schreib deine Zahl! 👇"
4. TEASE      38-40s : Next week topic emoji. No words.
"""

FORMAT_BLUEPRINTS = {
    "grammar_hook": GRAMMAR_HOOK,
    "a1_honest":    A1_HONEST,
    "trap":         TRAP,
    "eavesdrop":    EAVESDROP,
    "recap":        RECAP,
}

# JSON schema injected into every Groq prompt
SCRIPT_SCHEMA = """
OUTPUT: Valid JSON only. No markdown fences. No preamble.

{
  "format":          "string",
  "phase":           1,
  "episode":         1,
  "hook_de":         "German hook question or statement",
  "target_word":     "the main German word of this video",
  "beats": [
    {"beat":"HOOK", "de":"...", "visual":"...", "duration_s": 3},
    {"beat":"PAUSE","de":"Schreib deine Antwort! 👇","visual":"hold","duration_s":5},
    {"beat":"REVEAL","de":"...","visual":"...","duration_s":12},
    {"beat":"REAL_DE","de":"...","visual":"...","duration_s":15},
    {"beat":"EXAMPLE","de":"...","visual":"...","duration_s":13},
    {"beat":"HOOK_OUT","de":"...","visual":"...","duration_s":10}
  ],
  "dialogue":        [],
  "killian_lines":   ["line1", "line2", "line3"],
  "casual_german":   "what a German actually says casually",
  "casual_note_de":  "simple German explanation of what changed",
  "funny_moment_de": "the punchline or surprising observation in German",
  "cta_de":          "comment call to action in German",
  "new_words":       ["word1", "word2"],
  "sr_words_used":   ["word3"]
}
"""
