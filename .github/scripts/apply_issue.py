#!/usr/bin/env python3
"""Apply a banner settings issue to config.json.

Only the repository owner may change settings. The issue body carries a
```json block written by the playground. Everything is validated against a
whitelist before it is stored, so nothing from the issue is ever executed.
"""
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

WEATHER = {"klar", "wolkig", "regen", "gewitter", "nebel", "schnee"}
SEASONS = {"spring", "summer", "autumn", "winter", "december"}


def out(key, value):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"{key}<<EOF\n{value}\nEOF\n")


def main():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    issue = event["issue"]
    owner = os.environ["GITHUB_REPOSITORY_OWNER"]
    if issue["user"]["login"].lower() != owner.lower():
        out("result", "rejected")
        out("message", f"Nur @{owner} kann diesen Banner ändern. Hol dir deinen eigenen Banner und stell ihn dort ein 🌲")
        return

    m = re.search(r"```json\s*(\{.*?\})\s*```", issue.get("body") or "", re.S)
    if not m:
        out("result", "invalid")
        out("message", "Keine Einstellungen gefunden. Bitte über die Spielwiese speichern.")
        return
    req = json.loads(m.group(1))

    cfg = json.load(open("config.json")) if os.path.exists("config.json") else {}

    if isinstance(req.get("name"), str):
        cfg["name"] = re.sub(r"[^A-Za-z0-9 _.\-]", "", req["name"])[:24]
    if isinstance(req.get("city"), str):
        cfg["city"] = req["city"][:60]
    for k, lo, hi in (("lat", -90, 90), ("lon", -180, 180)):
        if isinstance(req.get(k), (int, float)) and lo <= req[k] <= hi:
            cfg[k] = round(float(req[k]), 4)
    if isinstance(req.get("tz"), str):
        try:
            ZoneInfo(req["tz"])
            cfg["tz"] = req["tz"]
        except Exception:
            pass

    ov = req.get("override")
    if ov is None:
        cfg["override"] = None
        summary = "Banner läuft wieder automatisch."
    else:
        clean = {
            "weather": ov.get("weather") if ov.get("weather") in WEATHER else None,
            "season": ov.get("season") if ov.get("season") in SEASONS else None,
            "hour": float(ov["hour"]) % 24 if isinstance(ov.get("hour"), (int, float)) else None,
            "until": None,
        }
        if isinstance(ov.get("until"), str):
            datetime.fromisoformat(ov["until"].replace("Z", "+00:00"))  # raises if malformed
            clean["until"] = ov["until"]
        if not any(clean[k] is not None for k in ("weather", "season", "hour")):
            clean = None
        cfg["override"] = clean
        parts = [f"{k}: {clean[k]}" for k in ("weather", "season", "hour") if clean and clean[k] is not None]
        summary = "Gespeichert: " + (", ".join(parts) or "auto") + (f" (bis {clean['until'].replace('T', ' ')[:16]} UTC)" if clean and clean["until"] else " (bis du zurücksetzt)")

    json.dump(cfg, open("config.json", "w"), indent=2, ensure_ascii=False)
    open("config.json", "a").write("\n")
    out("result", "ok")
    out("message", summary + "\n\nDein Profil-Banner ist in etwa einer Minute aktualisiert.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never leave the issue hanging
        out("result", "invalid")
        out("message", f"Konnte die Einstellungen nicht lesen: {e}")
        sys.exit(0)
