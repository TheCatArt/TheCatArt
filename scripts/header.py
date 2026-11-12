#!/usr/bin/env python3
"""writes assets/header.svg: terminal session, a bonsai that grows, the cat, a status bar.
edit SESSION / TREE / CAT and rerun."""
import math
import random
from html import escape
from pathlib import Path

W, H = 820, 420
BG, CARD, VIOLET, CYAN = "#0B0A12", "#16122A", "#7A3BF5", "#2FE3DC"
SILVER, TEXT, MUTED, EDGE = "#C9C7D6", "#ECEAF5", "#8E8AA6", "#241E3D"
TEAL, LILAC, BARK = "#1FA6A0", "#B9A4FF", "#A0897B"
EMERALD, PURPLE = "#50C878", "#A970FF"   # the sona's eyes
NK_PAPER, NK_ORANGE, NK_TURQ = "#F5F2EC", "#FBAA2B", "#00BABA"   # node-K's own colors
FONT = ("'JetBrains Mono','Iosevka','Fira Code','Cascadia Code','SF Mono',"
        "Menlo,Consolas,'DejaVu Sans Mono',monospace")

# (command, typo, output) - typo is (typed wrong, backspaces); output is text or [(text, css class)]
SESSION = [
    ("whoami", None, "weird cat, perpetually caffeinated"),
    ("cat job.txt", ("cat jbo", 2), "i do cybersecurity for fun and somehow for a living"),
    ("ssh admin@node-k.at", None, [("node-", "nkp"), ("K", "nko"), ("  one of the admins here. it's always dns", "nkt")]),
    ("cat /etc/motd", None, "i use arch btw"),
    ("cbonsai -l", None, None),          # no output, the tree on the right grows instead
]

FS, CW, LH = 15, 9.0, 24
X0, Y0 = 44, 116
CMD_X = X0 + 4 * CW

# the scene on the right has its own, slightly smaller grid
ROWS = 13
SX, SCW, SLH = 516, 7.6, 17
SY = Y0 + 9 * LH                        # bottom scene row sits on the idle prompt line
TREE = [
    "             .&&&&&&&.",
    "           &&&&&&&&&&&&&",
    "            '&&&&&&&&&'",
    "    .&&&&&.     \\|",
    "   &&&&&&&&&     |",
    "    '&&&&&'\\_    |      .&&&&.",
    "             \\__ (    _&&&&&&&&",
    "                \\\\)__/ '&&&&&'",
    "                 ))",
    "                ((",
    "          _____/  \\_____",
    "         |______________|",
    "           ''        ''",
]
LEAF = set("&.'")
CAT = [
    " /\\_/\\",
    "( O.O )",
    " > ^ <",
    "(\")_(\")",
]
CAT_ROW, CAT_COL = 9, 26
TAIL = [  # two frames of (row, col, glyph) relative to the cat's top left
    [(3, 7, "_"), (3, 8, "/"), (2, 9, ")")],
    [(3, 7, "_"), (3, 8, ")"), (2, 8, "(")],
]

rng = random.Random(7)


def chars(s, x0, y, cls, cw=CW):
    """one <text>, every glyph pinned to a grid cell so any mono font lines up."""
    xs, glyphs = [], []
    for i, c in enumerate(s):
        if c == " ":
            continue
        xs.append(f"{x0 + i * cw:g}")
        glyphs.append(escape(c))
    if not glyphs:
        return ""
    return f'<text class="{cls}" x="{" ".join(xs)}" y="{y:g}">{"".join(glyphs)}</text>'


def segments(parts, x0, y):
    out, col = [], 0
    for text, cls in parts:
        out.append(chars(text, x0 + col * CW, y, cls))
        col += len(text)
    return "".join(out)


def scattered(cells, cls):
    """glyphs at (row, col) cells of the scene grid."""
    if not cells:
        return ""
    xs = " ".join(f"{SX + c * SCW:g}" for r, c, _ in cells)
    ys = " ".join(f"{SY - (ROWS - 1 - r) * SLH:g}" for r, c, _ in cells)
    return f'<text class="{cls}" x="{xs}" y="{ys}">{"".join(escape(g) for _, _, g in cells)}</text>'


def t(v):
    return f"{v:.2f}s"


def show_at(start):
    """visible in a static render, hidden from 0s until `start` when animated."""
    if start <= 0:
        return ""
    return f'<set attributeName="opacity" to="0" begin="0s"/><set attributeName="opacity" to="1" begin="{t(start)}"/>'


def keystrokes(final, typo):
    states, done = [], ""
    if typo:
        wrong, back = typo
        states += [(wrong[:i], "key") for i in range(1, len(wrong) + 1)]
        states += [(wrong[:len(wrong) - k], "back") for k in range(1, back + 1)]
        done = wrong[:len(wrong) - back]
    states += [(final[:i], "key") for i in range(len(done) + 1, len(final) + 1)]
    return states


def prompt(y):
    return chars("~", X0, y, "c") + chars("❯", X0 + 2 * CW, y, "v")


def terminal():
    out, clock, y = [], 0.0, Y0
    for n, (cmd, typo, output) in enumerate(SESSION):
        prompt_at = clock
        out.append(f"<g>{show_at(prompt_at)}{prompt(y)}</g>")
        clock += 0.45 if n == 0 else 0.6
        frames, prev = [], None
        for s, kind in keystrokes(cmd, typo):
            if kind == "back":
                clock += 0.32 if prev == "key" else 0.07
            else:
                clock += rng.uniform(0.05, 0.12)
                if s.endswith(" ") or (len(s) > 1 and s[-2] == " "):
                    clock += rng.uniform(0.04, 0.12)
            frames.append((clock, s))
            prev = kind
        for i, (start, s) in enumerate(frames):
            if i == len(frames) - 1:
                out.append(f'<g>{show_at(start)}{chars(s, CMD_X, y, "t")}</g>')
            else:
                out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t(start)}"/>'
                           f'<set attributeName="opacity" to="0" begin="{t(frames[i + 1][0])}"/>'
                           f'{chars(s, CMD_X, y, "t")}</g>')
        enter = clock + 0.35
        times = [prompt_at] + [f[0] for f in frames]
        xs = [CMD_X] + [CMD_X + len(f[1]) * CW for f in frames]
        dur = enter - prompt_at
        out.append(
            f'<rect class="cur" x="{CMD_X:g}" y="{y - 13}" width="{CW - 1:g}" height="17" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t(prompt_at)}"/>'
            f'<set attributeName="opacity" to="0" begin="{t(enter)}"/>'
            f'<animate attributeName="x" calcMode="discrete" begin="{t(prompt_at)}" dur="{t(dur)}" '
            f'values="{";".join(f"{x:g}" for x in xs)}" '
            f'keyTimes="{";".join(f"{(tt - prompt_at) / dur:.4f}" for tt in times)}" fill="freeze"/></rect>')
        y += LH
        if output is None:
            clock = enter
            break
        wait = 0.5 if cmd.startswith("ssh") else 0.06      # ssh takes a moment
        body = segments(output, X0, y) if isinstance(output, list) else chars(output, X0, y, "o")
        out.append(f"<g>{show_at(enter + wait)}{body}</g>")
        y += LH
        clock = enter + wait + 0.2

    tree, grown = bonsai(clock + 0.25)
    idle = grown + 0.4
    out.append(f"<g>{show_at(idle)}{prompt(y)}</g>")
    out.append(f'<rect class="cur" x="{CMD_X:g}" y="{y - 13}" width="{CW - 1:g}" height="17">'
               f'<set attributeName="opacity" to="0" begin="0s"/>'
               f'<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" calcMode="discrete" '
               f'dur="1.1s" begin="{t(idle)}" repeatCount="indefinite"/></rect>')
    return "\n".join(out), tree


def bonsai(start):
    """the pot is there from the start, the trunk grows bottom up, then the pads fill in from the branch tips."""
    pot, bark, leaves = [], [], []
    for r, line in enumerate(TREE):
        for c, g in enumerate(line):
            if g == " ":
                continue
            if r >= 11 or (r == 10 and g in "_|"):
                pot.append((r, c, g))
            elif g in LEAF:
                leaves.append((r, c, g))
            else:
                bark.append((r, c, g))

    timed = [(start + (10 - r) * 0.14 + rng.uniform(0, 0.04), "bark", (r, c, g)) for r, c, g in bark]
    trunk_done = start + 7 * 0.14 + 0.1
    for r, c, g in leaves:
        d = min(math.hypot(r - br, (c - bc) / 2) for br, bc, _ in bark)
        cls = rng.choices(["leaf", "leaf2", "bloom"], weights=[55, 30, 15])[0]
        timed.append((trunk_done + d * 0.1 + rng.uniform(0, 0.22), cls, (r, c, g)))

    groups = {}
    for when, cls, cell in timed:
        groups.setdefault((round(when / 0.06) * 0.06, cls), []).append(cell)
    parts = [scattered(pot, "pot")]
    for (when, cls), cells in sorted(groups.items()):
        parts.append(f"<g>{show_at(when)}{scattered(cells, cls)}</g>")
    return "\n".join(parts), max(w for w, _, _ in timed)


def cat_and_mug():
    rows = [scattered([(CAT_ROW + r, CAT_COL + i, g) for i, g in enumerate(line) if g not in " O"], "k")
            for r, line in enumerate(CAT)]
    # heterochromia, like the sona: one emerald, one purple
    eye = scattered([(CAT_ROW + 1, CAT_COL + 2, "O")], "eyeL") + scattered([(CAT_ROW + 1, CAT_COL + 4, "O")], "eyeR")
    shut = [(CAT_ROW + 1, CAT_COL + 2, "-"), (CAT_ROW + 1, CAT_COL + 4, "-")]
    blink = ('<animate attributeName="opacity" values="{}" keyTimes="0;0.93;0.97" calcMode="discrete" '
             'dur="4.7s" repeatCount="indefinite"/>')
    tail = []
    for n, frame in enumerate(TAIL):
        vals = "1;0" if n == 0 else "0;1"
        tail.append(f'<g opacity="{1 if n == 0 else 0}"><animate attributeName="opacity" values="{vals}" '
                    f'keyTimes="0;0.5" calcMode="discrete" dur="1.6s" repeatCount="indefinite"/>'
                    f'{scattered([(CAT_ROW + r, CAT_COL + c, g) for r, c, g in frame], "k")}</g>')
    jitter = ('<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
              'values="0 0;0.7 0;-0.7 0;0.7 0;0 0" keyTimes="0;0.86;0.89;0.92;0.95" '
              'dur="3.6s" repeatCount="indefinite"/>')
    cat = (f"<g>{jitter}{''.join(rows)}{''.join(tail)}"
           f"<g>{blink.format('1;0;1')}{eye}</g>"
           f"<g opacity=\"0\">{blink.format('0;1;0')}{scattered(shut, 'k')}</g></g>")

    mug = scattered([(12, 0, "c"), (12, 1, "["), (12, 2, "_"), (12, 3, "]")], "mug")
    steam = []
    for n, (row, glyph) in enumerate([(11, "("), (10, ")")]):
        delay = f"-{n * 1.1}s"
        steam.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="0 4;0 -4" '
            f'dur="2.2s" begin="{delay}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.9;0" dur="2.2s" begin="{delay}" repeatCount="indefinite"/>'
            f'{scattered([(row, 2, glyph)], "s")}</g>')
    return cat + mug + "".join(steam)


def status_bar():
    y0, h = H - 16 - 30, 30
    base, cw = y0 + 20, 7.2
    left = " the_cat_art "
    lw = len(left) * cw
    windows = [("0:work", False), ("1:ctf", False), ("2:coffee*", True)]
    parts = [
        f'<rect x="16" y="{y0}" width="{W - 32}" height="{h}" fill="#100D20"/>',
        f'<line x1="16" y1="{y0}" x2="{W - 16}" y2="{y0}" stroke="{EDGE}"/>',
        f'<rect x="16" y="{y0}" width="{lw:g}" height="{h}" fill="{CYAN}"/>',
        chars(left, 16, base, "bar-in", cw),
    ]
    x = 16 + lw + 10
    for name, active in windows:
        parts.append(chars(name, x, base, "bar-on" if active else "bar", cw))
        x += (len(name) + 2) * cw
    right = " arch btw "
    rw = len(right) * cw
    parts.append(f'<rect x="{W - 16 - rw:g}" y="{y0}" width="{rw:g}" height="{h}" fill="{VIOLET}"/>')
    parts.append(chars(right, W - 16 - rw, base, "bar-v", cw))
    info = "hyprland  serpantinum"
    parts.append(chars(info, W - 16 - rw - 10 - len(info) * cw, base, "bar", cw))
    return f'<g clip-path="url(#panel)">{"".join(parts)}</g>'


def main():
    term, tree = terminal()
    name = chars("the_cat_art", 44, 62, "name", 13.2)
    where = chars("klagenfurt, at", 44 + 11 * 13.2 + 16, 62, "m", 7.8)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="the_cat_art: weird cat, perpetually caffeinated. i do cybersecurity for fun and somehow for a living. one of the it-admins at node-K. i use arch btw.">
<style>
text{{font-family:{FONT};font-size:{FS}px;font-variant-ligatures:none}}
.t{{fill:{TEXT}}} .o{{fill:{SILVER}}} .c{{fill:{CYAN}}} .v{{fill:{VIOLET}}} .m{{fill:{MUTED};font-size:13px}}
.nkp{{fill:{NK_PAPER};font-weight:700}} .nko{{fill:{NK_ORANGE};font-weight:700}} .nkt{{fill:{NK_TURQ}}}
.k,.mug,.s,.eye,.pot,.bark,.leaf,.leaf2,.bloom{{font-size:12.7px}}
.k{{fill:{SILVER}}} .mug{{fill:{VIOLET}}} .s{{fill:{MUTED}}} .pot{{fill:{VIOLET}}}
.eyeL,.eyeR{{font-size:12.7px;font-weight:700}} .eyeL{{fill:{EMERALD}}} .eyeR{{fill:{PURPLE}}}
.bark{{fill:{BARK};font-weight:700}} .leaf{{fill:{CYAN}}} .leaf2{{fill:{TEAL}}} .bloom{{fill:{LILAC}}}
.name{{fill:{CYAN};font-size:22px;font-weight:700}} .cur{{fill:{CYAN}}}
.bar,.bar-on,.bar-in,.bar-v{{font-size:12px}} .bar{{fill:{MUTED}}} .bar-on{{fill:{CYAN}}}
.bar-in{{fill:{BG};font-weight:700}} .bar-v{{fill:#FFFFFF;font-weight:700}}
</style>
<defs><clipPath id="panel"><rect x="16" y="16" width="{W - 32}" height="{H - 32}" rx="10"/></clipPath></defs>
<rect width="{W}" height="{H}" rx="14" fill="{BG}" stroke="{EDGE}"/>
<rect x="16" y="16" width="{W - 32}" height="{H - 32}" rx="10" fill="{CARD}"/>
{name}
{where}
<line x1="44" y1="84" x2="{W - 44}" y2="84" stroke="{EDGE}" stroke-width="1"/>
{term}
{tree}
{cat_and_mug()}
{status_bar()}
<rect x="16" y="16" width="{W - 32}" height="{H - 32}" rx="10" fill="none" stroke="{VIOLET}" stroke-width="1.2"/>
</svg>
'''
    dest = Path(__file__).resolve().parent.parent / "assets" / "header.svg"
    dest.write_text(svg, encoding="utf-8")
    print(f"wrote {dest} ({len(svg) // 1024} kb)")


if __name__ == "__main__":
    main()
