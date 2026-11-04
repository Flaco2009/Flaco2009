#!/usr/bin/env python3
"""Live fire-watchtower banner above a sea of treetops.
Season follows the date, light follows the real sun position in Zurich."""
import math
import random
import sys
from datetime import datetime, timezone

LAT, LON = 47.3769, 8.5417  # Zurich
W, H = 1200, 320


# ---------- sun ----------
def sun_position(now_utc):
    doy = now_utc.timetuple().tm_yday
    hour = now_utc.hour + now_utc.minute / 60
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    ha = (hour * 60 + eqt + 4 * LON) / 4 - 180
    lat = math.radians(LAT)
    cz = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(math.radians(ha))
    return 90 - math.degrees(math.acos(max(-1, min(1, cz)))), ha


def season_of(dt):
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(dt.month, "autumn")


# ---------- color ----------
def rgb(c):
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(rgb(a), rgb(b)))


NIGHT = dict(top="#050918", mid="#0e1735", bot="#253157", haze="#36426b", mtn="#29345e",
             msnow="#8592c0", tint="#141d44", k=0.6)
DUSK = dict(top="#222c5a", mid="#68598c", bot="#f19d76", haze="#c296a0", mtn="#69669a",
            msnow="#f4d5cf", tint="#f09a72", k=0.14)
DAY = dict(top="#3a89d4", mid="#7ab5e8", bot="#dbeeff", haze="#c6dcf1", mtn="#8fb0d3",
           msnow="#ffffff", tint="#ffffff", k=0.0)

SEASON = {
    "spring": dict(con=["#3c6f47", "#467b4e", "#335f3f"], acc=["#86c35d", "#a4d36d", "#6fae4f"], acc_frac=.32,
                   round=True, cap=40, snowtips=False, bloom=["#f7c3d4", "#ffffff", "#f3a9c2"],
                   haze_shift="#e8f3e0"),
    "summer": dict(con=["#1f4d37", "#245740", "#1a4230"], acc=["#3b7a3a", "#4a8a3e", "#32702f"], acc_frac=.3,
                   round=True, cap=16, snowtips=False, bloom=None, haze_shift="#f3ecd4"),
    "autumn": dict(con=["#2a4a3a", "#2f5240", "#243f33"], acc=["#e0892b", "#cf5a2e", "#e8b440", "#b8412c", "#d97a2a"],
                   acc_frac=.36, round=True, cap=30, snowtips=False, bloom=None, haze_shift="#f1d8c0"),
    "winter": dict(con=["#193731", "#1e3f38", "#15302b"], acc=[], acc_frac=0, round=False, cap=70,
                   snowtips=True, bloom=None, haze_shift="#e6edf7"),
}


def sky(elev):
    if elev <= -9:
        return dict(NIGHT)
    if elev >= 12:
        return dict(DAY)
    a, b, t = (NIGHT, DUSK, (elev + 9) / 9) if elev < 0 else (DUSK, DAY, elev / 12)
    return {k: (mix(a[k], b[k], t) if isinstance(a[k], str) else a[k] + (b[k] - a[k]) * t) for k in a}


def poly(pts):
    return "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts) + "Z"


# ---------- trees (tops only) ----------
def conifer(rnd, x, base, h, wf):
    w = h * wf * rnd.uniform(0.85, 1.15)
    apex = (x + rnd.uniform(-0.8, 0.8), base - h)
    sides, snow = [], []
    for s in (-1, 1):
        pts, prev = [], apex
        for i in range(4):
            t = (i + 1) / 4
            yb = base - h + h * t
            ww = w * t ** 0.85 * rnd.uniform(0.85, 1.12)
            tip = (x + s * ww, yb + rnd.uniform(-1, 1))
            notch = (x + s * ww * 0.48, yb - h * 0.035)
            ax, ay = prev
            bx, by = tip
            snow.append([(ax, ay), (bx, by - .4), (ax + (bx - ax) * .6, ay + (by - ay) * .6 + max(1.6, h * .045))])
            pts += [tip, notch]
            prev = notch
        pts.append((x + s * w * 1.02, H + 10))
        sides.append(pts)
    return [*sides[0][::-1], apex, *sides[1]], snow


def crown(rnd, x, base, h):
    r = h * 0.3
    d = ""
    for dx, dy, rr in ((0, -h * 0.62, r), (-r * 0.75, -h * 0.45, r * 0.85), (r * 0.75, -h * 0.47, r * 0.85)):
        cx, cy, rr = x + dx, base + dy, rr * rnd.uniform(0.9, 1.1)
        d += f"M{cx - rr:.1f} {cy:.1f}a{rr:.1f} {rr:.1f} 0 1 0 {2 * rr:.1f} 0a{rr:.1f} {rr:.1f} 0 1 0 {-2 * rr:.1f} 0"
    d += poly([(x - r * 1.2, base - h * 0.42), (x + r * 1.2, base - h * 0.42), (x + r * 1.05, base - h * 0.1), (x + r * 1.7, H + 10), (x - r * 1.7, H + 10), (x - r * 1.05, base - h * 0.1)])
    return d


def canopy(rnd, base, hmin, hmax, wf, spacing, k, S, haze, T, bloom_n=0):
    groups, snow, blooms = {}, [], []
    xs = [i * spacing + rnd.uniform(-spacing * .35, spacing * .35) for i in range(-1, int(W / spacing) + 2)]
    for x in xs:
        b = base + rnd.uniform(-4, 4) + 3 * math.sin(x / 90)
        h = rnd.uniform(hmin, hmax)
        if S["acc"] and rnd.random() < S["acc_frac"]:
            col = rnd.choice(S["acc"])
            if S["round"] and rnd.random() < 0.38:
                d = crown(rnd, x, b, h * 0.9)
            else:
                d = poly(conifer(rnd, x, b, h, wf)[0])
        else:
            col = rnd.choice(S["con"])
            pts, sn = conifer(rnd, x, b, h, wf)
            d = poly(pts)
            if S["snowtips"]:
                snow += [poly(q) for q in sn]
        groups.setdefault(col, []).append(d)
    if S["bloom"] and bloom_n:
        for _ in range(bloom_n):
            blooms.append((rnd.uniform(0, W), base - rnd.uniform(-6, hmax * .5), rnd.choice(S["bloom"])))
    out = "".join(f'<path d="{"".join(ds)}" fill="{T(mix(c, haze, k))}"/>' for c, ds in groups.items())
    if snow:
        out += f'<path d="{"".join(snow)}" fill="{T(mix("#f4f7fc", haze, k * .8), .8)}"/>'
    for x, y, c in blooms:
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.2, 2.4):.1f}" fill="{T(mix(c, haze, k))}"/>'
    return out


# ---------- scene ----------
def build(now_utc, season=None):
    elev, ha = sun_position(now_utc)
    season = season or season_of(now_utc)
    S = SEASON[season]
    p = sky(elev)
    haze = mix(p["haze"], S["haze_shift"], 0.25 * (1 - min(1, max(0, (2 - elev) / 10))))
    nf = max(0.0, min(1.0, (3 - elev) / 11))           # 0 day .. 1 dark
    T = lambda c, k=1.0: mix(c, p["tint"], p["k"] * k)  # scene lighting
    rnd = random.Random(2009)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    o.append(f'''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["top"]}"/><stop offset=".62" stop-color="{p["mid"]}"/><stop offset="1" stop-color="{p["bot"]}"/></linearGradient>
<linearGradient id="fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{haze}" stop-opacity="0"/><stop offset=".7" stop-color="{haze}" stop-opacity=".6"/><stop offset="1" stop-color="{haze}" stop-opacity="0"/></linearGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#fff4c4" stop-opacity=".85"/><stop offset=".35" stop-color="#fff4c4" stop-opacity=".22"/><stop offset="1" stop-color="#fff4c4" stop-opacity="0"/></radialGradient>
<radialGradient id="warm"><stop offset="0" stop-color="#ffc36a" stop-opacity=".75"/><stop offset="1" stop-color="#ffc36a" stop-opacity="0"/></radialGradient>
<mask id="cres"><rect width="{W}" height="{H}" fill="#fff"/><circle id="mc" cx="0" cy="0" r="0" fill="#000"/></mask>
<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>
<style>
.fa{{animation:fa linear infinite}}@keyframes fa{{from{{transform:translateY(-14px)}}to{{transform:translateY({H + 16}px)}}}}
.sa{{animation:sa ease-in-out infinite alternate}}@keyframes sa{{from{{transform:translateX(-10px)}}to{{transform:translateX(10px)}}}}
.sb{{animation:sb ease-in-out infinite alternate}}@keyframes sb{{from{{transform:translateX(-26px)}}to{{transform:translateX(18px)}}}}
.sp{{transform-box:fill-box;transform-origin:center;animation:sp linear infinite}}@keyframes sp{{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}
.tw{{animation:tw 2.8s ease-in-out infinite alternate}}@keyframes tw{{from{{opacity:.15}}to{{opacity:1}}}}
.ff{{animation:ff ease-in-out infinite alternate}}@keyframes ff{{0%{{opacity:0;transform:translate(0,0)}}50%{{opacity:1}}100%{{opacity:.1;transform:translate(14px,-10px)}}}}
.fl{{transform-box:fill-box;transform-origin:left center;animation:fl 1.6s ease-in-out infinite alternate}}@keyframes fl{{from{{transform:skewY(-6deg) scaleX(.92)}}to{{transform:skewY(5deg) scaleX(1)}}}}
.bd{{animation:bd linear infinite}}@keyframes bd{{from{{transform:translateX(-120px)}}to{{transform:translateX({W + 120}px)}}}}
.wg{{transform-box:fill-box;transform-origin:center;animation:wg .45s ease-in-out infinite alternate}}@keyframes wg{{from{{transform:scaleY(1)}}to{{transform:scaleY(-.5)}}}}
.gl{{animation:gl 3.5s ease-in-out infinite alternate}}@keyframes gl{{from{{opacity:.6}}to{{opacity:1}}}}
</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>''')

    # stars
    if nf > 0.05:
        o.append(f'<g opacity="{nf:.2f}">')
        for _ in range(130):
            x, y, r = rnd.uniform(0, W), rnd.uniform(0, 175), rnd.choice([.5, .6, .7, .9, 1.1, 1.5])
            cls = ' class="tw"' if r > .8 else ""
            o.append(f'<circle{cls} cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" style="animation-delay:-{rnd.uniform(0, 3):.1f}s"/>')
        o.append('</g>')

    # sun / moon
    hx = W / 2 + max(-1, min(1, ha / 100)) * W * 0.45
    if elev > -4:
        sy = max(48, 200 - max(-4, elev) / 40 * 165)
        o.append(f'<circle cx="{hx:.0f}" cy="{sy:.0f}" r="115" fill="url(#halo)"/><circle cx="{hx:.0f}" cy="{sy:.0f}" r="20" fill="#fff6d6"/>')
    else:
        mx, my = W - hx, 60
        o[1] = o[1].replace('cx="0" cy="0" r="0"', f'cx="{mx + 8:.0f}" cy="{my - 5}" r="17"')
        o.append(f'<circle cx="{mx:.0f}" cy="{my}" r="80" fill="url(#halo)" opacity=".45"/><circle cx="{mx:.0f}" cy="{my}" r="18" fill="#eef0ff" mask="url(#cres)"/>')

    # mountains, snow cap depth depends on season
    peaks = [(0, 196), (80, 168), (150, 186), (240, 126), (310, 166), (372, 150), (444, 182), (534, 116),
             (622, 170), (700, 140), (772, 178), (860, 104), (948, 164), (1018, 134), (1096, 172), (1164, 146), (1200, 160)]
    md = f"M0 {H}"
    for i, (x, y) in enumerate(peaks):
        if i:
            px, py = peaks[i - 1]
            for f in (.33, .66):
                md += f" L{px + (x - px) * f:.0f} {py + (y - py) * f + rnd.uniform(-4, 4):.0f}"
        md += f" L{x} {y}"
    o.append(f'<path d="{md} L{W} {H}Z" fill="{mix(p["mtn"], haze, .2)}"/>')
    caps = ""
    for i in range(1, len(peaks) - 1):
        x, y = peaks[i]
        d = S["cap"] * (1.0 if y < 140 else 0.6 if y < 170 else 0.25)
        if d < 8:
            continue
        (lx, ly), (rx, ry) = peaks[i - 1], peaks[i + 1]
        a = (x - (x - lx) * min(.95, d / max(1, ly - y)), y + d)
        b = (x + (rx - x) * min(.95, d / max(1, ry - y)), y + d)
        jag = [(a[0] + (b[0] - a[0]) * f, y + d - (d * .3 if j % 2 else 0) + rnd.uniform(-2, 2))
               for j, f in enumerate((.18, .36, .54, .72, .88))]
        caps += poly([(x, y), a] + jag + [b])
    if caps:
        o.append(f'<path d="{caps}" fill="{p["msnow"]}" opacity=".92"/>')
    o.append(f'<rect y="135" width="{W}" height="110" fill="url(#fog)"/>')

    # canopy rows (far -> near). tower sits between row 2 and 3
    rows = [(206, 18, 30, .30, 9, .72, 0), (224, 26, 42, .32, 12, .54, 0), (246, 36, 58, .33, 17, .36, 20)]
    for i, r in enumerate(rows):
        o.append(canopy(rnd, *r[:6], S, haze, T, bloom_n=r[6]))
        o.append(f'<rect y="{r[0] - 30}" width="{W}" height="50" fill="url(#fog)" opacity="{.75 if season == "autumn" else .5}"/>')

    # ---- fire watchtower ----
    cx = 905
    lit = elev < 4
    wood, dark, roof = T("#7a5236"), T("#4a3022"), T("#3a2a22")
    legs = (f'<path d="M{cx-31} 152 L{cx-52} 330 M{cx+31} 152 L{cx+52} 330" stroke="{dark}" stroke-width="4.5"/>'
            f'<path d="M{cx-14} 152 L{cx-22} 330 M{cx+14} 152 L{cx+22} 330" stroke="{mix(dark, haze, .25)}" stroke-width="3"/>')
    br = ""
    for y1, y2 in ((156, 205), (205, 258), (258, 312)):
        w1, w2 = 31 + (y1 - 152) * 0.118, 31 + (y2 - 152) * 0.118
        br += f"M{cx-w1:.1f} {y1} L{cx+w2:.1f} {y2} M{cx+w1:.1f} {y1} L{cx-w2:.1f} {y2} M{cx-w2:.1f} {y2} L{cx+w2:.1f} {y2}"
    stairs = "".join(f"M{cx-10} {y} L{cx+10} {y+16}" for y in range(160, 300, 16))
    o.append(f'<g>{legs}<path d="{br}" stroke="{dark}" stroke-width="1.8" fill="none"/>'
             f'<path d="{stairs}" stroke="{mix(wood, haze, .15)}" stroke-width="1.6" fill="none"/></g>')
    if lit:
        o.append(f'<circle class="gl" cx="{cx}" cy="124" r="{70 + 40 * nf:.0f}" fill="url(#warm)" opacity="{.35 + .65 * nf:.2f}"/>')
    glass = "#ffc96e" if lit else T(mix("#a9cbe6", p["bot"], .3))
    o.append(f'''<g>
<rect x="{cx-34}" y="104" width="68" height="46" fill="{wood}"/>
<rect x="{cx-28}" y="111" width="56" height="21" fill="{glass}"/>
<path d="M{cx-7} 132 v-9 a4 4 0 0 1 8 0 v9Z M{cx-6} 120 h9 v-3 h-9Z" fill="{T("#22160f")}"/>
<path d="M{cx-14} 111 v21 M{cx} 111 v21 M{cx+14} 111 v21" stroke="{dark}" stroke-width="2"/>
<path d="M{cx-34} 120 h68" stroke="{dark}" stroke-width="1" opacity=".4"/>
<rect x="{cx-48}" y="149" width="96" height="5" fill="{dark}"/>
<path d="M{cx-46} 134 h92 {''.join(f'M{cx-46+i*11.5:.1f} 134 v15' for i in range(9))}" stroke="{dark}" stroke-width="1.6"/>
<path d="M{cx-46} 107 L{cx} 82 L{cx+46} 107Z" fill="{roof}"/>
{f'<path d="M{cx-48} 106 L{cx} 79 L{cx+48} 106 L{cx+40} 105 L{cx} 86 L{cx-40} 105Z" fill="{T("#eef3fa", .8)}"/>' if season == "winter" else ''}
<path d="M{cx} 82 V56" stroke="{dark}" stroke-width="1.6"/>
<path class="fl" d="M{cx+1} 57 q8 -2 15 1 q4 1 8 0 v9 q-4 1 -8 0 q-7 -3 -15 -1Z" fill="{T("#c8402e")}"/>
<circle cx="{cx}" cy="55" r="1.8" fill="{T("#d9b35a")}"/>
</g>''')

    # near rows hide the bottom of the tower
    for r in [(274, 52, 80, .34, 24, .16, 26), (306, 72, 112, .36, 34, 0, 30)]:
        o.append(canopy(rnd, *r[:6], S, haze, T, bloom_n=r[6]))

    # birds (daylight, not deep winter)
    if nf < .55:
        for gi in range(2 if season != "winter" else 1):
            dur, y0 = rnd.uniform(38, 55), rnd.uniform(70, 120)
            o.append(f'<g class="bd" style="animation-duration:{dur:.0f}s;animation-delay:-{rnd.uniform(0, dur):.0f}s">')
            for b in range(rnd.randint(3, 5)):
                bx, by = b * 14 + rnd.uniform(-4, 4), y0 + rnd.uniform(-9, 9)
                o.append(f'<path class="wg" style="animation-delay:-{rnd.uniform(0, .45):.2f}s" d="M{bx-6:.0f} {by-2:.0f} q3 -3 6 1 q3 -4 6 -1" stroke="{T("#2b2f3a")}" stroke-width="1.5" fill="none"/>')
            o.append('</g>')

    # handle
    o.append('<text x="30" y="38" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
             'font-size="13" letter-spacing="5" fill="#ffffff" opacity=".75">FLACO2009</text>')

    # season particles
    def falling(n, make, spd=(16, 26), sway="sa"):
        for _ in range(n):
            x, dur = rnd.uniform(-20, W + 20), rnd.uniform(*spd)
            o.append(f'<g class="fa" style="animation-duration:{dur:.1f}s;animation-delay:-{rnd.uniform(0, dur):.1f}s">'
                     f'<g class="{sway}" style="animation-duration:{rnd.uniform(2.5, 5):.1f}s;animation-delay:-{rnd.uniform(0, 5):.1f}s">'
                     f'{make(x)}</g></g>')

    if season == "winter":
        for n, a, b, op, spd, sw in ((70, .6, 1.2, .5, (16, 26), "sa"), (45, 1.3, 2.1, .75, (11, 17), "sa"), (16, 2.4, 3.6, .9, (7, 11), "sb")):
            falling(n, lambda x, a=a, b=b, op=op: f'<circle cx="{x:.0f}" cy="0" r="{rnd.uniform(a, b):.1f}" fill="#fff" opacity="{op}"/>', spd, sw)
    elif season == "autumn":
        cols = ["#e0892b", "#cf5a2e", "#e8b440", "#b8412c"]
        falling(26, lambda x: f'<path class="sp" style="animation-duration:{rnd.uniform(2.5, 6):.1f}s" d="M{x:.0f} 0 q4 -4 8 0 q-4 4 -8 0Z" fill="{T(rnd.choice(cols))}"/>', (12, 20), "sb")
    elif season == "spring":
        falling(18, lambda x: f'<ellipse class="sp" style="animation-duration:{rnd.uniform(3, 7):.1f}s" cx="{x:.0f}" cy="0" rx="2.6" ry="1.5" fill="{T(rnd.choice(["#f7c3d4", "#ffffff", "#f3a9c2"]))}"/>', (18, 28), "sb")
    if season in ("summer", "spring") and nf > .45:
        for _ in range(30 if season == "summer" else 12):
            x, y = rnd.uniform(0, W), rnd.uniform(215, 300)
            o.append(f'<circle class="ff" cx="{x:.0f}" cy="{y:.0f}" r="1.6" fill="#e9ff8a" '
                     f'style="animation-duration:{rnd.uniform(2, 4):.1f}s;animation-delay:-{rnd.uniform(0, 4):.1f}s"/>')

    o.append('</g></svg>')
    return "\n".join(o)


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    season = None
    if len(sys.argv) > 2:  # preview: generate.py out.svg 2026-11-04T22:00 [season]
        now = datetime.fromisoformat(sys.argv[2]).replace(tzinfo=timezone.utc)
    if len(sys.argv) > 3:
        season = sys.argv[3]
    path = sys.argv[1] if len(sys.argv) > 1 else "banner.svg"
    with open(path, "w") as f:
        f.write(build(now, season))
    print(f"wrote {path}")
