#!/usr/bin/env python3
"""writes assets/langs.svg from every repo i own (private ones too). needs `gh` logged in.

the public stats cards can't see private repos, so this runs locally now and then.
score per language = sqrt(bytes) * sqrt(repos using it), otherwise one big repo eats the chart.
"""
import colorsys
import datetime
import json
import math
import subprocess
from collections import Counter
from html import escape
from pathlib import Path

OWNER = "TheCatArt"
W = 820
BG, CARD, VIOLET, CYAN = "#0B0A12", "#16122A", "#7A3BF5", "#2FE3DC"
TEXT, MUTED, EDGE = "#ECEAF5", "#8E8AA6", "#241E3D"
FONT = ("'JetBrains Mono','Iosevka','Fira Code','Cascadia Code','SF Mono',"
        "Menlo,Consolas,'DejaVu Sans Mono',monospace")
OTHER = "#6E6A85"
SHOWN = 10


def gh(*args):
    return json.loads(subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout)


def linguist_colors():
    """the colors github itself uses for languages."""
    raw = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github.raw",
         "repos/github-linguist/linguist/contents/lib/linguist/languages.yml"],
        check=True, capture_output=True, text=True).stdout
    colors, current = {}, None
    for line in raw.splitlines():
        if line and not line.startswith((" ", "#", "-")) and line.endswith(":"):
            current = line[:-1].strip("\"'")
        elif current and line.strip().startswith("color:"):
            colors[current] = line.split(":", 1)[1].strip().strip("\"'")
    return colors


def lum(h):
    r, g, b = (int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def visible(hexc, bg=CARD, need=3.0):
    """keep the real color unless it disappears on the card, then lighten the same hue."""
    hexc = hexc.upper()
    ratio = lambda c: (max(lum(c), lum(bg)) + 0.05) / (min(lum(c), lum(bg)) + 0.05)
    if ratio(hexc) >= need:
        return hexc
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    while l < 0.95:
        l += 0.02
        c = "#" + "".join(f"{round(v * 255):02X}" for v in colorsys.hls_to_rgb(h, l, s))
        if ratio(c) >= need:
            return c
    return "#FFFFFF"


def collect():
    repos = gh("repo", "list", OWNER, "--limit", "500", "--json", "nameWithOwner,isFork,visibility")
    own = [r for r in repos if not r["isFork"]]
    size, count = Counter(), Counter()
    for r in own:
        for lang, b in gh("api", f"repos/{r['nameWithOwner']}/languages").items():
            size[lang] += b
            count[lang] += 1
    stats = {"own": len(own), "private": sum(r["visibility"] == "PRIVATE" for r in own),
             "forks": len(repos) - len(own)}
    return size, count, stats


def render(size, count, stats, lang_colors):
    score = {l: math.sqrt(size[l]) * math.sqrt(count[l]) for l in size}
    total = sum(score.values())
    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    items = [(l, s / total) for l, s in ranked[:SHOWN]]
    rest = sum(s for _, s in ranked[SHOWN:]) / total
    colors = [visible(lang_colors.get(l, OTHER)) for l, _ in items]
    if rest > 0:
        items.append(("other", rest))
        colors.append(OTHER)

    bx, bw, by, bh = 40, W - 80, 76, 10
    segs, x = [], bx
    for (lang, share), col in zip(items, colors):
        w = share * bw
        segs.append(f'<rect x="{x:.2f}" y="{by}" width="{max(w - 2, 1):.2f}" height="{bh}" fill="{col}"/>')
        x += w

    cols, row_h, ly = 4, 26, 122
    legend = []
    for i, ((lang, share), col) in enumerate(zip(items, colors)):
        cx = bx + (i % cols) * (bw / cols)
        cy = ly + (i // cols) * row_h
        pct = f"{share * 100:.1f}%"
        legend.append(
            f'<rect x="{cx:.1f}" y="{cy - 9}" width="9" height="9" rx="2" fill="{col}"/>'
            f'<text class="t" x="{cx + 17:.1f}" y="{cy}">{escape(lang.lower())}</text>'
            f'<text class="m" x="{cx + 17 + (len(lang) + 1) * 7.8:.1f}" y="{cy}">{pct}</text>')

    rows = math.ceil(len(items) / cols)
    note_y = ly + (rows - 1) * row_h + 34
    h = note_y + 30
    today = datetime.date.today().isoformat()
    right = f"{stats['own']} own repos, {stats['private']} of them private"
    note = (f"weighted by size and how many repos use it. the {stats['forks']} forks aren't my code, "
            f"so they don't count. last run {today}")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="languages across {stats['own']} own repos: {escape(", ".join(f"{l} {s * 100:.0f}%" for l, s in items))}">
<style>
text{{font-family:{FONT};font-variant-ligatures:none}}
.h{{fill:{TEXT};font-size:15px;font-weight:700}} .t{{fill:{TEXT};font-size:13px}}
.m{{fill:{MUTED};font-size:13px}} .n{{fill:{MUTED};font-size:11px}}
</style>
<defs>
<clipPath id="bar"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="5"/></clipPath>
<clipPath id="grow"><rect x="{bx}" y="{by - 2}" width="{bw}" height="{bh + 4}">
<animate attributeName="width" values="0;{bw}" keyTimes="0;1" calcMode="spline" keySplines="0.2 0.7 0.3 1" dur="1.4s" begin="0s" fill="freeze"/>
</rect></clipPath>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{BG}" stroke="{EDGE}"/>
<rect x="16" y="16" width="{W - 32}" height="{h - 32}" rx="10" fill="{CARD}" stroke="{VIOLET}" stroke-width="1.2"/>
<text class="h" x="{bx}" y="54">languages</text>
<text class="m" x="{bx + bw}" y="54" text-anchor="end">{right}</text>
<g clip-path="url(#grow)"><g clip-path="url(#bar)">
<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{EDGE}"/>
{"".join(segs)}
</g></g>
{"".join(legend)}
<text class="n" x="{bx}" y="{note_y}">{note}</text>
</svg>
'''


def main():
    svg = render(*collect(), linguist_colors())
    dest = Path(__file__).resolve().parent.parent / "assets" / "langs.svg"
    dest.write_text(svg, encoding="utf-8")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
