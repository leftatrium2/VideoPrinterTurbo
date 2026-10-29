"""HeyGen standalone Lip Sync adapter; keeps the caller's final voice and timeline."""
import json
import logging
import math
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests

from pipeline.lip_sync.base import LipSyncBase
from pipeline.lip_sync.progress import ProgressFile, response_size

logger = logging.getLogger(__name__)


class HeyGen(LipSyncBase):
    PROGRESS_PROVIDER = 'heygen'
    def __init__(self, api_key: str, mode: str = "precision", *,
                 base_url: str = "https://api.heygen.com/v3", proxy_url: str | None = None,
                 request_timeout: float = 60, upload_timeout: float = 600,
                 poll_interval: float = 10, job_timeout: float = 3600, on_progress=None):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("HeyGen api_key is required")
        if mode not in ("speed", "precision"):
            raise ValueError("HeyGen mode must be speed or precision")
        for name, value in (("request_timeout", request_timeout), ("upload_timeout", upload_timeout),
                            ("poll_interval", poll_interval), ("job_timeout", job_timeout)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        self._check_url(base_url)
        self._api_key = api_key.strip()
        self._mode = mode
        self._base_url = base_url.rstrip("/")
        self._proxy_url = proxy_url
        self._request_timeout = request_timeout
        self._upload_timeout = upload_timeout
        self._poll_interval = poll_interval
        self._job_timeout = job_timeout
        self.on_progress = on_progress
        self.last_lipsync_id: str | None = None

    @staticmethod
    def _check_url(url):
        if not isinstance(url, str):
            raise ValueError("HeyGen returned an invalid media URL")
        parsed = urlsplit(url)
        if parsed.scheme != "https" and not (
                parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")):
            raise ValueError("HeyGen URLs require HTTPS (HTTP allowed only for local testing)")
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid HeyGen URL")

    def _error_text(self, value):
        text = str(value).replace(self._api_key, "<redacted>")
        return re.sub(r"https?://\S+", "<redacted-url>", text)[:1000]

    def _request(self, session, method, url, *, authenticated=False, **kwargs):
        self._check_url(url)
        headers = kwargs.pop("headers", {})
        if authenticated:
            headers["x-api-key"] = self._api_key
        try:
            response = session.request(method, url, headers=headers, allow_redirects=False,
                                       timeout=kwargs.pop("timeout", self._request_timeout), **kwargs)
        except requests.RequestException as exc:
            raise RuntimeError(f"HeyGen {method} request failed ({type(exc).__name__})") from None
        if not 200 <= response.status_code < 300:
            try:
                body = response.json()
                error = body.get("error", {}) if isinstance(body, dict) else {}
                if isinstance(error, dict):
                    detail = error.get("message", error.get("code", ""))
                else:
                    detail = error
                if not detail and isinstance(body, dict):
                    detail = body.get("message", "")
                detail = self._error_text(detail)
            except ValueError:
                detail = "non-JSON response"
            response.close()
            raise RuntimeError(f"HeyGen {method} HTTP {response.status_code}: {detail}")
        return response

    def _api(self, session, method, path, **kwargs):
        with self._request(session, method, f"{self._base_url}/{path}", authenticated=True, **kwargs) as response:
            try:
                result = response.json()
            except ValueError:
                raise RuntimeError("HeyGen returned invalid JSON") from None
        if not isinstance(result, dict):
            raise RuntimeError("HeyGen returned an invalid response object")
        if result.get("error"):
            raise RuntimeError(f"HeyGen API error: {self._error_text(result['error'])}")
        data = result.get("data")
        if not isinstance(data, dict):
            raise RuntimeError("HeyGen response missing data object")
        return data

    @staticmethod
    def _required(data, key):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"HeyGen response missing {key}")
        return value

    def _upload(self, session, path, content_type):
        size = path.stat().st_size
        signed = self._api(session, "POST", "assets/direct-uploads", json={
            "filename": path.name, "content_type": content_type, "size_bytes": size})
        asset_id = self._required(signed, "asset_id")
        upload_url = self._required(signed, "upload_url")
        headers = signed.get("upload_headers")
        if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                                for k, v in headers.items()):
            raise RuntimeError("HeyGen response missing valid upload_headers")
        if any(self._api_key in value for value in headers.values()):
            raise RuntimeError("HeyGen upload headers unexpectedly contain the API key")
        max_bytes = signed.get("max_bytes")
        if isinstance(max_bytes, int) and size > max_bytes:
            raise ValueError("HeyGen asset exceeds the server's upload size limit")
        with path.open("rb") as source, self._request(
                session, "PUT", upload_url, data=ProgressFile(source, self._report_progress, "upload_video" if content_type.startswith("video/") else "upload_audio", path.stat().st_size), headers=headers, timeout=self._upload_timeout):
            pass
        complete = self._api(session, "POST", f"assets/{quote(asset_id, safe='')}/complete", json={})
        if self._required(complete, "asset_id") != asset_id:
            raise RuntimeError("HeyGen completed asset ID mismatch")
        return asset_id

    @staticmethod
    def _probe(path, kind):
        try:
            result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                                     "-of", "json", str(path)], check=True, capture_output=True,
                                    text=True, timeout=60)
            data = json.loads(result.stdout)
            stream = next(s for s in data["streams"] if s.get("codec_type") == kind)
            duration = float(stream.get("duration") or data["format"]["duration"])
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("invalid duration")
            return duration
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, StopIteration):
            raise ValueError(f"Invalid or unreadable {kind} file: {path.name}") from None

    @staticmethod
    def _ffmpeg(args):
        try:
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", *args], check=True,
                           capture_output=True, timeout=1800)
        except (OSError, subprocess.SubprocessError):
            raise RuntimeError("Lip sync video decoding or final audio mux failed") from None

    def _wait(self, session, generation):
        job_id = self._required(generation, "lipsync_id")
        self.last_lipsync_id = job_id
        logger.info("HeyGen lipsync submitted: %s", job_id)
        deadline = time.monotonic() + self._job_timeout
        previous = None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"HeyGen lipsync {job_id} timed out locally; remote job may still run. "
                                   "Check this lipsync before submitting again.")
            state = self._api(session, "GET", f"lipsyncs/{quote(job_id, safe='')}",
                              timeout=min(self._request_timeout, remaining))
            status = state.get("status")
            stage = {'pending': 'queued', 'running': 'running', 'completed': 'remote_completed'}.get(status, 'failed')
            self._report_progress(stage, job_id=job_id)
            if status != previous:
                logger.info("HeyGen lipsync %s: %s", job_id, status)
                previous = status
            if status == "completed":
                return self._required(state, "video_url")
            if status == "failed":
                raise RuntimeError(f"HeyGen lipsync {job_id} failed: "
                                   f"{self._error_text(state.get('failure_message', ''))}")
            if status not in ("pending", "running"):
                raise RuntimeError(f"HeyGen lipsync {job_id}: unknown status {self._error_text(status)}")
            time.sleep(min(self._poll_interval, max(0, deadline - time.monotonic())))

    def lip_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        self._start_progress(self.PROGRESS_PROVIDER)
        self.last_lipsync_id = None
        video, audio, output = [Path(p).expanduser().resolve() for p in (video_path, audio_path, output_path)]
        if output in (video, audio) or output.exists():
            raise ValueError("Lip sync output must be a new file, distinct from both inputs")
        for path in (video, audio):
            if not path.is_file() or not path.stat().st_size:
                raise ValueError(f"Lip sync input missing or empty: {path.name}")

        video_duration = self._probe(video, "video")
        audio_duration = self._probe(audio, "audio")
        # Allow only encoding/frame rounding, never a genuine timing adjustment.
        if abs(video_duration - audio_duration) > 0.15:
            raise ValueError(
                f"Lip sync inputs must share a timeline: video={video_duration:.3f}s, audio={audio_duration:.3f}s")
        if output.suffix.lower() != ".mp4":
            raise ValueError("Lip sync output_path must end with .mp4")
        if video.suffix.lower() not in (".mp4", ".webm"):
            raise ValueError("HeyGen video must be MP4 or WebM")
        if video.stat().st_size > 200 * 1024 ** 2:
            raise ValueError("HeyGen video exceeds the 200 MiB direct-upload limit")
        output.parent.mkdir(parents=True, exist_ok=True)
        with requests.Session() as session, tempfile.TemporaryDirectory(prefix="heygen_lip_sync_",
                                                                        dir=output.parent) as temp:
            session.trust_env = False
            if self._proxy_url:
                session.proxies.update(http=self._proxy_url, https=self._proxy_url)
            # HeyGen assets accept WAV/MP3. Keep TTS M4A inputs intact and upload a WAV copy.
            upload_audio = audio
            if audio.suffix.lower() not in (".wav", ".mp3"):
                upload_audio = Path(temp) / "voice.wav"
                self._ffmpeg(["-i", str(audio), "-map", "0:a:0", "-vn", "-c:a", "pcm_s16le", str(upload_audio)])
                if abs(self._probe(upload_audio, "audio") - video_duration) > 0.15:
                    raise ValueError("HeyGen converted audio duration mismatch")
            if upload_audio.stat().st_size > int(1.5 * 1024 ** 3):
                raise ValueError("HeyGen audio exceeds the 1.5 GiB direct-upload limit")
            video_id = self._upload(session, video, "video/mp4" if video.suffix.lower() == ".mp4" else "video/webm")
            audio_id = self._upload(session, upload_audio,
                                    "audio/wav" if upload_audio.suffix.lower() == ".wav" else "audio/mpeg")
            self._report_progress("submitting")
            # No automatic retries: a lost response may hide an accepted paid job.
            generation = self._api(session, "POST", "lipsyncs", json={
                "video": {"type": "asset_id", "asset_id": video_id},
                "audio": {"type": "asset_id", "asset_id": audio_id},
                "mode": self._mode, "enable_dynamic_duration": False,
                "enable_caption": False, "disable_music_track": True,
                "enable_speech_enhancement": False, "keep_the_same_format": True,
                "fps_mode": "passthrough"})
            url = self._wait(session, generation)
            downloaded = Path(temp) / "download.mp4"
            # Separate unauthenticated request: never leak the API key to storage/CDN.
            try:
                with self._request(session, "GET", url, stream=True) as response, downloaded.open("wb") as target:
                    self._report_progress("download")
                    received = 0
                    total = response_size(response)
                    deadline = time.monotonic() + self._upload_timeout
                    for chunk in response.iter_content(1024 * 1024):
                        if time.monotonic() > deadline:
                            raise TimeoutError("HeyGen output download timed out")
                        target.write(chunk)
                        received += len(chunk)
                        self._report_progress("download", completed=received, total=total, unit="bytes")
            except requests.RequestException as exc:
                raise RuntimeError(f"HeyGen output transfer failed ({type(exc).__name__})") from None
            if not downloaded.stat().st_size:
                raise RuntimeError("HeyGen returned an empty output video")
            self._report_progress("validating")
            duration = self._probe(downloaded, "video")
            if abs(duration - video_duration) > 0.15:
                raise ValueError("HeyGen changed the video duration; output rejected")
            self._ffmpeg(["-i", str(downloaded), "-map", "0:v:0", "-f", "null", "-"])
            final = Path(temp) / "final.mp4"
            self._ffmpeg(["-i", str(downloaded), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
                          "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart", str(final)])
            self._probe(final, "audio")
            if abs(self._probe(final, "video") - video_duration) > 0.15:
                raise ValueError("Lip sync final video duration mismatch")
            # Same filesystem: atomic publication without replacing an existing file.
            try:
                os.link(final, output)
            except FileExistsError:
                raise ValueError("Lip sync output already exists") from None
        self._report_progress("completed", percent=100, force=True)
        return str(output)
