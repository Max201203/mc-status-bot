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
import socket
import struct
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from mcstatus import JavaServer
from mcstatus.responses import JavaStatusResponse

SERVER_ADDRESS = os.environ["MC_SERVER_ADDRESS"].strip()       # z. B. deinname.aternos.me
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"].strip()
START_LINK = os.environ.get("START_LINK", "").strip() or "https://aternos.org/servers/"
MESSAGE_ID_FILE = os.environ.get("MESSAGE_ID_FILE", "status_message_id.txt")

# Woran man erkennt, dass Aternos nur die "Server ist aus"-Platzhalterseite zeigt.
ATERNOS_NOT_RUNNING = ("offline", "starting", "preparing", "loading",
                       "stopping", "saving", "queue", "waiting",
                       "error", "not found")


def _varint(value):
    out = b""
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out += bytes([byte | 0x80])
        else:
            return out + bytes([byte])


def _packet(packet_id, data=b""):
    body = _varint(packet_id) + data
    return _varint(len(body)) + body


def _recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Server hat die Verbindung geschlossen")
        data += chunk
    return data


def _read_varint(sock):
    value = 0
    for i in range(5):
        byte = _recv_exact(sock, 1)[0]
        value |= (byte & 0x7F) << (7 * i)
        if not byte & 0x80:
            return value
    raise ValueError("Ungültige Antwort vom Server")


def ping_status(address, timeout=8):
    """Server List Ping, genau wie die Serverliste im Spiel.

    Handshake und Status-Anfrage werden in EINEM Stück gesendet. Der
    Aternos-Proxy antwortet sonst nicht: mcstatus' eigenes .status() schickt
    die Pakete in Einzelteilen und läuft bei Aternos deshalb in einen Timeout.
    """
    target = JavaServer.lookup(address, timeout=timeout).address  # SRV-Eintrag / Port auflösen
    host = target.host.encode()
    handshake = _varint(47) + _varint(len(host)) + host + struct.pack(">H", target.port) + _varint(1)
    with socket.create_connection((target.host, target.port), timeout=timeout) as sock:
        sock.sendall(_packet(0, handshake) + _packet(0))
        _read_varint(sock)  # Paketlänge
        if _read_varint(sock) != 0:
            raise ValueError("Unerwartete Antwort vom Server")
        raw = _recv_exact(sock, _read_varint(sock))
    return JavaStatusResponse.build(json.loads(raw))


def check_server():
    """Gibt (status, details) zurück. status ist 'online', 'starting' oder 'offline'."""
    status, error = None, None
    for _ in range(2):  # zweiter Versuch bei kurzen Netzwerkproblemen
        try:
            status = ping_status(SERVER_ADDRESS)
            break
        except Exception as exc:
            error = exc
    if status is None:  # nicht erreichbar = aus
        print(f"Server nicht erreichbar: {type(error).__name__}: {error}")
        return "offline", {"error": str(error)}

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
            "Klick auf den Button unten und dann auf „Starten“.\n"
            f"Nach ca. 1 Minute kannst du joinen: `{SERVER_ADDRESS}`"
        ),
        "color": 0xFF4040,
        "footer": {"text": "zuletzt geprüft"},
        "timestamp": now,
    }


def build_components(state):
    """Button „Server starten“ unter der Nachricht, nur wenn der Server aus ist."""
    if state != "offline":
        return []  # leere Liste entfernt einen vorhandenen Button wieder
    return [{
        "type": 1,  # Zeile mit Buttons
        "components": [{
            "type": 2,   # Button
            "style": 5,  # Link-Button (öffnet nur die Webseite)
            "label": "Server starten",
            "emoji": {"name": "▶️"},
            "url": START_LINK,
        }],
    }]


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
    payload = {
        "content": "",
        "embeds": [build_embed(state, details)],
        "components": build_components(state),
    }
    print(f"Status: {state} {details}")

    message_id = ""
    if os.path.exists(MESSAGE_ID_FILE):
        message_id = open(MESSAGE_ID_FILE).read().strip()

    # with_components=true: sonst ignoriert Discord Buttons bei normalen Webhooks
    if message_id:
        try:
            discord("PATCH", f"{WEBHOOK_URL}/messages/{message_id}?with_components=true", payload)
            print("Nachricht aktualisiert.")
            return
        except urllib.error.HTTPError as err:
            if err.code != 404:
                raise
            print("Alte Nachricht nicht gefunden, schicke eine neue.")

    message = discord("POST", f"{WEBHOOK_URL}?wait=true&with_components=true", payload)
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(message["id"])
    print(f"Neue Statusnachricht erstellt: {message['id']}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:  # Discords Begründung mit ausgeben (enthält keine Webhook-URL)
        print(f"Fehler von Discord: {exc.code} {exc.read().decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        sys.exit(1)
