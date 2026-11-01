"""Animated pixel pieces for the J-J22 profile README (same theme as make_banner.py), dark + light.
    python3 make_assets.py OUT_DIR   ->  OUT_DIR/assets/*.gif
Section headers that type themselves, project cards with animated icons, a quest log, an inventory (stack)
and find-me buttons. Everything is drawn at 1x and scaled 3x with nearest neighbour.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from make_banner import FONT, THEMES, flyers

SCALE = 3
PAD, GRID = 3, 412          # every piece gets PAD px of page bg around it; full-width pieces are GRID wide
EXTRA = {
    "dark": dict(purple="#a371f7", red="#f85149", blue="#58a6ff", blue2="#1f6feb", orange="#d29922", sel="#161b22"),
    "light": dict(purple="#8250df", red="#cf222e", blue="#0969da", blue2="#54aeff", orange="#9a6700", sel="#f6f8fa"),
}
F8 = ImageFont.truetype(FONT, 8)


def canvas(c, w, h):
    im = Image.new("RGB", (w, h), c["bg"])
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    return im, d


def panel(d, c, w, h, outline=None):
    d.rectangle([0, 0, w - 1, h - 1], outline=outline or c["border"])
    for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        d.point((x, y), fill=c["bg"])


def perimeter(w, h):
    return ([(x, 0) for x in range(1, w - 1)] + [(w - 1, y) for y in range(1, h - 1)] +
            [(x, h - 1) for x in range(w - 2, 0, -1)] + [(0, y) for y in range(h - 2, 0, -1)])


def border_glint(d, c, w, h, f, frames, col):
    pts = perimeter(w, h)
    head = int(f / frames * len(pts))
    for k in range(14):
        d.point(pts[(head - k) % len(pts)], fill=col)


def text(d, xy, s, col):
    """Char by char on the 8px grid, so the renderer can't merge glyphs (it turned 'fi' into a ligature)."""
    x, y = xy
    for i, ch in enumerate(s):
        d.text((x + 8 * i, y), ch, font=F8, fill=col)


def save(frames, path, durations, start=0):
    """Pads, scales and writes; `start` rotates the loop so frame 0 (what shows when autoplay is off) is complete."""
    frames = frames[start:] + frames[:start]
    if isinstance(durations, list):
        durations = durations[start:] + durations[:start]
    out = []
    for im in frames:
        bg = Image.new("RGB", (im.width + 2 * PAD, im.height + 2 * PAD), im.getpixel((0, 0)))
        bg.paste(im, (PAD, PAD))
        out.append(bg)
    frames = [im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST) for im in out]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True,
                   disposal=1)


def draw_map(d, rows, x, y, px, colors):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colors:
                d.rectangle([x + i * px, y + j * px, x + i * px + px - 1, y + j * px + px - 1], fill=colors[ch])


# ---------- icons (drawn inside a ~44x44 box at x, y) ----------

BUTTERFLY_OPEN = ["X.........X", "XX.......XX", "XXX.....XXX", "XXXX.B.XXXX", ".XXXXBXXXX.",
                  "..XXXBXXX..", ".XXX.B.XXX.", "XX...B...XX"]
BUTTERFLY_SHUT = ["...........", "...X...X...", "...XX.XX...", "....XBX....", "....XBX....",
                  "....XBX....", "...XXBXX...", "...X.B.X..."]


def icon_butterfly(d, c, e, f, x, y):          # hell butterfly for ReiatsuFlow
    rows = BUTTERFLY_OPEN if (f // 4) % 2 == 0 else BUTTERFLY_SHUT
    bob = round(math.sin(f / 48 * math.tau * 2) * 1.5)
    draw_map(d, rows, x + 5, y + 8 + bob * 3, 3, {"X": e["purple"], "B": c["muted"]})
    t = (f % 24) / 24                             # one reiatsu mote trailing below it
    d.point((x + 22 + round(math.sin(t * math.tau) * 3), y + 44 - int(t * 10)), fill=c["spark"])


HEART = [".XX...XX.", "XXXX.XXXX", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."]


def icon_heart(d, c, e, f, x, y):              # beating heart for Smriti (lub-dub, rest)
    big = (f % 24) in (0, 1, 2, 5, 6)
    if big:
        draw_map(d, HEART, x + 4, y + 6, 4, {"X": e["red"]})
    else:
        draw_map(d, HEART, x + 9, y + 10, 3, {"X": e["red"]})
    d.point((x + 14 if big else x + 15, y + 12 if big else y + 14), fill=c["glint"])


EYE = ["....XXXXX....", "..XX.....XX..", ".X.........X.", "X...........X", ".X.........X.", "..XX.....XX..",
       "....XXXXX...."]


def icon_eye(d, c, e, f, x, y):                # Vision: looks around and blinks
    ox, oy = x + 2, y + 12
    g = f % 48
    if 40 <= g <= 42:
        d.rectangle([ox, oy + 9, ox + 38, oy + 11], fill=e["blue"])
        return
    draw_map(d, EYE, ox, oy, 3, {"X": e["blue"]})
    look = 0 if g < 12 else (-2 if g < 24 else (2 if g < 36 else 0))
    cx = ox + 18 + look * 3
    d.rectangle([cx - 6, oy + 4, cx + 6, oy + 16], fill=e["blue2"])
    d.rectangle([cx - 2, oy + 7, cx + 2, oy + 13], fill=c["bg"])
    d.point((cx + 3, oy + 6), fill=c["glint"])


def icon_monitor(d, c, e, f, x, y):            # portfolio: a monitor typing code
    ox, oy = x + 2, y + 8
    d.rectangle([ox, oy, ox + 39, oy + 23], outline=e["orange"], width=2)
    d.rectangle([ox + 17, oy + 24, ox + 22, oy + 27], fill=e["orange"])
    d.rectangle([ox + 11, oy + 28, ox + 28, oy + 29], fill=e["orange"])
    g = f % 48
    lens = [7, 11, 5, 9]
    typed = g * 1.2
    for k, n in enumerate(lens):
        m = int(min(n, max(0, typed - sum(lens[:k]))))
        if m:
            col = c["accent"] if k % 2 == 0 else c["muted"]
            indent = 0 if k % 3 == 0 else 2
            d.line([ox + 4 + indent * 2, oy + 4 + k * 4, ox + 4 + indent * 2 + m * 2, oy + 4 + k * 4], fill=col)
    if (f // 3) % 2 == 0:
        d.rectangle([ox + 33, oy + 17, ox + 35, oy + 19], fill=c["accent"])


# ---------- pieces ----------

def header(c, e, label, seed):
    """Full-width strip: '> label' types in, cursor blinks, a hell butterfly flows across in front of it."""
    s = "> " + label
    w, h, n = GRID - 2 * PAD, 14, 100
    frames = []
    for f in range(n):
        im, d = canvas(c, w, h)
        k = min(f, len(s))
        text(d, (2, 3), s[:2][:k], c["accent"])
        text(d, (18, 3), s[2:k], c["text"])
        if k < len(s) or (f // 6) % 2 == 0:
            cx = 2 + 8 * k
            d.rectangle([cx + 1, 3, cx + 6, 10], fill=c["accent"])
        flyers(d, c, f, n, w, [(3, (seed * 0.37) % 1, 2, 0.8, 1)])
        frames.append(im)
    return frames, 70


CARDS = [
    ("reiatsuflow", "ReiatsuFlow", "study planner", "for linux", "qml, quickshell", icon_butterfly, "purple"),
    ("smriti", "Smriti", "offline app for", "dementia care", "js, sih 2026", icon_heart, "red"),
    ("vision", "Vision", "ai agents, idea", "to deployment", "ts, ju finals", icon_eye, "blue"),
    ("portfolio", "Portfolio", "my pixel site", "bleach themed", "css, live", icon_monitor, "orange"),
]


def card(c, e, title, l1, l2, tags, icon, colkey):
    w, h, n = 200, 56, 96
    frames = []
    for f in range(n):
        im, d = canvas(c, w, h)
        panel(d, c, w, h)
        border_glint(d, c, w, h, f, n, e[colkey])
        icon(d, c, e, f, 4, 5)
        text(d, (52, 7), title, e[colkey])
        text(d, (52, 20), l1, c["text"])
        text(d, (52, 30), l2, c["text"])
        text(d, (52, 43), tags, c["muted"])
        flyers(d, c, f, n, w, [(4 + len(title) * 5 % 38, (len(title) * 0.29) % 1, 3, 0.45, 1)])
        frames.append(im)
    return frames, 80


QUESTS = [("AWS SAA", "feb 2027"), ("Leetcode 500", "target"), ("hackathon build", "dec 2026"),
          ("http server", "on the side")]


def quest_log(c, e):
    w, h, n = GRID - 2 * PAD, 66, 144
    frames = []
    for f in range(n):
        im, d = canvas(c, w, h)
        panel(d, c, w, h)
        sel = (f // 12) % 4
        for k, (q, when) in enumerate(QUESTS):
            y = 5 + k * 15
            if k == sel:
                d.rectangle([3, y - 2, w - 4, y + 10], fill=e["sel"])
                text(d, (6, y + 1), ">", c["accent"])
            if (f // 3 + k) % 4:
                text(d, (18, y + 1), "!", e["orange"])
            text(d, (32, y + 1), q, c["text"] if k == sel else c["muted"])
            text(d, (w - 8 - 8 * len(when), y + 1), when, c["accent"] if k == sel else c["muted"])
        flyers(d, c, f, n, w, [(10, 0.2, 4, 0.45, 1), (44, 0.7, 4, 0.4, 1)])
        frames.append(im)
    return frames, 90


STACK = ["python", "c++", "c", "java", "bash", "git", "aws", "linux"]
TARGETS = ["Leetcode 500", "AWS SAA"]


def chip(d, c, x, y, s, lit, pad=6, col=None):
    w = 8 * len(s) + pad
    d.rectangle([x, y, x + w - 1, y + 13], outline=(col or c["accent"]) if lit else c["border"])
    text(d, (x + (w - 8 * len(s)) // 2, y + 3), s, col or c["text"])
    return x + w + 4


def inventory(c, e):
    w, h = GRID - 2 * PAD, 62
    total = len(STACK) + len(TARGETS)
    n = total * 12
    frames = []
    for f in range(n):
        im, d = canvas(c, w, h)
        panel(d, c, w, h)
        lit = (f // 4) % total
        # row 1 stretched to the panel width: spare space goes into the chips' inner padding
        spare = (w - 12) - sum(8 * len(s) + 6 for s in STACK) - 4 * (len(STACK) - 1)
        x = 6
        for k, s in enumerate(STACK):
            extra = spare // len(STACK) + (1 if k < spare % len(STACK) else 0)
            x = chip(d, c, x, 4, s, k == lit, pad=6 + extra)
        text(d, (6, 26), "target", e["orange"])
        x = 62
        spare2 = (w - 6 - x) - sum(8 * len(s) + 6 for s in TARGETS) - 4 * (len(TARGETS) - 1)
        for k, s in enumerate(TARGETS):          # goals, in quest-marker orange, stretched to the panel edge
            x = chip(d, c, x, 22, s, len(STACK) + k == lit, pad=6 + spare2 // len(TARGETS), col=e["orange"])
        text(d, (6, 46), "rig", c["accent"])
        text(d, (38, 46), "arch + hyprland, bleach rice", c["muted"])
        flyers(d, c, f, n, w, [(20, 0.4, 4, 0.45, 1), (46, 0.9, 3, 0.4, 1)])
        frames.append(im)
    return frames, 110


BUTTONS = [("linkedin", "linkedin"), ("portfolio", "portfolio"), ("email", "email")]


def button(c, e, label):
    w, h, n = 8 * len(label) + 24, 18, 40
    frames = []
    for f in range(n):
        im, d = canvas(c, w, h)
        panel(d, c, w, h)
        border_glint(d, c, w, h, f, n, c["accent"])
        text(d, (5, 5), ">", c["accent"])
        text(d, (17, 5), label, c["text"])
        frames.append(im)
    return frames, 70


def main(out):
    a = out / "assets"
    a.mkdir(parents=True, exist_ok=True)
    for th in THEMES:
        c, e = THEMES[th], EXTRA[th]
        for label in ("projects", "quest log", "inventory", "contributions", "find me"):
            fr, du = header(c, e, label, len(label) * 7 + ord(label[0]))
            save(fr, a / f"h-{label.replace(' ', '-')}-{th}.gif", du, start=len(label) + 3)
        for key, *rest in CARDS:
            fr, du = card(c, e, *rest)
            save(fr, a / f"card-{key}-{th}.gif", du)
        fr, du = quest_log(c, e)
        save(fr, a / f"quests-{th}.gif", du)
        fr, du = inventory(c, e)
        save(fr, a / f"inventory-{th}.gif", du)
        for key, label in BUTTONS:
            fr, du = button(c, e, label)
            save(fr, a / f"btn-{key}-{th}.gif", du)
    print("ok")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
