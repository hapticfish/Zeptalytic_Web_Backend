from fastapi import APIRouter

from app.api.routers.v1.addresses import router as addresses_router
from app.api.routers.v1.auth import router as auth_router
from app.api.routers.v1.communication_preferences import (
    router as communication_preferences_router,
)
from app.api.routers.v1.profiles import router as profiles_router
from app.api.routers.v1.rewards import router as rewards_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(addresses_router)
api_router.include_router(communication_preferences_router)
api_router.include_router(rewards_router)
