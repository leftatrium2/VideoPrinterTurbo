import asyncio
import logging
import os
import tempfile
from typing import Optional

import requests

import config.config as _config
from pipeline.tts.base import TTSBase
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils import const
from utils.file_utils import get_tts_rewrite_path, get_llm_rewrite_path
from utils.tts_utils import TTSUtils


class SiliconFlowTTS(TTSBase):
    __API_URL = "https://api.siliconflow.cn/v1/audio/speech"

    @staticmethod
    def synthesize(
            text,
            voice,
            out_path,
            api_key=None,
            model="FunAudioLLM/CosyVoice2-0.5B",
            response_format="mp3",
            speed=1.0,
            gain=0.0,
            proxy=None,
            **_,
    ):
        """
        调用硅基流动 TTS 接口合成语音并写入 out_path。

        voice: 系统预置音色需要带模型前缀，例如 "FunAudioLLM/CosyVoice2-0.5B:alex"；
               也可以传入音色克隆得到的 URI，例如 "speech:my-voice:xxx:yyy"。
        speed: 语速，浮点数，范围 [0.25, 4.0]，默认 1.0（本脚本仍会用 ffmpeg
               做二次精确对齐，speed 只是让首次合成结果更接近目标时长，减少
               后续拉伸幅度，非必需）。
        gain:  音量增益（dB），范围 [-10, 10]。
        """
        if not api_key:
            raise ValueError("provider=siliconflow 需要提供 --api-key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "gain": gain,
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None

        resp = requests.post(SiliconFlowTTS.__API_URL, json=payload, headers=headers, timeout=60, proxies=proxies)
        if resp.status_code != 200:
            raise RuntimeError(
                f"siliconflow tts 合成失败: {resp.status_code} {resp.text}"
            )

        with open(out_path, "wb") as f:
            f.write(resp.content)

    def __init__(self,
                 api_key: str,
                 proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
                 proxy_url: Optional[str] = None):
        self.__api_key = api_key
        self.__proxy_type = proxy_type
        self.__proxy_url = proxy_url

    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> Optional[str]:
        if not os.path.exists(subtitle_path):
            logging.error(f"File {subtitle_path} does not exist")
            return None
        name, ext = os.path.splitext(os.path.basename(subtitle_path))
        path = asyncio.run(get_tts_rewrite_path())
        subs = TTSUtils.parse_srt(subtitle_path)
        if not subs:
            logging.error(f"No subtitle in {subtitle_path}")
            return None
        tts_file_path = os.path.join(path, f"{name}.m4a")

        synth_kwargs = {
            "voice": voice, "api_key": self.__api_key, "model": "FunAudioLLM/CosyVoice2-0.5B",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            timeline = TTSUtils.build_timeline(subs, SiliconFlowTTS.synthesize, synth_kwargs, tmp_dir)
            TTSUtils.export_timeline(timeline, tts_file_path, bitrate=self.__bitrate)
        return tts_file_path


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    lang = asyncio.run(get_llm_rewrite_path())
    tts: TTSBase = SiliconFlowTTS(api_key="", proxy_url="http://127.0.0.1:7890")
    llm_rewrite_path = os.path.join(lang, "gSNFJbgoaHI.cn.srt")
    tts.rewrite(llm_rewrite_path, "", "FunAudioLLM/CosyVoice2-0.5B:alex")
