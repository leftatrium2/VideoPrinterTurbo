from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.i18n_middleware import get_current_lang
from models.model import VptAsrConfig
from models.schemas import ASRConfigItem
from utils import const
from utils.database import database
from utils.result import result_succ
import config.config as _config

router = APIRouter(
    prefix="/asr_config",
    tags=["asr配置模块"]
)


@router.get("/")
async def get_asr_config(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptAsrConfig).limit(1))
    item = result.scalar_one_or_none()
    ret_dict = {
        "tencent_cloud_secret_id": "",
        "tencent_cloud_secret_key": "",
        "xfyun_appid": "",
        "xfyun_secret_key": "",
        "xfyun_web_api": "",
        "local_whisper_type": ""
    }
    if not item:
        return result_succ(ret_dict)
    ret_dict = {
        "tencent_cloud_secret_id": item.tencent_cloud_secret_id,
        "tencent_cloud_secret_key": item.tencent_cloud_secret_key,
        "xfyun_appid": item.xfyun_appid,
        "xfyun_secret_key": item.xfyun_secret_key,
        "xfyun_web_api": item.xfyun_web_api,
        "local_whisper_type": item.local_whisper_type,
        "aliyun_cloud_api_key": item.aliyun_cloud_api_key,
        "aliyun_cloud_model": item.aliyun_cloud_model,
        "azure_subscription_key": item.azure_subscription_key,
        "azure_region": item.azure_region,
        "openai_api_key": item.openai_api_key,
        "openai_model": item.openai_model,
        "openai_base_url": item.openai_base_url,
        "volcengine_appid": item.volcengine_appid,
        "volcengine_access_token": item.volcengine_access_token
    }
    return result_succ(ret_dict)


@router.get("/local_whisper_list")
async def get_local_whisper_list():
    lang = get_current_lang()
    return result_succ([
        {"name": _config.i18n_config['asr_config']['local_whisper_list'][0][lang],
         "value": const.TASK_CONFIG_ASR_OPENAI_WHISPER},
        {"name": _config.i18n_config['asr_config']['local_whisper_list'][1][lang],
         "value": const.TASK_CONFIG_ASR_MLX_WHISPER},
        {"name": _config.i18n_config['asr_config']['local_whisper_list'][2][lang],
         "value": const.TASK_CONFIG_ASR_FASTER_WHISPER}
    ])


@router.post("/update")
async def update_asr_config(data: ASRConfigItem, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptAsrConfig).limit(1))
    item = result.scalar_one_or_none()
    if not item:
        item = VptAsrConfig(
            tencent_cloud_secret_id=data.tencent_cloud_secret_id,
            tencent_cloud_secret_key=data.tencent_cloud_secret_key,
            xfyun_appid=data.xfyun_appid,
            xfyun_secret_key=data.xfyun_secret_key,
            xfyun_web_api=data.xfyun_web_api,
            local_whisper_type=data.local_whisper_type,
            aliyun_cloud_api_key=data.aliyun_cloud_api_key,
            aliyun_cloud_model=data.aliyun_cloud_model,
            azure_subscription_key=data.azure_subscription_key,
            azure_region=data.azure_region,
            openai_api_key=data.openai_api_key,
            openai_model=data.openai_model,
            openai_base_url=data.openai_base_url,
            volcengine_appid=data.volcengine_appid,
            volcengine_access_token=data.volcengine_access_token
        )
        db.add(item)
    else:
        item.tencent_cloud_secret_id = data.tencent_cloud_secret_id
        item.tencent_cloud_secret_key = data.tencent_cloud_secret_key
        item.xfyun_appid = data.xfyun_appid
        item.xfyun_secret_key = data.xfyun_secret_key
        item.xfyun_web_api = data.xfyun_web_api
        item.local_whisper_type = data.local_whisper_type
        item.aliyun_cloud_api_key = data.aliyun_cloud_api_key
        item.aliyun_cloud_model = data.aliyun_cloud_model
        item.azure_subscription_key = data.azure_subscription_key
        item.azure_region = data.azure_region
        item.openai_api_key = data.openai_api_key
        item.openai_model = data.openai_model
        item.openai_base_url = data.openai_base_url
        item.volcengine_appid = data.volcengine_appid
        item.volcengine_access_token = data.volcengine_access_token
    await db.commit()
    await db.refresh(item)
    return result_succ({})
