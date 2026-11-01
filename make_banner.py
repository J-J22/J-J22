"""Animated pixel banner for the J-J22 GitHub profile, GitHub colours, dark + light.

A ~14 s loop told in scenes:
  intro    the blade draws out of the guard, 'JoC' / name / college type themselves in, the graph fills up
  idle     glint runs up the blade, reiatsu motes rise, a light wave rolls over the graph,
           a '>' ticker types and erases what I'm on right now
  charge   reiatsu aura flickers around the blade
  slash    a crescent slash sweeps across the banner, flash + screen shake, embers fall
  outro    everything erases and the blade goes back in, so the loop restarts cleanly

Drawn at 320x80, scaled 4x with nearest neighbour -> 1280x320 GIFs.
    python3 make_banner.py OUT_DIR   ->  banner-dark.gif, banner-light.gif
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

FONT = str(Path.home() / "Projects/reiatsuflow/ui/fonts/PressStart2P.ttf")
W, H, SCALE, FRAMES, MS = 320, 80, 4, 200, 70

# timeline (frame numbers)
OUT = 180                      # outro starts: erase + retract
CHARGE, SLASH, SLASH_LEN = 106, 120, 7
TICKER_START, TICKER_SLOT = 44, 33
TICKER = ["studying aws saa", "dsa in c++", "hackathon build", "ricing arch"]

THEMES = {
    "dark": dict(bg="#0d1117", dot="#161b22", border="#30363d", text="#e6edf3", muted="#8b949e", accent="#3fb950",
                 levels=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"], wave="#7ee787",
                 blade="#c9d1d9", edge="#f0f6fc", spine="#6e7681", glint="#ffffff", guard="#d29922",
                 wrap="#30363d", wrap2="#8b949e", pommel="#d29922", spark="#3fb950",
                 slash_core="#ffffff", slash_glow="#3fb950", flash="#12261a"),
    "light": dict(bg="#ffffff", dot="#eaeef2", border="#d0d7de", text="#1f2328", muted="#59636e", accent="#1a7f37",
                  levels=["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"], wave="#0f5323",
                  blade="#8c959f", edge="#d0d7de", spine="#424a53", glint="#ffffff", guard="#9a6700",
                  wrap="#24292f", wrap2="#8c959f", pommel="#9a6700", spark="#1a7f37",
                  slash_core="#116329", slash_glow="#4ac26b", flash="#dafbe1"),
}

GUARD = (30, 55)               # zanpakutō, diagonal: hilt bottom-left, tip top-right
BLADE_LEN = 41


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def typed(s, f, start, rate=1.0, erase=2.0):
    """Prefix of s visible at frame f: types in from `start`, erases from OUT."""
    n = clamp(int((f - start) * rate), 0, len(s))
    if f >= OUT:
        n = min(n, clamp(len(s) - int((f - OUT) * erase), 0, len(s)))
    return s[:n]


def blade_len(f):
    if f >= OUT:
        return clamp(int(BLADE_LEN * (1 - (f - OUT) / 14)), 0, BLADE_LEN)
    return clamp(int(f * BLADE_LEN / 12), 0, BLADE_LEN)


def blade_points():
    return [(GUARD[0] + 5 + i, GUARD[1] - 5 - i) for i in range(BLADE_LEN)]


def sword(d, c, f):
    bx, by = GUARD
    pts = blade_points()
    n = blade_len(f)
    for x, y in pts[:n]:                                  # blade: dark spine, body, bright cutting edge
        d.point((x - 1, y - 1), fill=c["spine"])
        d.point((x - 1, y), fill=c["spine"])
        d.rectangle([x, y, x + 1, y + 1], fill=c["blade"])
        d.point((x + 2, y + 1), fill=c["edge"])
        d.point((x + 1, y + 2), fill=c["edge"])
    if n == BLADE_LEN:
        tx, ty = pts[-1]
        d.rectangle([tx + 1, ty - 2, tx + 2, ty - 1], fill=c["edge"])
    for k in range(-6, 7):                                # tsuba
        d.rectangle([bx + k, by + k - 1, bx + k + 2, by + k + 1], fill=c["guard"])
    for i in range(2, 17):                                # tsuka with diamond wrap
        x, y = bx - i, by + i
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=c["wrap2"] if i % 3 == 0 else c["wrap"])
    d.rectangle([bx - 19, by + 16, bx - 16, by + 19], fill=c["pommel"])

    # glint: runs guard -> tip every 40 frames while the blade is fully out (not during the charge/slash)
    if n == BLADE_LEN and not (CHARGE <= f < SLASH + 20):
        g = (f - 30) % 40
        if f >= 30 and g < 16:
            gi = int(g / 15 * (BLADE_LEN - 1))
            for k in (0, -1, 1, -2):
                j = gi + k
                if 0 <= j < BLADE_LEN:
                    x, y = pts[j]
                    d.point((x, y), fill=c["glint"])
                    if k in (0, -1, 1):
                        d.point((x + 1, y + 1), fill=c["glint"])

    # charge: flickering reiatsu aura hugging the blade, growing until the slash
    if CHARGE <= f < SLASH:
        reach = (f - CHARGE) / (SLASH - CHARGE)
        for i, (x, y) in enumerate(pts):
            if i / BLADE_LEN > reach + 0.15 or (i + f) % 3 == 0:
                continue
            off = 3 + ((i * 7 + f) % 3 == 0)
            d.point((x - off, y - off), fill=c["spark"])
            d.point((x + off + 1, y + off + 1), fill=c["spark"])


def sparks(d, c, f, motes):
    """Reiatsu motes rising around the blade; period 50 frames so the 200-frame loop is seamless."""
    fast = CHARGE <= f < SLASH
    for x0, y0, ph, drift in motes:
        t = ((f / 50) * (2 if fast else 1) + ph) % 1
        y = int(y0 - t * 34)
        x = int(x0 + drift * math.sin(t * math.tau))
        if t < 0.85:
            d.point((x, y), fill=c["spark"])
            if t < 0.4:
                d.point((x + 1, y), fill=c["spark"])


# slash: crescent arc over the banner, sweeping left -> right
ARC_C, ARC_R = (160, 112), 92
A0, A1 = math.radians(158), math.radians(22)


def arc_xy(a, r):
    return ARC_C[0] + r * math.cos(a), ARC_C[1] - r * math.sin(a)


def slash(d, c, f, embers):
    t = (f - SLASH) / SLASH_LEN
    if 0 <= t <= 1.4:
        head = A0 + (A1 - A0) * min(t, 1)
        tail = A0 + (A1 - A0) * clamp(t - 0.55, 0, 1)
        steps = 140
        for s in range(steps + 1):
            a = tail + (head - tail) * s / steps
            u = s / steps                                  # 0 at tail, 1 at head
            thick = 0.5 + 4.5 * math.sin(math.pi * clamp(u * 0.9 + 0.1, 0, 1))
            for dr in range(-int(thick) - 1, int(thick) + 2):
                x, y = arc_xy(a, ARC_R + dr)
                col = c["slash_core"] if abs(dr) <= thick * 0.45 else c["slash_glow"]
                d.point((int(x), int(y)), fill=col)
    # embers drift down from the arc after it passes
    et = f - (SLASH + SLASH_LEN - 2)
    if 0 <= et < 30:
        for a, r, vx, life in embers:
            if et < life:
                x, y = arc_xy(a, r)
                d.point((int(x + vx * et), int(y + 0.6 * et + 0.03 * et * et)), fill=c["spark"])


def contributions(d, c, f, x0, y0, cols, grid):
    wave = ((f % 100) / 100) * (cols + 10) - 5
    shown = clamp(int((f - 4) * 0.9), 0, cols)            # intro: fill column by column
    gone = clamp(int((f - OUT) * 1.4), 0, cols) if f >= OUT else 0
    for col in range(cols):
        for r in range(7):
            lvl = grid[col][r] if gone <= col < shown else 0
            fill = c["levels"][lvl]
            if lvl and abs(col - wave) < 1.5:
                fill = c["wave"]
            x, y = x0 + col * 3, y0 + r * 3
            d.rectangle([x, y, x + 1, y + 1], fill=fill)


def ticker(f):
    """'> phrase' line: each phrase types, holds, erases inside its slot."""
    if not (TICKER_START <= f < TICKER_START + TICKER_SLOT * len(TICKER)):
        return "", False
    k, g = divmod(f - TICKER_START, TICKER_SLOT)
    s = TICKER[k]
    n = min(len(s), int(g * 1.6))
    end = TICKER_SLOT - 6
    if g >= end:
        n = max(0, len(s) - (g - end) * 3)
    return s[:n], g < end


def frame(c, f, motes, grid, embers):
    flash = SLASH + 3 <= f <= SLASH + 4
    im = Image.new("RGB", (W, H), c["flash"] if flash else c["bg"])
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    for y in range(4, H, 8):
        for x in range(4, W, 8):
            d.point((x, y), fill=c["dot"])
    sparks(d, c, f, motes)
    sword(d, c, f)

    big = ImageFont.truetype(FONT, 24)
    small = ImageFont.truetype(FONT, 8)
    name = typed("JoC", f, 2, rate=0.25, erase=0.4)
    d.text((92, 10), name, font=big, fill=c["text"])
    typing_name = f < 14 or f >= OUT
    if name and (typing_name or (f // 6) % 2 == 0):       # block cursor, solid while typing, blinks otherwise
        cx = 92 + 24 * len(name)
        d.rectangle([cx, 12, cx + 11, 33], fill=c["accent"])
    d.text((92, 40), typed("jaiwardhan joshi", f, 12), font=small, fill=c["muted"])
    d.text((92, 52), typed("cse @ jecrc, jaipur", f, 22), font=small, fill=c["muted"])
    tick, holding = ticker(f)
    if tick or TICKER_START <= f < OUT:
        d.text((92, 66), ">", font=small, fill=c["accent"])
        d.text((108, 66), tick, font=small, fill=c["text"])
        if not holding or (f // 4) % 2 == 0:
            cx = 108 + 8 * len(tick)
            d.rectangle([cx, 66, cx + 5, 73], fill=c["accent"])

    contributions(d, c, f, 256, 12, 20, grid)
    d.text((256, 38), typed("linux", f, 30), font=small, fill=c["accent"])
    d.text((256, 50), typed("c++", f, 34), font=small, fill=c["muted"])
    d.text((256, 62), typed("aws", f, 37), font=small, fill=c["muted"])

    slash(d, c, f, embers)

    shake = {SLASH + 3: 2, SLASH + 4: -2, SLASH + 5: 1, SLASH + 6: -1}.get(f, 0)
    if shake:
        im = ImageChops.offset(im, shake, shake // 2)
        d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=c["border"])
    return im.resize((W * SCALE, H * SCALE), Image.NEAREST)


def build(name, out):
    c = THEMES[name]
    rng = random.Random(22)
    motes = [(rng.randint(14, 82), rng.randint(36, 76), rng.random(), rng.uniform(1, 3)) for _ in range(18)]
    grid = [[(0 if rng.random() < 0.3 - col * 0.008 else min(4, int(rng.random() * 3 + col / 9)))
             for _ in range(7)] for col in range(21)]
    embers = [(A0 + (A1 - A0) * rng.random(), ARC_R + rng.randint(-2, 2), rng.uniform(-0.3, 0.3),
               rng.randint(10, 30)) for _ in range(40)]
    frames = [frame(c, f, motes, grid, embers) for f in range(FRAMES)]
    frames[0].save(out / f"banner-{name}.gif", save_all=True, append_images=frames[1:], duration=MS, loop=0,
                   optimize=True, disposal=1)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    for n in THEMES:
        build(n, out)
    print("ok")
