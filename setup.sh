#!/usr/bin/env bash
set -euo pipefail

PROJECT="taskflow"

mkdir -p "$PROJECT"/{scripts,backend/{app/{models,schemas,routers,services,middleware},alembic/versions,tests},frontend/{src/{api,stores,hooks,pages,components,utils},public}}

cd "$PROJECT"

# Root files
touch docker-compose.yml .env .env.example .gitignore README.md
touch scripts/bootstrap.sh && chmod +x scripts/bootstrap.sh

# Backend
touch backend/requirements.txt
touch backend/alembic.ini
touch backend/alembic/env.py
touch backend/alembic/script.py.mako
touch backend/app/__init__.py
touch backend/app/config.py
touch backend/app/database.py
touch backend/app/main.py
touch backend/app/dependencies.py
touch backend/app/models/__init__.py
touch backend/app/models/user.py
touch backend/app/models/project.py
touch backend/app/models/task.py
touch backend/app/schemas/__init__.py
touch backend/app/schemas/user.py
touch backend/app/schemas/project.py
touch backend/app/schemas/task.py
touch backend/app/routers/__init__.py
touch backend/app/routers/auth.py
touch backend/app/routers/users.py
touch backend/app/routers/projects.py
touch backend/app/routers/tasks.py
touch backend/app/services/__init__.py
touch backend/app/services/auth.py
touch backend/app/services/user.py
touch backend/app/middleware/__init__.py
touch backend/app/middleware/logging.py
touch backend/tests/__init__.py

# Frontend
touch frontend/package.json
touch frontend/vite.config.js
touch frontend/index.html
touch frontend/src/main.jsx
touch frontend/src/App.jsx
touch frontend/src/api/client.js
touch frontend/src/stores/authStore.js
touch frontend/src/hooks/useProjects.js
touch frontend/src/hooks/useTasks.js
touch frontend/src/pages/Login.jsx
touch frontend/src/pages/Dashboard.jsx
touch frontend/src/pages/ProjectDetail.jsx
touch frontend/src/components/Navbar.jsx
touch frontend/src/components/TaskCard.jsx
touch frontend/src/components/CreateProjectModal.jsx
touch frontend/src/utils/helpers.js

echo "✅ Structure created at ./$PROJECT"