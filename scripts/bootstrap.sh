#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[bootstrap]${NC} $1"; }
ok()  { echo -e "${GREEN}[✓]${NC} $1"; }

log "Starting Sentinel Vault bootstrap..."

# ── .env ──
if [ ! -f .env ]; then
  cp .env.example .env
  SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/change-me-to-a-random-64-char-string/$SECRET/" .env
  else
    sed -i "s/change-me-to-a-random-64-char-string/$SECRET/" .env
  fi
  ok ".env created with random secret"
else
  ok ".env already exists"
fi

# ── Docker services ──
log "Starting PostgreSQL and Redis..."
docker compose up -d postgres redis
ok "Docker services running"

# ── API deps ──
log "Setting up API..."
cd api
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -e ".[dev]"
ok "API dependencies installed"

# ── Migrations ──
log "Running database migrations..."
sleep 3  # wait for postgres
alembic upgrade head
ok "Migrations applied"

# ── Seed ──
log "Seeding demo data..."
python -m app.db.seed
ok "Demo data seeded"

deactivate
cd ..

# ── Web deps ──
log "Setting up Web..."
cd web
if [ ! -f .env ]; then
  cp .env.example .env
fi
npm install --silent
ok "Web dependencies installed"
cd ..

echo ""
ok "Bootstrap complete! Run 'make dev' to start."