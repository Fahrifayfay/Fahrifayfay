#!/usr/bin/env python3
"""Generate animated, font-embedded (as vector paths) SVG assets for a GitHub profile README.

Text is converted to <path> outlines, so the font renders identically on GitHub
(SVGs inside <img> cannot load web fonts).
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "profile")
os.makedirs(OUT, exist_ok=True)

POPPINS_BOLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Poppins-Bold.ttf")
POPPINS_MED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Poppins-Medium.ttf")
MONO_BOLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSansMono-Bold.ttf")

_fonts = {}


def font(path):
    if path not in _fonts:
        f = TTFont(path)
        _fonts[path] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, f["hmtx"])
    return _fonts[path]


def layout(text, path, size, tracking=0.0):
    """Return ([(char, d, x_offset)], total_width). Paths are drawn at baseline y=0."""
    f, gs, cmap, upm, hmtx = font(path)
    s = size / upm
    x = 0.0
    glyphs = []
    for ch in text:
        gname = cmap.get(ord(ch))
        adv = hmtx[gname][0] * s if gname else size * 0.3
        d = ""
        if gname and ch != " ":
            pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
            gs[gname].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
            d = pen.getCommands()
        glyphs.append((ch, d, x, adv))
        x += adv + tracking
    return glyphs, x - tracking


THEME_CSS = """
:root{--fg:#f4f4f5;--dim:#8b8b93;--acc:#b9a7ff;--line:#3a3a42;--g1:#8b5cf6;--g2:#c6e04a}
@media (prefers-color-scheme: light){
:root{--fg:#111114;--dim:#6b6b73;--acc:#6d28d9;--line:#c9c9d1;--g1:#7c3aed;--g2:#7f9a12}}
"""


def svg_wrap(w, h, body, css="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img">\n<defs>{defs}</defs>\n<style>{THEME_CSS}{css}</style>\n{body}\n</svg>\n'
    )


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", name, len(content) // 1024, "KB")


# ---------------------------------------------------------------- headings
CYCLE = 8.0  # seconds, full loop

HEAD_CSS = f"""
.l{{opacity:0;transform-box:fill-box;transform-origin:50% 100%;
animation:rise {CYCLE}s cubic-bezier(.2,.8,.2,1) infinite both}}
@keyframes rise{{
0%{{opacity:0;transform:translateY(26px) scale(.82) skewX(-8deg)}}
9%{{opacity:1;transform:translateY(-3px) scale(1.03) skewX(0)}}
12%{{opacity:1;transform:translateY(0) scale(1) skewX(0)}}
86%{{opacity:1;transform:translateY(0) scale(1)}}
94%,100%{{opacity:0;transform:translateY(-10px) scale(.96)}}}}
.gA,.gB{{opacity:0;animation:glitchA {CYCLE}s steps(1,end) infinite}}
.gB{{animation-name:glitchB}}
@keyframes glitchA{{
0%,34%{{opacity:0;transform:translate(0,0)}}
34.4%{{opacity:.75;transform:translate(-4px,1px)}}
35.2%{{opacity:.75;transform:translate(3px,-1px)}}
36%{{opacity:0;transform:translate(0,0)}}
64%{{opacity:0}}
64.4%{{opacity:.7;transform:translate(-2px,0)}}
65%{{opacity:0}}
100%{{opacity:0}}}}
@keyframes glitchB{{
0%,34%{{opacity:0;transform:translate(0,0)}}
34.4%{{opacity:.75;transform:translate(4px,-1px)}}
35.2%{{opacity:.75;transform:translate(-3px,1px)}}
36%{{opacity:0;transform:translate(0,0)}}
64%{{opacity:0}}
64.4%{{opacity:.7;transform:translate(2px,0)}}
65%{{opacity:0}}
100%{{opacity:0}}}}
.rule{{stroke:var(--fg);stroke-width:2;stroke-linecap:round;fill:none;
stroke-dasharray:var(--len);stroke-dashoffset:var(--len);
animation:draw {CYCLE}s cubic-bezier(.6,0,.2,1) infinite both}}
@keyframes draw{{
0%,8%{{stroke-dashoffset:var(--len);opacity:1}}
24%{{stroke-dashoffset:0;opacity:1}}
86%{{stroke-dashoffset:0;opacity:1}}
94%,100%{{stroke-dashoffset:0;opacity:0}}}}
.lab{{opacity:0;animation:lab {CYCLE}s ease-out infinite both}}
@keyframes lab{{
0%,2%{{opacity:0;transform:translateX(-14px)}}
12%{{opacity:1;transform:translateX(0)}}
86%{{opacity:1}}
94%,100%{{opacity:0}}}}
.dot{{fill:var(--acc);animation:pulse 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes pulse{{0%,100%{{opacity:.35;transform:scale(.7)}}50%{{opacity:1;transform:scale(1.15)}}}}
"""


def glyph_layers(glyphs, base_x, base_y, stagger, start_delay, cls_for=None):
    """Build 3 layers (main + 2 glitch layers) of per-letter animated paths."""
    def layer(cls, fill_default, with_class):
        parts = []
        k = 0
        for i, (ch, d, x, adv) in enumerate(glyphs):
            if not d:
                continue
            delay = start_delay + k * stagger
            k += 1
            fill = fill_default
            if cls_for and with_class:
                c = cls_for(i)
                if c:
                    fill = c
            parts.append(
                f'<g transform="translate({base_x + x:.2f},{base_y})">'
                f'<path class="l" style="animation-delay:{delay:.2f}s" fill="{fill}" d="{d}"/></g>'
            )
        return f'<g class="{cls}">' + "".join(parts) + "</g>" if cls else "".join(parts)

    return (
        layer("gB", "var(--g2)", False)
        + layer("gA", "var(--g1)", False)
        + layer("", "var(--fg)", True)
    )


def section_heading(name, index, title):
    W, H = 900, 140
    size = 58
    glyphs, tw = layout(title.upper(), POPPINS_BOLD, size, tracking=5)
    bx = (W - tw) / 2
    by = 100
    body = []
    # small mono label with accent dot
    lab_glyphs, lw = layout(f"// {index}", MONO_BOLD, 15, tracking=4)
    body.append(
        f'<g transform="translate({W/2 - lw/2:.2f},30)"><g class="lab">'
        + "".join(
            f'<g transform="translate({x:.2f},0)"><path fill="var(--dim)" d="{d}"/></g>'
            for ch, d, x, adv in lab_glyphs
            if d
        )
        + "</g></g>"
    )
    body.append(glyph_layers(glyphs, bx, by, stagger=0.045, start_delay=0.15))
    # animated rule with end dots, draws from center outward
    half = min(tw / 2, 260)
    body.append(
        f'<path class="rule" style="--len:{half:.0f}" d="M{W/2:.1f} 122 H{W/2 + half:.1f}"/>'
        f'<path class="rule" style="--len:{half:.0f}" d="M{W/2:.1f} 122 H{W/2 - half:.1f}"/>'
        f'<rect class="dot" x="{W/2 - 4:.1f}" y="118" width="8" height="8" transform="rotate(45 {W/2:.1f} 122)"/>'
    )
    write(name, svg_wrap(W, H, "\n".join(body), HEAD_CSS))


def sub_heading(name, title):
    W, H = 900, 64
    size = 24
    glyphs, tw = layout(title.upper(), POPPINS_MED, size, tracking=7)
    bx = (W - tw) / 2
    by = 40
    gap = 26
    body = [glyph_layers(glyphs, bx, by, stagger=0.05, start_delay=0.15)]
    L = 150
    body.append(
        f'<path class="rule" style="--len:{L}" d="M{bx - gap:.1f} 31 H{bx - gap - L:.1f}" />'
        f'<path class="rule" style="--len:{L}" d="M{bx + tw + gap:.1f} 31 H{bx + tw + gap + L:.1f}" />'
    )
    css = HEAD_CSS.replace("stroke-width:2", "stroke-width:1.5")
    write(name, svg_wrap(W, H, "\n".join(body), css))


def hey_heading(name):
    text = "Hey there! I'm Fahri"
    size = 44
    glyphs, tw = layout(text, POPPINS_BOLD, size, tracking=0.5)
    W, H = int(tw) + 20, 82
    by = 58
    start = text.index("Fahri")

    def cls_for(i):
        return "var(--acc)" if i >= start else None

    body = [glyph_layers(glyphs, 4, by, stagger=0.06, start_delay=0.1, cls_for=cls_for)]
    body.append(
        f'<path class="rule" style="--len:{tw:.0f}" d="M4 74 H{tw + 4:.0f}" />'
    )
    css = HEAD_CSS.replace("stroke-width:2", "stroke-width:2.5")
    write(name, svg_wrap(W, H, "\n".join(body), css))


# ---------------------------------------------------------------- tagline (typewriter)
def tagline(name):
    text = "Still learning. Still building. Still improving."
    size = 23
    f, gs, cmap, upm, hmtx = font(MONO_BOLD)
    adv = hmtx[cmap[ord("a")]][0] * size / upm
    tracking = 1.2
    step = adv + tracking
    n = len(text)
    tw = n * step - tracking
    W, H = 900, 84
    x0 = (W - tw) / 2
    by = 50
    glyphs, _ = layout(text, MONO_BOLD, size, tracking=tracking)

    # which chars are the dim word "Still"
    dim_idx = set()
    for word_start in [0, 16, 32]:
        for k in range(5):
            dim_idx.add(word_start + k)
    paths = []
    for i, (ch, d, x, a) in enumerate(glyphs):
        if not d:
            continue
        fill = "var(--dim)" if i in dim_idx else "var(--fg)"
        paths.append(
            f'<g transform="translate({x0 + x:.2f},{by})"><path fill="{fill}" d="{d}"/></g>'
        )

    # frames: (time fraction, chars shown)
    frames = [(0.0, 0)]
    t0, t1 = 0.05, 0.40
    for i in range(1, n + 1):
        frames.append((t0 + (t1 - t0) * i / n, i))
    e0, e1 = 0.86, 0.95
    k = 12
    for j in range(1, k + 1):
        frames.append((e0 + (e1 - e0) * j / k, max(0, round(n * (1 - j / k)))))
    frames.append((1.0, 0))
    # dedupe monotonic times
    times = []
    for t, c in frames:
        if times and t <= times[-1][0]:
            t = times[-1][0] + 1e-4
        times.append((t, c))
    dur = 9.0
    kt = ";".join(f"{t:.4f}" for t, c in times)
    wv = ";".join(f"{x0 + c * step:.2f}" for t, c in times)
    cur = ";".join(f"{x0 + c * step + 1:.2f}" for t, c in times)
    clip = (
        f'<clipPath id="reveal"><rect x="0" y="0" height="{H}" width="0">'
        f'<animate attributeName="width" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{kt}" values="{";".join(f"{x0 + c * step - tracking / 2 if c else 0:.2f}" for t, c in times)}"/>'
        f"</rect></clipPath>"
    )
    body = (
        f'<g clip-path="url(#reveal)">{"".join(paths)}</g>'
        f'<rect y="{by - size * 0.78:.1f}" width="3" height="{size * 0.98:.1f}" rx="1.5" fill="var(--acc)" x="{x0:.2f}">'
        f'<animate attributeName="x" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{cur}"/>'
        f'<animate attributeName="opacity" dur="0.9s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.55" values="1;0"/>'
        f"</rect>"
    )
    write(name, svg_wrap(W, H, body, "", clip))


# ---------------------------------------------------------------- divider line
def divider(name):
    W, H = 900, 26
    css = """
.pulse{animation:none}
"""
    defs = (
        '<linearGradient id="g" x1="0" x2="1" y1="0" y2="0">'
        '<stop offset="0" stop-color="var(--acc)" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="var(--acc)" stop-opacity="1"/>'
        '<stop offset="1" stop-color="var(--acc)" stop-opacity="0"/></linearGradient>'
    )
    body = (
        f'<line x1="0" y1="13" x2="{W}" y2="13" stroke="var(--line)" stroke-width="1"/>'
        f'<rect x="-220" y="12" width="220" height="2" rx="1" fill="url(#g)">'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{W + 220} 0" '
        f'dur="4.5s" repeatCount="indefinite"/></rect>'
        f'<g transform="translate({W/2},13)"><rect x="-5" y="-5" width="10" height="10" transform="rotate(45)" '
        f'fill="none" stroke="var(--fg)" stroke-width="1.5">'
        f'<animateTransform attributeName="transform" type="rotate" from="45" to="405" dur="9s" repeatCount="indefinite"/>'
        f"</rect></g>"
    )
    write(name, svg_wrap(W, H, body, css, defs))


# ---------------------------------------------------------------- social pills
def pill(name, label, accent_delay=0.0):
    size = 17
    glyphs, tw = layout(label.upper(), POPPINS_BOLD, size, tracking=3.5)
    W, H = int(tw) + 64, 48
    rx = H / 2 - 2
    perim = 2 * (W - 4 - 2 * rx) + 2 * 3.14159 * rx
    css = f"""
.p{{opacity:0;animation:pin 6s ease-out infinite both;animation-delay:{accent_delay}s}}
@keyframes pin{{0%{{opacity:0;transform:translateY(10px)}}8%,100%{{opacity:1;transform:translateY(0)}}}}
.trace{{fill:none;stroke:var(--acc);stroke-width:2;stroke-linecap:round;
stroke-dasharray:{perim * 0.22:.0f} {perim * 0.78:.0f};animation:run 3.2s linear infinite;animation-delay:{accent_delay}s}}
@keyframes run{{to{{stroke-dashoffset:-{perim:.0f}}}}}
.base{{fill:none;stroke:var(--line);stroke-width:1.5}}
"""
    letters = "".join(
        f'<g transform="translate({32 + x:.2f},{H/2 + size*0.36:.2f})"><path fill="var(--fg)" d="{d}"/></g>'
        for ch, d, x, adv in glyphs
        if d
    )
    body = (
        f'<g class="p"><rect class="base" x="2" y="2" width="{W-4}" height="{H-4}" rx="{rx}"/>'
        f'<rect class="trace" x="2" y="2" width="{W-4}" height="{H-4}" rx="{rx}"/>'
        f"{letters}</g>"
    )
    write(name, svg_wrap(W, H, body, css))


if __name__ == "__main__":
    section_heading("h-about.svg", "01 / about", "Know About Me")
    section_heading("h-projects.svg", "02 / work", "Top Projects")
    section_heading("h-stack.svg", "03 / tools", "Tech Stack")
    section_heading("h-connect.svg", "04 / reach out", "Connect")
    section_heading("h-contrib.svg", "05 / activity", "Contribution")
    sub_heading("l-dev.svg", "Development")
    sub_heading("l-design.svg", "Design & Cloud")
    hey_heading("h-hey.svg")
    tagline("tagline.svg")
    divider("line.svg")
    pill("github.svg", "GitHub", 0.0)
    pill("instagram.svg", "Instagram", 0.25)
    pill("email.svg", "Email", 0.5)
    pill("tiktok.svg", "TikTok", 0.75)
