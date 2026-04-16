for the rtsp steam :ffmpeg -f dshow -rtbufsize 100M -i video="USB2.0 FHD UVC WebCam" -vf scale=640:480 -r 15 -c:v libx264 -preset ultrafast -tune zerolatency -b:v 1M -f rtsp rtsp://localhost:8554/webcam

for the backend server : (sentinel_test) C:\Users\marve\Documents\Computer_Related\Sentinel_vault\api>uvicorn app.main:app --reload --port 8000

for the frontend server :(sentinel_test) C:\Users\marve\Documents\Computer_Related\Sentinel_vault\web>npm run dev


<div align="center">

# 🛡️ Sentinel Vault

**Self-hosted intelligent video surveillance system**

Built with FastAPI · React · PostgreSQL · Redis · FFmpeg

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Roadmap](#-roadmap)

---

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

---

## 📋 Overview

Sentinel Vault is a modern, self-hosted video surveillance platform that turns USB cameras (or RTSP/IP cameras) into a full-featured security system. Record continuously, stream live footage, detect events, and review historical playback — all from a sleek dark-themed dashboard.

No cloud. No subscriptions. **Your cameras, your data, your server.**

---

## ✨ Features

### 📹 Multi-Camera Management
- Add and configure multiple USB or RTSP/IP cameras
- Auto-start recording on server boot
- Real-time camera status monitoring
- Configurable recording segments (default 15 min)

### 🔴 Live Streaming
- Real-time WebSocket video streaming
- Low-latency JPEG frame delivery
- Multi-viewer support per camera

### ⏪ Playback & Review
- Browse recordings by camera and date
- Segment-based navigation with prev/next controls
- On-the-fly AVI/MPEG-4 → H.264 transcoding for browser playback
- Cached transcodes for instant replay

### ⚡ Event Detection & Logging
- Event logging with severity levels
- Filterable event list (by camera, type, date range)
- Event statistics dashboard with counts and trends

### 🔐 Authentication & Security
- JWT-based authentication with token refresh
- Role-based access control (Owner, Admin, Viewer)
- User management with invite system
- Secure password hashing with bcrypt

### ⚙️ System Settings
- System-wide configuration management
- Per-camera recording settings
- Storage path configuration

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│            Vite + TypeScript + Tailwind              │
│                                                      │
│   Dashboard · Cameras · Events · Playback · Settings │
└──────────────────────┬──────────────────────────────┘
                       │  REST API + WebSocket
┌──────────────────────┼──────────────────────────────┐
│            Docker Compose Stack                      │
│   ┌──────────────────┴────────────────────────┐     │
│   │          sv-api (FastAPI)                  │     │
│   │   Router Layer                             │     │
│   │   /auth  /cameras  /events  /playback      │     │
│   │   /recordings  /settings  /users           │     │
│   │   Service Layer                            │     │
│   │   Business logic · Validation · Queries    │     │
│   │   FFmpeg · Background Tasks                │     │
│   └──────┬─────────────────┬──────────────────┘     │
│   ┌──────┴──────┐   ┌─────┴─────┐                   │
│   │ sv-postgres │   │ sv-redis  │                    │
│   │ PostgreSQL  │   │  Redis 7  │                    │
│   │  :5433→5432 │   │  :6379    │                    │
│   └─────────────┘   └───────────┘                   │
└──────────────────────────────────────────────────────┘
         │
    ┌────┴────┐
    │ ./data  │  Mounted volume for recordings
    └─────────┘

🛠️ Tech Stack
Backend
Technology	Purpose
Python 3.11+	Runtime
FastAPI	Web framework & REST API
SQLAlchemy 2.0 (async)	Async ORM
PostgreSQL 16 + asyncpg	Primary database
Redis 7	Caching & session management
Alembic	Database migrations
FFmpeg	Camera capture & video transcoding
Pydantic v2	Schema validation & settings
Passlib + bcrypt	Password hashing
python-jose	JWT token handling
Uvicorn	ASGI server
httpx	Async HTTP client
Frontend
Technology	Purpose
React 18	UI framework
TypeScript	Type safety
Vite	Build tool & dev server
Tailwind CSS	Utility-first styling
Zustand	Lightweight state management
React Router v6	Client-side routing
Infrastructure
Technology	Purpose
Docker Compose	Container orchestration
PostgreSQL 16 Alpine	Database container
Redis 7 Alpine	Cache container

📁 Project Structure
text
Sentinel_vault/
├── docker-compose.yml              # Container orchestration
├── .env                            # Environment variables
├── data/                           # Mounted recording storage
├── api/                            # Backend (FastAPI)
│   ├── Dockerfile                  # API container build
│   ├── pyproject.toml              # Python project config & dependencies
│   ├── app/
│   │   ├── main.py                 # App entry point & lifespan
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings (env-based)
│   │   │   ├── exceptions.py       # Custom exception classes
│   │   │   ├── logging.py          # Structured logging setup
│   │   │   └── security.py        # JWT & password utilities
│   │   ├── db/
│   │   │   ├── base.py             # SQLAlchemy declarative base
│   │   │   ├── models.py           # Model registry
│   │   │   ├── seed.py             # Initial data seeding
│   │   │   └── session.py          # Async session factory
│   │   ├── dependencies/
│   │   │   ├── auth.py             # get_current_user dependency
│   │   │   └── common.py           # Shared DI (db session, pagination)
│   │   ├── middleware/
│   │   │   ├── error_handler.py    # Global exception handling
│   │   │   └── request_context.py  # Request ID & access logging
│   │   ├── modules/
│   │   │   ├── auth/               # Login, register, token refresh
│   │   │   ├── cameras/            # CRUD + capture manager
│   │   │   ├── events/             # Event logging & statistics
│   │   │   ├── playback/           # Video serving & transcoding
│   │   │   ├── recordings/         # Recording lifecycle & manager
│   │   │   ├── settings/           # System configuration
│   │   │   └── users/              # User management & roles
│   │   ├── services/
│   │   │   ├── audit.py            # Audit trail logging
│   │   │   ├── notifications.py    # Notification dispatch
│   │   │   ├── storage.py          # File storage abstraction
│   │   │   └── video.py            # FFmpeg video processing
│   │   ├── tasks/
│   │   │   └── sync_events.py      # Background task runners
│   │   └── utils/
│   │       ├── datetime.py         # Timezone & date helpers
│   │       ├── pagination.py       # Cursor/offset pagination
│   │       └── responses.py        # Standardized API responses
├── web/                            # Frontend (React)
│   └── src/
│       ├── api/                    # Typed API client functions
│       ├── app/                    # App.tsx, main.tsx, providers, router
│       ├── components/
│       │   ├── layout/             # AppShell, Sidebar, Topbar, PageHeader
│       │   └── ui/                 # Badge, Button, Input, Modal, Spinner
│       ├── hooks/                  # useAuth, useCurrentUser, useDebounce
│       ├── lib/                    # cn(), constants, date & format utils
│       ├── pages/
│       │   ├── Cameras/            # Camera grid & config forms
│       │   ├── Dashboard/          # Stat cards & recent events
│       │   ├── Events/             # Event browser with filters
│       │   ├── Login/              # Auth page
│       │   ├── Playback/           # Video player & timeline
│       │   └── Settings/           # System settings page
│       ├── store/                  # Zustand stores (auth, playback, ui)
│       └── types/                  # TypeScript interfaces
└── README.md

elixir

**Part 2 — paste directly after Part 1:**

```markdown
---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version |
|:------------|:--------|
| Docker | 24+ |
| Docker Compose | v2+ |
| Node.js | 18+ |
| FFmpeg | Latest (on host for camera access) |
| Camera | USB webcam or RTSP stream |

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sentinel-vault.git
cd sentinel-vault

2. Configure Environment
Create a .env file in the project root:

env
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel_vault
REDIS_URL=redis://redis:6379/0
STORAGE_PATH=/data/recordings
CORS_ORIGINS=["http://localhost:5173"]
SEGMENT_DURATION_MINUTES=15

⚠️ The hostnames postgres and redis resolve to Docker service names inside the compose network.

3. Start the Stack
bash
docker compose up -d

Container	Service	Port
sv-postgres	PostgreSQL 16	5433 → 5432
sv-redis	Redis 7	6379
sv-api	FastAPI (Uvicorn)	8000
bash
docker compose ps
docker compose logs -f api

On first startup the API will:

✅ Wait for PostgreSQL and Redis health checks to pass
✅ Run database migrations
✅ Seed default admin user
✅ Auto-detect configured cameras
✅ Begin continuous recording
4. Frontend Setup
bash
cd web
npm install
npm run dev

5. Open the App
Navigate to http://localhost:5173

Field	Value
Username	admin
Password	admin
⚠️ Change the default password immediately via Settings after first login.

🐳 Docker Services
Volumes
Volume	Mount	Purpose
pg_data	/var/lib/postgresql/data	Persistent database storage
redis_data	/data	Redis persistence
./api	/app	Live code reload (dev)
./data	/data	Recording file storage
Useful Commands
bash
docker compose up -d              # Start all services
docker compose down               # Stop all services
docker compose logs -f api        # View API logs
docker compose restart api        # Restart just the API
docker compose exec postgres psql -U sentinel -d sentinel_vault
docker compose exec redis redis-cli
docker compose up -d --build api  # Rebuild API container
docker compose down -v            # Nuke everything

🔌 API Reference
All endpoints are prefixed with /api/v1. Protected routes require Authorization: Bearer <token>.

Authentication
Method	Endpoint	Auth	Description
POST	/auth/login	❌	Login & receive JWT
POST	/auth/register	❌	Register new account
GET	/auth/me	✅	Get current user profile
Cameras
Method	Endpoint	Auth	Description
GET	/cameras	✅	List all cameras
POST	/cameras	✅	Add a new camera
GET	/cameras/{id}	✅	Get camera details
PUT	/cameras/{id}	✅	Update camera config
DELETE	/cameras/{id}	✅	Remove a camera
WS	/cameras/{id}/stream	✅	Live video WebSocket
Recordings
Method	Endpoint	Auth	Description
GET	/recordings	✅	List recording segments
POST	/recordings/start	✅	Start recording a camera
POST	/recordings/stop	✅	Stop recording a camera
Playback
Method	Endpoint	Auth	Description
GET	/playback/availability	✅	Get segments for camera + date
GET	/playback/recording/{id}/video	❌*	Stream transcoded video
*Video endpoint bypasses auth so <video> elements can fetch directly.

Events
Method	Endpoint	Auth	Description
GET	/events	✅	List events (filterable)
GET	/events/stats	✅	Aggregate event statistics
Users
Method	Endpoint	Auth	Description
GET	/users	✅	List all users
POST	/users	✅	Create user (admin only)
PUT	/users/{id}	✅	Update user
DELETE	/users/{id}	✅	Delete user (admin only)
Settings
Method	Endpoint	Auth	Description
GET	/settings	✅	Get system settings
PUT	/settings	✅	Update settings (admin only)
🧪 Testing
bash
cd api
pip install -e ".[dev]"
pytest
pytest --cov=app
ruff check .
ruff format .

The test suite uses aiosqlite as an in-memory database backend so tests run fast without requiring PostgreSQL.

🗺️ Roadmap
✅ Completed
 Multi-camera management (USB + RTSP)
 Continuous recording with auto-start on boot
 Configurable segment rotation
 Live WebSocket video streaming
 JWT authentication with role-based access
 User management (Owner, Admin, Viewer)
 Event logging with severity levels
 Event statistics dashboard
 Playback with date picker & segment navigation
 On-the-fly H.264 transcoding with caching
 Dark-themed responsive UI
 PostgreSQL with async SQLAlchemy
 Redis caching layer
 Alembic database migrations
 Docker Compose orchestration
 Structured request logging with correlation IDs

🔜 Coming Soon
 Automatic retention policy & storage management
 Background transcoding pipeline
 Motion detection
 Push notifications (browser, email, Discord)
 Visual timeline with event markers
 Camera offline detection & alerts
 Video clip export & download
 Multi-camera synchronized grid playback
 Production Docker Compose with Nginx

🔮 Future
 ONVIF camera auto-discovery
 AI object detection (person, vehicle, animal)
 Face recognition & known-person alerts
 Mobile app (React Native)
 Multi-site support with remote access
 Prometheus metrics & Grafana dashboards

🤝 Contributing
Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

<div align="center">

Sentinel Vault — Your cameras. Your data. Your server.

Built with ❤️

</div>

```