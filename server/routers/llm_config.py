from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptLlmConfig
from models.schemas import LLMConfigItem
from utils.database import database
from utils.result import result_succ

router = APIRouter(
    prefix="/llm_config",
    tags=["LLM Config Module"]
)


@router.get("/")
async def get_llm_config(db: AsyncSession = Depends(database.get_db)):
    ret_dict = {
        "base_url": "",
        "api_key": "",
        "provider_name": "",
        "llm_model_name": "",
        "memo": "",
    }

    result = await db.execute(select(VptLlmConfig).limit(1))
    item = result.scalar_one_or_none()
    if item:
        ret_dict['base_url'] = item.base_url
        ret_dict['api_key'] = item.api_key
        ret_dict['provider_name'] = item.provider_name
        ret_dict['llm_model_name'] = item.llm_model_name
        ret_dict['memo'] = item.memo
    return result_succ(ret_dict)


@router.post("/update")
async def update_llm_config(data: LLMConfigItem, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptLlmConfig).limit(1))
    item = result.scalar_one_or_none()
    if not item:
        item = VptLlmConfig()
        db.add(item)
    else:
        item.base_url = data.base_url
        item.api_key = data.api_key
        item.provider_name = data.provider_name
        item.llm_model_name = data.llm_model_name
        item.memo = data.memo
    await db.commit()
    await db.refresh(item)
    return result_succ()
