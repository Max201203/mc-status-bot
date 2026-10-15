"""
Minecraft-Status für Discord.

Pingt den Minecraft-Server (wie die Serverliste im Spiel) und aktualisiert
EINE Nachricht in einem Discord-Kanal über einen Webhook:
  🟢 Online  -> Spielerzahl und Namen
  🔴 Offline -> Link zum Starten auf Aternos

Es wird nur der normale Minecraft-Status abgefragt, kein Login bei Aternos.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from mcstatus import JavaServer

SERVER_ADDRESS = os.environ["MC_SERVER_ADDRESS"].strip()       # z. B. deinname.aternos.me
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"].strip()
START_LINK = os.environ.get("START_LINK", "").strip() or "https://aternos.org/servers/"
MESSAGE_ID_FILE = os.environ.get("MESSAGE_ID_FILE", "status_message_id.txt")

# Woran man erkennt, dass Aternos nur die "Server ist aus"-Platzhalterseite zeigt.
ATERNOS_NOT_RUNNING = ("offline", "starting", "preparing", "loading",
                       "stopping", "saving", "queue", "waiting")


def check_server():
    """Gibt (status, details) zurück. status ist 'online', 'starting' oder 'offline'."""
    try:
        status = JavaServer.lookup(SERVER_ADDRESS, timeout=8).status()
    except Exception as exc:  # nicht erreichbar = aus
        print(f"Server nicht erreichbar: {type(exc).__name__}: {exc}")
        return "offline", {"error": str(exc)}

    version = (status.version.name or "").lower()
    try:
        motd = status.motd.to_plain().lower()
    except AttributeError:
        motd = str(status.description).lower()
    print(f"Antwort vom Server -> Version: {status.version.name!r} | "
          f"MOTD: {motd!r} | Spieler: {status.players.online}/{status.players.max}")

    text = version + " " + motd
    if any(word in text for word in ("starting", "preparing", "loading", "queue", "waiting")):
        return "starting", {}
    if any(word in text for word in ATERNOS_NOT_RUNNING):
        return "offline", {}

    names = sorted(p.name for p in (status.players.sample or []))
    return "online", {
        "online": status.players.online,
        "max": status.players.max,
        "names": names,
        "version": status.version.name,
    }


def build_embed(state, details):
    now = datetime.now(timezone.utc).isoformat()
    if state == "online":
        players = f"**{details['online']} / {details['max']}** Spieler online"
        if details["names"]:
            players += "\n" + ", ".join(details["names"])
        return {
            "title": "🟢 Server ist ONLINE",
            "description": f"{players}\n\nAdresse: `{SERVER_ADDRESS}`",
            "color": 0x30C030,
            "footer": {"text": f"Version {details['version']} · zuletzt geprüft"},
            "timestamp": now,
        }
    if state == "starting":
        return {
            "title": "🟡 Server startet gerade …",
            "description": f"Gleich geht's los. Adresse: `{SERVER_ADDRESS}`",
            "color": 0xE0B000,
            "footer": {"text": "zuletzt geprüft"},
            "timestamp": now,
        }
    return {
        "title": "🔴 Server ist AUS",
        "description": (
            f"**[➜ Hier klicken und auf „Starten“ drücken]({START_LINK})**\n"
            f"Nach ca. 1 Minute kannst du joinen: `{SERVER_ADDRESS}`"
        ),
        "color": 0xFF4040,
        "footer": {"text": "zuletzt geprüft"},
        "timestamp": now,
    }


def discord(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", "User-Agent": "mc-status-bot"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


def main():
    state, details = check_server()
    payload = {"content": "", "embeds": [build_embed(state, details)]}
    print(f"Status: {state} {details}")

    message_id = ""
    if os.path.exists(MESSAGE_ID_FILE):
        message_id = open(MESSAGE_ID_FILE).read().strip()

    if message_id:
        try:
            discord("PATCH", f"{WEBHOOK_URL}/messages/{message_id}", payload)
            print("Nachricht aktualisiert.")
            return
        except urllib.error.HTTPError as err:
            if err.code != 404:
                raise
            print("Alte Nachricht nicht gefunden, schicke eine neue.")

    message = discord("POST", f"{WEBHOOK_URL}?wait=true", payload)
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(message["id"])
    print(f"Neue Statusnachricht erstellt: {message['id']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        sys.exit(1)
