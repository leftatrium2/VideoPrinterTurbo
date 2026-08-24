import asyncio
import os
import re
import subprocess
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from loguru import logger
import requests

from config.config import init_config
from pipeline.downloader.base import BaseDownloader, DownloaderContext, VideoBean
from utils.const import DOWNLOADER_CODEC_MUXER_TYPE
from utils.file_utils import get_download_path

_API_BASE_URL = "https://api.bilibili.com"
_REQUEST_TIMEOUT = (10, 60)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
}


class BiliBiliAPIError(RuntimeError):
    """The Bilibili API rejected or could not provide a playable video."""


def _is_bilibili_video_url(url: str) -> bool:
    """Return whether *url* is a Bilibili playback-detail page."""
    parsed = urlparse(url)
    return (
            parsed.scheme in {"http", "https"}
            and (parsed.netloc.lower() == "bilibili.com" or parsed.netloc.lower().endswith(".bilibili.com"))
            and parsed.path.startswith("/video/")
    )


def _get_bvid(url: str) -> str:
    match = re.search(r"/video/(BV[0-9A-Za-z]+)", urlparse(url).path, re.IGNORECASE)
    if not match:
        raise ValueError("Unable to find a Bilibili BV id in the URL")
    return match.group(1)


def _get_page_number(url: str) -> int:
    try:
        return max(1, int(parse_qs(urlparse(url).query).get("p", ["1"])[0]))
    except ValueError:
        return 1


def _proxies(proxy: Optional[str]) -> Optional[dict[str, str]]:
    return {"http": proxy, "https": proxy} if proxy else None


def _request_json(path: str, params: dict[str, Any], proxy: Optional[str]) -> dict[str, Any]:
    with requests.get(
            f"{_API_BASE_URL}{path}",
            params=params,
            headers=_HEADERS,
            proxies=_proxies(proxy),
            timeout=_REQUEST_TIMEOUT,
    ) as response:
        response.raise_for_status()
        payload = response.json()
    if payload.get("code") != 0 or not payload.get("data"):
        raise BiliBiliAPIError(payload.get("message") or "Bilibili API returned no video data")
    return payload["data"]


def _get_video_info(url: str, proxy: Optional[str]) -> tuple[str, dict[str, Any], int]:
    bvid = _get_bvid(url)
    info = _request_json("/x/web-interface/view", {"bvid": bvid}, proxy)
    pages = info.get("pages") or []
    page_number = _get_page_number(url)
    if pages:
        if page_number > len(pages):
            raise BiliBiliAPIError(f"Video only has {len(pages)} page(s)")
        cid = pages[page_number - 1].get("cid")
    else:
        cid = info.get("cid")
    if not cid:
        raise BiliBiliAPIError("Bilibili video does not contain a playable page")
    return bvid, info, int(cid)


def _get_mp4_segments(bvid: str, cid: int, proxy: Optional[str]) -> list[list[str]]:
    play_info = _request_json(
        "/x/player/playurl",
        {"bvid": bvid, "cid": cid, "qn": 64, "fnval": 0, "fnver": 0, "fourk": 1},
        proxy,
    )
    segments: list[list[str]] = []
    for item in play_info.get("durl") or []:
        urls = [item.get("url"), *(item.get("backup_url") or [])]
        candidates = [stream_url for stream_url in urls if stream_url]
        if candidates:
            segments.append(candidates)
    if not segments:
        raise BiliBiliAPIError("Bilibili did not provide an MP4 playback URL")
    return segments


def _download_segment(
        urls: list[str],
        output_path: str,
        page_url: str,
        proxy: Optional[str],
        context: Optional[DownloaderContext],
        segment_index: int,
        segment_count: int,
) -> None:
    headers = {**_HEADERS, "Referer": page_url}
    last_error: Optional[Exception] = None
    for stream_url in urls:
        try:
            with requests.get(
                    stream_url,
                    headers=headers,
                    proxies=_proxies(proxy),
                    timeout=_REQUEST_TIMEOUT,
                    stream=True,
            ) as response:
                response.raise_for_status()
                total_bytes = int(response.headers.get("Content-Length") or 0)
                downloaded_bytes = 0
                with open(output_path, "wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        output.write(chunk)
                        downloaded_bytes += len(chunk)
                        if context and total_bytes:
                            progress = (segment_index + downloaded_bytes / total_bytes) / segment_count
                            context.on_progress(page_url, DOWNLOADER_CODEC_MUXER_TYPE, min(progress, 1.0))
                if context and not total_bytes:
                    context.on_progress(page_url, DOWNLOADER_CODEC_MUXER_TYPE, (segment_index + 1) / segment_count)
                return
        except (OSError, requests.RequestException) as error:
            last_error = error
            if os.path.exists(output_path):
                os.unlink(output_path)
    raise BiliBiliAPIError(f"Unable to download Bilibili MP4 segment: {last_error}")


def _merge_segments(segment_paths: list[str], output_path: str) -> None:
    if len(segment_paths) == 1:
        os.replace(segment_paths[0], output_path)
        return

    concat_path = f"{output_path}.concat.txt"
    try:
        with open(concat_path, "w", encoding="utf-8") as concat_file:
            for segment_path in segment_paths:
                concat_file.write("file '{}'\n".format(segment_path.replace("'", r"'\''")))
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path, "-c", "copy", output_path],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise BiliBiliAPIError("ffmpeg is required to merge multi-segment Bilibili videos") from error
    except subprocess.CalledProcessError as error:
        raise BiliBiliAPIError(f"ffmpeg could not merge Bilibili MP4 segments: {error.stderr}") from error
    finally:
        if os.path.exists(concat_path):
            os.unlink(concat_path)
        for segment_path in segment_paths:
            if os.path.exists(segment_path):
                os.unlink(segment_path)


class BiliBiliDownloader(BaseDownloader):
    def check(self, url: str, proxy: str = None) -> bool:
        if not _is_bilibili_video_url(url):
            return False
        try:
            bvid, info, cid = _get_video_info(url, proxy)
            return bool(info.get("duration", 0) > 0 and _get_mp4_segments(bvid, cid, proxy))
        except Exception as error:
            logger.warning("Unable to inspect Bilibili video {}: {}", url, error)
            return False

    def download(
            self,
            url: str,
            video_full_path: str,
            context: Optional[DownloaderContext],
            proxy: str = None,
    ) -> Optional[VideoBean]:
        if not _is_bilibili_video_url(url):
            error = ValueError("Only Bilibili playback-detail URLs are supported")
            if context:
                context.on_error(url, error)
            return None

        if context:
            context.on_create(url)
        directory = os.path.dirname(video_full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        try:
            if context:
                context.on_start(url)
            bvid, info, cid = _get_video_info(url, proxy)
            segments = _get_mp4_segments(bvid, cid, proxy)
            video_path = f"{video_full_path}.mp4"
            segment_paths = [f"{video_full_path}.part{index}.mp4" for index in range(len(segments))]
            for index, (segment_urls, segment_path) in enumerate(zip(segments, segment_paths)):
                _download_segment(segment_urls, segment_path, url, proxy, context, index, len(segments))
            _merge_segments(segment_paths, video_path)
            if not os.path.isfile(video_path):
                raise FileNotFoundError(f"Bilibili download did not create the expected MP4: {video_path}")

            dimension = info.get("dimension") or {}
            video = VideoBean(
                video_path=video_path,
                metadata={
                    "id": info.get("aid"),
                    "bvid": bvid,
                    "cid": cid,
                    "webpage_url": url,
                },
                title=info.get("title") or "",
                duration=float(info.get("duration") or 0),
                width=int(dimension.get("width") or 0),
                height=int(dimension.get("height") or 0),
            )
            if context:
                context.on_complete(url)
            return video
        except Exception as error:
            logger.exception("Failed to download Bilibili video {}", url)
            if context:
                context.on_error(url, error)
            return None


if __name__ == "__main__":
    import sys
    import tempfile


    class TestDownloaderContext(DownloaderContext):
        def on_create(self, url: str):
            print(f"on_create: {url}")

        def on_start(self, url: str):
            print(f"on_start: {url}")

        def on_progress(self, url: str, codec_type: int, progress: float):
            print(f"on_progress: codec={codec_type}, progress={progress:.1%}")

        def on_error(self, url: str, error: Exception):
            print(f"on_error: {url}: {error}")

        def on_complete(self, url: str):
            print(f"on_complete: {url}")


    init_config()

    test_url = "https://www.bilibili.com/video/BV1B38b6pE2w/?spm_id_from=333.1007.tianma.1-1-1.click"
    test_base_path = os.path.join(tempfile.mkdtemp(prefix="vpt_bilibili_"), "video")
    assert "yt_dlp" not in sys.modules, "Bilibili downloader must not import yt-dlp"
    full_path = asyncio.run(get_download_path())
    full_path = os.path.join(full_path, "20260720215545133998")
    downloader = BiliBiliDownloader()
    assert downloader.check(test_url), "Bilibili playback page should pass validation"
    video = downloader.download(test_url, full_path, TestDownloaderContext())
    assert video is not None, "download should return video metadata"
    assert video.video_path.endswith(".mp4") and os.path.isfile(video.video_path), "MP4 should exist"
    print(video)
