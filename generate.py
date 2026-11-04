#!/usr/bin/env python3
"""Live winter banner. Light, sky and glow follow the real sun position in Zurich."""
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


# ---------- color ----------
def rgb(c):
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(rgb(a), rgb(b)))


NIGHT = dict(top="#050918", mid="#0e1735", bot="#253157", haze="#36426b", mtn="#29345e",
             msnow="#8592c0", tree="#08151d", snow="#aebbe0", shade="#5f6ea6",
             tint="#16204a", k=0.55)
DUSK = dict(top="#222c5a", mid="#68598c", bot="#f19d76", haze="#c296a0", mtn="#69669a",
            msnow="#f4d5cf", tree="#172b31", snow="#f5e7ea", shade="#a59fcb",
            tint="#f09a72", k=0.12)
DAY = dict(top="#3a89d4", mid="#7ab5e8", bot="#dbeeff", haze="#c6dcf1", mtn="#8fb0d3",
           msnow="#ffffff", tree="#173f34", snow="#ffffff", shade="#b4cbe8",
           tint="#ffffff", k=0.0)


def palette(elev):
    if elev <= -9:
        return dict(NIGHT)
    if elev >= 12:
        return dict(DAY)
    a, b, t = (NIGHT, DUSK, (elev + 9) / 9) if elev < 0 else (DUSK, DAY, elev / 12)
    return {k: (mix(a[k], b[k], t) if isinstance(a[k], str) else a[k] + (b[k] - a[k]) * t) for k in a}


# ---------- shapes ----------
def pine(rnd, x, base, h, wide=0.34):
    """Irregular fir silhouette as polygon points + snow wedges."""
    tiers = max(4, min(9, int(h / 13)))
    tw = max(1.2, h * 0.035)
    wb = h * wide * rnd.uniform(0.85, 1.12)
    step = h * 0.9 / tiers
    left, right, snow = [], [], []
    for i in range(tiers):
        t = i / tiers
        yb = base - h * 0.07 - i * step
        yin = yb - step * 0.55
        for side, pts in ((-1, left), (1, right)):
            w = wb * (1 - t) ** 0.92 * rnd.uniform(0.82, 1.15)
            tip = (x + side * w, yb + h * 0.012 + rnd.uniform(-1, 1.5))
            inner = (x + side * w * 0.3, yin)
            pts += [tip, inner]
            ax, ay = inner
            bx, by = tip
            cx, cy = ax + (bx - ax) * 0.62, ay + (by - ay) * 0.62 + max(2.0, h * 0.018)
            snow.append([(ax, ay), (bx, by - 0.5), (cx, cy)])
    apex = (x + rnd.uniform(-1, 1), base - h)
    pts = [(x - tw, base), (x - tw, base - h * 0.07)] + left + [apex] + right[::-1] + \
          [(x + tw, base - h * 0.07), (x + tw, base)]
    snow.append([apex, (x - wb * 0.14, apex[1] + h * 0.09), (x + wb * 0.14, apex[1] + h * 0.09)])
    return pts, snow, wb


def poly(pts):
    return "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts) + "Z"


def ridge(rnd, base, amp):
    ph = [rnd.uniform(0, 6.3) for _ in range(3)]
    return lambda x: base + amp * (math.sin(x / 130 + ph[0]) + 0.5 * math.sin(x / 47 + ph[1])
                                   + 0.25 * math.sin(x / 19 + ph[2]))


def forest(rnd, base, amp, hmin, hmax, spacing, color, snow_color=None, xs=None, ground=True):
    y = ridge(rnd, base, amp)
    d = "" if not ground else "M0 " + f"{H}" + "".join(f" L{x} {y(x):.1f}" for x in range(0, W + 11, 10)) + f" L{W} {H}Z"
    if not ground:
        d = ""
    sd = []
    xs = xs or [i * spacing + rnd.uniform(-spacing * .4, spacing * .4) for i in range(int(W / spacing) + 2)]
    for x in xs:
        pts, snow, _ = pine(rnd, x, y(x) + 3, rnd.uniform(hmin, hmax))
        d += poly(pts)
        if snow_color:
            sd += [poly(s) for s in snow]
    out = f'<path d="{d}" fill="{color}"/>'
    if snow_color:
        out += f'<path d="{"".join(sd)}" fill="{snow_color}"/>'
    return out, y


def star(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return poly(pts)


# ---------- scene ----------
def build(now_utc):
    elev, ha = sun_position(now_utc)
    p = palette(elev)
    nf = max(0.0, min(1.0, (3 - elev) / 11))     # 0 = full day, 1 = dark
    T = lambda c, k=1.0: mix(c, p["tint"], p["k"] * k)  # scene lighting on objects
    rnd = random.Random(2009)
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    o.append(f'''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["top"]}"/><stop offset=".6" stop-color="{p["mid"]}"/><stop offset="1" stop-color="{p["bot"]}"/></linearGradient>
<linearGradient id="fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["haze"]}" stop-opacity="0"/><stop offset=".7" stop-color="{p["haze"]}" stop-opacity=".55"/><stop offset="1" stop-color="{p["haze"]}" stop-opacity="0"/></linearGradient>
<linearGradient id="bank" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["snow"]}"/><stop offset="1" stop-color="{p["shade"]}"/></linearGradient>
<radialGradient id="ball" cx=".36" cy=".3" r=".8"><stop offset=".25" stop-color="{p["snow"]}"/><stop offset="1" stop-color="{p["shade"]}"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#fff4c4" stop-opacity=".85"/><stop offset=".35" stop-color="#fff4c4" stop-opacity=".25"/><stop offset="1" stop-color="#fff4c4" stop-opacity="0"/></radialGradient>
<radialGradient id="warm"><stop offset="0" stop-color="#ffc96b" stop-opacity=".7"/><stop offset="1" stop-color="#ffc96b" stop-opacity="0"/></radialGradient>
<linearGradient id="aur" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7cf5c0" stop-opacity="0"/><stop offset=".55" stop-color="#5ee6b0" stop-opacity=".55"/><stop offset="1" stop-color="#3fa0d8" stop-opacity="0"/></linearGradient>
<filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
<filter id="soft"><feGaussianBlur stdDeviation="1.2"/></filter>
<mask id="crescent"><rect width="{W}" height="{H}" fill="#fff"/><circle id="mcut" cx="0" cy="0" r="0" fill="#000"/></mask>
<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>
<style>
.fa{{animation:fall linear infinite}}@keyframes fall{{from{{transform:translateY(-12px)}}to{{transform:translateY({H + 14}px)}}}}
.sa{{animation:sa ease-in-out infinite alternate}}@keyframes sa{{from{{transform:translateX(-9px)}}to{{transform:translateX(9px)}}}}
.sb{{animation:sb ease-in-out infinite alternate}}@keyframes sb{{from{{transform:translateX(-22px)}}to{{transform:translateX(14px)}}}}
.tw{{animation:tw 2.8s ease-in-out infinite alternate}}@keyframes tw{{from{{opacity:.15}}to{{opacity:1}}}}
.bl{{animation:bl 1.3s ease-in-out infinite alternate}}@keyframes bl{{0%{{opacity:.25}}100%{{opacity:1}}}}
.au{{animation:au 9s ease-in-out infinite alternate}}@keyframes au{{from{{opacity:.35;transform:translateX(-30px)}}to{{opacity:.85;transform:translateX(30px)}}}}
.sm{{transform-box:fill-box;transform-origin:center;animation:sm 5s ease-out infinite}}@keyframes sm{{from{{opacity:.55;transform:translate(0,0) scale(.5)}}to{{opacity:0;transform:translate(-18px,-55px) scale(1.8)}}}}
.br{{transform-box:fill-box;transform-origin:center;animation:br 4s ease-out infinite}}@keyframes br{{0%,55%{{opacity:0;transform:translate(0,0) scale(.4)}}65%{{opacity:.55}}100%{{opacity:0;transform:translate(-14px,-6px) scale(1.6)}}}}
.gl{{animation:gl 3s ease-in-out infinite alternate}}@keyframes gl{{from{{opacity:.55}}to{{opacity:1}}}}
</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>''')

    # aurora (only properly dark)
    if elev < -10:
        o.append('<g filter="url(#blur)">'
                 '<path class="au" d="M-40 120 C180 40 360 150 600 70 S980 30 1240 110 L1240 170 C980 90 820 160 600 130 S200 110 -40 180Z" fill="url(#aur)"/>'
                 '<path class="au" style="animation-delay:-4s" d="M100 90 C300 20 520 110 760 50 S1100 60 1260 30 L1260 80 C1050 110 900 90 760 100 S320 80 100 140Z" fill="url(#aur)" opacity=".6"/>'
                 '</g>')

    # stars
    if nf > 0.05:
        o.append(f'<g opacity="{nf:.2f}">')
        for _ in range(140):
            x, y = rnd.uniform(0, W), rnd.uniform(0, 190) ** 1.0
            r = rnd.choice([0.5, 0.6, 0.7, 0.9, 1.1, 1.5])
            cls = ' class="tw"' if r > 0.8 else ""
            o.append(f'<circle{cls} cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" style="animation-delay:-{rnd.uniform(0,3):.1f}s"/>')
        o.append('</g>')
    else:
        for _ in range(140):
            rnd.uniform(0, 1); rnd.uniform(0, 1); rnd.choice([0]); rnd.uniform(0, 1)

    # sun or moon, x follows the hour angle
    hx = W / 2 + max(-1, min(1, ha / 100)) * W * 0.45
    if elev > -4:
        sy = 205 - max(-4, elev) / 40 * 170
        o.append(f'<circle cx="{hx:.0f}" cy="{sy:.0f}" r="110" fill="url(#halo)"/>'
                 f'<circle cx="{hx:.0f}" cy="{sy:.0f}" r="20" fill="#fff6d6"/>')
    else:
        mx, my = W - hx, 62
        o[1] = o[1].replace('cx="0" cy="0" r="0"', f'cx="{mx + 8:.0f}" cy="{my - 5}" r="17"')
        o.append(f'<circle cx="{mx:.0f}" cy="{my}" r="80" fill="url(#halo)" opacity=".45"/>'
                 f'<circle cx="{mx:.0f}" cy="{my}" r="18" fill="#eef0ff" mask="url(#crescent)"/>')

    # mountains with snow caps
    peaks = [(0, 205), (70, 176), (140, 194), (232, 132), (300, 172), (362, 156), (432, 188),
             (522, 122), (612, 178), (692, 146), (762, 184), (852, 110), (942, 172), (1012, 140),
             (1092, 178), (1162, 150), (1200, 166)]
    md = f"M0 {H}"
    for i, (x, y) in enumerate(peaks):
        if i:
            px, py = peaks[i - 1]
            for k in (0.33, 0.66):
                md += f" L{px + (x - px) * k:.0f} {py + (y - py) * k + rnd.uniform(-4, 4):.0f}"
        md += f" L{x} {y}"
    md += f" L{W} {H}Z"
    o.append(f'<path d="{md}" fill="{mix(p["mtn"], p["haze"], .25)}"/>')
    caps = ""
    for i in range(1, len(peaks) - 1):
        x, y = peaks[i]
        if y > 165:
            continue
        (lx, ly), (rx, ry) = peaks[i - 1], peaks[i + 1]
        d = 26
        a = (x - (x - lx) * d / (ly - y), y + d)
        b = (x + (rx - x) * d / (ry - y), y + d)
        jag = [(a[0] + (b[0] - a[0]) * f, y + d - (9 if j % 2 else 0) + rnd.uniform(-2, 3))
               for j, f in enumerate((0.2, 0.38, 0.55, 0.72, 0.86))]
        caps += poly([(x, y), a] + jag + [b])
    o.append(f'<path d="{caps}" fill="{p["msnow"]}" opacity=".9"/>')
    o.append(f'<rect y="140" width="{W}" height="120" fill="url(#fog)"/>')

    # forest layers, far to near
    l3, _ = forest(rnd, 224, 5, 20, 36, 8, mix(p["tree"], p["haze"], .68))
    o.append(l3)
    o.append(f'<rect y="200" width="{W}" height="60" fill="url(#fog)" opacity=".7"/>')
    l2, _ = forest(rnd, 240, 7, 34, 58, 13, mix(p["tree"], p["haze"], .42), mix(p["snow"], p["haze"], .45))
    o.append(l2)
    o.append(f'<path d="M0 262 Q200 246 420 256 T820 254 T1200 250 L1200 320 L0 320Z" fill="{mix(p["snow"], p["haze"], .3)}"/>')

    # cabin in the middle ground
    cx, cy = 236, 258
    lit = elev < 4
    o.append(f'''<g>
<path d="M{cx} {cy} v-30 h54 v30Z" fill="{T("#6e4a33")}"/>
<path d="M{cx-7} {cy-28} L{cx+27} {cy-52} L{cx+61} {cy-28}Z" fill="{T("#3d2a22")}"/>
<path d="M{cx-9} {cy-27} L{cx+27} {cy-55} L{cx+63} {cy-27} L{cx+56} {cy-28} L{cx+27} {cy-47} L{cx-2} {cy-28}Z" fill="{p["snow"]}"/>
<rect x="{cx+40}" y="{cy-58}" width="7" height="16" fill="{T("#4a3226")}"/>
<rect x="{cx+8}" y="{cy-21}" width="11" height="10" fill="{'#ffc76a' if lit else T('#9fbbd6')}"/>
<rect x="{cx+32}" y="{cy-19}" width="11" height="19" fill="{T("#33221a")}"/>
{f'<circle cx="{cx+13}" cy="{cy-16}" r="34" fill="url(#warm)" opacity="{0.4 + 0.6 * nf:.2f}"/>' if lit else ''}
<circle class="sm" cx="{cx+43}" cy="{cy-63}" r="5" fill="{mix("#e9edf5", p["haze"], .3)}"/>
<circle class="sm" cx="{cx+43}" cy="{cy-63}" r="5" fill="{mix("#e9edf5", p["haze"], .3)}" style="animation-delay:-1.7s"/>
<circle class="sm" cx="{cx+43}" cy="{cy-63}" r="5" fill="{mix("#e9edf5", p["haze"], .3)}" style="animation-delay:-3.4s"/>
</g>''')

    # near tree clusters at the sides (keep the middle open)
    xs = [rnd.uniform(0, 175) for _ in range(7)] + [rnd.uniform(320, 370) for _ in range(2)] + [rnd.uniform(960, 1200) for _ in range(9)]
    l1, _ = forest(rnd, 276, 6, 66, 112, 30, mix(p["tree"], p["haze"], .14), mix(p["snow"], p["haze"], .12), xs=xs, ground=False)
    o.append(l1)

    # foreground snow bank
    o.append(f'<path d="M0 290 C180 272 330 286 480 284 S760 276 900 284 S1100 280 1200 276 L1200 320 L0 320Z" fill="url(#bank)"/>')

    # ---- snowman ----
    sx, sb = 455, 300
    o.append(f'''<g>
<ellipse cx="{sx+6}" cy="{sb}" rx="40" ry="6" fill="{p["shade"]}" opacity=".7"/>
<circle cx="{sx}" cy="{sb-26}" r="28" fill="url(#ball)"/>
<circle cx="{sx}" cy="{sb-68}" r="20" fill="url(#ball)"/>
<circle cx="{sx}" cy="{sb-100}" r="15" fill="url(#ball)"/>
<path d="M{sx-19} {sb-72} Q{sx-38} {sb-80} {sx-52} {sb-96} M{sx-42} {sb-86} l-9 -3 M{sx-46} {sb-91} l1 -9" stroke="{T("#5b3d2b")}" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<path d="M{sx+19} {sb-70} Q{sx+36} {sb-70} {sx+50} {sb-58} M{sx+42} {sb-64} l7 -6" stroke="{T("#5b3d2b")}" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<path d="M{sx-15} {sb-111} Q{sx} {sb-136} {sx+15} {sb-111}Z" fill="{T("#c2402f")}"/>
<rect x="{sx-16}" y="{sb-114}" width="32" height="6" rx="3" fill="{T("#e8dccb")}"/>
<circle cx="{sx+2}" cy="{sb-134}" r="5" fill="{T("#e8dccb")}"/>
<circle cx="{sx-5}" cy="{sb-102}" r="1.9" fill="#1b1b22"/><circle cx="{sx+5}" cy="{sb-102}" r="1.9" fill="#1b1b22"/>
<path d="M{sx} {sb-98} l14 3 l-14 2Z" fill="{T("#e9782a")}"/>
<path d="M{sx-14} {sb-87} Q{sx} {sb-80} {sx+14} {sb-87} L{sx+13} {sb-82} Q{sx} {sb-75} {sx-13} {sb-82}Z" fill="{T("#2f6f8f")}"/>
<path d="M{sx+5} {sb-82} l2 20 l6 -1 l-2 -20Z" fill="{T("#28607c")}"/>
<path d="M{sx+7} {sb-62} v4 M{sx+10} {sb-62} v4 M{sx+13} {sb-63} v4" stroke="{T("#28607c")}" stroke-width="1.2"/>
<circle cx="{sx}" cy="{sb-70}" r="2" fill="#1b1b22"/><circle cx="{sx}" cy="{sb-60}" r="2" fill="#1b1b22"/><circle cx="{sx}" cy="{sb-35}" r="2.2" fill="#1b1b22"/>
</g>''')

    # ---- christmas tree ----
    tx, tb, th = 660, 298, 150
    tr = random.Random(77)
    pts, snow, wb = pine(tr, tx, tb, th, wide=0.42)
    o.append(f'<ellipse cx="{tx+8}" cy="{tb}" rx="62" ry="7" fill="{p["shade"]}" opacity=".7"/>')
    o.append(f'<path d="{poly(pts)}" fill="{T("#1d5a3d", 1.1)}"/>')
    o.append(f'<path d="{"".join(poly(s) for s in snow)}" fill="{p["snow"]}" opacity=".85"/>')

    def half(y):
        return wb * max(0.0, (tb - th * 0.07 - y) / -(th * 0.93) + 1) * 0.82

    gar = ""
    for k, (y1, y2) in enumerate([(tb - 120, tb - 100), (tb - 92, tb - 66), (tb - 58, tb - 30)]):
        x1, x2 = tx - half(y1), tx + half(y2)
        gar += f"M{x1:.0f} {y1} Q{tx:.0f} {(y1 + y2) / 2 + 14:.0f} {x2:.0f} {y2}"
    o.append(f'<path d="{gar}" stroke="{T("#e6c36a")}" stroke-width="1.6" fill="none" opacity=".9"/>')
    for _ in range(13):
        y = tr.uniform(tb - 118, tb - 22)
        x = tx + tr.uniform(-1, 1) * half(y) * 0.85
        c = tr.choice(["#c8373a", "#e2b44e", "#c8373a", "#d9dde6"])
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{T(c)}"/><circle cx="{x - 1:.1f}" cy="{y - 1.2:.1f}" r="1" fill="#fff" opacity=".8"/>')
    for i in range(28):
        y = tr.uniform(tb - 130, tb - 18)
        x = tx + tr.uniform(-1, 1) * half(y) * 0.92
        c = tr.choice(["#ffd98a", "#ffd98a", "#ff8a7a", "#9fd7ff", "#b6ffb0"])
        d = f"animation-delay:-{tr.uniform(0, 1.3):.2f}s;animation-duration:{tr.uniform(0.9, 1.8):.2f}s"
        if nf > 0.2:
            o.append(f'<circle class="bl" cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{c}" opacity="{0.35 * nf:.2f}" style="{d}"/>')
        o.append(f'<circle class="bl" cx="{x:.1f}" cy="{y:.1f}" r="1.7" fill="{c}" style="{d}"/>')
    ty = tb - th - 2
    o.append(f'<circle class="gl" cx="{tx}" cy="{ty}" r="{22 + 14 * nf:.0f}" fill="url(#halo)"/>')
    o.append(f'<path d="{star(tx, ty, 10)}" fill="#ffd45e"/>')
    # presents
    o.append(f'''<rect x="{tx-44}" y="{tb-15}" width="24" height="15" rx="1.5" fill="{T("#b8323a")}"/>
<rect x="{tx-34}" y="{tb-15}" width="4" height="15" fill="{T("#f0d58a")}"/><rect x="{tx-44}" y="{tb-10}" width="24" height="3.5" fill="{T("#f0d58a")}"/>
<rect x="{tx+22}" y="{tb-19}" width="19" height="19" rx="1.5" fill="{T("#2e7d82")}"/>
<rect x="{tx+29.5}" y="{tb-19}" width="4" height="19" fill="{T("#f4f1ea")}"/>
<path d="M{tx+31} {tb-19} q-7 -7 -9 -1 q4 3 9 1 q7 -7 9 -1 q-4 3 -9 1" fill="{T("#f4f1ea")}"/>
<path d="M{tx-70} {tb+2} Q{tx} {tb-10} {tx+70} {tb+2}Z" fill="{p["snow"]}"/>''')

    # ---- reindeer (faces the tree) ----
    rx, rb, s = 870, 298, 0.92
    body, dark, mane, ant = T("#8b5a3a"), T("#5e3b26"), T("#eadbc3"), T("#cdb185")
    o.append(f'<ellipse cx="{rx+4}" cy="{rb}" rx="46" ry="6" fill="{p["shade"]}" opacity=".7"/>')
    o.append(f'''<g transform="translate({rx} {rb}) scale({s})">
<path d="M18 -42 C22 -30 22 -18 24 -2 h6 C29 -18 30 -30 30 -40Z M31 -44 C36 -30 37 -18 38 -2 h6 C43 -18 43 -32 42 -44Z" fill="{dark}"/>
<path d="M-30 -42 C-29 -28 -30 -16 -30 -2 h6 C-23 -16 -22 -28 -20 -40Z M-19 -40 C-18 -28 -17 -16 -17 -2 h6 C-10 -16 -10 -28 -9 -40Z" fill="{dark}"/>
<path d="M-30 -1 h7 v3 h-7Z M-17 -1 h7 v3 h-7Z M25 -1 h7 v3 h-7Z M38 -1 h7 v3 h-7Z" fill="#241710"/>
<path d="M-36 -52 C-34 -66 -10 -66 14 -64 C32 -64 46 -60 46 -46 C46 -34 34 -32 20 -34 C4 -36 -14 -34 -26 -36 C-34 -38 -38 -44 -36 -52Z" fill="{body}"/>
<path d="M46 -58 q8 -2 6 6 q-5 -1 -6 -6Z" fill="{mane}"/>
<path d="M-24 -60 C-30 -72 -38 -82 -44 -92 L-58 -86 C-50 -76 -42 -58 -36 -44Z" fill="{body}"/>
<path d="M-34 -44 C-40 -56 -44 -66 -50 -76 C-46 -66 -50 -58 -44 -48Z" fill="{mane}"/>
<path d="M-40 -98 C-48 -102 -62 -98 -72 -90 C-76 -87 -74 -82 -69 -82 C-62 -82 -54 -82 -46 -84 C-40 -86 -36 -94 -40 -98Z" fill="{body}"/>
<circle cx="-72" cy="-86" r="2.6" fill="#241710"/>
<circle cx="-52" cy="-93" r="1.5" fill="#160d08"/>
<path d="M-42 -98 q8 -8 14 -6 q-6 6 -14 6Z" fill="{dark}"/>
<path d="M-46 -100 C-44 -116 -38 -126 -28 -136 M-42 -114 L-54 -124 M-36 -126 L-44 -140 M-31 -132 L-20 -140 M-50 -100 C-54 -116 -50 -130 -44 -144 M-52 -114 L-64 -120 M-50 -128 L-60 -138" stroke="{ant}" stroke-width="3.2" fill="none" stroke-linecap="round"/>
<circle class="br" cx="-80" cy="-84" r="5" fill="#fff" opacity="0"/>
</g>''')

    # big framing firs at the edges
    fr = random.Random(5)
    fd, fs = "", []
    for x, h in [(-6, 250), (44, 205), (1160, 220), (1214, 260)]:
        pts, snow, _ = pine(fr, x, 338, h)
        fd += poly(pts)
        fs += [poly(q) for q in snow]
    o.append(f'<path d="{fd}" fill="{mix(p["tree"], "#000000", .25)}"/>')
    o.append(f'<path d="{"".join(fs)}" fill="{mix(p["snow"], p["shade"], .25)}"/>')

    # sparkles on the snow in daylight
    if nf < 0.6:
        for _ in range(26):
            x, y = rnd.uniform(80, 1120), rnd.uniform(292, 316)
            o.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r=".9" fill="#fff" style="animation-delay:-{rnd.uniform(0,3):.1f}s"/>')

    # handle
    o.append(f'<text x="30" y="38" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="13" letter-spacing="5" fill="#ffffff" opacity=".75">FLACO2009</text>')

    # snowfall in three depths
    for n, rmin, rmax, op, spd, sway in ((70, .6, 1.2, .5, 1.0, "sa"), (45, 1.3, 2.1, .75, 1.5, "sa"), (16, 2.4, 3.6, .9, 2.4, "sb")):
        for _ in range(n):
            x = rnd.uniform(-20, W + 20)
            dur = rnd.uniform(16, 26) / spd
            o.append(f'<g class="fa" style="animation-duration:{dur:.1f}s;animation-delay:-{rnd.uniform(0, dur):.1f}s">'
                     f'<circle class="{sway}" cx="{x:.0f}" cy="0" r="{rnd.uniform(rmin, rmax):.1f}" fill="#fff" opacity="{op}" '
                     f'style="animation-duration:{rnd.uniform(2.5, 5):.1f}s;animation-delay:-{rnd.uniform(0, 5):.1f}s"/></g>')

    o.append('</g></svg>')
    return "\n".join(o)


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    if len(sys.argv) > 2:  # preview: generate.py out.svg 2026-11-04T22:00 (UTC)
        now = datetime.fromisoformat(sys.argv[2]).replace(tzinfo=timezone.utc)
    path = sys.argv[1] if len(sys.argv) > 1 else "banner.svg"
    with open(path, "w") as f:
        f.write(build(now))
    print(f"wrote {path}")
