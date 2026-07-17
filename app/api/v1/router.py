from fastapi import APIRouter

from app.api.v1 import wallets

router = APIRouter(prefix="/api/v1")
router.include_router(wallets.router)
