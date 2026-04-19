from fastapi import APIRouter

from app.api.routers.reward_notifications import router as reward_notifications_router
from app.api.routers.reward_objectives import router as reward_objectives_router
from app.api.routers.rewards_summary import router as rewards_summary_router

router = APIRouter()
router.include_router(reward_notifications_router)
router.include_router(reward_objectives_router)
router.include_router(rewards_summary_router)
