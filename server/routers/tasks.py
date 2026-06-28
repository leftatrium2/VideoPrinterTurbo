import json
import logging

from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.model import VptAsrConfig, VptVideoMaterialPexelsConfig, VptVideoMaterialPixabayConfig, VptTtsVoiceConfig
from pipeline.pipeline import pipeline
from utils import const
from utils.database import database
from utils.result import result_succ, result_failure

router = APIRouter(
    prefix="/tasks",
    tags=["任务模块"]
)


@router.get("/")
def get_tasks():
    return result_succ()


@router.post("/add")
def add_tasks():
    return {"message": "任务添加成功"}


@router.get("/config")
async def get_task_config(db: AsyncSession = Depends(database.get_db)):
    ret_dict = {}
    # 音频转文字 (ASR)
    ret_dict['asr'] = []
    ret_dict['asr'].append({"name": "从字幕提取", "value": const.TASK_CONFIG_ASR_FROM_SUBTITLE})
    result = await db.execute(select(VptAsrConfig).limit(1))
    item = result.scalar_one_or_none()
    # vpt_asr_config 表里面需要配置过相关的local whisper的项目，才会在新建任务的时候显示
    if item:
        if item.local_whisper_type != 0:
            ret_dict['asr'].append({"name": "从本地Whisper", "value": const.TASK_CONFIG_ASR_FROM_FASTER_WHISPER})
        if item.tencent_cloud_secret_id.strip() != "" and item.tencent_cloud_secret_key.strip() != "":
            ret_dict['asr'].append({"name": "从腾讯云ASR", "value": const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD})
        if item.xfyun_appid.strip() != "" and item.xfyun_secret_key.strip() != "":
            ret_dict['asr'].append({"name": "从科大讯飞ASR", "value": const.TASK_CONFIG_ASR_FROM_XF_YUN})
    # 输出到字幕
    ret_dict['subtitle'] = []
    ret_dict['subtitle'].append({"name": "Charm-Bold.ttf", "value": "Charm-Bold.ttf"})
    ret_dict['subtitle'].append({"name": "Charm-Regular.ttf", "value": "Charm-Regular.ttf"})
    ret_dict['subtitle'].append({"name": "MicrosoftYaHeiBold.ttf", "value": "MicrosoftYaHeiBold.ttf"})
    ret_dict['subtitle'].append({"name": "MicrosoftYaHeiNormal.ttf", "value": "MicrosoftYaHeiNormal.ttf"})
    ret_dict['subtitle'].append({"name": "STHeitiLight.ttf", "value": "STHeitiLight.ttf"})
    ret_dict['subtitle'].append({"name": "STHeitiMedium.ttf", "value": "STHeitiMedium.ttf"})
    ret_dict['subtitle'].append({"name": "UTM Kabel KT.ttf", "value": "UTM Kabel KT.ttf"})
    # 背景音乐
    ret_dict['bgm'] = []
    ret_dict['bgm'].append({"name": "随机背景音乐", "value": "random"})
    ret_dict['bgm'].append({"name": "自定义背景音乐", "value": "custom"})
    # 视频覆盖
    ret_dict['material'] = []
    ret_dict['material'].append({"name": "本地文件", "value": "local"})
    result = await db.execute(select(func.count()).select_from(VptVideoMaterialPexelsConfig))
    count = result.scalar_one()
    if count > 0:
        ret_dict['material'].append({"name": "Pexels", "value": "pexels"})
    result = await db.execute(select(func.count()).select_from(VptVideoMaterialPixabayConfig))
    count = result.scalar_one()
    if count > 0:
        ret_dict['material'].append({"name": "Pixabay", "value": "pixabay"})
    # 输出到语音 (TTS)
    ret_dict['tts'] = []
    # 输出到语音 -- Azure TTS V1
    result = await db.execute(select(VptTtsVoiceConfig))
    data = result.scalars().all()
    if len(data) != 0:
        for item in data:
            if item.tts_server_name.strip() == "TTS_LIST_AZURE_TTS_V1":
                # 输出到语音 -- Azure TTS V1
                ret_dict['tts'].append({"name": "Azure TTS V1", "value": "TTS_LIST_AZURE_TTS_V1",
                                        "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_AZURE_TTS_V2":
                # 输出到语音 -- Azure TTS V2
                ret_dict['tts'].append(
                    {"name": "Azure TTS V2", "value": "TTS_LIST_AZURE_TTS_V2",
                     "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_SILICON_FLOW_TTS":
                # 输出到语音 -- 硅基流动TTS
                ret_dict['tts'].append({"name": "SiliconFlow TTS", "value": "TTS_LIST_SILICON_FLOW_TTS",
                                        "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_GOOGLE_GEMINI_TTS":
                # 输出到语音 -- Google Gemini TTS
                ret_dict['tts'].append({"name": "Google Gemini TTS", "value": "TTS_LIST_GOOGLE_GEMINI_TTS",
                                        "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_XIAOMI_MIMO_TTS":
                # 输出到语音 -- Xiaomi MiMo TTS
                ret_dict['tts'].append({"name": "Xiaomi MiMo TTS", "value": "TTS_LIST_XIAOMI_MIMO_TTS",
                                        "voices": json.loads(item.tts_voice_content)})

    return result_succ(ret_dict)


@router.get("/check")
async def check_task_url(url: str = Query(default="", min_length=1, max_length=300)):
    logging.info(f"Checking task url: {url}")
    if not await pipeline.check(url):
        return result_failure(const.TASK_ERR_CHECK_URL, f"任务 url 检查失败，{url}")
    return result_succ()
