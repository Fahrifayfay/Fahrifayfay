#!/usr/bin/env python3
"""Generate live GitHub stats SVGs (stars, forks, followers, 30-day contributions).

Run by .github/workflows/update-profile.yml every day. If a fetch fails, the
previous SVGs are kept untouched.

Usage:
    python scripts/update_profile.py            # real data (needs GH_TOKEN for contributions)
    python scripts/update_profile.py --demo     # fake data, for previewing the design
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

USERNAME = os.environ.get("PROFILE_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Fahrifayfay"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "profile")
F_BOLD = os.path.join(HERE, "fonts", "Poppins-Bold.ttf")
F_MONO = os.path.join(HERE, "fonts", "DejaVuSansMono-Bold.ttf")

# ------------------------------------------------------------------ fonts -> paths
_cache = {}


def _font(path):
    if path not in _cache:
        f = TTFont(path)
        _cache[path] = (f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, f["hmtx"])
    return _cache[path]


def layout(text, path, size, tracking=0.0):
    gs, cmap, upm, hmtx = _font(path)
    s = size / upm
    x, out = 0.0, []
    for ch in text:
        g = cmap.get(ord(ch))
        adv = hmtx[g][0] * s if g else size * 0.3
        d = ""
        if g and ch != " ":
            pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
            gs[g].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
            d = pen.getCommands()
        out.append((d, x))
        x += adv + tracking
    return out, x - tracking


THEME = """
:root{--fg:#f4f4f5;--dim:#8b8b93;--acc:#b9a7ff;--line:#3a3a42}
@media (prefers-color-scheme: light){:root{--fg:#111114;--dim:#6b6b73;--acc:#6d28d9;--line:#c9c9d1}}
"""
CYCLE = 8
ANIM = """
.l{opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:rise CYCLE_s cubic-bezier(.2,.8,.2,1) infinite both}
@keyframes rise{0%{opacity:0;transform:translateY(24px) scale(.8)}
9%{opacity:1;transform:translateY(-3px) scale(1.04)}12%{opacity:1;transform:translateY(0) scale(1)}
86%{opacity:1}94%,100%{opacity:0;transform:translateY(-8px)}}
.fade{opacity:0;animation:fade CYCLE_s ease-out infinite both}
@keyframes fade{0%,6%{opacity:0}16%{opacity:1}86%{opacity:1}94%,100%{opacity:0}}
.bar{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:grow CYCLE_s cubic-bezier(.2,.8,.2,1) infinite both}
@keyframes grow{0%{transform:scaleY(0)}18%{transform:scaleY(1.06)}22%{transform:scaleY(1)}86%{transform:scaleY(1)}94%,100%{transform:scaleY(0)}}
.trace{fill:none;stroke:var(--acc);stroke-width:2;stroke-linecap:round;animation:run 3.6s linear infinite}
@keyframes run{to{stroke-dashoffset:-PERIM_}}
.base{fill:none;stroke:var(--line);stroke-width:1.5}
""".replace("CYCLE_", str(CYCLE))


def svg(w, h, body, css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
            f"<style>{THEME}{css}</style>{body}</svg>\n")


def static_text(text, path, size, tracking, x, y, fill, anchor="start", cls=""):
    glyphs, tw = layout(text, path, size, tracking)
    if anchor == "middle":
        x -= tw / 2
    parts = "".join(f'<g transform="translate({x + gx:.2f},{y})"><path fill="{fill}" d="{d}"/></g>'
                    for d, gx in glyphs if d)
    return f'<g class="{cls}">{parts}</g>' if cls else parts


def anim_text(text, path, size, tracking, x, y, fill, delay0=0.15, stagger=0.06):
    glyphs, tw = layout(text, path, size, tracking)
    parts, k = [], 0
    for d, gx in glyphs:
        if not d:
            continue
        parts.append(f'<g transform="translate({x + gx:.2f},{y})"><path class="l" '
                     f'style="animation-delay:{delay0 + k * stagger:.2f}s" fill="{fill}" d="{d}"/></g>')
        k += 1
    return "".join(parts), tw


# ------------------------------------------------------------------ stat badges
def badge(name, value, label):
    W, H = 260, 96
    rx = 22
    perim = 2 * (W - 4 - 2 * rx) + 2 * 3.14159 * rx
    num, _ = anim_text(f"{value:,}", F_BOLD, 40, 1, 26, 58, "var(--fg)")
    lab = static_text(label.upper(), F_MONO, 13, 4, 27, 80, "var(--dim)", cls="fade")
    css = ANIM.replace("PERIM_", f"{perim:.0f}") + f".trace{{stroke-dasharray:{perim*0.2:.0f} {perim*0.8:.0f}}}"
    body = (f'<rect class="base" x="2" y="2" width="{W-4}" height="{H-4}" rx="{rx}"/>'
            f'<rect class="trace" x="2" y="2" width="{W-4}" height="{H-4}" rx="{rx}"/>'
            f'<circle cx="{W-30}" cy="30" r="5" fill="var(--acc)" class="fade"/>{num}{lab}')
    write(name, svg(W, H, body, css))


# ------------------------------------------------------------------ contributions chart
def contributions(name, days):
    """days: list of (date_str, count), oldest first."""
    W, H = 900, 240
    left, right, base, maxh = 40, 860, 188, 120
    n = len(days)
    bw = 18
    gap = (right - left - n * bw) / max(n - 1, 1)
    top = max((c for _, c in days), default=0)
    total = sum(c for _, c in days)
    parts = [static_text(f"{total} CONTRIBUTIONS  /  LAST {n} DAYS", F_MONO, 13, 3, left, 30, "var(--dim)", cls="fade"),
             f'<line x1="{left}" y1="{base + 6}" x2="{right}" y2="{base + 6}" stroke="var(--line)" stroke-width="1"/>']
    for i, (date, c) in enumerate(days):
        x = left + i * (bw + gap)
        h = max(3, (c / top) * maxh) if top else 3
        is_peak = top and c == top
        fill = "var(--acc)" if is_peak else ("var(--fg)" if c else "var(--line)")
        op = 1 if (is_peak or not c) else 0.35 + 0.65 * (c / top)
        parts.append(f'<rect class="bar" style="animation-delay:{0.2 + i * 0.035:.2f}s" x="{x:.1f}" y="{base - h:.1f}" '
                     f'width="{bw}" height="{h:.1f}" rx="4" fill="{fill}" opacity="{op:.2f}"/>')
        if is_peak and c:
            parts.append(static_text(str(c), F_BOLD, 15, 0, x + bw / 2, base - h - 8, "var(--acc)", "middle", "fade"))
    if days:
        fmt = lambda s: dt.date.fromisoformat(s).strftime("%d %b").upper()
        parts.append(static_text(fmt(days[0][0]), F_MONO, 12, 2, left, 222, "var(--dim)", cls="fade"))
        glyphs, tw = layout(fmt(days[-1][0]), F_MONO, 12, 2)
        parts.append(static_text(fmt(days[-1][0]), F_MONO, 12, 2, right - tw, 222, "var(--dim)", cls="fade"))
    write(name, svg(W, H, "".join(parts), ANIM.replace("PERIM_", "0")))


# ------------------------------------------------------------------ data
def api(url, data=None):
    headers = {"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_totals():
    user = api(f"https://api.github.com/users/{USERNAME}")
    stars = forks = 0
    page = 1
    while True:
        repos = api(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for r in repos:
            if not r.get("fork"):
                stars += r["stargazers_count"]
                forks += r["forks_count"]
        page += 1
    return stars, forks, user["followers"]


def fetch_contribs(n=30):
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=n + 1)
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    payload = json.dumps({"query": q, "variables": {"u": USERNAME, "f": start.isoformat(), "t": end.isoformat()}}).encode()
    res = api("https://api.github.com/graphql", payload)
    weeks = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
    return days[-n:]


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", name)


def main():
    if "--demo" in sys.argv:
        import random
        random.seed(7)
        today = dt.date.today()
        days = [((today - dt.timedelta(days=29 - i)).isoformat(), random.choice([0, 0, 1, 2, 3, 5, 8, 12])) for i in range(30)]
        stats = (128, 17, 342)
    else:
        try:
            stats = fetch_totals()
            days = fetch_contribs()
        except Exception as e:  # keep last good SVGs
            print("fetch failed, keeping existing SVGs:", e)
            return 0
    badge("stars.svg", stats[0], "Stars")
    badge("forks.svg", stats[1], "Forks")
    badge("followers.svg", stats[2], "Followers")
    contributions("contributions.svg", days)
    return 0


if __name__ == "__main__":
    sys.exit(main())
