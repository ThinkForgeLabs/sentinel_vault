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
- Motion detection
- Event logging with severity levels
- Event statistics dashboard
- Filterable event history and review workflow

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
export $(grep -v '^#' .env | xargs)
docker compose -f docker-compose.prod.yml up -d --build
```

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
export POSTGRES_PASSWORD=... SECRET_KEY=...
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

On every deploy, run pending Alembic migrations against the running Postgres container:

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

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
| `/users` | User and role management |
| `/settings` | System-wide configuration |

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
│       │   ├── events/
│       │   ├── playback/
│       │   ├── recordings/
│       │   ├── settings/
│       │   └── users/
│       ├── services/
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
