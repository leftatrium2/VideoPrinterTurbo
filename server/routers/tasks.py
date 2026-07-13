import asyncio
import json
import logging
import os.path
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Query, Depends, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_

import config.config as _config
from middleware.i18n_middleware import get_current_lang
from models.model import VptAsrConfig, VptVideoMaterialPexelsConfig, VptVideoMaterialPixabayConfig, VptTtsVoiceConfig, \
    VptTask
from models.schemas import TaskItem
from pipeline.pipeline import pipeline
from utils import const
from utils.database import database
from utils.file_utils import get_upload_path
from utils.result import result_succ, result_failure
from utils.task_utils import gen_task_id

router = APIRouter(
    prefix="/tasks",
    tags=["Task Module"]
)

AUDIO_MIME_TYPE = ["audio/mpeg", "audio/wav", "audio/flac", "audio/aac", "audio/amr"]
VIDEO_MIME_TYPE = ["video/mp4", "video/mkv", "video/avi", "video/wmv", "video/flv"]
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.get("/list")
async def get_tasks(page: int = Query(default=1, min=1), page_size: int = Query(default=10, min=10, max=50),
                    db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(func.count()).select_from(VptTask).where(VptTask.is_deleted == 0))
    total = result.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(select(VptTask).where(VptTask.is_deleted == 0).offset(offset).limit(page_size))
    data = result.scalars().all()
    for item in data:
        del item.id
    return result_succ({
        "total": total,
        "data": data,
        "page": page,
        "page_size": page_size
    })


@router.get("/get")
async def get_tasks(task_id: str = Query(default=None), db: AsyncSession = Depends(database.get_db)):
    if not task_id:
        return result_failure(const.TASK_ERR_TASK_ID_EMPTY, "Task ID cannot be empty")
    result = await db.execute(select(VptTask).where(and_(
        VptTask.is_deleted == 0,
        VptTask.task_id == task_id
    )))
    item = result.scalar_one_or_none()
    if not item:
        return result_failure(const.TASK_ERR_TASK_NOT_FOUND, "Task not found")
    del item.id
    return result_succ(item)


@router.get("/del")
async def del_tasks(task_id: str = Query(default=None), db: AsyncSession = Depends(database.get_db)):
    if not task_id:
        return result_failure(const.TASK_ERR_TASK_ID_EMPTY, "Task ID cannot be empty")
    result = await db.execute(select(VptTask).where(and_(
        VptTask.is_deleted == 0,
        VptTask.task_id == task_id
    )))
    item = result.scalar_one_or_none()
    if not item:
        return result_failure(const.TASK_ERR_TASK_NOT_FOUND, "Task not found")
    item.is_deleted = 1
    await db.commit()
    await db.refresh(item)
    return result_succ()


@router.post("/add")
async def add_tasks(task: TaskItem, db: AsyncSession = Depends(database.get_db)):
    task_id = gen_task_id()
    item = VptTask(
        task_id=task_id,
        task_url=task.task_url,
        is_from_asr_or_subtitle=task.is_from_asr_or_subtitle,
        is_llm=task.is_llm,
        audio_rewrite_type=task.audio_rewrite_type,
        subtitle_lang=task.subtitle_lang,
        llm_prompt=task.llm_prompt,
        is_rewrite_to_tts=task.is_rewrite_to_tts,
        tts_server=task.tts_server,
        tts_voice=task.tts_voice,
        tts_volume=task.tts_volume,
        tts_speed=task.tts_speed,
        is_rewrite_to_subtitle=task.is_rewrite_to_subtitle,
        subtitle_font=task.subtitle_font,
        subtitle_position=task.subtitle_position,
        subtitle_font_color=task.subtitle_font_color,
        subtitle_border_color=task.subtitle_border_color,
        is_bgm=task.is_bgm,
        uploaded_bgm=json.dumps(task.uploaded_bgm),
        bgm_volume=task.bgm_volume,
        subtitle_size=task.subtitle_size,
        is_video_material=task.is_video_material,
        video_material_type=task.video_material_type,
        uploaded_video_material=json.dumps(task.uploaded_video_material),
        video_material_splicing_mode=task.video_material_splicing_mode,
        video_material_transition_mode=task.video_material_transition_mode,
        video_material_Video_ratio=task.video_material_Video_ratio,
        video_material_max_duration=task.video_material_max_duration,
        video_material_generate_count=task.video_material_generate_count,
        is_publish=task.is_publish
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return result_succ()


@router.post("/upload_material")
async def upload_material(files: list[UploadFile] = File(...)):
    ret_list = []
    for file in files:
        if file.content_type not in VIDEO_MIME_TYPE:
            return result_failure(const.TASK_CONFIG_ERR_INVALID_FILE_FORMAT, "Uploaded file must be in video format")
        # Read content to check size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return result_failure(const.TASK_CONFIG_ERR_FILE_SIZE_LIMIT_EXCEEDED,
                                  "Uploaded file size cannot exceed 50MB, filename: " + file.filename)
        content = await file.read()
        suffix = Path(file.filename).suffix
        saved_name = f"{uuid.uuid4().hex}{suffix}"
        upload_path = await get_upload_path()
        dest = Path(upload_path) / saved_name
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)
        abs_saved_name = os.path.join(_config.config['storage']['upload'], saved_name)
        ret_dict = {
            "filename": file.filename,
            "saved_as": abs_saved_name,
            "size": len(content),
            "content_type": file.content_type,
        }
        ret_list.append(ret_dict)
    return result_succ(ret_list)


@router.post("/upload_bgm")
async def upload_bgm(file: UploadFile = File(...)):
    if file.content_type not in AUDIO_MIME_TYPE:
        return result_failure(const.TASK_CONFIG_ERR_INVALID_FILE_FORMAT, "Uploaded file must be in audio format")
    # Read content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return result_failure(const.TASK_CONFIG_ERR_FILE_SIZE_LIMIT_EXCEEDED, "Uploaded file size cannot exceed 50MB")
    # Generate unique filename, preserving original extension
    suffix = Path(file.filename).suffix
    saved_name = f"{uuid.uuid4().hex}{suffix}"
    upload_path = await get_upload_path()
    dest = Path(upload_path) / saved_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)
    abs_saved_name = os.path.join(_config.config['storage']['upload'], saved_name)
    ret_dict = {
        "filename": file.filename,
        "saved_as": abs_saved_name,
        "size": len(content),
        "content_type": file.content_type,
    }
    return result_succ(ret_dict)


@router.get("/get_asr_lang")
async def get_asr_lang(asr_type: int = Query(default=None), db: AsyncSession = Depends(database.get_db)):
    lang = get_current_lang()
    if asr_type == const.TASK_CONFIG_ASR_FROM_SUBTITLE:
        ret_list = []
        for item in _config.i18n_config['asr_lang_list']['asr_lang_subtitle']:
            ret_list.append(item[lang])
        return result_succ(ret_list)

    return result_failure(const.TASK_ERR_UNKNOWN, "Unknown ASR type")


@router.get("/")
async def get_task_config(db: AsyncSession = Depends(database.get_db)):
    ret_dict = {}
    lang = get_current_lang()
    # Audio to Text (ASR)
    ret_dict['asr'] = []
    ret_dict['asr'].append(
        {"name": _config.i18n_config['task']['asr'][0][lang], "value": const.TASK_CONFIG_ASR_FROM_SUBTITLE})
    result = await db.execute(select(VptAsrConfig).limit(1))
    item = result.scalar_one_or_none()
    # vpt_asr_config: only show local whisper options when configured in the table
    if item:
        if item.local_whisper_type != 0:
            ret_dict['asr'].append({"name": _config.i18n_config['task']['asr'][1][lang],
                                    "value": const.TASK_CONFIG_ASR_FROM_FASTER_WHISPER})
        if item.tencent_cloud_secret_id.strip() != "" and item.tencent_cloud_secret_key.strip() != "":
            ret_dict['asr'].append({"name": _config.i18n_config['task']['asr'][2][lang],
                                    "value": const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD})
        if item.xfyun_appid.strip() != "" and item.xfyun_secret_key.strip() != "":
            ret_dict['asr'].append(
                {"name": _config.i18n_config['task']['asr'][3][lang], "value": const.TASK_CONFIG_ASR_FROM_XF_YUN})
    # Output to subtitle
    ret_dict['subtitle'] = []
    ret_dict['subtitle'].append({"name": _config.i18n_config['task']['subtitle'][0][lang], "value": "Charm-Bold.ttf"})
    ret_dict['subtitle'].append(
        {"name": _config.i18n_config['task']['subtitle'][1][lang], "value": "Charm-Regular.ttf"})
    ret_dict['subtitle'].append(
        {"name": _config.i18n_config['task']['subtitle'][2][lang], "value": "MicrosoftYaHeiBold.ttf"})
    ret_dict['subtitle'].append(
        {"name": _config.i18n_config['task']['subtitle'][3][lang], "value": "MicrosoftYaHeiNormal.ttf"})
    ret_dict['subtitle'].append({"name": _config.i18n_config['task']['subtitle'][4][lang], "value": "STHeitiLight.ttf"})
    ret_dict['subtitle'].append(
        {"name": _config.i18n_config['task']['subtitle'][5][lang], "value": "STHeitiMedium.ttf"})
    ret_dict['subtitle'].append({"name": _config.i18n_config['task']['subtitle'][6][lang], "value": "UTM Kabel KT.ttf"})
    # Background music
    ret_dict['bgm'] = []
    ret_dict['bgm'].append({"name": _config.i18n_config['task']['bgm'][0][lang], "value": "random"})
    ret_dict['bgm'].append({"name": _config.i18n_config['task']['bgm'][1][lang], "value": "custom"})
    # Video overlay
    ret_dict['material'] = {}
    # Video overlay - Video source
    ret_dict['material']['source'] = []
    ret_dict['material']['source'].append(
        {"name": _config.i18n_config['task']['material']['source'][0][lang], "value": const.VIDEO_MATERIAL_FROM_LOCAL})
    result = await db.execute(select(func.count()).select_from(VptVideoMaterialPexelsConfig))
    count = result.scalar_one()
    if count > 0:
        ret_dict['material']['source'].append({"name": _config.i18n_config['task']['material']['source'][1][lang],
                                               "value": const.VIDEO_MATERIAL_FROM_PEXELS})
    result = await db.execute(select(func.count()).select_from(VptVideoMaterialPixabayConfig))
    count = result.scalar_one()
    if count > 0:
        ret_dict['material']['source'].append({"name": _config.i18n_config['task']['material']['source'][2][lang],
                                               "value": const.VIDEO_MATERIAL_FROM_PIXABAY})
    # Video overlay - Splicing mode
    ret_dict['material']['splicing'] = []
    ret_dict['material']['splicing'].append(
        {"name": _config.i18n_config['task']['material']['splicing'][0][lang],
         "value": const.VIDEO_MATERIAL_RANDOM_SPLICING})
    ret_dict['material']['splicing'].append(
        {"name": _config.i18n_config['task']['material']['splicing'][1][lang],
         "value": const.VIDEO_MATERIAL_SEQUENTIAL_SPLICING})
    # Video overlay - Transition mode
    ret_dict['material']['transition'] = []
    ret_dict['material']['transition'].append({"name": _config.i18n_config['task']['material']['transition'][0][lang],
                                               "value": const.VIDEO_MATERIAL_TRANSITION_NO})
    ret_dict['material']['transition'].append(
        {"name": _config.i18n_config['task']['material']['transition'][1][lang],
         "value": const.VIDEO_MATERIAL_TRANSITION_RANDOM})
    ret_dict['material']['transition'].append(
        {"name": _config.i18n_config['task']['material']['transition'][2][lang],
         "value": const.VIDEO_MATERIAL_TRANSITION_GRADUAL_ENTRY})
    ret_dict['material']['transition'].append(
        {"name": _config.i18n_config['task']['material']['transition'][3][lang],
         "value": const.VIDEO_MATERIAL_TRANSITION_GRADUAL_EXIT})
    ret_dict['material']['transition'].append(
        {"name": _config.i18n_config['task']['material']['transition'][4][lang],
         "value": const.VIDEO_MATERIAL_TRANSITION_FADE_IN_OR_FADE_OUT})
    ret_dict['material']['transition'].append({"name": _config.i18n_config['task']['material']['transition'][5][lang],
                                               "value": const.VIDEO_MATERIAL_TRANSITION_SLIDE_IN})
    ret_dict['material']['transition'].append({"name": _config.i18n_config['task']['material']['transition'][6][lang],
                                               "value": const.VIDEO_MATERIAL_TRANSITION_SLIDE_OUT})
    # Video overlay - Video aspect ratio
    ret_dict['material']['ratio'] = []
    ret_dict['material']['ratio'].append(
        {"name": _config.i18n_config['task']['material']['ratio'][0][lang],
         "value": const.VIDEO_MATERIAL_SCREEN_RATIO_9_16})
    ret_dict['material']['ratio'].append(
        {"name": _config.i18n_config['task']['material']['ratio'][1][lang],
         "value": const.VIDEO_MATERIAL_SCREEN_RATIO_16_9})
    # Output to Speech (TTS)
    ret_dict['tts'] = []
    # Output to Speech -- Azure TTS V1
    result = await db.execute(select(VptTtsVoiceConfig))
    data = result.scalars().all()
    if len(data) != 0:
        for item in data:
            if item.tts_server_name.strip() == "TTS_LIST_AZURE_TTS_V1":
                # Output to Speech -- Azure TTS V1
                ret_dict['tts'].append({"name": "Azure TTS V1", "value": _config.i18n_config['task']['tts'][0][lang],
                                        "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_AZURE_TTS_V2":
                # Output to Speech -- Azure TTS V2
                ret_dict['tts'].append(
                    {"name": _config.i18n_config['task']['tts'][1][lang], "value": "TTS_LIST_AZURE_TTS_V2",
                     "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_SILICON_FLOW_TTS":
                # Output to Speech -- SiliconFlow TTS
                ret_dict['tts'].append(
                    {"name": _config.i18n_config['task']['tts'][2][lang], "value": "TTS_LIST_SILICON_FLOW_TTS",
                     "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_GOOGLE_GEMINI_TTS":
                # Output to Speech -- Google Gemini TTS
                ret_dict['tts'].append(
                    {"name": _config.i18n_config['task']['tts'][3][lang], "value": "TTS_LIST_GOOGLE_GEMINI_TTS",
                     "voices": json.loads(item.tts_voice_content)})
            if item.tts_server_name.strip() == "TTS_LIST_XIAOMI_MIMO_TTS":
                # Output to Speech -- Xiaomi MiMo TTS
                ret_dict['tts'].append(
                    {"name": _config.i18n_config['task']['tts'][4][lang], "value": "TTS_LIST_XIAOMI_MIMO_TTS",
                     "voices": json.loads(item.tts_voice_content)})

    return result_succ(ret_dict)


@router.get("/check")
async def check_task_url(url: str = Query(default="", min_length=1, max_length=300)):
    logging.info(f"Checking task url: {url}")
    result = await asyncio.to_thread(pipeline.check, url)
    if not result:
        return result_failure(const.TASK_ERR_CHECK_URL, f"Task URL check failed, {url}")
    return result_succ()
