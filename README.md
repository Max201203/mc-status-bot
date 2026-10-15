# Minecraft-Status für Discord

Zeigt in einem Discord-Kanal eine Nachricht, die sich alle paar Minuten selbst aktualisiert:

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

## 5. Pünktlicher Status mit cron-job.org

GitHub startet geplante Läufe unzuverlässig. Deshalb stößt der kostenlose Dienst **cron-job.org** den Workflow regelmäßig an (wie ein Klick auf „Run workflow“).

1. **GitHub-Schlüssel erstellen:** Profilbild → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
   - **Repository access:** *Only select repositories* → `mc-status-bot`
   - **Repository permissions** → **Actions:** *Read and write*
   - Schlüssel kopieren. Er ist geheim und gehört nur in cron-job.org, nie ins Repository.
2. **Cronjob auf cron-job.org anlegen:**
   - **URL:** `https://api.github.com/repos/<dein-name>/mc-status-bot/actions/workflows/status.yml/dispatches`
   - **Terminplan:** z. B. alle 2 Minuten
   - Reiter **Erweitert** → **Header:**
     - `Authorization`: `Bearer <dein Schlüssel>`
     - `Accept`: `application/vnd.github+json`
     - `X-GitHub-Api-Version`: `2022-11-28`
     - `Content-Type`: `application/json`
   - **Anfrage-Methode:** `POST`
   - **Anfrage-Body:** `{"ref":"main"}`
3. **Testlauf** muss **204** liefern, dann **Erstellen**.

Der Schlüssel läuft irgendwann ab (Datum steht bei GitHub). Dann einen neuen erstellen und im Cronjob austauschen.

---

## Gut zu wissen

- GitHubs eigener Zeitplan (alle 15 Minuten) ist nur eine Reserve: GitHub startet geplante Läufe oft verspätet oder gar nicht. Für einen pünktlichen Status siehe Abschnitt 5.
- Deine Freunde brauchen für den Start-Link einen Aternos-Account mit **Zugriff** auf deinen Server (Aternos → „Zugriff“).
- Zieht ihr später auf einen anderen Server um (z. B. Oracle), einfach `MC_SERVER_ADDRESS` ändern und `START_LINK` auf etwas Passendes setzen.
