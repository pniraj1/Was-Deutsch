"""
run.py — Was?! Deutsch pipeline entry point.

Usage:
    python run.py                     # next episode, auto format
    python run.py --format trap       # force format
    python run.py --topic "doch"      # force topic word
    python run.py --batch 7           # generate full week
    python run.py --preview           # print script only, no files saved
    python run.py --review            # show flagged episodes + SR stats
    python run.py --test              # test API connection only
    python run.py --skip-audio        # skip voice generation
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# ── Ensure we can import from project root ───────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from config import EPISODES_DIR, FRAMES_DIR, AUDIO_DIR, GROQ_API_KEY
from curriculum.schedule import (
    get_next_episode, update_tracker, load_tracker,
    print_tracker_stats, determine_format, determine_phase, get_sr_words
)
from pipeline.api     import test_connection
from pipeline.script_gen import generate_script
from pipeline.verify     import verify
from pipeline.renderer   import render_all
from pipeline.audio      import generate_episode_audio
import pipeline.fonts as fonts


# ── SINGLE EPISODE ────────────────────────────────────────────────────────────
def run_episode(
    force_format: str = None,
    force_topic:  str = None,
    skip_audio:   bool = False,
    preview:      bool = False,
) -> dict:

    # 1 — Schedule
    spec = get_next_episode(force_format, force_topic)
    ep   = spec["episode"]
    ph   = spec["phase"]
    fmt  = spec["format"]

    print(f"\n🇩🇪  WAS?! DEUTSCH — EPISODE GENERATOR")
    print("━" * 50)
    print(f"  Episode:  {ep}")
    print(f"  Phase:    {ph} — {spec['phase_name']}")
    print(f"  Format:   {fmt}")
    print(f"  SR due:   {spec['sr_words'] or 'none'}")
    print()

    # 2 — Generate script
    print("STEP 1 — Generating script...")
    script = generate_script(ep, ph, fmt, spec["sr_words"], force_topic)
    print()

    if preview:
        print("── PREVIEW ──────────────────────────────────")
        print(f"  Hook:          {script.get('hook_de', '')}")
        print(f"  Target word:   {script.get('target_word', '')}")
        print(f"  Casual German: {script.get('casual_german', '')}")
        print(f"  CTA:           {script.get('cta_de', '')}")
        print(f"  New words:     {script.get('new_words', [])}")
        print(f"  Killian lines:")
        for line in script.get("killian_lines", []):
            print(f"    • {line}")
        print()
        return script

    # 3 — Verify
    print("STEP 2 — Verifying German...")
    result = verify(script)
    final  = result["final_script"]
    final["verification"] = result["verdict"]
    print()

    # 4 — Render frames
    print("STEP 3 — Rendering frames...")
    fonts.init_fonts(verbose=True)
    frame_dir = FRAMES_DIR / f"ep_{ep:04d}"
    frame_paths = render_all(final, ep, fmt, frame_dir)
    print(f"  ✅ {len(frame_paths)} frames → {frame_dir}")
    print()

    # 5 — Audio
    audio_files = []
    if not skip_audio:
        print("STEP 4 — Generating audio...")
        audio_files = generate_episode_audio(final, ep, AUDIO_DIR)
        print()
    else:
        print("STEP 4 — Audio skipped (--skip-audio)")
        print()

    # 6 — Save episode
    final["frame_paths"]  = [str(p) for p in frame_paths]
    final["audio_files"]  = [str(p) for p in audio_files]
    final["generated_at"] = datetime.now().isoformat()

    ep_file = EPISODES_DIR / f"episode_{ep:04d}_{fmt}.json"
    ep_file.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    update_tracker(spec["tracker"], final, ep)

    # Summary
    print("━" * 50)
    print(f"✅  EPISODE {ep} COMPLETE")
    print(f"    Hook:         {final.get('hook_de', '')}")
    print(f"    Target word:  {final.get('target_word', '')}")
    print(f"    Verification: {result['verdict']}")
    print(f"    Saved:        {ep_file.name}")

    if result["verdict"] == "NEEDS_REVIEW":
        print()
        print("  ⚠️  Check the German before uploading — flagged for review.")

    return final


# ── BATCH ─────────────────────────────────────────────────────────────────────
def run_batch(
    n:            int,
    skip_audio:   bool = False,
    force_format: str  = None,
):
    print(f"\n📦 BATCH MODE — {n} episodes")
    print("━" * 50)

    results = []
    for i in range(n):
        print(f"\n[{i+1}/{n}]", end=" ")
        try:
            ep = run_episode(force_format=force_format, skip_audio=skip_audio)
            results.append(ep)
        except Exception as e:
            print(f"❌ Failed: {e}")
            continue

    print(f"\n✅ Batch done — {len(results)}/{n} succeeded.")
    return results


# ── REVIEW QUEUE ──────────────────────────────────────────────────────────────
def show_review():
    flagged = []
    for ep_path in sorted(EPISODES_DIR.glob("*.json")):
        ep = json.loads(ep_path.read_text(encoding="utf-8"))
        if ep.get("verification") == "NEEDS_REVIEW":
            flagged.append((ep_path.name, ep))

    print(f"\n🔍 REVIEW QUEUE")
    print("━" * 50)
    if not flagged:
        print("✅ Nothing flagged — all episodes approved.")
    else:
        print(f"⚠️  {len(flagged)} episode(s) need review:\n")
        for name, ep in flagged:
            print(f"  📄 {name}")
            print(f"     Hook:   {ep.get('hook_de', '')}")
            print(f"     Casual: {ep.get('casual_german', '')}")
            print()

    print()
    print_tracker_stats()


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Was?! Deutsch — automated German shorts pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--format",      metavar="FMT",  help="Force format: trap / grammar_hook / a1_honest / eavesdrop / recap")
    parser.add_argument("--topic",       metavar="WORD", help="Force a specific German word as topic")
    parser.add_argument("--batch",       metavar="N",    type=int, help="Generate N episodes in sequence")
    parser.add_argument("--preview",     action="store_true", help="Print script only — no files saved")
    parser.add_argument("--skip-audio",  action="store_true", help="Skip voice generation")
    parser.add_argument("--review",      action="store_true", help="Show flagged episodes and SR stats")
    parser.add_argument("--test",        action="store_true", help="Test API connection and exit")

    args = parser.parse_args()

    # Always show a key warning if missing
    if not GROQ_API_KEY and not args.review:
        print("⚠️  GROQ_API_KEY not set.")
        print("   Get a free key: https://console.groq.com")
        print("   Then: export GROQ_API_KEY=gsk_...")
        if not args.test:
            sys.exit(1)

    if args.test:
        test_connection()
        return

    if args.review:
        show_review()
        return

    if args.batch:
        run_batch(args.batch, skip_audio=args.skip_audio, force_format=args.format)
        return

    run_episode(
        force_format = args.format,
        force_topic  = args.topic,
        skip_audio   = args.skip_audio,
        preview      = args.preview,
    )


if __name__ == "__main__":
    main()
