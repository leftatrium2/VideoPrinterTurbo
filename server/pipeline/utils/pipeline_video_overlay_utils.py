import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from openai import OpenAI
from sqlalchemy import select

from models.model import VptLlmConfig, VptVideoMaterialPexelsConfig, VptVideoMaterialPixabayConfig
from pipeline.material.base import BaseMaterialSearcher, VideoAspect
from pipeline.material.pexels_searcher import PexelsSearcher
from pipeline.material.pixabay_searcher import PixabaySearcher
from utils.database import database
from utils.file_utils import get_material_path
from utils.video_utils import get_video_duration

SUBTITLE_TIMESTAMP_RE = re.compile(
    r"^\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*"
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}"
)


def __read_subtitle_text(subtitle_file: str | Path) -> str:
    """读取 SRT、VTT 或每行一句的纯文本字幕，去除序号和时间轴。"""
    raw = Path(subtitle_file).read_text(encoding="utf-8-sig")

    subtitle_lines = []
    for line in raw.splitlines():
        line = line.strip()

        if (
                not line
                or line == "WEBVTT"
                or line.isdigit()
                or SUBTITLE_TIMESTAMP_RE.match(line)
                or line.startswith(("NOTE", "STYLE", "REGION"))
        ):
            continue

        # 去掉 VTT/HTML 标签，如 <i>、<c.color>
        line = re.sub(r"<[^>]+>", "", line)

        # 去除相邻重复字幕
        if not subtitle_lines or subtitle_lines[-1] != line:
            subtitle_lines.append(line)

    return " ".join(subtitle_lines)


def __get_material_keyword_from_llm(text_file_path: str) -> Optional[list]:
    if not os.path.exists(text_file_path):
        logging.error(f"{text_file_path} is not exists")
        return None
    subtitle_text = __read_subtitle_text(text_file_path)
    db = database.get_sync_session()
    result = db.execute(select(VptLlmConfig).limit(1))
    item = result.scalar_one_or_none()
    if not item:
        logging.error(
            f"LLM is not configured to extract search keywords from the subtitles of the current video footage.")
        return None
    api_key = item.api_key
    base_url = item.base_url
    if not api_key or not base_url:
        logging.error(
            f"LLM configure is not correct. api key: {api_key} or base_url: {base_url} not set")
        return None
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    amount = 5
    model = "gpt-5.5"
    if item.llm_model_name:
        model = item.llm_model_name
    system_prompt = """
  你是一个视频素材搜索词生成器。

  任务：根据用户提供的视频字幕，生成适合 Pexels、Pixabay 等素材网站使用的英文搜索词。

  规则：
  1. 只返回 JSON 字符串数组，不要 Markdown，不要解释。
  2. 每个搜索词包含 1 至 4 个英文单词。
  3. 搜索词应对应可视觉化的内容：人物、动作、物品、场景、环境或情绪。
  4. 覆盖字幕中的不同重点，避免语义重复。
  5. 优先使用可在视频素材网站中实际搜索到的具体表达。
  """.strip()
    user_prompt = f"""
  请基于以下字幕生成 {amount} 个英文视频素材搜索词：

  <subtitle>
  {subtitle_text}
  </subtitle>
  """.strip()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        extra_body={"enable_thinking": False}
    )
    text = response.choices[0].message.content.strip()
    # 即使模型意外附带说明，也尽量提取 JSON 数组
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        logging.error(f"模型未返回 JSON 数组：{text}")
        return None
    terms = json.loads(match.group())
    if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
        logging.error(f"模型返回格式错误：{text}")
        return None
    return terms


def __get_material_api_key(material_type: str) -> Optional[str]:
    db = database.get_sync_session()
    result = None
    if material_type == "pexels":
        result = db.execute(select(VptVideoMaterialPexelsConfig).limit(1))
    elif material_type == "pixabay":
        result = db.execute(select(VptVideoMaterialPixabayConfig).limit(1))
    if not result:
        logging.error(
            f"{material_type} is not configured of the current video footage.")
        return None
    item = result.scalar_one_or_none()
    if not item:
        logging.error(
            f"{material_type} is not configured of the current video footage in step2.")
        return None
    api_key = None
    if material_type == "pexels":
        api_key = item.pexels_api_key
    elif material_type == "pixabay":
        api_key = item.pixabay_api_key
    if not api_key:
        logging.error(
            f"{material_type} is not configured of the current video footage in step3.")
        return None
    return api_key


# 7. Video overlay
def video_overlay(
        video_file_path: str,
        subtitle_file_path: str,
        material_type: str,
        material_keyword: str,
        material_video_ratio: int = 0,
        material_max_duration: int = 0,
        proxy: Optional[str] = None
) -> list:
    # 1. 通过下载的视频文件，获取视频时长
    video_duration = get_video_duration(video_file_path)
    if video_duration <= 0:
        logging.error(f"{video_file_path} is not exists or not a video file")
        return []
    # 2. 搜索关键字
    video_searcher: Optional[BaseMaterialSearcher] = None
    api_key = __get_material_api_key(material_type)
    if material_type == "pexels":
        video_searcher = PexelsSearcher()
    elif material_type == "pixabay":
        video_searcher = PixabaySearcher()
    if not video_searcher:
        logging.error(
            f"Must Pexels or pixabay will use the video_overlay function, otherwise use the local uploader!")
        return []
    if proxy:
        video_searcher.config(proxy=proxy, api_keys=api_key)
    else:
        video_searcher.config(api_keys=api_key)
    material_path = asyncio.run(get_material_path())
    keyword_list = []
    # 如果用户设置了搜索关键字，那么优先使用此关键字搜索
    if material_keyword:
        keyword_list = material_keyword.split(' ')
    else:
        # 如果没有找到搜索关键字，那么从当前的字幕（ASR导出的也算）
        keyword_list = __get_material_keyword_from_llm(subtitle_file_path)
        if not keyword_list:
            logging.error("No keyword found")
            return []
    # 4 开始搜索
    video_aspect = VideoAspect.portrait
    if material_video_ratio == 1:
        video_aspect = VideoAspect.portrait
    elif material_video_ratio == 2:
        video_aspect = VideoAspect.landscape
    material_info_list = video_searcher.search(keyword_list, video_aspect, material_max_duration)
    # 5. 下载
    curr_video_duration = 0
    material_list = []
    if material_info_list:
        for material_info in material_info_list:
            full_file_path = video_searcher.download(material_info, material_path)
            material_dict = {
                "file_path": full_file_path,
                "duration": material_info.duration,
                "aspect": video_aspect.value,
                "provider": material_info.provider,
                "url": material_info.url
            }
            material_list.append(material_dict)

            curr_video_duration += material_info.duration
            if curr_video_duration >= video_duration:
                break
    return material_list
