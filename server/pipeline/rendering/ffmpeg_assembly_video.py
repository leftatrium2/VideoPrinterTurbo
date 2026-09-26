import asyncio
import math
import os.path
import subprocess
import threading
from pathlib import Path

from pipeline.bean.asr_bean import AsrBean
from pipeline.bean.bgm_bean import BgmBean
from pipeline.bean.llm_bean import LLMBean
from pipeline.bean.pipeline_data import PipeLineData
from pipeline.bean.tts_bean import TTSBean
from pipeline.bean.video_downloader_bean import VideoDownloaderBean
from pipeline.bean.video_overlay_bean import MaterialVideoBean, MaterialVideoItem
from pipeline.rendering.base import BaseAssemblyVideo
from utils import const
from utils.convert_subtitle_ttml_to_srt import SubtitleBean
from utils.exception import VPTException
from utils.file_utils import get_output_path, get_resource_font_path, get_resource_bgm_path
from utils.font_utils import get_font_params
from utils.logger import logger
import config.config as _config


class FFMpegAssemblyVideo(BaseAssemblyVideo):
    def __init__(self, pipeline_data: PipeLineData):
        self.__pipeline_data = pipeline_data

    def __escape_filter_path(self, file_path: str) -> str:
        """
        转义 FFmpeg filter 参数中的文件路径。

        即使 subprocess 使用参数列表，字幕路径仍位于 filter_complex
        字符串内部，所以仍需要单独转义。
        """
        path = str(Path(file_path).resolve()).replace("\\", "/")

        return (
            path
            .replace(":", r"\:")
            .replace("'", r"\'")
            .replace(",", r"\,")
            .replace("[", r"\[")
            .replace("]", r"\]")
        )

    def __build_subtitle_style(
            self,
            video_height: int,
            position: str = "bottom-center",
            font_name: str = "Noto Sans CJK SC",
            font_size: int = 42,
            top_percent: float = 10,
            font_color: int = 0xFFFFFF,
            font_edge_color: int = 0xFFFFFF
    ) -> str:
        """
        生成 libass 字幕样式。

        position 可选值：
        - "bottom-center"：底部居中
        - "top-center"：顶部居中
        - "center"：画面正中
        - 数值字符串（如 "60"）：距顶部指定百分比的位置
        - 空字符串：默认，等同于 "bottom-center"

        font_size 基于 PlayResY=1080，推荐范围：
        - 常规字幕（影视/教程）：36 ~ 48
        - 大字字幕（短视频/手机竖屏）：48 ~ 64
        - 小字字幕（信息密集/双行）：28 ~ 36
        """
        common_style = (
            "PlayResY=1080,"
            f"FontName={font_name},"
            f"FontSize={font_size},"
            f"PrimaryColour=&H{font_color:06X},"
            f"OutlineColour=&H{font_edge_color:06X},"
            "Outline=2,"
            "Shadow=0"
        )

        if position in ("", "bottom-center"):
            return f"{common_style},Alignment=2,MarginV=50"

        if position == "top-center":
            return f"{common_style},Alignment=8,MarginV=50"

        if position == "center":
            return f"{common_style},Alignment=5,MarginV=0"

        if position.isdigit():
            margin_top = round(video_height * int(position) / 100)
            return f"{common_style},Alignment=8,MarginV={margin_top}"

        raise VPTException(
            const.PIPELINE_ERR_VIDEO_ASSEMBLY_SUBTITLE_POSITON,
            "position 仅支持：bottom-center、top-center、center 或数值字符串（如 \"60\"）"
        )

    def assembly(self, output_path: str) -> str:
        """
        合并纯视频、人声、背景音乐和字幕，生成 MP4。

        bgm_volume：
            背景音乐音量倍率。1.0 为原始音量，0.20 为原始音量的 20%。

        fonts_dir：
            可选字体目录。若系统未安装指定字体，可传入字体文件所在目录。
        """
        duration = self.__pipeline_data.video_bean.duration
        video_width = self.__pipeline_data.video_bean.width
        video_height = self.__pipeline_data.video_bean.height
        filter_complex = ""
        command = [
            "ffmpeg",
            "-y"
        ]

        # ── 视频输入 ──
        # next_input_idx 追踪当前已添加的 -i 数量，用于后续音频动态编号
        next_input_idx = 0
        if self.__pipeline_data.is_material:
            materials = self.__pipeline_data.material_video_bean.video_materials
            if not materials:
                raise VPTException(
                    const.PIPELINE_ERR_FILE_NOT_FOUND,
                    "is_material=True 但 video_materials 为空"
                )
            n = len(materials)
            total_material_dur = sum(item.duration for item in materials)
            repeat = math.ceil(duration / total_material_dur) if total_material_dur > 0 else 1
            # 逐段 scale + pad，再 split 出 repeat 份独立副本
            for i in range(n):
                filter_complex += (
                    f"[{i}:v]scale=w={video_width}:h={video_height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad=w={video_width}:h={video_height}:x=-1:y=-1,"
                    f"setsar=1,setpts=PTS-STARTPTS[v{i}];"
                )
                split_outputs = "".join(f"[v{i}_{r}]" for r in range(repeat))
                filter_complex += f"[v{i}]split={repeat}{split_outputs};"
            # 按轮次拼接所有副本
            concat_labels = ""
            for r in range(repeat):
                for i in range(n):
                    concat_labels += f"[v{i}_{r}]"
            total = n * repeat
            filter_complex += (
                f"{concat_labels}concat=n={total}:a=0,"
                f"trim=duration={duration},setpts=PTS-STARTPTS[vout];"
            )
            vsrc = "[vout]"
        else:
            command.append("-i")
            command.append(self.__pipeline_data.video_bean.video_full_path)
            next_input_idx = 1

        # ── 视频滤镜 ──
        if self.__pipeline_data.is_material:
            n = len(materials)
            concat_inputs = ""
            for i in range(n):
                filter_complex += (
                    f"[{i}:v]scale=w={video_width}:h={video_height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad=w={video_width}:h={video_height}:x=-1:y=-1,"
                    f"setsar=1,setpts=PTS-STARTPTS[v{i}];"
                )
                concat_inputs += f"[v{i}]"
            filter_complex += (
                f"{concat_inputs}concat=n={n}:a=0[vcat];"
            )
            filter_complex += (
                f"[vcat]loop=loop=-1:size=1:start=0,"
                f"trim=duration={duration},setpts=PTS-STARTPTS[vout];"
            )
            vsrc = "[vout]"
        else:
            vsrc = "[0:v:0]"

        # ── 字幕 ──
        if self.__pipeline_data.is_asr:
            subtitle_position = self.__pipeline_data.subtitle_bean.subtitle_position
            font_full_path = os.path.join(get_resource_font_path(), self.__pipeline_data.subtitle_bean.subtitle_font)
            font_dir, font_name = get_font_params(font_full_path)
            font_size = self.__pipeline_data.subtitle_bean.subtitle_size
            font_color = self.__pipeline_data.subtitle_bean.subtitle_font_color
            font_edge_color = self.__pipeline_data.subtitle_bean.subtitle_border_color
            subtitle_style = self.__build_subtitle_style(
                video_height=video_height,
                position=subtitle_position,
                font_name=font_name,
                font_size=font_size,
                font_color=font_color,
                font_edge_color=font_edge_color
            )
            subtitle_path = self.__pipeline_data.asr_bean.subtitle_full_path
            if self.__pipeline_data.is_llm:
                subtitle_path = self.__pipeline_data.llm_bean.llm_full_path
            subtitle_file = self.__escape_filter_path(subtitle_path)
            subtitle_filter = f"subtitles=filename='{subtitle_file}'"
            if font_dir:
                subtitle_filter += f":fontsdir='{self.__escape_filter_path(font_dir)}'"
            subtitle_filter += f":force_style='{subtitle_style}'"
            filter_complex += f"{vsrc}{subtitle_filter}[video];"
            vsrc = "[video]"

        # ── 人声 ──
        if self.__pipeline_data.is_tts:
            tts_idx = next_input_idx
            command.append("-i")
            command.append(self.__pipeline_data.tts_bean.tts_full_path)
            next_input_idx += 1
            filter_complex += f"[{tts_idx}:a]aresample=48000,asetpts=N/SR/TB[voice];"

        # ── BGM ──
        if self.__pipeline_data.is_bgm:
            bgm_idx = next_input_idx
            command.extend(["-stream_loop", "-1"])
            command.append("-i")
            if self.__pipeline_data.bgm_bean.uploaded_bgm:
                command.append(self.__pipeline_data.bgm_bean.uploaded_bgm)
            else:
                import glob, random
                bgm_dir = get_resource_bgm_path()
                bgm_path = random.choice(glob.glob(os.path.join(bgm_dir, "output*.mp3")))
                command.append(bgm_path)
            next_input_idx += 1
            filter_complex += (
                f"[{bgm_idx}:a]aresample=48000,"
                f"volume={self.__pipeline_data.bgm_bean.bgm_volume},"
                f"atrim=duration={duration},"
                f"asetpts=N/SR/TB[bgm];"
            )
            if self.__pipeline_data.is_tts:
                filter_complex += (
                    "[voice][bgm]"
                    "amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[audio]"
                )

        # ── 映射输出流 ──
        if filter_complex:
            command.extend(["-filter_complex", filter_complex])
            command.extend(["-map", vsrc])
            if self.__pipeline_data.is_tts or self.__pipeline_data.is_bgm:
                if self.__pipeline_data.is_tts and self.__pipeline_data.is_bgm:
                    command.extend(["-map", "[audio]"])
                elif self.__pipeline_data.is_tts:
                    command.extend(["-map", "[voice]"])
                else:
                    command.extend(["-map", "[bgm]"])

        # ── 输出配置 ──
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        command.extend(["-map_metadata", "-1"])
        command.extend(["-t", f"{duration:.3f}"])
        command.extend(["-c:v", "libx264"])
        command.extend(["-preset", "medium"])
        command.extend(["-crf", "23"])
        command.extend(["-pix_fmt", "yuv420p"])
        command.extend(["-c:a", "aac"])
        command.extend(["-b:a", "192k"])
        command.extend(["-movflags", "+faststart"])
        command.append(str(output))
        command.extend(["-progress", "pipe:1"])

        logger.info("FFmpeg 开始编码: %s", " ".join(command))
        duration_us = int(duration * 1_000_000)
        stderr_lines: list[str] = []
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        def _drain_stderr():
            for line in process.stderr:
                stderr_lines.append(line)

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        for line in process.stdout:
            line = line.strip()
            if line.startswith("out_time_ms="):
                try:
                    current_us = int(line.split("=")[1])
                    progress = min(current_us / duration_us * 100, 100)
                    logger.info("编码进度: %.1f%%", progress)
                except (ValueError, ZeroDivisionError):
                    pass

        process.wait()
        stderr_thread.join()
        if process.returncode != 0:
            stderr_tail = "".join(stderr_lines[-50:])
            raise VPTException(
                const.PIPELINE_ERR_VIDEO_ASSEMBLY_SUBTITLE_POSITON,
                f"FFmpeg 编码失败 (返回码 {process.returncode}): {stderr_tail[-500:]}"
            )
        logger.info("FFmpeg 编码完成: %s", output)


if __name__ == "__main__":
    _config.init_config()
    output_path = asyncio.run(get_output_path())
    if not output_path:
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "get_output_path 为空")
    output_path = os.path.join(output_path, "20260913190132110313.mp4")

    # 一个 PipeLineData 数据例子
    pipeline_data = PipeLineData()
    pipeline_data.task_id = "20260913190132110313"
    pipeline_data.url = "https://www.youtube.com/watch?v=DgovrfgLxYs"
    pipeline_data.status = 0
    pipeline_data.video_bean = VideoDownloaderBean()
    pipeline_data.video_bean.task_url = "https://www.youtube.com/watch?v=DgovrfgLxYs"
    pipeline_data.video_bean.task_upload_video_path = ""
    pipeline_data.video_bean.task_original_video_path = ""
    pipeline_data.video_bean.video_full_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260913190132110313.mp4"
    pipeline_data.video_bean.metadata = {'uploader': 'Brock Mesarich | AI for Non Techies',
                                         'description': "✅\xa0Use Higgsfield: https://higgsfield.ai/s/tauNvD\n✅\xa0Connect to 9,000+ Different Apps: https://bit.ly/46PXnZr\n📚 Join my Skool Community for all of my resources: https://bit.ly/4t2yNgG\n\nChatGPT-6 Astra is the most capable model I've ever used, and it can do things no other model has come close to. In this video I combine it with Blender and Higgsfield to generate 3D objects, full worlds, and animations that just weren't possible before. By the end you'll see how much this changes what one person can create.\n\n0:00 - ChatGPT 6 Astra\n1:24 - The one prompt that runs the whole workflow\n2:15 - Connecting Higgsfield inside ChatGPT\n4:03 - The output: 3D Lego model, exploded video, and brick PDF\n7:10 - Building a creator studio in Blender from Higgsfield images\n8:51 - Turning the 3D world into an interactive walkthrough\n9:26 - Real estate style video with Seedance 2.5",
                                         'thumbnail': 'https://i.ytimg.com/vi/DgovrfgLxYs/maxresdefault.jpg',
                                         'tags': ['gpt 6 astra', 'gpt 6', 'astra', 'chatgpt 6 astra use cases',
                                                  'gpt 6 blender', 'chatgpt 6 astra blender', 'gpt-6 astra',
                                                  'chatgpt astra', 'gpt astra tutorial', 'gpt astra review']
                                         }
    pipeline_data.video_bean.title = "ChatGPT 6 Astra + Blender = Endless Possibilities"
    pipeline_data.video_bean.duration = 639
    pipeline_data.video_bean.width = 3840
    pipeline_data.video_bean.height = 2160
    pipeline_data.is_asr = True
    pipeline_data.asr_bean = AsrBean()
    pipeline_data.asr_bean.audio_rewrite_type = "BYTEDANCE"
    pipeline_data.asr_bean.task_url = "https://www.youtube.com/watch?v=DgovrfgLxYs"
    pipeline_data.asr_bean.lang = 0
    pipeline_data.asr_bean.subtitle_full_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/video_to_text/20260913190132110313.srt"
    pipeline_data.is_llm = True
    pipeline_data.llm_bean = LLMBean()
    pipeline_data.llm_bean.llm_text = "翻译为中文"
    pipeline_data.llm_bean.llm_full_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/llm_rewrite/20260913190132110313.srt"
    pipeline_data.is_tts = True
    pipeline_data.tts_bean = TTSBean()
    pipeline_data.tts_bean.tts_server = "TTS_LIST_AZURE_TTS_V2"
    pipeline_data.tts_bean.tts_voice = "en-US-AvaMultilingualNeural"
    pipeline_data.tts_bean.tts_volume = 1.0
    pipeline_data.tts_bean.tts_speed = 1.0
    pipeline_data.tts_bean.tts_full_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/tts_rewrite/20260913190132110313.m4a"
    pipeline_data.is_rewrite_subtitle = True
    pipeline_data.subtitle_bean = SubtitleBean()
    pipeline_data.subtitle_bean.subtitle_lang = 0
    pipeline_data.subtitle_bean.subtitle_font = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/server/resources/fonts/NotoSansSC-Regular.ttf"
    pipeline_data.subtitle_bean.subtitle_font_color = 16777215
    pipeline_data.subtitle_bean.subtitle_border_color = 0
    pipeline_data.subtitle_bean.subtitle_position = "bottom-center"
    pipeline_data.subtitle_bean.subtitle_size = 60
    pipeline_data.is_bgm = True
    pipeline_data.bgm_bean = BgmBean()
    pipeline_data.bgm_bean.bgm_volume = 0.5
    pipeline_data.bgm_bean.uploaded_bgm = ""
    # pipeline_data.is_material = False
    # pipeline_data.material_video_bean = MaterialVideoBean()
    # pipeline_data.material_video_bean.video_material_type = ""
    # pipeline_data.material_video_bean.uploaded_video_material = ""
    # pipeline_data.material_video_bean.video_material_splicing_mode = 0
    # pipeline_data.material_video_bean.video_material_transition_mode = 0
    # pipeline_data.material_video_bean.video_material_video_ratio = 0
    # pipeline_data.material_video_bean.video_material_max_duration = 0
    # pipeline_data.material_video_bean.video_material_generate_count = 0
    # pipeline_data.material_video_bean.video_material_keyword = ""
    # pipeline_data.material_video_bean.video_materials = []
    pipeline_data.is_material = True
    pipeline_data.material_video_bean = MaterialVideoBean()
    pipeline_data.material_video_bean.video_material_type = "pixabay"
    pipeline_data.material_video_bean.uploaded_video_material = []
    pipeline_data.material_video_bean.video_material_splicing_mode = 1
    pipeline_data.material_video_bean.video_material_transition_mode = 1
    pipeline_data.material_video_bean.video_material_video_ratio = 1
    pipeline_data.material_video_bean.video_material_max_duration = 10
    pipeline_data.material_video_bean.video_material_generate_count = 1
    pipeline_data.material_video_bean.video_material_keyword = ""
    pipeline_data.material_video_bean.video_materials = []

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-c8883244fa39f454d484b945649aa5d7ec33dce30c6bdeffc5e77945b529dd8d.mp4"
    item.duration = 21
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2024/07/01/218954_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-913b42a073de880793dc404920097535855b273ebed88ea48fa5599ac9f129e0.mp4"
    item.duration = 15
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2025/01/10/251763_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-5f8f7058fd005e989ebbf51d4b480ef5f8618faa06f99099198df6c852d213c5.mp4"
    item.duration = 10
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2023/10/17/185341-875417497_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-db73ed1f590a627f2efed4a161f3334b9a86fdae7f0f468c4cdb330783d0c4b6.mp4"
    item.duration = 25
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2025/08/12/296958_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-5f8f7058fd005e989ebbf51d4b480ef5f8618faa06f99099198df6c852d213c5.mp4"
    item.duration = 10
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2023/10/17/185341-875417497_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-0dd6feb1d05f5a4fe2b59b803074045b1e68ff8516d4f09a292bb16383151a1d.mp4"
    item.duration = 44
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2026/02/23/336374_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    item = MaterialVideoItem()
    item.file_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/material/pixabay-473438b21d08aff75f433659d88bb5fc8d7fe631e1f5b9bd08281a7984adb2a4.mp4"
    item.duration = 24
    item.aspect = 1
    item.provider = "pixabay"
    item.url = "https://cdn.pixabay.com/video/2025/01/03/250395_large.mp4"
    pipeline_data.material_video_bean.video_materials.append(item)

    # FFMpegAssemblyVideo 例子
    assembly_video = FFMpegAssemblyVideo(pipeline_data=pipeline_data)
    full_path = assembly_video.assembly(output_path)
