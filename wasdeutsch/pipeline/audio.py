"""
pipeline/audio.py — Killian voice generation via edge-tts.

Designed to work correctly outside Jupyter (no event loop conflict).
Call generate_episode_audio() from run.py — it handles the event loop itself.
"""

import asyncio
from pathlib import Path
from config import VOICE_KILLIAN, VOICE_RATE_FORMAL, VOICE_RATE_CASUAL


async def _speak(text: str, voice: str, rate: str, out_path: Path) -> bool:
    """Single async TTS call."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(str(out_path))
        return True
    except ImportError:
        print("  edge-tts not installed. Run: pip install edge-tts")
        return False
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


async def _generate_all(lines: list[tuple], out_dir: Path) -> list[Path]:
    """Generate audio for all (text, rate) pairs concurrently."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks   = []
    paths   = []
    for i, (text, rate) in enumerate(lines):
        p = out_dir / f"killian_{i:02d}.mp3"
        paths.append(p)
        tasks.append(_speak(text, VOICE_KILLIAN, rate, p))

    results = await asyncio.gather(*tasks)

    successful = [p for p, ok in zip(paths, results) if ok]
    return successful


def generate_episode_audio(script: dict, episode_num: int, audio_base_dir: Path) -> list[Path]:
    """
    Top-level function — call from run.py.
    Handles the event loop correctly in any environment.

    Returns list of Path objects for generated audio files.
    """
    killian_lines = script.get("killian_lines", [])
    casual        = script.get("casual_german", "")

    if not killian_lines and not casual:
        print("  No Killian lines to voice.")
        return []

    # Build list of (text, rate) — casual line at natural speed
    lines_with_rate = []
    for i, line in enumerate(killian_lines):
        is_last_and_casual = (i == len(killian_lines) - 1 and casual)
        rate = VOICE_RATE_CASUAL if is_last_and_casual else VOICE_RATE_FORMAL
        lines_with_rate.append((line, rate))

    if casual and casual not in killian_lines:
        lines_with_rate.append((casual, VOICE_RATE_CASUAL))

    out_dir = audio_base_dir / f"ep_{episode_num:04d}"
    print(f"  Voicing {len(lines_with_rate)} line(s) as Killian...")

    # Run the async function correctly regardless of environment
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already inside a running loop (shouldn't happen outside Jupyter)
            # Use nest_asyncio if available, otherwise create a thread
            try:
                import nest_asyncio
                nest_asyncio.apply()
                files = loop.run_until_complete(_generate_all(lines_with_rate, out_dir))
            except ImportError:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, _generate_all(lines_with_rate, out_dir))
                    files  = future.result(timeout=120)
        else:
            files = loop.run_until_complete(_generate_all(lines_with_rate, out_dir))
    except RuntimeError:
        # No event loop at all — create one
        files = asyncio.run(_generate_all(lines_with_rate, out_dir))

    for i, f in enumerate(files):
        print(f"  ✅ Line {i+1}: {f.name}")

    return files
