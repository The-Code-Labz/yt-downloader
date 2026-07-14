# NeuroArchive

A modern, self-hosted YouTube archive / downloader web app for content **you own or are authorized to archive**. Paste a URL, choose audio or video and quality, then stream, re-download, or delete from a Netflix/Jellyfin-inspired library.

> ⚠️ **Legal notice**
> NeuroArchive is provided for personal archival of content you own the rights to (your own uploads, Creative Commons material, or content you have explicit permission to archive). Downloading copyrighted material you don't own may violate YouTube's Terms of Service and copyright law. You are solely responsible for how you use this software.

---

## Stack

| Layer       | Tech                                                |
| ----------- | --------------------------------------------------- |
| Frontend    | React 18 + Vite + Tailwind + shadcn/ui              |
| API         | Python 3.12 + FastAPI + Uvicorn                     |
| Worker      | Python + yt-dlp + ffmpeg + RQ (Redis queue)         |
| Queue       | Redis 7                                             |
| Database    | Supabase (Postgres + Auth + RLS)                    |
| Storage     | Cloudflare R2 (S3-compatible, boto3)                |
| Realtime    | FastAPI WebSocket (`/ws/jobs/{id}`)                 |
| Deployment  | Docker + docker-compose, Traefik-compatible labels  |

## Architecture

```
                       ┌────────────────┐
   Browser  ──HTTPS──▶ │   Frontend     │ (Vite/React, Nginx in prod)
                       └───────┬────────┘
                               │  REST + WS
                       ┌───────▼────────┐
                       │  FastAPI API   │── auth via Supabase JWT
                       └───┬────────┬───┘
                  enqueue  │        │ read/write
                           ▼        ▼
                       ┌────────┐  ┌──────────┐
                       │ Redis  │  │ Supabase │
                       └───┬────┘  └──────────┘
                           │ dequeues
                       ┌───▼────────────┐
                       │   Worker(s)    │ yt-dlp + ffmpeg
                       └───┬────────────┘
                           │ S3 PUT
                           ▼
                    ┌──────────────┐
                    │ Cloudflare R2│
                    └──────────────┘
```

Frontend polls `GET /jobs` and subscribes to `WS /ws/jobs/{id}` for live progress. Worker pushes progress events into Redis pub/sub, which the API relays to the WebSocket.

## Repository layout

```
neuroarchive/
├── README.md
├── .env.example                  ← copy to .env at repo root
├── docker-compose.yml
├── infra/
│   └── traefik.example.yml       ← optional reverse-proxy config
├── supabase/
│   └── schema.sql                ← run in Supabase SQL editor
├── backend/                      ← FastAPI API service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── deps.py
│       ├── db.py
│       ├── r2.py
│       ├── queue.py
│       ├── ws.py
│       ├── routes/
│       │   ├── downloads.py
│       │   └── health.py
│       └── schemas.py
├── worker/                       ← yt-dlp + ffmpeg consumer
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── worker.py
│       ├── tasks.py
│       ├── ytdl.py
│       ├── r2.py
│       ├── db.py
│       └── progress.py
└── frontend/                     ← Vite + React + Tailwind + shadcn
    ├── Dockerfile
    ├── docker-entrypoint.d/40-env-config.sh  ← writes runtime env-config.js on container start
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    ├── .env.example
    ├── public/env-config.js      ← dev-only placeholder, overwritten in the container
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── lib/{api.ts,utils.ts,supabase.ts,runtime-env.ts}
        ├── hooks/{useJobs.ts,useJobStream.ts}
        ├── pages/{Library.tsx,NewDownload.tsx,Settings.tsx,Login.tsx}
        └── components/
            ├── Sidebar.tsx
            ├── TopBar.tsx
            ├── DownloadCard.tsx
            ├── NewDownloadForm.tsx
            ├── EmptyState.tsx
            ├── Toaster.tsx
            └── ui/                ← shadcn primitives
```

---

## Local setup (step-by-step)

### 1. Prerequisites

* Docker 24+ and docker-compose
* A Supabase project (free tier is fine)
* A Cloudflare R2 bucket + API token

### 2. Provision Supabase

1. Create a Supabase project at <https://supabase.com>.
2. Open **SQL Editor** and run the contents of `supabase/schema.sql`. This creates a dedicated **`neuroarchive`** Postgres schema, the `downloads` table, RLS policies, and Realtime publication. Using a custom schema keeps NeuroArchive cleanly namespaced so it can share a project with other apps.
3. In **Project Settings → API → Exposed schemas**, add `neuroarchive` (comma-separated alongside `public`). PostgREST will refuse to see the table until you do this.
4. In **Project Settings → API**, copy:
   * `SUPABASE_URL`
   * `SUPABASE_ANON_KEY` (frontend)
   * `SUPABASE_SERVICE_ROLE_KEY` (backend only — keep secret)
5. Set `SUPABASE_SCHEMA=neuroarchive` in your `.env` (already the default).
6. In **Authentication → Providers**, enable Email (or any OAuth provider you prefer).

### 3. Provision Cloudflare R2

1. In the Cloudflare dashboard, go to **R2 → Create bucket** and name it (e.g. `neuroarchive`).
2. Under **Manage R2 API Tokens**, create a token with Object Read & Write for that bucket.
3. Record:
   * Account ID (forms the endpoint: `https://<account_id>.r2.cloudflarestorage.com`)
   * Access Key ID
   * Secret Access Key
   * Bucket name
4. (Optional) Connect a custom domain to the bucket if you want long-lived public URLs; otherwise NeuroArchive uses signed URLs.

### 4. Configure environment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp worker/.env.example worker/.env
cp frontend/.env.example frontend/.env
```

Fill in the values you collected above. The root `.env` is consumed by docker-compose; the per-service files are for running services outside of Docker.

### 5. Run with Docker

`docker-compose.yml` pulls pre-built, multi-arch (`linux/amd64` + `linux/arm64`) images
from GHCR — published by `.github/workflows/publish.yml` on every push to `main`
and on version tags — rather than building locally. This works unmodified on
Debian/Ubuntu x86_64 hosts and on ARM hosts (e.g. Oracle Cloud Ampere A1 free tier).

```bash
docker compose pull
docker compose up -d
```

Pin a specific release instead of `latest` by setting `IMAGE_TAG=v1.2.3` in `.env`.

Services come up on:

| Service  | URL                       |
| -------- | ------------------------- |
| Frontend | http://localhost:5173     |
| API      | http://localhost:8000/docs |
| Redis    | localhost:6379            |

The worker has no exposed port — it consumes from Redis.

### 6. Sign in and use

1. Open <http://localhost:5173>, sign up with email (Supabase will send a magic link / confirmation).
2. Paste a YouTube URL you have rights to archive.
3. Pick **Audio (MP3)** or **Video (MP4)** and a quality.
4. Watch the progress bar fill, then stream or copy the R2 link.

---

## Running services without Docker (dev)

```bash
# Terminal 1 — API
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Worker (needs ffmpeg on PATH)
cd worker && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
rq worker neuroarchive --url redis://localhost:6379/0

# Terminal 3 — Frontend
cd frontend && npm install && npm run dev

# Terminal 4 — Redis
docker run --rm -p 6379:6379 redis:7-alpine
```

---

## API reference

All endpoints require a Supabase JWT in `Authorization: Bearer <token>`.

| Method | Path                  | Description                          |
| ------ | --------------------- | ------------------------------------ |
| POST   | `/download`           | Create a new download job            |
| GET    | `/jobs`               | List the current user's jobs        |
| GET    | `/job/{id}`           | Get a single job (with signed URL)   |
| DELETE | `/job/{id}`           | Delete a job and its R2 object       |
| WS     | `/ws/jobs/{id}`       | Live progress events                 |
| GET    | `/health`             | Liveness probe                       |

**POST /download** body:

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "media_type": "audio" | "video",
  "quality": "best" | "1080p" | "720p" | "audio"
}
```

---

## Bonus features included

* **Auto-delete** — set `AUTO_DELETE_DAYS` in backend env; a daily RQ-scheduler job purges old objects.
* **Signed URLs** — `GET /job/{id}` returns a 1-hour presigned R2 URL.
* **Queue & retries** — RQ retries failed jobs up to 3 times with exponential backoff.
* **WebSocket realtime** — `/ws/jobs/{id}` pushes `{ progress, status, eta }` events.
* **Transcript placeholder** — `transcript` column on `downloads` and a stub `extract_transcript()` in the worker, ready to wire up Whisper later.

---

## YouTube bot-check

If jobs fail with `ERROR: [youtube] ...: Sign in to confirm you're not a bot`, YouTube is blocking the worker's IP as anonymous/automated traffic — expected on cloud/VPS IPs, not specific to this app. Two independent fixes, best used together:

* **Cookies** — proves the request comes from a real, logged-in session.
* **Proxy** — makes the request's *IP* look residential instead of datacenter, which is the other half of what triggers the wall.

### Quick manual fix (cookies only, one-time)

1. Log into `youtube.com` in a normal browser, export cookies in **Netscape format** with an extension like *Get cookies.txt LOCALLY*.
2. Save the export as `cookies.txt` next to `docker-compose.yml` on the host.
3. In `docker-compose.yml`, switch the worker's `YTDLP_COOKIES_FILE` to the "Option B" line and uncomment the matching `./cookies.txt:/app/cookies.txt:ro` volume line (also documented in `.env.example`).
4. `docker compose up -d --force-recreate worker`.

Cookies expire — re-export and repeat if the error comes back. This is fine for occasional use; for a set-and-forget deployment use the dynamic method below instead.

### Dynamic cookies (recommended — set-and-forget)

`scripts/refresh_cookies.py` pulls a fresh `cookies.txt` **directly out of a real browser's cookie store** on whatever machine you run it on — no manual export ever again — and pushes it to the backend's `PUT /admin/cookies` endpoint, which atomically writes it to a volume (`cookies-data`) shared with the worker. The worker re-reads the cookies file on every job, so a refresh takes effect on the very next download with **no restart, no redeploy, no SSH**.

Run it on the machine (or a machine on the network) where you're actually signed into `youtube.com` day-to-day — that session already has good standing with YouTube, which a bot-fresh session created just for this wouldn't have.

```bash
pip install -r scripts/requirements.txt

# One-off test:
python scripts/refresh_cookies.py \
  --browser chrome \
  --backend-url https://api-yt-downloader.neurolearninglabs.com \
  --admin-secret "$ADMIN_SECRET"   # matches ADMIN_SECRET in the deployed .env
```

Set `ADMIN_SECRET` in the deployed stack's `.env` first (`openssl rand -hex 32`) — the endpoint 404s until it's configured, and rejects any request whose `X-Admin-Secret` header doesn't match.

Then schedule it:

* **Linux (systemd)** — copy `scripts/systemd/refresh-cookies.{service,timer}` to `~/.config/systemd/user/`, put your real values in `~/.config/yt-downloader/refresh-cookies.env` (`REFRESH_COOKIES_BROWSER`, `REFRESH_COOKIES_BACKEND_URL`, `REFRESH_COOKIES_ADMIN_SECRET`, `chmod 600` it), then `systemctl --user enable --now refresh-cookies.timer` (runs every 30 min).
* **Linux/macOS (cron)** — `*/30 * * * * REFRESH_COOKIES_BACKEND_URL=... REFRESH_COOKIES_ADMIN_SECRET=... /usr/bin/python3 /path/to/refresh_cookies.py --browser chrome >> ~/refresh-cookies.log 2>&1`
* **Windows** — Task Scheduler, trigger every 30 min, action = `python.exe C:\path\refresh_cookies.py --browser chrome --backend-url ... --admin-secret ...`.

Notes: `browser_cookie3` copies the browser's SQLite cookie DB before reading it, so it generally works fine with the browser open on Linux/macOS; Chrome on Windows can occasionally hold a lock — the script just fails that one run and succeeds on the next schedule. Missing/unset `ADMIN_SECRET` or `YTDLP_COOKIES_FILE` are both silent no-ops elsewhere in the stack (non-YouTube sources are unaffected either way).

### Bypass via a home-network proxy (IP reputation)

Cookies alone don't help if the *IP* itself is what's flagged — cloud/VPS ranges (Oracle, Hetzner, AWS, etc.) get bot-walled far more aggressively than residential IPs, independent of login state. `infra/socks5-proxy/` is a minimal authenticated SOCKS5 proxy (`serjs/go-socks5-proxy`) meant to run **on your home network** — the same one you use for cookies above — so the worker's yt-dlp egress looks like your own household traffic instead of a datacenter.

1. On a machine at home: `cd infra/socks5-proxy && cp .env.example .env` (set real `PROXY_USER`/`PROXY_PASSWORD`), `docker compose up -d`.
2. Get that machine reachable from the yt-downloader host — a mesh VPN (NetBird/Tailscale/WireGuard) is the cleanest way; a reverse SSH `-R` tunnel also works if you'd rather not stand up a mesh.
3. In the yt-downloader deployment's `.env`, set:
   ```
   YTDLP_PROXY=socks5://<PROXY_USER>:<PROXY_PASSWORD>@<home-machine-mesh-ip>:1080
   ```
4. `docker compose up -d --force-recreate worker`.

yt-dlp needs `PySocks` for `socks5://` URLs — already pinned in `worker/requirements.txt`. `http://` proxy URLs work too if you'd rather front the tunnel with something else. Leave `YTDLP_PROXY` unset for direct egress (default).

---

## Traefik

`infra/traefik.example.yml` shows the labels needed to expose the frontend on `https://archive.example.com` and the API on `https://api.archive.example.com`. Drop it into your Traefik stack or merge the labels into `docker-compose.yml`.

---

## License

MIT. Use responsibly.
