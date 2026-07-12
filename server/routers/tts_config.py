import os
from pathlib import Path

import anyio.to_thread
import edge_tts
from fastapi import APIRouter
from fastapi.params import Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from models.model import VptTtsConfig
from models.schemas import TTSConfigItem
from utils import const
from utils.database import database
from utils.file_utils import get_current_path
from utils.result import result_failure, result_succ
from utils.tts_voice import get_edge_tts_voices, get_azure_tts_v2_voices, get_silicon_flow_tts_voices, \
    get_google_gemini_tts_voices, get_xiaomi_mimo_tts_voices

router = APIRouter(
    prefix="/tts_config",
    tags=["TTS Config Module"]
)


@router.get("/")
def get_tts_config():
    return {"abc": "bcd"}


@router.post("/update")
async def update(data: TTSConfigItem, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(VptTtsConfig).where(VptTtsConfig.tts_server == data.tts_server))
    item = result.scalar_one_or_none()
    if not item:
        # insert
        item = VptTtsConfig(
            tts_server=data.tts_server,
            tts_voice=data.tts_voice,
            tts_apikey=data.tts_apikey,
            tts_area=data.tts_area,
        )
        db.add(item)
    else:
        # update
        item.tts_voice = data.tts_voice
        item.tts_apikey = data.tts_apikey
        item.tts_area = data.tts_area
    await db.commit()
    await db.refresh(item)
    return result_succ({})


@router.get("/tts_list")
async def get_tts_list():
    return [
        {"name": "Azure TTS V1", "value": const.TTS_LIST_AZURE_TTS_V1},
        {"name": "Azure TTS V2", "value": const.TTS_LIST_AZURE_TTS_V2},
        {"name": "SiliconFlow TTS", "value": const.TTS_LIST_SILICON_FLOW_TTS},
        {"name": "Google Gemini TTS", "value": const.TTS_LIST_GOOGLE_GEMINI_TTS},
        {"name": "Xiaomi MiMo TTS", "value": const.TTS_LIST_XIAOMI_MIMO_TTS},
    ]


@router.get("/tts_config_detail")
async def get_tts_voice_list(engine: int = Query(default=0), db: AsyncSession = Depends(database.get_db)):
    if engine <= 0 or engine > 6:
        return result_failure(const.TTS_CONFIG_ERR_ENGINE_NOT_FOUND, f"TTS engine {engine} does not exist ")
    ret_list = {'voice': []}
    match engine:
        case const.TTS_LIST_AZURE_TTS_V1:
            ret_list['voice'] = await get_edge_tts_voices()
        case const.TTS_LIST_AZURE_TTS_V2:
            ret_list['voice'] = await get_azure_tts_v2_voices(db)
        case const.TTS_LIST_SILICON_FLOW_TTS:
            ret_list['voice'] = await get_silicon_flow_tts_voices()
        case const.TTS_LIST_GOOGLE_GEMINI_TTS:
            ret_list['voice'] = await get_google_gemini_tts_voices()
        case const.TTS_LIST_XIAOMI_MIMO_TTS:
            ret_list['voice'] = await get_xiaomi_mimo_tts_voices()
    result = await db.execute(select(VptTtsConfig).where(VptTtsConfig.tts_server == engine).limit(1))
    item = result.scalar_one_or_none()
    ret_list['tts_area'] = ""
    ret_list['tts_apikey'] = ""
    ret_list['tts_voice'] = ""
    ret_list['tts_server'] = ""
    if item:
        ret_list['tts_area'] = item.tts_area
        ret_list['tts_apikey'] = item.tts_apikey
        ret_list['tts_voice'] = item.tts_voice
        ret_list['tts_server'] = item.tts_server
    return result_succ(ret_list)


# Voice preview audition
@router.get("/tts_voice_preview")
async def get_tts_voice_preview(engine: int = Query(default=0), voice: str = Query(default="")):
    cwd = f"{Path.cwd().parent}"
    out_path = os.path.join(cwd, "storage/tts_sample/")
    await anyio.to_thread.run_sync(lambda: os.makedirs(out_path, exist_ok=True))
    output = os.path.join(out_path, voice + ".mp3")
    if engine <= 0 or engine > 6:
        return result_failure(const.TTS_CONFIG_ERR_ENGINE_NOT_FOUND, f"TTS engine {engine} does not exist ")
    voice = voice.strip()
    if not voice.startswith("zh-CN") and not voice.strip("en-US"):
        return result_failure(const.TTS_CONFIG_ERR_VOICE_NOT_FOUND, "TTS voice does not exist")
    text = None
    if voice.strip().startswith("zh-CN"):
        text = const.TTS_CONFIG_PREVIEW['zh']
    if voice.strip().startswith("en-US"):
        text = const.TTS_CONFIG_PREVIEW['en']
    if not text:
        return result_failure(const.TTS_CONFIG_ERR_VOICE_TEXT_NOT_FOUND, "TTS preview text does not exist")
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output)
    return result_succ({"output": output.replace(f"{cwd}/", "")})


@router.get("/preview")
async def get_tts_preview(file_path: str = Query(default="")):
    if not file_path.strip():
        return result_failure(const.TTS_CONFIG_ERR_PREVIEW_FILE_EMPTY, "File path cannot be empty")

    abs_file_path = os.path.join(get_current_path(), file_path)
    if not os.path.exists(abs_file_path):
        return result_failure(const.TTS_CONFIG_ERR_PREVIEW_FILE_NOT_EXISTS, "File path does not exist")

    def iterfile():
        with open(abs_file_path, "rb") as f:
            yield from f

    return StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={file_path}"},
    )
