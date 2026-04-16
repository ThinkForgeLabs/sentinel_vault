$PROJECT = "taskflow"

# Directories
$dirs = @(
    "scripts"
    "backend/app/models"
    "backend/app/schemas"
    "backend/app/routers"
    "backend/app/services"
    "backend/app/middleware"
    "backend/alembic/versions"
    "backend/tests"
    "frontend/src/api"
    "frontend/src/stores"
    "frontend/src/hooks"
    "frontend/src/pages"
    "frontend/src/components"
    "frontend/src/utils"
    "frontend/public"
)

foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path "$PROJECT/$d" | Out-Null
}

# Files
$files = @(
    "docker-compose.yml", ".env", ".env.example", ".gitignore", "README.md",
    "scripts/bootstrap.sh",
    "backend/requirements.txt",
    "backend/alembic.ini",
    "backend/alembic/env.py",
    "backend/alembic/script.py.mako",
    "backend/app/__init__.py",
    "backend/app/config.py",
    "backend/app/database.py",
    "backend/app/main.py",
    "backend/app/dependencies.py",
    "backend/app/models/__init__.py",
    "backend/app/models/user.py",
    "backend/app/models/project.py",
    "backend/app/models/task.py",
    "backend/app/schemas/__init__.py",
    "backend/app/schemas/user.py",
    "backend/app/schemas/project.py",
    "backend/app/schemas/task.py",
    "backend/app/routers/__init__.py",
    "backend/app/routers/auth.py",
    "backend/app/routers/users.py",
    "backend/app/routers/projects.py",
    "backend/app/routers/tasks.py",
    "backend/app/services/__init__.py",
    "backend/app/services/auth.py",
    "backend/app/services/user.py",
    "backend/app/middleware/__init__.py",
    "backend/app/middleware/logging.py",
    "backend/tests/__init__.py",
    "frontend/package.json",
    "frontend/vite.config.js",
    "frontend/index.html",
    "frontend/src/main.jsx",
    "frontend/src/App.jsx",
    "frontend/src/api/client.js",
    "frontend/src/stores/authStore.js",
    "frontend/src/hooks/useProjects.js",
    "frontend/src/hooks/useTasks.js",
    "frontend/src/pages/Login.jsx",
    "frontend/src/pages/Dashboard.jsx",
    "frontend/src/pages/ProjectDetail.jsx",
    "frontend/src/components/Navbar.jsx",
    "frontend/src/components/TaskCard.jsx",
    "frontend/src/components/CreateProjectModal.jsx",
    "frontend/src/utils/helpers.js"
)

foreach ($f in $files) {
    New-Item -ItemType File -Force -Path "$PROJECT/$f" | Out-Null
}

Write-Host "✅ Structure created at .\$PROJECT"