from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptLipSyncConfig
from models.schemas import LipSyncConfigItem
from utils.database import database
from utils.result import result_succ

router = APIRouter(
    prefix="/lip_sync",
    tags=["LLM Config Module"]
)


@router.get("/")
async def get_lip_sync_config(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptLipSyncConfig).limit(1))
    item = result.scalar_one_or_none()
    ret_dict = {
        "sync_labs_apikey": "",
        "fal_latent_sync_apikey": "",
        "hey_gen_apikey": "",
    }
    if not item:
        return result_succ(ret_dict)

    ret_dict = {
        "sync_labs_apikey": item.sync_labs_apikey,
        "fal_latent_sync_apikey": item.fal_latent_sync_apikey,
        "hey_gen_apikey": item.hey_gen_apikey,
    }

    return result_succ(ret_dict)


@router.post("/update")
async def update_lip_sync_config(data: LipSyncConfigItem, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptLipSyncConfig).limit(1))
    item = result.scalar_one_or_none()
    if not item:
        item = VptLipSyncConfig(
            sync_labs_apikey=data.sync_labs_apikey,
            fal_latent_sync_apikey=data.fal_latent_sync_apikey,
            hey_gen_apikey=data.hey_gen_apikey,
        )
        db.add(item)
    else:
        item.sync_labs_apikey = data.sync_labs_apikey
        item.fal_latent_sync_apikey = data.fal_latent_sync_apikey
        item.hey_gen_apikey = data.hey_gen_apikey
    await db.commit()
    await db.refresh(item)
    return result_succ()
