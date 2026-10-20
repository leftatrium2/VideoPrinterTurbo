"""list_formats.py — 列出指定 URL 所有可下载的视频/音频格式"""
import asyncio
import os.path
import re
from pathlib import Path
from typing import Any

import yt_dlp

import config.config as _config
from utils.file_utils import get_download_path
from utils.proxy_utils import build_yt_dlp_proxies
from utils.task_utils import gen_task_id


def download(
        url: str,
        format_id: str | None = None,
        output_dir: str | Path = '.',
        *,
        proxy: str | None = None,
) -> dict[str, Any]:
    """下载指定视频格式（未指定时优先 MP4 最佳视频），配合最佳音频。

    使用 FFmpeg 将独立音视频合并为 MP4；没有独立音频时回退至单个格式。
    指定 format_id 时始终保留该视频选择，不为 MP4 偏好替换它。
    """
    if not url:
        raise ValueError('url 不能为空')
    if format_id:
        selected_format = f'{format_id}+bestaudio/{format_id}'
    else:
        selected_format = (
            'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/'
            'bestvideo+bestaudio/best'
        )
    opts = {
        'format': selected_format,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'paths': {'home': str(Path(output_dir).expanduser().resolve())},
        'outtmpl': '%(title)s [%(id)s].%(ext)s',
    }

    selected_proxy = build_yt_dlp_proxies(proxy)
    if selected_proxy is not None:
        opts['proxy'] = selected_proxy
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    if not info:
        raise RuntimeError('下载未返回视频信息')
    return info


def priority(fmt: dict[str, Any]) -> tuple:
    codec = (fmt.get('vcodec') or 'none').lower()
    families = (
        ('avc1', 'avc3', 'h.264', 'h264'),
        ('hev1', 'hvc1', 'hevc', 'h.265', 'h265'),
        ('vp08', 'vp8'),
        ('vp09', 'vp9'),
        ('av01', 'av1'),
    )
    rank = 0
    suffix = ''
    for index, aliases in enumerate(families):
        prefix = next((alias for alias in aliases if codec.startswith(alias)), None)
        if prefix is not None:
            rank = len(families) - index
            suffix = codec[len(prefix):].lstrip('.')
            break
    # AVC 的六位十六进制后缀依次为 profile、约束标志和 level。
    if rank == 5 and re.fullmatch(r'[0-9a-f]{6}', suffix):
        version = (int(suffix[:2], 16), int(suffix[4:], 16))
    else:
        version = tuple(int(part) for part in re.findall(r'\d+', suffix))
    return ((fmt.get('acodec') or 'none') == 'none', rank, version,
            fmt.get('vbr') if fmt.get('vbr') is not None else -1,
            fmt.get('fps') if fmt.get('fps') is not None else -1)


def list_formats(url: str, proxy: str | None = None) -> list[dict[str, str]]:
    """每个分辨率标签保留一个首选视频格式，标签按首次出现顺序返回。

    依次优先：纯视频、H.264 > H.265 > VP8 > VP9 > AV1 > 其他、
    同编码较高的 profile/level、较大 vbr、较大 fps；完全相同时保留首条。
    编码字符串无法表示发布时间，这里以其 profile/level 数值作为“最新”
    的比较依据；缺少该信息时按码率和帧率选择。
    短边 1440/2160/4320 标记为 2K/4K/8K，其余使用如 1080p 的标签。
    """
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'noplaylist': True,
    }
    if proxy:
        opts['proxy'] = build_yt_dlp_proxies(proxy)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        print("未能获取到任何信息")
        return []

    selected: dict[str, dict[str, Any]] = {}
    labels = {1440: '2K', 2160: '4K', 4320: '8K'}
    for fmt in info.get('formats') or []:
        width = fmt.get('width') or 0
        height = fmt.get('height') or 0
        if ((fmt.get('vcodec') or 'none') == 'none' or not fmt.get('format_id')
                or width <= 0 or height <= 0):
            continue
        short_side = min(width, height)
        label = labels.get(short_side, f'{short_side}p')
        if label not in selected or priority(fmt) > priority(selected[label]):
            selected[label] = fmt
    return [{f'{label}分辨率': str(fmt['format_id'])} for label, fmt in selected.items()]


def get_video_list(formats: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """从原始格式字典列表中，筛选纯视频流并按分辨率、编码、码率去重分类。

    筛选规则：
      1. 只保留有视频轨道的格式（vcodec != 'none'）
      2. 以 (resolution, vcodec, vbr) 为去重键，相同组合只保留第一条
    返回按分辨率字符串分组的字典，键为分辨率（如 '854x480'），值为该分辨率下的格式列表。
    """
    seen: set[tuple[str, str, float | None]] = set()
    grouped: dict[str, list[dict[str, Any]]] = {}

    for fmt in formats:
        vcodec = fmt.get('vcodec') or 'none'
        if vcodec == 'none':
            continue
        width, height = fmt.get('width'), fmt.get('height')
        resolution = (f'{width}x{height}' if width and height
                      else fmt.get('resolution') or '')
        key = (resolution, vcodec, fmt.get('vbr'))
        if key in seen:
            continue
        seen.add(key)
        grouped.setdefault(resolution, []).append(fmt)

    return grouped


if __name__ == "__main__":
    _config.init_config()

    output_path = asyncio.run(get_download_path())
    output_path = os.path.join(output_path, f"{gen_task_id()}.mp4")

    target_url = "https://www.youtube.com/watch?v=J0qbXRjDuRQ"
    # target_url = "https://www.bilibili.com/video/BV193JS62Ekr/?trackid=web_pegasus_0.router-web-pegasus-2479516-gfll4.1792143356271.411&spm_id_from=333.1007.tianma.1-1-1.click&vd_source=94814ebcf808b481389a4f02a131ed69"
    target_proxy = "http://127.0.0.1:7890"
    res_list = list_formats(target_url, target_proxy)
    print(res_list)
    download(target_url, 270, output_path, proxy=target_proxy)
