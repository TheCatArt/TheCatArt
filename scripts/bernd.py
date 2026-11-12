#!/usr/bin/env python3
"""writes assets/bernd.svg: a grumpy loaf, pixel by pixel. iykyk."""
from html import escape
from pathlib import Path

PX = 7
# . nothing  c dark crust  C crust  b crumb  s crumb shade  w eye  p pupil  l lid  m mouth  a arms/legs
LOAF = [
    "......cccccccc......",
    "...cccCCCCCCCCccc...",
    "..cCCCCCCCCCCCCCCc..",
    ".cCCCCCCCCCCCCCCCCc.",
    ".cCCCCCCCCCCCCCCCCc.",
    ".ccbbbbbbbbbbbbbbcc.",
    "..sbbbbbbbbbbbbbbs..",
    "..sbbllllbbllllbbs..",
    "..sblllllbblllllbs..",
    "..sbwwwwwbbwwwwwbs..",
    "a.sbwwppwbbwppwwbs.a",
    "a.sbbwwwbbbbwwwbbs.a",
    "a.sbbbbbbbbbbbbbbs.a",
    "a.sbbbbbbbbbbbbbbs.a",
    "aasbbbbbmmmmbbbbbsaa",
    "..sbbbbmbbbbmbbbbs..",
    "..sbbbbbbbbbbbbbbs..",
    "..ssbbbbbbbbbbbbss..",
    "...ssssssssssssss...",
    ".....a........a.....",
    ".....a........a.....",
    "....aa........aa....",
]
COLORS = {"c": "#7A4518", "C": "#A9622A", "b": "#E9BC7E", "s": "#CF9452", "w": "#F7F2E8",
          "p": "#24160B", "l": "#C98A4B", "m": "#5A3216", "a": "#4A2A12"}
FONT = ("'JetBrains Mono','Iosevka','Fira Code','Cascadia Code','SF Mono',"
        "Menlo,Consolas,'DejaVu Sans Mono',monospace")
TALK = "#8E8AA6"


def rects(grid, only=None):
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            g = row[x]
            if g == "." or (only and g not in only):
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == g:
                run += 1
            out.append(f'<rect x="{x * PX}" y="{y * PX}" width="{run * PX}" height="{PX}" fill="{COLORS[g]}"/>')
            x += run
    return "".join(out)


def typed(text, x, y, start):
    out = []
    for i in range(1, len(text) + 1):
        t0, t1 = start + i * 0.07, start + (i + 1) * 0.07
        if i == len(text):
            sets = f'<set attributeName="opacity" to="0" begin="0s"/><set attributeName="opacity" to="1" begin="{t0:.2f}s"/>'
        else:
            sets = f'<set attributeName="opacity" to="1" begin="{t0:.2f}s"/><set attributeName="opacity" to="0" begin="{t1:.2f}s"/>'
        out.append(f'<text x="{x}" y="{y}" opacity="{1 if i == len(text) else 0}">{sets}{escape(text[:i])}</text>')
    return "".join(out)


def main():
    w, h = len(LOAF[0]) * PX, len(LOAF) * PX
    # eyes shut: lids slide down over the whites now and then, he's tired
    shut = [row.replace("w", "l").replace("p", "l") if 9 <= y <= 11 else "." * len(row) for y, row in enumerate(LOAF)]
    blink = ('<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.86;0.95" calcMode="discrete" '
             'dur="6s" repeatCount="indefinite"/>')
    sx = w + 18
    W, H = sx + 190, h
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="a grumpy loaf of bread: alpsec ist tot. mist.">
<style>text{{font-family:{FONT};font-size:14px;fill:{TALK};font-variant-ligatures:none}}</style>
<g shape-rendering="crispEdges">{rects(LOAF)}<g opacity="0">{blink}{rects(shut)}</g></g>
{typed("alpsec ist tot.", sx, 9 * PX + 4, 0.8)}
{typed("mist.", sx, 13 * PX + 4, 3.4)}
</svg>
'''
    dest = Path(__file__).resolve().parent.parent / "assets" / "bernd.svg"
    dest.write_text(svg, encoding="utf-8")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
