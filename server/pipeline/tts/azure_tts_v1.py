import asyncio
import logging
import os
import tempfile
from typing import Optional

from config.config import init_config
from pipeline.tts.base import TTSBase
from utils import const
from utils.file_utils import get_tts_rewrite_path, get_llm_rewrite_path
from utils.tts_utils import TTSUtils


class AzureTTSV1(TTSBase):
    def __init__(self,
                 proxy_type: int = const.PROXY_CONFIG_TYPE_UNKNOWN,
                 proxy_url: Optional[str] = None):
        self.__proxy_type = proxy_type
        self.__proxy_url = proxy_url
        self.__bitrate = "128k"

    @staticmethod
    def synthesize(text, voice, out_path, proxy=None, **_):
        """
        调用 edge-tts 把文本合成为音频文件。edge-tts 本身是异步库，这里用
        asyncio.run() 在函数内部同步等待结果，对外呈现为普通同步函数。
        """
        import edge_tts

        async def _run():
            communicate = edge_tts.Communicate(text, voice=voice, proxy=proxy)
            await communicate.save(out_path)

        asyncio.run(_run())

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
        synth_kwargs = {"voice": voice, "proxy": self.__proxy}
        with tempfile.TemporaryDirectory() as tmp_dir:
            timeline = TTSUtils.build_timeline(subs, AzureTTSV1.synthesize, synth_kwargs, tmp_dir)

            timeline.export(
                tts_file_path,
                format="ipod",  # ffmpeg 的 "ipod" muxer 对应 m4a (AAC in MP4)
                bitrate=self.__bitrate,
            )
        return tts_file_path


if __name__ == "__main__":
    init_config()
    lang = asyncio.run(get_llm_rewrite_path())
    llm_rewrite_path = os.path.join(lang, "20260720215545133997.srt")
    tts: TTSBase = AzureTTSV1(
        proxy_type=const.PROXY_CONFIG_TYPE_HTTPS,
        proxy_url="http://127.0.0.1:7890"
    )
    tts.rewrite(llm_rewrite_path, "zh-CN", "zh-CN-XiaoxiaoNeural")
