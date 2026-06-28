# 创建config缓存文件
import asyncio
import json
from datetime import datetime, timedelta

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import init_config
from models.model import VptTtsVoiceConfig
from utils.database import database
from utils.tts_voice import get_edge_tts_voices, get_azure_tts_v2_voices, get_silicon_flow_tts_voices, \
    get_google_gemini_tts_voices, get_xiaomi_mimo_tts_voices


async def gen_config(db: AsyncSession):
    ret_dict = {}
    DATETIME_FORMAT_STR = "%Y-%m-%d %H:%M:%S"
    # TTS_LIST_AZURE_TTS_V1
    result = await db.execute(
        select(VptTtsVoiceConfig).where(VptTtsVoiceConfig.tts_server_name == "TTS_LIST_AZURE_TTS_V1"))
    item = result.scalar_one_or_none()
    if not item:
        voices = await get_edge_tts_voices()
        item = VptTtsVoiceConfig(
            tts_server_name="TTS_LIST_AZURE_TTS_V1",
            tts_voice_content=json.dumps(voices),
            tts_server_time=datetime.now().strftime(DATETIME_FORMAT_STR),
        )
        db.add(item)
    else:
        the_update_datetime = datetime.now()
        dt_str = item.tts_server_time
        if dt_str.strip():
            the_update_datetime = datetime.strptime(dt_str, DATETIME_FORMAT_STR)
        if abs(the_update_datetime - datetime.now()) > timedelta(days=10):
            voices = await get_edge_tts_voices()
            item.tts_voice_content = json.dumps(voices)
            item.tts_server_time = datetime.now().strftime(DATETIME_FORMAT_STR)
    await db.commit()
    await db.refresh(item)
    # TTS_LIST_AZURE_TTS_V2
    result = await db.execute(
        select(VptTtsVoiceConfig).where(VptTtsVoiceConfig.tts_server_name == "TTS_LIST_AZURE_TTS_V2"))
    item = result.scalar_one_or_none()
    if not item:
        voices = await get_azure_tts_v2_voices(db)
        item = VptTtsVoiceConfig(
            tts_server_name="TTS_LIST_AZURE_TTS_V2",
            tts_voice_content=json.dumps(voices),
            tts_server_time=datetime.now().strftime(DATETIME_FORMAT_STR),
        )
        db.add(item)
    else:
        the_update_datetime = datetime.now()
        dt_str = item.tts_server_time
        if dt_str.strip():
            the_update_datetime = datetime.strptime(dt_str, DATETIME_FORMAT_STR)
        if abs(the_update_datetime - datetime.now()) > timedelta(days=10):
            voices = await get_edge_tts_voices()
            item.tts_voice_content = json.dumps(voices)
            item.tts_server_time = datetime.now().strftime(DATETIME_FORMAT_STR)
    await db.commit()
    await db.refresh(item)
    # TTS_LIST_SILICON_FLOW_TTS
    result = await db.execute(
        select(VptTtsVoiceConfig).where(VptTtsVoiceConfig.tts_server_name == "TTS_LIST_SILICON_FLOW_TTS"))
    item = result.scalar_one_or_none()
    if not item:
        voices = await get_silicon_flow_tts_voices()
        item = VptTtsVoiceConfig(
            tts_server_name="TTS_LIST_SILICON_FLOW_TTS",
            tts_voice_content=json.dumps(voices),
            tts_server_time=datetime.now().strftime(DATETIME_FORMAT_STR),
        )
        db.add(item)
    else:
        the_update_datetime = datetime.now()
        dt_str = item.tts_server_time
        if dt_str.strip():
            the_update_datetime = datetime.strptime(dt_str, DATETIME_FORMAT_STR)
        if abs(the_update_datetime - datetime.now()) > timedelta(days=10):
            voices = await get_edge_tts_voices()
            item.tts_voice_content = json.dumps(voices)
            item.tts_server_time = datetime.now().strftime(DATETIME_FORMAT_STR)
    await db.commit()
    await db.refresh(item)
    # TTS_LIST_GOOGLE_GEMINI_TTS
    result = await db.execute(
        select(VptTtsVoiceConfig).where(VptTtsVoiceConfig.tts_server_name == "TTS_LIST_GOOGLE_GEMINI_TTS"))
    item = result.scalar_one_or_none()
    if not item:
        voices = await get_google_gemini_tts_voices()
        item = VptTtsVoiceConfig(
            tts_server_name="TTS_LIST_GOOGLE_GEMINI_TTS",
            tts_voice_content=json.dumps(voices),
            tts_server_time=datetime.now().strftime(DATETIME_FORMAT_STR),
        )
        db.add(item)
    else:
        the_update_datetime = datetime.now()
        dt_str = item.tts_server_time
        if dt_str.strip():
            the_update_datetime = datetime.strptime(dt_str, DATETIME_FORMAT_STR)
        if abs(the_update_datetime - datetime.now()) > timedelta(days=10):
            voices = await get_edge_tts_voices()
            item.tts_voice_content = json.dumps(voices)
            item.tts_server_time = datetime.now().strftime(DATETIME_FORMAT_STR)
    await db.commit()
    await db.refresh(item)
    # TTS_LIST_XIAOMI_MIMO_TTS
    result = await db.execute(
        select(VptTtsVoiceConfig).where(VptTtsVoiceConfig.tts_server_name == "TTS_LIST_XIAOMI_MIMO_TTS"))
    item = result.scalar_one_or_none()
    if not item:
        voices = await get_xiaomi_mimo_tts_voices()
        item = VptTtsVoiceConfig(
            tts_server_name="TTS_LIST_XIAOMI_MIMO_TTS",
            tts_voice_content=json.dumps(voices),
            tts_server_time=datetime.now().strftime(DATETIME_FORMAT_STR),
        )
        db.add(item)
    else:
        the_update_datetime = datetime.now()
        dt_str = item.tts_server_time
        if dt_str.strip():
            the_update_datetime = datetime.strptime(dt_str, DATETIME_FORMAT_STR)
        if abs(the_update_datetime - datetime.now()) > timedelta(days=10):
            voices = await get_edge_tts_voices()
            item.tts_voice_content = json.dumps(voices)
            item.tts_server_time = datetime.now().strftime(DATETIME_FORMAT_STR)
    await db.commit()
    await db.refresh(item)


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
