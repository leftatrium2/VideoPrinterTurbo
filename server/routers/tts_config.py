import logging
import os
import wave
from pathlib import Path

import anyio.to_thread
import edge_tts
import httpx
from fastapi import APIRouter
from fastapi.params import Query, Depends
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from models.model import VptTtsConfig
from models.schemas import TTSConfigItem
from utils import const
from utils.database import database
from utils.file_utils import get_current_path
from utils.result import result_failure, result_succ
from utils.tts_utils import TTSUtils
from utils.tts_voice import get_edge_tts_voices, get_azure_tts_v2_voices, get_silicon_flow_tts_voices, \
    get_google_gemini_tts_voices, get_xiaomi_mimo_tts_voices
import azure.cognitiveservices.speech as speechsdk

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
async def get_tts_voice_preview(engine: int = Query(default=0), voice: str = Query(default=""),
                                db: AsyncSession = Depends(database.get_db)):
    cwd = f"{Path.cwd().parent}"
    out_path = os.path.join(cwd, "storage/tts_sample/")
    await anyio.to_thread.run_sync(lambda: os.makedirs(out_path, exist_ok=True))
    voice_file_name = voice.replace("/", "_")
    output = os.path.join(out_path, voice_file_name + ".mp3")
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
    else:
        text = const.TTS_CONFIG_PREVIEW['en']
    result = await db.execute(select(VptTtsConfig).where(VptTtsConfig.tts_server == engine))
    item = result.scalar_one_or_none()
    if not item:
        return result_failure(const.TTS_CONFIG_ERR_ENGINE_NOT_FOUND,
                              f"TTS ENGINE {TTSUtils.get_name(engine)} is not config,pls config tts first")
    tts_area = item.tts_area
    tts_apikey = item.tts_apikey
    result = None
    if engine == const.TTS_LIST_AZURE_TTS_V1:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(output)
        result = {"output": output.replace(f"{cwd}/", "")}
    elif engine == const.TTS_LIST_AZURE_TTS_V2:
        speech_config = speechsdk.SpeechConfig(subscription=tts_apikey, region=tts_area)
        speech_config.speech_synthesis_voice_name = voice
        # 设置输出格式为 MP3
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            result = {"output": output.replace(f"{cwd}/", "")}
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logging.error(f"合成失败: {cancellation.reason}, {cancellation.error_details}")
            return result_failure(const.TTS_CONFIG_ERR_UNKNOWN,
                                  f"合成失败: {cancellation.reason}, {cancellation.error_details}")
    elif engine == const.TTS_LIST_SILICON_FLOW_TTS:
        model: str = "FunAudioLLM/CosyVoice2-0.5B"
        url = "https://api.siliconflow.cn/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {tts_apikey}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "mp3"
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output, "wb") as f:
                f.write(response.content)
            result = {"output": output.replace(f"{cwd}/", "")}
        else:
            return result_failure(const.TTS_CONFIG_ERR_UNKNOWN,
                                  f"合成失败: {response.status_code}, {response.text}")
    elif engine == const.TTS_LIST_GOOGLE_GEMINI_TTS:
        model = "gemini-2.5-flash-preview-tts"
        client = genai.Client(api_key=tts_apikey)
        response = await client.aio.models.generate_content(
            model=model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                )
            )
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        # Gemini 返回的是 24kHz/16bit/单声道 PCM，先存成 wav
        wav_path = output.rsplit(".", 1)[0] + ".wav"
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        # 转成 mp3（需要装 pydub + ffmpeg）
        from pydub import AudioSegment
        AudioSegment.from_wav(wav_path).export(output, format="mp3")
        result = {"output": output.replace(f"{cwd}/", "")}
    if not result:
        logging.error(f"TTS ENGINE {engine} NOT FOUND")
        return result_failure(const.TTS_CONFIG_ERR_ENGINE_NOT_FOUND, f"TTS ENGINE {engine} NOT FOUND")
    return result_succ(result)


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
