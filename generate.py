#!/usr/bin/env python3
"""Live snowy forest banner: sky follows the real sun position in Zurich."""
import math
import random
import sys
from datetime import datetime, timezone

LAT, LON = 47.3769, 8.5417  # Zurich
W, H = 1200, 320


def sun_elevation(now_utc):
    """Solar elevation in degrees (NOAA approximation)."""
    doy = now_utc.timetuple().tm_yday
    hour = now_utc.hour + now_utc.minute / 60
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = hour * 60 + eqt + 4 * LON
    ha = math.radians(tst / 4 - 180)
    lat = math.radians(LAT)
    cos_z = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    elev = 90 - math.degrees(math.acos(max(-1, min(1, cos_z))))
    return elev, tst / 4 - 180  # elevation, hour angle in degrees


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def palette(elev):
    # night -> twilight -> day
    night = dict(top="#070b1f", bot="#1b2346", snow="#8e9bc4", tree="#0c1a24",
                 tree2="#13283a", mtn="#2a3560", light=0.0)
    dusk = dict(top="#2b3b7a", bot="#f2a27a", snow="#d9cde6", tree="#1d3a3a",
                tree2="#2a4d4a", mtn="#7a77a8", light=0.5)
    day = dict(top="#5aa7e8", bot="#d8eefc", snow="#ffffff", tree="#1f5a45",
               tree2="#2f7a5c", mtn="#a9c4de", light=1.0)
    if elev <= -8:
        return night
    if elev < 0:
        a, b, t = night, dusk, (elev + 8) / 8
    elif elev < 10:
        a, b, t = dusk, day, elev / 10
    else:
        return day
    return {k: (mix(a[k], b[k], t) if isinstance(a[k], str) else a[k] + (b[k] - a[k]) * t)
            for k in a}


def pine(x, base, h, color, snow):
    w = h * 0.45
    parts = [f'<rect x="{x - h*0.03:.1f}" y="{base - h*0.12:.1f}" width="{h*0.06:.1f}" height="{h*0.12:.1f}" fill="#3b2a20"/>']
    for i in range(3):
        top = base - h * (0.35 + 0.3 * i) - h * 0.1
        bw = w * (1 - 0.28 * i)
        bot = base - h * 0.1 - h * 0.28 * i
        parts.append(f'<polygon points="{x:.1f},{top:.1f} {x-bw/2:.1f},{bot:.1f} {x+bw/2:.1f},{bot:.1f}" fill="{color}"/>')
        # snow cap
        cap = (bot - top) * 0.35
        parts.append(f'<polygon points="{x:.1f},{top:.1f} {x-bw*0.18:.1f},{top+cap:.1f} {x:.1f},{top+cap*0.75:.1f} {x+bw*0.18:.1f},{top+cap:.1f}" fill="{snow}"/>')
    return "".join(parts)


def build(now_utc):
    elev, ha = sun_elevation(now_utc)
    p = palette(elev)
    is_night = elev < -4
    rnd = random.Random(2009)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    out.append(f'''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["top"]}"/><stop offset="1" stop-color="{p["bot"]}"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="#fff6c8" stop-opacity=".9"/><stop offset="1" stop-color="#fff6c8" stop-opacity="0"/></radialGradient>
<radialGradient id="lamp"><stop offset="0" stop-color="#ffcf6b" stop-opacity=".55"/><stop offset="1" stop-color="#ffcf6b" stop-opacity="0"/></radialGradient>
<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<style>
.f{{animation:fall linear infinite}}
@keyframes fall{{from{{transform:translate(0,-20px)}}to{{transform:translate(var(--dx),{H + 30}px)}}}}
.t{{animation:tw 3s ease-in-out infinite alternate}}
@keyframes tw{{from{{opacity:.2}}to{{opacity:1}}}}
.sm{{animation:smoke 6s ease-out infinite}}
@keyframes smoke{{from{{opacity:.6;transform:translate(0,0) scale(.6)}}to{{opacity:0;transform:translate(-20px,-60px) scale(1.6)}}}}
</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>''')

    # stars
    if elev < 2:
        op = max(0.0, min(1.0, (2 - elev) / 10))
        out.append(f'<g opacity="{op:.2f}">')
        for _ in range(90):
            x, y, r = rnd.uniform(0, W), rnd.uniform(0, H * 0.55), rnd.uniform(0.5, 1.6)
            out.append(f'<circle class="t" cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#fff" style="animation-delay:{rnd.uniform(0,3):.1f}s"/>')
        out.append('</g>')

    # sun / moon: x follows hour angle, y follows elevation
    sx = W / 2 + max(-1, min(1, ha / 90)) * (W * 0.42)
    if elev > -3:
        sy = H * 0.62 - max(-3, elev) / 60 * H * 0.6
        out.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="70" fill="url(#glow)"/><circle cx="{sx:.0f}" cy="{sy:.0f}" r="26" fill="#fff3b0"/>')
    else:
        mx = W - sx
        out.append(f'<circle cx="{mx:.0f}" cy="70" r="60" fill="url(#glow)" opacity=".5"/>'
                   f'<circle cx="{mx:.0f}" cy="70" r="22" fill="#eef1ff"/><circle cx="{mx+9:.0f}" cy="64" r="20" fill="{p["top"]}"/>')

    # mountains
    out.append(f'<path d="M0 230 L120 150 L210 200 L330 110 L450 190 L560 140 L700 210 L820 120 L960 200 L1080 140 L1200 190 L1200 320 L0 320Z" fill="{p["mtn"]}" opacity=".85"/>')
    out.append(f'<path d="M330 110 L300 135 L330 128 L355 140Z M820 120 L792 145 L820 137 L848 150Z" fill="{p["snow"]}"/>')

    # back trees
    for i in range(34):
        x = i * 37 + rnd.uniform(-10, 10)
        out.append(pine(x, 250 + rnd.uniform(-6, 6), rnd.uniform(55, 80), p["tree2"], p["snow"]))
    # ground
    out.append(f'<path d="M0 250 Q300 228 600 248 T1200 242 L1200 320 L0 320Z" fill="{p["snow"]}"/>')

    # cabin with chimney smoke (lights on at night)
    cx, cy = 900, 262
    win = "#ffcf6b" if is_night else "#a8c8e8"
    out.append(f'''<g>
<rect x="{cx}" y="{cy-40}" width="80" height="44" fill="#6b4630"/>
<polygon points="{cx-10},{cy-38} {cx+40},{cy-72} {cx+90},{cy-38}" fill="#4a2f22"/>
<polygon points="{cx-12},{cy-36} {cx+40},{cy-76} {cx+92},{cy-36} {cx+82},{cy-38} {cx+40},{cy-66} {cx-2},{cy-38}" fill="{p["snow"]}"/>
<rect x="{cx+58}" y="{cy-80}" width="10" height="22" fill="#5a3a2a"/>
<rect x="{cx+12}" y="{cy-28}" width="16" height="14" fill="{win}"/>
<rect x="{cx+50}" y="{cy-24}" width="16" height="28" fill="#3a2418"/>
{f'<circle cx="{cx+20}" cy="{cy-21}" r="40" fill="url(#lamp)"/>' if is_night else ''}
<circle class="sm" cx="{cx+63}" cy="{cy-86}" r="7" fill="#dfe3ea" style="transform-box:fill-box"/>
<circle class="sm" cx="{cx+63}" cy="{cy-86}" r="7" fill="#dfe3ea" style="transform-box:fill-box;animation-delay:2s"/>
<circle class="sm" cx="{cx+63}" cy="{cy-86}" r="7" fill="#dfe3ea" style="transform-box:fill-box;animation-delay:4s"/>
</g>''')

    # front trees
    for x, h in [(40, 150), (110, 120), (1080, 140), (1150, 170), (1010, 110), (180, 95)]:
        out.append(pine(x, 300, h, p["tree"], p["snow"]))
    out.append(f'<path d="M0 290 Q400 270 800 292 T1200 285 L1200 320 L0 320Z" fill="{p["snow"]}"/>')

    # snowman
    sx0, base = 560, 298
    out.append(f'''<g>
<ellipse cx="{sx0}" cy="{base+2}" rx="48" ry="7" fill="#000" opacity=".12"/>
<circle cx="{sx0}" cy="{base-30}" r="34" fill="#fbfdff" stroke="#c9d6e6" stroke-width="2"/>
<circle cx="{sx0}" cy="{base-84}" r="25" fill="#fbfdff" stroke="#c9d6e6" stroke-width="2"/>
<circle cx="{sx0}" cy="{base-124}" r="18" fill="#fbfdff" stroke="#c9d6e6" stroke-width="2"/>
<rect x="{sx0-17}" y="{base-147}" width="34" height="5" rx="2" fill="#1c1c1c"/>
<rect x="{sx0-11}" y="{base-170}" width="22" height="25" rx="2" fill="#1c1c1c"/>
<rect x="{sx0-11}" y="{base-153}" width="22" height="5" fill="#c0392b"/>
<circle cx="{sx0-6}" cy="{base-128}" r="2.4" fill="#1c1c1c"/><circle cx="{sx0+6}" cy="{base-128}" r="2.4" fill="#1c1c1c"/>
<polygon points="{sx0},{base-123} {sx0+20},{base-119} {sx0},{base-117}" fill="#e67e22"/>
<path d="M{sx0-8} {base-114} Q{sx0} {base-109} {sx0+8} {base-114}" stroke="#1c1c1c" stroke-width="2" fill="none" stroke-dasharray="1.5 3" stroke-linecap="round"/>
<path d="M{sx0-19} {base-108} Q{sx0} {base-100} {sx0+19} {base-108} L{sx0+17} {base-102} Q{sx0} {base-94} {sx0-17} {base-102}Z" fill="#c0392b"/>
<rect x="{sx0+6}" y="{base-104}" width="8" height="26" rx="3" fill="#a93226"/>
<circle cx="{sx0}" cy="{base-90}" r="2.6" fill="#1c1c1c"/><circle cx="{sx0}" cy="{base-78}" r="2.6" fill="#1c1c1c"/>
<path d="M{sx0-24} {base-88} L{sx0-60} {base-112} M{sx0-48} {base-104} L{sx0-56} {base-118}" stroke="#5a3a2a" stroke-width="3" stroke-linecap="round"/>
<path d="M{sx0+24} {base-88} L{sx0+60} {base-108} M{sx0+50} {base-102} L{sx0+62} {base-96}" stroke="#5a3a2a" stroke-width="3" stroke-linecap="round"/>
</g>''')

    # name
    out.append(f'<text x="{W/2}" y="52" text-anchor="middle" font-family="Segoe UI,Verdana,sans-serif" font-size="34" font-weight="700" fill="#fff" opacity=".92" style="paint-order:stroke" stroke="#000" stroke-opacity=".15" stroke-width="4">Flaco2009</text>')

    # snowflakes
    for _ in range(110):
        x = rnd.uniform(0, W)
        r = rnd.uniform(1, 3.4)
        dur = rnd.uniform(6, 16) * (2.2 / (r + 0.8))
        dx = rnd.uniform(-60, 60)
        out.append(f'<circle class="f" cx="{x:.0f}" cy="0" r="{r:.1f}" fill="#fff" opacity="{rnd.uniform(.55,.95):.2f}" '
                   f'style="--dx:{dx:.0f}px;animation-duration:{dur:.1f}s;animation-delay:-{rnd.uniform(0,dur):.1f}s"/>')

    out.append('</g></svg>')
    return "\n".join(out)


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    if len(sys.argv) > 2:  # optional: generate.py out.svg 2026-11-04T22:00
        now = datetime.fromisoformat(sys.argv[2]).replace(tzinfo=timezone.utc)
    path = sys.argv[1] if len(sys.argv) > 1 else "banner.svg"
    with open(path, "w") as f:
        f.write(build(now))
    print(f"wrote {path}")
