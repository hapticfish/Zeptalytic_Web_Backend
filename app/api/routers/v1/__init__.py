from fastapi import APIRouter

from app.api.routers.v1.rewards import router as rewards_router

api_router = APIRouter()
api_router.include_router(rewards_router)
