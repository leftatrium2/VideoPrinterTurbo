import asyncio

import azure.cognitiveservices.speech as speechsdk
from edge_tts import VoicesManager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.i18n_middleware import get_current_lang
from models.model import VptTtsConfig
from utils import const


async def get_xiaomi_mimo_tts_voices() -> list:
    ret_list = []
    lang = get_current_lang()
    # MiMo V2.5-TTS 预置音色列表（来源：官方文档截图）
    if lang == "en":
        MIMO_VOICES = [
            {"name": "mimo_default", "lang": "-", "gender": "-", "desc": "Default (Domestic=BingTang, Overseas=Mia)"},
            {"name": "BingTang", "lang": "Chinese", "gender": "Female"},
            {"name": "MoLi", "lang": "Chinese", "gender": "Female"},
            {"name": "SuDa", "lang": "Chinese", "gender": "Male"},
            {"name": "BaiHua", "lang": "Chinese", "gender": "Male"},
            {"name": "Mia", "lang": "English", "gender": "Female"},
            {"name": "Chloe", "lang": "English", "gender": "Female"},
            {"name": "Milo", "lang": "English", "gender": "Male"},
            {"name": "Dean", "lang": "English", "gender": "Male"},
        ]
    elif lang == "cn":
        MIMO_VOICES = [
            {"name": "mimo_default", "lang": "-", "gender": "-", "desc": "默认（国内集群=冰糖，海外=Mia）"},
            {"name": "冰糖", "lang": "Chinese", "gender": "女"},
            {"name": "茉莉", "lang": "Chinese", "gender": "女"},
            {"name": "苏打", "lang": "Chinese", "gender": "男"},
            {"name": "白桦", "lang": "Chinese", "gender": "男"},
            {"name": "Mia", "lang": "English", "gender": "女"},
            {"name": "Chloe", "lang": "English", "gender": "女"},
            {"name": "Milo", "lang": "English", "gender": "男"},
            {"name": "Dean", "lang": "English", "gender": "男"},
        ]
    for voice in MIMO_VOICES:
        ret_list.append(
            {"DisplayName": f"mimo:{voice['name']}-{voice['lang']}-{voice['gender']}", "Value": voice['name']})
    return ret_list


async def get_google_gemini_tts_voices() -> list:
    ret_list = []
    # 30 个声音 + 性别信息（来源：Google 官方文档及 Replicate 声音表）
    lang = get_current_lang()
    GEMINI_VOICES = []
    if lang == "en":
        GEMINI_VOICES = [
            {"name": "Zephyr", "gender": "Female"},
            {"name": "Puck", "gender": "Male"},
            {"name": "Charon", "gender": "Male"},
            {"name": "Kore", "gender": "Female"},
            {"name": "Fenrir", "gender": "Male"},
            {"name": "Leda", "gender": "Female"},
            {"name": "Orus", "gender": "Male"},
            {"name": "Aoede", "gender": "Female"},
            {"name": "Callirrhoe", "gender": "Female"},
            {"name": "Autonoe", "gender": "Female"},
            {"name": "Enceladus", "gender": "Male"},
            {"name": "Iapetus", "gender": "Male"},
            {"name": "Umbriel", "gender": "Male"},
            {"name": "Algieba", "gender": "Male"},
            {"name": "Despina", "gender": "Female"},
            {"name": "Erinome", "gender": "Female"},
            {"name": "Algenib", "gender": "Male"},
            {"name": "Rasalgethi", "gender": "Male"},
            {"name": "Laomedeia", "gender": "Female"},
            {"name": "Achernar", "gender": "Female"},
            {"name": "Alnilam", "gender": "Male"},
            {"name": "Schedar", "gender": "Female"},
            {"name": "Gacrux", "gender": "Male"},
            {"name": "Pulcherrima", "gender": "Female"},
            {"name": "Achird", "gender": "Male"},
            {"name": "Zubenelgenubi", "gender": "Male"},
            {"name": "Vindemiatrix", "gender": "Female"},
            {"name": "Sadachbia", "gender": "Male"},
            {"name": "Sadaltager", "gender": "Male"},
            {"name": "Sulafat", "gender": "Female"},
        ]
    elif lang == "cn":
        GEMINI_VOICES = [
            {"name": "Zephyr", "gender": "女"},
            {"name": "Puck", "gender": "男"},
            {"name": "Charon", "gender": "男"},
            {"name": "Kore", "gender": "女"},
            {"name": "Fenrir", "gender": "男"},
            {"name": "Leda", "gender": "女"},
            {"name": "Orus", "gender": "男"},
            {"name": "Aoede", "gender": "女"},
            {"name": "Callirrhoe", "gender": "女"},
            {"name": "Autonoe", "gender": "女"},
            {"name": "Enceladus", "gender": "男"},
            {"name": "Iapetus", "gender": "男"},
            {"name": "Umbriel", "gender": "男"},
            {"name": "Algieba", "gender": "男"},
            {"name": "Despina", "gender": "女"},
            {"name": "Erinome", "gender": "女"},
            {"name": "Algenib", "gender": "男"},
            {"name": "Rasalgethi", "gender": "男"},
            {"name": "Laomedeia", "gender": "女"},
            {"name": "Achernar", "gender": "女"},
            {"name": "Alnilam", "gender": "男"},
            {"name": "Schedar", "gender": "女"},
            {"name": "Gacrux", "gender": "男"},
            {"name": "Pulcherrima", "gender": "女"},
            {"name": "Achird", "gender": "男"},
            {"name": "Zubenelgenubi", "gender": "男"},
            {"name": "Vindemiatrix", "gender": "女"},
            {"name": "Sadachbia", "gender": "男"},
            {"name": "Sadaltager", "gender": "男"},
            {"name": "Sulafat", "gender": "女"},
        ]
    for voice in GEMINI_VOICES:
        ret_list.append({"DisplayName": f"gemini:{voice['name']}-{voice['gender']}", "Value": voice['name']})
    return ret_list


async def get_silicon_flow_tts_voices() -> list:
    lang = get_current_lang()
    ret_list = []
    if lang == "en":
        ret_list = [
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:alex-Steady Male",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:alex"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:benjamin-Deep Male",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:benjamin"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:charles-Magnetic Male",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:charles"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:david-Cheerful Male",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:david"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:anna-Steady Female",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:anna"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:bella-Passionate Female",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:bella"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:claire-Gentle Female",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:claire"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:diana-Cheerful Female",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:diana"},
        ]
    elif lang == "cn":
        ret_list = [
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:alex-沉稳男声", "Value": "FunAudioLLM/CosyVoice2-0.5B:alex"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:benjamin-低沉男声",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:benjamin"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:charles-磁性男声",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:charles"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:david-欢快男声", "Value": "FunAudioLLM/CosyVoice2-0.5B:david"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:anna-沉稳女声", "Value": "FunAudioLLM/CosyVoice2-0.5B:anna"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:bella-激情女声", "Value": "FunAudioLLM/CosyVoice2-0.5B:bella"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:claire-温柔女声",
             "Value": "FunAudioLLM/CosyVoice2-0.5B:claire"},
            {"DisplayName": "FunAudioLLM/CosyVoice2-0.5B:diana-欢快女声", "Value": "FunAudioLLM/CosyVoice2-0.5B:diana"},
        ]
    return ret_list


async def get_edge_tts_voices() -> list:
    lang = get_current_lang()
    ret_list = []
    voices = await VoicesManager.create()
    for voice in voices.voices:
        if voice['ShortName'].strip().startswith("en-US") or voice['ShortName'].strip().startswith("zh-CN"):
            if lang == "cn":
                sex = "女性" if voice['Gender'] == "Female" else "男性"
            elif lang == "en":
                sex = "Female" if voice['Gender'] == "Female" else "Male"
            ret_list.append(
                {"Value": voice['ShortName'], "DisplayName": f"{voice['ShortName']}-{sex}"})
    return ret_list


async def get_azure_tts_v2_voices(db: AsyncSession) -> list:
    ret_list = []
    lang = get_current_lang()
    # 查询 Azure TTS V2 配置
    result = await db.execute(select(VptTtsConfig).where(VptTtsConfig.tts_server == const.TTS_LIST_AZURE_TTS_V2))
    tts_config_item = result.scalar_one_or_none()
    if not tts_config_item:
        return ret_list

    api_key = tts_config_item.tts_apikey
    area = tts_config_item.tts_area

    speech_config = speechsdk.SpeechConfig(
        subscription=api_key,
        region=area
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    # get_voices_async 返回的是 SDK 自己的 Future，不是 asyncio.Future
    # 用 loop.run_in_executor 包一层，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: synthesizer.get_voices_async("").get()
    )
    if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
        for voice in result.voices:
            if lang == "cn":
                sex = "女性" if voice.gender.name == "Female" else "男性"
            elif lang == "en":
                sex = "Female" if voice.gender.name == "Female" else "Male"
            short_name = voice.short_name
            if short_name.strip().startswith("en-US") or short_name.strip().startswith("zh-CN"):
                ret_list.append({"DisplayName": f"{short_name}-V2-{sex}", "Value": short_name})
    return ret_list
