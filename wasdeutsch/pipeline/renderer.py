"""
pipeline/renderer.py — Renders the 3 Was?! Deutsch video frames.

Frame 1 — Hook:     off-white field, black crown, gold bar, red base
Frame 2 — Reveal:   full red field (visual shock)
Frame 3 — Authentic: full black field (register shift)
"""

from pathlib import Path
from PIL import Image, ImageDraw
from config import BLACK, RED, GOLD, WHITE, SMOKE, MIDG, OFFW, VIDEO_W as W, VIDEO_H as H
import pipeline.fonts as fonts


# ── DRAWING HELPERS ───────────────────────────────────────────────────────────
def _tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def _th(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]

def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words, lines, current = text.split(), [], []
    for word in words:
        test = " ".join(current + [word])
        if _tw(draw, test, font) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [""]

def _flag_stripe(draw, y: int, width: int = W, thick: int = 14) -> int:
    draw.rectangle([0, y,            width, y + thick],          fill=BLACK)
    draw.rectangle([0, y+thick+2,    width, y + thick*2 + 2],    fill=RED)
    draw.rectangle([0, y+thick*2+4,  width, y + thick*3 + 4],    fill=GOLD)
    return y + thick * 3 + 12


# ── FRAME 1 — HOOK ────────────────────────────────────────────────────────────
def render_hook(script: dict, episode_num: int, fmt: str) -> Image.Image:
    img  = Image.new("RGB", (W, H), OFFW)
    draw = ImageDraw.Draw(img)

    # Structural bands
    draw.rectangle([0, 0,       W, 290],    fill=BLACK)
    draw.rectangle([0, 290,     W, 306],    fill=GOLD)
    draw.rectangle([0, H - 210, W, H],      fill=RED)
    draw.rectangle([0, H - 210, W, H - 202], fill=GOLD)

    # Ghost "WAS?!" watermark
    try:
        ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd    = ImageDraw.Draw(ghost)
        gd.text((-40, H // 2 - 200), "WAS?!", font=fonts.get(None, 360), fill=(204, 20, 20, 16))
        ghost = ghost.rotate(-14, resample=Image.BICUBIC, center=(W // 2, H // 2))
        img   = Image.alpha_composite(img.convert("RGBA"), ghost).convert("RGB")
        draw  = ImageDraw.Draw(img)
    except Exception:
        pass

    # Channel name
    f_ch = fonts.get(None, 42)
    draw.text((54, 60), "WAS?! DEUTSCH", font=f_ch, fill=GOLD)
    cw = _tw(draw, "WAS?! DEUTSCH", f_ch)
    draw.rectangle([54, 115, 54 + cw, 119], fill=GOLD)

    # Small flag (top right of crown)
    for idx, col in enumerate([BLACK, RED, GOLD]):
        sy = 86 + idx * 15
        draw.rectangle([W - 220, sy, W - 20, sy + 11], fill=col)

    draw.text(
        (54, 196),
        f"EP {episode_num:02d}  ·  {fmt.upper().replace('_', ' ')}",
        font=fonts.get(None, 30), fill=MIDG
    )

    # Hook question
    y    = 348
    hook = script.get("hook_de", "Was?")
    f_q  = fonts.get(None, 78)
    for line in _wrap(draw, hook, f_q, W - 108):
        draw.text((54, y), line, font=f_q, fill=BLACK)
        y += _th(draw, line, f_q) + 8
    y += 20
    draw.rectangle([54, y, W - 54, y + 5], fill=GOLD)
    y += 32

    # Target word — big black block
    target = script.get("target_word", "")
    if target:
        bh = 230
        draw.rectangle([0, y, W, y + bh], fill=BLACK)
        draw.rectangle([0, y, 16, y + bh], fill=GOLD)
        f_w  = fonts.get(None, 190)
        tw_  = _tw(draw, target, f_w)
        th_  = _th(draw, target, f_w)
        ty   = y + (bh - th_) // 2 - 6
        # Red shadow
        try:
            sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sl)
            sd.text((62, ty + 4), target, font=f_w, fill=(204, 20, 20, 55))
            img  = Image.alpha_composite(img.convert("RGBA"), sl).convert("RGB")
            draw = ImageDraw.Draw(img)
        except Exception:
            pass
        draw.text((54, ty), target, font=f_w, fill=GOLD)
        y += bh + 40

    # Answer options
    f_opt = fonts.get(None, 44)
    bw2   = (W - 128) // 2
    draw.rounded_rectangle([54, y, 54 + bw2, y + 100],          radius=14, fill=BLACK, outline=GOLD, width=3)
    draw.text((82, y + 24), "A  ☠️", font=f_opt, fill=GOLD)
    bx2 = 54 + bw2 + 20
    draw.rounded_rectangle([bx2, y, bx2 + bw2, y + 100],        radius=14, fill=RED)
    draw.text((bx2 + 28, y + 24), "B  🎁", font=f_opt, fill=WHITE)
    y += 120

    # Pause prompt
    f_p  = fonts.get(None, 50)
    pt   = "Schreib deine Antwort! 👇"
    draw.text(((W - _tw(draw, pt, f_p)) // 2, y), pt, font=f_p, fill=BLACK)

    # CTA in red base
    cta = script.get("cta_de", "Kommentiere! 👇")
    f_c = fonts.get(None, 46)
    draw.text(((W - _tw(draw, cta, f_c)) // 2, H - 160), cta, font=f_c, fill=WHITE)

    return img


# ── FRAME 2 — REVEAL ──────────────────────────────────────────────────────────
def render_reveal(script: dict) -> Image.Image:
    img  = Image.new("RGB", (W, H), RED)
    draw = ImageDraw.Draw(img)

    # Flag stripe at top
    draw.rectangle([0,  0, W, 14],  fill=GOLD)
    draw.rectangle([0, 14, W, 28],  fill=RED)
    draw.rectangle([0, 28, W, 42],  fill=BLACK)

    f_ch = fonts.get(None, 36)
    draw.text((54, 68), "WAS?! DEUTSCH 🇩🇪", font=f_ch, fill=WHITE)

    # FALSCH! header
    f_wr = fonts.get(None, 140)
    wr   = "FALSCH!"
    ww   = _tw(draw, wr, f_wr)
    draw.text(((W - ww) // 2, 210), wr, font=f_wr, fill=BLACK)
    draw.rectangle(
        [(W - ww) // 2, 210 + _th(draw, wr, f_wr) + 4,
         (W - ww) // 2 + ww, 210 + _th(draw, wr, f_wr) + 18],
        fill=GOLD
    )

    # Funny moment
    y      = 490
    funny  = script.get("funny_moment_de", "Überraschung!")
    f_f    = fonts.get(None, 64)
    for line in _wrap(draw, funny, f_f, W - 108):
        lw = _tw(draw, line, f_f)
        draw.text(((W - lw) // 2, y), line, font=f_f, fill=WHITE)
        y += _th(draw, line, f_f) + 14
    y += 30

    # Casual German box
    casual = script.get("casual_german", "")
    note   = script.get("casual_note_de", "")
    if casual:
        draw.rounded_rectangle([54, y, W - 54, y + 220], radius=16, fill=BLACK, outline=GOLD, width=4)
        f_tip = fonts.get(None, 34)
        tip   = "💡 Was Deutsche wirklich sagen:"
        draw.text(((W - _tw(draw, tip, f_tip)) // 2, y + 22), tip, font=f_tip, fill=GOLD)
        f_c2  = fonts.get(None, 42)
        draw.text(((W - _tw(draw, casual, f_c2)) // 2, y + 76), casual, font=f_c2, fill=WHITE)
        if note:
            f_n = fonts.get(None, 32)
            draw.text(((W - _tw(draw, note, f_n)) // 2, y + 136), note, font=f_n, fill=MIDG)
        y += 250

    _flag_stripe(draw, H - 190)

    cta = script.get("cta_de", "Schreib es! 👇")
    f_cta = fonts.get(None, 48)
    draw.text(((W - _tw(draw, cta, f_cta)) // 2, H - 132), cta, font=f_cta, fill=WHITE)

    return img


# ── FRAME 3 — AUTHENTIC ───────────────────────────────────────────────────────
def render_authentic(script: dict) -> Image.Image:
    img  = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    # Gold left bar + red bottom
    draw.rectangle([0,    0, 20, H],       fill=GOLD)
    draw.rectangle([0, H - 20, W, H],      fill=RED)

    # Header
    f_s  = fonts.get(None, 30)
    sec  = "WAS DEUTSCHE WIRKLICH SAGEN"
    draw.text((50, 62), sec, font=f_s, fill=MIDG)
    sw = _tw(draw, sec, f_s)
    draw.rectangle([50, 62 + _th(draw, sec, f_s) + 5, 50 + sw, 62 + _th(draw, sec, f_s) + 8], fill=RED)
    f_ch = fonts.get(None, 34)
    ch   = "WAS?! DEUTSCH 🇩🇪"
    draw.text((W - _tw(draw, ch, f_ch) - 54, 62), ch, font=f_ch, fill=GOLD)
    draw.rectangle([50, 138, W - 50, 142], fill=SMOKE)

    y = 190

    # Textbook line
    f_l = fonts.get(None, 32)
    draw.text((50, y), "📚 LEHRBUCH SAGT:", font=f_l, fill=MIDG)
    y += _th(draw, "X", f_l) + 14
    f_tb = fonts.get(None, 50)
    tb   = (script.get("killian_lines") or ['"Ich möchte Kaffee."'])[0]
    draw.rounded_rectangle([50, y - 10, W - 50, y + _th(draw, tb, f_tb) + 20], radius=10, fill=SMOKE)
    draw.text((76, y), tb, font=f_tb, fill=OFFW)
    y += _th(draw, tb, f_tb) + 50

    # Arrow
    for i in range(4):
        draw.line([W // 2, y + i * 18, W // 2, y + i * 18 + 12], fill=GOLD, width=4)
    draw.polygon(
        [(W // 2 - 18, y + 4 * 18 + 2), (W // 2 + 18, y + 4 * 18 + 2), (W // 2, y + 4 * 18 + 20)],
        fill=GOLD
    )
    y += 90

    # Casual German
    casual = script.get("casual_german", '"Ich hätt gern Kaffee."')
    draw.text((50, y), "🗣️ DEUTSCH SAGT:", font=f_l, fill=GOLD)
    y += _th(draw, "X", f_l) + 14
    f_r  = fonts.get(None, 62)
    rh   = _th(draw, casual, f_r)
    draw.rounded_rectangle([50, y - 10, W - 50, y + rh + 20], radius=10, fill=(28, 20, 0), outline=GOLD, width=3)
    draw.text((76, y), casual, font=f_r, fill=GOLD)
    y += rh + 40

    # Note
    note = script.get("casual_note_de", "")
    if note:
        f_n = fonts.get(None, 38)
        for line in _wrap(draw, note, f_n, W - 120):
            lw = _tw(draw, line, f_n)
            draw.text(((W - lw) // 2, y), line, font=f_n, fill=OFFW)
            y += _th(draw, line, f_n) + 12
        y += 20

    # Speak with Killian
    f_say = fonts.get(None, 46)
    say   = "🎙️ Sag es mit Killian!"
    draw.text(((W - _tw(draw, say, f_say)) // 2, y), say, font=f_say, fill=WHITE)
    y += _th(draw, say, f_say) + 16
    if casual:
        f_big = fonts.get(None, 56)
        draw.text(((W - _tw(draw, casual, f_big)) // 2, y), casual, font=f_big, fill=GOLD)

    cta   = script.get("cta_de", "Klingt das richtig? 👇")
    f_cta = fonts.get(None, 44)
    draw.text(((W - _tw(draw, cta, f_cta)) // 2, H - 118), cta, font=f_cta, fill=WHITE)

    return img


# ── SAVE ─────────────────────────────────────────────────────────────────────
def render_all(script: dict, episode_num: int, fmt: str, out_dir: Path) -> list[Path]:
    """Render all 3 frames, save to out_dir, return list of paths."""
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = [
        ("frame1_hook.png",      render_hook(script, episode_num, fmt)),
        ("frame2_reveal.png",    render_reveal(script)),
        ("frame3_authentic.png", render_authentic(script)),
    ]

    paths = []
    for fname, img in frames:
        p = out_dir / fname
        img.save(str(p))
        paths.append(p)

    return paths
