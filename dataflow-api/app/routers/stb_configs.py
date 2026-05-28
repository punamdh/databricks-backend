from fastapi import APIRouter

from app.schemas.common import success_response
from app.schemas.stb_config import STBConfigCreate
from app.services.stb_config_service import STBConfigService

router = APIRouter(prefix="/stb/configs", tags=["stb-configs"])


@router.post("")
def create_stb_config(payload: STBConfigCreate):
    return success_response(STBConfigService.create(payload.model_dump()))
