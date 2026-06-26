# 创建config缓存文件
import asyncio
import json

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import init_config
from utils import const
from utils.database import database
from utils.tts_voice import get_edge_tts_voices, get_azure_tts_v2_voices, get_silicon_flow_tts_voices, \
    get_google_gemini_tts_voices, get_xiaomi_mimo_tts_voices


async def gen_config(db: AsyncSession):
    ret_dict = {}
    # 音频转文字
    ret_dict['asr'] = []
    ret_dict['asr'].append({"name": "从字幕提取", "value": const.TASK_CONFIG_ASR_FROM_SUBTITLE})
    ret_dict['asr'].append({"name": "从本地Whisper", "value": const.TASK_CONFIG_ASR_FROM_FASTER_WHISPER})
    ret_dict['asr'].append({"name": "从腾讯云ASR", "value": const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD})
    ret_dict['asr'].append({"name": "从科大讯飞ASR", "value": const.TASK_CONFIG_ASR_FROM_XF_YUN})
    # 输出到语音
    ret_dict['tts'] = []
    # 输出到语音 -- Azure TTS V1
    ret_dict['tts'].append({"name": "Azure TTS V1", "value": await get_edge_tts_voices()})
    # 输出到语音 -- Azure TTS V2
    ret_dict['tts'].append({"name": "Azure TTS V2", "value": await get_azure_tts_v2_voices(db)})
    # 输出到语音 -- 硅基流动TTS
    ret_dict['tts'].append({"name": "SiliconFlow TTS", "value": await get_silicon_flow_tts_voices()})
    # 输出到语音 -- Google Gemini TTS
    ret_dict['tts'].append({"name": "Google Gemini TTS", "value": await get_google_gemini_tts_voices()})
    # 输出到语音 -- Xiaomi MiMo TTS
    ret_dict['tts'].append({"name": "Xiaomi MiMo TTS", "value": await get_xiaomi_mimo_tts_voices()})
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
    ret_dict['bgm'].append({"name": "随机背景音乐", "value": "随机背景音乐"})
    ret_dict['bgm'].append({"name": "自定义背景音乐", "value": "自定义背景音乐"})
    # 视频覆盖
    ret_dict['material'] = []
    ret_dict['material'].append({"name": "Pexels", "value": "Pexels"})
    ret_dict['material'].append({"name": "Pixabay", "value": "Pixabay"})
    ret_dict['material'].append({"name": "本地文件", "value": "本地文件"})
    print(json.dumps(ret_dict, ensure_ascii=False, indent=4))
    async with aiofiles.open("config.result", "w", encoding="utf-8") as f:
        await f.write(json.dumps(ret_dict))


async def main():
    init_config()
    # 在脚本环境中直接创建数据库会话，而不是使用 get_db() 生成器
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession

    engine = database.get_engine()
    if engine is None:
        # 如果引擎未初始化，先启动
        database.start()
        engine = database.get_engine()

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await gen_config(session)


if __name__ == '__main__':
    asyncio.run(main())
