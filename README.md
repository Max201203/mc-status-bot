# Minecraft-Status für Discord

Zeigt in einem Discord-Kanal eine Nachricht, die sich alle ~2 Minuten selbst aktualisiert:

- 🟢 **Online**: Spielerzahl und Namen
- 🟡 **Startet gerade**
- 🔴 **Aus**: mit Link zum Starten auf Aternos

Läuft kostenlos über GitHub Actions. Du brauchst keinen eigenen PC und keinen Server dafür.
Der Bot fragt nur den normalen Minecraft-Status ab (wie die Serverliste im Spiel) und loggt sich nicht bei Aternos ein.

---

## 1. Discord-Kanal und Webhook

1. In deinem Discord-Server einen Kanal anlegen, z. B. `#server-status`.
2. Tipp: In den Kanal-Berechtigungen für `@everyone` „Nachrichten senden“ ausschalten, damit dort nur der Status steht.
3. Kanal-Einstellungen (Zahnrad) → **Integrationen** → **Webhooks** → **Neuer Webhook**.
4. Name z. B. „Server-Status“, optional ein Bild hochladen.
5. **Webhook-URL kopieren**. Diese URL ist geheim: Wer sie hat, kann in den Kanal schreiben. Nirgends öffentlich posten.

## 2. GitHub-Repository anlegen

1. Kostenlosen Account auf **github.com** erstellen.
2. Oben rechts **+** → **New repository**.
3. Name z. B. `mc-status-bot`, **Public** auswählen (nur dann sind die Läufe unbegrenzt kostenlos; deine geheimen Daten liegen trotzdem sicher in den „Secrets“, nicht im Code).
4. **Create repository**.
5. **Add file** → **Upload files** → `status.py` und `README.md` hochladen → **Commit changes**.
6. **Add file** → **Create new file**. Als Dateinamen genau eingeben:
   `.github/workflows/status.yml`
   Dann den Inhalt der Datei `status.yml` hineinkopieren → **Commit changes**.

## 3. Geheime Einstellungen eintragen

Im Repository: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

| Name | Inhalt |
|---|---|
| `MC_SERVER_ADDRESS` | eure Serveradresse, z. B. `deinname.aternos.me` |
| `DISCORD_WEBHOOK_URL` | die kopierte Webhook-URL |
| `START_LINK` | *(optional)* Link zum Starten, Standard: `https://aternos.org/servers/` |

Außerdem: **Settings** → **Actions** → **General** → ganz unten bei „Workflow permissions“ **Read and write permissions** auswählen → **Save**.

## 4. Testen

1. Oben auf **Actions** klicken (falls gefragt: Workflows aktivieren).
2. Links **Minecraft-Status** → rechts **Run workflow**.
3. Nach ca. 30 Sekunden erscheint die Statusnachricht im Discord-Kanal.

Ab dann aktualisiert sie sich automatisch. Löscht jemand die Nachricht, wird beim nächsten Lauf einfach eine neue erstellt.

---

## Gut zu wissen

- Der Workflow startet alle 5 Minuten (kürzer erlaubt GitHub nicht) und prüft pro Lauf 3-mal im Abstand von ~2 Minuten. GitHub startet geplante Läufe aber manchmal ein paar Minuten zu spät, dann kann der Status auch mal länger hinterherhinken.
- Deine Freunde brauchen für den Start-Link einen Aternos-Account mit **Zugriff** auf deinen Server (Aternos → „Zugriff“).
- Zieht ihr später auf einen anderen Server um (z. B. Oracle), einfach `MC_SERVER_ADDRESS` ändern und `START_LINK` auf etwas Passendes setzen.
