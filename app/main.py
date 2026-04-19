from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.routers import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
