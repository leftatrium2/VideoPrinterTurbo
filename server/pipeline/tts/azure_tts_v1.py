import asyncio
import logging
import os
import subprocess
import tempfile
from datetime import timedelta

import edge_tts
import srt
from pydub import AudioSegment

from config.config import init_config
from pipeline.tts.base import TTSBase
from utils.file_utils import get_tts_rewrite_path, get_llm_rewrite_path


class AzureTTSV1(TTSBase):
    @staticmethod
    def parse_srt(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read()
        return list(srt.parse(content))

    @staticmethod
    def timedelta_to_ms(td: timedelta) -> int:
        return int(td.total_seconds() * 1000)

    @staticmethod
    def escape_ssml(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    @staticmethod
    def synthesize_to_file(text, voice, out_path, rate="+0%", volume="+0%",
                           pitch="+0Hz", proxy=None):
        """
        调用 edge-tts 把文本合成为音频文件（mp3），支持通过 proxy 参数走代理。
        对外是普通的同步函数：内部用 asyncio.run() 驱动 edge-tts 的异步调用。
        """

        async def _run():
            communicate = edge_tts.Communicate(
                text, voice=voice, rate=rate, volume=volume, pitch=pitch, proxy=proxy
            )
            await communicate.save(out_path)

        asyncio.run(_run())

    @staticmethod
    def stretch_to_duration(in_path, out_path, target_ms):
        """
        用 ffmpeg atempo 滤镜把 in_path 的音频精确拉伸/压缩到 target_ms 长度。
        单个 atempo 只支持 0.5~2.0 倍速区间，超出范围时链式组合多个 atempo。
        """
        current = AudioSegment.from_file(in_path)
        current_ms = len(current)

        if current_ms == 0 or target_ms <= 0:
            AudioSegment.silent(duration=max(target_ms, 0)).export(out_path, format="wav")
            return

        tempo = current_ms / target_ms  # >1 表示原音频偏长，需要加速
        filters = []
        remaining = tempo
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        filters.append(f"atempo={remaining:.6f}")

        cmd = [
            "ffmpeg", "-y", "-i", in_path,
            "-filter:a", ",".join(filters),
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        # atempo 拉伸后可能有几毫秒取整误差，这里做精确 pad/trim
        stretched = AudioSegment.from_file(out_path)
        diff = target_ms - len(stretched)
        if diff > 0:
            stretched = stretched + AudioSegment.silent(duration=diff)
        elif diff < 0:
            stretched = stretched[:target_ms]
        stretched.export(out_path, format="wav")

    @staticmethod
    def build_timeline(subs, voice, tmp_dir):
        total_end_ms = AzureTTSV1.timedelta_to_ms(subs[-1].end) if subs else 0
        timeline = AudioSegment.silent(duration=total_end_ms)

        for i, sub in enumerate(subs):
            start_ms = AzureTTSV1.timedelta_to_ms(sub.start)
            end_ms = AzureTTSV1.timedelta_to_ms(sub.end)
            target_ms = max(end_ms - start_ms, 1)

            raw_mp3 = os.path.join(tmp_dir, f"raw_{i}.mp3")
            fit_wav = os.path.join(tmp_dir, f"fit_{i}.wav")

            text = sub.content.strip()
            print(f"[{i + 1}/{len(subs)}] {text[:24]!r}  "
                  f"{start_ms}ms -> {end_ms}ms (目标 {target_ms}ms)")

            synthesize_to_file(text, voice, raw_mp3, proxy=proxy)
            AzureTTSV1.stretch_to_duration(raw_mp3, fit_wav, target_ms)

            clip = AudioSegment.from_file(fit_wav)
            timeline = timeline.overlay(clip, position=start_ms)

        return timeline

    __bitrate = "128k"

    def config(self, area: str, api_key: str, region: str):
        # edge-tts 不需要设置
        pass

    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> str or None:
        if not os.path.exists(subtitle_path):
            logging.error(f"File {subtitle_path} does not exist")
            return None
        name, ext = os.path.splitext(os.path.basename(subtitle_path))
        path = asyncio.run(get_tts_rewrite_path())
        subs = AzureTTSV1.parse_srt(subtitle_path)
        if not subs:
            logging.error(f"No subtitle in {subtitle_path}")
            return None
        tts_file_path = os.path.join(path, f"{name}.m4a")
        with tempfile.TemporaryDirectory() as tmp_dir:
            timeline = AzureTTSV1.build_timeline(subs, voice, tmp_dir)

            timeline.export(
                tts_file_path,
                format="ipod",  # ffmpeg 的 "ipod" muxer 对应 m4a (AAC in MP4)
                bitrate=self.__bitrate,
            )
        return tts_file_path


if __name__ == "__main__":
    init_config()
    lang = asyncio.run(get_llm_rewrite_path())
    llm_rewrite_path = os.path.join(lang, "gSNFJbgoaHI.cn.srt")
    tts: TTSBase = AzureTTSV1()
    tts.config()
    tts.rewrite(llm_rewrite_path, "zh-CN")
