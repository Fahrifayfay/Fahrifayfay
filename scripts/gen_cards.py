#!/usr/bin/env python3
"""Intro card (character + name), project cards, and small captions.

Run:  python scripts/gen_cards.py
Edit the PROJECTS list below to change card text, then re-run and commit the SVGs.
"""
import base64
import os

import gen_static_assets as g
from gen_static_assets import (HEAD_CSS, MONO_BOLD, POPPINS_BOLD, glyph_layers,
                               layout, svg_wrap, write)

HERE = os.path.dirname(os.path.abspath(__file__))
POPPINS_REG = os.path.join(HERE, "fonts", "Poppins-Regular.ttf")
CHAR_PNG = os.path.join(HERE, "..", "assets", "char.png")
CYCLE = g.CYCLE

EXTRA_CSS = """
:root{--card:rgba(255,255,255,.035)}
@media (prefers-color-scheme: light){:root{--card:rgba(0,0,0,.03)}}
.fd{opacity:0;animation:fd CYC_s ease-out infinite both}
@keyframes fd{0%,3%{opacity:0;transform:translateY(12px)}13%{opacity:1;transform:translateY(0)}
86%{opacity:1}94%,100%{opacity:0}}
.chip{opacity:0;animation:fd CYC_s ease-out infinite both}
.float{transform-box:fill-box;transform-origin:50% 100%;animation:float 4.6s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0) rotate(-1.5deg)}50%{transform:translateY(-9px) rotate(1.5deg)}}
.shadow{transform-box:fill-box;transform-origin:center;animation:shadow 4.6s ease-in-out infinite}
@keyframes shadow{0%,100%{transform:scaleX(1);opacity:.55}50%{transform:scaleX(.82);opacity:.3}}
.blink{animation:blink 1s steps(1,end) infinite}
@keyframes blink{0%,55%{opacity:1}56%,100%{opacity:0}}
.nudge{animation:nudge 1.8s ease-in-out infinite}
@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(3px,-3px)}}
.trace{fill:none;stroke:var(--acc);stroke-width:2;stroke-linecap:round;animation:run 6s linear infinite}
@keyframes run{to{stroke-dashoffset:-PERIM_}}
.d1{animation:dots 1.4s infinite both}.d2{animation:dots 1.4s .2s infinite both}.d3{animation:dots 1.4s .4s infinite both}
@keyframes dots{0%,100%{opacity:.2}40%{opacity:1}}
""".replace("CYC_", str(CYCLE))


def wrap(text, path, size, maxw, tracking=0.0):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if layout(t, path, size, tracking)[1] <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def static(text, path, size, tracking, x, y, fill, anchor="start", extra=""):
    glyphs, tw = layout(text, path, size, tracking)
    if anchor == "end":
        x -= tw
    elif anchor == "middle":
        x -= tw / 2
    parts = "".join(f'<g transform="translate({x + gx:.2f},{y})"><path fill="{fill}" {extra} d="{d}"/></g>'
                    for ch, d, gx, adv in glyphs if d)
    return parts, tw


def rise(text, path, size, tracking, x, y, fill, delay0, stagger=0.045):
    glyphs, tw = layout(text, path, size, tracking)
    out, k = [], 0
    for ch, d, gx, adv in glyphs:
        if not d:
            continue
        out.append(f'<g transform="translate({x + gx:.2f},{y})"><path class="l" '
                   f'style="animation-delay:{delay0 + k * stagger:.2f}s" fill="{fill}" d="{d}"/></g>')
        k += 1
    return "".join(out), tw


# ---------------------------------------------------------------- intro
def intro():
    W = 900
    tx, maxx = 345, 868
    with open(CHAR_PNG, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    body = []
    # character (floating) + shadow
    body.append('<ellipse class="shadow" cx="170" cy="316" rx="88" ry="8" fill="var(--line)"/>')
    body.append(f'<g class="float"><image x="40" y="32" width="260" height="268" preserveAspectRatio="xMidYMid meet" '
                f'href="data:image/png;base64,{b64}"/></g>')

    # label
    lab, _ = static("// HELLO, WORLD", MONO_BOLD, 13, 4, 0, 0, "var(--dim)")
    body.append(f'<g transform="translate({tx},62)"><g class="lab">{lab}</g></g>')

    # line 1 + name (with glitch layers like the section headings)
    g1, _ = layout("Hey there! I'm", POPPINS_BOLD, 34, 0.5)
    body.append(glyph_layers(g1, tx, 112, 0.05, 0.1))
    name = "Fahri Rahmadhan"
    g2, tw2 = layout(name, POPPINS_BOLD, 54, 0.5)
    acc_from = name.index("Rahmadhan")
    body.append(glyph_layers(g2, tx, 178, 0.045, 0.45,
                             cls_for=lambda i: "var(--acc)" if i >= acc_from else None))
    body.append(f'<path class="rule" style="--len:{tw2:.0f}" d="M{tx} 196 H{tx + tw2:.0f}"/>')

    # alias + cursor
    al, alw = static("a.k.a. Fayy", MONO_BOLD, 17, 1.5, 0, 0, "var(--dim)")
    body.append(f'<g transform="translate({tx},234)"><g class="fd" style="animation-delay:.9s">{al}'
                f'<rect class="blink" x="{alw + 6:.1f}" y="-14" width="3" height="18" rx="1.5" fill="var(--acc)"/></g></g>')

    # chips
    chips = ["XII RPL 1", "SOFTWARE ENGINEERING", "WEB DEVELOPER", "GAMER"]
    x, y, h, pad, gap = tx, 256, 30, 12, 8
    for i, c in enumerate(chips):
        txt, tw = static(c, MONO_BOLD, 11, 1.4, pad, h / 2 + 3.8, "var(--acc)" if i == 0 else "var(--fg)")
        cw = tw + 2 * pad
        if x + cw > maxx:
            x, y = tx, y + h + 10
        stroke = "var(--acc)" if i == 0 else "var(--line)"
        body.append(f'<g transform="translate({x:.1f},{y})"><g class="chip" style="animation-delay:{1.1 + i * 0.12:.2f}s">'
                    f'<rect x="1" y="1" width="{cw - 2:.1f}" height="{h - 2}" rx="{(h - 2) / 2}" fill="var(--card)" stroke="{stroke}" stroke-width="1.5"/>{txt}</g></g>')
        x += cw + gap
    H = max(340, y + h + 28)
    write("intro.svg", svg_wrap(W, H, "".join(body), HEAD_CSS + EXTRA_CSS.replace("PERIM_", "0")))


# ---------------------------------------------------------------- project cards
PROJECTS = [
    dict(file="proj-1.svg", idx=1, year="2026", title="Kebab Sumatera", sub="BUSINESS WEBSITE",
         desc="Online storefront for a street-food kebab stall: promos, a full menu, and a build-your-own order flow that sends orders to WhatsApp.",
         feats=["25+ MENU ITEMS", "BUILD YOUR OWN", "ORDER VIA WA"], tech="HTML / CSS / JS"),
    dict(file="proj-2.svg", idx=2, year="2026", title="Portfolio", sub="PERSONAL WEBSITE",
         desc="My personal corner of the web: scroll-driven motion, a tech-stack explorer, travel photos, and a music player with a lyrics view.",
         feats=["GSAP MOTION", "STACK EXPLORER", "MUSIC PLAYER"], tech="HTML / CSS / JS / GSAP"),
    dict(file="proj-3.svg", idx=3, year="2025", title="FBS UNIMED", sub="SERVICE SYSTEM",
         desc="A one-stop service system for the Faculty of Languages and Arts: equipment loans, stamp requests, mail logs, and building services.",
         feats=["7 SERVICES", "MAIL LOGS", "ONE PLATFORM"], tech="HTML / CSS / BS / JS / PHP / MYSQL"),
    dict(file="proj-4.svg", idx=4, year="2026", title="FAYWALKOT", sub="CITY PORTAL",
         desc="Information portal for the Medan city government, with document management, a meeting-room showcase, and a simple 3-step guide.",
         feats=["DOCUMENTS", "4 MEETING ROOMS", "3-STEP GUIDE"], tech="HTML / CSS / BS / JS / PHP / MYSQL"),
]


def card(p, n):
    W, H, pad = 420, 282, 26
    inner = W - 2 * pad
    d0 = n * 0.18  # stagger between cards
    rx = 20
    perim = 2 * (W - 4 - 2 * rx) + 2 * 3.14159 * rx
    css = HEAD_CSS + EXTRA_CSS.replace("PERIM_", f"{perim:.0f}") + \
        f".trace{{stroke-dasharray:{perim * 0.16:.0f} {perim * 0.84:.0f};animation-delay:{d0}s}}"
    b = [f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="{rx}" fill="var(--card)" stroke="var(--line)" stroke-width="1.5"/>',
         f'<rect class="trace" x="2" y="2" width="{W - 4}" height="{H - 4}" rx="{rx}"/>']

    # big outlined index number (background decoration)
    num, nw = static(f"{p['idx']:02d}", POPPINS_BOLD, 50, 0, 0, 0, "none", extra='stroke="var(--dim)" stroke-width="1.3"')
    b.append(f'<g transform="translate({W - pad - nw:.1f},88)"><g class="fd" style="animation-delay:{d0 + .1:.2f}s">{num}</g></g>')

    # top row: case label + LIVE
    top, _ = static(f"CASE {p['idx']:02d}  /  {p['year']}", MONO_BOLD, 10.5, 2.5, 0, 0, "var(--dim)")
    b.append(f'<g transform="translate({pad},40)"><g class="fd" style="animation-delay:{d0:.2f}s">{top}</g></g>')
    live, lw = static("LIVE", MONO_BOLD, 10.5, 2.5, 0, 0, "var(--acc)")
    b.append(f'<g transform="translate({W - pad - lw:.1f},40)"><g class="fd" style="animation-delay:{d0:.2f}s">{live}</g></g>')
    b.append(f'<circle class="dot" cx="{W - pad - lw - 12:.1f}" cy="36.5" r="3.5"/>')

    # title (letters rise) + subtitle
    t, tw = rise(p["title"], POPPINS_BOLD, 30, 0.3, pad, 86, "var(--fg)", d0 + 0.15)
    b.append(t)
    sub, _ = static(p["sub"], MONO_BOLD, 11, 3, 0, 0, "var(--acc)")
    b.append(f'<g transform="translate({pad},110)"><g class="fd" style="animation-delay:{d0 + .35:.2f}s">{sub}</g></g>')

    # description (wrapped)
    lines = wrap(p["desc"], POPPINS_REG, 12.5, inner)
    assert len(lines) <= 3, (p["title"], lines)
    for i, ln in enumerate(lines):
        tx_, _ = static(ln, POPPINS_REG, 12.5, 0, 0, 0, "var(--fg)", extra='fill-opacity=".78"')
        b.append(f'<g transform="translate({pad},{140 + i * 19})"><g class="fd" style="animation-delay:{d0 + .5 + i * .1:.2f}s">{tx_}</g></g>')

    # feature chips (bottom-anchored)
    cy, ch = H - 48 - 18 - 26, 26
    x = pad
    for i, f in enumerate(p["feats"]):
        txt, fw = static(f, MONO_BOLD, 9.5, 1.2, 10, ch / 2 + 3.4, "var(--fg)")
        cw = fw + 20
        b.append(f'<g transform="translate({x:.1f},{cy})"><g class="chip" style="animation-delay:{d0 + .8 + i * .1:.2f}s">'
                 f'<rect x="1" y="1" width="{cw - 2:.1f}" height="{ch - 2}" rx="{(ch - 2) / 2}" fill="none" stroke="var(--line)" stroke-width="1.4"/>{txt}</g></g>')
        x += cw + 8
    assert x - 8 <= W - pad + 0.5, (p["title"], "chips overflow", x)

    # footer: divider, tech stack, VISIT arrow
    sy = H - 48
    b.append(f'<line x1="{pad}" y1="{sy}" x2="{W - pad}" y2="{sy}" stroke="var(--line)" stroke-width="1"/>')
    tech, techw = static(p["tech"], MONO_BOLD, 9.5, 1, 0, 0, "var(--dim)")
    b.append(f'<g transform="translate({pad},{H - 22})"><g class="fd" style="animation-delay:{d0 + 1.1:.2f}s">{tech}</g></g>')
    vis, vw = static("VISIT", MONO_BOLD, 11, 3, 0, 0, "var(--acc)")
    ax = W - pad - 12
    assert pad + techw + 16 < ax - vw - 10, (p["title"], "tech overlaps VISIT", techw)
    b.append(f'<g transform="translate({ax - vw - 10:.1f},{H - 22})"><g class="fd" style="animation-delay:{d0 + 1.1:.2f}s">{vis}</g></g>')
    b.append(f'<g transform="translate({ax:.1f},{H - 22})"><g class="nudge"><path d="M0 0 L10 -10 M2 -10 H10 V-2" '
             f'fill="none" stroke="var(--acc)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g></g>')
    write(p["file"], svg_wrap(W, H, "".join(b), css))


# ---------------------------------------------------------------- captions
def caption(name, text, dots=False):
    W, H = 900, 56
    glyphs, tw = layout(text, MONO_BOLD, 14, 4)
    total = tw + (44 if dots else 0)
    x0 = (W - total) / 2
    parts = "".join(f'<g transform="translate({x0 + gx:.2f},34)"><path fill="var(--dim)" d="{d}"/></g>'
                    for ch, d, gx, adv in glyphs if d)
    body = f'<g class="fd">{parts}</g>'
    if dots:
        for i in range(3):
            body += f'<circle class="d{i + 1}" cx="{x0 + tw + 14 + i * 14:.1f}" cy="30" r="2.6" fill="var(--acc)"/>'
    write(name, svg_wrap(W, H, body, EXTRA_CSS.replace("PERIM_", "0")))


if __name__ == "__main__":
    intro()
    for n, p in enumerate(PROJECTS):
        card(p, n)
    caption("cap-more.svg", "MORE PROJECTS LOADING", dots=True)
    caption("cap-thanks.svg", "THANKS FOR STOPPING BY  /  FAYY")
