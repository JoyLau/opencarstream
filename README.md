# Tesla MJPEG Streamer

Stream any YouTube video to your Tesla browser via MJPEG.  
No `<video>` element → Tesla's driving speed-lock doesn't apply.

---

## Architecture

```
Tesla browser
    │  GET /watch?url=https://youtube.com/watch?v=xxx
    ▼
[nginx] (optional TLS + DDNS domain)
    │
    ▼
[streamer container]
  yt-dlp stdout
    │ pipe
  ffmpeg stdin → JPEG frames → multipart/x-mixed-replace
    │
    └──► Tesla sees a fast-updating <img> — not a <video>
```

---

## Quick start

### 1. Clone / copy this folder to your server

```bash
scp -r tesla-streamer/ user@yourserver:~/
ssh user@yourserver
cd tesla-streamer
```

### 2. Build and start

```bash
docker compose up -d --build
```

If Docker Hub is flaky in your region, override the Python base image source:

```bash
PYTHON_IMAGE=mirror.gcr.io/library/python:3.12-slim docker compose up -d --build
```

### 3. Test locally

```
http://localhost:8080/health
http://localhost:8080/
```

### 4. Open in Tesla browser

Navigate to your server's status page and use the **Stream** tab, or go directly to:

```
http://YOUR_SERVER_IP:8080/watch?url=https://www.youtube.com/watch?v=VIDEO_ID
```

---

## Channel feed & subscriptions

The **Channel Feed** tab lets you browse recent uploads from any YouTube channel
and click to stream them directly.

### Browsing a single channel

Enter `@channelhandle` or a full channel URL in the feed tab and click **Load Feed**.

### Syncing your YouTube subscriptions

Run `sync_subscriptions.py` once on your home machine to generate a
`subscriptions.json` file. The streamer mounts this file — no cookies or
network calls needed in the container.

**Option A — read directly from your browser (easiest, no manual export):**

```bash
# Chrome / Chromium / Brave / Edge / Firefox / Opera / Safari
uv run sync_subscriptions.py --browser chrome
uv run sync_subscriptions.py --browser firefox
```

Make sure you are logged in to YouTube in that browser before running.
yt-dlp reads the browser's cookie store directly.

**Option B — export cookies.txt manually:**

1. Install the [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   Chrome extension (or equivalent for Firefox).
2. Go to `youtube.com` while logged in → click the extension → Export.
3. Save the file as `cookies.txt` in the project folder.

```bash
uv run sync_subscriptions.py --cookies cookies.txt
```

Both options write `subscriptions.json` in the current directory.
Re-run whenever you follow or unfollow channels.

**Mount it in the container** (already configured in `docker-compose.yml`):

```yaml
volumes:
  - ./subscriptions.json:/subscriptions.json:ro
```

Then restart the container:

```bash
docker compose restart streamer
```

The **My Subscriptions** panel appears automatically in the Channel Feed tab
once the file is mounted. It shows all your followed channels sorted
alphabetically with a filter box. Clicking any channel loads its recent videos.

---

## Expose to the internet (DDNS)

### Option A — No-IP / DuckDNS / Dynu (port forwarding)

1. Sign up for a free DDNS provider (no-ip.com, duckdns.org, dynu.com)
2. Install their update client on your server or router
3. Port-forward TCP 8080 (or 443 if using nginx TLS) on your router to the server
4. Open Tesla browser to: `http://yourname.ddns.net:8080/`

### Option B — Cloudflare Tunnel (no port forwarding needed)

```bash
# Install cloudflared
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
  https://pkg.cloudflare.com/cloudflared any main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared

# Authenticate and create tunnel
cloudflared tunnel login
cloudflared tunnel create tesla-stream
cloudflared tunnel route dns tesla-stream stream.yourdomain.com

# Run (or add to systemd)
cloudflared tunnel run --url http://localhost:8080 tesla-stream
```

Tesla URL becomes: `https://stream.yourdomain.com/`

### Option C — Nginx + Let's Encrypt TLS (with DDNS domain)

1. Uncomment the `nginx` service in `docker-compose.yml`
2. Edit `nginx.conf` → set your domain in `server_name`
3. Get a free TLS cert:

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d stream.yourdomain.com
sudo cp /etc/letsencrypt/live/stream.yourdomain.com/fullchain.pem certs/cert.pem
sudo cp /etc/letsencrypt/live/stream.yourdomain.com/privkey.pem   certs/key.pem
```

4. `docker compose up -d`

---

## Environment variables

| Variable              | Default               | Description                             |
|-----------------------|-----------------------|-----------------------------------------|
| `PORT`                | 8080                  | HTTP port inside container              |
| `MJPEG_FPS`           | 24                    | Frames/sec sent to client               |
| `FFMPEG_QUALITY`      | 3                     | JPEG quality: 1=best, 31=smallest       |
| `STREAM_WIDTH`        | 1920                  | Output width (px)                       |
| `STREAM_HEIGHT`       | 1080                  | Output height (px)                      |
| `MAX_STREAMS`         | 3                     | Max parallel video streams              |
| `AUDIO_DELAY_MS`      | 0                     | ms to delay video start after audio     |
| `SUBSCRIPTIONS_FILE`  | /subscriptions.json   | Path to subscriptions JSON inside container |

Override in `docker-compose.yml` under `environment:`.

---

## API endpoints

| Endpoint                        | Description                                      |
|---------------------------------|--------------------------------------------------|
| `GET /`                         | Status dashboard with stream/feed/info tabs      |
| `GET /watch?url=…`              | Watch page (MJPEG video + audio)                 |
| `GET /feed?channel=@handle`     | JSON list of recent uploads for a channel        |
| `GET /subscriptions`            | JSON list of channels from subscriptions.json    |
| `GET /health`                   | `{"ok":true}` — for uptime monitors              |
| `GET /status`                   | JSON list of active streams                      |

---

## Tips

- **Bookmark it in Tesla**: Save `http://yourserver/` as a bookmark and use the UI
- **Lower bandwidth**: Set `MJPEG_FPS=15` and `FFMPEG_QUALITY=6` in docker-compose.yml
- **Update yt-dlp** (YouTube changes frequently):
  ```bash
  docker compose build --no-cache && docker compose up -d
  ```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Black screen in Tesla | Make sure URL ends in `/watch?url=...` not just `/` |
| `502 Pipeline error` | yt-dlp may need updating: rebuild image |
| `DeadlineExceeded` while pulling base image | Retry with a mirror: `PYTHON_IMAGE=mirror.gcr.io/library/python:3.12-slim docker compose build --no-cache` |
| Stream stutters on LAN | Lower `MJPEG_FPS` to 12–15 |
| Can't reach from internet | Check port forwarding / firewall; try `curl http://yourserver:8080/health` from outside |
| Container exits immediately | `docker compose logs streamer` to see the error |
| Subscriptions panel not visible | `subscriptions.json` not mounted — check volume in docker-compose.yml |
| `‼ yt-dlp failed` in sync script | Make sure you are logged in to YouTube in the browser you specified |
