"""Resumable client for the self-hosted VideoPrinterTurbo_LipSync service."""
import hashlib
import json
import math
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

import requests

from pipeline.lip_sync.base import LipSyncBase
from pipeline.lip_sync._publish import publish_result

import config.config as _config


class RemoteHTTPError(RuntimeError):
    def __init__(self, status, detail):
        self.status = status
        super().__init__(f'LipSync HTTP {status}: {detail}')


def _digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _probe(path, kind, timeout=60):
    try:
        data = json.loads(subprocess.run(
            ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
            check=True, capture_output=True, text=True, timeout=timeout).stdout)
        stream = next(s for s in data['streams'] if s.get('codec_type') == kind)
        duration = float(stream.get('duration') or data['format']['duration'])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('Invalid duration')
        return duration
    except subprocess.TimeoutExpired:
        raise TimeoutError('LipSync media verification timed out; checkpoint retained') from None
    except FileNotFoundError:
        raise RuntimeError('FFprobe is missing; add FFmpeg/ffprobe to the client PATH') from None
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError):
        raise ValueError(f'Invalid or unreadable {kind} file: {path.name}') from None


@contextmanager
def _output_lock(path):
    # Keep the inode after unlock: deleting a lock file introduces a race with waiters.
    with path.open('a+b') as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError('Another LipSync client is using this output path') from None
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == 'nt':
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


class RemoteLipSync(LipSyncBase):
    PROGRESS_PROVIDER = "remote"

    def __init__(self, base_url: str, *, api_key: str = '', request_timeout: float = 60,
                 poll_interval: float = 2, job_timeout: float = 0,
                 chunk_size: int = 8 * 1024 ** 2, retries: int = 3, retry_delay: float = 1,
                 timeline: str = 'strict', readiness_timeout: float = 600, on_progress=None):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise ValueError('base_url must be an HTTP(S) service URL without credentials/query/fragment')
        for name, value in (('request_timeout', request_timeout), ('poll_interval', poll_interval),
                            ('retry_delay', retry_delay),
                            ('readiness_timeout', readiness_timeout)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
        if isinstance(job_timeout, bool) or not math.isfinite(job_timeout) or job_timeout < 0:
            raise ValueError('job_timeout must be finite and nonnegative (0 disables the total deadline)')
        if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or not 0 < chunk_size <= 8 * 1024 ** 2:
            raise ValueError('chunk_size must be an integer in 1..8MiB')
        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
            raise ValueError('retries must be a nonnegative integer')
        if timeline not in ('strict', 'audio'):
            raise ValueError('timeline must be strict or audio')
        self.base_url, self.api_key = base_url.rstrip('/'), api_key
        self.request_timeout, self.poll_interval, self.job_timeout = request_timeout, poll_interval, job_timeout
        self.chunk_size, self.retries, self.retry_delay = chunk_size, retries, retry_delay
        self.last_job_id = None
        self.on_progress = on_progress
        self.timeline, self.readiness_timeout = timeline, readiness_timeout

    def _remaining(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f'LipSync timed out (job_timeout={self.job_timeout:g}s, '
                f'job_id={self.last_job_id or "unknown"}); checkpoint retained, '
                'remote job may still be running; retry with the same inputs and output '
                'to resume, or set job_timeout=0 to disable the total deadline')
        return remaining

    def _pause(self, duration):
        time.sleep(min(duration, self._remaining()))
        self._remaining()

    def _request(self, method, path, *, root=False, deadline=None, **kwargs):
        remaining = self._remaining()
        if deadline is not None:
            remaining = min(remaining, deadline - time.monotonic())
            if remaining <= 0:
                raise TimeoutError('LipSync service readiness timed out; checkpoint retained')
        url = self.base_url + ('/' if root else '/v1/') + path
        response = self._session.request(method, url,
                                         timeout=min(self.request_timeout, remaining),
                                         allow_redirects=False, **kwargs)
        if not 200 <= response.status_code < 300:
            try:
                detail = str(response.json().get('detail', 'Request failed'))[:500]
            except (ValueError, AttributeError):
                detail = 'Non-JSON error response'
            status = response.status_code
            response.close()
            raise RemoteHTTPError(status, detail)
        return response

    def _ready_pause(self, deadline):
        remaining = min(self._remaining(), deadline - time.monotonic())
        if remaining <= 0:
            raise TimeoutError('LipSync service readiness timed out; checkpoint retained')
        time.sleep(min(self.poll_interval, remaining))
        self._remaining()
        if time.monotonic() >= deadline:
            raise TimeoutError('LipSync service readiness timed out; checkpoint retained')

    def _wait_ready(self, deadline=None):
        self._report_progress("waiting_ready")
        deadline = min(self._deadline, deadline if deadline is not None else time.monotonic() + self.readiness_timeout)
        while True:
            self._report_progress('waiting_ready')
            try:
                with self._request('GET', 'health', root=True, deadline=deadline) as response:
                    health = response.json()
                if not isinstance(health, dict) or not isinstance(health.get('ready'), bool):
                    raise RuntimeError('Invalid LipSync health response')
                if health['ready']:
                    timelines = health.get('timelines', ['strict'])
                    if not isinstance(timelines, list) or self.timeline not in timelines:
                        raise RuntimeError(f'LipSync server does not support the {self.timeline} timeline')
                    return
            except RemoteHTTPError as exc:
                if exc.status in (404, 405) and self.timeline == 'strict':
                    return  # Older strict-only servers did not expose health.
                if exc.status not in (408, 429, 500, 502, 503, 504):
                    raise
            except ValueError as exc:
                raise RuntimeError('Invalid LipSync health JSON') from exc
            except requests.RequestException:
                pass  # Startup can temporarily refuse connections.
            self._ready_pause(deadline)

    def _recover_ready(self, deadline):
        deadline = deadline if deadline is not None else time.monotonic() + self.readiness_timeout
        self._wait_ready(deadline)
        # Bound repeated API 503s even if a proxy reports ready at /health.
        self._ready_pause(deadline)
        return deadline

    def _validate_job(self, job, duration):
        if job.get('timeline', 'strict') != self.timeline:
            raise RuntimeError('LipSync server returned a different timeline')
        reported = job.get('expected_duration')
        if reported is None:
            if self.timeline == 'audio' and job.get('status') == 'succeeded':
                raise RuntimeError('LipSync server did not confirm the audio output duration')
        elif (isinstance(reported, bool) or not isinstance(reported, (int, float))
              or not math.isfinite(reported) or reported <= 0 or abs(reported - duration) > .15):
            raise RuntimeError('LipSync server returned an unexpected output duration')

    def _api(self, method, path, **kwargs):
        failures, recovery = 0, None
        while True:
            try:
                with self._request(method, path, **kwargs) as response:
                    data = response.json()
                if not isinstance(data, dict) or data.get('code') != 0 or not isinstance(data.get('data'), dict):
                    raise RuntimeError('Invalid LipSync response')
                return data['data']
            except (requests.RequestException, RemoteHTTPError) as exc:
                if isinstance(exc, RemoteHTTPError) and exc.status == 503:
                    recovery = self._recover_ready(recovery)
                    continue
                if isinstance(exc, RemoteHTTPError) and exc.status not in (408, 429, 500, 502, 503, 504):
                    raise
                failures += 1
                if failures > self.retries:
                    raise
                self._pause(self.retry_delay * failures)

    @staticmethod
    def _save(path, state):
        temp = path.with_name(path.name + '.tmp')
        with temp.open('w', encoding='utf-8') as target:
            json.dump(state, target)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temp, path)

    def _upload(self, state, checkpoint, inputs):
        uid = state['upload_id']
        for kind, path in inputs.items():
            failures, recovery = 0, None
            while True:
                current = self._api('GET', f'uploads/{uid}')
                if current.get('job_id'):
                    state['job_id'] = current['job_id']
                    self._save(checkpoint, state)
                    return
                offset = current['files'][kind]['offset']
                if not isinstance(offset, int) or not 0 <= offset <= state['identity']['files'][kind]['size']:
                    raise RuntimeError('Invalid server upload offset')
                self._report_progress('upload_' + kind, completed=offset,
                                      total=state['identity']['files'][kind]['size'], unit='bytes')
                if offset == state['identity']['files'][kind]['size']:
                    break
                with path.open('rb') as source:
                    source.seek(offset)
                    chunk = source.read(self.chunk_size)
                if not chunk:
                    raise ValueError('Input file changed during upload')
                try:
                    # PATCH retries must query offset first: a lost response may mean committed data.
                    with self._request('PATCH', f'uploads/{uid}/{kind}', data=chunk,
                                       headers={'Upload-Offset': str(offset),
                                                'Content-Type': 'application/octet-stream'}):
                        pass
                    failures = 0
                    recovery = None
                except (requests.RequestException, RemoteHTTPError) as exc:
                    if isinstance(exc, RemoteHTTPError) and exc.status == 503:
                        recovery = self._recover_ready(recovery)
                        continue  # Re-query the committed offset before PATCH.
                    if isinstance(exc, RemoteHTTPError) and exc.status not in (408, 409, 429, 500, 502, 503, 504):
                        raise
                    failures += 1
                    if failures > self.retries:
                        raise
                    self._pause(self.retry_delay * failures)

    def _download(self, jid, result, part):
        self._report_progress("download", job_id=jid)
        size, sha = result['size'], result['sha256']
        if not isinstance(size, int) or size <= 0 or not isinstance(sha, str) or len(sha) != 64:
            raise RuntimeError('Invalid LipSync result metadata')
        failures, recovery = 0, None
        while True:
            offset = part.stat().st_size if part.exists() else 0
            if offset > size:
                part.unlink()
                offset = 0
            if offset == size:
                if _digest(part) == sha:
                    return
                part.unlink()
                offset = 0
            headers = {'Range': f'bytes={offset}-', 'If-Range': f'"{sha}"'} if offset else {}
            try:
                with self._request('GET', f'jobs/{jid}/result', headers=headers, stream=True) as response:
                    if response.status_code == 206:
                        expected = f'bytes {offset}-{size - 1}/{size}'
                        if response.headers.get('Content-Range') != expected:
                            raise RuntimeError('Invalid download Content-Range')
                    elif response.status_code == 200:
                        offset = 0  # Server ignored Range / If-Range; safely restart instead of appending.
                    else:
                        raise RuntimeError('Unexpected result download status')
                    with part.open('ab' if offset else 'wb') as target:
                        for chunk in response.iter_content(256 * 1024):
                            self._remaining()
                            offset += len(chunk)
                            if offset > size:
                                raise RuntimeError('Result download exceeds declared size')
                            target.write(chunk)
                            self._report_progress("download", completed=offset, total=size, unit="bytes", job_id=jid)
                if offset != size or _digest(part) != sha:
                    if offset == size:
                        part.unlink()
                    raise requests.ConnectionError('Incomplete or corrupt LipSync download')
                return
            except (requests.RequestException, RemoteHTTPError) as exc:
                if isinstance(exc, RemoteHTTPError) and exc.status == 503:
                    recovery = self._recover_ready(recovery)
                    continue
                if isinstance(exc, RemoteHTTPError) and exc.status not in (408, 429, 500, 502, 503, 504):
                    raise
                failures += 1
                if failures > self.retries:
                    raise
                self._pause(self.retry_delay * failures)

    def lip_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        self._start_progress(self.PROGRESS_PROVIDER)
        self.last_job_id = None
        inputs = {kind: Path(path).expanduser().resolve() for kind, path in
                  (('video', video_path), ('audio', audio_path))}
        output = Path(output_path).expanduser().resolve()
        if output in inputs.values() or output.exists() or output.suffix.lower() != '.mp4':
            raise ValueError('output_path must be a new .mp4 file distinct from inputs')
        for path in inputs.values():
            if not path.is_file() or not path.stat().st_size:
                raise ValueError(f'Input missing or empty: {path.name}')
        video_duration = _probe(inputs['video'], 'video')
        audio_duration = _probe(inputs['audio'], 'audio')
        if self.timeline == 'strict' and abs(video_duration - audio_duration) > .15:
            raise ValueError(f'Video ({video_duration:.3f}s) and audio ({audio_duration:.3f}s) must share a timeline '
                             '(maximum duration difference 150ms); use timeline="audio" for different durations')
        duration = audio_duration if self.timeline == 'audio' else video_duration
        output.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = output.with_name(output.name + '.lipsync.json')
        part = output.with_name(output.name + '.lipsync.part')
        identity = {'base_url': self.base_url, 'timeline': self.timeline, 'files': {
            kind: {'name': path.name, 'size': path.stat().st_size, 'sha256': _digest(path)}
            for kind, path in inputs.items()}}
        self._deadline = time.monotonic() + self.job_timeout if self.job_timeout else math.inf
        with _output_lock(output.with_name(output.name + '.lipsync.lock')), requests.Session() as session:
            if output.exists():
                raise ValueError('LipSync output already exists')
            session.trust_env = False
            session.headers['Accept-Encoding'] = 'identity'
            if self.api_key:
                session.headers['Authorization'] = f'Bearer {self.api_key}'
            self._session = session
            try:
                state = json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else {}
            except (ValueError, OSError):
                state = {}
            if (isinstance(state, dict) and isinstance(state.get('identity'), dict)
                    and 'timeline' not in state['identity'] and self.timeline == 'strict'
                    and {**state['identity'], 'timeline': 'strict'} == identity):
                state['identity'] = identity  # Proven strict-only legacy checkpoint.
                self._save(checkpoint, state)
            if not isinstance(state, dict) or state.get('identity') != identity:
                state = {'identity': identity}
                part.unlink(missing_ok=True)
            # A restarted server invalidates the checkpoint. Retry one fresh session.
            for restart in range(2):
                try:
                    if not state.get('job_id'):
                        self._wait_ready()
                    if not state.get('upload_id'):
                        upload = self._api('POST', 'uploads', json=identity['files'])
                        state['upload_id'] = upload['upload_id']
                        self._save(checkpoint, state)
                    if not state.get('job_id'):
                        self._upload(state, checkpoint, inputs)
                    if not state.get('job_id'):
                        self._report_progress("submitting")
                        job = self._api('POST', f"uploads/{state['upload_id']}/submit",
                                        json={'timeline': self.timeline})
                        state['job_id'] = job['job_id']
                        self._save(checkpoint, state)
                        self._validate_job(job, duration)
                    self.last_job_id = state['job_id']
                    while True:
                        job = self._api('GET', f"jobs/{state['job_id']}")
                        self._validate_job(job, duration)
                        progress = job.get('progress') if isinstance(job.get('progress'), dict) else {}
                        stage = progress.get('stage') or {'queued': 'queued', 'running': 'running',
                                                         'succeeded': 'remote_completed', 'failed': 'failed'}.get(job['status'], 'running')
                        if job['status'] == 'succeeded':
                            stage = 'remote_completed'  # Download/validation/publication are still pending.
                        elif job['status'] == 'failed':
                            stage = 'failed'
                        self._report_progress(stage, percent=progress.get('percent'),
                                              completed=progress.get('completed'), total=progress.get('total'),
                                              unit=progress.get('unit'), queue_position=progress.get('queue_position'),
                                              job_id=state['job_id'])
                        if job['status'] == 'failed':
                            raise RuntimeError(f"LipSync job {state['job_id']} failed: {job.get('error')}")
                        if job['status'] == 'succeeded':
                            break
                        if job['status'] not in ('queued', 'running'):
                            raise RuntimeError('Unknown LipSync job status')
                        self._pause(self.poll_interval)
                    self._download(state['job_id'], job['result'], part)
                    break
                except RemoteHTTPError as exc:
                    if exc.status != 404 or restart:
                        raise
                    state = {'identity': identity}
                    part.unlink(missing_ok=True)
                    self._save(checkpoint, state)
            self._report_progress('validating')
            if abs(_probe(part, 'video', min(60, self._remaining())) - duration) > .15:
                raise ValueError('LipSync output video duration changed')
            if abs(_probe(part, 'audio', min(60, self._remaining())) - audio_duration) > .15:
                raise ValueError('LipSync output audio duration changed')
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(part),
                            '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
                           check=True, capture_output=True, timeout=min(1800, self._remaining()))
            # Atomic no-clobber publication, matching the existing cloud adapters.
            self._remaining()
            publish_result(part, output)
            part.unlink(missing_ok=True)
            checkpoint.unlink(missing_ok=True)
            self._report_progress("completed", percent=100, force=True)
            return str(output)


if __name__ == "__main__":
    _config.init_config()
    lip_sync = RemoteLipSync(
        base_url="http://192.168.0.101:8081"
    )
    result = lip_sync.lip_sync(
        video_path="/Users/sunxiao5/Downloads/musetalk/speaker.mp4",
        audio_path="/Users/sunxiao5/Downloads/musetalk/voice_12.200.wav",
        output_path="/Users/sunxiao5/Downloads/musetalk/speaker_synced_back.mp4"
    )
    print(result)
