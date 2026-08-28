<div align="center">

# 🛡️ Sentinel Vault

**Self-hosted surveillance platform for reliable, local-first camera monitoring.**

Built with FastAPI · React · PostgreSQL · Redis · FFmpeg

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

[Overview](#-overview) •
[Features](#-features) •
[Architecture](#-architecture) •
[Quick Start](#-quick-start) •
[Local Development](#-local-development) •
[Roadmap](#-roadmap) •
[License](#-license)

</div>

---

## 📋 Overview

**Sentinel Vault** is a local-first, self-hosted video surveillance system for **USB** and **RTSP/IP** cameras.

It is built to provide the core features you need:

- continuous recording
- live monitoring
- motion-based events
- timeline playback
- user and role management
- storage retention
- self-hosted deployment

**No cloud required. No subscriptions. Your cameras, your data, your server.**

---

## ✨ Features

### 📹 Camera & Recording
- Multi-camera management for **USB** and **RTSP/IP** sources
- Continuous recording with **automatic start on boot**
- Configurable recording segment rotation
- Automatic retention policy and storage management

### 📡 Live Monitoring
- Real-time **WebSocket** video streaming
- Responsive live camera viewing
- Multi-camera support from a single dashboard

### 🎞️ Playback & Timeline
- Playback by **camera** and **date**
- Segment navigation for recorded footage
- Timeline-based browsing
- Real-time playback review
- On-the-fly **H.264 transcoding** with caching for browser playback

### 🚨 Events & Detection
- Motion detection (frame-difference based, per-camera tunable)
- **YOLO object detection** as a per-camera alternative backend to motion detection
- Bundled stock YOLO model plus support for uploading your own custom-trained models
- Configurable detection confidence threshold and class filtering per camera
- Event logging with severity levels
- Event statistics dashboard
- Filterable event history and review workflow

### 📡 Alerting — MQTT & Cursor-on-Target (CoT)
- Optional MQTT publishing of detection alerts (JSON payload) for integration with home-automation or SOC tooling
- Optional Cursor-on-Target (CoT) event publishing for TAK Server / FreeTAKServer / ATAK integration
- Per-camera static latitude/longitude for CoT plotting (a surveyed camera position, **not** computed target geolocation — see note below)
- Per-camera alert cooldown to prevent alert flooding during sustained detections

### 🔐 Authentication & Access Control
- JWT authentication
- Role-based access control
- User management with **Owner**, **Admin**, and **Viewer** roles

### 🛠️ Platform & Operations
- Dark-themed responsive UI
- PostgreSQL with async SQLAlchemy
- Redis caching layer
- Alembic database migrations
- Docker Compose orchestration
- Structured request logging with correlation IDs

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│                 Vite + TypeScript + Tailwind                │
│                                                              │
│    Dashboard · Cameras · Events · Playback · Settings       │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST API + WebSocket
┌───────────────────────────┼──────────────────────────────────┐
│                     FastAPI Backend                          │
│                                                              │
│  Auth · Cameras · Recordings · Playback · Events · Users    │
│  Settings · FFmpeg integration · Background processing       │
└───────────────┬───────────────────────────────┬──────────────┘
                │                               │
        ┌───────▼────────┐              ┌───────▼───────┐
        │   PostgreSQL   │              │     Redis     │
        │   App data     │              │ Cache / fast  │
        │   metadata     │              │ access layer  │
        └────────────────┘              └───────────────┘
                         │
                  ┌──────▼──────┐
                  │   Storage   │
                  │ recordings  │
                  │ segments    │
                  └─────────────┘
```

---

## 🧰 Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI | Web framework and API |
| SQLAlchemy (async) | ORM |
| PostgreSQL | Primary database |
| Redis | Caching layer |
| Alembic | Database migrations |
| FFmpeg | Camera ingest and transcoding |
| Pydantic | Validation and configuration |
| Uvicorn | ASGI server |

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Dev server and build tool |
| Tailwind CSS | Styling |
| Zustand | State management |
| React Router | Client-side routing |

### Infrastructure

| Technology | Purpose |
|---|---|
| Docker Compose | Local orchestration |
| PostgreSQL | Persistent storage |
| Redis | Fast caching and coordination |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker | 24+ |
| Docker Compose | v2+ |
| FFmpeg | Installed on host |
| Camera Source | USB webcam or RTSP stream |

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root.

### Example for local backend development

```env
SECRET_KEY=change-this-to-a-secure-random-value
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@localhost:5433/sentinel_vault
REDIS_URL=redis://localhost:6379/0
STORAGE_ROOT=./data/recordings
CORS_ORIGINS=["http://localhost:5173"]
SEGMENT_DURATION_MINUTES=15
```

### Example for Dockerized backend

```env
SECRET_KEY=change-this-to-a-secure-random-value
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel_vault
REDIS_URL=redis://redis:6379/0
STORAGE_ROOT=/data/recordings
CORS_ORIGINS=["http://localhost:5173"]
SEGMENT_DURATION_MINUTES=15
```

> **Note:** Use `localhost` when the backend runs on your machine, and use Docker service names like `postgres` and `redis` when the backend runs inside Docker.

### Optional — YOLO detection, model storage, MQTT & CoT

All of these are optional and default to "off" — the platform runs exactly as before if you don't set them. Add any of the following to your `.env` to enable them:

```env
# Directory where uploaded/stock detection models are stored on disk
MODELS_DIR=./data/models

# MQTT alert + CoT publishing (disabled by default)
MQTT_ENABLED=false
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TLS_ENABLED=false
MQTT_TLS_INSECURE=false
MQTT_TOPIC_ALERTS=sentinelvault/alerts
MQTT_TOPIC_COT=cot

# Cursor-on-Target (CoT) event settings, used when a camera has
# cot_publish_enabled=true and a latitude/longitude set
COT_TYPE=a-u-G
COT_STALE_SECONDS=60.0
```

- `MQTT_ENABLED=false` (the default) makes the MQTT client fully inert — no connection is attempted and publish calls are silent no-ops.
- Detection backend, model selection, confidence threshold, class filtering, alert cooldown, and MQTT/CoT publishing are all configured **per camera** via `PUT /api/v1/detection/{camera_id}/detection-settings`, not globally.

---

## 💻 Local Development

This is the easiest setup if you are actively building features.

### 1. Start PostgreSQL and Redis

```bash
docker compose up -d postgres redis
```

If your compose file uses different service names, replace them accordingly.

---

### 2. Start an RTSP stream for a USB webcam (Windows example)

If you are testing with a USB webcam and want to expose it as an RTSP stream, run:

```bash
ffmpeg -f dshow -rtbufsize 100M -i video="USB2.0 FHD UVC WebCam" -vf scale=640:480 -r 15 -c:v libx264 -preset ultrafast -tune zerolatency -b:v 1M -f rtsp rtsp://localhost:8554/webcam
```

> Replace `USB2.0 FHD UVC WebCam` with your actual device name.
>
> If you already have an RTSP/IP camera, you can skip this step and use the camera’s RTSP URL directly.
>
> Make sure an RTSP server is available on `localhost:8554` if you are publishing to that address.

---

### 3. Start the backend server

From the `api` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

---

### 4. Start the frontend server

From the `web` directory:

```bash
npm install
npm run dev
```

---

### 5. Open the app

Open your browser and go to:

```text
http://localhost:5173
```

---

## 🐳 Docker Development

If you want to run more of the stack with Docker:

```bash
docker compose up -d --build
```

Useful commands:

```bash
docker compose up -d
docker compose down
docker compose ps
docker compose logs -f
docker compose logs -f api
docker compose restart api
docker compose down -v
```

---

## 🚢 Production Deployment

`docker-compose.prod.yml` runs the full stack as four containers: Postgres, Redis, the API, and an Nginx-fronted build of the web app that reverse-proxies `/api` to the API. No database/cache ports are published to the host, and the API waits for Postgres and Redis to report healthy before starting.

**Option A — build from source on the deploy machine:**

```bash
git clone <repo-url> && cd sentinel_vault
cp .env.example .env   # fill in POSTGRES_PASSWORD, SECRET_KEY, CORS_ORIGINS
docker compose -f docker-compose.prod.yml up -d --build
```

Compose automatically loads variables from a `.env` file in the same
directory as the compose file -- no manual `export` needed. Don't use
`export $(grep -v '^#' .env | xargs)` to load it into your shell: word
splitting strips the quotes from values like `CORS_ORIGINS`, and a
shell-exported variable then silently overrides the correct `.env` value
(shell env takes precedence over `.env` in Compose's resolution order).

**Option B — pull prebuilt images (no build step, no source checkout):**

Every push to `main` that passes CI publishes tagged images to GitHub Container Registry (`ghcr.io/thinkforgelabs/sentinel_vault-api` and `-web`, tagged `latest` and by commit SHA). To deploy from those instead of building locally, swap the `build:` blocks in `docker-compose.prod.yml` for `image:` references, e.g.:

```yaml
api:
  image: ghcr.io/thinkforgelabs/sentinel_vault-api:latest
web:
  image: ghcr.io/thinkforgelabs/sentinel_vault-web:latest
```

then run:

```bash
# still via a .env file, not manual export -- see the note above
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

On every deploy, run pending Alembic migrations against the running Postgres container:

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

**Create the first admin account.** There's no self-service registration --
every user-creation endpoint requires an existing owner login, so a fresh
database has zero accounts. Bootstrap the first one with:

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.db.create_admin
# prompts for a username (default "admin") and a password, hidden as you type
```

This creates a single `owner`-role user and nothing else. Don't use
`app/db/seed.py` for this -- that script is dev/demo data only: it hardcodes
the password `sentinel` and adds 3 fake cameras with placeholder RTSP URLs,
which you don't want in a real deployment.

**USB camera scanning.** "Scan for Cameras" (USB tab) needs the `api`
container to see the host's `/dev/videoN` device nodes -- containers get no
hardware access by default. Run `ls /dev/video*` on the host, then uncomment
and fill in the `devices:` block for the `api` service in
`docker-compose.prod.yml` with the actual paths, e.g.:

```yaml
  api:
    devices:
      - /dev/video0:/dev/video0
```

If scanning still fails with a permissions error after that, add the host's
`video` group to the container with `group_add: ["video"]` under the same
service. IP/RTSP cameras (the "IP / RTSP" tab) don't need any of this --
they're reached over the network, not through host hardware.

**Note:** the current setup terminates TLS nowhere — `web` serves plain HTTP on port 80. Put it behind a TLS-terminating reverse proxy (e.g. Caddy, or Nginx + certbot) if it's reachable from the public internet.

---

## 🔌 Core API Areas

Sentinel Vault is organized around these main backend modules:

| Module | Purpose |
|---|---|
| `/auth` | Login, token handling, current user |
| `/cameras` | Camera management and stream access |
| `/recordings` | Recording lifecycle management |
| `/playback` | Playback availability and video delivery |
| `/events` | Event listing, filtering, and statistics |
| `/detection` | Per-camera detection settings (motion/YOLO), detection-engine status |
| `/ml-models` | Upload, list, set-default, and delete detection models (stock + custom) |
| `/users` | User and role management |
| `/settings` | System-wide configuration |

---

## 🎯 Detection Backends & Model Management

Each camera independently picks its detection backend via `detect_backend`: `motion` (the original frame-difference detector, unchanged) or `yolo` (object detection). Switching a camera's backend, model, confidence threshold, or class filter is done through `PUT /api/v1/detection/{camera_id}/detection-settings` and takes effect immediately without a restart.

**Stock + custom models, side by side.** On first boot the backend registers a bundled stock YOLO model (`yolov8n.pt`, COCO classes) as the default. You can additionally upload your own custom-trained `.pt`/`.onnx` model through `POST /api/v1/ml-models`, and set either the stock model or any custom model as a camera's active model — both are always available side by side, and the stock model cannot be deleted.

**Two important behavioral notes carried over from this integration:**

1. **Camera `latitude`/`longitude` are a static, surveyed camera position** used only to plot the camera itself on a CoT/TAK map when it publishes a detection event. They are **not** computed target geolocation — there is no range/bearing/heading-based math to estimate where a detected object actually is; only the camera's own fixed position is reported.
2. **Recording-enabled cameras running the YOLO backend will log two Event rows per detection burst**: the original motion-detector `event_type="motion"` clip event (unchanged, still has a video clip) and a separate `event_type="detection"` alert event created for the YOLO trigger (thumbnail only, no clip — by design, so the existing recording pipeline stays untouched). This is expected and both rows show up in Event history.
3. **Known minor gap:** if you switch a camera's `detect_backend` back to `motion` after having customized its motion-detector thresholds (via the separate motion-settings endpoint), the motion detector is rebuilt with default sensitivity values rather than your previously saved custom thresholds. Re-apply your custom motion settings after switching back if needed.

---

## 📁 Project Structure

```text
Sentinel_vault/
├── docker-compose.yml
├── .env
├── data/
├── api/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── core/
│       ├── db/
│       ├── dependencies/
│       ├── middleware/
│       ├── modules/
│       │   ├── auth/
│       │   ├── cameras/
│       │   ├── detection/
│       │   ├── events/
│       │   ├── ml_models/
│       │   ├── playback/
│       │   ├── recordings/
│       │   ├── settings/
│       │   └── users/
│       ├── services/
│       │   ├── cot_builder.py
│       │   ├── mqtt_service.py
│       │   └── storage.py
│       ├── tasks/
│       └── utils/
├── web/
│   └── src/
│       ├── api/
│       ├── app/
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       ├── pages/
│       ├── store/
│       └── types/
└── README.md
```

---

## 🧪 Testing

### Backend

```bash
cd api
pytest
```

If you use linting/formatting tools:

```bash
ruff check .
ruff format .
```

---

## 🗺️ Roadmap

### ✅ Completed
- Multi-camera management (USB + RTSP)
- Continuous recording with auto-start on boot
- Configurable segment rotation
- Live WebSocket video streaming
- JWT authentication with role-based access
- User management (Owner, Admin, Viewer)
- Event logging with severity levels
- Event statistics dashboard
- Playback with date picker and segment navigation
- On-the-fly H.264 transcoding with caching
- Dark-themed responsive UI
- PostgreSQL with async SQLAlchemy
- Redis caching layer
- Alembic database migrations
- Docker Compose orchestration
- Structured request logging with correlation IDs
- Automatic retention policy and storage management
- Motion detection and real-time playback
- Timeline-based navigation
- YOLO object detection as a per-camera alternative to motion detection
- Stock + user-uploaded custom detection model support, side by side
- MQTT and Cursor-on-Target (CoT) alert publishing for TAK/FreeTAKServer integration

### 🔜 Coming Soon
- Background transcoding pipeline
- Push notifications (browser, email, Discord)
- Visual timeline with event markers
- Camera offline detection and alerts
- Video clip export and download
- Multi-camera synchronized grid playback
- Production Docker Compose with Nginx

### 🔮 Future
- ONVIF camera auto-discovery
- Mobile app (React Native)
- Multi-site support with remote access
- Prometheus metrics and Grafana dashboards

---

## 🤝 Contributing

Contributions, suggestions, and feedback are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a pull request

Example:

```bash
git checkout -b feature/amazing-feature
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

---

## 📄 License

This project is licensed under the **MIT License**.

---

<div align="center">

**Sentinel Vault**  
Your cameras. Your data. Your server.

</div>
