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

## Traefik

`infra/traefik.example.yml` shows the labels needed to expose the frontend on `https://archive.example.com` and the API on `https://api.archive.example.com`. Drop it into your Traefik stack or merge the labels into `docker-compose.yml`.

---

## License

MIT. Use responsibly.
