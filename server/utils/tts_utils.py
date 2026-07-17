import os
import subprocess
from datetime import timedelta

import srt
from pydub import AudioSegment

from utils import const


class TTSUtils:
    @staticmethod
    def get_name(engine: int) -> str or None:
        if engine == const.TTS_LIST_AZURE_TTS_V1:
            return "AZURE TTS V1"
        elif engine == const.TTS_LIST_AZURE_TTS_V2:
            return "AZURE TTS V2"
        elif engine == const.TTS_LIST_SILICON_FLOW_TTS:
            return "SILICON FLOW TTS"
        elif engine == const.TTS_LIST_GOOGLE_GEMINI_TTS:
            return "GOOGLE GEMINI TTS"
        return None

    @staticmethod
    def parse_srt(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read()
        return list(srt.parse(content))

    @staticmethod
    def timedelta_to_ms(td: timedelta) -> int:
        return int(td.total_seconds() * 1000)

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
    def build_timeline(subs, synth_fn, synth_kwargs, tmp_dir):
        """
        subs: parse_srt() 得到的字幕列表
        synth_fn: 形如 synth_fn(text, out_path=..., **synth_kwargs) 的合成函数，
                  由调用方根据所选 TTS provider 传入
        """
        total_end_ms = TTSUtils.timedelta_to_ms(subs[-1].end) if subs else 0
        timeline = AudioSegment.silent(duration=total_end_ms)

        for i, sub in enumerate(subs):
            start_ms = TTSUtils.timedelta_to_ms(sub.start)
            end_ms = TTSUtils.timedelta_to_ms(sub.end)
            target_ms = max(end_ms - start_ms, 1)

            raw_audio = os.path.join(tmp_dir, f"raw_{i}.audio")
            fit_wav = os.path.join(tmp_dir, f"fit_{i}.wav")

            text = sub.content.strip()
            print(f"[{i + 1}/{len(subs)}] {text[:24]!r}  "
                  f"{start_ms}ms -> {end_ms}ms (目标 {target_ms}ms)")

            synth_fn(text, out_path=raw_audio, **synth_kwargs)
            TTSUtils.stretch_to_duration(raw_audio, fit_wav, target_ms)

            clip = AudioSegment.from_file(fit_wav)
            timeline = timeline.overlay(clip, position=start_ms)

        return timeline

    @staticmethod
    def export_timeline(timeline, output_path, bitrate="128k"):
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        timeline.export(
            output_path,
            format="ipod",  # ffmpeg 的 "ipod" muxer 对应 m4a (AAC in MP4)
            bitrate=bitrate,
        )
