from fastapi import APIRouter
from fastapi.params import Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptVideoMaterialPexelsConfig, VptVideoMaterialPixabayConfig
from models.schemas import MaterialPexelsItem, MaterialPixabayItem
from utils import const
from utils.database import database
from utils.result import result_succ, result_failure

router = APIRouter(
    prefix="/material_config",
    tags=["Material Config Module"]
)


@router.get("/pexels_list")
async def get_pexels_list_config(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(database.get_db)):
    offset = (page - 1) * page_size
    result = await db.execute(select(VptVideoMaterialPexelsConfig).offset(offset).limit(page_size))
    return result_succ({
        "data": result.scalars().all(),
        "page": page,
        "page_size": page_size
    })


@router.post("/add_pexels_config")
async def add_pexels_config(data: MaterialPexelsItem, db: AsyncSession = Depends(database.get_db)):
    item = VptVideoMaterialPexelsConfig(
        pexels_api_key=data.pexels_api_key
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return result_succ()


@router.get("/del_pexels_config")
async def del_pexels_config(pexels_config_id: int = Query(default=0), db: AsyncSession = Depends(database.get_db)):
    if not pexels_config_id:
        return result_failure(const.TTS_CONFIG_ERR_MATERIAL_PARAM, "pexels_config_id is empty")
    result = await db.execute(
        select(VptVideoMaterialPexelsConfig).where(VptVideoMaterialPexelsConfig.id == pexels_config_id))
    item = result.scalar_one_or_none()
    if not item:
        return result_failure(const.TTS_CONFIG_ERR_MATERIAL_PARAM, "pexels_config_id does not exist")
    print(item)
    await db.delete(item)
    await db.commit()
    return result_succ()


@router.get("/pixabay_list")
async def get_pixabay_list_config(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(database.get_db)):
    offset = (page - 1) * page_size
    result = await db.execute(select(VptVideoMaterialPixabayConfig).offset(offset).limit(page_size))
    return result_succ({
        "data": result.scalars().all(),
        "page": page,
        "page_size": page_size
    })


@router.post("/add_pixabay_config")
async def add_pixabay_config(data: MaterialPixabayItem, db: AsyncSession = Depends(database.get_db)):
    item = VptVideoMaterialPixabayConfig(
        pixabay_api_key=data.pixabay_api_key
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return result_succ()


@router.get("/del_pixabay_config")
async def del_pixabay_config(pixabay_config_id: int = Query(default=0), db: AsyncSession = Depends(database.get_db)):
    if not pixabay_config_id:
        return result_failure(const.TTS_CONFIG_ERR_MATERIAL_PARAM, "pixabay_config_id is empty")
    result = await db.execute(
        select(VptVideoMaterialPixabayConfig).where(VptVideoMaterialPixabayConfig.id == pixabay_config_id))
    item = result.scalar_one_or_none()
    if not item:
        return result_failure(const.TTS_CONFIG_ERR_MATERIAL_PARAM, "pixabay_config_id does not exist")
    await db.delete(item)
    await db.commit()
    return result_succ()
