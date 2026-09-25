import asyncio
import json
import subprocess
from pathlib import Path

from mpmath.ctx_mp_python import return_mpc

from pipeline.bean.asr_bean import AsrBean
from pipeline.bean.bgm_bean import BgmBean
from pipeline.bean.llm_bean import LLMBean
from pipeline.bean.tts_bean import TTSBean
from pipeline.bean.video_downloader_bean import VideoDownloaderBean
from pipeline.bean.video_overlay_bean import MaterialVideoBean
from pipeline.rendering.base import BaseAssemblyVideo
from pipeline.bean.pipeline_data import PipeLineData
from utils import const
from utils.convert_subtitle_ttml_to_srt import SubtitleBean
from utils.exception import VPTException
import config.config as _config
from utils.file_utils import get_output_path


class FFMpegAssemblyVideo(BaseAssemblyVideo):
    def __init__(self, pipeline_data: PipeLineData):
        self.__pipeline_data = pipeline_data

    def __escape_filter_path(file_path: str) -> str:
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
            video_height: int,
            position: str = "bottom",
            font_name: str = "Noto Sans CJK SC",
            font_size: int = 42,
            top_percent: float = 10,
    ) -> str:
        """
        生成 libass 字幕样式。

        position 可选值：
        - bottom：底部居中
        - top：顶部居中
        - top_percent：距顶部指定百分比的位置
        """
        common_style = (
            f"FontName={font_name},"
            f"FontSize={font_size},"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H80000000,"
            "Outline=2,"
            "Shadow=0"
        )

        if position == "bottom":
            # Alignment=2：底部居中
            return f"{common_style},Alignment=2,MarginV=50"

        if position == "top":
            # Alignment=8：顶部居中
            return f"{common_style},Alignment=8,MarginV=50"

        if position == "top_percent":
            # 将距顶部的百分比换算为像素；Alignment=8 表示顶部居中。
            margin_top = round(video_height * top_percent / 100)
            return f"{common_style},Alignment=8,MarginV={margin_top}"

        raise VPTException(const.PIPELINE_ERR_VIDEO_ASSEMBLY_SUBTITLE_POSITON, "position 仅支持：bottom、top、top_percent")

    def assembly(self, output_path: str) -> str:
        """
        合并纯视频、人声、背景音乐和字幕，生成 MP4。

        bgm_volume：
            背景音乐音量倍率。1.0 为原始音量，0.20 为原始音量的 20%。

        fonts_dir：
            可选字体目录。若系统未安装指定字体，可传入字体文件所在目录。
        """
        duration = self.__pipeline_data.video_bean.duration
        video_height = self.__pipeline_data.video_bean.height

        subtitle_style = self.__build_subtitle_style(
            video_height=video_height,
            position=subtitle_position,
            font_name=font_name,
            font_size=font_size,
            top_percent=subtitle_top_percent,
        )

        subtitle_file = escape_filter_path(subtitle_path)

        subtitle_filter = f"subtitles=filename='{subtitle_file}'"
        if fonts_dir:
            subtitle_filter += f":fontsdir='{escape_filter_path(fonts_dir)}'"

        subtitle_filter += f":force_style='{subtitle_style}'"

        filter_complex = (
            # 烧录字幕。烧录到画面后，视频必须重新编码。
            f"[0:v:0]{subtitle_filter}[video];"

            # 人声音频。
            "[1:a]aresample=48000,asetpts=N/SR/TB[voice];"

            # 背景音乐：调整音量，并裁剪到视频时长。
            f"[2:a]aresample=48000,"
            f"volume={bgm_volume},"
            f"atrim=duration={duration},"
            "asetpts=N/SR/TB[bgm];"

            # 混合人声和背景音乐。
            # normalize=0 保持设定的背景音量比例，但音源本身过大时可能削波。
            "[voice][bgm]"
            "amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[audio]"
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        command = [
            "ffmpeg",
            "-y",

            # 输入 0：纯视频。
            "-i", video_path,

            # 输入 1：人声。
            "-i", voice_path,

            # 输入 2：背景音乐；无限循环，后续会按视频时长裁剪。
            "-stream_loop", "-1",
            "-i", bgm_path,

            "-filter_complex", filter_complex,
            "-map", "[video]",
            "-map", "[audio]",

            # 保留源视频的容器级 metadata（若有）。
            "-map_metadata", "0",

            # 确保最终文件不会超过视频时长。
            "-t", f"{duration:.3f}",

            # H.264 + AAC 兼容性较好。
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",

            "-c:a", "aac",
            "-b:a", "192k",

            # 便于网页端边下载边播放。
            "-movflags", "+faststart",

            str(output),
        ]

    subprocess.run(command, check=True)


if __name__ == "__main__":
    _config.init_config()
    output_path = asyncio.run(get_output_path())
    if not output_path:
        raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "get_output_path 为空")

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
    pipeline_data.asr_bean.lang = "af"
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
    pipeline_data.subtitle_bean.subtitle_font = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/server/resources/fonts/MicrosoftYaHeiBold.ttf"
    pipeline_data.subtitle_bean.subtitle_font_color = 16777215
    pipeline_data.subtitle_bean.subtitle_border_color = 0
    pipeline_data.subtitle_bean.subtitle_position = ""
    pipeline_data.subtitle_bean.subtitle_size = 60
    pipeline_data.is_bgm = True
    pipeline_data.bgm_bean = BgmBean()
    pipeline_data.bgm_bean.bgm_volume = 0.5
    pipeline_data.bgm_bean.uploaded_bgm = ""
    pipeline_data.is_material = False
    pipeline_data.material_video_bean = MaterialVideoBean()
    pipeline_data.material_video_bean.video_material_type = ""
    pipeline_data.material_video_bean.uploaded_video_material = ""
    pipeline_data.material_video_bean.video_material_splicing_mode = 0
    pipeline_data.material_video_bean.video_material_transition_mode = 0
    pipeline_data.material_video_bean.video_material_video_ratio = 0
    pipeline_data.material_video_bean.video_material_max_duration = 0
    pipeline_data.material_video_bean.video_material_generate_count = 0
    pipeline_data.material_video_bean.video_material_keyword = ""
    pipeline_data.material_video_bean.video_materials = []

    # FFMpegAssemblyVideo 例子
    assembly_video = FFMpegAssemblyVideo(pipeline_data=pipeline_data)
    full_path = assembly_video.assembly(output_path)
