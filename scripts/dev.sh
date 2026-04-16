#!/usr/bin/env bash
set -euo pipefail

CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[dev]${NC} $1"; }

# Ensure Docker services are running
docker compose up -d postgres redis

log "Starting API server..."
cd api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
deactivate
cd ..

log "Starting Web dev server..."
cd web
npx vite --host &
WEB_PID=$!
cd ..

trap "kill $API_PID $WEB_PID 2>/dev/null; exit" SIGINT SIGTERM

log "Sentinel Vault running:"
log "  Web → http://localhost:5173"
log "  API → http://localhost:8000"
log "  Docs → http://localhost:8000/docs"
echo ""
log "Press Ctrl+C to stop."

wait