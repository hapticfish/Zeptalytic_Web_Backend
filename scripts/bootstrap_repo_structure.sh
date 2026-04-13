#!/usr/bin/env bash
set -euo pipefail

FORCE="false"
if [[ "${1:-}" == "--force" ]]; then
  FORCE="true"
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

write_file() {
  local path="$1"
  local content="$2"

  mkdir -p "$(dirname "$path")"

  if [[ -f "$path" && "$FORCE" != "true" ]]; then
    echo "skip  $path (already exists)"
    return
  fi

  printf "%s" "$content" > "$path"
  echo "write $path"
}

mkdir -p \
  app/api/routers \
  app/core \
  app/db/models \
  app/db/repositories \
  app/integrations \
  app/schemas \
  app/services \
  app/utils \
  app/workers \
  docs/architecture \
  prompt \
  progress \
  scripts \
  specs \
  tests/integration \
  tests/unit \
  alembic/versions

write_file app/__init__.py '"""Application package for Zeptalytic Web Backend."""\n'
write_file app/main.py $'from fastapi import FastAPI\n\nfrom app.core.config import settings\n\napp = FastAPI(title=settings.app_name)\n\n\n@app.get("/health")\ndef health() -> dict[str, str]:\n    return {"status": "ok"}\n'
write_file app/core/__init__.py '"""Core configuration and shared runtime utilities."""\n'
write_file app/core/config.py $'from pydantic_settings import BaseSettings, SettingsConfigDict\n\n\nclass Settings(BaseSettings):\n    app_env: str = "dev"\n    app_name: str = "Zeptalytic Web Backend"\n    api_v1_prefix: str = "/api/v1"\n    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/zeptalytic_web_backend"\n    pay_service_base_url: str = "http://localhost:8080"\n    pay_service_internal_token: str | None = None\n\n    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")\n\n\nsettings = Settings()\n'
write_file app/api/__init__.py '"""API layer for browser-facing routes and dependencies."""\n'
write_file app/api/deps.py $'from app.core.config import settings\n\n\ndef get_settings():\n    return settings\n'
write_file app/api/routers/__init__.py '"""API router modules live here."""\n'
write_file app/db/__init__.py '"""Database package."""\n'
write_file app/db/base.py $'from sqlalchemy.orm import DeclarativeBase\n\n\nclass Base(DeclarativeBase):\n    pass\n'
write_file app/db/session.py $'from sqlalchemy import create_engine\nfrom sqlalchemy.orm import sessionmaker\n\nfrom app.core.config import settings\n\nengine = create_engine(settings.database_url, future=True)\nSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)\n'
write_file app/db/models/__init__.py '"""ORM models package.\n\nModels are imported here as they are added so Alembic can see them.\n"""\n'
write_file app/db/repositories/__init__.py '"""Database repository layer."""\n'
write_file app/integrations/__init__.py '"""External integration clients and adapters."""\n'
write_file app/schemas/__init__.py '"""Pydantic request/response schemas."""\n'
write_file app/services/__init__.py '"""Service-layer business orchestration."""\n'
write_file app/utils/__init__.py '"""Shared utilities."""\n'
write_file app/workers/__init__.py '"""Background worker package."""\n'
write_file tests/__init__.py '"""Test package."""\n'
write_file tests/conftest.py '"""Shared pytest fixtures will live here."""\n'
write_file tests/unit/__init__.py '"""Unit tests."""\n'
write_file tests/integration/__init__.py '"""Integration tests."""\n'
write_file tests/unit/test_health.py $'from fastapi.testclient import TestClient\n\nfrom app.main import app\n\n\nclient = TestClient(app)\n\n\ndef test_health() -> None:\n    response = client.get("/health")\n    assert response.status_code == 200\n    assert response.json() == {"status": "ok"}\n'
write_file progress/progress.txt $'# Progress log (append-only)\n\n## Format for each iteration\n- Date/time (ISO 8601 with timezone):\n- Goal for this iteration:\n- What I found (repo search summary):\n- What I changed: (short description)\n- Why I changed:\n- Updated Files: (full repo-relative paths)\n- New Files: (full repo-relative paths)\n- Removed Files: (full repo-relative paths)\n\n- Tests run + results:\n- Notes / risks:\n- Next:\n- Sources used (only if needed; prefer official docs):\n'
write_file progress/last_message.txt ''
write_file .env.example $'APP_ENV=dev\nAPP_NAME=Zeptalytic Web Backend\nAPI_V1_PREFIX=/api/v1\nDATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/zeptalytic_web_backend\nPAY_SERVICE_BASE_URL=http://localhost:8080\nPAY_SERVICE_INTERNAL_TOKEN=replace-me\n'
write_file main.py $'from app.main import app\n\n\nif __name__ == "__main__":\n    import uvicorn\n\n    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)\n'
write_file .gitignore $'# Python\n__pycache__/\n*.py[cod]\n.venv/\nvenv/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n.coverage\nhtmlcov/\n\n# Local env\n.env\n.env.*\n!.env.example\n\n# Logs / harness outputs\n*.log\nprogress/codex.log\nprogress/last_message.txt\n'

echo
echo "Scaffold complete."
echo "Run the harness docs + spec files separately if they are not already in the repo."
