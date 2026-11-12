#!/usr/bin/env python3
"""writes assets/node-k.svg: the net from the node-k.at hero, as a looping svg.

the site draws it live on a canvas (<nk-netz>), which a readme can't run. this is a python port
of the same simulation (node-K's net device: seeded mulberry32, drifting nodes, the carinthia
shape, links by distance) with the hero's settings. only data comes from the site: the carinthia
points and the wordmark. the shape doesn't move and is drawn once; the drifting nodes and their
links get a frame each, played forward then backward so the loop never jumps.
"""
import json
import math
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

SITE = "https://node-k.at"
UA = {"User-Agent": "Mozilla/5.0 (profile-readme-build)"}
W, H = 898, 423                      # the hero's size on node-k.at
FPS, SECONDS = 12, 5
BG, ORANGE, TURQ = "#171717", "#fbaa2b", "#00baba"

# the hero's <nk-netz> attributes and the shape LandingNet passes in
NET = dict(density=1.4, seed=42, speed=1.5, link_dist=110, opacity=0.85, node_size=1, link_width=1, turq_ratio=0.32)
SHAPE = dict(margin=32, strength=2, node_size=1, link_dist=50, link_width=1.5)


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read().decode()


def site_data():
    html = get(f"{SITE}/en")
    points = None
    for chunk in dict.fromkeys(re.findall(r"/_nuxt/[\w.-]+\.js", html)):
        js = get(SITE + chunk)
        i = js.find('JSON.parse(`[{"x"')
        if i >= 0:
            start = i + len("JSON.parse(`")
            points = json.loads(js[start:js.index("`)", start)])
            break
    if not points:
        raise SystemExit("couldn't find the carinthia points on node-k.at")
    return points, get(f"{SITE}/brand/wordmark-dark.svg")


def mulberry32(a):
    a &= 0xFFFFFFFF
    imul = lambda x, y: (x * y) & 0xFFFFFFFF

    def rnd():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return rnd


def drifting_nodes():
    rnd = mulberry32(NET["seed"])
    count = max(10, min(round(W * H / 15000 * NET["density"]), 800))
    nodes = []
    for _ in range(count):
        n = dict(x=rnd() * W, y=rnd() * H, r=(rnd() * 2.2 + 1.2) * NET["node_size"])
        n["turq"] = rnd() < NET["turq_ratio"]
        n["vx"], n["vy"] = (rnd() - 0.5) * 26, (rnd() - 0.5) * 26
        n.update(ph=rnd() * 6.283, drift=True, pulse=True, strength=1, reach=NET["link_dist"],
                 lw=NET["node_size"] * NET["link_width"], opacity=NET["opacity"])
        nodes.append(n)
    return nodes


def shape_nodes(points):
    xs, ys = [p["x"] for p in points], [p["y"] for p in points]
    bw, bh = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    m = SHAPE["margin"]
    aw, ah = W - 2 * m, H - 2 * m
    s = min(aw / bw, ah / bh)
    ox, oy = m + (aw - bw * s) / 2 - min(xs) * s, m + (ah - bh * s) / 2 - min(ys) * s
    rnd = mulberry32(NET["seed"] + 9781)
    nodes = []
    for p in points:
        r = p["r"] if "r" in p else rnd() * 2.2 + 1.2
        turq = p["turq"] if "turq" in p else rnd() < NET["turq_ratio"]
        nodes.append(dict(x=p["x"] * s + ox, y=p["y"] * s + oy, r=r * SHAPE["node_size"], turq=turq, vx=0, vy=0,
                          ph=rnd() * 6.283, drift=False, pulse=False, strength=SHAPE["strength"],
                          reach=SHAPE["link_dist"], lw=SHAPE["node_size"] * SHAPE["link_width"], opacity=NET["opacity"]))
    return nodes


def connect(A, B, same):
    out = []
    for i, a in enumerate(A):
        for b in A[i + 1:] if same else B:
            L = max(a["reach"], b["reach"])
            dx, dy = a["x"] - b["x"], a["y"] - b["y"]
            if abs(dx) > L or abs(dy) > L:
                continue
            d = math.hypot(dx, dy)
            if d < L:
                out.append((a, b, (1 - d / L) * 0.5))
    return out


def link_style(a, b, al):
    tq = a["turq"] and b["turq"]
    st = (a["strength"] + b["strength"]) / 2
    alpha = min(1, max(0, (a["opacity"] + b["opacity"]) / 2 * (al if tq else al * 0.9) * st))
    width = max(0.2, 0.7 * (a["lw"] + b["lw"]) / 2 * st)
    return TURQ if tq else ORANGE, round(alpha * 16) / 16, (round(width * 4) / 4) or 0.25


def node_style(n, t):
    pulse = 1 + 0.18 * math.sin(t * 1.5 + n["ph"]) if n["pulse"] else 1
    r = max(0.3, n["r"] * n["strength"] * pulse)
    alpha = round(min(1, n["opacity"] * n["strength"]) * 16) / 16
    return r, alpha, r + 6 * n["strength"]


def f1(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def link_paths(links, coarse=False):
    """drawNet's batching: one path per color, alpha step and width. moving links use whole pixels."""
    batch = defaultdict(list)
    for a, b, al in links:
        col, alpha, width = link_style(a, b, al)
        if alpha <= 0.03:
            continue
        if coarse:
            x, y = round(a["x"]), round(a["y"])
            batch[(col, alpha, width)].append(f"M{x} {y}l{round(b['x']) - x} {round(b['y']) - y}")
        else:
            batch[(col, alpha, width)].append(f"M{f1(a['x'])} {f1(a['y'])}L{f1(b['x'])} {f1(b['y'])}")
    return "".join(f'<path d="{"".join(d)}" stroke="{c}" stroke-opacity="{al:g}" stroke-width="{w:g}"/>'
                   for (c, al, w), d in batch.items())


def glows(nodes, t):
    out = []
    for n in nodes:
        r, alpha, spread = node_style(n, t)
        out.append(f'<circle cx="{f1(n["x"])}" cy="{f1(n["y"])}" r="{f1(spread)}" '
                   f'fill="url(#{"gt" if n["turq"] else "go"})" opacity="{alpha * 0.55:.2f}"/>')
    return "".join(out)


def cores(nodes, t):
    out = []
    for n in nodes:
        r, alpha, _ = node_style(n, t)
        out.append(f'<circle cx="{f1(n["x"])}" cy="{f1(n["y"])}" r="{r:.2f}" '
                   f'fill="{TURQ if n["turq"] else ORANGE}" fill-opacity="{alpha:g}"/>')
    return "".join(out)


def main():
    points, wordmark = site_data()
    drift, anchored = drifting_nodes(), shape_nodes(points)
    fixed_links = connect(anchored, anchored, True)

    frames, t = [], 0.0
    for _ in range(FPS * SECONDS):
        d = (1 / FPS) * NET["speed"]
        t += d
        for n in drift:
            n["x"] += n["vx"] * d
            n["y"] += n["vy"] * d
            if n["x"] < -12: n["x"] += W + 24
            if n["x"] > W + 12: n["x"] -= W + 24
            if n["y"] < -12: n["y"] += H + 24
            if n["y"] > H + 12: n["y"] -= H + 24
        links = connect(drift, drift, True) + connect(drift, anchored, False)
        snap = [dict(n) for n in drift]
        ids = {id(n): s for n, s in zip(drift, snap)}
        links = [(ids.get(id(a), a), ids.get(id(b), b), al) for a, b, al in links]
        frames.append((t, snap, links))

    F = len(frames)
    S = 2 * F - 2
    kt = lambda s: f"{s / S:.4f}"

    def show(i):
        if i == 0:
            return f'values="visible;hidden" keyTimes="0;{kt(1)}"'
        if i == F - 1:
            return f'values="hidden;visible;hidden" keyTimes="0;{kt(i)};{kt(i + 1)}"'
        return f'values="hidden;visible;hidden;visible;hidden" keyTimes="0;{kt(i)};{kt(i + 1)};{kt(S - i)};{kt(S - i + 1)}"'

    def layer(draw):
        return "\n".join(
            f'<g{" visibility=\"hidden\"" if i else ""}><animate attributeName="visibility" calcMode="discrete" '
            f'dur="{S / FPS:.2f}s" repeatCount="indefinite" {show(i)}/>{draw(fr)}</g>'
            for i, fr in enumerate(frames))

    wm_paths = "".join(re.findall(r"<path\b[^>]*?(?:/>|>\s*</path>)", wordmark))
    _, _, ww, wh = (float(v) for v in re.search(r'viewBox="([^"]+)"', wordmark).group(1).split())
    wm_w = 288
    wm_h = wm_w * wh / ww
    stops = [(0, 0.85), (0.18, 0.55), (0.42, 0.22), (0.7, 0.06), (1, 0)]
    grad = lambda gid, col: (f'<radialGradient id="{gid}">'
                             + "".join(f'<stop offset="{o}" stop-color="{col}" stop-opacity="{a}"/>' for o, a in stops)
                             + "</radialGradient>")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="node-K, hackspace klagenfurt">
<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
{grad("go", ORANGE)}{grad("gt", TURQ)}
<radialGradient id="veil" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{BG}" stop-opacity=".72"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
</defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<g opacity=".8">
<g fill="none" stroke-linecap="round">{link_paths(fixed_links)}
{layer(lambda fr: link_paths(fr[2], coarse=True))}
</g>
<g>{glows(anchored, 0)}
{layer(lambda fr: glows(fr[1], fr[0]))}
</g>
<g>{cores(anchored, 0)}
{layer(lambda fr: cores(fr[1], fr[0]))}
</g>
</g>
<ellipse cx="{W / 2:g}" cy="{H / 2:g}" rx="{W * 0.28:.1f}" ry="{H * 0.3:.1f}" fill="url(#veil)"/>
<g transform="translate({f1((W - wm_w) / 2)} {f1((H - wm_h) / 2)}) scale({wm_w / ww:.4f})">{wm_paths}</g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#2a2a2a"/>
</svg>
'''
    dest = Path(__file__).resolve().parent.parent / "assets" / "node-k.svg"
    dest.write_text(svg, encoding="utf-8")
    print(f"wrote {dest.name} ({len(svg) // 1024} kb): {len(anchored)} carinthia nodes, {len(drift)} drifting, "
          f"{len(fixed_links)} fixed links, {F} frames")


if __name__ == "__main__":
    main()
