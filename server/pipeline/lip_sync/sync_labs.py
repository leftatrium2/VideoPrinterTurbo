"""Sync Labs adapter. Configuration is explicit; no credentials are read from disk."""
import json
import logging
import math
import mimetypes
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

import requests

from pipeline.lip_sync.base import LipSyncBase

logger = logging.getLogger(__name__)


class SyncLabs(LipSyncBase):
    def __init__(self, api_key: str, model: str = "lipsync-2", *,
                 base_url: str = "https://api.sync.so/v2", proxy_url: str | None = None,
                 request_timeout: float = 60, upload_timeout: float = 600,
                 poll_interval: float = 10, job_timeout: float = 3600):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Sync Labs api_key is required")
        if not model or not isinstance(model, str):
            raise ValueError("Sync Labs model is required")
        for name, value in (("request_timeout", request_timeout), ("upload_timeout", upload_timeout),
                            ("poll_interval", poll_interval), ("job_timeout", job_timeout)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        self._check_url(base_url)
        self._api_key = api_key.strip()
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._proxy_url = proxy_url
        self._request_timeout = request_timeout
        self._upload_timeout = upload_timeout
        self._poll_interval = poll_interval
        self._job_timeout = job_timeout
        self.last_generation_id: str | None = None

    @staticmethod
    def _check_url(url):
        if not isinstance(url, str):
            raise ValueError("Sync Labs returned an invalid media URL")
        parsed = urlsplit(url)
        if parsed.scheme != "https" and not (
                parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")):
            raise ValueError("Sync Labs URLs require HTTPS (HTTP allowed only for local testing)")
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid Sync Labs URL")

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
            raise RuntimeError(f"Sync Labs {method} request failed ({type(exc).__name__})") from None
        if not 200 <= response.status_code < 300:
            try:
                body = response.json()
                detail = self._error_text(body.get("errorCode", body.get("message", ""))) if isinstance(body,
                                                                                                        dict) else ""
            except ValueError:
                detail = "non-JSON response"
            response.close()
            raise RuntimeError(f"Sync Labs {method} HTTP {response.status_code}: {detail}")
        return response

    def _download_request(self, session, url):
        # Follow CDN redirects explicitly so every target passes URL validation.
        # API requests and signed uploads retain their no-redirect policy.
        for hop in range(6):
            self._check_url(url)
            try:
                response = session.get(url, stream=True, allow_redirects=False,
                                       timeout=self._request_timeout)
            except requests.RequestException as exc:
                raise RuntimeError(f"Sync Labs GET request failed ({type(exc).__name__})") from None
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise RuntimeError("Sync Labs download redirect missing Location")
                if hop == 5:
                    raise RuntimeError("Sync Labs download exceeded 5 redirects")
                target = urljoin(url, location)
                self._check_url(target)
                if urlsplit(url).scheme == "https" and urlsplit(target).scheme != "https":
                    raise RuntimeError("Sync Labs download redirect requires HTTPS")
                url = target
                continue
            if not 200 <= response.status_code < 300:
                response.close()
                raise RuntimeError(f"Sync Labs download HTTP {response.status_code}")
            return response

    def _api(self, session, method, path, **kwargs):
        with self._request(session, method, f"{self._base_url}/{path}", authenticated=True, **kwargs) as response:
            try:
                result = response.json()
            except ValueError:
                raise RuntimeError("Sync Labs returned invalid JSON") from None
        if not isinstance(result, dict):
            raise RuntimeError("Sync Labs returned an invalid response object")
        return result

    @staticmethod
    def _required(data, key):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"Sync Labs response missing {key}")
        return value

    def _upload(self, session, path, kind):
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix.lower() == ".wav":
            content_type = "audio/wav"
        signed = self._api(session, "POST", "assets/upload", json={
            "fileName": path.name, "contentType": content_type, "size": path.stat().st_size})
        upload_url = self._required(signed, "uploadUrl")
        asset_url = self._required(signed, "url")
        self._check_url(asset_url)
        with path.open("rb") as source:
            with self._request(session, "PUT", upload_url, data=source,
                               headers={"Content-Type": content_type}, timeout=self._upload_timeout):
                pass
        asset = self._api(session, "POST", "assets", json={"url": asset_url, "type": kind, "name": path.name})
        return self._required(asset, "id")

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
        deadline = time.monotonic() + self._job_timeout
        job_id = self._required(generation, "id")
        self.last_generation_id = job_id
        logger.info("Sync Labs generation submitted: %s", job_id)
        previous_status = None
        while True:
            status = generation.get("status")
            if status != previous_status:
                logger.info("Sync Labs generation %s: %s", job_id, status)
                previous_status = status
            if status == "COMPLETED":
                return self._required(generation, "outputUrl")
            if status in ("FAILED", "REJECTED"):
                raise RuntimeError(f"Sync Labs generation {job_id} {status}: "
                                   f"{self._error_text(generation.get('errorCode', ''))} "
                                   f"{self._error_text(generation.get('error', ''))}")
            if status not in ("PENDING", "PROCESSING"):
                raise RuntimeError(f"Sync Labs generation {job_id}: unknown status {self._error_text(status)}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Sync Labs generation {job_id} timed out locally; remote job may still run. "
                                   "Check this generation before submitting again.")
            time.sleep(min(self._poll_interval, remaining))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                continue
            generation = self._api(session, "GET", f"generate/{quote(job_id, safe='')}",
                                   timeout=min(self._request_timeout, remaining))

    def lip_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        self.last_generation_id = None
        video, audio, output = [Path(p).expanduser().resolve() for p in (video_path, audio_path, output_path)]
        if output in (video, audio) or output.exists():
            raise ValueError("Lip sync output must be a new file, distinct from both inputs")
        for path in (video, audio):
            if not path.is_file() or not path.stat().st_size:
                raise ValueError(f"Lip sync input missing or empty: {path.name}")
            if path.stat().st_size > 5 * 1024 ** 3:
                raise ValueError("Sync Labs assets cannot exceed 5 GiB per file")
        video_duration = self._probe(video, "video")
        audio_duration = self._probe(audio, "audio")
        # Allow only encoding/frame rounding, never a genuine timing adjustment.
        if abs(video_duration - audio_duration) > 0.15:
            raise ValueError(
                f"Lip sync inputs must share a timeline: video={video_duration:.3f}s, audio={audio_duration:.3f}s")
        if output.suffix.lower() != ".mp4":
            raise ValueError("Lip sync output_path must end with .mp4")
        output.parent.mkdir(parents=True, exist_ok=True)
        with requests.Session() as session, tempfile.TemporaryDirectory(prefix="lip_sync_", dir=output.parent) as temp:
            session.trust_env = False
            if self._proxy_url:
                session.proxies.update(http=self._proxy_url, https=self._proxy_url)
            video_id = self._upload(session, video, "VIDEO")
            audio_id = self._upload(session, audio, "AUDIO")
            generation = self._api(session, "POST", "generate", json={
                "model": self._model,
                "input": [{"type": "video", "assetId": video_id}, {"type": "audio", "assetId": audio_id}],
                "options": {"sync_mode": "silence"}},
                                   headers={"Idempotency-Key": uuid.uuid4().hex})
            url = self._wait(session, generation)
            downloaded = Path(temp) / "download.mp4"
            # Separate unauthenticated request: never leak the API key to storage/CDN.
            try:
                with self._download_request(session, url) as response, downloaded.open("wb") as target:
                    deadline = time.monotonic() + self._upload_timeout
                    for chunk in response.iter_content(1024 * 1024):
                        if time.monotonic() > deadline:
                            raise TimeoutError("Sync Labs output download timed out")
                        target.write(chunk)
            except requests.RequestException as exc:
                raise RuntimeError(f"Sync Labs output transfer failed ({type(exc).__name__})") from None
            if not downloaded.stat().st_size:
                raise RuntimeError("Sync Labs returned an empty output video")
            duration = self._probe(downloaded, "video")
            if abs(duration - video_duration) > 0.15:
                raise ValueError("Sync Labs changed the video duration; output rejected")
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
        return str(output)
