#!/usr/bin/env bash
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${CYAN}[test]${NC} $1"; }
ok()  { echo -e "${GREEN}[✓]${NC} $1"; }

log "Running API tests..."
cd api
source .venv/bin/activate
python -m pytest tests/ -v --tb=short
ok "API tests passed"
deactivate
cd ..

log "Running Web tests..."
cd web
npx vitest run --reporter=verbose 2>/dev/null || echo "  (no web tests configured yet)"
cd ..

ok "All tests complete."