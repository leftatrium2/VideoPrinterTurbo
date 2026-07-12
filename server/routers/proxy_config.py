from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptProxyConfig
from models.schemas import ProxyConfigItem
from utils import const
from utils.database import database
from utils.result import result_succ

router = APIRouter(
    prefix="/proxy_config",
    tags=["Proxy Config Module"]
)


@router.get("/")
async def get_proxy_config(db: AsyncSession = Depends(database.get_db)):
    ret_dict = {
        "proxy_type": const.PROXY_CONFIG_TYPE_UNKNOWN,
        "proxy_url": "",
        "proxy_username": "",
        "proxy_password": ""
    }
    result = await db.execute(select(VptProxyConfig).limit(1))
    item = result.scalar_one_or_none()
    if item:
        ret_dict['proxy_type'] = item.proxy_server_type
        ret_dict['proxy_url'] = item.proxy_server_url
        ret_dict['proxy_username'] = item.proxy_server_username
        ret_dict['proxy_password'] = item.proxy_server_password
    return result_succ(ret_dict)


@router.post("/update")
async def update_proxy_config(data: ProxyConfigItem, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptProxyConfig).limit(1))
    item = result.scalar_one_or_none()
    if not item:
        item = VptProxyConfig(
            proxy_server_type=data.proxy_type,
            proxy_server_url=data.proxy_url,
            proxy_server_username=data.proxy_username,
            proxy_server_password=data.proxy_password
        )
        db.add(item)
    else:
        item.proxy_server_type = data.proxy_type
        item.proxy_server_url = data.proxy_url
        item.proxy_server_username = data.proxy_username
        item.proxy_server_password = data.proxy_password
    await db.commit()
    await db.refresh(item)
    return result_succ()
