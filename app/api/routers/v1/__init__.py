from fastapi import APIRouter

from app.api.routers.v1.announcements import router as announcements_router
from app.api.routers.v1.addresses import router as addresses_router
from app.api.routers.v1.billing import router as billing_router
from app.api.routers.v1.auth import router as auth_router
from app.api.routers.v1.communication_preferences import (
    router as communication_preferences_router,
)
from app.api.routers.v1.dashboard import router as dashboard_router
from app.api.routers.v1.launcher import router as launcher_router
from app.api.routers.v1.profiles import router as profiles_router
from app.api.routers.v1.rewards import router as rewards_router
from app.api.routers.v1.service_status import router as service_status_router
from app.api.routers.v1.support import router as support_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(addresses_router)
api_router.include_router(communication_preferences_router)
api_router.include_router(support_router)
api_router.include_router(announcements_router)
api_router.include_router(service_status_router)
api_router.include_router(rewards_router)
api_router.include_router(dashboard_router)
api_router.include_router(launcher_router)
api_router.include_router(billing_router)
