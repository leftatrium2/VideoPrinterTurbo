"""fal.ai LatentSync queue adapter; no global SDK configuration or new dependencies."""
import json
import logging
import math
import mimetypes
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests

from pipeline.lip_sync.base import LipSyncBase

logger = logging.getLogger(__name__)


class FalLatentSync(LipSyncBase):
    MODEL_ID = "fal-ai/latentsync"

    def __init__(self, api_key: str, *, guidance_scale: float = 1, seed: int | None = None,
                 queue_base_url: str = "https://queue.fal.run",
                 storage_base_url: str = "https://rest.fal.ai", proxy_url: str | None = None,
                 request_timeout: float = 60, upload_timeout: float = 600,
                 poll_interval: float = 5, job_timeout: float = 3600):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("fal.ai api_key is required")
        for name, value in (("guidance_scale", guidance_scale), ("request_timeout", request_timeout),
                            ("upload_timeout", upload_timeout), ("poll_interval", poll_interval),
                            ("job_timeout", job_timeout)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self._check_url(queue_base_url)
        self._check_url(storage_base_url)
        self._api_key = api_key.strip()
        self._guidance_scale = guidance_scale
        self._seed = seed
        self._queue_base_url = queue_base_url.rstrip("/")
        self._storage_base_url = storage_base_url.rstrip("/")
        self._proxy_url = proxy_url
        self._request_timeout = request_timeout
        self._upload_timeout = upload_timeout
        self._poll_interval = poll_interval
        self._job_timeout = job_timeout
        self.last_request_id: str | None = None

    @staticmethod
    def _check_url(url):
        if not isinstance(url, str):
            raise ValueError("fal.ai returned an invalid URL")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" and not
        (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1"))):
            raise ValueError("fal.ai URLs require HTTPS (HTTP allowed only for local testing)")
        if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("Invalid fal.ai URL")

    def _safe_error(self, value):
        return re.sub(r"https?://\S+", "<redacted-url>", str(value).replace(self._api_key, "<redacted>"))[:1000]

    def _check_api_url(self, url):
        self._check_url(url)
        target = urlsplit(url)
        for base in (self._queue_base_url, self._storage_base_url):
            allowed = urlsplit(base)
            if ((target.scheme, target.netloc) == (allowed.scheme, allowed.netloc)
                    and target.path.startswith(allowed.path.rstrip("/") + "/")):
                return
        raise ValueError("fal.ai returned a queue URL outside the configured API origins")

    def _request(self, session, method, url, *, authenticated=False, **kwargs):
        self._check_url(url)
        headers = kwargs.pop("headers", {})
        if authenticated:
            self._check_api_url(url)
            headers["Authorization"] = f"Key {self._api_key}"
        try:
            response = session.request(method, url, headers=headers, allow_redirects=False,
                                       timeout=kwargs.pop("timeout", self._request_timeout), **kwargs)
        except requests.RequestException as exc:
            raise RuntimeError(f"fal.ai {method} request failed ({type(exc).__name__})") from None
        if not 200 <= response.status_code < 300:
            try:
                body = response.json()
                detail = self._safe_error(body.get("detail", body.get("error", ""))) if isinstance(body, dict) else ""
            except ValueError:
                detail = "non-JSON response"
            response.close()
            raise RuntimeError(f"fal.ai {method} HTTP {response.status_code}: {detail}")
        return response

    def _json(self, session, method, url, **kwargs):
        with self._request(session, method, url, authenticated=True, **kwargs) as response:
            try:
                data = response.json()
            except ValueError:
                raise RuntimeError("fal.ai returned invalid JSON") from None
        if not isinstance(data, dict):
            raise RuntimeError("fal.ai returned an invalid response object")
        return data

    @staticmethod
    def _required(data, key):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"fal.ai response missing {key}")
        return value

    def _upload(self, session, path):
        content_type = "audio/wav" if path.suffix.lower() == ".wav" else (
                mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        # Same storage initiation contract as the official Python client's GCS repository.
        upload = self._json(session, "POST", f"{self._storage_base_url}/storage/upload/initiate",
                            params={"storage_type": "gcs"},
                            json={"file_name": path.name, "content_type": content_type})
        upload_url = self._required(upload, "upload_url")
        file_url = self._required(upload, "file_url")
        self._check_url(file_url)
        with path.open("rb") as source, self._request(
                session, "PUT", upload_url, data=source, headers={"Content-Type": content_type},
                timeout=self._upload_timeout):
            pass
        return file_url

    def _wait(self, session, submitted):
        request_id = self._required(submitted, "request_id")
        self.last_request_id = request_id
        root = f"{self._queue_base_url}/{self.MODEL_ID}/requests/{quote(request_id, safe='')}"
        status_url = submitted.get("status_url", root + "/status")
        response_url = submitted.get("response_url", root)
        self._check_api_url(status_url)
        self._check_api_url(response_url)
        logger.info("fal.ai LatentSync submitted: %s", request_id)
        deadline = time.monotonic() + self._job_timeout
        previous = None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"fal.ai request {request_id} timed out locally; remote job may still run. "
                                   "Check the existing request before submitting again.")
            state = self._json(session, "GET", status_url, timeout=min(self._request_timeout, remaining))
            status = state.get("status")
            if previous != status:
                logger.info("fal.ai request %s: %s", request_id, status)
                previous = status
            if status == "COMPLETED":
                # fal signals failed inference with COMPLETED + error, not a FAILED queue state.
                if state.get("error") or state.get("error_type"):
                    raise RuntimeError(f"fal.ai request {request_id} failed: "
                                       f"{self._safe_error(state.get('error_type', ''))} "
                                       f"{self._safe_error(state.get('error', ''))}")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"fal.ai request {request_id}: timed out before result retrieval")
                result = self._json(session, "GET", response_url,
                                    timeout=min(self._request_timeout, remaining))
                video = result.get("video")
                if not isinstance(video, dict):
                    raise RuntimeError(f"fal.ai request {request_id}: result missing video")
                return self._required(video, "url")
            if status not in ("IN_QUEUE", "IN_PROGRESS"):
                raise RuntimeError(f"fal.ai request {request_id}: unknown status {self._safe_error(status)}")
            time.sleep(min(self._poll_interval, max(0, deadline - time.monotonic())))

    @staticmethod
    def _probe(path, kind):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                check=True, capture_output=True, text=True, timeout=60)
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
            raise RuntimeError("LatentSync video decoding or final audio mux failed") from None

    def _download(self, session, url, destination):
        try:
            with self._request(session, "GET", url, stream=True) as response, destination.open("wb") as target:
                deadline = time.monotonic() + self._upload_timeout
                for chunk in response.iter_content(1024 * 1024):
                    if time.monotonic() > deadline:
                        raise TimeoutError("fal.ai output download timed out")
                    target.write(chunk)
        except requests.RequestException as exc:
            raise RuntimeError(f"fal.ai output transfer failed ({type(exc).__name__})") from None
        if not destination.stat().st_size:
            raise RuntimeError("fal.ai returned an empty video")

    def lip_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        self.last_request_id = None
        video, audio, output = [Path(p).expanduser().resolve() for p in (video_path, audio_path, output_path)]
        if output in (video, audio) or output.exists():
            raise ValueError("Lip sync output must be a new file, distinct from both inputs")
        if output.suffix.lower() != ".mp4":
            raise ValueError("Lip sync output_path must end with .mp4")
        for path in (video, audio):
            if not path.is_file() or not path.stat().st_size:
                raise ValueError(f"Lip sync input missing or empty: {path.name}")
        duration = self._probe(video, "video")
        audio_duration = self._probe(audio, "audio")
        if abs(audio_duration - duration) > 0.15 or audio_duration - duration > 0.001:
            raise ValueError(f"LatentSync inputs must share a timeline and audio must not exceed video duration: "
                             f"video={duration:.3f}s, audio={audio_duration:.3f}s")
        output.parent.mkdir(parents=True, exist_ok=True)
        with requests.Session() as session, tempfile.TemporaryDirectory(prefix="fal_lip_sync_",
                                                                        dir=output.parent) as tmp:
            session.trust_env = False
            if self._proxy_url:
                session.proxies.update(http=self._proxy_url, https=self._proxy_url)
            video_url = self._upload(session, video)
            audio_url = self._upload(session, audio)
            arguments = {"video_url": video_url, "audio_url": audio_url,
                         "guidance_scale": self._guidance_scale, "enable_safety_checker": True}
            if self._seed is not None:
                arguments["seed"] = self._seed
            # Do not retry paid submission automatically; a lost response may hide an accepted job.
            submitted = self._json(session, "POST", f"{self._queue_base_url}/{self.MODEL_ID}", json=arguments)
            url = self._wait(session, submitted)
            downloaded = Path(tmp) / "download.mp4"
            self._download(session, url, downloaded)
            if abs(self._probe(downloaded, "video") - duration) > 0.15:
                raise ValueError("fal.ai changed the video duration; output rejected")
            self._ffmpeg(["-i", str(downloaded), "-map", "0:v:0", "-f", "null", "-"])
            final = Path(tmp) / "final.mp4"
            self._ffmpeg(["-i", str(downloaded), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
                          "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart", str(final)])
            self._probe(final, "audio")
            if abs(self._probe(final, "video") - duration) > 0.15:
                raise ValueError("LatentSync final video duration mismatch")
            try:
                os.link(final, output)
            except FileExistsError:
                raise ValueError("Lip sync output already exists") from None
        return str(output)
