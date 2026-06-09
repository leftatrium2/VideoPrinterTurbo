"""YtDlpDownloader — downloads videos via yt-dlp with subtitle extraction."""

import json
import os
import subprocess
from pathlib import Path

from loguru import logger

from app.plugins.downloader.base import BaseDownloader, VideoPackage
from app.plugins.base import PluginType
from app.utils import utils


class YtDlpDownloader(BaseDownloader):
    """Download videos from URLs using yt-dlp.

    Supports automatic subtitle extraction and audio extraction.
    """

    type = PluginType.DOWNLOADER
    name = "yt-dlp"

    def __init__(self):
        self._check_available()

    @staticmethod
    def _check_available():
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.warning("yt-dlp not found. Install with: pip install yt-dlp")

    def validate_config(self) -> bool:
        return True

    def download(self, url: str, output_dir: str = "") -> VideoPackage:
        """Download a video and its associated subtitle/audio.

        Args:
            url: The video URL (YouTube, Bilibili, etc.).
            output_dir: Override directory. Defaults to utils.downloads_dir().

        Returns:
            VideoPackage with paths to video, audio, and optional subtitle.
        """
        if not output_dir:
            output_dir = utils.downloads_dir()

        video_id = utils.md5(url)[:12]
        task_dir = os.path.join(output_dir, video_id)
        os.makedirs(task_dir, exist_ok=True)

        # Output template
        output_template = os.path.join(task_dir, "%(title).80s.%(ext)s")

        # Step 1: Download best video + best audio
        logger.info(f"downloading video: {url}")
        video_cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", output_template,
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs", "all",
            "--convert-subs", "srt",
            "--no-playlist",
            "--print", "after_move:filepath",
            url,
        ]

        result = subprocess.run(video_cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp download failed: {result.stderr.strip()}")

        # Parse output path from yt-dlp's --print
        output_paths = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        video_path = ""
        subtitle_path = ""

        for p in output_paths:
            lower = p.lower()
            if lower.endswith((".mp4", ".mkv", ".webm")):
                video_path = p
            elif lower.endswith((".srt", ".vtt", ".ass")):
                subtitle_path = p

        if not video_path or not os.path.isfile(video_path):
            # Fallback: find the largest mp4 in the directory
            mp4_files = list(Path(task_dir).glob("*.mp4"))
            if mp4_files:
                video_path = str(mp4_files[0])

        # Step 2: Extract audio
        audio_path = os.path.join(task_dir, "audio.mp3")
        if not os.path.isfile(audio_path) and os.path.isfile(video_path):
            audio_cmd = [
                "yt-dlp",
                "-f", "bestaudio[ext=m4a]/bestaudio",
                "-o", os.path.join(task_dir, "audio.%(ext)s"),
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--no-playlist",
                "--print", "after_move:filepath",
                url,
            ]
            audio_result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=300)
            if audio_result.returncode == 0:
                audio_lines = [l.strip() for l in audio_result.stdout.strip().split("\n") if l.strip()]
                for p in audio_lines:
                    if p.lower().endswith(".mp3"):
                        audio_path = p
                        break

        # Step 3: Extract metadata via --dump-json
        metadata = {}
        info_cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=60)
        if info_result.returncode == 0:
            try:
                info = json.loads(info_result.stdout.strip().split("\n")[0])
                metadata = {
                    "title": info.get("title", ""),
                    "duration": info.get("duration", 0),
                    "width": info.get("width", 0),
                    "height": info.get("height", 0),
                    "uploader": info.get("uploader", ""),
                    "webpage_url": info.get("webpage_url", ""),
                }
            except (json.JSONDecodeError, IndexError):
                pass

        if not os.path.isfile(subtitle_path):
            # Try to find any subtitle file in the directory
            srt_files = list(Path(task_dir).glob("*.srt")) + list(Path(task_dir).glob("*.vtt"))
            if srt_files:
                subtitle_path = str(srt_files[0])

        package = VideoPackage(
            video_path=video_path,
            audio_path=audio_path if os.path.isfile(audio_path) else "",
            subtitle_path=subtitle_path if os.path.isfile(subtitle_path) else "",
            metadata=metadata,
            title=metadata.get("title", ""),
            duration=float(metadata.get("duration", 0)),
            width=int(metadata.get("width", 0)),
            height=int(metadata.get("height", 0)),
        )

        logger.success(f"downloaded: {video_path}, audio: {audio_path}, subtitle: {subtitle_path}")
        return package
