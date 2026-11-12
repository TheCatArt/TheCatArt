#!/usr/bin/env python3
"""writes assets/icons/*.svg and the stack block in README.md (between the stack markers).

logos come from simple icons in their real brand colors. a few brands made simple icons drop
them (adobe, java, c#, canva, twitter), those come from the last release that still had them.
tools simple icons never had (the *arr stack, flaresolverr, rapid7, exploit-db) use their projects'
own logos as they are. kotlin uses its old colorful logo. a color that disappears on github's background gets nudged
just enough to read: black logos turn white in dark mode, pale ones darken in light mode.
"""
import base64
import colorsys
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GH_DARK, GH_LIGHT = "#0D1117", "#FFFFFF"
UA = {"User-Agent": "Mozilla/5.0 (profile-readme-build)"}
SIZE = 30

OLD = "https://cdn.jsdelivr.net/npm/simple-icons@{v}/icons/{slug}.svg"
PINNED = {  # slug: (source url, brand hex)
    "adobephotoshop": (OLD.format(v="10.4.0", slug="adobephotoshop"), "31A8FF"),
    "adobeillustrator": (OLD.format(v="10.4.0", slug="adobeillustrator"), "FF9A00"),
    "adobepremierepro": (OLD.format(v="10.4.0", slug="adobepremierepro"), "9999FF"),
    "adobeaftereffects": (OLD.format(v="10.4.0", slug="adobeaftereffects"), "9999FF"),
    "adobelightroom": (OLD.format(v="10.4.0", slug="adobelightroom"), "31A8FF"),
    "adobeaudition": (OLD.format(v="10.4.0", slug="adobeaudition"), "9999FF"),
    "csharp": (OLD.format(v="10.4.0", slug="csharp"), "512BD4"),
    "canva": (OLD.format(v="10.4.0", slug="canva"), "00C4CC"),
    "java": (OLD.format(v="6.23.0", slug="java"), "007396"),
    "twitter": (OLD.format(v="10.4.0", slug="twitter"), "1D9BF0"),
    "papermc": ("https://raw.githubusercontent.com/PaperMC/website/HEAD/src/assets/brand/paper.svg", "FFFFFF"),
}

# not in simple icons at all: the projects' own logos, kept in their own colors
GH_RAW = "https://raw.githubusercontent.com/{}/HEAD/{}"
ORIGINAL = {  # slug: (source url, optional crop)
    "jellyseerr": (GH_RAW.format("Fallenbagel/jellyseerr", "public/os_icon.svg"), None),
    "prowlarr": (GH_RAW.format("Prowlarr/Prowlarr", "frontend/src/Content/Images/logo.svg"), None),
    "lidarr": (GH_RAW.format("Lidarr/Lidarr", "frontend/src/Content/Images/logo.svg"), None),
    "flaresolverr": (GH_RAW.format("FlareSolverr/FlareSolverr", "resources/flaresolverr_logo.svg"), None),
    # the rapid7 wordmark; the icon is just its orange 7 mark on the right
    "rapid7": ("https://www.rapid7.com/cdn/images/blt3da7d9f2fa8a488c/6724caccac1d71e009a67c69/Rapid7_logo.svg",
               ("#E95F26", "210 -8 62 62")),
}
PNG = {  # exploit-db only ships its spider as a png
    "exploitdb": "https://www.exploit-db.com/images/spider-orange.png",
}

# the 2016 kotlin logo, the colorful one
KOTLIN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>kotlin</title><defs>
<linearGradient id="kb" gradientUnits="userSpaceOnUse" x1="2" y1="26" x2="18" y2="14"><stop offset=".1" stop-color="#0095D5"/><stop offset=".3" stop-color="#238AD9"/><stop offset=".62" stop-color="#557BDE"/><stop offset=".86" stop-color="#7472E2"/><stop offset="1" stop-color="#806EE3"/></linearGradient>
<linearGradient id="kt" gradientUnits="userSpaceOnUse" x1="0" y1="11" x2="11" y2="0"><stop offset=".1" stop-color="#0095D5"/><stop offset=".3" stop-color="#238AD9"/><stop offset=".62" stop-color="#557BDE"/><stop offset=".86" stop-color="#7472E2"/><stop offset="1" stop-color="#806EE3"/></linearGradient>
<linearGradient id="ko" gradientUnits="userSpaceOnUse" x1="1" y1="23" x2="20" y2="4"><stop offset=".11" stop-color="#C757BC"/><stop offset=".17" stop-color="#D0609A"/><stop offset=".31" stop-color="#E1725C"/><stop offset=".42" stop-color="#EE7E2F"/><stop offset=".51" stop-color="#F58613"/><stop offset=".57" stop-color="#F88909"/></linearGradient>
</defs><path d="M0 0H12L0 12.65Z" fill="url(#kt)"/><path d="M12 0H24L0 24V12.65Z" fill="url(#ko)"/><path d="M0 24L12 12L24 24Z" fill="url(#kb)"/></svg>
"""

STACK = [
    ("languages", [("javascript", "javascript"), ("typescript", "typescript"), ("python", "python"),
                   ("java", "java"), ("kotlin", "kotlin"), ("php", "php"), ("rust", "rust"), ("lua", "lua"),
                   ("bash", "gnubash"), ("c", "c"), ("c#", "csharp"), ("c++", "cplusplus"), ("qml", "qt"),
                   ("html", "html5"), ("css", "css")]),
    ("web, apps & games", [("react", "react"), ("next.js", "nextdotjs"), ("vite", "vite"), ("tailwind", "tailwindcss"),
                           ("astro", "astro"), ("three.js", "threedotjs"), ("d3", "d3"), ("react native", "expo"),
                           ("jetpack compose", "jetpackcompose"), ("unity", "unity")]),
    ("backend & data", [("node.js", "nodedotjs"), ("express", "express"), ("fastapi", "fastapi"),
                        ("discord.js", "discorddotjs"), ("mysql", "mysql"), ("mariadb", "mariadb"),
                        ("postgresql", "postgresql"), ("sqlite", "sqlite"), ("paper plugins", "papermc"),
                        ("gradle", "gradle"), ("claude api", "claude"), ("mcp", "modelcontextprotocol")]),
    ("selfhosting & infra", [("arch linux", "archlinux"), ("hyprland", "hyprland"), ("docker", "docker"),
                             ("caddy", "caddy"), ("nginx", "nginx"), ("cloudflare", "cloudflare"),
                             ("github actions", "githubactions"), ("jellyfin", "jellyfin"), ("jellyseerr", "jellyseerr"),
                             ("sonarr", "sonarr"), ("radarr", "radarr"), ("lidarr", "lidarr"), ("prowlarr", "prowlarr"),
                             ("qbittorrent", "qbittorrent"), ("flaresolverr", "flaresolverr"),
                             ("pi-hole", "pihole"), ("wireguard", "wireguard"),
                             ("home assistant", "homeassistant"), ("raspberry pi", "raspberrypi")]),
    ("security", [("burp suite", "burpsuite"), ("wireshark", "wireshark"), ("metasploit", "metasploit"),
                  ("rapid7", "rapid7"), ("exploit-db", "exploitdb"),
                  ("kali linux", "kalilinux"), ("hack the box", "hackthebox"), ("tryhackme", "tryhackme"),
                  ("owasp", "owasp"), ("tor", "torproject")]),
    ("design & video", [("figma", "figma"), ("blender", "blender"), ("krita", "krita"), ("gimp", "gimp"),
                        ("photoshop", "adobephotoshop"), ("illustrator", "adobeillustrator"),
                        ("premiere pro", "adobepremierepro"), ("after effects", "adobeaftereffects"),
                        ("lightroom", "adobelightroom"), ("audition", "adobeaudition"), ("canva", "canva")]),
]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read().decode()


def lum(h):
    r, g, b = (int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def readable(hexc, bg, need):
    """the brand color, or the closest version of it that still shows up on bg."""
    hexc = "#" + hexc.lstrip("#").upper()
    ratio = lambda c: (max(lum(c), lum(bg)) + 0.05) / (min(lum(c), lum(bg)) + 0.05)
    if ratio(hexc) >= need:
        return hexc
    dark_bg = lum(bg) < 0.2
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.15:
        return "#FFFFFF" if dark_bg else "#171717"
    step = 0.02 if dark_bg else -0.02
    while 0.05 < l < 0.95:
        l += step
        c = "#" + "".join(f"{round(v * 255):02X}" for v in colorsys.hls_to_rgb(h, l, s))
        if ratio(c) >= need:
            return c
    return "#FFFFFF" if dark_bg else "#171717"


def original_svg(slug, title):
    url, crop = ORIGINAL[slug]
    src = get(url)
    if re.search(r"<script|<foreignObject|\son\w+=|href=\"(?:https?:|//)", src, re.I):
        raise SystemExit(f"{slug}: logo has scripts or external references, not using it")
    src = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->", "", src, flags=re.S).strip()
    if crop:
        color, box = crop
        paths = "".join(p for p in re.findall(r"<path\b[^>]*?/?>(?:</path>)?", src) if color.lower() in p.lower())
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}"><title>{title}</title>{paths}</svg>\n'
    tag = re.search(r"<svg\b[^>]*>", src).group(0)
    new_tag = tag
    if "viewBox" not in tag:
        w = re.search(r'\bwidth="([\d.]+)', tag).group(1)
        h = re.search(r'\bheight="([\d.]+)', tag).group(1)
        new_tag = new_tag.replace("<svg", f'<svg viewBox="0 0 {w} {h}"', 1)
    return src.replace(tag, new_tag + f"<title>{title}</title>", 1) + "\n"


def png_svg(slug, title):
    req = urllib.request.Request(PNG[slug], headers=UA)
    data = base64.b64encode(urllib.request.urlopen(req).read()).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><title>{title}</title>'
            f'<image href="data:image/png;base64,{data}" width="64" height="64"/></svg>\n')


def icon_svg(slug, title):
    if slug == "kotlin":
        return KOTLIN
    if slug in ORIGINAL:
        return original_svg(slug, title)
    if slug in PNG:
        return png_svg(slug, title)
    if slug in PINNED:
        url, hexc = PINNED[slug]
        src = get(url)
    else:
        src = get(f"https://cdn.simpleicons.org/{slug}")
        hexc = re.search(r'fill="#([0-9A-Fa-f]{6})"', src).group(1)
    paths = "".join(re.sub(r'\s(fill|stroke)="[^"]*"', "", p) for p in re.findall(r"<path\b[^>]*?/?>(?:</path>)?", src))
    light, dark = readable(hexc, GH_LIGHT, 1.6), readable(hexc, GH_DARK, 3.0)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>{title}</title>'
            f'<style>path{{fill:{light}}}@media (prefers-color-scheme:dark){{path{{fill:{dark}}}}}</style>'
            f'{paths}</svg>\n')


def main():
    icons = ROOT / "assets" / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    blocks = []
    for n, (title, items) in enumerate(STACK):
        imgs = []
        for name, slug in items:
            (icons / f"{slug}.svg").write_text(icon_svg(slug, name), encoding="utf-8")
            imgs.append(f'<img src="assets/icons/{slug}.svg" width="{SIZE}" height="{SIZE}" title="{name}" alt="{name}">')
        blocks.append(f'<details{" open" if n == 0 else ""}>\n<summary><b>{title}</b></summary>\n<br>\n\n'
                      + "&nbsp;&nbsp;\n".join(imgs) + "\n\n</details>")
    (icons / "twitter.svg").write_text(icon_svg("twitter", "twitter"), encoding="utf-8")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = "<!-- stack:start (generated by scripts/stack.py) -->\n" + "\n\n".join(blocks) + "\n<!-- stack:end -->"
    text, n = re.subn(r"<!-- stack:start.*?<!-- stack:end -->", lambda m: block, text, flags=re.S)
    if not n:
        raise SystemExit("no stack markers in README.md")
    readme.write_text(text, encoding="utf-8")
    print(f"wrote {sum(len(i) for _, i in STACK)} icons and the stack block")


if __name__ == "__main__":
    main()
